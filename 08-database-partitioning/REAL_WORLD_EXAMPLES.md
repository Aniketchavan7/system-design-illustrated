# Real-World Production Deep Dives: Database Partitioning & Sharding

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> Deep-dive architectural dissections of how **Google** and **Uber/Netflix** partition databases to scale to billions of records, prevent hot shards, and handle dynamic rebalancing.

---

## 🏢 Deep Dive 1: How Google Uses Partitioning (Bigtable Tablet Splitting & Range Partitioning)

### 1. Production Context & Scale
- **System**: Google Bigtable.
- **Data Volume**: Exabytes of data distributed across hundreds of thousands of commodity machines.
- **Operations**: Hundreds of millions of continuous read/write operations per second.

### 2. The Core Problem at Google Scale
- Static hash sharding (e.g., `hash(key) % N`) fails when the volume of data grows dynamically:
  - If you double the number of servers, every single key must be rehashed and moved across the network, saturating data center switches.
  - Hash sharding destroys range query efficiency: scanning keys from `user:1000` to `user:2000` requires querying every single shard in the cluster.

### 3. Google's Architecture: Dynamic Range-Based Tablet Splitting

```
[ Table Sorted Lexicographically by Row Key ]
┌─────────────────────────────────────────────────────────────┐
│  "aaa" ──> "com.google.a" ──> "com.google.m" ──> "zzz"      │
└─────────────────────────────────────────────────────────────┘
                               │
                 Split into Tablets (~100MB - 200MB)
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
 [ Tablet 1: "a" - "g" ] [ Tablet 2: "h" - "p" ] [ Tablet 3: "q" - "z" ]
       │                       │                       │
       ▼                       ▼                       ▼
 [ Tablet Server 1 ]     [ Tablet Server 2 ]     [ Tablet Server 3 ]
```

#### A. Lexicographically Sorted Row Keys
- Bigtable maintains all rows in sorted alphabetical order by row key.
- **Range Queries are Localized**: Scanning a contiguous range of keys reads from a single or small sequence of tablets, achieving maximum sequential disk I/O performance.

#### B. Dynamic Tablet Splitting
- A table starts as a single tablet.
- As rows are inserted and a tablet grows beyond **100MB to 200MB**, the hosting Tablet Server automatically splits the tablet into two equal halves at a middle row key.
- The Tablet Server updates the root metadata in Chubby/Colossus. The **Master Server** detects unbalanced server loads and migrates tablet leases to underutilized servers in the cluster without copying underlying storage files (since files reside in Google's Colossus distributed filesystem).

#### C. The Domain-Reversal Pattern (Preventing Hotspotting)
When storing web crawler pages, sequential URLs like:
- `http://google.com/search`
- `http://google.com/images`
- `http://google.com/maps`
would all cluster onto the same tablet server, creating a massive write hotspot.
- **Google's Inverted Row Key Pattern**:
  Google stores URLs with reversed domain names:
  `com.google/search`, `com.google/images`, `com.google/maps`.
  This clusters pages from the same site together for efficient sub-domain scans while naturally dispersing traffic from millions of distinct domains across the entire cluster.

---

## 🚙 Deep Dive 2: How Uber Uses Sharding ("Schemaless" Sharded MySQL Architecture)

### 1. Production Context & Scale
- **System**: Uber "Schemaless" (built on top of sharded MySQL clusters).
- **Scale**: Hundreds of millions of global ride trips, driver locations, and fare calculations.
- **Availability Requirement**: Five-nines. Drivers and riders cannot be stranded due to database failovers.

### 2. The Core Problem at Uber Scale
- In 2014, Uber's Postgres database was crumbling under write load during peak commute hours. Secondary index updates and write amplification caused replication lag exceeding minutes.
- Commercial NoSQL databases lacked proven reliability and transactional tooling, while raw MySQL could not scale horizontally on a single instance.

### 3. Uber's Architecture: Schemaless Sharded MySQL

```
[ Inbound Ride Trip Event ]
             │
             ▼
[ Uber Schemaless Routing Proxy ]
   ├── Computes Shard ID: MurmurHash(trip_uuid) % 4096
   ├── Locates Host for Shard in Routing Table
   └── Dispatches Append-Only Mutation
             │
      ┌──────┴──────┐
      ▼             ▼
[ MySQL Shard 01 ] [ MySQL Shard 02 ] ... [ MySQL Shard 4096 ]
  (Master)           (Master)
    ├── Local Replication to 2 In-Rack Replicas
    └── Append-Only Cell Data Model
```

#### A. Fixed Virtual Shards (4,096 Shards)
- Uber established **4,096 virtual shards** partitioned across dozens of physical MySQL server pairs.
- Each trip is assigned a globally unique UUID. The routing proxy determines the shard:
  $$\text{Shard ID} = \text{MurmurHash3}(\text{trip\_uuid}) \pmod{4096}$$
- **Zero Resharding Required**: As data grew, Uber moved virtual shards across physical database servers without changing the hashing formula.

#### B. Append-Only Cell Model
To completely eliminate row locks and database deadlocks:
- Schemaless never executes SQL `UPDATE` statements!
- Data is modeled as **immutable cells**:
  - Each cell has a `row_key` (e.g., `trip_uuid`), `column_name` (e.g., `status`), and `ref_key` (auto-incrementing version number: 1, 2, 3).
  - When a ride changes status from `REQUESTED` to `DISPATCHED` to `COMPLETED`, Uber inserts a **new cell version** with an incremented `ref_key`.
  - The latest state is simply the cell with the highest version number.

#### C. Secondary Indexing via Async Triggers
- Sharding by `trip_uuid` makes querying by `driver_uuid` impossible without querying all 4,096 shards ("scatter-gather").
- Uber solves this by publishing mutation events to **Kafka** from MySQL binlogs. An indexing worker consumes the event and writes a secondary mapping `(driver_uuid -> trip_uuid)` into a dedicated index shard.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Google Bigtable | Uber Schemaless | Netflix Cassandra |
|---|---|---|---|
| **Partitioning Strategy** | Range-Based (Lexicographical) | Hash-Based (Virtual Shards) | Hash-Based (Consistent Hash Ring) |
| **Rebalancing Mechanism** | Dynamic automated split & lease move | Manual/Automated virtual shard remapping | Node addition distributes vnodes automatically |
| **Range Query Support** | First-class, highly efficient | Poor (Requires scatter-gather) | Only within single partition key |
| **Hotspot Risk** | High on monotonically increasing keys | Low (Randomized uniform hashing) | Low (Cryptographic hashing) |
| **Underlying Engine** | Google Colossus + SSTables | Sharded MySQL InnoDB | Custom Cassandra LSM Engine |

---

## 🎯 System Design Interview Takeaways
1. **Range vs Hash Partitioning Tradeoff**:
   - Recommend **Range Partitioning** when the application requires efficient range scans (e.g., time-series data, alphabetized directories), but address the risk of write hotspots on sequential keys.
   - Recommend **Hash Partitioning** for uniform write distribution across all nodes when point lookups are the dominant query pattern.
2. **The "Scatter-Gather" Trap**: If you shard by `userId`, querying by `orderDate` requires sending the query to *every single shard* and aggregating results in memory. Explain how to avoid this via **Global Secondary Indexes** maintained asynchronously via message queues.
3. **Virtual Shards**: Always propose virtual shards (e.g., 4096 fixed logical shards) to simplify future physical rebalancing without rehashing keys.
