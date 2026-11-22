"""
Interactive Demo: Cache Eviction (LRU) & Failure Modes Mitigation
Run this script to observe O(1) LRU eviction, and how Mutex Locks (Singleflight)
prevent catastrophic Cache Stampedes (Thundering Herds).
"""

import time
import random
import threading

# ==============================================================
# 1. Thread-Safe O(1) LRU Cache Implementation
# ==============================================================
class Node:
    def __init__(self, key: str, val: str):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int = 3):
        self.capacity = capacity
        self.map = {}
        # Dummy head and tail nodes
        self.head = Node("HEAD", "")
        self.tail = Node("TAIL", "")
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: str):
        if key in self.map:
            node = self.map[key]
            # Move accessed node to head (Most Recently Used)
            self._remove(node)
            self._add_to_front(node)
            return node.val
        return None

    def put(self, key: str, val: str):
        if key in self.map:
            self._remove(self.map[key])
        elif len(self.map) >= self.capacity:
            # Evict Least Recently Used (tail.prev)
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
            print(f"  🗑️ [EVICTED] Cache full! Evicted LRU key: '{lru.key}'")

        new_node = Node(key, val)
        self._add_to_front(new_node)
        self.map[key] = new_node

    def current_keys_order(self):
        curr = self.head.next
        keys = []
        while curr != self.tail:
            keys.append(curr.key)
            curr = curr.next
        return keys

# ==============================================================
# 2. Cache Stampede (Thundering Herd) Simulation
# ==============================================================
def simulate_stampede():
    db_query_count = 0
    cache = {}
    lock = threading.Lock()

    def simulate_heavy_db_query(key):
        nonlocal db_query_count
        db_query_count += 1
        time.sleep(0.05)  # Simulate 50ms expensive DB calculation
        return "Hot World Cup Score: 2 - 1"

    def worker_without_mutex(thread_id):
        # All 5 threads miss cache simultaneously and hit DB!
        if "world_cup_score" not in cache:
            val = simulate_heavy_db_query("world_cup_score")
            cache["world_cup_score"] = val

    def worker_with_singleflight(thread_id):
        # Thread 1 acquires lock; others wait and read cached result!
        if "world_cup_score_locked" not in cache:
            with lock:
                # Double-check inside lock
                if "world_cup_score_locked" not in cache:
                    val = simulate_heavy_db_query("world_cup_score_locked")
                    cache["world_cup_score_locked"] = val

    print("\n" + "=" * 70)
    print(" 🚨 SIMULATION A: Cache Stampede WITHOUT Mutex (10 Concurrent Threads)")
    print("=" * 70)
    db_query_count = 0
    threads = [threading.Thread(target=worker_without_mutex, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  💥 DISASTER: 10 simultaneous threads made {db_query_count} redundant DB queries! (Thundering Herd)")

    print("\n" + "=" * 70)
    print(" 🛡️ SIMULATION B: Cache Stampede WITH Mutex / Singleflight Lock")
    print("=" * 70)
    db_query_count = 0
    threads = [threading.Thread(target=worker_with_singleflight, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  ✅ SUCCESS: 10 simultaneous threads made ONLY {db_query_count} DB query! Remaining 9 threads read cached result.")

if __name__ == "__main__":
    print("=" * 70)
    print(" ⚡ PART 1: O(1) LRU CACHE EVICTION LIFECYCLE (Capacity = 3)")
    print("=" * 70)
    lru = LRUCache(capacity=3)

    print("Inserting 'A', 'B', 'C':")
    lru.put("A", "Data A")
    lru.put("B", "Data B")
    lru.put("C", "Data C")
    print("  Current order (MRU -> LRU):", lru.current_keys_order())

    print("\nAccessing key 'A' (should move to Head / MRU):")
    lru.get("A")
    print("  Current order (MRU -> LRU):", lru.current_keys_order())

    print("\nInserting key 'D' (Capacity exceeded! 'B' is now LRU):")
    lru.put("D", "Data D")
    print("  Current order (MRU -> LRU):", lru.current_keys_order())

    # Run stampede demonstration
    simulate_stampede()
    print("=" * 70)
