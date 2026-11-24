# Build a trail usage report twice

Trail Notes needs a daily count of visits per region and a dashboard that updates within one minute. Both count a visit once by its event ID and assign it to the UTC day when it happened. A phone can upload yesterday's visit today. Treat dashboard totals as provisional and allow corrections.

## Choose the representation around the question

Store a visit as `(event_id, occurred_at, trail_id)`. Keep region assignments in a table keyed by trail and effective date. Join each visit to the assignment valid at the time of the visit. Joining against today's region would silently rewrite history when a boundary moves. A nested document suits fetching one entire inspection. An edge list such as `(trail_a, trail_b)` suits finding trails reachable in two hops. A two-hop query joins the edge list to itself on the intermediate trail. High-degree junctions can produce many paths to the same destination, so deduplicate destinations if the question asks for distinct trails.

## Build yesterday's report in a batch

Freeze a manifest of input files and a version of the assignments. Deduplicate visits by event ID, attach the region, then group by day and region. Broadcast the assignments to every worker if they fit comfortably in memory. Otherwise partition both inputs by trail ID so matching records meet on the same worker. Sorting each partition by key lets a worker merge large inputs sequentially.

Suppose 12 workers each read 1 million distinct visits and each sees all 50 regions on one day. After the join, each worker emits 50 partial counts. The final summation receives 600 records for 12 million visits. This optimization relies on addition being associative. For an average, carry the sum and count instead of averaging worker averages.

Write results to a fresh output version. Publish the completed version by atomically switching the report pointer. A failed worker can retry its partition against the same manifest. Choose one successful output per partition so a retried task cannot double a region's total.

## Update the same report from a stream

Partition by event ID to suppress duplicate deliveries, then repartition by day and region to update counts. Track source positions along with operator state. Use a transactional sink or idempotent versioned output so a crash between publishing and checkpointing cannot increment a count twice. Choose a deduplication retention period that covers the supported retry window. Reconcile older events from the retained source.

A visit at 23:59 that arrives at 00:03 belongs to yesterday. A watermark estimates how far event time has advanced. Define what happens when later evidence revises a published window. Here the dashboard flags totals as provisional and emits a versioned correction. The batch report reconciles arrivals that exceed the dashboard's correction window.

## Rebuild and delete safely

A search index and a dashboard are derived views. To build a new view while writes continue, obtain a consistent source snapshot with a corresponding change-log position. Load the snapshot, then consume changes after that position, including deletes. Preserve per-key ordering. Monitor lag and compare counts against the source before switching readers. If the saved log position has fallen outside retention, take a fresh snapshot.

Restrict raw visit access and publish aggregates at the granularity users actually need. When a visit must be removed, propagate its deletion into derived views and apply the deletion during historical rebuilds. Define backup expiry and restore procedures so restoring an old snapshot cannot silently republish deleted records.

**Try it on paper.** Trail A belongs to East on Monday and West on Tuesday. Visits v1 and v2 occur on A on Monday. On Tuesday, v2 arrives twice and v3 occurs on A. Which totals should a rebuild publish?

<details><summary>Check your answer</summary>

Monday East has 2 and Tuesday West has 1. Both deliveries of v2 describe the same visit. Looking up only the current assignment would incorrectly put Monday's visits in West. If v1 is later deleted, publish Monday East as 1 and keep Tuesday West at 1.

</details>

Continue with [ad click aggregation](../45-system-design-ad-click-aggregation/), [schema evolution](../30-data-encoding-and-schema-evolution/) and [event sourcing](../18-event-sourcing-and-cqrs/).

For the execution model behind the batch example, read the [original MapReduce paper](https://research.google/pubs/mapreduce-simplified-data-processing-on-large-clusters/).
