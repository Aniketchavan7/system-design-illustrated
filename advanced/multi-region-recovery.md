# Multi-region failover and disaster recovery

Imagine a bakery with a second shop across town. Sending orders to the second shop helps it keep serving customers when the first shop closes. An archived copy of the order book helps when an error deletes records in both shops.

## Set recovery targets

| Objective | What to measure | Checkout example |
| --- | --- | --- |
| Recovery time objective (RTO) | Maximum acceptable time until users can complete the operation again | 15 minutes |
| Recovery point objective (RPO) | Maximum acceptable gap between the failure and the latest recoverable data | 60 seconds |

Scope the targets to a service and failure scenario. A catalog may tolerate an older restore point than checkout. Replication lag indicates potential exposure. After an incident, compare the newest recoverable committed writes with the source records to learn what went missing.

~~~mermaid
flowchart LR
    C[Clients] --> T[Traffic routing]
    T --> A[Checkout in Region A]
    T -. Route after promotion .-> B[Checkout in Region B]
    A --> P[(Primary database)]
    P -. Async replication .-> S[(Standby database)]
    B -. Writes after promotion .-> S
    P --> V[(Versioned backups)]
~~~

## Choose a recovery strategy

| Strategy | What is already running in the recovery region? | Trade-off |
| --- | --- | --- |
| Backup and restore | Backups and deployment definitions are available | Restore time and backup frequency set the recovery limits. |
| Pilot light | Essential infrastructure and a copy of critical data | Application capacity must still be started and tested. |
| Warm standby | A smaller copy of the full system | Cutover can start earlier. Plan time and capacity to scale. |
| Active-active | Both regions serve live traffic | Write ownership and conflict resolution become normal operating concerns. |

With consensus replication, 2F+1 voting replicas need a majority of F+1. Place the voters and durable copies so that the required quorum can survive the region failure you plan for. Zero loss of acknowledged writes depends on the acknowledgment rule and the failure scenario. Cross-region coordination can add latency, and losing quorum may pause writes. With asynchronous replication, a write can be acknowledged before the standby has it. [AWS recovery strategies](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_planning_for_recovery_disaster_recovery.html) · [Consensus and leader election](../15-consensus-and-leader-election/)

## Walk through a regional outage

1. **Detect.** At 12:00 UTC, regional probes and failed checkout requests confirm Region A is unavailable. Start the recovery clock.
2. **Fence the old writer.** Use the database control plane or a write lease the old primary cannot retain. Keep writes paused if you cannot establish single-writer ownership.
3. **Promote and route.** Promote Region B and verify its dependencies before opening traffic. Account for cached DNS answers, open connections, and the time it takes to scale.
4. **Measure and reconcile.** Checkout succeeds at 12:11. The standby reports committed writes through 11:59:35. The observed recovery took 11 minutes and exposed 25 seconds of recent writes. Match order IDs against receipts before replaying missing operations with their original idempotency keys.
5. **Fail back deliberately.** Rebuild the former primary from the new source of truth, validate that it has caught up, and schedule a controlled switchover.

## Prove that a backup can be restored

Try this on paper. A bad migration ran at 14:00 and replicated to both regions. You discover it at 14:05. Pick a restore point, work out how to recover valid writes made after 14:00, and describe what you would check before reopening traffic.

<details>
<summary>Check your answer</summary>

Restore into an isolated database just before the bad migration. Compare records with an append-only event or audit log and replay only validated operations. Time the recovery, check row counts and business invariants such as order totals, and run checkout and refund checks against sandbox dependencies. Record the measured recovery time and any missing committed writes.

</details>

[PostgreSQL point-in-time recovery](https://www.postgresql.org/docs/17/continuous-archiving.html) · [Database replication](../07-database-replication/) · [Fault tolerance and resilience](../20-fault-tolerance-and-resilience/)
