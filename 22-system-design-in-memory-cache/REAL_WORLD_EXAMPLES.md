# Real-World Production Deep Dives: In-Memory Cache (Redis & Twemproxy)

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> Deep-dive architectural dissections of how **Twitter / X** and **Netflix** implement massive in-memory caching fleets, prevent slab fragmentation, manage connection pooling, and sustain hundreds of millions of operations per second.

---

## 🐦 Deep Dive 1: How Twitter / X Uses In-Memory Caching (Twemproxy & Pelikan)

### 1. Production Context & Scale
- **System**: Twitter Caching Fleet (formerly Twemproxy, now **Pelikan Cache**).
- **Scale**: Hundreds of millions of queries per second across tens of thousands of cache instances holding terabytes of social graph, tweet metadata, and timeline states in RAM.
- **Latency Requirement**: P99 latency **under 1.5 milliseconds**.

### 2. The Core Problem at Twitter Scale
1. **TCP Connection Exhaustion**:
   - Thousands of frontend backend services connecting directly to hundreds of Redis/Memcached instances created millions of active TCP sockets, exhausting server file descriptors and causing CPU thrashing due to kernel context switching.
2. **Memory Fragmentation & The "Out of Memory" Paradox**:
   - Standard memory allocators (like `malloc`) suffer from memory fragmentation when handling millions of variable-sized tweet payloads. A cache node could report 90% memory utilization yet fail an allocation due to lack of contiguous free memory.

### 3. Twitter's Architecture: Twemproxy & Pelikan

```
[ Frontend API Services (Thousands of Clients) ]
                        │
                        ▼
         [ Twemproxy (nutcracker) Layer ]
  ├── Client Connection Multiplexing (1000s -> 10 persistent links)
  ├── Request Pipelining (Batches queries into single TCP packets)
  └── Consistent Hashing (Ketama ring with Virtual Nodes)
                        │
      ┌─────────────────┼─────────────────┐
      ▼                 ▼                 ▼
[ Cache Node 1 ]  [ Cache Node 2 ]  [ Cache Node 3 ]
  (Pelikan Segregated Slab Allocator Engine)
```

#### A. Connection Multiplexing via Twemproxy
- Twitter developed and open-sourced **Twemproxy** (nutcracker), an ultra-fast, lightweight C proxy:
  - Sits between application servers and the cache tier.
  - Thousands of incoming client connections are multiplexed over a tiny pool of long-lived, pre-warmed persistent connections to backend cache nodes.
  - **Request Pipelining**: Twemproxy buffers multiple read commands arriving within microsecond windows and packs them into a single TCP packet, drastically cutting network syscalls.

#### B. Pelikan & The Segregated Slab Allocator
To eliminate memory fragmentation permanently, Twitter designed **Pelikan Cache**:
- **Slab Allocation**: Memory is pre-allocated into large 1MB chunks called **Slabs**.
- Slabs are partitioned into dedicated **Slab Classes** of fixed sizes (e.g., 64 bytes, 128 bytes, 256 bytes, 512 bytes).
- A 100-byte tweet payload is strictly assigned to a 128-byte slab chunk.
- **Zero Fragmentation**: When an item expires, its chunk is returned to the slab class free-list. Memory is never freed back to the OS `malloc` pool, guaranteeing zero external memory fragmentation and eliminating memory-related server reboots.

---

## 🎬 Deep Dive 2: How Netflix Uses EVCache at Scale (Multi-Tier In-Memory Architecture)

### 1. Production Context & Scale
- **System**: Netflix **EVCache**.
- **Scale**: Thousands of AWS EC2 instances, processing tens of millions of operations per second with sub-millisecond latencies.
- **Storage Profile**: Tens of terabytes of hot in-memory data replicated across multiple AWS Availability Zones.

### 2. The Multi-Region Replication Mechanics

```
[ us-east-1 Microservice ]                   [ eu-west-1 Microservice ]
            │                                            │
            ▼                                            ▼
   [ EVCache Client East ]                      [ EVCache Client EU ]
            │                                            │
   ┌────────┴────────┐                          ┌────────┴────────┐
   ▼                 ▼                          ▼                 ▼
[ Node East-A ] [ Node East-B ]              [ Node EU-A ]   [ Node EU-B ]
   └── Rend Proxy   └── Rend Proxy              └── Rend Proxy   └── Rend Proxy
         │                 │
         └────────┬────────┘
                  │ (Async Replication via Kafka)
                  ▼
         [ Cross-Region Kafka Stream ] ──> Updates EVCache in EU & West
```

#### A. Asynchronous Multi-Region Replication
- When a user updates their profile in North America (`us-east-1`), writing synchronously to Europe (`eu-west-1`) would impose a 100ms latency penalty.
- **Netflix's Solution**:
  - The local write commits to the `us-east-1` EVCache cluster in **under 1ms**.
  - An asynchronous replication agent tails local mutations and publishes change events to an Apache Kafka topic spanning AWS regions.
  - Kafka consumers in `eu-west-1` apply the mutations to the European EVCache cluster in the background, achieving eventual consistency within 100-200 milliseconds.

#### B. The Rend Proxy Hybrid Storage (RAM + NVMe Flash)
- Pure RAM instances (AWS `r5` family) are expensive.
- Netflix engineered **Rend**, a custom C proxy placed in front of storage engines on each cache machine:
  - **Hot Tier (Memcached in RAM)**: Items accessed within the last hour sit in RAM.
  - **Warm Tier (RocksDB on NVMe SSD)**: Infrequently accessed keys are offloaded to local high-speed NVMe flash drives.
  - **Cost Savings**: Allows Netflix to store 5x more cached data per server rack at less than half the hardware cost.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Twitter Pelikan Cache | Netflix EVCache |
|---|---|---|
| **Core Storage Engine** | Custom Segregated Slab Allocator in C | Hybrid Memcached (RAM) + RocksDB (NVMe) |
| **Proxy Layer** | Centralized Twemproxy / Embedded Pelikan | Rend proxy co-located on each cache node |
| **Replication Model** | Master-Replica with Twemproxy failover | Cross-AZ synchronous + Cross-Region async via Kafka |
| **Connection Strategy** | Aggressive client multiplexing & pipelining | Client-side connection pooling in Java EVCache SDK |
| **Memory Management** | Slab classes; zero runtime OS malloc | Slab-based Memcached memory model |

---

## 🎯 System Design Interview Takeaways
1. **Never Allow Direct Connection Flooding**: In large-scale caching designs, explain that having 10,000 microservice pods connect directly to Redis exhausts file descriptors and CPU. Recommend a **connection proxy layer (like Twemproxy or Envoy)** to multiplex client connections.
2. **Slab Allocation vs Malloc**: Impress interviewers by explaining how in-memory caches avoid memory fragmentation: **Slab Allocation** pre-allocates memory into fixed chunk classes, eliminating the external fragmentation caused by standard `malloc`/`free`.
3. **RAM + NVMe Tiering**: For multi-terabyte cache designs where RAM is cost-prohibitive, propose a **hybrid storage tier (RAM for hot data + NVMe RocksDB for warm data)** inspired by Netflix's Rend architecture.

---

## 🏢 Deep Dive 3: How Google Scales In-Memory Caching (Web Search Serving Tier)

### 1. Production Context & Scale
- **System**: Google Search In-Memory Serving Cache.
- **Scale**: Billions of searches daily; sub-100 millisecond response time SLA.

### 2. Architecture: Inverted Index In-Memory Partitioning
- The web index is too massive to search on disk for every query.
- Google holds billions of hot posting lists and inverted index segments directly in distributed RAM:
  - Queries hit a front-end cache (checking if the exact query was executed seconds ago).
  - On a miss, queries scatter across in-memory search leaf nodes holding segments of the web index in RAM, ranking documents in milliseconds before aggregating results at root mixers.

