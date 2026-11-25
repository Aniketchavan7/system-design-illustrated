# Real-World Production Deep Dives: Rate Limiting

> ⚠️ **Partly source-checked.** Deep Dive 1 (Stripe) is checked against Stripe's own post. The others summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> How **Stripe**, **Google**, and **Netflix** approach distributed rate limiting, protect against cascading failures, and enforce concurrency limits.

---

## 💳 Deep Dive 1: How Stripe Uses Rate Limiters and Load Shedders

> **Source:** Paul Tarjan, ["Scaling your API with rate limiters"](https://stripe.com/blog/rate-limiters), Stripe engineering blog, 30 March 2017. Everything in this section comes from that post. Where it gives no number, neither do we.

### 1. The problem
Stripe's API serves many users at once. One user who sends too much traffic, by accident or on purpose, must not take the API down for everyone else. The post separates two kinds of protection:

- A **rate limiter** decides per *user*: "this user is sending too much."
- A **load shedder** decides from the state of the *whole system*: "we are overloaded, drop the least important work first."

### 2. The four limiters Stripe runs in production

```
[ Inbound API request ]
          │
          ▼
[ 1. Request rate limiter ]          N requests per second per user (token bucket)
          │
          ▼
[ 2. Concurrent requests limiter ]   cap on requests in flight at once
          │
          ▼
[ 3. Fleet usage load shedder ]      keeps part of the fleet free for critical requests
          │
          ▼
[ 4. Worker utilization load shedder ] last line of defence on a busy box
          │
          ▼
[ API servers ]
```

#### 1. Request rate limiter
- Restricts each user to *N* requests per second. The post calls it "by far the most important one". It rejected millions of requests in the month the post was written.
- It allows brief bursts above the cap, so a real spike such as a flash sale still gets through.

#### 2. Concurrent requests limiter
- Caps requests *in progress*, not requests per second. The post's example: "You can only have 20 API requests in progress at the same time."
- It targets CPU-heavy endpoints, where many slow requests at once compete for resources. It triggered far less often: 12,000 requests in that month.

#### 3. Fleet usage load shedder
- Splits traffic into critical methods (for example, creating charges) and non-critical ones (for example, listing charges), and counts each type in a Redis cluster.
- It reserves a share of the fleet for critical work. In the post's example, with 20% reserved, non-critical requests beyond their 80% allocation get **HTTP 503**.

#### 4. Worker utilization load shedder
- The "final line of defense". When a box runs short of free workers, it sheds the least critical traffic first. It starts with test-mode traffic and moves up through GETs and POSTs, keeping critical methods for last.
- Shedding and recovery are deliberately slow, so the system doesn't "flap" between the two states. Only 100 requests were rejected by it in that month.

### 3. How it is built
- **Algorithm:** "We use the token bucket algorithm to do rate limiting." Every Stripe user has a bucket. Each request takes a token, and tokens drip back in over time.
- **Store:** "We implement our rate limiters using Redis."
- **Fail open:** errors inside the limiter are caught so that a bug or outage in the limiter lets traffic through rather than blocking everyone.
- **Rollout:** dark-launch each limiter first to watch what it *would* block, and keep a kill switch or feature flag to turn it off quickly.
- **Status codes:** the post discusses choosing between **429 Too Many Requests** and **503 Service Unavailable**. It does not describe rate-limit response headers.

> ℹ️ An earlier version of this page described a "usage" tier and a fraud or card-testing tier, and showed `X-RateLimit-*` headers on every response. The source doesn't support any of that, so we removed it.
---

## 🎬 Deep Dive 2: How Netflix & Google Handle Rate Limiting (Adaptive Concurrency Limits)

### 1. Production Context & Scale
- **Companies**: Netflix (Edge & Inter-service RPC) and Google (Site Reliability Engineering & gRPC).
- **The Epiphany**: **Static Rate Limits are Inherently Broken in Dynamic Clouds.**
  - If you set a static limit of 10,000 QPS, what happens when a database node crashes and backend capacity drops to 6,000 QPS? The rate limiter still permits 10,000 QPS, causing a catastrophic cascading collapse.
  - What happens if you scale up the cluster to handle 25,000 QPS? The static limit blocks legitimate traffic unnecessarily.

### 2. Netflix's Architecture: Adaptive Concurrency Limits (TCP Vegas & Little's Law)
Netflix open-sourced the `concurrency-limits` library, replacing arbitrary static RPS limits with mathematical feedback loops inspired by TCP congestion control.

```
[ Inbound Request Stream ]
             │
             ▼
[ Netflix Adaptive Concurrency Limiter ]
   ├── Measures Current Latency (RTT)
   ├── Compares with Baseline Latency (No-Load RTT)
   │
   ├── If RTT <= Baseline: Increase Concurrency Limit (+1)
   └── If RTT > Threshold: Decrease Concurrency Limit (Backoff)
             │
             ▼
[ Microservice Business Logic ]
```

#### The Algorithm Mechanics (Little's Law)
According to Little's Law:
$$L = \lambda \times W$$
$$\text{Concurrency} = \text{Throughput} \times \text{Latency}$$

1. The service continuously monitors request round-trip time (RTT).
2. It tracks the **Minimum RTT** observed during low-traffic periods (the physical baseline latency of the system).
3. If current RTT begins to climb significantly above baseline, the system has entered **queueing delay** (congestion).
4. The limiter dynamically contracts the permitted concurrency limit:
   $$\text{Limit}_{t+1} = \text{Limit}_t \times \beta \quad (\text{Multiplicative Decrease})$$
5. When RTT recovers, it gradually increases the limit:
   $$\text{Limit}_{t+1} = \text{Limit}_t + \alpha \quad (\text{Additive Increase})$$

#### Traffic Prioritization
When throttling is active, Netflix drops low-priority background traffic first:
- **Priority 1 (Critical)**: Video playback start, license verification (Never dropped).
- **Priority 2 (User Interactive)**: Search queries, browsing UI.
- **Priority 3 (Background)**: Viewing history bookmarks, analytics beacons (Dropped immediately).

---

## 🏢 Deep Dive 3: How Google SRE Uses Client-Side Throttling

Google SRE solves the problem of a struggling server being killed by client retries. Google implemented **Client-Side Throttling** inside the gRPC client stub.

### The Formula
Clients track the number of requests they sent in the last 2 minutes (`requests`) and the number of requests accepted by the server without error (`accepts`).
Clients compute the probability of dropping their own request before sending it:

$$P_{\text{drop}} = \max\left(0, \frac{\text{requests} - K \times \text{accepts}}{\text{requests} + 1}\right)$$

- Where $K$ is the multiplier (typically $K = 2.0$ or $1.5$).
- **How it behaves**:
  - If the server accepts all requests, $\text{requests} \approx \text{accepts}$, so $\text{requests} - 2(\text{accepts}) < 0 \implies P_{\text{drop}} = 0$ (no throttling).
  - If the server starts failing requests due to overload, $P_{\text{drop}}$ automatically increases. The client itself discards requests locally with zero network load on the struggling server!

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Stripe (rate limiters + load shedders) | Netflix (Adaptive Concurrency Limits) | Google (Client-Side Adaptive Throttling) |
|---|---|---|---|
| **Location** | In front of the API servers | Ingress Gateway + Embedded Service Interceptor | Client SDK / gRPC Transport Stub |
| **Limiting Dimension** | Requests per second per user, requests in flight, then fleet and worker load | Dynamic In-flight Concurrency based on RTT | Request vs Accept ratio over sliding window |
| **Storage Dependency** | Redis (token buckets and request counts) | In-memory atomic counters (zero external dependencies) | In-memory local client metrics |
| **Responsiveness** | Static thresholds updated via configuration | Autonomic, continuous adaptation to real-time load | Client-side self-policing protects downstream servers |

---

## 🎯 System Design Interview Takeaways
1. **Never Propose a Single Global Limiter**: Structure it in layers, as Stripe does: per-user rate limit, then a concurrency cap, then load shedders that protect critical traffic when the whole system is busy.
2. **Preventing Race Conditions**: Always mention that distributed token buckets in Redis must be implemented via **atomic Lua scripts** or Redis cell modules to prevent concurrent read-modify-write race conditions.
3. **Adaptive Limits Impress Interviewers**: Differentiate yourself by explaining why static RPS limits fail during cascading failures and proposing latency-based adaptive concurrency limits (Little's Law / TCP Vegas).
