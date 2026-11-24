# Real-World Production Deep Dives: Distributed Transactions

> Deep-dive architectural dissections of how **Google** and **Uber/Netflix** execute distributed transactions, comparing Google's two-phase locking snapshot isolation (Percolator & Spanner) with the asynchronous Saga Pattern.

---

## 🏢 Deep Dive 1: How Google Uses Distributed Transactions (Percolator: Distributed ACID on Bigtable)

### 1. Production Context & Scale
- **System**: Google **Percolator**.
- **Mission**: Incremental web index updating for Google Search.
- **The Shift**: Prior to Percolator, Google rebuilt its web search index using batch MapReduce jobs running every few days. Percolator allowed Google to process incremental document updates within seconds of a web page being crawled, indexing billions of pages daily.

### 2. The Core Problem at Google Scale
- Google's web index resides across thousands of Bigtable tablet servers.
- Bigtable natively provides atomic transactions **only within a single row**.
- Indexing a new web page requires updating multiple tables and rows simultaneously (e.g., updating the Document Table, Word Inverted Index, and Link Graph). If the indexing process crashes midway, the search index is left with broken links and corrupted search results.

### 3. Google's Architecture: The Percolator Two-Phase Protocol

```
[ Percolator Client (Transaction Coordinator) ]
             │
      ┌──────┴──────────────────────────┐
      ▼                                 ▼
[ Primary Lock Row ]           [ Secondary Lock Rows ]
  ├── Step 1: Prewrite Primary   ├── Step 2: Prewrite Secondaries
  │   (Acquires data lock)       │   (Point to Primary Lock)
  │                              │
  ▼                              ▼
[ Commit Primary Row ] ────────> [ Commit Secondary Rows ]
(Sets commit timestamp)          (Removes locks; writes commit record)
```

#### A. The Timestamp Oracle (TSO)
- Percolator utilizes a centralized **Timestamp Oracle (TSO)** that dishes out monotonically increasing 64-bit timestamps.
- Every transaction requests a `start_timestamp` and eventually a `commit_timestamp`.

#### B. Primary Lock and Decentralized Coordination
Instead of relying on an external transaction coordinator that could become a single point of failure:
1. **Prewrite Phase**:
   - The client designates one cell as the **Primary**.
   - It writes the data and places a lock on the primary cell with its `start_timestamp`.
   - It then writes data and locks on all **Secondary** cells. Crucially, each secondary lock contains an explicit pointer to the primary lock cell!
2. **Commit Phase**:
   - The client gets a `commit_timestamp` from the TSO.
   - It commits the **Primary** cell by converting the lock into a permanent commit record. **The transaction is now officially committed!**
   - The client asynchronously converts the secondary locks into commit records.

#### C. Crash Recovery without Central Locks
What happens if the client crashes halfway through?
- When a concurrent reader encounters an orphaned secondary lock, it follows the embedded pointer to the **Primary cell**:
  - If the primary cell was committed, the reader rolls the secondary forward (commits it).
  - If the primary cell has no commit record and is abandoned, the reader rolls the transaction back and clears the locks!

---

## 🚙 Deep Dive 2: How Uber & Netflix Use Sagas (Cadence / Temporal Orchestration)

### 1. Production Context & Scale
- **Systems**: Uber Cadence (now open-sourced as Temporal) and Netflix Conductor.
- **Scale**: Hundreds of millions of business workflows executing daily (Trip dispatch, Driver payroll, Customer refund requests, Video encoding pipelines).
- **Duration**: Workflows that span seconds, hours, or even days across independent microservices.

### 2. The Core Problem: Why Two-Phase Commit (2PC) Fails in Microservices
- Two-Phase Commit requires all participating databases to hold row locks until the coordinator confirms commit:
  - If Service C experiences network latency, Services A and B hold database locks for seconds.
  - Across hundreds of independent microservices owned by different teams, 2PC creates **tight temporal coupling**, distributed deadlocks, and collapses system availability to the product of all service availabilities ($A_{\text{system}} = A_1 \times A_2 \times A_3$).

### 3. Uber's Architecture: Orchestrated Saga Pattern with Temporal

```
[ Rider Clicks "Book Trip" ]
             │
             ▼
[ Temporal / Cadence Saga Orchestrator ]
  ├── Manages State Machine & Persistent Execution History
  │
  ├── Step 1: Dispatch DispatchService.assignDriver() ──> [ OK ]
  ├── Step 2: Dispatch PaymentService.authorizePayment() ─> [ OK ]
  ├── Step 3: Dispatch NotificationService.sendSMS() ───> [ FAILED! ]
  │
  ▼ (Compensation Triggered in Reverse Order!)
[ Compensating Transaction Flow ]
  ├── Step 2Comp: PaymentService.refundAuthorization() ──> [ REVERSED ]
  └── Step 1Comp: DispatchService.releaseDriver() ───────> [ REVERSED ]
             │
             ▼
[ User Notified: "Booking Failed; No Charges Incurred" ]
```

#### A. Sagas: Local Transactions & Compensations
- A Saga decomposes a distributed transaction into a sequence of **local transactions**:
  - Each service performs its local database transaction and updates its state.
  - If any step fails (e.g., credit card declined, flight sold out), the Saga executes **Compensating Transactions** in reverse order to undo the changes made by earlier steps.

#### B. Orchestration vs Choreography
- **Choreography (Event-Driven)**: Services emit events and listen to each other's events.
  - *Why Uber Abandoned It*: At high scale, choreography became "spaghetti event architecture". It was impossible to visualize where a stuck ride was, circular event loops caused catastrophic double-charging, and debugging required distributed log correlation across 20 services.
- **Orchestration (Temporal)**:
  - A centralized **Orchestrator** defines the workflow as code.
  - It explicitly controls step execution, handles timeouts, retries transient failures, and manages the deterministic execution of compensating actions.

---

## ⚖️ Comparative Architecture Matrix: 2PC vs Saga

| Architectural Dimension | Two-Phase Commit (Google Spanner / Percolator) | Saga Pattern (Uber Temporal / Netflix) |
|---|---|---|
| **Consistency Guarantee** | Strict ACID (Immediate Consistency) | Eventual Consistency (BASE) |
| **Locking Semantics** | Holds distributed database locks across phase | No cross-service locks; local commits only |
| **Failure Recovery** | Rollback leaves database as if nothing happened | Compensating transactions clean up committed data |
| **Latency & Throughput** | High latency; sensitive to slowest participant | High throughput; decoupled asynchronous execution |
| **Best Used For** | Financial balances, stock trading, internal DBs | Multi-microservice business workflows, orders |

---

## 🎯 System Design Interview Takeaways
1. **Never Propose 2PC for Microservices**: If an interviewer asks how to handle a distributed transaction across independent microservices (e.g., Order Service -> Payment Service -> Inventory Service), explicitly reject 2PC due to lock contention and propose the **Saga Pattern**.
2. **Orchestrated vs Choreographed Sagas**: Recommend **Orchestrated Sagas** for complex multi-step workflows to maintain visibility, centralize timeout management, and prevent event-loop deadlocks.
3. **Idempotency in Compensating Actions**: Explain that all compensating transactions *must be strictly idempotent*. If a network glitch occurs during a refund step, the orchestrator will retry the refund call, which must not result in double refunds!
