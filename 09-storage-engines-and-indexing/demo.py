"""
Interactive Demo: Storage Engines & Indexing Mechanics
Run this script to observe the internal lifecycle of an LSM-Tree
(WAL append, MemTable flush, SSTable immutable generation, Compaction)
and how Bloom Filters eliminate unnecessary disk I/O.
"""

import math
import zlib

# ==============================================================
# 1. Bloom Filter Implementation (Zero False Negatives)
# ==============================================================
class BloomFilterSimulator:
    def __init__(self, size: int = 32):
        self.size = size
        self.bit_array = [0] * size

    def _hashes(self, key: str):
        h1 = zlib.crc32(key.encode('utf-8'))
        h2 = zlib.adler32(key.encode('utf-8'))
        return [(h1 + i * h2) % self.size for i in range(3)]

    def add(self, key: str):
        for idx in self._hashes(key):
            self.bit_array[idx] = 1

    def might_contain(self, key: str) -> bool:
        for idx in self._hashes(key):
            if self.bit_array[idx] == 0:
                return False  # GUARANTEED NOT PRESENT (0 False Negatives!)
        return True  # PROBABLY PRESENT (Potential False Positive)

# ==============================================================
# 2. LSM-Tree Storage Engine Simulator
# ==============================================================
class LSMTreeSimulator:
    def __init__(self, memtable_limit: int = 3):
        self.memtable_limit = memtable_limit
        self.memtable = {}  # In-memory sorted structure (e.g. Red-Black tree)
        self.wal_log = []   # Disk append-only log
        self.sstables = []  # List of immutable on-disk sorted tables
        self.bloom_filter = BloomFilterSimulator(size=64)

    def write(self, key: str, val: str):
        # 1. Append to WAL (Sequential disk I/O)
        self.wal_log.append(f"{key}:{val}")
        # 2. Insert into in-memory MemTable
        self.memtable[key] = val
        self.bloom_filter.add(key)
        print(f"  ✍️ [WRITE] '{key}' = '{val}' (Appended to WAL & MemTable)")

        # 3. Check flush threshold
        if len(self.memtable) >= self.memtable_limit:
            self._flush()

    def _flush(self):
        print(f"\n  💾 [MEMTABLE FLUSH] MemTable reached capacity ({self.memtable_limit} keys).")
        # Sort keys and freeze as immutable SSTable
        sorted_items = sorted(self.memtable.items())
        sstable_name = f"SSTable_Level0_#{len(self.sstables) + 1}"
        self.sstables.append((sstable_name, dict(sorted_items)))
        print(f"     -> Flushed to disk as: [{sstable_name}]: {sorted_items}")
        # Clear RAM MemTable & truncate WAL
        self.memtable.clear()
        self.wal_log.clear()

    def read(self, key: str):
        print(f"\n🔍 [READ QUERY] Looking up key '{key}'...")
        # Step A: Check in-memory MemTable first
        if key in self.memtable:
            val = self.memtable[key]
            print(f"  ⚡ Found in MemTable (RAM): '{key}' = '{val}'")
            return val

        # Step B: Check Bloom Filter before touching disk!
        if not self.bloom_filter.might_contain(key):
            print(f"  🛑 [BLOOM FILTER] Key '{key}' is DEFINITELY NOT in any SSTable! (0 Disk Reads)")
            return None

        # Step C: Search SSTables in reverse chronological order (newest to oldest)
        print("  🔎 Bloom filter passed. Scanning SSTables on disk...")
        for name, table in reversed(self.sstables):
            if key in table:
                val = table[key]
                print(f"  ✅ Found on disk in [{name}]: '{key}' = '{val}'")
                return val

        print(f"  ❌ Not found in SSTables (Bloom filter false positive).")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print(" ⚡ STEP 1: LSM-TREE WRITE PATH & MEMTABLE FLUSHING")
    print("=" * 70)
    lsm = LSMTreeSimulator(memtable_limit=3)

    # Insert 3 keys -> triggers first flush
    lsm.write("user:101", "Alice")
    lsm.write("user:102", "Bob")
    lsm.write("user:103", "Charlie")

    # Insert next batch
    print("\nWriting next batch of keys:")
    lsm.write("user:104", "Diana")
    lsm.write("user:101", "Alice Updated")  # Update to existing key!

    print("\n" + "=" * 70)
    print(" 🔎 STEP 2: READING WITH BLOOM FILTER ACCELERATION")
    print("=" * 70)
    # Read key that is in RAM MemTable
    lsm.read("user:101")

    # Read key that is on disk in SSTable #1
    lsm.read("user:102")

    # Read non-existent key: Bloom Filter rejects immediately!
    lsm.read("user:999_nonexistent")
    print("=" * 70)
