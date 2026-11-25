# Real-World Case Studies: Consistency Models

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> The consistency spectrum as real products expose it: Spanner at the strong end, Azure Cosmos DB with five selectable levels, and DynamoDB's per-request choice between eventual and strong reads.

---

## 🏢 Deep Dive 1: Google Spanner, External Consistency

> **Source:** [Spanner: Google's Globally-Distributed Database](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (Corbett et al., OSDI 2012). Everything in this section comes from the paper.

- **The guarantee.** Spanner's timestamps "reflect serialization order", and that order "satisfies external consistency (or equivalently, linearizability): if a transaction T1 commits before another transaction T2 starts, then T1's commit timestamp is smaller than T2's."
- **How.** TrueTime gives each server an interval guaranteed to contain the real time. Its uncertainty is "typically a sawtooth function of time, varying from about 1 to 7 ms". Before making a commit visible, the coordinator waits until the commit timestamp is definitely in the past ("commit wait"), so no later transaction can get an earlier timestamp.

---

## 🌐 Deep Dive 2: Azure Cosmos DB, Five Levels You Can Choose

> **Sources:** Microsoft Learn, [Consistency levels in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels) and [Manage consistency levels](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-manage-consistency). Everything in this section comes from those pages.

"From strongest to weakest, the levels are: Strong, Bounded staleness, Session, Consistent prefix, Eventual."

| Level | What the docs promise |
| :--- | :--- |
| **Strong** | "a linearizability guarantee": reads return "the most recent committed version of an item" |
| **Bounded staleness** | the lag between regions "is always less than a specified amount": K versions or T time, "whichever is reached first" |
| **Session** | within one client session, "read-your-writes, and write-follows-reads guarantees" |
| **Consistent prefix** | writes in one multi-document transaction "are always visible together" |
| **Eventual** | a read may hit a replica that is "lagging and could return stale or no data" |

- **Session is the default.** It works with a session token. "After every write operation, the client receives an updated Session Token", and reads only use a replica that has caught up to that token. If an app runs on several servers and doesn't pass the token along, reads can be inconsistent "for a while".
- **Bounded staleness has floors.** For multi-region accounts the minimum is "100,000 write operations or 300 seconds".
- **Stronger costs more.** Strong and bounded staleness read from two replicas, so their "read throughput ... is half that of the other consistency levels", and each such read costs twice as much.

---

## ⚡ Deep Dive 3: Amazon DynamoDB, Choose per Read

> **Source:** AWS docs, [DynamoDB read consistency](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html). Everything in this section comes from it.

- "Eventually consistent is the default read consistent model for all read operations." Such a read "might not reflect the results of a recently completed write operation".
- Setting `ConsistentRead` to true returns "the most up-to-date data, reflecting the updates from all prior write operations that were successful."
- "Eventually consistent reads are half the cost of strongly consistent reads."
- Strong reads work on tables and local secondary indexes only: "All reads from GSIs and streams are eventually consistent."

---

> ℹ️ An earlier version of this page claimed NTP clocks drift "100ms to 250ms" across data centers, and described Netflix pinning sessions to replicas and letting bookmarks lag "2 to 5 seconds". We couldn't find sources for those claims, so we replaced them with the documented Cosmos DB and DynamoDB behaviour.

## 🎯 System Design Interview Takeaways
1. **Name the anomaly each level prevents.** Session consistency in Cosmos DB, for example, guarantees you read your own writes. Eventual consistency doesn't.
2. **Strong consistency costs real money.** Cosmos DB halves read throughput and DynamoDB doubles read cost for the stronger option.
3. **Session guarantees need plumbing.** If requests from one user can hit different app servers, the session token (or equivalent) must travel with them.
