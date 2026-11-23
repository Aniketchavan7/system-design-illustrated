# 27 · Back-of-the-Envelope Estimation

> **Part 0 · Foundations** · ⏱️ ~20 min read · Prerequisites: None (Foundational)

---

> 🏢 **Real-World Deep Dives**: Detailed case studies of how **Google** (Jeff Dean's latency rules) & **Netflix** (capacity planning for 260M subscribers) execute real-world estimations are documented in [REAL_WORLD_EXAMPLES.md](./REAL_WORLD_EXAMPLES.md).

---

## 🧒 The 30-second version

Back-of-the-envelope estimation is the art of **rapidly calculating system scale (QPS, memory, disk storage, network bandwidth)** before writing a single line of architecture. It is not about finding the exact decimal; it is about finding the **order of magnitude** ($10	ext{ RPS}$ vs $10,000	ext{ RPS}$; $10	ext{ GB}$ vs $10	ext{ TB}$).

- **Powers of 10 shortcuts**:
  - $1	ext{ Million requests/day} \approx \mathbf{12	ext{ requests/second (RPS)}}$.
  - $1	ext{ Billion requests/day} \approx \mathbf{12,000	ext{ RPS}}$.
  - Peak traffic is typically estimated at $\mathbf{2	imes 	ext{average}}$.
- **Hardware Latency Reality**: Reading from RAM ($\approx 100	ext{ ns}$) is **100,000 times faster** than reading from a spinning disk ($\approx 10	ext{ ms}$) and **1,500,000 times faster** than a cross-ocean network round trip ($\approx 150	ext{ ms}$).

---

## 🍕 Everyday analogy: Planning a Wedding Banquet

Imagine planning a wedding:
- You don't need to know if Uncle Bob eats exactly $412	ext{ grams}$ or $420	ext{ grams}$ of chicken.
- You estimate: *"150 guests $	imes$ 1 main dish $\approx$ 150 meals. Plus 20% buffer for hungry eaters $\approx$ 180 portions."*
- If your rough estimate said 150 portions and you prepared for 15, your guests starve. If you prepared for 15,000, food rots and you go bankrupt.

Back-of-the-envelope estimation gives you the exact ballpark to pick the right server size, database tier, and caching budget.

---

## 🧩 The Problem It Solves

Without back-of-the-envelope estimations:
1. **Architectural Over-Engineering**: A candidate proposes a multi-datacenter Kafka cluster with Cassandra sharding for a service receiving $5	ext{ requests/minute}$.
2. **Catastrophic Under-Provisioning**: A team provisions a standard \$20/mo SQL database for a service expected to ingest $50	ext{ GB of telemetry logs per second}$, causing Day 1 production crashes.
3. **Interview Disqualification**: Top-tier tech companies (Google, Meta, Amazon) explicitly score candidates on whether they can calculate QPS, storage growth, and RAM sizing in under 3 minutes.

---

## 🔢 The Cheat Sheet: Powers of 2 & 10

| Power of 2 | Exact Bytes | Approximate (Powers of 10) | Standard Unit | Real-World Context |
| :--- | :--- | :--- | :--- | :--- |
| $2^{10}$ | 1,024 | $1	ext{ Thousand } (10^3)$ | **1 KB** | Small JSON API response |
| $2^{20}$ | 1,048,576 | $1	ext{ Million } (10^6)$ | **1 MB** | High-res thumbnail / photo |
| $2^{30}$ | 1,073,741,824 | $1	ext{ Billion } (10^9)$ | **1 GB** | 1 hour of SD video stream |
| $2^{40}$ | 1,099,511,627,776 | $1	ext{ Trillion } (10^{12})$ | **1 TB** | Standard server NVMe SSD |
| $2^{50}$ | 1,125,899,906,842,624 | $1	ext{ Quadrillion } (10^{15})$ | **1 PB** | Daily YouTube upload ingestion |
| $2^{60}$ | 1,152,921,504,606,846,976| $1	ext{ Quintillion } (10^{18})$ | **1 EB** | Total storage of global cloud providers |

---

## ⏱️ Latency Numbers Every Software Engineer Must Know

*Original figures compiled by Google Senior Fellow Jeff Dean, updated for modern NVMe hardware:*

| Operation | Real-World Time | Scaled to Human Time (1ns = 1s) |
| :--- | :--- | :--- |
| **L1 CPU Cache Reference** | $0.5	ext{ ns}$ | 0.5 seconds (A single heartbeat) |
| **Branch Mispredict** | $5	ext{ ns}$ | 5 seconds |
| **L2 CPU Cache Reference** | $7	ext{ ns}$ | 7 seconds |
| **Mutex Lock / Unlock** | $25	ext{ ns}$ | 25 seconds |
| **Main Memory (RAM) Reference**| $100	ext{ ns}$ | 1.6 minutes |
| **Compress 1KB with Snappy** | $2,000	ext{ ns } (2	ext{ }\mu	ext{s})$ | 33 minutes |
| **Read 1MB Sequentially from Memory** | $5,000	ext{ ns } (5	ext{ }\mu	ext{s})$ | 1.4 hours |
| **Read 1MB Sequentially from NVMe SSD** | $10,000	ext{ ns } (10	ext{ }\mu	ext{s})$ | 2.8 hours |
| **SSD Random Read (NVMe)** | $20,000	ext{ ns } (20	ext{ }\mu	ext{s})$ | 5.5 hours |
| **Send 1KB Packet over 1Gbps LAN** | $10,000	ext{ ns } (10	ext{ }\mu	ext{s})$ | 2.8 hours |
| **HDD Spinning Disk Seek** | $10,000,000	ext{ ns } (10	ext{ ms})$ | **4 months!** |
| **Round Trip Time (RTT): US to Europe** | $150,000,000	ext{ ns } (150	ext{ ms})$ | **5 years!** |

### The Core Architectural Takeaways:
1. **RAM is $100,000	imes$ faster than disk seeks**: Keep hot data in cache.
2. **Sequential disk I/O matches network speed**: Log-structured storage (Kafka, LSM-trees) is fast because it uses sequential disk writes.
3. **Cross-region network latency dominates everything**: Avoid synchronous cross-datacenter round-trips on write paths.

---

## 📐 The Master Estimation Template

Whenever an interviewer gives you a design problem:

### 1. Traffic (QPS) Math
- **Input**: Daily Active Users (DAU) and average actions per user per day.
- **Formula**:
  $$	ext{Average QPS} = \frac{	ext{DAU} 	imes 	ext{Requests per user}}{86,400	ext{ seconds}}$$
- **Rule of Thumb**: Round $86,400$ to **$100,000$** for fast mental math:
  $$	ext{Average QPS} \approx \frac{	ext{Total Daily Requests}}{100,000}$$
- **Peak QPS**: $	ext{Peak QPS} = 	ext{Average QPS} 	imes 2$.

### 2. Storage Estimation Math
- **Formula**:
  $$	ext{Daily Storage} = 	ext{Daily Writes} 	imes 	ext{Average Payload Size}$$
  $$	ext{5-Year Storage} = 	ext{Daily Storage} 	imes 365 	imes 5 \approx 	ext{Daily Storage} 	imes 2,000$$

### 3. Memory (Cache Sizing) Math: The 80/20 Rule
- **The Pareto Principle**: $20\%$ of hot content generates $80\%$ of read traffic.
- **Formula**:
  $$	ext{RAM Required} = 	ext{Daily Read Volume (Bytes)} 	imes 0.20$$

---

## 💻 Try It Yourself

The companion script [`demo.py`](./demo.py) is an interactive estimation tool that takes DAU, read/write ratios, and payload sizes to generate complete infrastructure sizing reports in milliseconds.

Run it directly in your terminal:
```bash
python demo.py
```

---

## 🌍 Where You'll See It in Production

- **Google Search**: Capacity engineers use QPS estimates to provision Borg container tasks worldwide ahead of major global events (Olympics, elections).
- **Netflix Open Connect**: Uses 80/20 cache estimations to determine how many 200TB flash storage appliances (OCAs) must be deployed in each regional ISP.
- **Amazon AWS**: EC2 auto-scaling groups use capacity prediction curves based on historical back-of-the-envelope models.

---

## 🎯 Top 5 Interview Questions & Deep Answers

### Q1: "How do you quickly estimate QPS from Daily Active Users (DAU) in an interview?"
<details>
<summary>💡 Click to reveal the ideal senior engineering answer</summary>

State your assumptions clearly:
1. *"Assume $100	ext{M DAU}$ and each user makes 10 requests per day."*
2. Total requests $= 1	ext{ Billion requests/day}$.
3. Divide by $100,000$ seconds (rounding $86,400$):
   $$	ext{Average QPS} \approx \frac{1,000,000,000}{100,000} = \mathbf{10,000	ext{ QPS}}$$
4. Apply peak multiplier ($2	imes$):
   $$	ext{Peak QPS} = 10,000 	imes 2 = \mathbf{20,000	ext{ QPS}}$$
Interviewers reward fast, clean arithmetic over struggling with exact decimals.

</details>

---

### Q2: "Estimate the storage required for Twitter over 5 years."
<details>
<summary>💡 Click to reveal the ideal senior engineering answer</summary>

1. Assume $300	ext{M DAU}$. $100	ext{M}$ users post 2 tweets/day $= 200	ext{M tweets/day}$.
2. Each tweet is 280 chars $+$ metadata (User ID, timestamp) $\approx 500	ext{ bytes}$.
3. Assume 20% of tweets contain an image ($200	ext{ KB}$):
   - Text storage: $200	ext{M} 	imes 500	ext{B} = 100	ext{ GB/day}$.
   - Media storage: $40	ext{M} 	imes 200	ext{ KB} = 8,000	ext{ GB/day} = 8	ext{ TB/day}$.
   - Total daily storage $\approx 8.1	ext{ TB/day}$.
4. 5-Year Storage:
   $$8.1	ext{ TB} 	imes 365 	imes 5 \approx 8.1	ext{ TB} 	imes 1,825 \approx \mathbf{14.8	ext{ Petabytes}}$$

</details>

---

### Q3: "How do you size the RAM needed for a Redis caching tier?"
<details>
<summary>💡 Click to reveal the ideal senior engineering answer</summary>

Apply the **80/20 Pareto rule**:
1. Calculate daily read volume. If daily active data volume is $5	ext{ TB}$.
2. To satisfy 80% of reads from RAM, you need:
   $$5	ext{ TB} 	imes 0.20 = \mathbf{1	ext{ TB of RAM}}$$
3. Account for Redis memory overhead (pointers, hash tables, slab allocation) $\approx 25\%$ extra buffer:
   $$	ext{Total RAM} \approx 1	ext{ TB} 	imes 1.25 = \mathbf{1.25	ext{ TB}}$$
4. Provision four $256	ext{ GB}$ or eight $128	ext{ GB}$ Redis cluster instances.

</details>

---

### Q4: "Why is sequential disk access comparable in speed to RAM access?"
<details>
<summary>💡 Click to reveal the ideal senior engineering answer</summary>

Disk latency is dominated by physical seek times (moving the mechanical head or initializing NAND flash row buffers). Once the initial seek occurs, hardware controllers read contiguous blocks at the physical bus bandwidth limit (up to 3–7 GB/s on PCIe 4.0 NVMe). Sequential disk access bypasses seek overhead, which is why log-structured engines (Kafka, LSM-trees) achieve near-RAM write throughput on standard disks.

</details>

---

### Q5: "Estimate the network egress bandwidth for YouTube."
<details>
<summary>💡 Click to reveal the ideal senior engineering answer</summary>

1. Assume 1 Billion hours of video watched per day.
2. Average bitrate across mobile and desktop: $2.5	ext{ Mbps}$.
3. Continuous egress bandwidth:
   $$	ext{Bandwidth} = \frac{1,000,000,000	ext{ hrs} 	imes 3600	ext{s} 	imes 2.5	ext{ Mbps}}{86,400	ext{s}} \approx \mathbf{104	ext{ Terabits per second (Tbps)}}$$
4. With a 98% CDN cache offload, origin egress drops to only $\approx 2	ext{ Tbps}$.

</details>

---

## 📚 Go Deeper
- **System Design Interview – An Insider's Guide (Volume 1)** by Alex Xu: Chapter 2 (*Back-of-the-envelope Estimation*).
- **Jeff Dean's Original Stanford Talk**: *Numbers Everyone Should Know* (Google Research).
