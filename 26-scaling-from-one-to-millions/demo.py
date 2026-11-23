"""
Interactive Demo: Scaling from One to Millions of Users
Simulates the evolutionary progression of scaling a web system:
1. Single-Server Monolith collapsing under concurrency.
2. Adding In-Memory Cache (Redis) absorbing read traffic.
3. Adding Load Balancer distributing load across multiple stateless workers.
"""

import time
import random
from typing import List, Dict

class SingleServerMonolith:
    """Stage 1: Single box running application logic and slow disk database queries."""
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.active_requests = 0

    def handle_request(self, user_id: str) -> bool:
        if self.active_requests >= self.max_concurrent:
            return False  # 503 Service Unavailable / Connection Dropped
        self.active_requests += 1
        # Simulate slow DB disk seek (15ms)
        time.sleep(0.015)
        self.active_requests -= 1
        return True

class ScaledArchitecture:
    """Stage 5+: Load Balancer + Stateless Web Fleet + Redis Cache Tier."""
    def __init__(self, worker_count: int = 4):
        self.workers = worker_count
        self.cache: Dict[str, str] = {}
        self.db: Dict[str, str] = {f"user_{i}": f"Profile Data for {i}" for i in range(100)}
        self.db_queries = 0
        self.cache_hits = 0

    def handle_request(self, user_id: str) -> str:
        # 1. Check in-memory Cache (Redis)
        if user_id in self.cache:
            self.cache_hits += 1
            return self.cache[user_id]
        
        # 2. Cache Miss -> Query Database
        self.db_queries += 1
        time.sleep(0.005)  # DB query latency
        data = self.db.get(user_id, "Not Found")
        self.cache[user_id] = data
        return data

def run_simulation():
    print("=" * 65)
    print("STAGE 1: SINGLE-SERVER MONOLITH UNDER LOAD (50 Concurrent Requests)")
    print("=" * 65)
    monolith = SingleServerMonolith(max_concurrent=5)
    dropped = 0
    success = 0
    
    for i in range(50):
        # Simulate burst traffic
        monolith.active_requests = random.randint(1, 8)
        if monolith.handle_request(f"user_{i}"):
            success += 1
        else:
            dropped += 1
            
    print(f"Total Requests: 50 | Succeeded: {success} | Dropped: {dropped}")
    print(f"Failure Rate: {(dropped / 50) * 100:.1f}% -> Single server crashed!")

    print("\n" + "=" * 65)
    print("STAGE 5+: SCALED ARCHITECTURE (Load Balancer + Cache Tier)")
    print("=" * 65)
    scaled = ScaledArchitecture(worker_count=4)
    
    # Simulate 100 requests requesting a set of 10 hot users
    for _ in range(100):
        hot_user = f"user_{random.randint(0, 9)}"
        scaled.handle_request(hot_user)
        
    print("Total Requests Processed: 100")
    print(f"Cache Hits (Sub-millisecond RAM): {scaled.cache_hits}")
    print(f"Database Queries (Disk I/O): {scaled.db_queries}")
    cache_hit_rate = (scaled.cache_hits / 100) * 100
    print(f"Cache Offload Efficiency: {cache_hit_rate:.1f}% DB Load Eliminated!")

if __name__ == "__main__":
    run_simulation()
