# Real-World Case Studies: Consistent Hashing

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Consistent hashing with virtual nodes in Amazon's Dynamo and Apache Cassandra, and how Discord made ring lookups fast enough to reconnect millions of users.

---

## 📦 Deep Dive 1: Amazon Dynamo, Virtual Nodes

> **Source:** [Dynamo: Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) (DeCandia et al., SOSP 2007). Everything in this section comes from the paper.

- **The idea.** Instead of placing each server at one point on the ring, "each node gets assigned to multiple points in the ring". Dynamo calls these "virtual nodes".
- **Why it helps.** The paper lists three advantages:
  1. If a node becomes unavailable, "the load handled by this node is evenly dispersed across the remaining available nodes."
  2. When a node joins or returns, it "accepts a roughly equivalent amount of load from each of the other available nodes."
  3. The number of virtual nodes per server "can be decided based on its capacity, accounting for heterogeneity in the physical infrastructure."

---

## 🗄️ Deep Dive 2: Apache Cassandra, Tokens on a Ring

> **Source:** Apache Cassandra docs, [Dynamo architecture](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html). Everything in this section comes from it.

- "Cassandra partitions data over storage nodes using a special form of hashing called consistent hashing", and "maps every node to one or more tokens on a continuous hash ring."
- "Virtual nodes solve the problem by assigning multiple tokens in the token ring to each physical node", which spreads each node's share of the data over many small ranges.

---

## 🎮 Deep Dive 3: Discord, Making Ring Lookups Fast

> **Sources:** Stanislav Vishnevskiy, ["How Discord Scaled Elixir to 5,000,000 Concurrent Users"](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users) (July 2017), and the [ex_hash_ring](https://github.com/discord/ex_hash_ring) README. Everything in this section comes from those.

- **What the ring does.** "When a session connects, it has to lookup the remote node for each guild it is interested in", using a consistent hash ring.
- **The problem.** A session server holds up to 500,000 sessions, and the average user is in 5 guilds. When many users reconnected at once, the process owning the ring "would start to get so busy that it would fail to keep up". After a crash, the lookups alone took "about 30 seconds".
- **The fixes.** Copying the ring into an ETS table cut a lookup to about 7 μs, or 17.5 seconds in total. Putting the ring in a read-only shared heap (mochiglobal, later Discord's FastGlobal) cut a lookup to "0.3us, bringing the total time down to 750ms".
- **Scale at the time.** "Nearly five million concurrent users and millions of events per second."
- **Open source.** Discord's ring library, ex_hash_ring, has a "configurable replica count for virtual nodes" (512 by default in the current version) and is "in use at Discord".

---

> ℹ️ An earlier version of this page said Discord sustains "over 100 million concurrent WebSocket connections", claimed 256 virtual nodes keep imbalance "less than 1-2%", and described Netflix EVCache's use of virtual nodes. The sources don't support those figures, so we removed them.

## 🎯 System Design Interview Takeaways
1. **Consistent hashing limits movement.** Adding or removing a server moves only the keys next to it on the ring, not almost all keys as `hash(key) % N` does.
2. **Use virtual nodes.** They spread a failed server's load across many servers, and let bigger machines take more of the ring.
3. **The lookup path matters too.** Discord's ring was correct but too slow under reconnect storms. Make lookups cheap and local.
