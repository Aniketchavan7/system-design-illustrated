# System design reading map

The [reference folder](https://github.com/aasthas2022/SDE-Interview-and-Prep-Roadmap/tree/main/System%20Design/Resources) contains Martin Kleppmann's *Designing Data-Intensive Applications* and Alex Xu's *System Design Interview*. Use this map to practice the main chapter topics from the editions in that folder. The links lead to this repository's explanations and exercises.

## Designing Data-Intensive Applications

| Chapter | Topic | Read or practice |
| --- | --- | --- |
| 1 | Reliability, scale and maintainability | [fault tolerance and resilience](../20-fault-tolerance-and-resilience/), [scaling from one to millions](../26-scaling-from-one-to-millions/), [system design metrics monitoring and alerting](../44-system-design-metrics-monitoring-and-alerting/) |
| 2 | Data models and queries | [relational and non relational databases](../06-relational-and-non-relational-databases/) and [build a trail usage report](./batch-stream-and-derived-data.md) |
| 3 | Storage and retrieval | [storage engines and indexing](../09-storage-engines-and-indexing/), [system design ad click aggregation](../45-system-design-ad-click-aggregation/) |
| 4 | Encoding and evolution | [data encoding and schema evolution](../30-data-encoding-and-schema-evolution/) |
| 5 | Replication | [database replication](../07-database-replication/) |
| 6 | Partitioning | [database partitioning](../08-database-partitioning/) |
| 7 | Transactions | [database transactions and isolation](../29-database-transactions-and-isolation/), [distributed transactions](../19-distributed-transactions/) |
| 8 | Distributed system failure modes | [fault tolerance and resilience](../20-fault-tolerance-and-resilience/), [time clocks and ordering](../31-time-clocks-and-ordering/) |
| 9 | Consistency and consensus | [consistency models](../14-consistency-models/), [consensus and leader election](../15-consensus-and-leader-election/) |
| 10 | Batch processing | [system design search autocomplete](../37-system-design-search-autocomplete/) and [build a trail usage report](./batch-stream-and-derived-data.md) |
| 11 | Stream processing | [message queues](../17-message-queues/), [system design ad click aggregation](../45-system-design-ad-click-aggregation/) and [build a trail usage report](./batch-stream-and-derived-data.md) |
| 12 | Integrating systems and maintaining derived data | [event sourcing and cqrs](../18-event-sourcing-and-cqrs/), [cache eviction and invalidation](../11-cache-eviction-and-invalidation/) and [build a trail usage report](./batch-stream-and-derived-data.md) |

## System Design Interview

| Chapter | Topic | Read or practice |
| --- | --- | --- |
| 1 | Scaling a service | [scaling from one to millions](../26-scaling-from-one-to-millions/) |
| 2 | Capacity estimates | [back of the envelope estimation](../27-back-of-the-envelope-estimation/) |
| 3 | Interview process | [Study guide and timed interview practice](../STUDY_GUIDE.md) |
| 4 | Rate limiting | [system design rate limiter](../25-system-design-rate-limiter/) |
| 5 | Consistent hashing | [consistent hashing](../16-consistent-hashing/) |
| 6 | Durable key-value storage | [Design a durable store](./durable-key-value-store.md), [storage engines and indexing](../09-storage-engines-and-indexing/), [system design in memory cache](../22-system-design-in-memory-cache/) |
| 7 | Distributed IDs | [distributed unique id generator](../28-distributed-unique-id-generator/) |
| 8 | Short links | [system design url shortener](../21-system-design-url-shortener/) |
| 9 | Crawling | [system design web crawler](../36-system-design-web-crawler/) |
| 10 | Notifications | [system design notification system](../35-system-design-notification-system/) |
| 11 | Feeds | [system design news feed](../34-system-design-news-feed/) |
| 12 | Chat | [system design chat app](../23-system-design-chat-app/) |
| 13 | Autocomplete | [system design search autocomplete](../37-system-design-search-autocomplete/) |
| 14 | Video delivery | [system design video streaming](../24-system-design-video-streaming/) |
| 15 | File synchronization | [system design cloud file storage](../38-system-design-cloud-file-storage/) |
| 16 | Further study | [Study guide and timed interview practice](../STUDY_GUIDE.md) |
