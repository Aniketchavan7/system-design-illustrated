# 🔀 System Design Master Decision Flowcharts

> Architectural decision trees, evaluation flowcharts, and trade-off matrices to navigate complex system design forks during technical interviews and production RFC designs.

---

## 📑 Table of Contents
1. [Database Selection Master Flowchart](#1-database-selection-master-flowchart)
2. [Consistency Models & CAP Theorem Flowchart](#2-consistency-models--cap-theorem-flowchart)
3. [Caching Strategy & Eviction Flowchart](#3-caching-strategy--eviction-flowchart)
4. [Client-Server Communication Protocol Flowchart](#4-client-server-communication-protocol-flowchart)
5. [Message Queues vs. Event Streaming Flowchart](#5-message-queues-vs-event-streaming-flowchart)
6. [Distributed Transactions & Concurrency Flowchart](#6-distributed-transactions--concurrency-flowchart)
7. [API Rate Limiting Algorithm Flowchart](#7-api-rate-limiting-algorithm-flowchart)
8. [Database Sharding & Partition Key Flowchart](#8-database-sharding--partition-key-flowchart)
9. [Fault Tolerance & System Resilience Flowchart](#9-fault-tolerance--system-resilience-flowchart)

---

## 1. Database Selection Master Flowchart

Choosing the correct datastore is the single most critical architectural decision.

```mermaid
flowchart TD
    Start(["Data Storage Requirement"]) --> Q1{"Is the data primarily<br/>structured tabular, document,<br/>graph, time-series, or analytical?"}
    
    Q1 -->|"Analytical Queries & Aggregations<br/>(SUM, AVG, GROUP BY over billions)"| OLAP["Columnar OLAP Store<br/>(ClickHouse, BigQuery, Snowflake)"]
    Q1 -->|"Time-Stamped Numeric Readings<br/>(CPU %, metrics, sensor telemetry)"| TSDB["Time-Series Database<br/>(Prometheus, TimescaleDB, InfluxDB)"]
    Q1 -->|"Deep Entity Relationships<br/>(Social graphs, fraud rings, knowledge graphs)"| Graph["Graph Database<br/>(Neo4j, Amazon Neptune)"]
    Q1 -->|"Simple Lookup by Single Key<br/>(Sessions, tokens, cart, user profiles)"| KV["Key-Value Store<br/>(Redis, DynamoDB, Memcached)"]
    Q1 -->|"Tabular Records or Unstructured Docs"| Q2{"Do you need strict multi-row<br/>ACID transactions & foreign keys?"}
    
    Q2 -->|"Yes (Financial ledgers, orders, ERP)"| Q3{"Does the data fit on a single node<br/>(< 5TB) or require global horizontal scale?"}
    Q3 -->|"Fits on Single Node / Replicas"| RDBMS["Relational Database (SQL)<br/>(PostgreSQL, MySQL)"]
    Q3 -->|"Global Scale / Distributed ACID"| NewSQL["Distributed SQL (NewSQL)<br/>(Google Spanner, CockroachDB)"]
    
    Q2 -->|"No (Flexible schema, write scale)"| Q4{"Is access pattern nested JSON<br/>or high-throughput write append?"}
    Q4 -->|"Nested Hierarchical JSON"| Doc["Document Store<br/>(MongoDB, Couchbase)"]
    Q4 -->|"Massive Write Throughput (> 50k/s)<br/>Time-ordered IoT / Logs"| WideCol["Wide-Column Store<br/>(Apache Cassandra, ScyllaDB, Bigtable)"]
```

### Database Decision Summary Matrix

| Requirement | Recommended Technology | Why Pick It? |
| :--- | :--- | :--- |
| **ACID Financial Transactions** | PostgreSQL, MySQL | Strong consistency, foreign keys, rollback guarantees. |
| **Global Distributed ACID** | Google Cloud Spanner, CockroachDB | Multi-region linearizability without manual sharding. |
| **High-Throughput Append Writes** | Apache Cassandra, ScyllaDB | Masterless peer-to-peer ring; zero single point of failure. |
| **Sub-Millisecond Read Caching** | Redis, Memcached | Stored directly in RAM; $100\text{k}+ \text{ ops/sec}$ per node. |
| **Flexible JSON Catalog** | MongoDB, DynamoDB | Dynamic schema, fast nested indexing, document model. |
| **Social / Knowledge Graph** | Neo4j, Amazon Neptune | Traverses multi-hop edges ($N$-degrees) without expensive SQL joins. |
| **Analytical Reporting & BI** | ClickHouse, Snowflake, BigQuery | Columnar compression scans billions of rows in milliseconds. |

---

## 2. Consistency Models & CAP Theorem Flowchart

Navigating consistency vs. availability during network partitions.

```mermaid
flowchart TD
    Start(["Distributed Data Replication"]) --> Q_Partition{"Network Partition Occurs<br/>(Nodes cannot communicate)?"}
    
    Q_Partition -->|"During Partition (CAP Theorem)"| CAP_Choice{"What is the business priority?"}
    CAP_Choice -->|"Financial / Booking Accuracy<br/>(Never return stale or duplicate state)"| CP["CP System (Consistency + Partition)<br/>Reject or block writes until quorum reaches agreement<br/>(e.g., Google Spanner, Raft, etcd, ZooKeeper)"]
    CAP_Choice -->|"High Availability / Uptime<br/>(Always accept writes, resolve later)"| AP["AP System (Availability + Partition)<br/>Accept local writes on both sides of partition<br/>(e.g., Cassandra, DynamoDB, DNS)"]
    
    Q_Partition -->|"Without Partition (PACELC Theorem)"| Normal_Choice{"What is the trade-off in normal operation?"}
    Normal_Choice -->|"Prefer Lowest Read Latency"| LatencyPref["PACELC: PA / EL<br/>Read from nearest local replica<br/>(Eventual Consistency)"]
    Normal_Choice -->|"Prefer Immediate Data Freshness"| FreshnessPref["PACELC: PC / EC<br/>Synchronous replication before acknowledge<br/>(Linearizability / Strong Consistency)"]
    
    FreshnessPref --> Q_User{"User Experience Requirement?"}
    Q_User -->|"User must see their own edits immediately"| RAW["Read-After-Write Consistency<br/>Route user's reads to Leader for 10s after write"]
    Q_User -->|"Never see time go backwards"| Monotonic["Monotonic Read Consistency<br/>Pin user sessions to the same replica"]
```

---

## 3. Caching Strategy & Eviction Flowchart

Choosing when to load and update cache entries.

```mermaid
flowchart TD
    Start(["Application Data Access"]) --> Q_Type{"Is the cache read-heavy<br/>or write-heavy?"}
    
    Q_Type -->|"Read-Heavy (> 80% Reads)"| Q_Miss{"Can the application tolerate<br/>cache misses on startup?"}
    Q_Miss -->|"Yes (Standard consumer traffic)"| CacheAside["Cache-Aside (Lazy Loading)<br/>App checks Cache -> On Miss, reads DB -> Writes to Cache"]
    Q_Miss -->|"No (Predictable popular items)"| RefreshAhead["Refresh-Ahead / Warm Cache<br/>Background worker re-populates cache before TTL expires"]
    
    Q_Type -->|"Write-Heavy / Critical Durability"| Q_Durability{"Can data loss be tolerated<br/>in exchange for extreme write speed?"}
    Q_Durability -->|"No (Financial, orders, billing)"| WriteThrough["Write-Through Cache<br/>App writes to Cache -> Cache synchronously writes to DB"]
    Q_Durability -->|"Yes (Social likes, view counts, telemetry)"| WriteBehind["Write-Behind (Write-Back)<br/>App writes to Cache instantly -> Asynchronously batched to DB"]
    Q_Durability -->|"Data written once, rarely re-read"| WriteAround["Write-Around Cache<br/>App writes directly to DB, bypassing cache entirely"]

    Start --> Eviction{"Cache Memory Full: Eviction Policy"}
    Eviction -->|"Recently accessed items likely needed again"| LRU["LRU (Least Recently Used) - Default"]
    Eviction -->|"Popular historical items dominate"| LFU["LFU (Least Frequently Used) / W-TinyLFU"]
    Eviction -->|"Strict expiration times"| TTL["TTL-based Eviction"]
```

---

## 4. Client-Server Communication Protocol Flowchart

Choosing the transport mechanism between clients and backend microservices.

```mermaid
flowchart TD
    Start(["Client-Server Communication"]) --> Q_Party{"Who initiates the conversation?"}
    
    Q_Party -->|"Client Requests, Server Responds"| Q_Client{"Who is the client?"}
    Q_Client -->|"Public Mobile App or Web Browser"| REST["REST / HTTP 2 or 3<br/>Human-readable JSON, widespread tooling, edge CDN cacheable"]
    Q_Client -->|"Internal Microservice-to-Microservice"| gRPC["gRPC over HTTP/2<br/>Binary Protobuf, typed contracts, multiplexing, ultra-fast"]
    
    Q_Party -->|"Server Must Push Real-Time Data to Client"| Q_Duplex{"Does client need to send<br/>frequent messages back on same channel?"}
    Q_Duplex -->|"Yes (Bidirectional: Chat, Multiplayer gaming, Collab editing)"| WebSockets["WebSockets<br/>Persistent full-duplex TCP connection, low per-frame overhead"]
    Q_Duplex -->|"No (One-Way Server Push: Live stock ticker, sports score, notifications)"| SSE["Server-Sent Events (SSE)<br/>Lightweight text stream over standard HTTP, automatic reconnect"]
    
    Q_Party -->|"Third-Party Server-to-Server Event Trigger"| Webhooks["Webhooks (HTTP POST Callback)<br/>e.g., Stripe payment confirmation, GitHub PR notification"]
```

---

## 5. Message Queues vs. Event Streaming Flowchart

Choosing between message brokers and distributed commit logs.

```mermaid
flowchart TD
    Start(["Asynchronous Messaging Requirement"]) --> Q_Model{"What is the consumption model?"}
    
    Q_Model -->|"Task Dispatch to Worker Pool<br/>(Each task processed by EXACTLY ONE worker)"| TaskQueue{"Do tasks require strict ordering<br/>or complex routing?"}
    TaskQueue -->|"Complex topic exchange / routing headers"| RabbitMQ["RabbitMQ / ActiveMQ<br/>AMQP, smart broker, message deleted once acknowledged"]
    TaskQueue -->|"Simple cloud serverless queue"| SQS["AWS SQS / Google Cloud Tasks<br/>Managed, auto-scaling, dead-letter queues"]
    
    Q_Model -->|"Event Log Stream<br/>(Multiple independent consumers read same stream)"| Stream{"Do you need historical replay<br/>or stream processing windows?"}
    Stream -->|"Yes (Event Sourcing, Flink, Data Lake, Analytics)"| Kafka["Apache Kafka / Apache Pulsar<br/>Immutable append-only distributed commit log, retention by days"]
    Stream -->|"Ephemeral In-Memory Real-Time Broadcast<br/>(No persistence needed)"| RedisPubSub["Redis Pub/Sub<br/>Fire-and-forget in-memory pub/sub for chat/presence"]
```

---

## 6. Distributed Transactions & Concurrency Flowchart

Managing transactional boundaries across microservices.

```mermaid
flowchart TD
    Start(["Multi-Service State Mutation"]) --> Q_Scope{"Does the transaction span<br/>a single database or multiple services?"}
    
    Q_Scope -->|"Single Database Engine"| LocalACID["Local ACID Transaction<br/>(BEGIN -> COMMIT / ROLLBACK)"]
    
    Q_Scope -->|"Multiple Microservices / Databases"| Q_Latency{"Can services hold locks across network<br/>and accept high latency & low availability?"}
    
    Q_Latency -->|"Yes (Rare: Core banking clearing, strict atomic)"| TwoPC["Two-Phase Commit (2PC) / XA<br/>Coordinator prepares, then commits. High lock contention!"]
    
    Q_Latency -->|"No (Modern Microservices - Industry Standard)"| SagaChoice{"How complex is the workflow?"}
    SagaChoice -->|"Simple 2-3 step workflow"| SagaChoreo["Saga: Choreography<br/>Services publish events to Kafka; next service listens.<br/>No central coordinator."]
    SagaChoice -->|"Complex multi-step workflow with many fallbacks"| SagaOrchestrator["Saga: Orchestration<br/>Central orchestrator (Temporal, Netflix Conductor)<br/>executes state machine and triggers compensating actions"]
```

---

## 7. API Rate Limiting Algorithm Flowchart

Selecting the right rate limiting algorithm.

```mermaid
flowchart TD
    Start(["API Rate Limiting Requirement"]) --> Q_Bursts{"Does the API need to support<br/>short burst traffic gracefully?"}
    
    Q_Bursts -->|"Yes (Standard Web/Mobile APIs)"| TokenBucket["Token Bucket (Industry Standard)<br/>Tokens added at constant rate; capacity allows short bursts.<br/>Used by Stripe, AWS, GitHub."]
    
    Q_Bursts -->|"No (Downstream service requires strictly stable, smoothed flow)"| LeakyBucket["Leaky Bucket<br/>Requests queue in FIFO buffer and drip at strictly constant rate.<br/>Smooths traffic spikes."]
    
    Q_Bursts -->|"Strict sliding window boundary precision"| Q_Memory{"Can system afford memory for<br/>every single request timestamp?"}
    Q_Memory -->|"Yes (Ultra-accurate low-volume limits)"| SlidingLog["Sliding Window Log<br/>Stores exact timestamps in Redis ZSET. 100% accurate, high RAM."]
    Q_Memory -->|"No (High-volume planetary traffic)"| SlidingCounter["Sliding Window Counter<br/>Approximates rate based on weighted sum of current + previous window.<br/>Low RAM, 99% accuracy."]
```

---

## 8. Database Sharding & Partition Key Flowchart

Distributing data across database shards.

```mermaid
flowchart TD
    Start(["Database Sharding Strategy"]) --> Q_Query{"What is the dominant query access pattern?"}
    
    Q_Query -->|"Range Queries over sequential values<br/>(e.g., date ranges, alphabet ranges)"| RangeSharding["Range-Based Sharding<br/>Shard 1: Jan-Mar, Shard 2: Apr-Jun.<br/>Risk: Extreme write hotspots on current date!"]
    
    Q_Query -->|"Single Entity Point Lookups<br/>(e.g., user_id, order_id)"| HashSharding{"Do cluster nodes scale dynamically up/down?"}
    HashSharding -->|"Fixed static cluster"| ModuloHash["Hash Modulo: hash(key) % N<br/>Adding nodes requires rehashing entire database!"]
    HashSharding -->|"Dynamic cluster adding/removing nodes"| ConsistentHash["Consistent Hashing Ring with Vnodes<br/>Adding node moves only 1/N keys.<br/>Used by DynamoDB, Cassandra, Discord."]
    
    Q_Query -->|"Geographic / Regulatory Compliance<br/>(GDPR European data must stay in EU)"| GeoSharding["Geo-Partitioning<br/>Keys tagged by country code (EU, US, APAC)."]
```

---

## 9. Fault Tolerance & System Resilience Flowchart

Handling network failures, slow dependencies, and service outages.

```mermaid
flowchart TD
    Start(["Downstream Dependency Call Fails / Slows"]) --> Q_Transient{"Is the failure transient<br/>(e.g., temporary network glitch, 503 error)?"}
    
    Q_Transient -->|"Yes (Intermittent network blip)"| RetryPattern["Exponential Backoff with Full Jitter<br/>Wait = min(cap, base * 2^attempt) + random_jitter.<br/>Prevents thundering herd retries."]
    
    Q_Transient -->|"No (Downstream service is continuously timing out / dead)"| Q_FailFast{"Should callers keep waiting on timeouts?"}
    Q_FailFast -->|"No (Protect upstream thread pools)"| CircuitBreaker["Circuit Breaker Pattern<br/>Trip to OPEN after threshold failures.<br/>Fails fast in 0ms without making network call."]
    
    Start --> Isolation{"Prevent one tenant/feature from starving others"}
    Isolation --> Bulkhead["Bulkhead Pattern<br/>Isolate thread pools & connection limits per dependency/tenant.<br/>Failure in recommendations cannot crash checkout."]
    
    CircuitBreaker --> Fallback["Graceful Fallback<br/>Return stale cached response or static default rather than 500 error."]
```
