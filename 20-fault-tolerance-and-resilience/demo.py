"""
Interactive Demo: Fault Tolerance & Resilience Patterns
Run this script to observe:
1. Circuit Breaker State Machine: Closed -> Open (Fail-Fast Fallback) -> Half-Open -> Closed.
2. Exponential Backoff with Full Jitter algorithm preventing synchronized retry storms.
3. The Bulkhead Pattern: Isolating thread pools so slow dependencies cannot starve healthy endpoints.
"""

import time
import random
from enum import Enum
from typing import Callable, Any

# ==============================================================
# 1. Production Circuit Breaker Implementation
# ==============================================================
class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time_s: float = 0.5):
        self.failure_threshold = failure_threshold
        self.recovery_time_s = recovery_time_s
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def call(self, func: Callable, fallback: Callable, *args, **kwargs) -> Any:
        now = time.time()

        # Check transition from OPEN -> HALF_OPEN
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.recovery_time_s:
                self.state = CircuitState.HALF_OPEN
                print("  [CircuitBreaker] 🟡 Cooldown expired! Transitioning to HALF-OPEN (Testing canary probe)...")
            else:
                # Fail-Fast immediately!
                return fallback("Fail-Fast: Circuit is OPEN!")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as err:
            self._on_failure(err)
            return fallback(f"Fallback triggered: {err}")

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            print("  [CircuitBreaker] 🟢 Canary probe succeeded! Circuit reset to CLOSED.")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def _on_failure(self, err: Exception):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            print("  [CircuitBreaker] 🔴 Canary probe failed! Reverting back to OPEN.")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"  [CircuitBreaker] 🔴 Failure threshold ({self.failure_threshold}) reached! Circuit tripped to OPEN!")


# ==============================================================
# 2. Exponential Backoff with Full Jitter (AWS Standard)
# ==============================================================
def calculate_backoff(attempt: int, base: float = 0.1, cap: float = 2.0) -> float:
    """Computes exponential backoff with full jitter: Uniform(0, min(cap, base * 2^attempt))."""
    max_sleep = min(cap, base * (2 ** attempt))
    sleep_time = random.uniform(0, max_sleep)
    return sleep_time


# ==============================================================
# 3. Bulkhead Pattern Simulation
# ==============================================================
class Bulkhead:
    def __init__(self, name: str, max_concurrent: int):
        self.name = name
        self.max_concurrent = max_concurrent
        self.active_count = 0

    def try_acquire(self) -> bool:
        if self.active_count < self.max_concurrent:
            self.active_count += 1
            return True
        return False

    def release(self):
        if self.active_count > 0:
            self.active_count -= 1


def main():
    print("=" * 70)
    print("FAULT TOLERANCE & RESILIENCE PATTERNS SIMULATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Test 1: Circuit Breaker Lifecycle
    # ---------------------------------------------------------
    print("\n--- Test 1: Circuit Breaker Lifecycle & Fail-Fast ---")
    cb = CircuitBreaker(failure_threshold=3, recovery_time_s=0.3)

    # Simulated fragile dependency
    outage = False
    def fragile_service():
        if outage:
            raise ConnectionError("504 Gateway Timeout")
        return "200 OK: Recommendations Data"

    def cached_fallback(reason: str):
        return f"[Fallback Cache] Default Recommendations ({reason})"

    # Normal operation
    print("Step 1: Normal call (Downstream healthy):")
    print(f"  Response: {cb.call(fragile_service, cached_fallback)}")

    # Downstream crashes
    print("\nStep 2: Downstream dependency experiences an outage!")
    outage = True
    for i in range(1, 5):
        t0 = time.perf_counter()
        resp = cb.call(fragile_service, cached_fallback)
        dur_ms = (time.perf_counter() - t0) * 1000
        print(f"  Call {i}: State={cb.state.value} | Dur={dur_ms:.3f}ms | Resp={resp}")

    # Cooldown and recovery
    print("\nStep 3: Waiting 0.35s for cooldown timer to expire...")
    time.sleep(0.35)
    outage = False  # Downstream recovered

    print("Step 4: Next request (Probe):")
    resp = cb.call(fragile_service, cached_fallback)
    print(f"  Probe Result: State={cb.state.value} | Resp={resp}")

    # ---------------------------------------------------------
    # Test 2: Exponential Backoff with Full Jitter
    # ---------------------------------------------------------
    print("\n--- Test 2: Exponential Backoff with Full Jitter ---")
    print("Simulating retry sleep intervals across 4 retry attempts:")
    for attempt in range(1, 5):
        sleep_dur = calculate_backoff(attempt, base=0.05, cap=1.0)
        print(f"  Retry #{attempt}: Backoff sleep = {sleep_dur * 1000:6.2f} ms")

    # ---------------------------------------------------------
    # Test 3: Bulkhead Pattern Isolation
    # ---------------------------------------------------------
    print("\n--- Test 3: Bulkhead Pattern (Preventing Resource Exhaustion) ---")
    checkout_pool = Bulkhead("CheckoutServicePool", max_concurrent=5)
    recommendation_pool = Bulkhead("RecommendationsPool", max_concurrent=2)

    # Saturate recommendation pool with slow requests
    print("Simulating 2 hanging requests to Recommendations...")
    recommendation_pool.try_acquire()
    recommendation_pool.try_acquire()
    print(f"Recommendation Pool Active: {recommendation_pool.active_count}/{recommendation_pool.max_concurrent} (Saturated!)")

    # 3rd recommendation request
    can_exec_rec = recommendation_pool.try_acquire()
    print(f"3rd Recommendation request allowed? {can_exec_rec} (🛑 Bulkhead rejected to protect memory!)")

    # Healthy checkout service request
    can_exec_checkout = checkout_pool.try_acquire()
    print(f"Checkout request allowed? {can_exec_checkout} (✅ Checkout operates with 100% capacity in its own bulkhead!)")

    print("=" * 70)
    print("Fault tolerance simulation completed successfully!")

if __name__ == "__main__":
    main()
