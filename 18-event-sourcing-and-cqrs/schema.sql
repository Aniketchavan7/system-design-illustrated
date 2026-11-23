-- PostgreSQL / CockroachDB Event Store Schema
-- Enforces immutable append-only events and Optimistic Concurrency Control (OCC)
CREATE TABLE event_store (
    stream_id       VARCHAR(64) NOT NULL,
    version         BIGINT NOT NULL,
    event_type      VARCHAR(128) NOT NULL,
    payload_json    TEXT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (stream_id, version)
);
