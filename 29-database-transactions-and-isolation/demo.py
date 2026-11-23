"""
Interactive Demo: Database Transactions & Concurrency Anomalies
Simulates:
1. The Lost Update Problem (Naive concurrent reads/writes) vs Atomic CAS Defense.
2. The Write Skew Anomaly (The Doctors on Call scenario) under Snapshot Isolation vs Serializable check.
"""

import threading
import time

class AccountLedger:
    def __init__(self):
        self.balance = 100
        self.version = 1
        self.lock = threading.Lock()

    def naive_transfer(self, amount: int):
        # 1. Read balance
        current = self.balance
        # Simulate processing delay / thread switch
        time.sleep(0.001)
        # 2. Write back (Lost Update vulnerable)
        self.balance = current + amount

    def atomic_cas_transfer(self, amount: int) -> bool:
        # Optimistic Locking (Compare-and-Swap)
        with self.lock:
            current_version = self.version
            new_balance = self.balance + amount
            self.balance = new_balance
            self.version += 1
            return True

class DoctorsOnCallSystem:
    """Simulates Write Skew: Invariant requires at least 1 doctor on call."""
    def __init__(self):
        # doctor_name -> on_call (bool)
        self.doctors = {"Alice": True, "Bob": True}
        self.lock = threading.Lock()

    def snapshot_isolation_leave(self, doctor_name: str) -> bool:
        """Snapshot Isolation: Reads local snapshot, updates distinct row."""
        # Check snapshot invariant: Are there >= 2 doctors on call?
        other_doctor = "Bob" if doctor_name == "Alice" else "Alice"
        if self.doctors[other_doctor]:
            time.sleep(0.002) # Context switch
            self.doctors[doctor_name] = False
            return True
        return False

    def serializable_leave(self, doctor_name: str) -> bool:
        """Serializable Isolation: Locks on-call table before check and update."""
        with self.lock:
            other_doctor = "Bob" if doctor_name == "Alice" else "Alice"
            if self.doctors[other_doctor]:
                self.doctors[doctor_name] = False
                return True
            return False

def run_simulation():
    print("=" * 65)
    print("1. SIMULATING LOST UPDATE ANOMALY")
    print("=" * 65)
    ledger = AccountLedger()
    print(f"Initial Account Balance: ${ledger.balance}")

    # Two concurrent threads both trying to add $50
    t1 = threading.Thread(target=ledger.naive_transfer, args=(50,))
    t2 = threading.Thread(target=ledger.naive_transfer, args=(50,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"Balance after 2 x +$50 deposits (Naive): ${ledger.balance}")
    if ledger.balance == 150:
        print("💥 ANOMALY OCCURRED: One deposit was lost! Expected $200, got $150.")

    # With Atomic CAS / Locking
    ledger.balance = 100
    t1 = threading.Thread(target=ledger.atomic_cas_transfer, args=(50,))
    t2 = threading.Thread(target=ledger.atomic_cas_transfer, args=(50,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f"Balance after 2 x +$50 deposits (Atomic CAS): ${ledger.balance} (Correct!)")

    print("\n" + "=" * 65)
    print("2. SIMULATING WRITE SKEW ANOMALY (Doctors on Call)")
    print("=" * 65)
    hospital = DoctorsOnCallSystem()
    print(f"Initial State: Alice on call = {hospital.doctors['Alice']}, Bob on call = {hospital.doctors['Bob']}")

    # Alice and Bob simultaneously request to leave under Snapshot Isolation
    t_alice = threading.Thread(target=hospital.snapshot_isolation_leave, args=("Alice",))
    t_bob = threading.Thread(target=hospital.snapshot_isolation_leave, args=("Bob",))
    t_alice.start()
    t_bob.start()
    t_alice.join()
    t_bob.join()

    print(f"State after Snapshot Isolation Leave: Alice={hospital.doctors['Alice']}, Bob={hospital.doctors['Bob']}")
    if not hospital.doctors["Alice"] and not hospital.doctors["Bob"]:
        print("💥 WRITE SKEW DISASTER: Zero doctors left on call! Both committed safely under SI!")

    # Reset and test with Serializable
    hospital = DoctorsOnCallSystem()
    t_alice = threading.Thread(target=hospital.serializable_leave, args=("Alice",))
    t_bob = threading.Thread(target=hospital.serializable_leave, args=("Bob",))
    t_alice.start()
    t_bob.start()
    t_alice.join()
    t_bob.join()
    print(f"State after Serializable Leave: Alice={hospital.doctors['Alice']}, Bob={hospital.doctors['Bob']}")
    active_count = sum(1 for v in hospital.doctors.values() if v)
    print(f"Active Doctors Remaining: {active_count} (Invariant preserved by Serializable check!)")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
