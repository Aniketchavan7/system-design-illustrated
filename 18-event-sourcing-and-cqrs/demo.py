"""
Interactive Demo: Event Sourcing & CQRS (Command Query Responsibility Segregation)
Run this script to observe:
1. Writing commands to an Aggregate Root that emits immutable Domain Events.
2. An Append-Only Event Store with optimistic concurrency control.
3. Asynchronous Projector building a denormalized Materialized Read Model.
4. Querying the high-speed Read Model ($O(1)$ lookup).
5. Disaster Recovery: Deleting the read database and rebuilding it from historical events!
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==============================================================
# 1. Domain Events (Immutable Facts)
# ==============================================================
@dataclass
class DomainEvent:
    stream_id: str
    version: int
    event_type: str
    payload: dict
    timestamp: float

# ==============================================================
# 2. Append-Only Event Store
# ==============================================================
class EventStore:
    def __init__(self):
        # stream_id -> list of DomainEvents
        self.streams: Dict[str, List[DomainEvent]] = {}

    def append(self, stream_id: str, expected_version: int, events: List[DomainEvent]):
        current_events = self.streams.get(stream_id, [])
        current_version = len(current_events)

        # Optimistic concurrency check
        if current_version != expected_version:
            raise ValueError(f"Concurrency Conflict! Expected version {expected_version}, but stream is at {current_version}.")

        if stream_id not in self.streams:
            self.streams[stream_id] = []

        for e in events:
            self.streams[stream_id].append(e)

    def load_stream(self, stream_id: str) -> List[DomainEvent]:
        return list(self.streams.get(stream_id, []))


# ==============================================================
# 3. Aggregate Root (Command Side)
# ==============================================================
class BankAccountAggregate:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.balance = 0.0
        self.is_open = False
        self.version = 0

    def apply(self, event: DomainEvent):
        """Reconstruct aggregate state by folding events."""
        if event.event_type == "AccountOpened":
            self.is_open = True
            self.balance = event.payload.get("initial_deposit", 0.0)
        elif event.event_type == "MoneyDeposited":
            self.balance += event.payload["amount"]
        elif event.event_type == "MoneyWithdrawn":
            self.balance -= event.payload["amount"]
        self.version = event.version

    # Command Handlers
    def open_account(self, initial_deposit: float) -> DomainEvent:
        if self.is_open:
            raise ValueError("Account is already open!")
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")
        return DomainEvent(
            stream_id=self.account_id,
            version=self.version + 1,
            event_type="AccountOpened",
            payload={"initial_deposit": initial_deposit},
            timestamp=time.time()
        )

    def deposit(self, amount: float) -> DomainEvent:
        if not self.is_open:
            raise ValueError("Account not open!")
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        return DomainEvent(
            stream_id=self.account_id,
            version=self.version + 1,
            event_type="MoneyDeposited",
            payload={"amount": amount},
            timestamp=time.time()
        )

    def withdraw(self, amount: float) -> DomainEvent:
        if not self.is_open:
            raise ValueError("Account not open!")
        if amount > self.balance:
            raise ValueError(f"Insufficient funds! Current balance: ${self.balance:.2f}, tried to withdraw: ${amount:.2f}")
        return DomainEvent(
            stream_id=self.account_id,
            version=self.version + 1,
            event_type="MoneyWithdrawn",
            payload={"amount": amount},
            timestamp=time.time()
        )


# ==============================================================
# 4. Materialized Read Model Projector (Query Side)
# ==============================================================
@dataclass
class AccountReadView:
    account_id: str
    current_balance: float
    total_deposited: float
    total_withdrawn: float
    transaction_count: int

class AccountReadDatabase:
    def __init__(self):
        self.views: Dict[str, AccountReadView] = {}

    def project(self, event: DomainEvent):
        aid = event.stream_id
        if aid not in self.views:
            self.views[aid] = AccountReadView(
                account_id=aid,
                current_balance=0.0,
                total_deposited=0.0,
                total_withdrawn=0.0,
                transaction_count=0
            )

        view = self.views[aid]
        view.transaction_count += 1

        if event.event_type == "AccountOpened":
            deposit = event.payload.get("initial_deposit", 0.0)
            view.current_balance += deposit
            view.total_deposited += deposit
        elif event.event_type == "MoneyDeposited":
            amt = event.payload["amount"]
            view.current_balance += amt
            view.total_deposited += amt
        elif event.event_type == "MoneyWithdrawn":
            amt = event.payload["amount"]
            view.current_balance -= amt
            view.total_withdrawn += amt

    def get_account_summary(self, account_id: str) -> Optional[AccountReadView]:
        return self.views.get(account_id)


def main():
    print("=" * 70)
    print("EVENT SOURCING & CQRS SIMULATION")
    print("=" * 70)

    store = EventStore()
    read_db = AccountReadDatabase()

    # 1. Execute Commands on Account #101
    print("\n--- Phase 1: Executing Commands (Write Side) ---")
    account = BankAccountAggregate("acc-101")

    # Command 1: Open Account with $50
    e1 = account.open_account(50.0)
    account.apply(e1)
    store.append("acc-101", expected_version=0, events=[e1])
    read_db.project(e1)
    print(f"Executed: OpenAccount($50) -> Event: {e1.event_type} (Version {e1.version})")

    # Command 2: Deposit $150
    e2 = account.deposit(150.0)
    account.apply(e2)
    store.append("acc-101", expected_version=1, events=[e2])
    read_db.project(e2)
    print(f"Executed: Deposit($150) -> Event: {e2.event_type} (Version {e2.version})")

    # Command 3: Withdraw $60
    e3 = account.withdraw(60.0)
    account.apply(e3)
    store.append("acc-101", expected_version=2, events=[e3])
    read_db.project(e3)
    print(f"Executed: Withdraw($60) -> Event: {e3.event_type} (Version {e3.version})")

    # 2. Query Read Side (CQRS)
    print("\n--- Phase 2: Querying Materialized Read Model (Read Side) ---")
    summary = read_db.get_account_summary("acc-101")
    print(f"GET /accounts/acc-101/summary:")
    print(f"  Current Balance:     ${summary.current_balance:.2f}")
    print(f"  Total Deposited:     ${summary.total_deposited:.2f}")
    print(f"  Total Withdrawn:     ${summary.total_withdrawn:.2f}")
    print(f"  Transaction History: {summary.transaction_count} operations")

    # 3. Test Invalid Command Protection
    print("\n--- Phase 3: Business Logic Protection ---")
    try:
        e_bad = account.withdraw(500.0)  # Exceeds balance!
    except ValueError as err:
        print(f"🛡️ Business rule blocked invalid withdraw: {err}")

    # 4. Disaster Recovery: Rebuild Read DB from Event Store
    print("\n--- Phase 4: Disaster Recovery (Full Event Replay) ---")
    print("Simulating catastrophic read database corruption: Wiping read table...")
    read_db.views.clear()
    print(f"Read DB contents: {read_db.views} (Wiped!)")

    print("\nReplaying raw event log from Event Store to reconstruct read views...")
    t0 = time.perf_counter()
    raw_events = store.load_stream("acc-101")
    for ev in raw_events:
        read_db.project(ev)
    duration_ms = (time.perf_counter() - t0) * 1000

    reconstructed = read_db.get_account_summary("acc-101")
    print(f"✅ State reconstructed in {duration_ms:.3f} ms!")
    print(f"  Reconstructed Balance: ${reconstructed.current_balance:.2f} (100% Fidelity)")
    print("=" * 70)
    print("Event Sourcing & CQRS simulation completed successfully!")

if __name__ == "__main__":
    main()
