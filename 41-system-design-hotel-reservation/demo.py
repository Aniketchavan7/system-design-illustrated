"""
Standalone Simulation of High-Concurrency Hotel & Ticket Reservation System.
Demonstrates:
  1. Atomic temporary inventory holds with TTL countdown.
  2. Double-booking prevention across concurrent booking threads.
  3. Payment confirmation transitioning status to CONFIRMED.
  4. Automatic hold expiration returning inventory to public pool.
"""

import time
import threading
import uuid
from typing import Dict, Optional, Tuple

class InventorySlot:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.status = "AVAILABLE"  # AVAILABLE, HELD, CONFIRMED
        self.held_by: Optional[str] = None
        self.hold_expires_at: float = 0.0
        self.lock = threading.Lock()

class HotelReservationEngine:
    def __init__(self):
        # Room ID -> InventorySlot
        self.inventory: Dict[str, InventorySlot] = {
            "Room_101": InventorySlot("Room_101"),
            "Room_102": InventorySlot("Room_102")
        }
        self.confirmed_bookings: Dict[str, dict] = {}

    def attempt_hold(self, room_id: str, user_id: str, hold_duration_secs: float = 0.5) -> Tuple[bool, str]:
        slot = self.inventory.get(room_id)
        if not slot:
            return False, "Room does not exist"

        now = time.time()
        with slot.lock:
            # Check if previous hold has expired
            if slot.status == "HELD" and now > slot.hold_expires_at:
                print(f"  [AUTO-EXPIRE] Previous hold on {room_id} expired! Releasing to public.")
                slot.status = "AVAILABLE"
                slot.held_by = None

            if slot.status == "AVAILABLE":
                slot.status = "HELD"
                slot.held_by = user_id
                slot.hold_expires_at = now + hold_duration_secs
                hold_token = f"hold_{uuid.uuid4().hex[:6]}"
                return True, hold_token
            else:
                return False, f"Room {room_id} is currently {slot.status} by {slot.held_by}"

    def confirm_booking(self, room_id: str, user_id: str, hold_token: str) -> bool:
        slot = self.inventory.get(room_id)
        if not slot:
            return False

        now = time.time()
        with slot.lock:
            # Must be HELD by this user and NOT expired
            if slot.status == "HELD" and slot.held_by == user_id and now <= slot.hold_expires_at:
                slot.status = "CONFIRMED"
                booking_id = f"bk_{uuid.uuid4().hex[:6]}"
                self.confirmed_bookings[booking_id] = {
                    "booking_id": booking_id,
                    "room_id": room_id,
                    "user_id": user_id
                }
                return True
            return False

def concurrent_booker(engine: HotelReservationEngine, room_id: str, user_id: str, pay_delay: float, results: list):
    success, res = engine.attempt_hold(room_id, user_id, hold_duration_secs=0.3)
    if success:
        time.sleep(pay_delay)  # simulate time taken to pay
        confirmed = engine.confirm_booking(room_id, user_id, res)
        results.append((user_id, "CONFIRMED" if confirmed else "EXPIRED_BEFORE_PAY"))
    else:
        results.append((user_id, "REJECTED_CONCURRENT_HOLD"))

def run_simulation():
    print("=" * 65)
    print("HOTEL & TICKET RESERVATION CONCURRENCY SIMULATION")
    print("=" * 65)

    engine = HotelReservationEngine()

    print("Initial Inventory: Room_101 and Room_102 are AVAILABLE.\n")

    # 1. Simulate 5 concurrent users competing for Room_101
    print("Step 1: 5 concurrent users attempt to hold Room_101 simultaneously:")
    threads = []
    results = []

    # User_A will pay quickly (0.1s delay, before 0.3s TTL expires)
    # Others will either be rejected or time out
    users = ["User_Alice", "User_Bob", "User_Charlie", "User_David", "User_Eve"]
    for u in users:
        delay = 0.1 if u == "User_Alice" else 0.4
        t = threading.Thread(target=concurrent_booker, args=(engine, "Room_101", u, delay, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("Results of Room_101 competition:")
    for user, outcome in results:
        print(f"  {user:12} -> Outcome: {outcome}")

    # Check Room_101 status
    print(f"\nFinal Status of Room_101: {engine.inventory['Room_101'].status} (Held by: {engine.inventory['Room_101'].held_by})")
    assert engine.inventory["Room_101"].status == "CONFIRMED"

    # 2. Test Timeout Expiration on Room_102
    print("\nStep 2: User_Frank holds Room_102 but abandons checkout (TTL expires):")
    held, token = engine.attempt_hold("Room_102", "User_Frank", hold_duration_secs=0.2)
    print(f"  User_Frank hold acquired: {held} (Token: {token})")
    print("  Waiting 0.3s for hold to expire...")
    time.sleep(0.3)

    # Now User_Grace tries to book Room_102 after expiration
    held_grace, token_grace = engine.attempt_hold("Room_102", "User_Grace", hold_duration_secs=0.5)
    print(f"  User_Grace hold acquired on expired room: {held_grace} (Token: {token_grace})")
    assert held_grace is True
    print("  User_Grace completes payment...")
    confirmed_grace = engine.confirm_booking("Room_102", "User_Grace", token_grace)
    print(f"  User_Grace booking confirmed: {confirmed_grace}")
    assert confirmed_grace is True

    print("\nSUCCESS: Exactly one user booked Room_101; expired Room_102 was cleanly reclaimed!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
