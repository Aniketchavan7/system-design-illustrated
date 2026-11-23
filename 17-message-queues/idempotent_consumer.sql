-- Idempotent Consumer Transaction
-- Prevents duplicate payment processing during network retries
BEGIN;
    INSERT INTO bank_transactions (id, amount, account_id) 
    VALUES ('tx_88', 100, 'acc_1');

    UPDATE account_balances 
    SET balance = balance + 50.00 
    WHERE account_id = 'user_99';
COMMIT;
