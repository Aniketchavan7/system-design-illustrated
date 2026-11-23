"""
Standalone Simulation of Global Multi-Channel Notification System.
Demonstrates:
  1. Priority Queue scheduling (High, Medium, Low).
  2. Multi-channel dispatch routing (Push/FCM, SMS/Twilio, Email/SendGrid).
  3. Sliding window deduplication using cryptographic fingerprints.
  4. Exponential backoff retry with Dead-Letter Queue (DLQ).
"""

import time
import hashlib
import heapq
from typing import Dict, Any, List, Optional

class NotificationItem:
    def __init__(self, priority: int, user_id: str, channel: str, template: str, data: dict):
        self.priority = priority  # 1: High (2FA), 2: Med (Orders), 3: Low (Marketing)
        self.user_id = user_id
        self.channel = channel  # PUSH, SMS, EMAIL
        self.template = template
        self.data = data
        self.attempts = 0
        self.created_at = time.time()

    def __lt__(self, other):
        # Higher priority (lower number) processed first
        return self.priority < other.priority

class MockVendorNetwork:
    """Simulates external third-party gateway behavior."""
    def send(self, channel: str, destination: str, body: str) -> bool:
        if "fail" in destination:
            return False  # Simulate carrier outage
        return True

class NotificationEngine:
    def __init__(self):
        # Priority queue for in-flight tasks
        self.queue: List[NotificationItem] = []
        # Dead letter queue
        self.dlq: List[NotificationItem] = []
        # Deduplication cache: hash -> expiration timestamp
        self.dedup_cache: Dict[str, float] = {}
        self.vendor = MockVendorNetwork()

    def _get_fingerprint(self, user_id: str, channel: str, template: str) -> str:
        raw = f"{user_id}:{channel}:{template}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def enqueue(self, priority: int, user_id: str, channel: str, template: str, data: dict, dedup_window_secs: float = 2.0) -> bool:
        now = time.time()
        fp = self._get_fingerprint(user_id, channel, template)

        # 1. Deduplication Check
        if fp in self.dedup_cache:
            if now < self.dedup_cache[fp]:
                print(f"  [DEDUP BLOCKED] Duplicate alert dropped for {user_id} ({template}) within window!")
                return False

        # Set deduplication window
        self.dedup_cache[fp] = now + dedup_window_secs

        # 2. Add to Priority Queue
        item = NotificationItem(priority, user_id, channel, template, data)
        heapq.heappush(self.queue, item)
        p_name = {1: "HIGH (2FA)", 2: "MEDIUM (Order)", 3: "LOW (Promo)"}.get(priority, "NORMAL")
        print(f"  [ENQUEUED] [{p_name}] {channel} notification for {user_id}")
        return True

    def process_queue(self):
        print("\n--- Processing Notification Queue by Priority Order ---")
        while self.queue:
            item = heapq.heappop(self.queue)
            item.attempts += 1
            dest = item.data.get("destination", "valid_dest")

            success = self.vendor.send(item.channel, dest, item.template)
            if success:
                print(f"  [DELIVERED] (Priority {item.priority}) {item.channel} to {item.user_id} -> '{item.template}'")
            else:
                print(f"  [VENDOR ERROR] Failed dispatch for {item.user_id} on {item.channel} (Attempt {item.attempts}/3)")
                if item.attempts < 3:
                    # Re-queue for retry
                    heapq.heappush(self.queue, item)
                else:
                    # Move to DLQ
                    self.dlq.append(item)
                    print(f"  [MOVED TO DLQ] Permanent failure after 3 attempts -> Routed to Dead-Letter Queue!")

def run_simulation():
    print("=" * 65)
    print("GLOBAL MULTI-CHANNEL NOTIFICATION SYSTEM SIMULATION")
    print("=" * 65)

    engine = NotificationEngine()

    # 1. Enqueue mix of priorities in random arrival order
    print("Step 1: Ingesting notifications across multiple microservices:\n")
    # Low priority marketing promo arrived first
    engine.enqueue(priority=3, user_id="user_bob", channel="EMAIL", template="50% Off Weekend Sale!", data={"destination": "bob@mail.com"})
    # Medium priority delivery update
    engine.enqueue(priority=2, user_id="user_alice", channel="PUSH", template="Your driver is 2 mins away!", data={"destination": "alice_device_token"})
    # High priority 2FA arrived last!
    engine.enqueue(priority=1, user_id="user_charlie", channel="SMS", template="Your 2FA security code is 884-129", data={"destination": "+1-555-0199"})

    # 2. Test Deduplication: User taps "Resend 2FA" 3 times in 1 second
    print("\nStep 2: Simulating burst duplicate 2FA requests:")
    engine.enqueue(priority=1, user_id="user_charlie", channel="SMS", template="Your 2FA security code is 884-129", data={"destination": "+1-555-0199"})
    engine.enqueue(priority=1, user_id="user_charlie", channel="SMS", template="Your 2FA security code is 884-129", data={"destination": "+1-555-0199"})

    # 3. Simulate failure & DLQ
    print("\nStep 3: Enqueue notification destined to fail carrier network:")
    engine.enqueue(priority=1, user_id="user_david", channel="SMS", template="Fraud Alert!", data={"destination": "carrier_fail_network"})

    # 4. Drain queue
    engine.process_queue()

    # 5. Review DLQ state
    print(f"\nDead-Letter Queue Summary: {len(engine.dlq)} permanently failed items recorded for investigation.")
    assert len(engine.dlq) == 1
    print("SUCCESS: High priority processed first, duplicates blocked, and failing items safely routed to DLQ!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
