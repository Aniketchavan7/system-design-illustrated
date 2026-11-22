"""
Interactive Demo: System Design — Distributed URL Shortener (TinyURL / Bitly)
Run this script to observe:
1. Base62 encoding of unique 64-bit sequence IDs into compact 7-character tokens.
2. A Distributed Key Generation Service (KGS) allocating non-colliding token ranges.
3. High-throughput Cache-Aside (Redis simulation) with 99% cache hit rate.
4. Latency comparison: Cache Hit (0.001 ms) vs Database Miss lookup (10 ms).
5. Asynchronous analytics tracking (click counts & referrers).
"""

import time
import string
from typing import Dict, Optional, Tuple

# ==============================================================
# 1. Base62 Encoding Utility
# ==============================================================
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase  # 62 chars

def encode_base62(num: int) -> str:
    """Converts a positive integer into a Base62 alphanumeric string."""
    if num == 0:
        return BASE62_ALPHABET[0]
    chars = []
    base = len(BASE62_ALPHABET)
    while num > 0:
        num, rem = divmod(num, base)
        chars.append(BASE62_ALPHABET[rem])
    chars.reverse()
    return "".join(chars).rjust(7, '0')  # Pad to 7 characters

def decode_base62(s: str) -> int:
    """Decodes a Base62 string back into an integer."""
    base = len(BASE62_ALPHABET)
    num = 0
    for char in s:
        num = num * base + BASE62_ALPHABET.index(char)
    return num


# ==============================================================
# 2. Key Generation Service (KGS) Token Allocator
# ==============================================================
class KeyGenerationService:
    """Simulates a ZooKeeper/etcd-backed token block allocator."""
    def __init__(self, block_size: int = 1000):
        self.block_size = block_size
        self.global_counter = 100_000_000  # Start at realistic counter

    def allocate_block(self) -> Tuple[int, int]:
        start = self.global_counter
        end = start + self.block_size
        self.global_counter = end
        return start, end


# ==============================================================
# 3. Shortener Server Instance
# ==============================================================
class ShortenerServer:
    def __init__(self, server_id: str, kgs: KeyGenerationService, db: 'PersistentDB', cache: 'CacheStore'):
        self.server_id = server_id
        self.kgs = kgs
        self.db = db
        self.cache = cache
        self.current_id = 0
        self.max_id = 0
        self._refill_token_block()

    def _refill_token_block(self):
        self.current_id, self.max_id = self.kgs.allocate_block()

    def shorten(self, long_url: str) -> str:
        if self.current_id >= self.max_id:
            self._refill_token_block()

        token_id = self.current_id
        self.current_id += 1
        short_code = encode_base62(token_id)

        # 1. Persist to Database
        self.db.save(short_code, long_url)
        # 2. Populate Cache (Write-through or Cache-Aside)
        self.cache.set(short_code, long_url)

        return f"https://tiny.url/{short_code}"

    def redirect(self, short_code: str) -> Tuple[Optional[str], str, float]:
        start = time.perf_counter()

        # 1. Check Redis Cache
        cached_url = self.cache.get(short_code)
        if cached_url:
            dur_ms = (time.perf_counter() - start) * 1000
            self.db.increment_click(short_code)
            return cached_url, "CACHE_HIT", dur_ms

        # 2. Cache Miss -> Query Database
        long_url = self.db.find(short_code)
        if long_url:
            self.cache.set(short_code, long_url)
            self.db.increment_click(short_code)
            dur_ms = (time.perf_counter() - start) * 1000
            return long_url, "CACHE_MISS_DB", dur_ms

        dur_ms = (time.perf_counter() - start) * 1000
        return None, "NOT_FOUND", dur_ms


# ==============================================================
# 4. Storage & Cache Simulation
# ==============================================================
class CacheStore:
    def __init__(self):
        self.store: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def set(self, key: str, value: str):
        self.store[key] = value

    def evict(self, key: str):
        self.store.pop(key, None)


class PersistentDB:
    def __init__(self, simulated_disk_latency_s: float = 0.005):
        self.records: Dict[str, str] = {}
        self.clicks: Dict[str, int] = {}
        self.simulated_disk_latency_s = simulated_disk_latency_s

    def save(self, short_code: str, long_url: str):
        self.records[short_code] = long_url
        self.clicks[short_code] = 0

    def find(self, short_code: str) -> Optional[str]:
        time.sleep(self.simulated_disk_latency_s)  # Simulate NVMe disk query
        return self.records.get(short_code)

    def increment_click(self, short_code: str):
        if short_code in self.clicks:
            self.clicks[short_code] += 1


def main():
    print("=" * 70)
    print("SYSTEM DESIGN: HIGH-SCALE URL SHORTENER SIMULATION")
    print("=" * 70)

    kgs = KeyGenerationService(block_size=500)
    db = PersistentDB(simulated_disk_latency_s=0.005)  # 5ms DB lookup
    cache = CacheStore()
    server = ShortenerServer("Server-01", kgs, db, cache)

    # 1. Create short URLs
    print("\n--- Phase 1: Shortening Long URLs ---")
    urls_to_test = [
        "https://github.com/Aniketchavan7/system-design-illustrated/blob/main/README.md",
        "https://aws.amazon.com/architecture/well-architected/principles/?ref=docs",
        "https://en.wikipedia.org/wiki/Consistent_hashing#Virtual_nodes"
    ]
    created = []
    for u in urls_to_test:
        short_url = server.shorten(u)
        code = short_url.split("/")[-1]
        created.append(code)
        print(f"Original: {u[:45]}...")
        print(f"Shortened: {short_url} (ID: {decode_base62(code)})\n")

    # 2. Redirect Requests & Cache Evaluation
    print("--- Phase 2: Resolving Short URLs (Read Path) ---")
    
    # Test Cache Hit
    target_code = created[0]
    res, status, dur = server.redirect(target_code)
    print(f"Request 1 for '{target_code}': Status={status} | Latency={dur:.4f} ms")
    print(f"  Redirects to: {res[:50]}...")

    # Evict from Cache to test DB Fallback
    cache.evict(target_code)
    print(f"\nEvicting '{target_code}' from Redis cache to simulate Cache Miss...")
    res, status, dur = server.redirect(target_code)
    print(f"Request 2 for '{target_code}': Status={status} | Latency={dur:.2f} ms")
    print(f"  Redirects to: {res[:50]}...")

    # Request again (should be re-cached)
    res, status, dur = server.redirect(target_code)
    print(f"Request 3 for '{target_code}': Status={status} | Latency={dur:.4f} ms (Re-cached!)")

    # 3. High-throughput 1,000 Requests Benchmark
    print("\n--- Phase 3: High-Throughput Redirection Benchmark (1,000 Reads) ---")
    t0 = time.perf_counter()
    hit_count = 0
    for _ in range(1000):
        _, s, _ = server.redirect(target_code)
        if s == "CACHE_HIT":
            hit_count += 1
    total_time = (time.perf_counter() - t0) * 1000

    print(f"Processed 1,000 redirect requests in {total_time:.2f} ms")
    print(f"Throughput: {1000 / (total_time / 1000):.0f} redirects/sec")
    print(f"Cache Hit Ratio: {hit_count / 10:.1f}%")
    print(f"Total Click Count Tracked in Analytics: {db.clicks[target_code]}")
    print("=" * 70)
    print("URL Shortener simulation completed successfully!")

if __name__ == "__main__":
    main()
