"""
Interactive Demo: Distributed Consistency Models in Action
Run this script to observe:
1. Eventual Consistency Anomalies (Stale reads and Time-Travel back into the past).
2. Client-Centric Session Guarantees:
   - Read-Your-Own-Writes (RYOW)
   - Monotonic Reads (preventing backwards time travel)
3. Causal Consistency:
   - Preserving causal ordering ("Question" must appear before "Answer") using logical timestamps.
"""

import time
from typing import Dict, List, Optional, Tuple

class ReplicaNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        # key -> (value, version_ts, causal_parent_id)
        self.data: Dict[str, Tuple[str, int, Optional[str]]] = {}
        self.pending_causal_buffer: List[Tuple[str, str, int, Optional[str]]] = []

    def apply_write(self, key: str, value: str, version: int, parent_id: Optional[str] = None):
        # If write depends on a parent that isn't applied yet, buffer it (Causal consistency)
        if parent_id and parent_id not in self.data:
            self.pending_causal_buffer.append((key, value, version, parent_id))
            return False

        self.data[key] = (value, version, parent_id)
        self._flush_causal_buffer()
        return True

    def _flush_causal_buffer(self):
        applied_any = True
        while applied_any:
            applied_any = False
            for item in list(self.pending_causal_buffer):
                k, v, ver, pid = item
                if pid in self.data:
                    self.data[k] = (v, ver, pid)
                    self.pending_causal_buffer.remove(item)
                    applied_any = True

    def read(self, key: str) -> Optional[Tuple[str, int]]:
        if key in self.data:
            val, ver, _ = self.data[key]
            return val, ver
        return None


class ConsistencyCluster:
    def __init__(self):
        self.replicas = {
            "Replica-1": ReplicaNode("Replica-1"),
            "Replica-2": ReplicaNode("Replica-2"),
            "Replica-3": ReplicaNode("Replica-3")
        }
        self.global_version = 0

    # -------------------------------------------------------------
    # 1. Eventual Write (Only updates Replica-1 initially, simulates lag)
    # -------------------------------------------------------------
    def write_eventual(self, key: str, value: str) -> int:
        self.global_version += 1
        ver = self.global_version
        self.replicas["Replica-1"].apply_write(key, value, ver)
        return ver

    def sync_replica(self, target_replica: str, key: str):
        if key in self.replicas["Replica-1"].data:
            val, ver, pid = self.replicas["Replica-1"].data[key]
            self.replicas[target_replica].apply_write(key, val, ver, pid)

    # -------------------------------------------------------------
    # 2. Monotonic Read Guarantee
    # -------------------------------------------------------------
    def monotonic_read(self, key: str, last_seen_version: int, replica_order: List[str]) -> Tuple[str, int]:
        for r_name in replica_order:
            result = self.replicas[r_name].read(key)
            if result is not None:
                val, ver = result
                # Enforce: Never return a version older than what client already saw!
                if ver >= last_seen_version:
                    return val, ver
        # If requested replica is stale, fall back to leading replica
        return self.replicas["Replica-1"].read(key)


def main():
    print("=" * 70)
    print("DISTRIBUTED CONSISTENCY MODELS SIMULATION")
    print("Replicas: [Replica-1 (Primary), Replica-2 (Lagging), Replica-3 (Lagging)]")
    print("=" * 70)

    cluster = ConsistencyCluster()

    # ---------------------------------------------------------
    # Scenario 1: The Eventual Consistency "Time Travel" Anomaly
    # ---------------------------------------------------------
    print("\n--- 1. Eventual Consistency Anomaly: Time-Travel Reads ---")
    ver1 = cluster.write_eventual("user:123:status", "OFFLINE")
    cluster.sync_replica("Replica-2", "user:123:status")
    cluster.sync_replica("Replica-3", "user:123:status")
    print("Initial state synced across all nodes: 'OFFLINE' (Version 1)")

    # User updates status to ONLINE
    print("\nUser updates status to 'ONLINE'...")
    ver2 = cluster.write_eventual("user:123:status", "ONLINE")
    # Replica-1 has 'ONLINE', but Replica-2 and Replica-3 are lagging behind!

    # Client queries round-robin without monotonic read guarantees
    read1, _ = cluster.replicas["Replica-1"].read("user:123:status")
    print(f"Request 1 hits Replica-1: Status = '{read1}' (Latest!)")

    read2, _ = cluster.replicas["Replica-2"].read("user:123:status")
    print(f"Request 2 hits Replica-2: Status = '{read2}' (💥 TIME TRAVEL! User sees old state!)")

    # ---------------------------------------------------------
    # Scenario 2: Monotonic Reads (Session Guarantee)
    # ---------------------------------------------------------
    print("\n--- 2. Fix: Monotonic Reads (Client Session Tokens) ---")
    client_last_seen = 2  # Client knows they already observed version 2

    print(f"Client requests with session header: `X-Last-Seen-Version: {client_last_seen}`")
    val, ver = cluster.monotonic_read("user:123:status", client_last_seen, ["Replica-2", "Replica-3"])
    print(f"Cluster rejected stale replicas and served: '{val}' (Version {ver})")
    print("✅ Backward time-travel prevented!")

    # ---------------------------------------------------------
    # Scenario 3: Causal Consistency (Chat Thread Ordering)
    # ---------------------------------------------------------
    print("\n--- 3. Causal Consistency: Preserving Cause & Effect ---")
    print("Bob asks: 'Did you get the job?' (Event ID: Q1)")
    cluster.replicas["Replica-1"].apply_write("msg:Q1", "Did you get the job?", 10, parent_id=None)

    print("Alice replies: 'Yes, I start Monday!' (Event ID: A1, Causal Parent: Q1)")
    # Alice's answer causally depends on Bob's question!
    cluster.replicas["Replica-1"].apply_write("msg:A1", "Yes, I start Monday!", 11, parent_id="msg:Q1")

    # Due to network race, Replica-3 receives Answer A1 BEFORE Question Q1!
    print("\n⚡ Network Race: Replica-3 receives Answer A1 before Question Q1!")
    applied = cluster.replicas["Replica-3"].apply_write("msg:A1", "Yes, I start Monday!", 11, parent_id="msg:Q1")
    print(f"Replica-3 causal check: Parent 'msg:Q1' missing? -> Buffered: {not applied}")
    print(f"Replica-3 current visible state: {cluster.replicas['Replica-3'].data.keys()}")

    print("\nNow Question Q1 arrives at Replica-3...")
    cluster.replicas["Replica-3"].apply_write("msg:Q1", "Did you get the job?", 10, parent_id=None)
    print(f"Replica-3 auto-flushed buffer! Keys now visible: {list(cluster.replicas['Replica-3'].data.keys())}")
    print("✅ Question and Answer rendered in strict causal order! No causality violation.")

    print("=" * 70)
    print("Simulation finished successfully!")

if __name__ == "__main__":
    main()
