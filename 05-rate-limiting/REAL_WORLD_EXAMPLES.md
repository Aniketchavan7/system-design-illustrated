# Real-World Production Deep Dives: Rate Limiting

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

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

## 🎬 Deep Dive 2: How Netflix Adapts Concurrency Limits

> **Source:** the README of Netflix's open-source [`concurrency-limits`](https://github.com/Netflix/concurrency-limits) library. Everything in this section comes from it.

### 1. The idea
Instead of a fixed "N requests per second", the library argues that "we should be thinking in terms of concurrent requests where we apply queuing theory". It describes itself as a Java library that "implements and integrates concepts from TCP congestion control to auto-detect concurrency limits for services". A service's concurrency limit is treated like a TCP congestion window: it grows while things are healthy and shrinks when requests start queueing.

### 2. Little's Law
The README states the relationship as:

$$\text{Limit} = \text{Average RPS} \times \text{Average Latency}$$

For example, a service handling 200 requests per second at 50 ms each has about 200 × 0.05 = **10 requests in flight** on average. (This worked example is ours, not the README's.)

### 3. Two limit algorithms
- **Vegas** estimates how many requests are waiting in a queue as `L * (1 - minRTT/sampleRtt)`, where `minRTT` is the fastest latency seen (roughly, latency with no queue) and `sampleRtt` is the latest measurement. At the end of each sampling window it raises the limit **by 1** if the queue is below `alpha` (typically 2–3) and lowers it **by 1** if the queue is above `beta` (typically 4–6).
- **Gradient2** compares a long-term and a short-term exponential average of latency. When they diverge for a while, it treats that as a queue building up and "aggressively reduces the limit". It exists to address the bias and drift of relying on minimum latency alone.

### 4. Where it plugs in
- **gRPC** server and client interceptors. The server rejects excess requests with `Status.UNAVAILABLE`.
- A **servlet filter** that rejects with **HTTP 429 Too Many Requests**.
- An **executor** (`BlockingAdaptiveExecutor`) that sizes its thread pool to the current limit and blocks when the limit is reached.

### 5. Reserving capacity for important traffic
The limit can be split into percentage partitions by request type. The README's example guarantees **live traffic 90%** and **batch traffic 10%** of the limit, and requests in neither group "may only use excess capacity".

> ℹ️ An earlier version of this page listed Netflix's load-shedding priorities (playback and licence checks never dropped, bookmarks and analytics dropped first) and said the limit shrinks multiplicatively. We couldn't confirm the priority list from a source we could read, and the library's Vegas algorithm changes the limit by one at a time, so we removed both. Netflix describes its gateway-level shedding in ["Keeping Netflix Reliable Using Prioritized Load Shedding"](https://netflixtechblog.com/keeping-netflix-reliable-using-prioritized-load-shedding-6cc827b02f94) (2020). A sourced summary of that post would be a welcome contribution.

---

## 🏢 Deep Dive 3: How Google Throttles Requests at the Client

> **Source:** Alejandro Forero Cuervo, ["Handling Overload"](https://sre.google/sre-book/handling-overload/), chapter 21 of *Site Reliability Engineering* (Google, O'Reilly 2016). Everything in this section comes from that chapter.

When a backend is overloaded, rejecting a request still costs it work. If clients keep sending, the backend spends its capacity saying "no". Google's answer is **adaptive throttling**: once a client sees that "a significant portion of its recent requests have been rejected due to 'out of quota' errors", it starts rejecting some requests itself, so they "fail locally without even reaching the network".

### The formula
Each client task keeps two counts "for the last two minutes of its history":

- `requests`: requests the application tried to send
- `accepts`: requests the backend accepted

The client rejects a new request locally with probability:

$$P_{\text{reject}} = \max\left(0, \frac{\text{requests} - K \times \text{accepts}}{\text{requests} + 1}\right)$$

- While the backend accepts everything, `requests` stays below `K × accepts`, so the probability is 0.
- As the backend rejects more, `requests` outgrows `K × accepts` and the client drops more of its own traffic.

### Choosing K
The chapter says "we generally prefer the 2x multiplier". A **lower** K throttles more aggressively. With K = 1.1, only about one request is rejected by the backend for every 10 it accepts. A **higher** K throttles less: it wastes more backend work but spreads the backend's state to clients faster. The decision uses only local information, with "no additional dependencies or latency penalties".

> ℹ️ An earlier version said this runs "inside the gRPC client stub". The chapter doesn't say where it is implemented, only that clients do it, so we removed that.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Stripe (rate limiters + load shedders) | Netflix (`concurrency-limits`) | Google (adaptive throttling) |
|---|---|---|---|
| **Location** | In front of the API servers | Inside each service (gRPC interceptor, servlet filter or executor) | In each client task |
| **Limiting Dimension** | Requests per second per user, requests in flight, then fleet and worker load | Requests in flight, limit adjusted from measured latency | Ratio of requests to accepts over the last two minutes |
| **Storage Dependency** | Redis (token buckets and request counts) | None: each service measures its own latency | None: each client keeps its own counts |
| **Responsiveness** | Fixed limits per user; load shedders react to system load | Limit moves every sampling window | Rejection probability rises as backend rejections rise |

---

## 🎯 System Design Interview Takeaways
1. **Never Propose a Single Global Limiter**: Structure it in layers, as Stripe does: per-user rate limit, then a concurrency cap, then load shedders that protect critical traffic when the whole system is busy.
2. **Preventing Race Conditions**: Always mention that distributed token buckets in Redis must be implemented via **atomic Lua scripts** or Redis cell modules to prevent concurrent read-modify-write race conditions.
3. **Adaptive Limits Impress Interviewers**: Differentiate yourself by explaining why static RPS limits fail during cascading failures and proposing latency-based adaptive concurrency limits (Little's Law / TCP Vegas).
