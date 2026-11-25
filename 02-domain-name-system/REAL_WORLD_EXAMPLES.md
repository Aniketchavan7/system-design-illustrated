# DNS in production

> ✅ **Source-checked, with one gap.** We checked every claim against its linked source, except the Netflix tech blog post, which blocks automated reading. Treat that sentence as unverified until someone confirms it. Found an error, or can confirm the Netflix post? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

## Google Public DNS · Recursive caching and anycast

Google documents two levels of DNS caching. A cache near the user contains popular names. A second pool partitions its cache by name so repeated queries for a name can reach the same cache. Google also documents the use of anycast for its resolver addresses. Multiple locations advertise the same address, and internet routing selects a reachable path. [Google Public DNS performance documentation](https://developers.google.com/speed/public-dns/docs/performance) · [Google Public DNS FAQ](https://developers.google.com/speed/public-dns/faq)

**Apply it to Trail Notes.** A recursive resolver can answer a repeat lookup from cache. On a miss, it may reuse cached referrals and query only the parts of the DNS hierarchy it still needs.

## Amazon Route 53 · Authoritative DNS failover

Route 53 supports primary and secondary failover records. Health checks can affect the endpoint returned in new DNS answers. Previously cached answers can remain in use for their remaining TTL, and clients with an open connection may not look up the name again immediately. [Route 53 failover record settings](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-failover.html) · [AWS failover FAQ](https://aws.amazon.com/route53/faqs/)

Netflix's 2019 regional evacuation write-up describes preparing compute capacity in other regions before moving traffic. It illustrates the operational work behind a traffic shift. [Netflix engineering on regional evacuation](https://netflixtechblog.com/evolving-regional-evacuation-69e6cc1d24c6)

**Apply it to Trail Notes.** Measure when the authoritative answer changes, when clients reconnect, and whether the destination can absorb the shifted load. Those are three different checks in this hypothetical failover exercise.

[Return to the DNS lesson](./README.md#first-pass)
