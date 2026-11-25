# Real-World Production Deep Dives: Relational vs NoSQL Databases

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> Deep-dive architectural dissections of how **Google** and **Netflix** navigate the relational vs NoSQL trade-off at multi-petabyte scale, contrasting Google Spanner/Bigtable with Netflix Cassandra/Aurora polyglot persistence.

---

## 🏢 Deep Dive 1: How Google Uses Databases (Cloud Spanner vs Bigtable)

### 1. Production Context & Scale
- **Google Spanner**: Powers Google AdWords, Google Play Billing, and Cloud Spanner. Manages billions of dollars in real-time transactions with strict ACID guarantees across worldwide data centers.
- **Google Bigtable**: Powers Google Search indexing, Google Maps, Google Earth, and YouTube monitoring. Manages petabytes of semi-structured data across millions of operations per second with sub-10ms response times.

### 2. The Core Problem at Google Scale
1. **The Traditional Relational Wall**:
   - Standard relational databases (MySQL, PostgreSQL) provide strong ACID guarantees, but scaling them horizontally requires complex manual sharding, breaking cross-shard ACID transactions and foreign keys.
2. **The Traditional NoSQL Sacrifices**:
   - First-generation NoSQL databases (Bigtable, Dynamo) scaled horizontally by abandoning ACID transactions, joins, and secondary indexes.
   - For Google AdWords (financial billing), engineers spent months writing complex application-level compensation logic to handle eventual consistency anomalies, race conditions, and phantom balance deductions.

### 3. Google's Solution: Two Specialized Architectures

```
                    [ Database Workload at Google ]
                                   │
               Does it require multi-row ACID & SQL?
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼ (YES)                             ▼ (NO - Massive Write QPS)
     [ Google Cloud Spanner ]                [ Google Bigtable ]
     ├── Globally-Distributed SQL            ├── Wide-Column NoSQL Key-Value
     ├── Synchronous Paxos Replication       ├── Appends to SSTables (LSM-tree)
     ├── TrueTime API (Atomic Clocks + GPS)  ├── Sub-10ms Point Lookups
     └── Strict Serializable ACID            └── Millions of QPS per Cluster
```

#### A. Google Cloud Spanner: Globally Distributed Relational ACID
Spanner was the world's first globally distributed database to achieve both horizontal scale and strict serializability:
- **TrueTime API**: Every Google data center contains dedicated **GPS receivers and Atomic Rubidium Clocks**. TrueTime exposes an API returning an uncertainty window: $[\text{earliest}, \text{latest}]$, guaranteeing time uncertainty $\epsilon < 7\text{ms}$.
- **Lock-Free Read Transactions**: Spanner uses TrueTime to assign globally monotonic commit timestamps. Readers read data at a past timestamp without acquiring *any* locks, completely eliminating lock contention between readers and writers.
- **Two-Phase Commit over Paxos**: Distributed writes use Paxos groups to replicate state safely across continents, followed by 2PC across Paxos leaders for multi-table transactions.

#### B. Google Bigtable: High-Throughput Wide-Column NoSQL
- Bigtable organizes data into a sparse, distributed, persistent multi-dimensional sorted map:
  $$\text{(row:string, column:string, time:int64)} \to \text{string}$$
- **Data Model**: Rows are maintained in lexicographical order.
- **High-Write Ingestion**: High-velocity analytics (e.g., crawler pages, time-series telemetry) write directly to append-only logs and memory tables (MemTables) without coordination locks, achieving millions of writes per second per cluster.

---

## 🎬 Deep Dive 2: How Netflix Uses Databases (Polyglot Persistence: Cassandra vs Aurora)

### 1. Production Context & Scale
- **Subscribers**: 260+ million worldwide streaming over 100 million hours of video daily.
- **Read/Write Asymmetry**:
  - **Viewing History & Bookmark States**: Massive write volume (every device saves playback timestamps every few seconds).
  - **Billing & Subscriptions**: Relatively low write volume, but absolute zero tolerance for inconsistencies or race conditions.

### 2. The Core Problem at Netflix Scale
- A single "one-size-fits-all" database architecture causes catastrophic failure:
  - Storing petabytes of high-velocity viewing bookmarks in a relational database caused database locks and replication lag.
  - Storing user subscription states in an eventually consistent NoSQL database led to race conditions where users could upgrade their tier but still receive "Access Denied" or double-billing errors.

### 3. Netflix's Architecture: Polyglot Persistence Strategy

```
               [ Netflix API Gateway (Zuul) ]
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
   [ Playback Service ]              [ Billing & Subscription ]
             │                                 │
             ▼                                 ▼
[ Apache Cassandra Clusters ]         [ AWS Aurora / MySQL ]
  ├── 100+ Nodes Multi-Region           ├── Multi-AZ Synchronous Replication
  ├── Key: (accountId, videoId)         ├── Strict ACID Relational Transactions
  ├── Writes: LOCAL_QUORUM              ├── Foreign Keys & Constraints
  └── Tunable Eventual Consistency      └── Guaranteed Financial Accuracy
```

#### A. Viewing History in Apache Cassandra
- **Why Cassandra**: Masterless ring architecture with zero single points of failure.
- **Data Partitioning**: The row key is `accountId`, ensuring all viewing history for a family profile is collocated on the same partition.
- **Clustering Key**: The `last_viewed_timestamp` acts as a clustering key, allowing Netflix to fetch the subscriber's "Continue Watching" carousel with a single disk seek:
  ```sql
  SELECT videoId, playback_offset 
  FROM viewing_history 
  WHERE accountId = 'user_12345' 
  ORDER BY last_viewed_timestamp DESC 
  LIMIT 20;
  ```
- **Consistency Level**: Writes use `LOCAL_QUORUM` (satisfies quorum within the local AWS region in <5ms, asynchronously replicating to peer regions).

#### B. Member Billing in AWS Aurora / MySQL
- Member registration, credit card payment tokens, plan tier changes (Standard vs Premium), and invoices live in relational **AWS Aurora MySQL**.
- **Transaction Safety**: Upgrading a subscription involves inserting an audit invoice, updating account limits, and extending the billing cycle in a single atomic database transaction (`BEGIN ... COMMIT`).

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Google Cloud Spanner | Netflix Cassandra Tier | Netflix Aurora Tier | Google Bigtable |
|---|---|---|---|---|
| **Data Model** | Relational / SQL Tables | Wide-Column Key-Value | Relational / SQL | Wide-Column Sparse Map |
| **Consistency** | Strict Serializability | Eventual / Tunable Quorum | Strong ACID (Per-Cluster) | Strong on Single Row |
| **Horizontal Scale** | Unlimited (Auto-sharding) | Linear Horizontal (Ring) | Vertical + Read Replicas | Unlimited (Tablets) |
| **Global Clocks** | Hardware TrueTime (GPS) | System NTP (LWW resolution) | Single Primary Master | System Timestamp |
| **Ideal Workload** | Global Financials & Ads | Viewing History & Telemetry | Subscriptions & Invoicing | Crawl Data & Metrics |

---

## 🎯 System Design Interview Takeaways
1. **Never Default to One Database**: Always demonstrate **Polyglot Persistence**. In high-scale system designs, explicitly separate high-volume append data (viewing history, metrics, logs -> NoSQL) from low-volume transactional state (payments, auth, user profiles -> Relational).
2. **Explain TrueTime in Spanner**: Citing TrueTime demonstrates deep distributed systems knowledge: explain that Spanner solves the CAP theorem in practice by using atomic clocks to bound time uncertainty to <7ms.
3. **Cassandra Data Modeling Rule**: In Cassandra/NoSQL interviews, emphasize that queries dictate schema design. Design tables around exact query patterns (Partition Key for distribution + Clustering Keys for sorting).
