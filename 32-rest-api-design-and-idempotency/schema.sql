-- Database-Level Idempotency Schema and Atomic Execution Pattern
-- Used for guaranteeing exactly-once transactional semantics at the SQL layer

CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key VARCHAR(128) PRIMARY KEY,
    payload_hash VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PROCESSING',
    response_code INT,
    response_body JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_created_at ON idempotency_keys (created_at);

-- Atomic Mutation Transaction Example
-- 1. Try inserting the idempotency key lock
-- 2. If conflict on PRIMARY KEY, abort or inspect status
-- 3. Otherwise execute business logic and save response

BEGIN TRANSACTION;

INSERT INTO idempotency_keys (idempotency_key, payload_hash, status, created_at)
VALUES ('req_payment_sample_123', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'PROCESSING', NOW());

-- Perform core business logic
INSERT INTO payment_ledger (user_id, amount, status)
VALUES ('user_alice', 250.00, 'SUCCESS');

-- Update key record with final response
UPDATE idempotency_keys
SET status = 'COMPLETED',
    response_code = 201,
    response_body = '{"charge_id": "ch_sample_123", "amount": 250.00, "status": "succeeded"}'::jsonb,
    updated_at = NOW()
WHERE idempotency_key = 'req_payment_sample_123';

COMMIT;
