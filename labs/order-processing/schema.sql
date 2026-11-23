CREATE TABLE orders (
    order_id uuid PRIMARY KEY
);
CREATE TABLE order_outbox (
    event_id uuid PRIMARY KEY REFERENCES orders(order_id),
    published_at timestamptz
);
CREATE TABLE fulfillments (
    order_id uuid PRIMARY KEY REFERENCES orders(order_id),
    fulfilled_at timestamptz NOT NULL DEFAULT now()
);
