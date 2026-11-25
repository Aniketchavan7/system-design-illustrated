# Real-World Case Studies: Database Replication

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Two opposite designs: Google Spanner replicates every write synchronously through a Paxos leader, while Amazon's Dynamo and Apache Cassandra let any replica accept writes and reconcile later.

---

## 🏢 Deep Dive 1: Google Spanner, Synchronous Replication with Paxos

> **Sources:** [Spanner: Google's Globally-Distributed Database](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (Corbett et al., OSDI 2012); Google Cloud, [Spanner replication](https://docs.cloud.google.com/spanner/docs/replication). Everything in this section comes from those.

- **One Paxos group per tablet.** "Each spanserver implements a single Paxos state machine on top of each tablet." Writes go through that group's leader and are applied in order.
- **Long-lived leaders.** "Our Paxos implementation supports long-lived leaders with time-based leader leases, whose length defaults to 10 seconds." When a zone fails, leadership moves as those leases expire.
- **Replica count is a choice.** Spanner's first customer, F1, "uses five replicas spread across the United States".
- **Witness replicas (Cloud Spanner).** Some replicas exist only to vote. Witness replicas "participate in voting to commit writes" and in leader election, but "aren't eligible to become a leader replica", "don't support reads", and "don't maintain a full copy of data".

---

## 🛒 Deep Dive 2: Amazon Dynamo and Apache Cassandra, Leaderless Replication

> **Sources:** Werner Vogels, ["Amazon's Dynamo"](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) (October 2007, introducing DeCandia et al., SOSP 2007); Apache Cassandra docs, [Dynamo architecture](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html). Everything in this section comes from those.

**Dynamo** is "internal technology developed at Amazon to address the need for an incrementally scalable, highly-available key-value storage system". It aims to be "always writeable": for example, the shopping cart "must allow customers to add and remove items from their shopping cart even amidst network and server failures".

- **No fixed leader.** Data is spread with consistent hashing, and a write can land on whichever replicas are reachable ("sloppy quorum"). If a replica is down, another node keeps the write and hands it over later ("hinted handoff").
- **Conflicts are expected.** Dynamo uses "vector clocks in order to capture causality between different versions of the same object", and conflicting versions are reconciled later.
- **Tunable quorums.** With N replicas, a write waits for W of them and a read for R. "Setting R and W such that R + W > N yields a quorum-like system."

**Cassandra** borrows the same ideas:

- **Replicas per datacenter.** "NetworkTopologyStrategy requires a specified replication factor for each datacenter in the cluster."
- **Local quorums.** With `LOCAL_QUORUM`, "a majority of the replicas in the local datacenter ... must respond", so a write doesn't wait on another region.
- **Last write wins.** "Every mutation is timestamped (including deletes) and then the latest version of data is the 'winning' value." Because correctness "does depend on these clocks", the docs say to run time synchronization such as NTP.
- **Repairing replicas.** Hinted handoff in the write path and read repair in the read path help replicas converge.

> ℹ️ An earlier version of this page described Netflix's specific Cassandra regions, "<4ms" writes and custom NTP daemons, and gave Spanner a five-nines SLA across "5 continents". We couldn't find sources we could read for those details, so we described the general Dynamo and Cassandra mechanics from their own documentation instead.

---

## ⚖️ Side by Side

| | Spanner | Dynamo / Cassandra |
| :--- | :--- | :--- |
| **Who accepts a write** | The Paxos leader for that tablet | Any replica the coordinator reaches |
| **When a write is acknowledged** | When a Paxos majority has it | When W replicas (or a local quorum) have it |
| **Conflicts** | Prevented: writes are ordered by the leader | Expected: resolved by vector clocks (Dynamo) or last-write-wins timestamps (Cassandra) |
| **Main cost** | Write latency includes a round trip to a majority | Reads can see stale data unless R + W > N |

---

## 🎯 System Design Interview Takeaways
1. **State the quorum rule.** With N replicas, choosing R + W > N makes every read set overlap every write set. Cassandra's docs express the same rule as W + R > RF.
2. **Synchronous vs. asynchronous is a latency vs. data-loss trade-off.** Waiting for a majority, as Spanner does, costs a round trip but survives losing a minority. Acknowledging locally is faster but can lose recent writes.
3. **Last-write-wins needs good clocks.** If you propose it, mention clock synchronization, as Cassandra's docs do.
