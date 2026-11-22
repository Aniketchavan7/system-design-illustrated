# 14 - Distributed Consistency Models

> **Real-World Analogy:**  
> Imagine a group chat with friends across different time zones. With Strong Consistency, nobody can send a new message until every single member's phone buzzes and marks 'Delivered'. With Eventual Consistency, messages arrive whenever network connectivity permits; everyone will eventually see all messages, but someone on an airplane might see replies slightly out of order until they reconnect.

---

## 🎯 What & Why
Demystifies the spectrum of consistency guarantees in distributed datastores, from strict linearizability to causal, monotonic reads, and eventual consistency.

---

## 📊 Visual Architecture Diagram
```mermaid
flowchart LR
    Strict["🔒 Strict / Linearizable"] --> Sequential["Sequential Consistency"]
    Sequential --> Causal["Causal Consistency"]
    Causal --> ReadYourWrites["Read-Your-Writes"]
    ReadYourWrites --> Eventual["⚡ Eventual Consistency"]
```

---

## ⚙️ How It Works Under The Hood
### The Spectrum of Consistency Models

1. **Linearizability (Strong Consistency)**:
   - Operations appear to execute instantaneously on a single copy of data at some point between their invocation and response.
   - Once a write completes, every subsequent read anywhere in the cluster MUST observe that write or a newer one.

2. **Sequential Consistency**:
   - Operations take effect in some sequential order, and operations of each individual process appear in this sequence in the order specified by its program.

3. **Causal Consistency**:
   - Operations that are causally related must be seen by every node in the same order. Operations that are not causally related (concurrent) may be seen in different orders.
   - Example: A question must always appear before its answer.

4. **Eventual Consistency**:
   - If no new updates are made to a given item, all replicas will eventually return the last updated value.
   - Provides highest availability and lowest write latencies, but applications must handle transient stale reads.

---

### Client-Centric Consistency Guarantees

- **Read-Your-Writes**: A user who updates a field will always see their own updated value when refreshing the page.
- **Monotonic Reads**: If a user reads version $V_2$, they will never subsequently observe an older version $V_1$ on another replica.
- **Monotonic Writes**: A system guarantees that writes from the same client are processed in the order they were submitted.

---

## 💻 Concrete Code Implementation
```python
# Python simulation: Eventual consistency with Vector Clocks for causal ordering

class VectorClock:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.clock = {node_id: 0}

    def tick(self):
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1

    def update(self, other_clock: dict):
        for node, timestamp in other_clock.items():
            self.clock[node] = max(self.clock.get(node, 0), timestamp)
        self.tick()

    def __repr__(self):
        return f"{self.node_id}:{self.clock}"

if __name__ == "__main__":
    node_a = VectorClock("NodeA")
    node_b = VectorClock("NodeB")

    # Node A performs local event
    node_a.tick()
    print("Node A state:", node_a)

    # Node A sends message to Node B
    node_b.update(node_a.clock)
    print("Node B state after sync:", node_b)

```

---

## ⚖️ Trade-Offs & Architectural Considerations
- **Quorums**: Choose odd-numbered cluster sizes (3, 5, 7) to avoid split votes.
- **Failover Speeds**: Balance election timeouts to avoid false failovers during transient CPU spikes.
- **Consistency**: Strict consistency trades off availability during partitions.
