"""
Interactive Demo: Caching Strategies & Architecture Patterns
Run this script to observe Cache-Aside (Lazy Loading), Write-Through,
and Write-Behind (Write-Back) with simulated memory vs disk timings.
"""

import time

# Simulated Disk Database (15 ms latency)
class DatabaseMock:
    def __init__(self):
        self.store = {"user:101": "Alice Johnson", "user:102": "Bob Smith"}

    def query(self, key: str):
        time.sleep(0.015)  # Simulate 15ms disk I/O
        return self.store.get(key)

    def write(self, key: str, val: str):
        time.sleep(0.015)  # Simulate 15ms disk I/O
        self.store[key] = val

# ==============================================================
# 1. Cache-Aside (Lazy Loading) Engine
# ==============================================================
class CacheAsideEngine:
    def __init__(self, db: DatabaseMock):
        self.db = db
        self.cache = {}  # key -> (value, expires_at)

    def get(self, key: str, ttl_seconds: float = 3.0):
        now = time.time()
        # Step A: Check in-memory Cache
        if key in self.cache:
            val, expires_at = self.cache[key]
            if now < expires_at:
                print(f"  ⚡ [CACHE HIT] '{key}' found in Redis RAM! (Latency: 0.2 ms)")
                return val
            else:
                print(f"  ⌛ [CACHE EXPIRED] TTL elapsed for '{key}'. Evicting from cache.")
                del self.cache[key]

        # Step B: Cache Miss -> Query Database on disk
        print(f"  ❌ [CACHE MISS] '{key}' not in RAM. Querying Database on disk (15 ms)...")
        start = time.perf_counter()
        val = self.db.query(key)
        elapsed = (time.perf_counter() - start) * 1000

        if val:
            # Step C: Populate Cache with TTL
            self.cache[key] = (val, now + ttl_seconds)
            print(f"  💾 Cached '{key}' in Redis for {ttl_seconds}s. DB query time: {elapsed:.1f} ms")
        return val

# ==============================================================
# 2. Write-Through Engine (Strong Freshness)
# ==============================================================
class WriteThroughEngine:
    def __init__(self, db: DatabaseMock):
        self.db = db
        self.cache = {}

    def write(self, key: str, val: str):
        print(f"\n[Write-Through] Updating '{key}' = '{val}'...")
        # Synchronously write to Cache AND Database before returning
        self.cache[key] = val
        self.db.write(key, val)
        print("  ✅ Synchronously written to both Cache and DB! Data is 100% fresh.")

# ==============================================================
# 3. Write-Behind (Write-Back) Engine (Batching)
# ==============================================================
class WriteBehindEngine:
    def __init__(self, db: DatabaseMock):
        self.db = db
        self.cache = {}
        self.write_queue = []

    def write(self, key: str, val: str):
        # 1. Update in-memory cache immediately in 0.1ms
        self.cache[key] = val
        self.write_queue.append((key, val))
        print(f"  ⚡ [Write-Behind] Updated in RAM immediately in 0.1ms! Queued for batch disk flush.")

    def flush_batch(self):
        print(f"\n  🔄 [BACKGROUND WORKER] Flushing {len(self.write_queue)} queued writes to Database in batch...")
        for key, val in self.write_queue:
            self.db.write(key, val)
        self.write_queue.clear()
        print("  ✅ Batch disk flush completed.")

if __name__ == "__main__":
    db = DatabaseMock()

    print("=" * 70)
    print(" ⚡ PART 1: CACHE-ASIDE (LAZY LOADING) DEMONSTRATION")
    print("=" * 70)
    cache_aside = CacheAsideEngine(db)

    # First read: Cache Miss
    print("First read for 'user:101':")
    cache_aside.get("user:101")

    # Second read: Cache Hit
    print("\nSecond read for 'user:101':")
    cache_aside.get("user:101")

    print("\n" + "=" * 70)
    print(" ✍️  PART 2: WRITE-THROUGH PATTERN")
    print("=" * 70)
    wt = WriteThroughEngine(db)
    wt.write("user:101", "Alice Updated (Write-Through)")

    print("\n" + "=" * 70)
    print(" 🚀 PART 3: WRITE-BEHIND (WRITE-BACK) PATTERN")
    print("=" * 70)
    wb = WriteBehindEngine(db)
    wb.write("user:103", "Charlie")
    wb.write("user:104", "Diana")
    wb.flush_batch()
    print("=" * 70)
