"""
Interactive Demo: Time, Clocks & Ordering in Distributed Systems
Simulates:
1. Physical NTP Clock Skew causing Last-Write-Wins (LWW) silent data loss.
2. Lamport Timestamps establishing monotonic causal event ordering.
3. Vector Clocks detecting concurrent write conflicts vs causal progression.
"""

import time
from typing import Dict, List, Tuple

class LamportClockNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.clock = 0

    def local_event(self) -> int:
        self.clock += 1
        return self.clock

    def send_message(self) -> int:
        self.clock += 1
        return self.clock

    def receive_message(self, remote_clock: int) -> int:
        self.clock = max(self.clock, remote_clock) + 1
        return self.clock

class VectorClockNode:
    def __init__(self, node_id: str, cluster_nodes: List[str]):
        self.node_id = node_id
        self.vector: Dict[str, int] = {n: 0 for n in cluster_nodes}

    def local_event(self) -> Dict[str, int]:
        self.vector[self.node_id] += 1
        return self.vector.copy()

    def send_message(self) -> Dict[str, int]:
        self.vector[self.node_id] += 1
        return self.vector.copy()

    def receive_message(self, remote_vector: Dict[str, int]) -> Dict[str, int]:
        for n, val in remote_vector.items():
            self.vector[n] = max(self.vector[n], val)
        self.vector[self.node_id] += 1
        return self.vector.copy()

    @staticmethod
    def compare(v1: Dict[str, int], v2: Dict[str, int]) -> str:
        """Returns 'CAUSAL_BEFORE', 'CAUSAL_AFTER', or 'CONCURRENT_CONFLICT'."""
        v1_le = all(v1[k] <= v2[k] for k in v1)
        v2_le = all(v2[k] <= v1[k] for k in v1)
        if v1_le and not v2_le:
            return "V1 HAPPENED BEFORE V2"
        elif v2_le and not v1_le:
            return "V2 HAPPENED BEFORE V1"
        elif v1 == v2:
            return "IDENTICAL"
        else:
            return "CONCURRENT CONFLICT DETECTED!"

def run_simulation():
    print("=" * 65)
    print("1. SIMULATING NTP CLOCK SKEW & LAST-WRITE-WINS (LWW) DATA LOSS")
    print("=" * 65)
    
    # Server A's clock is 100ms slow!
    server_a_clock = 1000  # ms
    server_b_clock = 1200  # ms (Ahead by 200ms)

    # Real-world Event 1 occurs at Server B
    event_1 = {"server": "B", "value": "Initial State", "time": server_b_clock}
    print(f"Time 1: Server B writes: '{event_1['value']}' with timestamp {event_1['time']}")

    # Real-world Event 2 occurs AFTER Event 1 at Server A
    event_2 = {"server": "A", "value": "Updated State", "time": server_a_clock + 50}
    print(f"Time 2: Server A writes: '{event_2['value']}' with timestamp {event_2['time']}")

    # In Cassandra / LWW resolution:
    winning_event = event_1 if event_1["time"] > event_2["time"] else event_2
    print(f"LWW Winning Record: '{winning_event['value']}' (from Server {winning_event['server']})")
    print("💥 DATA LOSS DISASTER: Server A's newer write was discarded due to clock skew!")

    print("\n" + "=" * 65)
    print("2. LAMPORT TIMESTAMPS: GUARANTEEING MONOTONIC CAUSALITY")
    print("=" * 65)
    node_a = LamportClockNode("A")
    node_b = LamportClockNode("B")

    c1 = node_a.local_event()
    print(f"Node A local event -> Clock = {c1}")
    msg_clock = node_a.send_message()
    print(f"Node A sends message to B with attached Clock = {msg_clock}")
    
    c2 = node_b.receive_message(msg_clock)
    print(f"Node B receives message -> Clock = max(0, {msg_clock}) + 1 = {c2}")
    print(f"Causality preserved: {c1} -> {msg_clock} -> {c2}")

    print("\n" + "=" * 65)
    print("3. VECTOR CLOCKS: DETECTING CONCURRENT WRITE CONFLICTS")
    print("=" * 65)
    nodes = ["NodeA", "NodeB"]
    v_a = VectorClockNode("NodeA", nodes)
    v_b = VectorClockNode("NodeB", nodes)

    # Both nodes perform independent local writes concurrently
    clock_a = v_a.local_event()
    clock_b = v_b.local_event()
    print(f"Node A independent write vector: {clock_a}")
    print(f"Node B independent write vector: {clock_b}")

    relationship = VectorClockNode.compare(clock_a, clock_b)
    print(f"Comparison Result: {relationship}")
    print("SUCCESS: Vector clocks mathematically proved these writes conflicted!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
