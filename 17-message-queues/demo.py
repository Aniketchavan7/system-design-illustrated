"""
Interactive Demo: Message Queues & Partitioned Commit Logs
Run this script to observe:
1. Append-Only Partitioned Log (Kafka-style) with key-based partitioning.
2. Independent Consumer Groups reading at completely different offsets.
3. Replaying events by rewinding consumer group offsets.
4. Competing Consumer Work Queue with Dead-Letter Queue (DLQ) retry routing.
"""

import time
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass

# ==============================================================
# 1. Partitioned Commit Log (Kafka Architecture)
# ==============================================================
@dataclass
class LogMessage:
    offset: int
    key: str
    payload: str
    timestamp: float

class CommitLogPartition:
    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.messages: List[LogMessage] = []

    def append(self, key: str, payload: str) -> int:
        offset = len(self.messages)
        msg = LogMessage(offset=offset, key=key, payload=payload, timestamp=time.time())
        self.messages.append(msg)
        return offset

    def read_from(self, offset: int, max_batch: int = 10) -> List[LogMessage]:
        return self.messages[offset : offset + max_batch]


class PartitionedTopic:
    def __init__(self, name: str, num_partitions: int = 2):
        self.name = name
        self.partitions = [CommitLogPartition(i) for i in range(num_partitions)]

    def _get_partition(self, key: str) -> CommitLogPartition:
        idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(self.partitions)
        return self.partitions[idx]

    def publish(self, key: str, payload: str) -> tuple[int, int]:
        partition = self._get_partition(key)
        offset = partition.append(key, payload)
        return partition.partition_id, offset


class ConsumerGroup:
    def __init__(self, group_name: str, topic: PartitionedTopic):
        self.group_name = group_name
        self.topic = topic
        # partition_id -> committed offset
        self.offsets: Dict[int, int] = {p.partition_id: 0 for p in topic.partitions}

    def poll(self) -> List[LogMessage]:
        consumed = []
        for partition in self.topic.partitions:
            current_off = self.offsets[partition.partition_id]
            batch = partition.read_from(current_off)
            for msg in batch:
                consumed.append(msg)
                self.offsets[partition.partition_id] = msg.offset + 1
        return consumed

    def rewind(self, partition_id: int, target_offset: int):
        self.offsets[partition_id] = target_offset

# ==============================================================
# 2. Competing Consumers Queue with DLQ (RabbitMQ / SQS Architecture)
# ==============================================================
@dataclass
class QueueTask:
    task_id: str
    data: str
    retry_count: int = 0

class WorkQueueWithDLQ:
    def __init__(self, max_retries: int = 2):
        self.main_queue: List[QueueTask] = []
        self.dlq: List[QueueTask] = []
        self.max_retries = max_retries

    def enqueue(self, task: QueueTask):
        self.main_queue.append(task)

    def process_next(self, simulate_failure: bool = False) -> str:
        if not self.main_queue:
            return "Queue Empty"
        task = self.main_queue.pop(0)
        if simulate_failure:
            task.retry_count += 1
            if task.retry_count > self.max_retries:
                self.dlq.append(task)
                return f"Task {task.task_id} FAILED permanently -> Routed to DLQ!"
            else:
                self.main_queue.append(task)
                return f"Task {task.task_id} failed (attempt {task.retry_count}) -> Re-queued with backoff."
        return f"Task {task.task_id} successfully processed and ACKed."


def main():
    print("=" * 70)
    print("MESSAGE QUEUES & DISTRIBUTED COMMIT LOGS SIMULATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Part 1: Kafka-Style Partitioned Log with Independent Groups
    # ---------------------------------------------------------
    print("\n--- Part 1: Partitioned Commit Log & Independent Consumer Groups ---")
    orders_topic = PartitionedTopic("orders", num_partitions=2)

    # Publish events
    events = [
        ("user_101", "OrderPlaced(id=1, total=$99)"),
        ("user_102", "OrderPlaced(id=2, total=$249)"),
        ("user_101", "OrderPaid(id=1)"),
        ("user_103", "OrderPlaced(id=3, total=$15)"),
    ]
    for key, payload in events:
        p_id, off = orders_topic.publish(key, payload)
        print(f"Produced: '{payload}' -> Partition {p_id}, Offset {off}")

    # Consumer Group 1: Payments (Fast / Real-time)
    payments_group = ConsumerGroup("PaymentService", orders_topic)
    consumed_p = payments_group.poll()
    print(f"\n[PaymentService Group] Processed {len(consumed_p)} events. Offsets: {payments_group.offsets}")

    # Consumer Group 2: Analytics (Batch / Lagging)
    analytics_group = ConsumerGroup("AnalyticsService", orders_topic)
    print(f"[AnalyticsService Group] Starting from offsets: {analytics_group.offsets} (Lagging behind)")

    # ---------------------------------------------------------
    # Part 2: Time-Travel Offset Rewind
    # ---------------------------------------------------------
    print("\n--- Part 2: Event Replay (Offset Rewind) ---")
    print("Bug found in PaymentService accounting! Rewinding Partition 0 offset back to 0...")
    payments_group.rewind(partition_id=0, target_offset=0)
    replayed = payments_group.poll()
    print(f"PaymentService replayed {len(replayed)} historical events from Partition 0:")
    for msg in replayed:
        print(f"  Re-processed: Offset {msg.offset} | Payload: {msg.payload}")
    print("Notice: AnalyticsService state and offsets were completely untouched!")

    # ---------------------------------------------------------
    # Part 3: Work Queue & Dead-Letter Queue (DLQ)
    # ---------------------------------------------------------
    print("\n--- Part 3: Competing Consumer Queue with DLQ Failures ---")
    queue = WorkQueueWithDLQ(max_retries=2)
    queue.enqueue(QueueTask("email_1", "Welcome Email to User 101"))
    queue.enqueue(QueueTask("email_bad", "Corrupted PDF Attachment to User 102"))

    print(f"1. {queue.process_next(simulate_failure=False)}")
    print(f"2. {queue.process_next(simulate_failure=True)}")
    print(f"3. {queue.process_next(simulate_failure=True)}")
    print(f"4. {queue.process_next(simulate_failure=True)}")
    print(f"DLQ contents: {[t.task_id for t in queue.dlq]}")
    print("=" * 70)
    print("Simulation completed successfully!")

if __name__ == "__main__":
    main()
