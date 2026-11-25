# Real-World Case Studies: Caching Patterns

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Three cache designs: Facebook's TAO sits in the read and write path of the social graph, Netflix's EVCache keeps copies in every availability zone, and Bigtable layers two caches inside each server.

---

## 👥 Deep Dive 1: Facebook TAO, a Cache That Owns the Read and Write Path

> **Source:** [TAO: Facebook's Distributed Data Store for the Social Graph](https://www.usenix.org/conference/atc13/technical-sessions/presentation/bronson) (Bronson et al., USENIX ATC 2013). Everything in this section comes from the paper.

- **Scale.** TAO "runs on thousands of machines" and "can process a billion reads and millions of writes each second".
- **Data model.** "TAO objects are typed nodes, and TAO associations are typed directed edges between objects." For example, a user and a post are objects, and a "like" is an association between them.
- **Not a lookaside cache.** Instead of the application reading the database and filling the cache itself, TAO's fixed API lets Facebook "move the control logic into the cache itself".
- **Two tiers.** To add servers without one giant tier, TAO splits "the cache into two levels: a leader tier and multiple follower tiers". Followers serve reads and pass misses and writes to the leader for that data.
- **Consistency.** TAO "explicitly favors availability and per-machine efficiency over strong consistency". After a write, the leader "enqueues invalidation messages to each corresponding follower". The follower that sent the write is updated straight away, which gives "read-after-write consistency within a single tier".
- **Hot items.** Some objects are read "orders of magnitude more often than other objects". Their hit rate is high enough that TAO also caches them on the client.

---

## 🎬 Deep Dive 2: Netflix EVCache, a Replicated memcached

> **Sources:** the [EVCache README](https://github.com/Netflix/EVCache) and [wiki](https://github.com/Netflix/EVCache/wiki), and the [Rend README](https://github.com/Netflix/rend), on Netflix's GitHub. Everything in this section comes from those pages.

- **What it is.** EVCache is short for **Ephemeral Volatile Cache**: data lives only as long as its TTL, and "can disappear any time". It is "a memcached & spymemcached based caching solution that is mainly used for AWS EC2 infrastructure", used through a Java client.
- **A copy in every zone.** Writes go to every availability zone, so "data is replicated across both the zones". Reads come from the local zone, which avoids cross-zone traffic and "improves the latency". The number of copies varies: "some clusters run with 2, others with 9".
- **Falling back.** If the local copy misses, clients can optionally fall back to other zones. That "will incur an additional cost but typically is a lot smaller than going to the source of truth."
- **Bigger caches on SSD.** Rend is a Go proxy that sits "on the same server as both a memcached process and an SSD-backed L2 cache", so a node can serve from memory first and from SSD second.

---

## 🏢 Deep Dive 3: Bigtable, Two Cache Levels in Each Server

> **Source:** [Bigtable: A Distributed Storage System for Structured Data](https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/) (Chang et al., OSDI 2006). Everything in this section comes from the paper.

"To improve read performance, tablet servers use two levels of caching":

| Cache | What it holds | Helps when |
| :--- | :--- | :--- |
| **Scan Cache** | The key-value pairs returned by the SSTable interface | An application "tends to read the same data repeatedly" |
| **Block Cache** | SSTable blocks read from the file system | An application reads "data that is close to the data they recently read" |

---

> ℹ️ An earlier version of this page gave TAO a "99.8%" hit rate and "under 1 millisecond" reads and applied it to Instagram, expanded EVCache as "Elastic, Replicated, Clustered Memcached", and described RocksDB on NVMe at "one-tenth the cost" and probabilistic early expiration at Netflix. The sources above don't support any of that, so we removed it.

## 🎯 System Design Interview Takeaways
1. **Lookaside vs. owning the path.** In a lookaside (cache-aside) design the application fills the cache on a miss. TAO instead puts the cache in front of every read and write, which lets it keep the cache and database in step.
2. **Tier your cache to keep each tier small.** TAO's leader and follower tiers limit how many servers must talk to each other.
3. **Replicate across failure zones.** EVCache keeps a copy per zone, so losing a zone doesn't empty the cache, and reads stay local.
4. **Cache at more than one level.** Bigtable caches both decoded rows and raw disk blocks, because different access patterns benefit from each.
