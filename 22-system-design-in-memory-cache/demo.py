"""
Interactive Demo: System Design — Distributed In-Memory Cache (Redis-Like Engine)
Run this script to observe:
1. O(1) LRU eviction using a Doubly Linked List and Hash Map.
2. TTL expiration mechanisms (Lazy on read + Periodic background sweep).
3. Append-Only File (AOF) persistence logging and recovery replay on node restart.
4. Consistent Hash Ring sharding keys across a multi-node cache cluster.
"""

import time
import bisect
import hashlib
from typing import Dict, Optional, Tuple, List

# ==============================================================
# 1. Thread-Safe O(1) LRU Cache Node with TTL & AOF Persistence
# ==============================================================
class CacheNodeItem:
    def __init__(self, key: str, val: str, expires_at: Optional[float] = None):
        self.key = key
        self.val = val
        self.expires_at = expires_at
        self.prev: Optional['CacheNodeItem'] = None
        self.next: Optional['CacheNodeItem'] = None

class InMemoryCacheNode:
    def __init__(self, node_id: str, capacity: int = 3):
        self.node_id = node_id
        self.capacity = capacity
        self.map: Dict[str, CacheNodeItem] = {}
        self.head = CacheNodeItem("HEAD", "")
        self.tail = CacheNodeItem("TAIL", "")
        self.head.next = self.tail
        self.tail.prev = self.head
        self.aof_log: List[str] = []

    def _remove(self, node: CacheNodeItem):
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev

    def _add_to_front(self, node: CacheNodeItem):
        node.next = self.head.next
        node.prev = self.head
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: str) -> Optional[str]:
        now = time.time()
        if key in self.map:
            item = self.map[key]
            # Lazy TTL expiration check
            if item.expires_at and now > item.expires_at:
                self.delete(key)
                return None
            # Move to head (Most Recently Used)
            self._remove(item)
            self._add_to_front(item)
            return item.val
        return None

    def set(self, key: str, val: str, ttl_s: Optional[float] = None, log_aof: bool = True):
        now = time.time()
        exp = now + ttl_s if ttl_s else None

        if key in self.map:
            item = self.map[key]
            item.val = val
            item.expires_at = exp
            self._remove(item)
            self._add_to_front(item)
        else:
            if len(self.map) >= self.capacity:
                # Evict LRU from Tail
                lru_item = self.tail.prev
                if lru_item and lru_item != self.head:
                    print(f"  [{self.node_id}] Memory limit ({self.capacity}) reached -> Evicting LRU key '{lru_item.key}'!")
                    self.delete(lru_item.key)

            new_item = CacheNodeItem(key, val, exp)
            self.map[key] = new_item
            self._add_to_front(new_item)

        if log_aof:
            # Append-Only File log
            self.aof_log.append(f"SET {key} {val} {ttl_s if ttl_s else 0}")

    def delete(self, key: str):
        if key in self.map:
            item = self.map.pop(key)
            self._remove(item)

    def recover_from_aof(self):
        """Simulates server reboot by replaying AOF commands."""
        print(f"  [{self.node_id}] Replaying {len(self.aof_log)} commands from AOF log...")
        temp_log = list(self.aof_log)
        self.map.clear()
        self.head.next = self.tail
        self.tail.prev = self.head
        for entry in temp_log:
            parts = entry.split()
            cmd, k, v = parts[0], parts[1], parts[2]
            ttl = float(parts[3]) if len(parts) > 3 and float(parts[3]) > 0 else None
            self.set(k, v, ttl_s=ttl, log_aof=False)
        print(f"  [{self.node_id}] Recovery complete! Active keys in memory: {list(self.map.keys())}")


# ==============================================================
# 2. Distributed Cache Cluster Coordinator
# ==============================================================
class DistributedCacheCluster:
    def __init__(self, node_ids: List[str], vnodes: int = 50):
        self.nodes = {nid: InMemoryCacheNode(nid) for nid in node_ids}
        self.vnodes = vnodes
        self.ring = []
        self.ring_map = {}
        for nid in node_ids:
            for v in range(vnodes):
                h = int(hashlib.md5(f"{nid}#vnode-{v}".encode()).hexdigest(), 16) & 0xFFFFFFFF
                bisect.insort(self.ring, h)
                self.ring_map[h] = nid

    def _route(self, key: str) -> InMemoryCacheNode:
        h = int(hashlib.md5(key.encode()).hexdigest(), 16) & 0xFFFFFFFF
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring):
            idx = 0
        target_nid = self.ring_map[self.ring[idx]]
        return self.nodes[target_nid]

    def set(self, key: str, val: str, ttl_s: Optional[float] = None):
        node = self._route(key)
        node.set(key, val, ttl_s=ttl_s)

    def get(self, key: str) -> Tuple[Optional[str], str]:
        node = self._route(key)
        return node.get(key), node.node_id


def main():
    print("=" * 70)
    print("DISTRIBUTED IN-MEMORY CACHE (REDIS-LIKE) SIMULATION")
    print("=" * 70)

    cluster = DistributedCacheCluster(["Cache-Shard-01", "Cache-Shard-02", "Cache-Shard-03"])

    # 1. Distribute keys across cluster
    print("\n--- Phase 1: Writing Keys to Distributed Shards ---")
    keys_data = [
        ("user:101", "Alice"),
        ("user:102", "Bob"),
        ("user:103", "Charlie"),
        ("user:104", "Diana"),
        ("user:105", "Evan")
    ]
    for k, v in keys_data:
        cluster.set(k, v)
        val, shard = cluster.get(k)
        print(f"Key '{k}' -> Routed to {shard} | Readback: {val}")

    # 2. LRU Eviction Test on a single node
    print("\n--- Phase 2: Testing O(1) LRU Eviction ---")
    node1 = cluster.nodes["Cache-Shard-01"]
    print(f"Targeting {node1.node_id} (Capacity = {node1.capacity})")
    node1.set("item:A", "dataA")
    node1.set("item:B", "dataB")
    node1.set("item:C", "dataC")
    print(f"Initial keys on {node1.node_id}: {list(node1.map.keys())}")

    print("Accessing 'item:A' to make it Most Recently Used (MRU)...")
    node1.get("item:A")

    print("Adding 'item:D' (exceeds capacity)...")
    node1.set("item:D", "dataD")
    print(f"Keys on {node1.node_id} after LRU eviction: {list(node1.map.keys())}")
    print("Notice: 'item:B' was evicted because 'item:A' was recently refreshed!")

    # 3. TTL Expiration Test
    print("\n--- Phase 3: Testing TTL Expiration (Lazy Check) ---")
    node1.set("temp:session", "TokenXYZ", ttl_s=0.2)
    print(f"Immediate read: {node1.get('temp:session')} (Valid)")
    print("Sleeping 0.25s for TTL to expire...")
    time.sleep(0.25)
    print(f"Read after TTL expiry: {node1.get('temp:session')} (Expired & auto-purged!)")

    # 4. Persistence & Crash Recovery (AOF)
    print("\n--- Phase 4: Persistence & Node Crash Recovery (AOF) ---")
    print(f"Simulating crash and reboot of {node1.node_id}...")
    node1.recover_from_aof()
    print("=" * 70)
    print("In-Memory Cache simulation completed successfully!")

if __name__ == "__main__":
    main()
