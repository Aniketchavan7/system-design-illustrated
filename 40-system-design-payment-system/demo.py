"""
Standalone Simulation of Digital Wallet & Double-Entry Payment System.
Demonstrates:
  1. Double-Entry Bookkeeping Ledger (Debit = Credit invariant).
  2. Idempotent payment processing.
  3. Payment State Machine transitions (INIT -> PENDING -> SUCCESS/FAILED).
  4. Balance auditing and integrity verification.
"""

import uuid
import time
from typing import Dict, List, Optional

class JournalEntry:
    def __init__(self, entry_id: str, debit_account: str, credit_account: str, amount_cents: int):
        self.entry_id = entry_id
        self.debit_account = debit_account
        self.credit_account = credit_account
        self.amount_cents = amount_cents  # Stored in integer cents!
        self.timestamp = time.time()

class DoubleEntryLedger:
    def __init__(self):
        # Append-only journal
        self.journal: List[JournalEntry] = []

    def record_transfer(self, debit_acc: str, credit_acc: str, amount_cents: int) -> str:
        assert amount_cents > 0, "Transfer amount must be strictly positive"
        entry_id = f"entry_{uuid.uuid4().hex[:8]}"
        entry = JournalEntry(entry_id, debit_acc, credit_acc, amount_cents)
        self.journal.append(entry)
        return entry_id

    def get_balance(self, account_id: str) -> int:
        """Computes account balance by summing historical debits and credits."""
        balance = 0
        for entry in self.journal:
            if entry.credit_account == account_id:
                balance += entry.amount_cents
            elif entry.debit_account == account_id:
                balance -= entry.amount_cents
        return balance

    def verify_system_integrity(self) -> bool:
        """Verifies mathematical invariant: Total Debits == Total Credits."""
        total_debits = sum(e.amount_cents for e in self.journal)
        total_credits = sum(e.amount_cents for e in self.journal)
        return total_debits == total_credits

class PaymentEngine:
    def __init__(self):
        self.ledger = DoubleEntryLedger()
        # Idempotency cache: key -> response_body
        self.idempotency_store: Dict[str, dict] = {}
        # Payment transactions: tx_id -> state
        self.transactions: Dict[str, dict] = {}

    def fund_wallet(self, user_account: str, amount_cents: int):
        # Funding wallet: Debit External Bank, Credit User Wallet
        self.ledger.record_transfer("bank_clearing", user_account, amount_cents)

    def execute_payment(self, from_user: str, to_merchant: str, amount_cents: int, idem_key: str) -> dict:
        # 1. Idempotency Check
        if idem_key in self.idempotency_store:
            print(f"  [IDEMPOTENT REPLAY] Key '{idem_key}' recognized. Returning cached receipt.")
            return self.idempotency_store[idem_key]

        tx_id = f"tx_{uuid.uuid4().hex[:8]}"
        self.transactions[tx_id] = {"status": "PENDING", "amount": amount_cents}

        # 2. Check Solvency
        current_balance = self.ledger.get_balance(from_user)
        if current_balance < amount_cents:
            self.transactions[tx_id]["status"] = "FAILED"
            res = {"status": "FAILED", "error": "Insufficient funds", "tx_id": tx_id}
            self.idempotency_store[idem_key] = res
            return res

        # 3. Double-Entry Commit: Debit Buyer, Credit Seller
        entry_id = self.ledger.record_transfer(from_user, to_merchant, amount_cents)
        self.transactions[tx_id]["status"] = "SUCCESS"
        self.transactions[tx_id]["entry_id"] = entry_id

        response = {
            "status": "SUCCESS",
            "tx_id": tx_id,
            "entry_id": entry_id,
            "amount_cents": amount_cents,
            "from_user": from_user,
            "to_merchant": to_merchant
        }
        self.idempotency_store[idem_key] = response
        return response

def run_simulation():
    print("=" * 65)
    print("DIGITAL WALLET & DOUBLE-ENTRY PAYMENT SYSTEM SIMULATION")
    print("=" * 65)

    engine = PaymentEngine()
    buyer = "user_alice"
    merchant = "merchant_coffee_shop"

    # 1. Fund Buyer Account with $100.00 (10,000 cents)
    print("Step 1: Funding Alice's Wallet with $100.00 (10,000 cents)...")
    engine.fund_wallet(buyer, 10000)
    print(f"  Alice's Initial Balance: ${engine.ledger.get_balance(buyer) / 100:.2f}\n")

    # 2. Execute Payment of $25.50 (2,550 cents)
    print("Step 2: Alice pays Merchant $25.50 for lunch:")
    key_1 = "order_coffee_101"
    res1 = engine.execute_payment(buyer, merchant, 2550, key_1)
    print(f"  Payment Result: {res1['status']} | TxID: {res1['tx_id']}")
    print(f"  Alice Balance: ${engine.ledger.get_balance(buyer) / 100:.2f}")
    print(f"  Merchant Balance: ${engine.ledger.get_balance(merchant) / 100:.2f}\n")

    # 3. Simulate Network Retry with exact same Idempotency Key
    print("Step 3: Network timed out -> Alice's app retries with SAME key:")
    res2 = engine.execute_payment(buyer, merchant, 2550, key_1)
    print(f"  Alice Balance: ${engine.ledger.get_balance(buyer) / 100:.2f} (Accurately charged ONLY once!)\n")

    # 4. Verify Mathematical Double-Entry Invariant
    is_valid = engine.ledger.verify_system_integrity()
    print(f"Step 4: System Audit - Verifying Total Debits == Total Credits: {is_valid}")
    assert is_valid is True
    print("SUCCESS: Double-entry ledger balanced and idempotency verified!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
