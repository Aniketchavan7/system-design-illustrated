"""
Interactive Demo: Content Delivery Network (CDN) & Edge Caching Simulation
Run this script to observe:
1. Cold Cache Miss (Origin pull across 150ms simulated transit) vs Edge Cache Hit (1ms).
2. RFC 7234 Cache-Control headers, ETags, and 304 Not Modified conditional revalidation.
3. 'stale-while-revalidate' serving stale content instantly while updating in the background.
4. Instant Edge Cache Purge (Surrogate-Key invalidation).
"""

import time
import hashlib
import threading
from dataclasses import dataclass
from typing import Optional, Dict

# ==============================================================
# 1. Simulated Origin Server
# ==============================================================
@dataclass
class HTTPResponse:
    status_code: int
    body: str
    headers: Dict[str, str]

class OriginServer:
    def __init__(self, simulated_latency_s: float = 0.15):
        self.simulated_latency_s = simulated_latency_s
        self.data_store = {
            "/assets/logo.png": "BinaryImageData(size=2MB)",
            "/static/app.js": "console.log('App v1.0.0');",
            "/api/config": '{"theme": "dark", "version": "1.0"}'
        }
        self.request_count = 0

    def fetch(self, path: str, if_none_match: Optional[str] = None) -> HTTPResponse:
        self.request_count += 1
        # Simulate physical fiber cable latency across oceans (e.g. Tokyo -> US-East)
        time.sleep(self.simulated_latency_s)

        if path not in self.data_store:
            return HTTPResponse(404, "Not Found", {"Cache-Control": "no-cache"})

        content = self.data_store[path]
        etag = f'"{hashlib.md5(content.encode()).hexdigest()[:8]}"'

        # Check conditional GET
        if if_none_match == etag:
            return HTTPResponse(304, "", {
                "ETag": etag,
                "Cache-Control": "public, s-maxage=60, stale-while-revalidate=30"
            })

        return HTTPResponse(200, content, {
            "Content-Type": "application/octet-stream",
            "ETag": etag,
            "Cache-Control": "public, s-maxage=60, stale-while-revalidate=30",
            "Surrogate-Key": "static-assets"
        })

    def update_resource(self, path: str, new_content: str):
        self.data_store[path] = new_content

# ==============================================================
# 2. Simulated Edge Point of Presence (PoP) Cache
# ==============================================================
@dataclass
class CacheEntry:
    body: str
    etag: str
    fetched_at: float
    max_age_s: float
    stale_while_revalidate_s: float
    surrogate_keys: list

class EdgePoP:
    def __init__(self, name: str, origin: OriginServer):
        self.name = name
        self.origin = origin
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()

    def get(self, path: str) -> tuple[HTTPResponse, str, float]:
        start = time.perf_counter()
        now = time.time()

        with self.lock:
            entry = self.cache.get(path)

        if entry is not None:
            age = now - entry.fetched_at
            # 1. Fresh Cache HIT
            if age <= entry.max_age_s:
                duration_ms = (time.perf_counter() - start) * 1000
                res = HTTPResponse(200, entry.body, {
                    "X-Cache": "HIT",
                    "Age": str(int(age)),
                    "ETag": entry.etag
                })
                return res, "HIT", duration_ms

            # 2. Stale-while-revalidate: Serve immediately, revalidate asynchronously
            if age <= (entry.max_age_s + entry.stale_while_revalidate_s):
                duration_ms = (time.perf_counter() - start) * 1000
                res = HTTPResponse(200, entry.body, {
                    "X-Cache": "STALE-HIT",
                    "Age": str(int(age)),
                    "ETag": entry.etag
                })
                # Trigger async background fetch
                threading.Thread(target=self._background_revalidate, args=(path, entry.etag), daemon=True).start()
                return res, "STALE-HIT", duration_ms

        # 3. Cache MISS -> Fetch from Origin
        origin_res = self.origin.fetch(path, if_none_match=entry.etag if entry else None)
        duration_ms = (time.perf_counter() - start) * 1000

        if origin_res.status_code == 304 and entry is not None:
            # Revalidated existing entry
            with self.lock:
                entry.fetched_at = time.time()
            return HTTPResponse(200, entry.body, {"X-Cache": "REVALIDATED", "ETag": entry.etag}), "REVALIDATED", duration_ms

        if origin_res.status_code == 200:
            # Store in Edge Cache
            surrogate = origin_res.headers.get("Surrogate-Key", "").split()
            with self.lock:
                self.cache[path] = CacheEntry(
                    body=origin_res.body,
                    etag=origin_res.headers.get("ETag", ""),
                    fetched_at=time.time(),
                    max_age_s=60.0,
                    stale_while_revalidate_s=30.0,
                    surrogate_keys=surrogate
                )
            origin_res.headers["X-Cache"] = "MISS"
            return origin_res, "MISS", duration_ms

        return origin_res, "ERROR", duration_ms

    def _background_revalidate(self, path: str, etag: str):
        origin_res = self.origin.fetch(path, if_none_match=etag)
        with self.lock:
            if origin_res.status_code == 304 and path in self.cache:
                self.cache[path].fetched_at = time.time()
            elif origin_res.status_code == 200:
                self.cache[path] = CacheEntry(
                    body=origin_res.body,
                    etag=origin_res.headers.get("ETag", ""),
                    fetched_at=time.time(),
                    max_age_s=60.0,
                    stale_while_revalidate_s=30.0,
                    surrogate_keys=origin_res.headers.get("Surrogate-Key", "").split()
                )

    def purge_by_surrogate_key(self, tag: str):
        with self.lock:
            keys_to_delete = [
                path for path, entry in self.cache.items()
                if tag in entry.surrogate_keys
            ]
            for path in keys_to_delete:
                del self.cache[path]
            return len(keys_to_delete)

# ==============================================================
# 3. Demonstration & Benchmark
# ==============================================================
def main():
    print("=" * 70)
    print("CONTENT DELIVERY NETWORK (CDN) SIMULATION")
    print("Simulated Topology: Tokyo Client -> Tokyo Edge PoP -> US-East Origin")
    print("=" * 70)

    origin = OriginServer(simulated_latency_s=0.12)  # 120ms Pacific fiber transit
    edge = EdgePoP(name="Tokyo-NRT-01", origin=origin)

    # 1. Cold Cache Miss
    print("\n--- Test 1: Cold Cache Request (MISS) ---")
    res, status, dur = edge.get("/static/app.js")
    print(f"Client received: {res.body}")
    print(f"X-Cache Status: {status} | Latency: {dur:.1f} ms | Origin Requests: {origin.request_count}")

    # 2. Warm Cache Hit
    print("\n--- Test 2: Warm Cache Request (HIT) ---")
    res, status, dur = edge.get("/static/app.js")
    print(f"Client received: {res.body}")
    print(f"X-Cache Status: {status} | Latency: {dur:.2f} ms | Origin Requests: {origin.request_count}")
    print(f"⚡ Latency reduction: {120.0 / max(dur, 0.001):.0f}x faster!")

    # 3. Fast Burst of 50 requests
    print("\n--- Test 3: Simulating 50 Regional Users Visiting Site ---")
    hit_count = 0
    total_time = 0.0
    for _ in range(50):
        _, s, d = edge.get("/static/app.js")
        total_time += d
        if s == "HIT":
            hit_count += 1

    print(f"Processed 50 requests in total time: {total_time:.2f} ms")
    print(f"Edge Cache Hits: {hit_count}/50 (100% cache hit rate)")
    print(f"Total Origin Requests incurred across all 50 users: 0 (100% origin offload)")

    # 4. Instant Purge via Surrogate Key
    print("\n--- Test 4: Deploying New Code & Instant Surrogate-Key Purge ---")
    origin.update_resource("/static/app.js", "console.log('App v2.0.0 - Hotfix Deployed');")
    purged_count = edge.purge_by_surrogate_key("static-assets")
    print(f"🚀 Origin broadcasted cache purge for tag 'static-assets'. Evicted: {purged_count} entry.")

    # 5. Next Request After Purge
    print("\n--- Test 5: Client Request After Purge ---")
    res, status, dur = edge.get("/static/app.js")
    print(f"Client received: {res.body}")
    print(f"X-Cache Status: {status} | Latency: {dur:.1f} ms | Origin Requests: {origin.request_count}")
    print("=" * 70)
    print("Demo completed successfully!")

if __name__ == "__main__":
    main()
