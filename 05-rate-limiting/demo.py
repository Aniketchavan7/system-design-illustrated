"""Rate limiting algorithms, side by side.

Run:  python demo.py

Every limiter takes the current time as an argument instead of reading the
clock, so the simulation is deterministic and you can replay the exact same
traffic through each algorithm. Try changing TRAFFIC or the limits below.
"""

from collections import deque


class FixedWindow:
    """Count requests per calendar window (e.g. per whole minute)."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.current_window = None
        self.count = 0

    def allow(self, now: float) -> bool:
        w = int(now // self.window)
        if w != self.current_window:  # a new window started: reset the counter
            self.current_window, self.count = w, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class SlidingLog:
    """Remember the timestamp of every accepted request in the last window."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.log = deque()

    def allow(self, now: float) -> bool:
        while self.log and self.log[0] <= now - self.window:
            self.log.popleft()  # forget requests that are too old to matter
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


class SlidingWindowCounter:
    """Estimate the last-window count from two counters (cheap and close)."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.current_window = 0
        self.current = 0
        self.previous = 0

    def allow(self, now: float) -> bool:
        w = int(now // self.window)
        if w != self.current_window:
            # If we skipped a whole window, the previous one had 0 requests.
            self.previous = self.current if w == self.current_window + 1 else 0
            self.current, self.current_window = 0, w
        elapsed_fraction = (now % self.window) / self.window
        estimate = self.current + self.previous * (1 - elapsed_fraction)
        if estimate < self.limit:
            self.current += 1
            return True
        return False


class TokenBucket:
    """Tokens drip in at a steady rate; each request spends one."""

    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity, self.rate = capacity, refill_per_sec
        self.tokens = float(capacity)
        self.last = 0.0

    def allow(self, now: float) -> bool:
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class LeakyBucket:
    """Requests wait in a small queue that drains at a fixed speed.

    allow() answers "was it accepted into the queue?". Accepted requests are
    then processed one by one at `leak_per_sec`, never faster.
    """

    def __init__(self, capacity: int, leak_per_sec: float):
        self.capacity, self.rate = capacity, leak_per_sec
        self.water = 0.0
        self.last = 0.0

    def allow(self, now: float) -> bool:
        self.water = max(0.0, self.water - (now - self.last) * self.rate)
        self.last = now
        if self.water + 1 <= self.capacity:
            self.water += 1
            return True
        return False


# Traffic: a burst of 5 just BEFORE the window boundary at t=60, a burst of 5
# just AFTER it, then a few calm requests spread out.
TRAFFIC = [55.0, 56.0, 57.0, 58.0, 59.0] + [60.5, 61.0, 61.5, 62.0, 62.5] + [90, 110, 130]

LIMIT, WINDOW = 5, 60.0  # "5 requests per minute"


def main() -> None:
    limiters = {
        "fixed window": FixedWindow(LIMIT, WINDOW),
        "sliding log": SlidingLog(LIMIT, WINDOW),
        "sliding counter": SlidingWindowCounter(LIMIT, WINDOW),
        # Same long-term average (5/min) but allows a burst of 5:
        "token bucket": TokenBucket(capacity=5, refill_per_sec=LIMIT / WINDOW),
        "leaky bucket": LeakyBucket(capacity=5, leak_per_sec=LIMIT / WINDOW),
    }

    print(f"Limit: {LIMIT} requests per {WINDOW:.0f}s\n")
    print("  time  " + "".join(f"{name:>17}" for name in limiters))
    totals = dict.fromkeys(limiters, 0)
    for t in TRAFFIC:
        row = []
        for name, limiter in limiters.items():
            ok = limiter.allow(t)
            totals[name] += ok
            row.append("✅ allow" if ok else "❌ 429  ")
        print(f"{t:6.1f}s " + "".join(f"{cell:>17}" for cell in row))

    print("\nallowed " + "".join(f"{totals[n]:>17}" for n in limiters))
    print(
        "\nLook at 55–63s: fixed window lets all 10 requests through in under"
        "\n8 seconds (double the limit!) because its counter resets at t=60."
        "\nEvery other algorithm stops most or all of the second burst."
    )


if __name__ == "__main__":
    main()
