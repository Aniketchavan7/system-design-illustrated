# Real-World Case Studies: Database Partitioning and Sharding

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Three ways to split data: Bigtable splits sorted key ranges automatically, Uber's Schemaless hashes rows into a fixed set of shards, and Discord picks a composite partition key that bounds partition size.

---

## 🏢 Deep Dive 1: Google Bigtable, Range Partitioning with Automatic Splits

> **Source:** [Bigtable: A Distributed Storage System for Structured Data](https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/) (Chang et al., OSDI 2006). Everything in this section comes from the paper.

- **Sorted ranges.** "Bigtable maintains data in lexicographic order by row key. The row range for a table is dynamically partitioned. Each row range is called a tablet."
- **Automatic splitting.** "Initially, each table consists of just one tablet. As a table grows, it is automatically split into multiple tablets, each approximately 100-200 MB in size by default."
- **Assignment.** A master assigns tablets to tablet servers, and "Bigtable uses Chubby to keep track of tablet servers".
- **Choosing row keys for locality.** In the paper's web-page table, "pages in the same domain are grouped together into contiguous rows by reversing the hostname components of the URLs": `maps.google.com/index.html` is stored under `com.google.maps/index.html`. This "makes some host and domain analyses more efficient", because reading one site means scanning one contiguous range.

---

## 🚙 Deep Dive 2: Uber Schemaless, Hashing into a Fixed Set of Shards

> **Sources:** Jakob Holdgaard Thomsen, ["Designing Schemaless, Uber Engineering's Scalable Datastore Using MySQL"](https://www.uber.com/blog/schemaless-part-one-mysql-datastore/) and ["The Architecture of Schemaless"](https://www.uber.com/blog/schemaless-part-two-architecture/) (January 2016). Everything in this section comes from those posts.

- **Why.** "In early 2014, we were running out of database space due to flourishing trip growth." The new store "needed to be able to linearly add capacity by adding more servers, a property our Postgres setup lacked."
- **Fixed shard count.** "We divide the data set into a fixed number of shards (typically configured to 4096), which we then map to storage nodes." A cell goes to a shard "based on the row key of the cell". Adding capacity means remapping shards to nodes, not changing the shard count.
- **Append-only cells.** Schemaless is "append-only sharded MySQL with buffered writes". Data lives in cells, each "a JSON blob referenced by a row key, a column name, and a reference key called ref key". To update a cell, "you would write a new cell with a higher ref key".
- **Secondary indexes.** Indexes over fields in the JSON are "eventually consistent": the index entries are updated when a cell is written, but "it does not happen in the same transaction". The post adds that "most of the time the lag is well below 20ms".

---

## 💬 Deep Dive 3: Discord, a Partition Key that Bounds Partition Size

> **Sources:** [How Discord Stores Billions of Messages](https://discord.com/blog/how-discord-stores-billions-of-messages) (Stanislav Vishnevskiy, January 2017); [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) (Bo Ingram, March 2023). Everything in this section comes from those posts.

- **First attempt.** Partitioning by `channel_id` alone made busy channels' partitions grow without limit, and Cassandra warned about "partitions ... over 100MB in size". Large partitions "put a lot of GC pressure on Cassandra" and "cannot be distributed around the cluster".
- **The fix: add a time bucket.** They found that storing "about 10 days of messages within a bucket" kept partitions "comfortably" under 100 MB. The primary key became `((channel_id, bucket), message_id)`. Buckets "had to be derivable from the message_id or a timestamp", which works because Discord's IDs are Snowflakes and therefore "chronologically sortable".
- **Hot partitions later.** By 2023, many people reading the same channel at once could "hotspot a partition", raising latency for every query on those nodes. Discord added a layer of data services that route all requests for a channel to the same instance and coalesce them: "If multiple users are requesting the same row at the same time, we'll only query the database once."

> ℹ️ An earlier version of this page said Schemaless picks shards with MurmurHash3 and builds indexes from MySQL binlogs via Kafka, said Bigtable holds "exabytes", and said reversed URLs prevent hotspots. The sources don't support any of that, so we removed it.

---

## 🎯 System Design Interview Takeaways
1. **Range vs. hash partitioning.** Range partitioning (Bigtable) keeps neighbouring keys together for scans. Hashing into shards (Schemaless) spreads load evenly but makes range scans hit many shards.
2. **Fix the shard count, move the shards.** Schemaless maps rows to a fixed number of shards and remaps shards to machines as it grows, so a row's shard never changes.
3. **Design the partition key around partition size.** Discord added a time bucket to its key so no partition grows without bound.
4. **Plan for hot keys.** Even a good key can't stop many readers hitting one partition. Coalescing duplicate requests, as Discord does, is one answer.
