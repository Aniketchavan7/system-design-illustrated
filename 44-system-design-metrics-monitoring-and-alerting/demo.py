"""
Standalone Simulation of Metrics Monitoring & Alerting System.
Demonstrates:
  1. Time-series metric ingestion with timestamp and label tags.
  2. Gorilla-style Delta-of-Delta timestamp compression.
  3. Metric downsampling (10-second raw points rolled into 1-minute averages).
  4. Alert Rule evaluation state machine (OK -> PENDING -> FIRING).
"""

import time
from typing import Dict, List, Tuple, Optional

class MetricDataPoint:
    def __init__(self, metric_name: str, labels: dict, value: float, timestamp: int):
        self.metric_name = metric_name
        self.labels = labels
        self.value = value
        self.timestamp = timestamp

class SimpleGorillaCompressor:
    """Demonstrates Delta-of-Delta compression mechanics."""
    @staticmethod
    def compress_timestamps(timestamps: List[int]) -> Tuple[List[int], float]:
        if len(timestamps) < 2:
            return timestamps, 1.0

        # Calculate deltas: D_i = T_i - T_{i-1}
        deltas = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        
        # Calculate delta-of-deltas: DD_i = D_i - D_{i-1}
        delta_of_deltas = [deltas[0]] + [deltas[i] - deltas[i-1] for i in range(1, len(deltas))]
        
        # In Gorilla: if DD == 0, it takes 1 single bit!
        zero_bits = sum(1 for dd in delta_of_deltas if dd == 0)
        estimated_bits = (zero_bits * 1) + ((len(delta_of_deltas) - zero_bits) * 16)
        raw_bits = len(timestamps) * 64
        compression_ratio = raw_bits / max(1, estimated_bits)
        
        return delta_of_deltas, compression_ratio

class AlertRule:
    def __init__(self, metric_name: str, threshold: float, sustained_window_secs: float):
        self.metric_name = metric_name
        self.threshold = threshold
        self.sustained_window = sustained_window_secs
        self.state = "OK"  # OK, PENDING, FIRING
        self.breach_start_time: Optional[float] = None

    def evaluate(self, current_value: float, current_time: float) -> str:
        if current_value > self.threshold:
            if self.state == "OK":
                self.state = "PENDING"
                self.breach_start_time = current_time
                print(f"    [ALERT] Threshold breached ({current_value:.1f} > {self.threshold}) -> State: PENDING")
            elif self.state == "PENDING":
                elapsed = current_time - (self.breach_start_time or current_time)
                if elapsed >= self.sustained_window:
                    self.state = "FIRING"
                    print(f"    [ALERT] Breached for {elapsed:.1f}s >= {self.sustained_window}s -> State: FIRING (Page on-call!)")
        else:
            if self.state in ("PENDING", "FIRING"):
                print(f"    [ALERT RECOVERED] Value returned to normal ({current_value:.1f} <= {self.threshold}) -> State: OK")
            self.state = "OK"
            self.breach_start_time = None

        return self.state

def run_simulation():
    print("=" * 65)
    print("METRICS MONITORING & ALERTING SYSTEM SIMULATION")
    print("=" * 65)

    # 1. Gorilla Timestamp Compression
    print("Step 1: Ingesting 10 regular metric timestamps (10-second intervals):")
    base_time = 1700000000
    timestamps = [base_time + (i * 10) for i in range(10)]
    dd, ratio = SimpleGorillaCompressor.compress_timestamps(timestamps)
    print(f"  Raw Timestamps: {timestamps[:4]}... (10 entries)")
    print(f"  Delta-of-Deltas: {dd}")
    print(f"  Gorilla Timestamp Compression Ratio: {ratio:.1f}x compression factor!\n")

    # 2. Downsampling Rollup Simulation
    print("Step 2: Simulating Downsampling (Rolling six 10s raw points into 1m average):")
    raw_readings = [42.1, 43.5, 41.8, 44.0, 42.9, 43.1]
    avg_val = sum(raw_readings) / len(raw_readings)
    min_val = min(raw_readings)
    max_val = max(raw_readings)
    print(f"  Raw 10s Readings (CPU %): {raw_readings}")
    print(f"  1-Minute Rollup: Avg={avg_val:.2f}%, Min={min_val:.2f}%, Max={max_val:.2f}% (6x storage reduction)\n")

    # 3. Alert Rule Evaluation (Flapping Prevention)
    print("Step 3: Alert Evaluation State Machine (Threshold > 90% CPU, Sustained: 0.3s):")
    rule = AlertRule("cpu_usage", threshold=90.0, sustained_window_secs=0.3)

    t0 = time.time()
    # Reading 1: Normal
    print("  Time 0.0s: Reading = 75.0% CPU")
    rule.evaluate(75.0, t0)

    # Reading 2: Transient Spike (should enter PENDING, not page)
    time.sleep(0.1)
    print("  Time 0.1s: Reading = 94.0% CPU (Spike)")
    s1 = rule.evaluate(94.0, time.time())
    assert s1 == "PENDING"

    # Reading 3: Brief recovery (flapping avoided!)
    time.sleep(0.1)
    print("  Time 0.2s: Reading = 80.0% CPU (Drop)")
    s2 = rule.evaluate(80.0, time.time())
    assert s2 == "OK"

    # Reading 4: Sustained Outage
    print("\n  Simulating Sustained Production Outage (> 90% for > 0.3s):")
    t_start = time.time()
    rule.evaluate(95.0, t_start)
    time.sleep(0.35)
    s3 = rule.evaluate(96.0, time.time())
    assert s3 == "FIRING"

    print("\nSUCCESS: Delta-of-delta compression verified, and alert flapping prevented!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
