# 17 - Message Queues & Event Streaming

> **Real-World Analogy:**  
> Imagine a busy bakery. The counter staff take customer orders and write them onto hanging tickets on an order wheel (Message Queue). The kitchen bakers pick tickets off the wheel at their own pace and bake the cakes (Consumers). Even if 50 customers arrive simultaneously, the counter never refuses an order, and the kitchen bakers never choke.

---

## 🎯 What & Why
Deep dive into asynchronous messaging systems, comparing message queues (RabbitMQ, SQS) with distributed commit log streams (Apache Kafka, Redpanda), along with consumer groups and delivery semantics.

---

## 📊 Visual Architecture Diagram
```mermaid
flowchart LR
    subgraph Producers["Message Producers"]
        P1["Order Service"]
        P2["Payment Gateway"]
    end

    subgraph KafkaCluster["Distributed Log Broker (Kafka Topic)"]
        direction TB
        Part0["Partition 0 [Offset 0, 1, 2, 3...]"]
        Part1["Partition 1 [Offset 0, 1, 2, 3...]"]
        Part2["Partition 2 [Offset 0, 1, 2, 3...]"]
    end

    subgraph ConsumerGroup["Consumer Group Fleet"]
        C1["Worker 1 (Reads Part 0)"]
        C2["Worker 2 (Reads Part 1)"]
        C3["Worker 3 (Reads Part 2)"]
    end

    P1 --> Part0
    P2 --> Part1
    P1 --> Part2

    Part0 --> C1
    Part1 --> C2
    Part2 --> C3
```

---

## ⚙️ How It Works Under The Hood
### Message Queues vs Distributed Log Streaming

| Dimension | Traditional Message Queue (RabbitMQ, SQS) | Event Log Stream (Apache Kafka, Redpanda) |
| :--- | :--- | :--- |
| **Data Retention** | Messages deleted immediately after consumer ACK | Messages persisted to disk for days/months; durable log |
| **Model** | Smart broker, dumb consumer (broker tracks delivery) | Dumb broker, smart consumer (consumer tracks own offset) |
| **Replayability** | Cannot replay processed messages | Consumers can rewind offset and replay historical events |
| **Ordering** | Ordered within queue; complex with competing workers | Strictly ordered per partition |
| **Throughput** | Typically lower per broker (it tracks and deletes each message) | Very high: millions of events/sec across a cluster (sequential disk I/O, batching) |

---

### Delivery Semantics

1. **At-Most-Once**:
   - Messages may be lost, but are never redelivered.
   - Example: Telemetry metrics, sensor updates where occasional loss is acceptable.
2. **At-Least-Once** (Most common):
   - Messages are guaranteed never to be lost, but duplicates may arrive during network retries.
   - **Requirement**: Consumers must be designed to be **Idempotent** (processing the same message ID twice produces identical results).
3. **Exactly-Once**:
   - True exactly-once *delivery* isn't possible over an unreliable network. What systems offer is **effectively-once processing**: at-least-once delivery plus deduplication or idempotent writes. Kafka adds transactions so that a read → process → write cycle *within Kafka* happens exactly once.

---

## 💻 Concrete Code Implementation
```python
# In-memory pub/sub: every subscriber gets its own copy of each event (fan-out).
# (A consumer *group* would instead split events between its members.)
from collections import defaultdict, deque

class EventBus:
    def __init__(self):
        self.topics = defaultdict(deque)
        self.subscribers = defaultdict(list)

    def subscribe(self, topic: str, callback):
        self.subscribers[topic].append(callback)

    def publish(self, topic: str, event_payload: dict):
        self.topics[topic].append(event_payload)
        for consumer in self.subscribers[topic]:
            consumer(event_payload)

if __name__ == "__main__":
    bus = EventBus()

    # Define subscriber callbacks
    def email_notification_worker(event):
        print(f"[Email Worker] Sending welcome email to {event['email']}")

    def analytics_worker(event):
        print(f"[Analytics Worker] Logged signup event for user {event['user_id']}")

    bus.subscribe("user.created", email_notification_worker)
    bus.subscribe("user.created", analytics_worker)

    print("Publishing 'user.created' event...")
    bus.publish("user.created", {"user_id": 402, "email": "alice@example.com"})

```

---

## ⚖️ Trade-offs

| Decision | Trade-off |
| :--- | :--- |
| **Queue (RabbitMQ, SQS)** | Simple work distribution, per-message retries and dead-letter queues; no replay once a message is consumed |
| **Log (Kafka, Redpanda)** | Replay history, many independent readers, huge throughput; more to operate, and ordering only within a partition |
| **More partitions** | More parallel consumers, but ordering only holds within each partition, and more files and connections |
| **At-least-once** | Nothing lost, but every consumer must be idempotent |
| **At-most-once** | Simplest, but messages can silently disappear |

**Cost of going async at all:** the caller no longer knows when (or whether) the work finished, failures surface later and elsewhere, and you need monitoring for queue depth and consumer lag.
