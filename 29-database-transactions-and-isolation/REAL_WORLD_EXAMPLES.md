# Real-World Case Studies: Database Transactions and Isolation

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> How Google Spanner serializes transactions across the world, how PostgreSQL implements Serializable without heavy locking, and how Stripe makes retries safe with idempotency keys.

---

## 🏢 Deep Dive 1: Google Spanner, Locks Plus Clocks

> **Source:** [Spanner: Google's Globally-Distributed Database](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (Corbett et al., OSDI 2012). Everything in this section comes from the paper.

- **Read-write transactions use locks.** "Transactional reads and writes use two-phase locking." Each Paxos leader keeps a lock table, and the paper lists read-write concurrency control as "pessimistic". Transactions that span Paxos groups use two-phase commit, which runs "over Paxos" to stay available.
- **Read-only transactions don't.** A read-only transaction "has the performance benefits of snapshot isolation": it reads at a timestamp without locks, from any replica that is up to date enough.
- **TrueTime.** `TT.now()` returns an interval guaranteed to contain the true time, using "GPS and atomic clocks". The uncertainty ε is "typically a sawtooth function of time, varying from about 1 to 7 ms", so "4 ms most of the time".
- **Commit wait.** The coordinator "ensures that clients cannot see any data committed by Ti until TT.after(si) is true". Waiting out the uncertainty guarantees that if T1 commits before T2 starts, T1 gets the smaller timestamp. The paper calls this "external consistency (or equivalently, linearizability)".

---

## 🐘 Deep Dive 2: PostgreSQL, Serializable Snapshot Isolation

> **Source:** PostgreSQL documentation, [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html). Everything in this section comes from it.

- **Repeatable Read is snapshot isolation.** It is "also known ... as Snapshot Isolation", and it can still produce a serialization anomaly. In the docs' example, two transactions each read a sum from one group of rows and insert it into the other. At Repeatable Read "both would be allowed to commit", even though no serial order gives that result.
- **Serializable is SSI.** It is "implemented using a technique known in academic database literature as Serializable Snapshot Isolation". Instead of locking more, it watches for read/write dependencies that could cause an anomaly. When it finds one, it rolls a transaction back with SQLSTATE `40001`. The monitoring adds no blocking beyond Repeatable Read.
- **So retry.** "Applications using this level must be prepared to retry transactions due to serialization failures."
- **Read Uncommitted** "behaves like Read Committed" in PostgreSQL.

---

## 💳 Deep Dive 3: Stripe, Making Retries Safe

> **Source:** Brandur Leach, ["Designing robust and predictable APIs with idempotency"](https://stripe.com/blog/idempotency) (Stripe, February 2017). Everything in this section comes from the post.

- **The problem.** If a request to charge a card times out, the client can't tell whether the charge happened. A blind retry might charge twice.
- **Idempotency keys.** Stripe lets clients "pass a unique value in with the special Idempotency-Key header". If the first attempt's outcome is unclear, "you can safely retry it with the same idempotency key, and the customer is charged only once."
- **Retry politely.** The post recommends "something akin to an exponential backoff algorithm", with random "jitter" so many clients don't retry in lockstep.
- **Transactions help.** If a failed operation "was successfully rolled back by way of an ACID database, it'll be safe to retry it wholesale."

> ℹ️ An earlier version of this page said Spanner uses Serializable Snapshot Isolation (its read-write transactions use two-phase locking) and described how Netflix handles billing in Aurora MySQL. We couldn't find a source we could read for the Netflix story, so we replaced it with the PostgreSQL and Stripe sections.

---

## 🎯 System Design Interview Takeaways
1. **Know the levels and their anomalies.** In PostgreSQL, Repeatable Read is snapshot isolation and still allows serialization anomalies. Serializable prevents them by aborting one of the transactions.
2. **Serializable means retries.** Whether it's Spanner retrying internally or PostgreSQL returning `40001`, a correct design plans for transactions that must run again.
3. **Make retried requests idempotent.** A client-supplied idempotency key, as Stripe uses, turns "did it happen?" into a safe retry.
4. **Keep slow network calls out of open transactions.** Holding locks while waiting on a third party ties up the database. This is general practice, not a claim from the sources above.
