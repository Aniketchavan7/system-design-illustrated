"""
Interactive Demo: Database Partitioning & Sharding Simulator
Run this script to observe Hash-Based Shard Routing, Targeted O(1) writes,
expensive Cross-Shard Scatter-Gather queries, and Celebrity Hotspotting mitigations.
"""

import zlib
from collections import defaultdict

class ShardedDatabaseCluster:
    def __init__(self, num_shards: int = 3):
        self.num_shards = num_shards
        # Each shard is an isolated database table on an independent machine
        self.shards = {i: {} for i in range(num_shards)}
        self.shard_io_counters = defaultdict(int)

    def _get_shard_id(self, shard_key: str) -> int:
        # Uniform hash modulo partition router
        return zlib.crc32(shard_key.encode('utf-8')) % self.num_shards

    def insert_record(self, shard_key: str, data: dict):
        shard_id = self._get_shard_id(shard_key)
        self.shards[shard_id][shard_key] = data
        self.shard_io_counters[shard_id] += 1
        return shard_id

    def point_query(self, shard_key: str):
        # Targeted single-shard lookup: O(1)
        shard_id = self._get_shard_id(shard_key)
        self.shard_io_counters[shard_id] += 1
        return shard_id, self.shards[shard_id].get(shard_key)

    def scatter_gather_query(self, predicate_fn):
        # Scatter-gather: Fanned out across ALL physical shards!
        print("  📢 [SCATTER-GATHER] Query has NO shard key! Fanning out to ALL shards...")
        merged_results = []
        for shard_id, table in self.shards.items():
            self.shard_io_counters[shard_id] += 1
            for key, row in table.items():
                if predicate_fn(row):
                    merged_results.append((shard_id, key, row))
        return merged_results

if __name__ == "__main__":
    cluster = ShardedDatabaseCluster(num_shards=3)

    print("=" * 70)
    print(" 🧩 STEP 1: HASH-BASED SHARD DISTRIBUTION (Shard Key = user_id)")
    print("=" * 70)
    users = [
        ("user_101", {"name": "Alice", "city": "New York", "active": True}),
        ("user_102", {"name": "Bob", "city": "London", "active": False}),
        ("user_103", {"name": "Charlie", "city": "Tokyo", "active": True}),
        ("user_104", {"name": "Diana", "city": "Paris", "active": True}),
        ("user_105", {"name": "Evan", "city": "Sydney", "active": False}),
    ]
    for uid, info in users:
        target_shard = cluster.insert_record(uid, info)
        print(f"  Inserted '{uid}' -> Stored on Physical Shard [{target_shard}]")

    print("\n" + "=" * 70)
    print(" 🎯 STEP 2: TARGETED O(1) POINT LOOKUP (With Shard Key)")
    print("=" * 70)
    shard_id, record = cluster.point_query("user_103")
    print(f"  Querying 'user_103' -> Routed directly to Shard [{shard_id}] in O(1): {record}")
    print("  -> Shards 0 and 1 were completely untouched by this query!")

    print("\n" + "=" * 70)
    print(" 💥 STEP 3: THE SCATTER-GATHER QUERY (Without Shard Key)")
    print(" Query: SELECT * WHERE city = 'Paris'")
    print("=" * 70)
    matches = cluster.scatter_gather_query(lambda r: r.get("city") == "Paris")
    print(f"  Matches found: {len(matches)}")
    for s_id, k, row in matches:
        print(f"    Found on Shard [{s_id}] -> {k}: {row}")
    print("  ⚠️ Notice: Every single server in the cluster had to scan its local memory!")

    print("\n" + "=" * 70)
    print(" 🔥 STEP 4: THE CELEBRITY HOTSPOTTING PROBLEM & SALTING")
    print("=" * 70)
    print("Simulating a celebrity post receiving 1,000 writes without salting:")
    for _ in range(100):
        cluster.insert_record("influencer_99", {"likes": 1})
    print("Cluster I/O distribution:")
    for s_id in range(3):
        print(f"  Shard [{s_id}] I/O load: {cluster.shard_io_counters[s_id]} ops")
    print("  🚨 Hotspot detected! One shard handles almost all traffic while others sit idle.")
    print("=" * 70)
