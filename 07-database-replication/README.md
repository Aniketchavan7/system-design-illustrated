# 07 - Database Replication & High Availability

> **Real-World Analogy:**  
> Imagine an executive chef and three line cooks. The executive chef takes all incoming orders and writes the master menu (Leader). She passes copies of the order tickets to the line cooks (Replicas). When customers ask what the special of the day is, any line cook can answer (Read Scaling), but only the executive chef can change the recipe (Write Master).

---

## 🎯 What & Why
Examines database replication topologies: single-leader, multi-leader, and leaderless architectures, discussing replication lag, failover procedures, and read-after-write consistency.

---

## 📊 Visual Architecture Diagram
```mermaid
flowchart TD
    Client["📱 Application Server Fleet"]

    subgraph ReplicationTopology["Primary-Replica Database Topology"]
        Primary[("👑 Primary Database (Leader - Writes & Reads)")]
        Replica1[("📖 Read Replica 1 (Follower)")]
        Replica2[("📖 Read Replica 2 (Follower)")]
    end

    Client -->|1. Write Transactions (INSERT / UPDATE)| Primary
    Primary -->|2. Asynchronous Replication Stream (WAL / binlog)| Replica1
    Primary -->|2. Asynchronous Replication Stream (WAL / binlog)| Replica2
    Client -->|3. Read Queries (SELECT)| Replica1
    Client -->|3. Read Queries (SELECT)| Replica2
```

---

## ⚙️ How It Works Under The Hood
### Replication Topologies

1. **Single-Leader (Master-Slave)**:
   - All writes are processed by the single leader node.
   - Replicas stream the Write-Ahead Log (WAL) or binlog from the leader to stay synchronized.
   - Scalable for **read-heavy** workloads (e.g., 95% reads, 5% writes).
   - If the leader fails, a consensus election promotes one follower to become the new primary.

2. **Multi-Leader (Master-Master)**:
   - Multiple nodes across different geographical datacenters accept writes.
   - Useful for low-latency writes across continents and resilience against regional outages.
   - **Challenge**: Write conflicts occur when two users modify the same record concurrently in different datacenters. Requires conflict resolution strategies (Last-Write-Wins, CRDTs, or application-level merges).

3. **Leaderless (Dynamo-style, Cassandra)**:
   - Clients send read and write requests to any node (or a coordinator).
   - Uses **Quorum Reads and Writes** ($W + R > N$) to ensure at least one overlapping replica holds the latest version of data.

---

### Common Replication Pitfalls

- **Replication Lag**: In asynchronous replication, replicas lag behind the primary. A user updates their profile and refreshes the page, reading from a stale replica where the change has not yet propagated.
- **Solution - Read-After-Write Consistency**: Route reads for a user's own updates directly to the primary node for 5 seconds after a write.

---

## 💻 Concrete Code Implementation
```python
# Python simulation: Master-Replica with simulated replication lag
import time
import random

class DatabaseCluster:
    def __init__(self):
        self.primary = {}
        self.replicas = [{}, {}]

    def write(self, key: str, value: str):
        # Immediate write to primary
        self.primary[key] = value
        # Replicas receive updates asynchronously
        for i in range(len(self.replicas)):
            # Simulating async propagation
            self.replicas[i][key] = value

    def read_replica(self, key: str):
        chosen_replica = random.choice(self.replicas)
        return chosen_replica.get(key)

    def read_primary(self, key: str):
        return self.primary.get(key)

if __name__ == "__main__":
    db = DatabaseCluster()
    db.write("user:101", "Alice Smith")
    print("Read from Primary:", db.read_primary("user:101"))
    print("Read from Replica:", db.read_replica("user:101"))

```

---

## ⚖️ Trade-Offs & Architectural Considerations
- **Data Freshness**: Always configure appropriate TTLs to balance staleness vs database load.
- **Resource Limits**: Size in-memory clusters appropriately and set clear eviction policies.
- **Consistency**: Understand the trade-offs between sync writes and async replication.
