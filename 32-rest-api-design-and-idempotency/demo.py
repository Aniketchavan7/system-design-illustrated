"""
Standalone Simulation of REST API Design & Idempotency Key Handling.
Demonstrates:
  1. Standard RESTful HTTP methods (GET, POST, PUT, DELETE).
  2. Idempotency Key locking and duplicate suppression.
  3. Payload fingerprint verification (detecting key reuse with mismatched body).
  4. Cached replay of completed idempotent mutations.
"""

import hashlib
import json
import time
import uuid
from typing import Dict, Any, Tuple, Optional

class IdempotencyRecord:
    def __init__(self, key: str, payload_hash: str):
        self.key = key
        self.payload_hash = payload_hash
        self.status = "PROCESSING"  # "PROCESSING" or "COMPLETED"
        self.response_status = 0
        self.response_body: Optional[Dict[str, Any]] = None
        self.created_at = time.time()

class IdempotentPaymentGateway:
    def __init__(self):
        # In-memory store simulating Redis Key-Value cluster
        self.idempotency_store: Dict[str, IdempotencyRecord] = {}
        # In-memory database simulating payment ledger
        self.ledger: Dict[str, Dict[str, Any]] = {}
        self.user_balances: Dict[str, float] = {"user_alice": 1000.0}

    def _hash_payload(self, method: str, path: str, body: Dict[str, Any]) -> str:
        serialized = f"{method}:{path}:{json.dumps(body, sort_keys=True)}"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def post_charge(self, user_id: str, amount: float, idempotency_key: Optional[str]) -> Tuple[int, Dict[str, Any]]:
        body = {"user_id": user_id, "amount": amount}
        path = "/v1/charges"
        method = "POST"

        if not idempotency_key:
            return 400, {"error": "Missing required 'Idempotency-Key' header"}

        payload_hash = self._hash_payload(method, path, body)

        # 1. Atomic Check & Lock
        if idempotency_key in self.idempotency_store:
            record = self.idempotency_store[idempotency_key]

            # Verify payload hash matches original request
            if record.payload_hash != payload_hash:
                return 422, {
                    "error": "Idempotency key reused with different request payload",
                    "code": "idempotency_key_mismatch"
                }

            # If still processing, return conflict
            if record.status == "PROCESSING":
                return 409, {
                    "error": "A concurrent request with this Idempotency-Key is actively being processed",
                    "code": "concurrent_mutation_in_flight"
                }

            # Return cached response instantly
            return record.response_status, {
                **record.response_body,
                "_idempotent_replay": True
            }

        # First-time key arrival: Acquire lock
        record = IdempotencyRecord(idempotency_key, payload_hash)
        self.idempotency_store[idempotency_key] = record

        # 2. Execute Business Logic
        if self.user_balances.get(user_id, 0.0) < amount:
            record.status = "COMPLETED"
            record.response_status = 402
            record.response_body = {"error": "Insufficient funds"}
            return 402, record.response_body

        # Deduct balance and create transaction
        charge_id = f"ch_{uuid.uuid4().hex[:8]}"
        self.user_balances[user_id] -= amount
        self.ledger[charge_id] = {
            "charge_id": charge_id,
            "user_id": user_id,
            "amount": amount,
            "status": "succeeded"
        }

        # 3. Commit Cache Response
        response = {
            "charge_id": charge_id,
            "user_id": user_id,
            "amount": amount,
            "status": "succeeded",
            "balance_remaining": self.user_balances[user_id]
        }
        record.status = "COMPLETED"
        record.response_status = 201
        record.response_body = response

        return 201, {**response, "_idempotent_replay": False}

    def get_charge(self, charge_id: str) -> Tuple[int, Dict[str, Any]]:
        # Safe and idempotent GET
        if charge_id not in self.ledger:
            return 404, {"error": "Charge not found"}
        return 200, self.ledger[charge_id]

    def delete_charge(self, charge_id: str) -> Tuple[int, Dict[str, Any]]:
        # Idempotent DELETE: removing an already deleted item yields same state
        if charge_id in self.ledger:
            del self.ledger[charge_id]
            return 200, {"message": f"Charge {charge_id} deleted successfully"}
        return 200, {"message": f"Charge {charge_id} does not exist (idempotent no-op)"}

def run_simulation():
    print("=" * 65)
    print("REST API & IDEMPOTENCY KEY PROTOCOL SIMULATION")
    print("=" * 65)

    gateway = IdempotentPaymentGateway()
    user = "user_alice"
    idem_key = "req_payment_9941a"

    print(f"Initial Balance for {user}: ${gateway.user_balances[user]}\n")

    # 1. First Attempt: Successful mutation
    print("--> [Request 1] Client sends POST /v1/charges ($250.00)")
    status, body = gateway.post_charge(user, 250.0, idem_key)
    print(f"<-- Response {status}: {body}\n")

    # 2. Network drop simulation & retry with same key
    print("--> [Request 2 - Retry] Client network timed out; resends POST with SAME key")
    status, body = gateway.post_charge(user, 250.0, idem_key)
    print(f"<-- Response {status}: {body}")
    print(f"    Notice: _idempotent_replay = {body.get('_idempotent_replay')}")
    print(f"    Current Account Balance: ${gateway.user_balances[user]} (Accurately charged ONLY once!)\n")

    # 3. Buggy Client: Reuses key with different amount
    print("--> [Request 3 - Buggy Client] Reuses SAME key but requests $500.00")
    status, body = gateway.post_charge(user, 500.0, idem_key)
    print(f"<-- Response {status}: {body}")
    print("    Key mismatch caught and rejected safely!\n")

    # 4. Demonstrate Idempotent DELETE
    charge_id = body.get("charge_id", "ch_sample")
    # Grab the actual created charge id
    first_charge = list(gateway.ledger.keys())[0]
    print(f"--> [DELETE Request 1] DELETE /v1/charges/{first_charge}")
    s1, b1 = gateway.delete_charge(first_charge)
    print(f"<-- Response {s1}: {b1}")

    print(f"--> [DELETE Request 2 - Repeated] DELETE /v1/charges/{first_charge}")
    s2, b2 = gateway.delete_charge(first_charge)
    print(f"<-- Response {s2}: {b2}")
    print("    DELETE is idempotent: repeated calls produce identical state!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
