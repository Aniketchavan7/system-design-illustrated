"""
Interactive Demo: Consistent Hashing & Virtual Nodes Simulation
Run this script to observe:
1. Traditional Modulo Hashing vs Consistent Hashing during cluster scaling (N=4 -> N=5).
2. Key remapping percentages: Why Modulo hashing causes catastrophic cache stampedes (80% invalidated)
   while Consistent Hashing remaps only ~20% of keys.
3. The impact of Virtual Nodes (V-nodes) in eliminating hot spots and balancing load uniformly.
"""

import hashlib
import bisect
from typing import List, Dict

# ==============================================================
# 1. Consistent Hash Ring Implementation with Virtual Nodes
# ==============================================================
class ConsistentHashRing:
    def __init__(self, nodes: List[str] = None, vnodes_per_node: int = 150):
        self.vnodes_per_node = vnodes_per_node
        self.ring: List[int] = []  # Sorted list of virtual node hashes
        self.hash_to_node: Dict[int, str] = {}  # hash -> physical node name
        self.nodes = set()

        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key: str) -> int:
        # MD5 32-bit integer hash for uniform circular distribution
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFF

    def add_node(self, node: str):
        self.nodes.add(node)
        for i in range(self.vnodes_per_node):
            v_key = f"{node}#vnode-{i}"
            h = self._hash(v_key)
            self.hash_to_node[h] = node
            bisect.insort(self.ring, h)

    def remove_node(self, node: str):
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        new_ring = []
        for h in self.ring:
            if self.hash_to_node[h] == node:
                del self.hash_to_node[h]
            else:
                new_ring.append(h)
        self.ring = new_ring

    def get_node(self, key: str) -> str:
        if not self.ring:
            raise ValueError("Ring is empty!")
        h = self._hash(key)
        # Binary search for the first node clockwise (>= hash)
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring):
            idx = 0  # Wrap around to start of ring
        return self.hash_to_node[self.ring[idx]]

# ==============================================================
# 2. Modulo Hashing Implementation
# ==============================================================
class ModuloCluster:
    def __init__(self, nodes: List[str]):
        self.nodes = list(nodes)

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFF

    def get_node(self, key: str) -> str:
        idx = self._hash(key) % len(self.nodes)
        return self.nodes[idx]

    def add_node(self, node: str):
        self.nodes.append(node)


def main():
    print("=" * 70)
    print("CONSISTENT HASHING & VIRTUAL NODES BENCHMARK")
    print("=" * 70)

    keys = [f"user_session:{i}" for i in range(10000)]
    initial_nodes = ["Node-A", "Node-B", "Node-C", "Node-4"]

    # ---------------------------------------------------------
    # Test 1: Cluster Scaling Remap Test (N = 4 -> N = 5)
    # ---------------------------------------------------------
    print("\n--- Test 1: Cluster Scale-Out Remapping Test (4 Nodes -> 5 Nodes) ---")
    
    # Modulo Hashing
    mod = ModuloCluster(initial_nodes)
    mod_mapping_before = {k: mod.get_node(k) for k in keys}
    mod.add_node("Node-5")
    mod_remapped = sum(1 for k in keys if mod.get_node(k) != mod_mapping_before[k])
    print(f"Traditional Modulo (hash % N):")
    print(f"  Total Keys Remapped: {mod_remapped} / 10,000 ({mod_remapped / 100:.1f}%)")
    print(f"  💥 Cache Invalidation Rate: {mod_remapped / 100:.1f}% (Causes Severe Cache Stampede!)")

    # Consistent Hashing (V-Nodes = 150)
    ring = ConsistentHashRing(initial_nodes, vnodes_per_node=150)
    ring_mapping_before = {k: ring.get_node(k) for k in keys}
    ring.add_node("Node-5")
    ring_remapped = sum(1 for k in keys if ring.get_node(k) != ring_mapping_before[k])
    print(f"\nConsistent Hashing Ring (with 150 V-nodes):")
    print(f"  Total Keys Remapped: {ring_remapped} / 10,000 ({ring_remapped / 100:.1f}%)")
    print(f"  ✅ Cache Preserved: {100.0 - (ring_remapped / 100):.1f}% of cache intact!")
    print(f"  Theoretical minimum remapping (1/N): {100.0 / 5:.1f}%")

    # ---------------------------------------------------------
    # Test 2: The Critical Value of Virtual Nodes (Load Balance)
    # ---------------------------------------------------------
    print("\n--- Test 2: Key Distribution With vs Without Virtual Nodes ---")
    
    # Without Virtual Nodes (1 token per node)
    ring_no_vnodes = ConsistentHashRing(initial_nodes, vnodes_per_node=1)
    counts_no_vnodes = {n: 0 for n in initial_nodes}
    for k in keys:
        counts_no_vnodes[ring_no_vnodes.get_node(k)] += 1

    print("\nKey Distribution WITHOUT Virtual Nodes (1 token / node):")
    for n, count in sorted(counts_no_vnodes.items()):
        print(f"  {n}: {count:5d} keys ({count / 100:.1f}%)")
    max_no = max(counts_no_vnodes.values())
    min_no = min(counts_no_vnodes.values())
    print(f"  ⚠️ Variance: Heaviest node has {max_no/min_no:.1f}x the load of the lightest node (Severe Hot Spot)!")

    # With 150 Virtual Nodes
    ring_vnodes = ConsistentHashRing(initial_nodes, vnodes_per_node=150)
    counts_vnodes = {n: 0 for n in initial_nodes}
    for k in keys:
        counts_vnodes[ring_vnodes.get_node(k)] += 1

    print("\nKey Distribution WITH Virtual Nodes (150 tokens / node):")
    for n, count in sorted(counts_vnodes.items()):
        print(f"  {n}: {count:5d} keys ({count / 100:.1f}%)")
    max_v = max(counts_vnodes.values())
    min_v = min(counts_vnodes.values())
    print(f"  ✅ Near-Perfect Balance: Heaviest node has only {max_v/min_v:.2f}x the load of lightest node.")

    print("=" * 70)
    print("Benchmark completed successfully!")

if __name__ == "__main__":
    main()
