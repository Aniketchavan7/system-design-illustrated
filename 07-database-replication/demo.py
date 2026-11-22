"""
Interactive Demo: Database Replication & Replication Lag Simulator
Run this script to observe Asynchronous Replication Lag, the Read-Your-Own-Writes
consistency anomaly, the Read-After-Write routing fix, and automated failover.
"""

import time

class DatabaseReplicationCluster:
    def __init__(self):
        self.primary_data = {}
        self.replica_data = {}
        self.replica_sync_time = 0.0
        self.primary_alive = True

    def write_primary(self, key: str, value: str):
        if not self.primary_alive:
            raise RuntimeError("Primary is DEAD! Cannot accept writes.")
        now = time.time()
        self.primary_data[key] = (value, now)
        # Asynchronous lag: replica will only catch up after 1.5 seconds
        self.replica_sync_time = now + 1.5
        print(f"\n✍️  [PRIMARY WRITE] Written '{key}' = '{value}' to Primary at t=0.00s")

    def read_replica_naive(self, key: str):
        now = time.time()
        # If replica has caught up
        if now >= self.replica_sync_time and key in self.primary_data:
            val, _ = self.primary_data[key]
            self.replica_data[key] = val

        data = self.replica_data.get(key, "<EMPTY / NOT_FOUND>")
        print(f"📖 [NAIVE REPLICA READ] Read from Follower Replica: '{key}' = '{data}'")
        return data

    def read_with_read_after_write_consistency(self, key: str, user_last_write_time: float):
        now = time.time()
        # If user modified data within the last 3 seconds, route read to Primary!
        if (now - user_last_write_time) < 3.0:
            val, _ = self.primary_data.get(key, ("<EMPTY>", 0))
            print(f"👑 [SMART READ ROUTER] Recent write detected ({now - user_last_write_time:.2f}s ago). Routed directly to PRIMARY -> '{val}'")
            return val
        else:
            return self.read_replica_naive(key)

if __name__ == "__main__":
    cluster = DatabaseReplicationCluster()

    print("=" * 70)
    print(" 🚨 SCENARIO 1: THE READ-YOUR-OWN-WRITES ANOMALY (Async Lag)")
    print("=" * 70)
    # Alice updates her profile
    cluster.write_primary("user_42:bio", "Senior Distributed Systems Engineer")
    alice_write_time = time.time()

    # Alice immediately refreshes the page (200ms later)
    print("\nAlice refreshes page 0.2 seconds later:")
    cluster.read_replica_naive("user_42:bio")
    print("  ❌ PROBLEM: Alice sees an empty bio! She panics and clicks 'Save' again.")

    print("\n" + "=" * 70)
    print(" 🛡️ SCENARIO 2: FIX WITH READ-AFTER-WRITE CONSISTENCY")
    print("=" * 70)
    print("Same scenario, but application routes recent user writes to Primary for 3 seconds:")
    cluster.read_with_read_after_write_consistency("user_42:bio", alice_write_time)
    print("  ✅ SUCCESS: Alice immediately sees her fresh update!")

    print("\n" + "=" * 70)
    print(" ⏳ SCENARIO 3: REPLICATION CONVERGENCE AFTER ASYNC LAG")
    print("=" * 70)
    print("Waiting 1.6 seconds for asynchronous binlog replication to catch up...")
    time.sleep(1.6)
    print("\nBob (another user) reads Alice's bio from Replica:")
    cluster.read_replica_naive("user_42:bio")
    print("  ✅ Replicas are now in-sync! Reads served from replica pool.")

    print("\n" + "=" * 70)
    print(" 👑 SCENARIO 4: PRIMARY CRASH & FOLLOWER PROMOTION (FAILOVER)")
    print("=" * 70)
    print("⚠️ Primary database crashes due to power loss!")
    cluster.primary_alive = False
    print("Consensus Heartbeat detects Primary missing for 3 seconds.")
    print("Promoting Replica 1 to be the new PRIMARY LEADER!")
    # Replica 1 becomes primary
    cluster.primary_data = dict(cluster.replica_data)
    cluster.primary_alive = True
    cluster.write_primary("user_42:status", "New Primary accepting writes!")
    print("=" * 70)
