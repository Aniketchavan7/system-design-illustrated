# Real-World Case Studies: CAP and PACELC

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> CAP describes what a system gives up during a network partition. PACELC adds what it gives up the rest of the time. Two real systems sit at opposite corners: Google Spanner and Amazon's Dynamo.

---

## 🏢 Deep Dive 1: Is Google Spanner "CA"?

> **Source:** Eric Brewer, ["Inside Cloud Spanner and the CAP Theorem"](https://cloud.google.com/blog/products/databases/inside-cloud-spanner-and-the-cap-theorem) (Google Cloud blog, February 2017), which summarizes his paper ["Spanner, TrueTime and the CAP Theorem"](https://research.google/pubs/pub45855/). Everything in this section comes from the post.

Brewer, who formulated CAP, asks whether Spanner gets around it. His answer: "The short answer is 'no' technically, but 'yes' in effect and its users can and do assume CA."

- **Technically CP.** In CAP, "A" means "100% availability, for both reads and updates". Partitions "can happen and in fact have happened at Google", and "during some partitions, Spanner chooses C and forfeits A. It is technically a CP system."
- **Effectively CA.** No real system is 100% available, so the practical question is whether outages are rare enough not to worry about. Brewer reports "more than five 9s of availability".
- **Why partitions rarely matter.** "Spanner runs on Google's private network", and "Google controls the entire network and thus can ensure redundancy of hardware and paths." In Google's data, "the network contributed less than 10% of Spanner's already rare outages."

---

## 📦 Deep Dive 2: Amazon Dynamo and Cassandra Choose Availability

> **Sources:** [Dynamo: Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) (DeCandia et al., SOSP 2007); Daniel J. Abadi, ["Consistency Tradeoffs in Modern Distributed Database System Design"](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) (IEEE Computer, February 2012). Everything in this section comes from those.

- **Why availability.** Amazon's customers "should be able to view and add items to their shopping cart even if disks are failing, network routes are flapping, or data centers are being destroyed by tornados." Dynamo was built to be "always writeable".
- **The PACELC label.** Abadi writes: "The default versions of Dynamo, Cassandra, and Riak are PA/EL systems: if a partition occurs, they give up consistency for availability, and under normal operation they give up consistency for lower latency."
- **"Default" matters.** Cassandra lets each request choose a consistency level, so the same database can behave more like PC/EC when an application asks for it.

---

## ⚖️ Deep Dive 3: PACELC, the Trade-off Without a Partition

> **Source:** Daniel J. Abadi, ["Consistency Tradeoffs in Modern Distributed Database System Design"](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) (IEEE Computer, February 2012). Everything in this section comes from the paper.

Abadi's point is that CAP only describes behaviour during a partition, which is rare, while the trade-off between consistency and **latency** applies all the time. PACELC reads: if there is a **P**artition, choose **A**vailability or **C**onsistency; **E**lse, choose **L**atency or **C**onsistency.

| Label | Examples in the paper |
| :--- | :--- |
| **PA/EL** | Default Dynamo, Cassandra, Riak |
| **PC/EC** | VoltDB/H-Store, Megastore, BigTable/HBase |

Spanner was published after Abadi's paper, so it isn't classified there. By his definitions it behaves like a PC/EC system: it forfeits availability during some partitions, and it pays latency (commit wait) for consistency the rest of the time. That classification is our reading, not Abadi's.

---

> ℹ️ An earlier version of this page said Spanner backs "AdWords, Google Play Store, and enterprise financial ledgers", that Google's partition rate is "virtually negligible", and that Netflix uses Cassandra for viewing history. Brewer says partitions "have happened at Google", and we couldn't source the rest, so we removed it.

## 🎯 System Design Interview Takeaways
1. **CAP is only about partitions.** It says nothing about normal operation. Use PACELC to discuss the everyday consistency vs. latency choice.
2. **"CA" is an availability claim, not a theorem violation.** Spanner is CP, but with a private, redundant network its users can treat it as available.
3. **Name the default.** Systems like Cassandra are PA/EL by default but tunable. Say which setting your design relies on.
