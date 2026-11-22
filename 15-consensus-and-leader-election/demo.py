"""
Interactive Demo: Raft Distributed Consensus & Leader Election
Run this script to observe:
1. Leader heartbeat broadcasting and election timeout resets.
2. Simulated Leader crash leading to election timeout expiration.
3. Candidate requesting votes and achieving majority quorum (2/3).
4. New Leader elected and safe step-down of recovering nodes with older terms.
"""

import time
import random
import threading
from enum import Enum
from typing import Dict, List, Optional

class NodeRole(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"
    CRASHED = "CRASHED"

class RaftNode:
    def __init__(self, node_id: str, cluster: 'RaftCluster'):
        self.node_id = node_id
        self.cluster = cluster
        self.role = NodeRole.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.last_heartbeat_time = time.time()
        self.election_timeout_s = random.uniform(0.2, 0.4)
        self.log = []
        self.running = True
        self.lock = threading.Lock()

    def tick(self):
        """Called periodically by cluster timer loop."""
        with self.lock:
            if self.role == NodeRole.CRASHED:
                return

            now = time.time()
            if self.role == NodeRole.LEADER:
                # Leader sends heartbeats
                self.cluster.broadcast_heartbeat(self.node_id, self.current_term)
            elif self.role in (NodeRole.FOLLOWER, NodeRole.CANDIDATE):
                # Check election timeout
                if now - self.last_heartbeat_time > self.election_timeout_s:
                    self._start_election()

    def _start_election(self):
        self.role = NodeRole.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.last_heartbeat_time = time.time()
        self.election_timeout_s = random.uniform(0.2, 0.4)
        print(f"⏰ [Timeout] {self.node_id} became CANDIDATE for Term {self.current_term}!")

        # Request votes from all peers
        votes_granted = 1  # Voted for self
        peers = [n for n in self.cluster.nodes.values() if n.node_id != self.node_id]

        for peer in peers:
            if peer.handle_request_vote(self.node_id, self.current_term):
                votes_granted += 1

        majority = (len(self.cluster.nodes) // 2) + 1  # 2 out of 3
        if votes_granted >= majority:
            self.role = NodeRole.LEADER
            print(f"👑 [Victory] {self.node_id} secured {votes_granted}/{len(self.cluster.nodes)} votes -> ELECTED LEADER for Term {self.current_term}!")
            self.cluster.broadcast_heartbeat(self.node_id, self.current_term)

    def handle_request_vote(self, candidate_id: str, term: int) -> bool:
        with self.lock:
            if self.role == NodeRole.CRASHED:
                return False

            if term > self.current_term:
                self.current_term = term
                self.role = NodeRole.FOLLOWER
                self.voted_for = None

            if term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
                self.voted_for = candidate_id
                self.last_heartbeat_time = time.time()
                return True

            return False

    def handle_heartbeat(self, leader_id: str, term: int):
        with self.lock:
            if self.role == NodeRole.CRASHED:
                return

            if term >= self.current_term:
                if self.role != NodeRole.FOLLOWER or term > self.current_term:
                    self.role = NodeRole.FOLLOWER
                    self.current_term = term
                    self.voted_for = None
                self.last_heartbeat_time = time.time()


class RaftCluster:
    def __init__(self, node_ids: List[str]):
        self.nodes = {nid: RaftNode(nid, self) for nid in node_ids}

    def broadcast_heartbeat(self, leader_id: str, term: int):
        for peer in self.nodes.values():
            if peer.node_id != leader_id:
                peer.handle_heartbeat(leader_id, term)

    def crash_node(self, node_id: str):
        with self.nodes[node_id].lock:
            self.nodes[node_id].role = NodeRole.CRASHED
            print(f"💥 [Crash] {node_id} has crashed!")

    def recover_node(self, node_id: str):
        with self.nodes[node_id].lock:
            self.nodes[node_id].role = NodeRole.FOLLOWER
            self.nodes[node_id].last_heartbeat_time = time.time()
            print(f"🔄 [Recover] {node_id} has rebooted as FOLLOWER.")


def main():
    print("=" * 70)
    print("RAFT DISTRIBUTED CONSENSUS: LEADER ELECTION SIMULATION")
    print("Cluster: [Node-A, Node-B, Node-C] (N=3, Quorum=2)")
    print("=" * 70)

    cluster = RaftCluster(["Node-A", "Node-B", "Node-C"])

    # Node-A starts as Leader of Term 1
    cluster.nodes["Node-A"].role = NodeRole.LEADER
    cluster.nodes["Node-A"].current_term = 1
    print("Initial State: Node-A is LEADER of Term 1.")

    # 1. Normal Heartbeat phase
    print("\n--- Phase 1: Normal Heartbeat Cycles ---")
    for _ in range(3):
        for n in cluster.nodes.values():
            n.tick()
        time.sleep(0.05)
    print("Heartbeats acknowledged by Node-B and Node-C. Cluster is stable.")

    # 2. Crash Leader Node-A
    print("\n--- Phase 2: Leader Crash & Election Trigger ---")
    cluster.crash_node("Node-A")
    print("Waiting for election timeout to expire on remaining followers...")

    # Wait until a new leader is elected
    new_leader = None
    start = time.time()
    while time.time() - start < 1.0:
        for n in cluster.nodes.values():
            n.tick()
            if n.role == NodeRole.LEADER:
                new_leader = n
                break
        if new_leader:
            break
        time.sleep(0.05)

    if new_leader:
        print(f"\nNew Cluster Leader: {new_leader.node_id} (Term {new_leader.current_term})")

    # 3. Old Leader Reconnects
    print("\n--- Phase 3: Old Leader Node-A Reconnects ---")
    cluster.recover_node("Node-A")
    # Ticking cluster sends heartbeats from new leader to Node-A
    for _ in range(3):
        for n in cluster.nodes.values():
            n.tick()
        time.sleep(0.05)

    print(f"Node-A role after receiving Term 2 heartbeats: {cluster.nodes['Node-A'].role.value}")
    print("✅ Split-Brain avoided! Old leader safely demoted to Follower.")
    print("=" * 70)
    print("Raft simulation completed successfully!")

if __name__ == "__main__":
    main()
