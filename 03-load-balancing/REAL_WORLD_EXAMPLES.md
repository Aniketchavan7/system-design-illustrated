# Load balancing in production

## Google · Maglev

Google's 2016 NSDI paper describes Maglev as a software network load balancer. Routers distribute packets to Maglev instances using equal-cost multipath routing. Each instance selects service endpoints and uses consistent hashing and connection tracking to reduce disruption to existing connections during failures. The paper reports that a single Maglev machine could saturate a **10 Gbps** link using small packets in the setup it evaluated. That is a historical packet-processing result for Maglev. [Google's 2016 Maglev paper](https://research.google/pubs/maglev-a-fast-and-reliable-software-network-load-balancer/)

**Apply it to Trail Notes.** When a backend disappears, distinguish what should happen to new requests from what can happen to a connection already assigned to the failed backend.

## Netflix · Routing and overload

Netflix's original Zuul write-up describes using Ribbon for outbound client-side load balancing. Its November 2020 engineering post describes how Zuul shed lower-priority requests progressively under pressure to protect playback. The team reported that its streaming availability metric held steady during the incident shown in the post. [Netflix's original Zuul write-up](https://netflixtechblog.com/announcing-zuul-edge-service-in-the-cloud-ab3af5be08ee) · [Netflix's 2020 load-shedding write-up](https://netflixtechblog.com/keeping-netflix-reliable-using-prioritized-load-shedding-6cc827b02f94)

**Apply it to Trail Notes.** In the hypothetical lesson workload, protect the guide request first during a sustained capacity shortfall. Optional work, such as recommendations, may be a candidate for shedding. Decide which requests qualify and measure whether essential requests still meet their latency target.

[Return to the load-balancing lesson](./README.md#first-pass)
