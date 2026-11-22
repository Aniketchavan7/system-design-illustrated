# 13 - The CAP & PACELC Theorems

> **Real-World Analogy:**  
> Imagine planning an event with two coordinators who communicate via walkie-talkie. Suddenly, the radio batteries die (Network Partition). You now have only two choices: Coordinator A can keep selling tickets anyway, but risk double-booking seats that Coordinator B also sold (High Availability, Low Consistency); or both can refuse to sell any tickets until the radios work again (Strong Consistency, Zero Availability).

---

## 🎯 What & Why
Explains the foundational trade-offs in distributed systems when network partitions occur, examining the classic CAP theorem and the more comprehensive PACELC theorem.

---

## 📊 Visual Architecture Diagram
```mermaid
flowchart TD
    subgraph CAP["The CAP Theorem (In the event of Network Partition)"]
        P["⚡ Network Partition Occurs"]
        P --> Choice{"Must choose between:"}
        Choice -->|CP: Consistency over Availability| CP["🔒 CP Systems (Raft, Paxos, Spanner, Zookeeper)\nRejects operations if quorum cannot be reached"]
        Choice -->|AP: Availability over Consistency| AP["⚡ AP Systems (Cassandra, DynamoDB, CouchDB)\nAccepts all writes; resolves discrepancies eventually"]
    end
```

---

## ⚙️ How It Works Under The Hood
### Understanding the CAP Properties

- **Consistency (Linearizability)**: Every read receives the most recent write or an error.
- **Availability**: Every non-failing node returns a non-error response for every request (no guarantee it is the newest write).
- **Partition Tolerance**: The system continues to operate despite an arbitrary number of messages being dropped or delayed by the network between nodes.

> ⚠️ **Key Truth**: In distributed systems, networks are inherently unreliable (fiber cuts, router reboots, cloud latency spikes). Therefore, **Partition Tolerance (P) is non-negotiable**. When a partition occurs, you must choose between **Consistency (CP)** or **Availability (AP)**.

---

### PACELC: The Modern Extension

The CAP theorem only describes behavior *during a network partition*. But what about normal times when the network is healthy?

**PACELC Theorem**:
- **If there is a Partition (P)**, trade off **Availability (A)** vs **Consistency (C)**.
- **Else (E)**, trade off **Latency (L)** vs **Consistency (C)**.

| Database | PACELC Classification | Explanation |
| :--- | :--- | :--- |
| **Apache Cassandra** | **PA/EL** | On partition, chooses Availability. Else, chooses low Latency (async replication). |
| **Google Spanner** | **PC/EC** | On partition, chooses Consistency (quorums). Else, chooses Consistency via TrueTime. |
| **MongoDB** | **PC/EC** (default) | On partition, rejects writes on partitioned secondaries. Else, returns consistent primary reads. |
| **Amazon DynamoDB** | **PA/EL** | Configurable, but defaults to high availability and ultra-low latency. |

---

## 💻 Concrete Code Implementation
```python
# Python simulation: Demonstrating CP vs AP behavior during network partition

class DistributedClusterNode:
    def __init__(self, name: str):
        self.name = name
        self.data = {}
        self.is_partitioned = False

    def write_cp(self, key: str, value: str):
        if self.is_partitioned:
            # CP: Reject write to preserve global consistency
            raise RuntimeError(f"[{self.name}] Quorum unavailable. Write rejected (CP).")
        self.data[key] = value
        return True

    def write_ap(self, key: str, value: str):
        # AP: Accept write locally regardless of network partition
        self.data[key] = value
        return f"[{self.name}] Write accepted locally (AP). May be stale."

if __name__ == "__main__":
    node = DistributedClusterNode("node-virginia")
    node.is_partitioned = True

    print("--- AP System Behavior ---")
    print(node.write_ap("status", "active"))

    print("\n--- CP System Behavior ---")
    try:
        node.write_cp("status", "active")
    except RuntimeError as e:
        print(e)

```

---

## ⚖️ Trade-Offs & Architectural Considerations
- **Quorums**: Choose odd-numbered cluster sizes (3, 5, 7) to avoid split votes.
- **Failover Speeds**: Balance election timeouts to avoid false failovers during transient CPU spikes.
- **Consistency**: Strict consistency trades off availability during partitions.
