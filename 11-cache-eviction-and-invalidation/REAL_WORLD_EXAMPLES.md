# Real-World Production Deep Dives: Cache Eviction and Invalidation

> Deep-dive architectural dissections of how **Meta** and **Google** solve the hardest problems in distributed caching: cache invalidation consistency, race condition prevention, and state-of-the-art eviction algorithms (W-TinyLFU).

---

## 👥 Deep Dive 1: How Meta Handles Cache Invalidation (mcrouter, Leases & The Invalidation Pipeline)

### 1. Production Context & Scale
- **System**: Meta's Memcached Fleet & mcrouter.
- **Scale**: Thousands of Memcached servers holding petabytes of user data in RAM, handling billions of requests per second.
- **The Stakes**: If a user deletes a photo or updates a privacy setting from "Public" to "Friends Only", the cache *must* be invalidated globally. Serving stale data from cache violates user privacy and legal compliance.

### 2. The Core Problem at Meta Scale: The Invalidation Race Condition
Consider a classic Cache-Aside race condition without coordination:
1. Thread 1 reads key `user_100` from Cache -> **Cache Miss**.
2. Thread 1 queries Database -> Gets old value (`v1`).
3. Thread 2 updates Database with new value (`v2`).
4. Thread 2 sends an Invalidation command to Cache -> Key `user_100` is evicted.
5. Thread 1 (which lagged due to a GC pause or network delay) finally writes its stale value `v1` into Cache!
- **Catastrophe**: The cache now holds stale data `v1` *indefinitely* until the TTL expires or another write occurs.

### 3. Meta's Engineering Solution: Leases & Invalidation Daemons

```
[ Web Application Server ]
           │
           ▼
     [ mcrouter ]  <-- Memcached Routing Proxy
           │
     ┌─────┴───────────────────────┐
     ▼                             ▼
[ Memcached Server ]     [ MySQL Primary Database ]
  └── Issues 64-bit Lease Token    │
                                   ▼ (Database Commit)
                        [ MySQL Binary Log (Binlog) ]
                                   │
                                   ▼
                       [ Wormhole Invalidation Daemon ]
                                   │
                                   ▼ (Reliable Invalidation Broadcast)
                        [ mcrouter / Memcached ]
```

#### A. Lease Tokens (Defeating Stale Race Conditions)
- When a client experiences a cache miss, the Memcached server does *not* merely return `NULL`.
- Instead, Memcached issues a **64-bit Lease Token** bound to that specific key:
  - If a database write occurs while the client is querying the DB, the cache invalidation cancels the active lease token on the server.
  - When the slow client attempts to write `v1` back into the cache, it presents its expired lease token.
  - Memcached **rejects the write**, preventing stale data from poisoning the cache!

#### B. Wormhole: Asynchronous Binlog Invalidation Pipeline
- Application servers *never* invalidate remote caches directly over HTTP (web servers can crash midway, leaving stale caches).
- Meta engineered **Wormhole**, an asynchronous invalidation pipeline:
  1. All database mutations commit to the **MySQL Binary Log (WAL)**.
  2. The Wormhole daemon tails the binlog on the database server.
  3. Whenever a row update is committed, Wormhole extracts the modified primary keys and publishes invalidation messages across high-speed internal network buses to `mcrouter` instances in all global regions.
  4. Median invalidation latency across worldwide regions is **under 50 milliseconds**.

#### C. Gutter Pools (Mitigating Server Outages)
- If a Memcached server crashes, routing requests directly to MySQL would cause immediate database overload ("thundering herd").
- Meta directs traffic for dead cache nodes to a dedicated **Gutter Pool** (a small backup cluster of cache machines). Gutter machines store entries with very short TTLs (e.g., 60 seconds), absorbing traffic spikes while the dead primary node reboots.

---

## 🏢 Deep Dive 2: How Google Uses Eviction Algorithms (Caffeine & W-TinyLFU)

### 1. Production Context & Scale
- **System**: Caffeine Cache (powering Google Guava, Cassandra, Spring, and Google Cloud services).
- **The Challenge**: Traditional eviction algorithms fail in modern high-throughput environments:
  - **LRU (Least Recently Used)**: Suffers from "Scan Pollution". If a background batch job reads 100,000 cold records sequentially, LRU evicts the entire working set of hot items.
  - **LFU (Least Frequently Used)**: Items that were popular yesterday (e.g., a viral video) remain locked in memory with sky-high frequency counters long after interest fades, preventing new trending items from entering the cache.

### 2. Google's Solution: Window TinyLFU (W-TinyLFU)

```
[ Inbound Read / Insert Key ]
             │
             ▼
┌───────────────────────────┐
│     Window Cache (LRU)    │  <-- Holds 1% of capacity (Absorbs burst traffic)
└───────────────────────────┘
             │
             ▼ (Item candidate for eviction from Window)
   [ TinyLFU Admission Policy ]  <-- 4-Bit Count-Min Sketch Frequency Filter
             │
      ┌──────┴──────────────────────┐
      ▼ (Higher Frequency)          ▼ (Lower Frequency)
┌───────────────────────────┐    [ Discarded from Cache ]
│     Main Cache (SLRU)     │
│ ├── Probationary (20%)    │
│ └── Protected (79%)       │
└───────────────────────────┘
```

#### A. The Admission Policy (The Bouncer Pattern)
- Traditional caches always accept incoming items and evict the oldest.
- W-TinyLFU asks: **"Is the incoming item more likely to be accessed again than the least valuable item currently in the cache?"**
- If the incoming item has lower historical frequency than the eviction candidate, it is rejected at the door, preserving hot memory.

#### B. 4-Bit Count-Min Sketch with Periodic Aging
- Storing full integer counters for millions of keys in LFU would consume 4-8 bytes of metadata per key (multiplying RAM costs).
- Caffeine uses a **Count-Min Sketch** with 4-bit counters:
  - Consumes only **8 bits of overhead per key**.
  - Maximum counter value is 15.
  - **Periodic Aging**: When total accesses reach a sample size ($W$), all 4-bit counters are right-shifted by 1 ($	ext{halved}$). Historical frequency decays exponentially, allowing historical viral hits to make way for new trending data.

#### C. Segmented LRU (SLRU) in the Main Cache
- Items that pass admission enter the **Probationary Segment** (20% of Main Cache).
- If accessed again while in Probation, they are promoted to the **Protected Segment** (80% of Main Cache), completely immune from eviction until capacity forces demotion back to Probation.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Meta (mcrouter & Wormhole) | Google / Caffeine (W-TinyLFU) |
|---|---|---|
| **Primary Domain** | Distributed Remote Invalidation (L6/L7 Network) | In-Memory Local Heap Eviction (Process RAM) |
| **Consistency Strategy** | Binlog tailing + 64-bit Lease Tokens | Time-based TTL + High-precision Admission Policy |
| **Eviction Algorithm** | Standard LRU per Slab Allocation class | Window TinyLFU (Probabilistic Count-Min Sketch) |
| **Scan Resistance** | Dependent on application TTL tuning | Near-perfect scan resistance via admission filter |
| **Failure Recovery** | Gutter Pool absorbs dead node traffic | Direct fallback to remote cache / persistent store |

---

## 🎯 System Design Interview Takeaways
1. **Explain the Invalidation Race Condition**: Differentiate yourself in an interview by sketching the race condition where a stale database read overwrites an invalidation. Propose **Lease Tokens** (or version timestamps) to solve it.
2. **Never Invalidate Synchronously from Web Servers**: Recommend asynchronous cache invalidation via database binlog CDC (Change Data Capture) pipelines like Debezium or Meta's Wormhole to ensure zero dropped invalidations on server crashes.
3. **Caffeine / W-TinyLFU for In-Memory Caches**: When designing application-level caching, cite **Window TinyLFU** over plain LRU to demonstrate modern knowledge of scan-resistant cache eviction.

---

## 🎬 Deep Dive 3: How Netflix Handles Cache Invalidation (Cross-Region Kafka & TTL Jitter)

### 1. Production Context & Scale
- **System**: Netflix EVCache Invalidation Pipeline.
- **Scale**: Thousands of AWS EC2 instances replicated across 3 global AWS regions.

### 2. Architecture: Probabilistic TTL Jitter & Kafka Broadcasts
- **TTL Jitter**: If 100,000 cached records are inserted with a static TTL of 3,600 seconds, they all expire at the exact same millisecond, triggering a massive **Cache Stampede**.
  - Netflix adds **Randomized TTL Jitter** (e.g., $TTL = 3600 \pm \text{random}(0, 300)$ seconds), smoothing cache expirations evenly across time.
- **Cross-Region Invalidation**:
  - When a user updates their password or subscription plan, the mutation emits an invalidation event to **Apache Kafka**.
  - Kafka consumers in all peer AWS regions immediately evict the key from their local EVCache clusters in under 100 milliseconds.

