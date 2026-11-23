"""
Interactive Demo: 64-Bit Distributed Snowflake ID Generator (Twitter / Discord)
Simulates:
1. Bitwise bit-packing: 41-bit timestamp, 10-bit worker ID, 12-bit sequence.
2. Concurrent generation across parallel threads with zero collisions.
3. Monotonic sorting verification.
"""

import time
import threading
from typing import List

# Custom Epoch (2026-01-01 00:00:00 UTC)
CUSTOM_EPOCH = 1767225600000

class SnowflakeGenerator:
    def __init__(self, datacenter_id: int, worker_id: int):
        self.datacenter_id = datacenter_id & 0x1F  # 5 bits (0-31)
        self.worker_id = worker_id & 0x1F          # 5 bits (0-31)
        self.sequence = 0                          # 12 bits (0-4095)
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        with self.lock:
            now = self._current_timestamp_ms()

            # Clock rollback protection
            if now < self.last_timestamp:
                raise RuntimeError(f"Clock moved backwards! Refusing to generate ID for {self.last_timestamp - now}ms")

            if now == self.last_timestamp:
                # Same millisecond: increment sequence counter
                self.sequence = (self.sequence + 1) & 0xFFF  # 4095 max
                if self.sequence == 0:
                    # Sequence overflow in same millisecond: wait for next ms
                    while now <= self.last_timestamp:
                        now = self._current_timestamp_ms()
            else:
                self.sequence = 0

            self.last_timestamp = now

            # Assemble 64-bit integer
            time_delta = now - CUSTOM_EPOCH
            snowflake_id = (
                (time_delta << 22) |
                (self.datacenter_id << 17) |
                (self.worker_id << 12) |
                self.sequence
            )
            return snowflake_id

def run_simulation():
    print("=" * 65)
    print("TWITTER SNOWFLAKE 64-BIT DISTRIBUTED ID GENERATOR SIMULATION")
    print("=" * 65)

    gen = SnowflakeGenerator(datacenter_id=1, worker_id=7)
    generated_ids: List[int] = []
    
    def worker_task(count: int):
        for _ in range(count):
            generated_ids.append(gen.next_id())

    # Spawn 5 concurrent threads generating 200 IDs each
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker_task, args=(200,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"Total IDs Generated Concurrently: {len(generated_ids)}")
    unique_ids = set(generated_ids)
    print(f"Unique IDs Count:                {len(unique_ids)}")
    print(f"Duplicate IDs:                   {len(generated_ids) - len(unique_ids)} (Guaranteed Zero!)")

    # Sample ID breakdown
    sample = generated_ids[0]
    print(f"\nSample Generated ID (64-bit integer): {sample}")
    print(f'Serialized as JSON String:            "{sample}"')

    # Verify monotonic time ordering
    is_sorted = all(generated_ids[i] <= generated_ids[i+1] for i in range(len(generated_ids)-1))
    print(f"Monotonically Time-Ordered:           {is_sorted}")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
