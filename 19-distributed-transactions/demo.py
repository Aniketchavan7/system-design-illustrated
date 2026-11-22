"""
Interactive Demo: Distributed Transactions — Saga Pattern & Transactional Outbox
Run this script to observe:
1. Orchestrated Saga Happy Path (Order Created -> Inventory Reserved -> Payment Charged).
2. Saga Failure & Compensating Transactions (Payment Declined -> Inventory Restored -> Order Cancelled).
3. The Transactional Outbox Pattern preventing the dreaded Dual-Write Problem.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# ==============================================================
# 1. Independent Microservices (Database-per-Service)
# ==============================================================
class InventoryService:
    def __init__(self, stock: int = 10):
        self.stock = stock
        self.reservations: Dict[str, int] = {}

    def reserve(self, order_id: str, qty: int) -> bool:
        if self.stock >= qty:
            self.stock -= qty
            self.reservations[order_id] = qty
            return True
        return False

    def compensate_release(self, order_id: str):
        """Compensating action: reverse the inventory reservation."""
        if order_id in self.reservations:
            qty = self.reservations.pop(order_id)
            self.stock += qty


class PaymentService:
    def __init__(self):
        self.charged_orders = set()

    def process_payment(self, order_id: str, amount: float, card_valid: bool = True) -> bool:
        if not card_valid:
            return False
        self.charged_orders.add(order_id)
        return True

    def compensate_refund(self, order_id: str):
        """Compensating action: refund charged payment."""
        self.charged_orders.discard(order_id)


class OrderService:
    def __init__(self):
        # order_id -> status
        self.orders: Dict[str, str] = {}

    def create_pending(self, order_id: str):
        self.orders[order_id] = "PENDING"

    def confirm(self, order_id: str):
        self.orders[order_id] = "CONFIRMED"

    def cancel(self, order_id: str):
        self.orders[order_id] = "CANCELLED"


# ==============================================================
# 2. Saga Orchestrator
# ==============================================================
class CheckoutSagaOrchestrator:
    def __init__(self, order_svc: OrderService, inv_svc: InventoryService, pay_svc: PaymentService):
        self.order_svc = order_svc
        self.inv_svc = inv_svc
        self.pay_svc = pay_svc

    def execute_checkout(self, order_id: str, amount: float, qty: int, card_valid: bool = True) -> str:
        # Step 1: Create Order in PENDING state
        self.order_svc.create_pending(order_id)
        print(f"  [Step 1] OrderService created order '{order_id}' (Status: PENDING)")

        # Step 2: Reserve Inventory
        reserved = self.inv_svc.reserve(order_id, qty)
        if not reserved:
            self.order_svc.cancel(order_id)
            return "FAILED: Out of Stock -> Order Cancelled"
        print(f"  [Step 2] InventoryService reserved {qty} item(s). Remaining stock: {self.inv_svc.stock}")

        # Step 3: Authorize Payment
        paid = self.pay_svc.process_payment(order_id, amount, card_valid=card_valid)
        if not paid:
            print(f"  [Step 3] 💥 PaymentService: Payment Declined (Card Invalid)!")
            # Trigger Compensating Transaction!
            print(f"  [Compensation] Rolling back Step 2: Restoring inventory stock...")
            self.inv_svc.compensate_release(order_id)
            self.order_svc.cancel(order_id)
            print(f"  [Compensation] Order '{order_id}' marked CANCELLED. Restored stock: {self.inv_svc.stock}")
            return "FAILED: Payment Declined -> Cleanly Rolled Back via Compensation"

        # Step 4: Confirm Order
        self.order_svc.confirm(order_id)
        print(f"  [Step 4] Payment Charged! Order '{order_id}' CONFIRMED.")
        return "SUCCESS: Order Fully Completed"


# ==============================================================
# 3. Transactional Outbox Pattern
# ==============================================================
@dataclass
class OutboxRecord:
    event_id: str
    aggregate_type: str
    aggregate_id: str
    payload: str
    published: bool = False

class TransactionalOutboxDatabase:
    def __init__(self):
        self.business_table: Dict[str, dict] = {}
        self.outbox_table: List[OutboxRecord] = []

    def atomic_create_order(self, order_id: str, details: dict):
        """Simulates atomic local SQL transaction: BEGIN ... COMMIT."""
        # 1. Insert into business table
        self.business_table[order_id] = details
        # 2. Insert event into outbox table in the SAME transaction
        outbox_event = OutboxRecord(
            event_id=f"evt_{order_id}",
            aggregate_type="Order",
            aggregate_id=order_id,
            payload=f"OrderCreated({details})"
        )
        self.outbox_table.append(outbox_event)

    def relay_events_to_bus(self) -> List[str]:
        published = []
        for record in self.outbox_table:
            if not record.published:
                # Publish to message broker (e.g. Kafka / SNS)
                record.published = True
                published.append(record.payload)
        return published


def main():
    print("=" * 70)
    print("DISTRIBUTED TRANSACTIONS: SAGAS & OUTBOX SIMULATION")
    print("=" * 70)

    orders = OrderService()
    inventory = InventoryService(stock=10)
    payment = PaymentService()
    orchestrator = CheckoutSagaOrchestrator(orders, inventory, payment)

    # ---------------------------------------------------------
    # Scenario 1: Happy Path Saga
    # ---------------------------------------------------------
    print("\n--- Scenario 1: Saga Happy Path (Order #101) ---")
    result1 = orchestrator.execute_checkout("order-101", amount=120.0, qty=1, card_valid=True)
    print(f"Result: {result1}")
    print(f"Current Order Status: {orders.orders['order-101']}")
    print(f"Current Inventory Stock: {inventory.stock}")

    # ---------------------------------------------------------
    # Scenario 2: Failure & Compensating Transaction
    # ---------------------------------------------------------
    print("\n--- Scenario 2: Saga Failure & Compensating Rollback (Order #102) ---")
    result2 = orchestrator.execute_checkout("order-102", amount=450.0, qty=2, card_valid=False)
    print(f"Result: {result2}")
    print(f"Current Order Status: {orders.orders['order-102']}")
    print(f"Current Inventory Stock: {inventory.stock} (Stock cleanly preserved!)")

    # ---------------------------------------------------------
    # Scenario 3: The Transactional Outbox Pattern
    # ---------------------------------------------------------
    print("\n--- Scenario 3: The Transactional Outbox Pattern (Atomicity) ---")
    outbox_db = TransactionalOutboxDatabase()
    print("Writing Order #103 to local DB and Outbox in a single ACID transaction...")
    outbox_db.atomic_create_order("order-103", {"item": "Laptop", "total": 1200})

    print(f"Local Business Table: {outbox_db.business_table}")
    print(f"Outbox Table: {[r.payload for r in outbox_db.outbox_table]}")

    print("\nBackground Outbox Publisher waking up to relay events to Kafka...")
    events_sent = outbox_db.relay_events_to_bus()
    print(f"Events reliably dispatched to broker: {events_sent}")
    print("✅ Zero Dual-Write Inconsistency possible!")
    print("=" * 70)
    print("Simulation completed successfully!")

if __name__ == "__main__":
    main()
