# Real-World Case Studies: Storage Engines and Indexing

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> One design, three generations: Bigtable's memtable-and-SSTable engine (based on the 1996 LSM-tree), LevelDB, which is "similar in spirit" to a Bigtable tablet, and RocksDB, which started as a fork of LevelDB.

---

## 🏢 Deep Dive 1: Bigtable's Write Path

> **Source:** [Bigtable: A Distributed Storage System for Structured Data](https://research.google/pubs/bigtable-a-distributed-storage-system-for-structured-data/) (Chang et al., OSDI 2006). Everything in this section comes from the paper.

- **Writes.** Updates are "committed to a commit log", and "the recently committed ones are stored in memory in a sorted buffer called a memtable; the older updates are stored in a sequence of SSTables."
- **Compactions.** When the memtable reaches a threshold it is frozen and written out as an SSTable ("minor compaction"). A "merging compaction" combines a few SSTables and the memtable into one. A merging compaction that rewrites everything into a single SSTable is a "major compaction", and only that one removes deleted data for good.
- **Reads.** A read uses "a merged view of the sequence of SSTables and the memtable". To avoid touching every SSTable on disk, clients can ask for **Bloom filters**, which tell you whether an SSTable might contain the row and column you want. They're opt-in, per locality group.
- **Where the idea comes from.** The paper says this design "is analogous to the way that the Log-Structured Merge Tree stores updates to index data", citing O'Neil et al. (1996).

---

## 🗂️ Deep Dive 2: LevelDB, Levels of Sorted Files

> **Sources:** LevelDB [implementation notes](https://github.com/google/leveldb/blob/main/doc/impl.md) and [README](https://github.com/google/leveldb) (authors Sanjay Ghemawat and Jeff Dean). Everything in this section comes from those.

- **Lineage.** "The implementation of leveldb is similar in spirit to the representation of a single Bigtable tablet."
- **Writes.** Updates go to a log file, with a copy in memory (the memtable). "When the log file reaches a pre-determined size (approximately 4MB by default), it is converted to a sorted table" in level 0.
- **Levels.** Files in level 0 "may contain overlapping keys", but files in other levels "have distinct non-overlapping key ranges". Level 0 is compacted when it holds more than four files. Level L is compacted when it exceeds 10^L MB (10 MB for level 1, 100 MB for level 2, and so on).
- **Compaction.** "The compaction picks a file from level L and all overlapping files from the next level L+1" and merges them. "Compactions drop overwritten values". Deletion markers are dropped only when no deeper level could still hold the key.

---

## 🔬 Deep Dive 3: RocksDB, LevelDB Tuned for Flash

> **Source:** the [RocksDB Overview](https://github.com/facebook/rocksdb/wiki/RocksDB-Overview) wiki page. Everything in this section comes from it.

- **Origin.** "RocksDB started at Facebook as a storage engine for server workloads on various storage media", with "the initial focus on fast storage (especially Flash storage)". "The initial code was forked from open source leveldb 1.5."
- **Choose your trade-off.** RocksDB offers several compaction styles: Level Style (the default), Universal Style, which "typically results in lower write-amplification but higher space- and read-amplification", and FIFO Style, for cache-like data.
- **Other additions.** Column families partition one database into several, compactions "may occur in multiple threads", and a prefix extractor adds prefix hashes to the Bloom filter for prefix scans.

> ℹ️ An earlier version of this page said Google's LevelDB "pioneered" the LSM-tree, which predates it by more than a decade, and quoted MyRocks storage savings, ZippyDB throughput and Netflix's use of RocksDB in Flink and Mantis. None of the sources above cover those, so we removed them.

---

## 🎯 System Design Interview Takeaways
1. **LSM-trees turn random writes into sequential ones.** Buffer writes in memory, flush sorted files, and merge them in the background.
2. **Compaction is the cost.** Every byte may be rewritten several times as files merge (write amplification). RocksDB's compaction styles let you trade that against space and read cost.
3. **Bloom filters keep reads cheap.** They let a read skip files that definitely don't contain the key.
