"""
Interactive Demo: CAP and PACELC Theorems Simulation
Run this script to observe:
1. Normal healthy cluster operation under CP vs AP configurations.
2. The impact of a network partition (P) on a 3-node cluster.
3. CP behavior: Strict quorum requirement rejects writes in minority partitions.
4. AP behavior: Minority node accepts writes, causing divergence, followed by LWW healing.
5. PACELC Else-Latency (EL) benchmark: Sync replication latency vs Async replication latency.
"""

import time
from typing import Dict, List, Optional, Tuple

class DistributedNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.store: Dict[str, Tuple[str, float]] = {}  # key -> (value, timestamp)

    def write_local(self, key: str, value: str, ts: Optional[float] = None) -> float:
        commit_ts = ts if ts is not None else time.time()
        self.store[key] = (value, commit_ts)
        return commit_ts

    def read_local(self, key: str) -> Optional[Tuple[str, float]]:
        return self.store.get(key)


class DistributedCluster:
    def __init__(self, node_ids: List[str]):
        self.nodes = {nid: DistributedNode(nid) for nid in node_ids}
        # Adjacency matrix for network connectivity
        self.partitions: Dict[str, set[str]] = {nid: set(node_ids) for nid in node_ids}

    def sever_network(self, group1: List[str], group2: List[str]):
        """Isolate group1 from group2 (Network Partition)."""
        for n1 in group1:
            for n2 in group2:
                self.partitions[n1].discard(n2)
                self.partitions[n2].discard(n1)

    def heal_network(self):
        """Restore all network links."""
        all_nodes = set(self.nodes.keys())
        for nid in self.nodes:
            self.partitions[nid] = set(all_nodes)

    # ---------------------------------------------------------
    # CP Mode: Strict Majority Quorum (R + W > N, W >= 2 in 3 nodes)
    # ---------------------------------------------------------
    def write_cp(self, target_node: str, key: str, value: str) -> Tuple[bool, str]:
        connected_nodes = self.partitions[target_node]
        quorum_size = (len(self.nodes) // 2) + 1  # 2 out of 3

        if len(connected_nodes) < quorum_size:
            return False, f"CP Quorum Failed! Node {target_node} can only reach {len(connected_nodes)} nodes (Quorum needs {quorum_size}). WRITE REJECTED."

        # Commit to all reachable nodes
        commit_ts = time.time()
        for nid in connected_nodes:
            self.nodes[nid].write_local(key, value, commit_ts)

        return True, f"CP Write Committed successfully across {len(connected_nodes)} nodes (Majority Quorum met)."

    # ---------------------------------------------------------
    # AP Mode: High Availability (Accept local, async sync)
    # ---------------------------------------------------------
    def write_ap(self, target_node: str, key: str, value: str) -> Tuple[bool, str]:
        commit_ts = time.time()
        # Always write to local target node
        self.nodes[target_node].write_local(key, value, commit_ts)
        # Try best-effort async push to connected peers
        connected_nodes = self.partitions[target_node]
        for nid in connected_nodes:
            if nid != target_node:
                self.nodes[nid].write_local(key, value, commit_ts)

        return True, f"AP Write Accepted on Node {target_node} at timestamp {commit_ts:.4f}. Status: 200 OK."

    # ---------------------------------------------------------
    # Conflict Resolution: Last-Write-Wins (LWW)
    # ---------------------------------------------------------
    def reconcile_lww(self, key: str):
        latest_val = None
        latest_ts = -1.0

        for nid, node in self.nodes.items():
            record = node.read_local(key)
            if record and record[1] > latest_ts:
                latest_val = record[0]
                latest_ts = record[1]

        if latest_val is not None:
            for nid, node in self.nodes.items():
                node.write_local(key, latest_val, latest_ts)


def main():
    print("=" * 70)
    print("CAP & PACELC THEOREMS: DISTRIBUTED SIMULATION")
    print("Cluster Topology: 3 Nodes [Node-A, Node-B, Node-C]")
    print("=" * 70)

    cluster = DistributedCluster(["Node-A", "Node-B", "Node-C"])

    # 1. Healthy State Operation
    print("\n--- Phase 1: Normal Network Operation (No Partition) ---")
    ok, msg = cluster.write_cp("Node-A", "balance", "$100")
    print(f"Write to Node-A: {msg}")
    print(f"Reading from Node-B: {cluster.nodes['Node-B'].read_local('balance')[0]}")
    print(f"Reading from Node-C: {cluster.nodes['Node-C'].read_local('balance')[0]}")

    # 2. Inject Network Partition: Node-C isolated
    print("\n--- Phase 2: Injecting Network Partition (P) ---")
    print("⚡ Fiber cut: [Node-A, Node-B] (Majority) <--- X ---> [Node-C] (Minority)")
    cluster.sever_network(["Node-A", "Node-B"], ["Node-C"])

    # Test CP Mode in Minority
    print("\n[CP System Evaluation under Partition]")
    ok, msg = cluster.write_cp("Node-C", "balance", "$200")
    print(f"Write attempt to isolated Node-C: {msg}")

    ok, msg = cluster.write_cp("Node-A", "balance", "$150")
    print(f"Write attempt to majority Node-A: {msg}")

    # Test AP Mode in Minority
    print("\n[AP System Evaluation under Partition]")
    ok, msg = cluster.write_ap("Node-C", "status", "ONLINE_IN_ISOLATION")
    print(f"Write to isolated Node-C: {msg}")
    print(f"Node-C sees status = '{cluster.nodes['Node-C'].read_local('status')[0]}'")
    print(f"Node-A sees status = '{cluster.nodes['Node-A'].read_local('status')}' (Divergence!)")

    # 3. Heal Partition & Reconcile
    print("\n--- Phase 3: Healing Partition & LWW Reconciliation ---")
    cluster.heal_network()
    print("Network connectivity fully restored. Running Last-Write-Wins (LWW) anti-entropy...")
    cluster.reconcile_lww("status")
    print(f"Node-A reconciled status: {cluster.nodes['Node-A'].read_local('status')[0]}")
    print(f"Node-C reconciled status: {cluster.nodes['Node-C'].read_local('status')[0]}")

    # 4. PACELC Latency Comparison (When Healthy)
    print("\n--- Phase 4: PACELC (Else: Latency vs Consistency) ---")
    print("In absence of partition: Do you want ultra-low latency or immediate sync consistency?")
    
    # Latency: Async write
    t0 = time.perf_counter()
    cluster.write_ap("Node-A", "counter", "1")
    t_async = (time.perf_counter() - t0) * 1000

    # Latency: Sync quorum write
    t0 = time.perf_counter()
    cluster.write_cp("Node-A", "counter", "2")
    t_sync = (time.perf_counter() - t0) * 1000

    print(f"PA/EL (Eventual Consistency / Async ACK) Local Latency: {t_async:.4f} ms")
    print(f"PC/EC (Strong Consistency / Sync Quorum ACK) Latency:    {t_sync:.4f} ms")
    print("=" * 70)
    print("Simulation finished successfully!")

if __name__ == "__main__":
    main()
