# Metrics monitoring in production

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

## Google · Monarch

Google's 2020 paper describes Monarch as a multi-tenant, in-memory time-series database. Its regional architecture keeps collection close to sources, and a global query plane integrates results. The paper reports ingesting terabytes of time-series data per second at the time of publication. [Google's Monarch paper](https://research.google/pubs/monarch-googles-planet-scale-in-memory-time-series-database/)

Which parts of a query can execute near regional data? Counts can be added across regions. A percentile needs mergeable data such as histogram buckets with compatible boundaries.

## Netflix · Atlas

Netflix introduced Atlas publicly in December 2014. The company reported sustaining more than **1.2 billion distinct time series** during North American regional failover exercises. That number counts series. The same post describes the separate publication rate in data points per minute. [Netflix's Atlas engineering write-up](https://netflixtechblog.com/introducing-atlas-netflixs-primary-telemetry-platform-bd31f4d8ed9a)

Atlas identifies metrics with sets of key-value pairs. An operator can group requests by region or filter to a particular application. Its public project describes the storage layer as an in-memory dimensional time-series database. [Netflix Atlas source](https://github.com/Netflix/atlas)

## Worked example · Series count versus sample rate

Suppose 100 services run in three regions, expose ten metrics each, and emit one sample per series every ten seconds. With one series per service, region, and metric, that is 3,000 series and 300 samples per second on average. Adding a dimension with 20 values across every combination multiplies both figures by 20. Measure actual label combinations before provisioning.
