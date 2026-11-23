-- Apache Cassandra / ScyllaDB Message Store Schema
-- Optimized for O(1) range queries fetching recent channel messages
CREATE TABLE messages (
    channel_id      UUID,
    message_id      TIMEUUID, -- Embeds timestamp + unique worker ID
    sender_id       UUID,
    content         TEXT,
    created_at      TIMESTAMP,
    PRIMARY KEY (channel_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
