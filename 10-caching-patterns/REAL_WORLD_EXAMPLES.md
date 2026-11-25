# Real-World Production Deep Dives: Caching Patterns

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> Deep-dive architectural dissections of how **Meta** and **Netflix** implement caching at scale, exploring Meta TAO graph caching and Netflix EVCache cluster architectures.

---

## 👥 Deep Dive 1: How Meta Uses Caching (TAO: The Social Graph Distributed Cache)

### 1. Production Context & Scale
- **System**: Meta TAO (The Associative Object store).
- **Scale**: Serves over **1 billion reads per second** for the Facebook/Instagram social graph.
- **Data Model**: Models the world as **Objects** (nodes: users, posts, photos, comments) and **Associations** (edges: friendships, likes, tagged-in).
- **Cache Hit Ratio**: Greater than **99.8%**, shielding the underlying sharded MySQL database tier from over 999 out of every 1,000 read queries.

### 2. The Core Problem at Meta Scale
- Social networks have extreme read/write asymmetry (>99% reads).
- Fetching a single Facebook user profile requires traversing thousands of graph edges (friends, recent posts, liked pages, check-ins).
- Executing SQL joins across thousands of sharded MySQL databases would cause catastrophic latency (seconds per page view) and collapse database servers.

### 3. Meta's Architecture: Two-Tier Master-Follower Cache

```
[ Web Server (Client) ]
           │
           ▼
[ Follower Cache Tier (Local Region) ] ── (99.8% Cache Hits Served Locally!)
           │
           │ (Cache Miss or Write)
           ▼
[ Leader Cache Tier (Data Center Hosting Primary DB) ]
           │
           ▼ (Write-Through)
[ Sharded MySQL Database Tier ]
```

#### A. Read-Through Caching Pattern
- TAO uses a **Read-Through** architecture.
- When an application server requests an association (e.g., `get_friends(user_123)`), it asks the local **Follower Cache**:
  - **Cache Hit**: Follower cache returns the edge list in under **1 millisecond**.
  - **Cache Miss**: The Follower cache itself fetches the record from the **Leader Cache** (or database), populates its local cache memory, and returns the result to the web server.

#### B. The Write-Through Invariant with Invalidation
- Writes (e.g., user clicks "Like") must be durable:
  1. The client sends the write to the local Follower cache.
  2. The Follower cache proxies the write directly to the **Leader Cache** for that shard.
  3. The Leader cache writes through to the underlying **MySQL primary database**.
  4. Once MySQL commits, the Leader cache updates its own in-memory state and sends an asynchronous **Invalidation Message** down to all Follower caches via a dedicated pub/sub backbone.

#### C. Point-in-Time Read Consistency
- To prevent users from seeing stale data immediately after posting a comment, TAO provides **Read-After-Write Consistency (Session Consistency)**:
  - If a user performs a write, the web server caches a short-lived version token in the user's session cookie.
  - Subsequent reads from that user are routed directly to the Leader cache (or wait until the local Follower has received the invalidation message), ensuring users always see their own updates immediately.

---

## 🎬 Deep Dive 2: How Netflix Uses Caching (EVCache: Distributed In-Memory Fleet)

### 1. Production Context & Scale
- **System**: Netflix **EVCache** (Elastic, Replicated, Clustered Memcached).
- **Scale**: Thousands of AWS EC2 instances running in-memory cache nodes across multiple AWS regions.
- **Data Volume**: Tens of terabytes of hot data in RAM, handling **tens of millions of operations per second** with median read latencies **under 1 millisecond**.

### 2. The Core Problem at Netflix Scale
- Standard open-source Memcached is a single-node in-memory cache without native replication or cross-datacenter synchronization.
- If an AWS Availability Zone experienced network degradation or an EC2 instance rebooted, thousands of cached subscriber sessions were wiped, creating a massive **Cache Stampede (Thundering Herd)** on downstream Cassandra databases.

### 3. Netflix's Architecture: EVCache Cluster Architecture

```
[ Netflix Microservice (e.g., Recommendation Service) ]
           │
   EVCache Java Client
   ├── Zone-Aware Ketama Consistent Hash Ring
   ├── Probabilistic Early Expiration (Stampede Protection)
   └── Parallel Read-Aside Fallback
           │
      ┌────┴────────────────────────┐
      ▼ (Local Zone)                ▼ (Cross-Zone Async Replication)
[ EVCache Node A (us-east-1a) ]  [ EVCache Node B (us-east-1b) ]
   └── Rend Proxy                   └── Rend Proxy
         ├── Memcached (RAM)              ├── Memcached (RAM)
         └── RocksDB (Local NVMe SSD)      └── RocksDB (Local NVMe SSD)
```

#### A. Cache-Aside with Zone-Aware Ketama Hashing
- Netflix uses the **Cache-Aside (Lazy Loading)** pattern:
  1. The microservice asks the EVCache client for the key.
  2. If hit, returns data.
  3. If miss, the microservice queries Cassandra, writes the result back into EVCache with a TTL, and returns.
- **Zone-Aware Routing**: The EVCache client maintains consistent hashing rings for each AWS Availability Zone. A service in `us-east-1a` reads strictly from the cache node in `us-east-1a`, avoiding cross-AZ network latency and bandwidth transfer costs.

#### B. The "Rend" High-Performance Hybrid Proxy
- High RAM costs made storing cold items in pure memory expensive.
- Netflix engineered **Rend**, a custom C/Go server proxy sitting in front of storage engines on each cache node:
  - **Hot Data**: Kept in volatile **Memcached** (RAM) for sub-millisecond access.
  - **Warm Data**: Kept in local **RocksDB on NVMe SSDs**, allowing single cache nodes to store terabytes of data at one-tenth the cost of pure RAM instances.

#### C. Preventing Cache Stampedes via Probabilistic Early Expiration
When a popular cache key (e.g., the homepage banner for *Stranger Things*) expires, thousands of concurrent requests miss simultaneously and slam the database.
- Netflix uses **Probabilistic Early Expiration (Optimal Probabilistic Cache Refresh)**:
  - As a key approaches its expiration time, the EVCache client computes an algorithmically randomized probability based on remaining TTL and current read volume:
    $$\Delta \cdot \beta \cdot \log(\text{random}())$$
  - A single random worker thread triggers a background refresh *before* the key physically expires, refreshing the cache smoothly with zero latency spike or database stampede!

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Meta TAO | Netflix EVCache |
|---|---|---|
| **Caching Pattern** | Read-Through & Write-Through | Cache-Aside (Lazy Loading) |
| **Data Model** | Social Graph Nodes & Edges (Objects/Assocs) | Arbitrary Serialized Binary/JSON Key-Value |
| **Topology** | 2-Tier Master-Follower Hierarchical Tree | Sharded Cluster with Cross-AZ / Cross-Region Replication |
| **Stampede Defense** | Request coalescing at Leader cache tier | Probabilistic early expiration in client library |
| **Persistence Layer** | Sharded MySQL database | Multi-Region Apache Cassandra / DynamoDB |

---

## 🎯 System Design Interview Takeaways
1. **Cache-Aside vs Read-Through Tradeoff**:
   - Recommend **Cache-Aside** when the application does not need strict cache consistency and cache failures should not prevent direct database access.
   - Recommend **Read-Through/Write-Through** when you want to encapsulate caching logic away from application code and simplify data access layers.
2. **Always Address the Cache Stampede**: In any caching design interview, explicitly explain how you prevent the Thundering Herd problem using either **Mutex locks / Singleflight** or **Probabilistic Early Refresh**.
3. **Cache Eviction vs Expiration**: Clarify that **TTL (Expiration)** prevents stale data, while **Eviction (LRU/LFU)** protects the cache from running out of RAM when memory limits are reached.

---

## 🏢 Deep Dive 3: How Google Uses Caching (Multi-Tier Bigtable Block Cache & Near Cache)

### 1. Production Context & Scale
- **System**: Google Bigtable Block Cache & Web Search In-Memory Cache.
- **Scale**: Hundreds of millions of queries per second across Google Search, YouTube, and Google Cloud Bigtable.

### 2. Architecture: Multi-Tier Hierarchical Caching
- **L1 Application Near-Cache**: In-memory heap cache on frontend workers holding frequently requested user session and configuration objects (sub-millisecond access).
- **L2 Distributed Block Cache**: Bigtable Tablet Servers maintain a compressed in-memory block cache for 64KB SSTable blocks:
  - When a query misses L1, it checks the Tablet Server's in-memory block cache before touching persistent Colossus SSD storage.
  - **Cache Hit Ratio**: Over 95% of Bigtable point queries are served directly from RAM without disk I/O.

