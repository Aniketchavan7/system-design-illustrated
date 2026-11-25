# Real-World Case Studies: Consensus and Leader Election

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Three generations of consensus in practice: Google's Chubby lock service (Paxos), the Raft algorithm designed to be understandable, and etcd, the Raft-based store behind every Kubernetes cluster.

---

## 🏢 Deep Dive 1: Google Chubby, Consensus as a Lock Service

> **Source:** Mike Burrows, [The Chubby lock service for loosely-coupled distributed systems](https://research.google/pubs/the-chubby-lock-service-for-loosely-coupled-distributed-systems/) (OSDI 2006). Everything in this section comes from the paper.

- **Why a lock service.** Instead of every system implementing consensus, Chubby provides "coarse-grained locking as well as reliable (though low-volume) storage". Its main use is electing a leader: "the Google File System uses a Chubby lock to appoint a GFS master server", and Bigtable uses Chubby "to elect a master, to allow the master to discover the servers it controls, and to permit clients to find the master".
- **A cell of replicas.** The paper's diagram shows a cell of five servers. They use Paxos to elect a master, which gets votes from a majority plus "promises that those replicas will not elect a different master for an interval of a few seconds known as the master lease".
- **Reads and writes.** Writes are acknowledged once they reach "a majority of the replicas in the cell". Reads are served "by the master alone; this is safe provided the master lease has not expired".
- **Client sessions.** Separately, each client session has a lease that the master keeps extending. "The default extension is 12s."
- **Sequencers.** A lock holder can request "a sequencer, an opaque byte-string that describes the state of the lock immediately after acquisition", and pass it to servers. They can then reject requests from a holder whose lock has since been lost. This is the same idea as a fencing token.

---

## 🗳️ Deep Dive 2: Raft, Consensus Designed to Be Understood

> **Source:** Diego Ongaro and John Ousterhout, [In Search of an Understandable Consensus Algorithm (Extended Version)](https://raft.github.io/raft.pdf) (2014). Everything in this section comes from the paper.

- **Goal.** "In order to enhance understandability, Raft separates the key elements of consensus, such as leader election, log replication, and safety."
- **Elections without split votes.** "Raft uses randomized election timeouts to ensure that split votes are rare and that they are resolved quickly." Timeouts "are chosen randomly from a fixed interval (e.g., 150–300ms)", so usually a single server times out first, wins, and starts sending heartbeats before others time out.

---

## ☸️ Deep Dive 3: etcd, the Raft Store Under Kubernetes

> **Sources:** etcd docs: [FAQ](https://etcd.io/docs/v3.5/faq/) and [Tuning](https://etcd.io/docs/v3.5/tuning/); Kubernetes docs: [Cluster architecture](https://kubernetes.io/docs/concepts/architecture/) and [Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/). Everything in this section comes from those pages.

- **What it is.** "etcd is a consistent distributed key-value store." Kubernetes uses it as its "backing store for all cluster data", and "all Kubernetes objects are stored in etcd".
- **Leader-based.** "Raft is leader-based; the leader handles all client requests which need cluster consensus." Followers forward those requests to the leader.
- **Odd sizes.** "For a cluster with n members, quorum is (n/2)+1." A 3-member cluster tolerates 1 failure and a 5-member cluster tolerates 2, while 4 and 6 members tolerate no more than 3 and 5. Kubernetes recommends a five-member cluster in production.
- **Timing defaults.** etcd uses a 100 ms heartbeat interval and a 1000 ms election timeout by default.
- **Losing quorum.** If a majority of members fail, "Kubernetes cannot make any changes to its current state", so no new pods can be scheduled.

---

> ℹ️ An earlier version of this page said Borg relies on Chubby and that Chubby's master lease is "typically 12 seconds". The paper describes a master lease of "a few seconds", and 12 s is the default extension of a client's session lease. It also mentioned Netflix's Titus platform running on etcd. We couldn't source the Borg and Titus claims, so we removed them.

## 🎯 System Design Interview Takeaways
1. **Use a consensus service, don't build one.** Chubby, ZooKeeper and etcd exist so other systems can elect leaders and store small, critical metadata safely.
2. **Leases make leader reads cheap.** While a leader's lease is valid, no other leader can exist, so it can answer reads alone.
3. **Fence stale leaders.** A sequencer or fencing token lets downstream servers reject a former leader that doesn't know it has lost its lock.
4. **Run an odd number of members.** Adding a fourth member to a three-member cluster costs more and tolerates no extra failure.
