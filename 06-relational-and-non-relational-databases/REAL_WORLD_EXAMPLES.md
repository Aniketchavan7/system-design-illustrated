# Real-World Case Studies: Relational and Non-Relational Databases

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Google built a NoSQL store (Bigtable), then a relational one with transactions (Spanner), and explained why. Discord moved its messages from MongoDB to Cassandra to ScyllaDB as it grew.

---

## 🏢 Deep Dive 1: Google Bigtable, a Wide-Column Store

> **Source:** [Bigtable: A Distributed Storage System for Structured Data](https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/) (Chang et al., OSDI 2006). Everything in this section comes from the paper.

- **Data model.** "A Bigtable is a sparse, distributed, persistent multidimensional sorted map. The map is indexed by a row key, column key, and a timestamp."
- **What it gives up.** "Every read or write of data under a single row key is atomic", but there are no general transactions across rows.
- **Scale it was built for.** "Petabytes of data across thousands of commodity servers." In 2006 it was used by "more than sixty Google products and projects, including Google Analytics, Google Finance, Orkut, Personalized Search, Writely, and Google Earth".
- **Layout.** Rows are stored "in lexicographic order by row key", so reading a range of nearby keys touches few machines.

---

## 🏢 Deep Dive 2: Google Spanner, Bringing Back Transactions

> **Source:** [Spanner: Google's Globally-Distributed Database](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (Corbett et al., OSDI 2012). Everything in this section comes from the paper.

- **What it is.** "Spanner is Google's scalable, multi-version, globally-distributed, and synchronously-replicated database." The authors call it "the first system to distribute data at global scale and support externally-consistent distributed transactions".
- **Why Google built it.** The paper is direct about Bigtable's limits: "the lack of cross-row transactions in Bigtable led to frequent complaints". It argues it is "better to have application programmers deal with performance problems due to overuse of transactions as bottlenecks arise, rather than always coding around the lack of transactions."
- **First customer.** "Our initial customer was F1, a rewrite of Google's advertising backend. F1 uses five replicas spread across the United States."
- **How it stays consistent.** A time API called TrueTime, built on "GPS and atomic clocks", reports how uncertain the current time is. Module 29 covers how Spanner uses it.

---

## 💬 Deep Dive 3: Discord, from MongoDB to Cassandra to ScyllaDB

> **Sources:** [How Discord Stores Billions of Messages](https://discord.com/blog/how-discord-stores-billions-of-messages) (Stanislav Vishnevskiy, January 2017); [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) (Bo Ingram, March 2023). Everything in this section comes from those posts.

1. **MongoDB (2015).** Messages lived in "a MongoDB collection with a single compound index on channel_id and created_at". By November 2015, at 100 million stored messages, "the data and the index could no longer fit in RAM and latencies started to become unpredictable". Reads were "extremely random" and the read/write ratio "about 50/50".
2. **Cassandra (2017).** "Cassandra was the only database that fulfilled all of our requirements": they could "just add nodes to scale it", and it tolerates losing nodes. In 2017 they ran "a 12 node cluster with a replica factor of 3".
3. **ScyllaDB (2022).** By early 2022 the cluster had grown to "177 nodes with trillions of messages", and hot partitions, compaction backlogs and garbage-collection pauses made latency unpredictable. They moved to ScyllaDB, "going from running 177 Cassandra nodes to just 72 ScyllaDB nodes". Fetching historical messages went from a p99 of "40-125ms on Cassandra" to "15ms" on ScyllaDB.

> ℹ️ An earlier version of this page described Netflix storing viewing history in Cassandra and billing in Aurora, and gave "sub-10ms" and "millions of operations per second" figures for Bigtable. We couldn't find sources we could read for any of that, so we replaced it with the sections above.

---

## 🎯 System Design Interview Takeaways
1. **Choose by access pattern, not fashion.** Discord picked Cassandra for random reads, a 50/50 read/write mix, and the ability to add nodes. Name the access pattern before naming a database.
2. **Know what you give up.** Bigtable makes single-row operations atomic and nothing more. If your design needs multi-row invariants, say how you'll enforce them, or pick a store with transactions.
3. **Transactions can scale.** Spanner's authors chose to offer transactions and deal with their cost, rather than make every application code around their absence.
