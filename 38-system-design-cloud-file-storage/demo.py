"""
Standalone Simulation of Cloud File Storage & Delta Sync (Google Drive / Dropbox).
Demonstrates:
  1. File Chunking into 4MB uniform blocks.
  2. SHA-256 Block Deduplication across files.
  3. Delta Sync: uploading ONLY modified blocks on file edits.
  4. Metadata versioning and block-list assembly.
"""

import hashlib
from typing import Dict, List, Tuple, Set

CHUNK_SIZE = 4 * 1024  # Scaled down to 4KB for simulation (normally 4MB)

class CloudObjectStore:
    """Simulates Amazon S3 / Google Cloud Storage binary block repository."""
    def __init__(self):
        # block_hash -> raw bytes
        self.blocks: Dict[str, bytes] = {}
        self.total_bytes_stored = 0

    def has_block(self, block_hash: str) -> bool:
        return block_hash in self.blocks

    def put_block(self, block_hash: str, data: bytes):
        if block_hash not in self.blocks:
            self.blocks[block_hash] = data
            self.total_bytes_stored += len(data)

class MetadataService:
    """Simulates PostgreSQL file metadata ledger."""
    def __init__(self, storage: CloudObjectStore):
        self.storage = storage
        # file_path -> { "version": int, "block_hashes": [str, ...] }
        self.files: Dict[str, dict] = {}

    def sync_file(self, file_path: str, raw_content: bytes) -> Tuple[int, int, int]:
        """
        Splits file into chunks, deduplicates against storage,
        and uploads only missing blocks.
        Returns: (total_chunks, new_chunks_uploaded, bytes_saved)
        """
        chunks = [raw_content[i:i + CHUNK_SIZE] for i in range(0, len(raw_content), CHUNK_SIZE)]
        block_hashes = [hashlib.sha256(c).hexdigest() for c in chunks]

        new_uploaded = 0
        saved_bytes = 0

        for chunk_data, b_hash in zip(chunks, block_hashes):
            if self.storage.has_block(b_hash):
                # Deduplication / Delta sync: Block already exists!
                saved_bytes += len(chunk_data)
            else:
                self.storage.put_block(b_hash, chunk_data)
                new_uploaded += 1

        prev_version = self.files.get(file_path, {}).get("version", 0)
        self.files[file_path] = {
            "version": prev_version + 1,
            "block_hashes": block_hashes,
            "file_size": len(raw_content)
        }

        return len(chunks), new_uploaded, saved_bytes

def run_simulation():
    print("=" * 65)
    print("CLOUD FILE STORAGE & DELTA SYNC SIMULATION")
    print("=" * 65)

    storage = CloudObjectStore()
    metadata = MetadataService(storage)

    # 1. First Upload: 3-chunk document (approx 12KB)
    # Exactly 4096 bytes per chunk so boundaries align
    chunk1 = (b"Section 1: Architecture. " * 300)[:CHUNK_SIZE]
    chunk2 = (b"Section 2: Replication.  " * 300)[:CHUNK_SIZE]
    chunk3 = (b"Section 3: Storage.      " * 300)[:CHUNK_SIZE]
    file_v1 = chunk1 + chunk2 + chunk3

    print("Step 1: User uploads initial 3-block file ('report.docx'):")
    total, new_up, saved = metadata.sync_file("report.docx", file_v1)
    print(f"  Total Blocks: {total} | Uploaded: {new_up} | Bandwidth Saved: {saved} bytes")
    print(f"  Storage Cloud Repository Size: {storage.total_bytes_stored} bytes\n")

    # 2. Delta Sync: User edits Section 2, leaving Sections 1 and 3 unchanged
    print("Step 2: User modifies ONLY Section 2 (typo fix) and re-syncs:")
    chunk2_edited = (b"Section 2: Replication UPDATED. " * 300)[:CHUNK_SIZE]
    file_v2 = chunk1 + chunk2_edited + chunk3

    total, new_up, saved = metadata.sync_file("report.docx", file_v2)
    print(f"  Total Blocks: {total} | Uploaded: {new_up} (ONLY modified block!) | Bandwidth Saved: {saved} bytes")
    print(f"  Delta Sync saved {saved / len(file_v2) * 100:.1f}% of network bandwidth!\n")

    # 3. Cross-User Deduplication: Another user uploads identical file
    print("Step 3: User 2 uploads identical file under 'backup_report.docx':")
    total, new_up, saved = metadata.sync_file("backup_report.docx", file_v2)
    print(f"  Total Blocks: {total} | Uploaded: {new_up} | Bandwidth Saved: {saved} bytes")
    print("  Zero bytes uploaded to cloud storage due to cross-user block deduplication!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
