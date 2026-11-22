"""
Interactive Demo: SQL (Relational ACID) vs NoSQL (Document & Key-Value)
Run this script to observe ACID transaction rollbacks in SQL,
polymorphic schema-less inserts in Document stores, and O(1) Key-Value lookups.
"""

import time

# ==============================================================
# 1. SQL Relational Simulator with ACID Transaction Rollback
# ==============================================================
class RelationalDatabaseSimulator:
    def __init__(self):
        self.users = {"u1": {"name": "Alice", "balance": 100.0}}
        self.orders = {}

    def execute_transaction_order(self, order_id: str, user_id: str, amount: float):
        print(f"\n[SQL RDBMS] Starting ACID Transaction for Order '{order_id}'...")
        # Step 1: Verify Foreign Key Constraint
        if user_id not in self.users:
            print("  ❌ [ROLLBACK] Foreign Key Violation: user_id does not exist in 'users' table!")
            return False

        # Step 2: Check balance constraint
        user = self.users[user_id]
        if user["balance"] < amount:
            print(f"  ❌ [ROLLBACK] Check Constraint Failed: Balance ${user['balance']} < Order ${amount}!")
            return False

        # Step 3: Atomic Mutation
        user["balance"] -= amount
        self.orders[order_id] = {"order_id": order_id, "user_id": user_id, "amount": amount}
        print(f"  ✅ [COMMIT] Transaction Committed! New User Balance: ${user['balance']}")
        return True

# ==============================================================
# 2. NoSQL Document Store Simulator (Schema-less Polymorphism)
# ==============================================================
class DocumentStoreSimulator:
    def __init__(self):
        self.collection = {}

    def insert_document(self, doc_id: str, document: dict):
        self.collection[doc_id] = document
        print(f"  📄 [NoSQL Insert] Stored Document '{doc_id}': keys={list(document.keys())}")

# ==============================================================
# 3. Key-Value Store Simulator (Microsecond O(1) Read)
# ==============================================================
class KeyValueSimulator:
    def __init__(self):
        self.kv = {}

    def set(self, key: str, val: str):
        self.kv[key] = val

    def get(self, key: str):
        return self.kv.get(key)

if __name__ == "__main__":
    print("=" * 70)
    print(" 🗄️ PART 1: SQL RELATIONAL ACID TRANSACTION & CONSTRAINTS")
    print("=" * 70)
    sql = RelationalDatabaseSimulator()

    # Successful Transaction
    sql.execute_transaction_order("ord_1", "u1", 40.0)

    # Failed Transaction: Insufficient Balance -> Rolls back atomically!
    sql.execute_transaction_order("ord_2", "u1", 80.0)

    # Failed Transaction: Foreign Key Failure -> Rolls back!
    sql.execute_transaction_order("ord_3", "u999_nonexistent", 10.0)

    print("\n" + "=" * 70)
    print(" 📄 PART 2: NoSQL DOCUMENT STORE (Polymorphic JSON Schema)")
    print("=" * 70)
    docs = DocumentStoreSimulator()
    # Storing completely different schema shapes in the exact same collection!
    docs.insert_document("prod_laptop", {
        "title": "Pro Laptop",
        "price": 1299.99,
        "specs": {"ram": "32GB", "cpu": "M3 Max", "voltage": "110V-240V"}
    })
    docs.insert_document("prod_shirt", {
        "title": "Cotton T-Shirt",
        "price": 24.99,
        "clothing_attributes": {"size": "L", "material": "100% Cotton", "colors": ["black", "navy"]}
    })
    print("  -> Notice: Zero database migrations or ALTER TABLE statements required!")

    print("\n" + "=" * 70)
    print(" ⚡ PART 3: KEY-VALUE O(1) LOOKUP")
    print("=" * 70)
    kv = KeyValueSimulator()
    kv.set("session_user_u1", "{token: 'xyz', expires: 1780000000}")
    val = kv.get("session_user_u1")
    print(f"  Microsecond Key-Value Lookup: 'session_user_u1' -> {val}")
    print("=" * 70)
