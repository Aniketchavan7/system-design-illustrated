# Real-World Production Deep Dives: Distributed Rate Limiter

> Deep-dive architectural dissections of how **Google (Doorman & Cloud Armor)**, **Netflix (Zuul & Concurrency Limits)**, **Cloudflare (eBPF/XDP)**, and **Stripe (Redis Lua)** implement distributed rate limiting and overload protection at multi-million QPS scale.

---

## 🏢 Deep Dive 1: How Google Implements Rate Limiting (Doorman & Cloud Armor)

### 1. Production Context & Scale
- **Systems**: **Google Doorman** (Global Distributed Client-Side Quota Server) and **Google Cloud Armor**.
- **Traffic Volume**: Handles millions of RPCs per second across internal Google services (YouTube, Search, Bigtable) and cloud perimeter ingress.
- **The Challenge**: A single client fleet with 50,000 Borg containers can accidentally launch an internal DDoS attack on a shared backend database if not coordinated globally.

### 2. Google's Architecture: The Doorman Client-Side Quota Architecture

```
[ Google Service Client Fleet (50,000 Containers) ]
      │                   │                   │
      ▼                   ▼                   ▼
 [ Local Bucket ]    [ Local Bucket ]    [ Local Bucket ]
 (Local Cache)       (Local Cache)       (Local Cache)
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │ (Periodic Token Leases: Every 5s)
                          ▼
            [ Google Doorman Quota Server ]
              ├── Global Resource Capacity Model
              ├── Fair-Share Proportional Allocation
              └── Dynamic Master Election via Chubby
```

#### A. The Lease-Based Token Model
- Querying a centralized quota server for *every single RPC* would multiply network traffic and add 5ms latency to every operation.
- **Google Doorman's Solution**:
  - Client containers periodically contact Doorman (e.g., every 5 seconds) to request a **Lease of Capacity** (e.g., "grant me 200 operations for the next 5 seconds").
  - The client consumes those operations locally in RAM with **zero network latency**.
  - If the client's local bucket runs dry before the lease renews, it throttles requests locally.

#### B. Fair-Share Allocation Algorithm
- When total demand from all 50,000 clients exceeds backend capacity:
  - Doorman does *not* randomly drop requests.
  - It computes a **Fair-Share Max-Min algorithm**, ensuring small, low-traffic clients receive 100% of their small requests, while massive batch jobs are proportionally dialed down.

---

## 🎬 Deep Dive 2: How Netflix Uses Rate Limiting (Zuul Adaptive Concurrency Limits)

### 1. Production Context & Scale
- **System**: Netflix **Zuul Edge Rate Limiter** and the `concurrency-limits` library.
- **Scale**: Over 100 billion edge requests daily; peak loads exceeding 2+ million concurrent connections.
- **Philosophy**: Dynamic adaptive limits based on system health rather than brittle static numbers.

### 2. Netflix's Architecture: TCP Vegas & Little's Law

```
[ Inbound Request Stream to Zuul Gateway ]
                    │
                    ▼
[ Netflix Adaptive Concurrency Limiter (Netty Interceptor) ]
  ├── Measures Round-Trip Latency (RTT) per Request
  ├── Compares with Moving Baseline (No-Load RTT)
  │
  ├── If RTT <= Baseline: Limit = Limit + 1  (Additive Increase)
  └── If RTT > Baseline:  Limit = Limit * β  (Multiplicative Decrease)
                    │
                    ▼
[ Upstream Microservice Target Pool ]
```

#### A. Why Static RPS Limits Fail at Netflix
- If Netflix sets a hard-coded rate limit of 5,000 RPS for a service:
  - If a database node slows down, the service can only process 2,500 RPS before thread pools choke. The static rate limiter still lets 5,000 RPS through, causing the service to crash.
  - Netflix replaced static RPS limits with **Adaptive Concurrency Limits** based on **Little's Law**:
    $$\text{Concurrency} = \text{Throughput} \times \text{Latency}$$

#### B. Priority Shedding
When congestion occurs, Netflix sheds traffic according to strict priority tiers:
1. **Critical (Never Dropped)**: Video playback start, license checks.
2. **Interactive**: UI catalog browsing, user search.
3. **Background (Dropped First)**: Telemetry pings, viewing history sync.

---

## 🛡️ Deep Dive 3: How Cloudflare Implements Line-Rate Drops (eBPF & XDP)

### 1. Production Context & Scale
- Handles over **55 million HTTP requests per second** across 330+ cities worldwide.
- Mitigates multi-terabit volumetric DDoS attacks at line rate.

### 2. In-Kernel eBPF & XDP Drops
- Standard web application proxies crash from kernel interrupt overhead when flooded with millions of packets per second.
- Cloudflare runs **eBPF bytecode programs inside the Network Interface Card (NIC) driver** using **XDP (eXpress Data Path)**:
  - Packets exceeding rate limit thresholds are dropped via `XDP_DROP` directly in the network card ring buffer before the Linux kernel allocates memory or triggers CPU interrupts.
  - Absorbs millions of malicious packets per second with virtually **zero server CPU utilization**!

---

## 💳 Deep Dive 4: How Stripe Uses Atomic Redis Sliding Windows

### 1. Production Context & Scale
- Millions of payment API transactions daily across thousands of merchants.
- Multi-tier defense: Request Limiter, Concurrency Limiter, Usage Limiter, and Fraud Limiter.

### 2. Atomic Redis Lua Execution
- Fixed window counters suffer from the **Boundary Burst Problem** (doubling the permitted rate across window resets).
- Stripe implements a **Sliding Window Log** using Redis Sorted Sets (`ZREMRANGEBYSCORE`, `ZCARD`, `ZADD`) executed atomically inside a **single Redis Lua script**:
  - Redis executes Lua scripts atomically in a single thread, eliminating concurrency race conditions.
  - Guarantees 100% mathematical accuracy under massive concurrency with sub-millisecond execution.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Google Doorman | Netflix Concurrency Limits | Cloudflare Edge Limiter | Stripe API Limiter |
|---|---|---|---|---|
| **Primary Level** | Client-Side / Quota Server | Gateway / Interceptor | L3/L4/L7 Kernel (eBPF) | L7 Reverse Proxy |
| **Limiting Strategy** | Lease-based Fair-Share | Dynamic RTT Feedback (TCP Vegas) | Volumetric Sliding Window | Multi-Tier Token & Sliding Window |
| **State Storage** | In-Memory Doorman Server | Local In-Memory Counters | eBPF Kernel Maps | Distributed Redis Clusters |
| **Drop Action** | Client delays or throttles | Drops non-critical traffic | `XDP_DROP` at line rate | HTTP 429 Too Many Requests |

---

## 🎯 System Design Interview Takeaways
1. **Never Propose a Single Global Limiter**: Structure rate limiting as a multi-tier defense: Edge eBPF DDoS filter -> API Gateway Token Bucket -> Concurrency Limiter -> Database query cost limiter.
2. **Preventing Race Conditions**: Always explain that distributed rate limiters in Redis require **atomic Lua scripts** or Redis Cell modules to avoid race conditions.
3. **Adaptive Concurrency vs Static Limits**: Differentiate yourself by explaining why static RPS limits fail during cascading failures and proposing **Adaptive Concurrency Limits** (Little's Law).
