# Real-World Case Studies: Cache Eviction and Invalidation

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> How Facebook keeps memcache consistent with its databases (leases, an invalidation pipeline and a standby "Gutter" pool), and how the Caffeine library decides which entries to keep with W-TinyLFU.

---

## 👥 Deep Dive 1: Facebook Memcache, Keeping Caches Fresh

> **Source:** [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (Nishtala et al., NSDI 2013). Everything in this section comes from the paper.

Facebook's memcache deployment "handles billions of requests per second and holds trillions of items".

### Leases: stale sets and thundering herds
Leases solve two problems. A **stale set** happens when a slow client writes an outdated value back into the cache after a newer one was invalidated. A **thundering herd** happens when a popular key is invalidated and many clients hit the database at once.

- On a miss, memcached gives the client a lease: "a 64-bit token bound to the specific key the client originally requested". The client must present it when it writes the value back. If the key was invalidated in the meantime, the lease is no longer valid and the stale write is rejected.
- Each server returns a token for a key "only once every 10 seconds". Other clients asking in that window are told to wait briefly and retry, by which time "the data is often present in cache".

### Invalidation from the database's commit log
"We deploy invalidation daemons (named mcsqueal) on every database. Each daemon inspects the SQL statements that its database commits, extracts any deletes, and broadcasts these deletes" to the memcache deployment. Because invalidations come from what the database actually committed, a web server crashing mid-request can't leave stale data behind. The web server that made a change also invalidates its own cluster directly, so the user sees their own write.

### Gutter: a standby pool for failed servers
When a memcached server stops responding, its traffic goes to a small pool called Gutter, rather than straight to the database. "Gutter accounts for approximately 1% of the memcached servers in a cluster", and "entries in Gutter expire quickly". Requests are routed by **mcrouter**, a proxy that "presents a memcached server interface and routes the requests/replies to/from other servers".

---

## ☕ Deep Dive 2: Caffeine, Choosing What to Keep with W-TinyLFU

> **Sources:** Einziger, Friedman and Manes, ["TinyLFU: A Highly Efficient Cache Admission Policy"](https://arxiv.org/abs/1512.00727) (2015), and the Caffeine project's [README](https://github.com/ben-manes/caffeine), [Efficiency](https://github.com/ben-manes/caffeine/wiki/Efficiency) and [Design](https://github.com/ben-manes/caffeine/wiki/Design) pages. Everything in this section comes from those.

Caffeine is an open-source Java cache "using a Google Guava inspired API". Its README lists projects it powers, including Cassandra, Kafka, HBase and Solr.

- **Admission, not just eviction.** When the cache is full, TinyLFU compares the newcomer with the entry that would be evicted, and keeps whichever has "the highest historic usage". A one-off scan can't push out entries that are used often.
- **A cheap frequency estimate.** Frequencies are kept "in a 4-bit CountMinSketch, which requires 8 bytes per cache entry to be accurate".
- **Forgetting old popularity.** Every addition increments a counter. "Once this counter reaches the sample size (W), we divide it and all other counters in the approximation sketch by 2", so yesterday's hits fade.
- **W-TinyLFU.** New entries always land in a small LRU **window**. The window's victim then competes, through TinyLFU, for a place in the **main cache**, a segmented LRU with "80% of the space ... allocated to hot items". In Caffeine 2.0 the window was "1% of the total cache size". Current versions size it automatically with "hill climbing", favouring a larger window for recency-heavy workloads.

---

> ℹ️ An earlier version of this page credited Caffeine and W-TinyLFU to Google and said Caffeine "powers Google Guava". Caffeine is an independent project whose API was inspired by Guava's. It also called Facebook's invalidation pipeline "Wormhole", but the memcache paper describes the mcsqueal daemons. And it described Netflix's cross-region invalidation through Kafka with TTL jitter, which we couldn't source. We removed all three.

## 🎯 System Design Interview Takeaways
1. **Draw the stale-set race.** A reader misses, reads the old value, a writer updates and invalidates, then the reader writes the old value back. Leases (or version checks) stop the last step.
2. **Invalidate from the source of truth.** Tailing what the database committed, as mcsqueal does, can't miss an update the way a crashed web server can.
3. **Protect the database when a cache node dies.** A small standby pool with short TTLs, like Gutter, absorbs the misses.
4. **Eviction is also an admission decision.** W-TinyLFU only admits a new entry if it's likely to be used more than the one it would replace.
