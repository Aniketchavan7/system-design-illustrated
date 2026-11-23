"""
Standalone Simulation of Real-Time Ad Click Aggregation System.
Demonstrates:
  1. Tumbling 1-minute window click aggregation.
  2. Watermark event-time evaluation with bounded out-of-order latency.
  3. Late-arriving event side output routing.
  4. Real-time click-fraud deduplication window (5-second duplicate suppression).
"""

import time
from typing import Dict, List, Tuple, Optional

class RawClickEvent:
    def __init__(self, click_id: str, ad_id: str, user_id: str, event_time: int, cost_cents: int):
        self.click_id = click_id
        self.ad_id = ad_id
        self.user_id = user_id
        self.event_time = event_time  # Unix timestamp in seconds
        self.cost_cents = cost_cents

class WindowAggregation:
    def __init__(self, ad_id: str, window_start: int, window_end: int):
        self.ad_id = ad_id
        self.window_start = window_start
        self.window_end = window_end
        self.total_clicks = 0
        self.total_cost_cents = 0
        self.unique_users = set()

    def add_click(self, event: RawClickEvent):
        self.total_clicks += 1
        self.total_cost_cents += event.cost_cents
        self.unique_users.add(event.user_id)

    def __repr__(self):
        return (f"Window[{self.window_start}-{self.window_end}] Ad:{self.ad_id} -> "
                f"Clicks: {self.total_clicks}, Cost: ${self.total_cost_cents / 100:.2f}, "
                f"Unique Users: {len(self.unique_users)}")

class StreamClickAggregator:
    def __init__(self, window_size_secs: int = 60, allowed_lateness_secs: int = 120):
        self.window_size = window_size_secs
        self.allowed_lateness = allowed_lateness_secs
        
        # (ad_id, window_start) -> WindowAggregation
        self.active_windows: Dict[Tuple[str, int], WindowAggregation] = {}
        # Closed windows emitted to storage
        self.emitted_windows: List[WindowAggregation] = []
        # Late events arriving after window was closed
        self.side_output_late_events: List[RawClickEvent] = []
        
        # Fraud deduplication cache: (user_id, ad_id) -> last_event_time
        self.dedup_cache: Dict[Tuple[str, str], int] = {}
        self.watermark: int = 0

    def ingest_click(self, event: RawClickEvent) -> bool:
        # 1. Click Fraud Deduplication (5-second cooldown per user per ad)
        dedup_key = (event.user_id, event.ad_id)
        if dedup_key in self.dedup_cache:
            last_click_time = self.dedup_cache[dedup_key]
            if abs(event.event_time - last_click_time) < 5:
                print(f"  [BOT FRAUD BLOCKED] Suppressed duplicate click by {event.user_id} on {event.ad_id} within 5s!")
                return False

        self.dedup_cache[dedup_key] = event.event_time

        # 2. Advance Watermark: max(event_time) - allowed_lateness
        if event.event_time - self.allowed_lateness > self.watermark:
            self.watermark = event.event_time - self.allowed_lateness

        # 3. Compute Tumbling Window Bounds
        window_start = (event.event_time // self.window_size) * self.window_size
        window_end = window_start + self.window_size
        window_key = (event.ad_id, window_start)

        # Check if event is too late (window already closed by watermark)
        if window_end <= self.watermark:
            print(f"  [LATE EVENT DETECTED] Event {event.click_id} (ts={event.event_time}) arrived after Watermark {self.watermark} -> Diverting to Side Output!")
            self.side_output_late_events.append(event)
            return True

        # Assign to window
        if window_key not in self.active_windows:
            self.active_windows[window_key] = WindowAggregation(event.ad_id, window_start, window_end)

        self.active_windows[window_key].add_click(event)
        print(f"  [INGESTED] Click {event.click_id} -> Assigned to Window [{window_start}-{window_end}]")
        return True

    def trigger_watermark_closures(self):
        """Closes windows whose window_end <= current watermark."""
        to_close = []
        for key, win in list(self.active_windows.items()):
            if win.window_end <= self.watermark:
                to_close.append(key)

        for key in to_close:
            closed_win = self.active_windows.pop(key)
            self.emitted_windows.append(closed_win)
            print(f"  [WINDOW CLOSED & EMITTED] {closed_win}")

def run_simulation():
    print("=" * 65)
    print("AD CLICK AGGREGATION & STREAM WINDOWING SIMULATION")
    print("=" * 65)

    aggregator = StreamClickAggregator(window_size_secs=60, allowed_lateness_secs=30)

    # Base timestamp: 12:00:00 (1700000000)
    t0 = 1700000000

    print("Step 1: Normal Ingestion in Window 1 [12:00:00 - 12:01:00]:")
    aggregator.ingest_click(RawClickEvent("c1", "ad_nike", "u1", t0 + 10, cost_cents=50))
    aggregator.ingest_click(RawClickEvent("c2", "ad_nike", "u2", t0 + 25, cost_cents=50))
    aggregator.ingest_click(RawClickEvent("c3", "ad_nike", "u1", t0 + 40, cost_cents=50))

    # Test Click Fraud
    print("\nStep 2: Simulating Bot Click Fraud (Rapid double-click within 2s):")
    aggregator.ingest_click(RawClickEvent("c4", "ad_nike", "u1", t0 + 41, cost_cents=50))  # within 1s of c3!

    # Advance time to Window 2 [12:01:00 - 12:02:00]
    print("\nStep 3: Advancing stream time into Window 2 (advances Watermark):")
    aggregator.ingest_click(RawClickEvent("c5", "ad_nike", "u3", t0 + 75, cost_cents=50))
    # Event at t0 + 120 (Window 3) advances watermark to 120 - 30 = 90 (surpassing Window 1 end 60)
    aggregator.ingest_click(RawClickEvent("c6", "ad_nike", "u4", t0 + 120, cost_cents=50))
    aggregator.trigger_watermark_closures()

    # Late-arriving event from Window 1 (subway tunnel disconnect)
    print("\nStep 4: Submitting Late Event from Window 1 after Window Closure:")
    aggregator.ingest_click(RawClickEvent("c_late", "ad_nike", "u5", t0 + 15, cost_cents=50))

    print("\nStep 5: Reviewing Results:")
    print(f"  Emitted Windows Count: {len(aggregator.emitted_windows)}")
    for w in aggregator.emitted_windows:
        print(f"    -> {w}")
    print(f"  Side-Output Late Events Count: {len(aggregator.side_output_late_events)}")
    assert len(aggregator.side_output_late_events) == 1
    assert aggregator.side_output_late_events[0].click_id == "c_late"

    print("\nSUCCESS: 1-minute window aggregated, fraud suppressed, and late clicks isolated!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
