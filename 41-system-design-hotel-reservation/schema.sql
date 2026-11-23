-- Hotel & Ticket Reservation Database Schema
-- Implements Normalized Daily Room Inventory and Atomic Reservation Holds

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC'
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id BIGSERIAL PRIMARY KEY,
    hotel_id BIGINT REFERENCES hotels(hotel_id),
    room_number VARCHAR(32) NOT NULL,
    room_type VARCHAR(64) NOT NULL, -- DELUXE, SUITE, STANDARD
    price_cents INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normalized Daily Inventory Table (1 row per room per calendar day)
CREATE TABLE IF NOT EXISTS room_daily_inventory (
    room_id BIGINT REFERENCES rooms(room_id),
    stay_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, HELD, CONFIRMED
    hold_token VARCHAR(64),
    hold_expires_at TIMESTAMP WITH TIME ZONE,
    version INT NOT NULL DEFAULT 1,
    PRIMARY KEY (room_id, stay_date)
);

CREATE INDEX IF NOT EXISTS idx_room_inv_date_status ON room_daily_inventory(stay_date, status);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id VARCHAR(64) PRIMARY KEY,
    room_id BIGINT REFERENCES rooms(room_id),
    user_id VARCHAR(64) NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_amount_cents INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, CONFIRMED, CANCELLED, EXPIRED
    hold_token VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example Atomic Multi-Day Reservation Hold Query (e.g. 2 nights)
-- UPDATE room_daily_inventory
-- SET status = 'HELD',
--     hold_token = 'token_abc123',
--     hold_expires_at = NOW() + INTERVAL '10 minutes',
--     version = version + 1
-- WHERE room_id = 101 
--   AND stay_date IN ('2026-12-31', '2027-01-01')
--   AND status = 'AVAILABLE';
