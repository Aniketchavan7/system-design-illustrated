# Design a durable key-value store

A field team saves trail inspection reports under keys such as `inspection/492`. After a successful save, a report must survive the loss of one machine. A cache that can evict the only copy cannot meet that promise.

## Trace a save

1. Route the key to a shard using a stable partition map. Each shard has three replicas in separate failure domains and one elected leader.
2. The leader validates the client's expected version. It orders an update containing the key, report, request ID and new version in a replicated log. Acknowledge only once the consensus protocol commits the entry and the result is available. Require durable log storage on a majority before reporting success.
3. Apply committed entries to the local index in order. On restart, load a snapshot, then replay committed entries after its log position. Record each request ID and result with the update so a retry after a lost reply returns the same result within the advertised retry window.
4. For a read that must see the latest completed write, verify current leadership with a quorum and wait until the local index has applied the corresponding committed position. A follower read can trade freshness for lower latency if the caller allows it.

| Event | Client-visible behavior |
| --- | --- |
| Leader fails after commit, before reply | Retry the same request ID against the new leader to recover the outcome. |
| Two replicas lose contact with the third | The majority can elect or keep a leader. A client on the isolated side cannot get an acknowledged write there. |
| Two users edit version 8 | The leader serializes the conditional writes. One can create version 9. The other receives a conflict and can reread. |
| A deleted key reappears on an old disk | Replay the committed delete or install a current snapshot before that replica serves reads. |

**Size it.** Ten million 1 KB reports occupy about 10 GB of payload in decimal units, or 30 GB across three replicas. Budget separately for keys, indexes, log retention, compaction and recovery headroom. Adding shards distributes independent keys. A single hot report still belongs to one shard.

**Interview variation.** Suppose inspectors must save offline on both sides of a partition. The majority design above cannot acknowledge both writes. Let devices stage independent revisions with parent version IDs, then reconcile them on reconnect. If the edits conflict, preserve both until an inspector resolves them. Explain which promise changes in the API.

Continue with [consensus](../15-consensus-and-leader-election/), [partitioning](../08-database-partitioning/) and [storage engines](../09-storage-engines-and-indexing/).

Explore a leader election and read the replicated-log protocol in the [Raft authors' guide](https://raft.github.io/).
