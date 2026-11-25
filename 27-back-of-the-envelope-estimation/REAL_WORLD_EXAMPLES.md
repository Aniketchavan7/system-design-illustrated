# Real-World Production Deep Dives: Back-of-the-Envelope Estimation

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

> Deep-dive architectural dissections of how **Google** and **Netflix** use quantitative estimation models for global capacity planning, datastore sizing, and network bandwidth forecasting.

---

## 🏢 Deep Dive 1: How Google Uses Quantitative Estimation (Jeff Dean's Capacity Planning)

### 1. Production Context & History
- In the early 2000s, Google Fellow **Jeff Dean** formulated the famous lecture *"Numbers Everyone Should Know"*, transforming distributed systems engineering from guesswork into rigorous quantitative sizing.
- Google SREs (Site Reliability Engineers) never deploy a new service without a **Capacity Plan** proving that network switches, memory allocations, and cluster CPU quotas can survive traffic growth.

### 2. Google's Web Search Index Sizing Model
When Google sized its crawling and index storage:
1. **The Crawl Target**: Estimate 20 Billion web pages indexed.
2. **Page Content**: Average HTML page after compression is $\approx 20\text{ KB}$.
3. **Raw Storage Requirement**:
   $$20,000,000,000 \times 20\text{ KB} = 400\text{ Terabytes of raw text}$$
4. **The Storage Multipliers**:
   - Inverted word index + PageRank link graph adds $2\times$ overhead $\to 800\text{ TB}$.
   - 3x GFS / Colossus distributed replication $\to \mathbf{2.4\text{ Petabytes}}$.
5. **Memory Sizing**:
   - Google calculated that keeping the entire 2.4PB index in RAM was financially impossible.
   - Using the 80/20 rule, they partitioned the inverted index so the top 20% most frequent search terms resided in RAM across thousands of leaf search machines, while long-tail queries fetched from disk.

---

## 🎬 Deep Dive 2: How Netflix Sizes Its Global CDN (Capacity Planning for 260M Subscribers)

### 1. Production Context & Scale
- Over 260 million active subscribers streaming over **100+ million hours of video daily**.
- Accounts for **15%+ of the world's downstream internet traffic**.

### 2. Netflix's Open Connect Appliance (OCA) Sizing Math
How does Netflix determine how many physical storage appliances to ship to an ISP (e.g., Comcast in Chicago)?
1. **Peak Evening Consumption**:
   - Chicago subscribers stream a peak aggregate bandwidth of **1.2 Terabits per second (Tbps)** at 9:00 PM.
2. **OCA Hardware Capacity**:
   - Each custom Netflix OCA server has a **100Gbps network interface card** and **200TB of NVMe flash storage**.
3. **Server Count Calculation**:
   $$\text{Servers Needed} = \frac{1,200\text{ Gbps}}{100\text{ Gbps/server}} = 12\text{ Servers}$$
   Add $N+2$ redundancy for hardware failure $\to \mathbf{14\text{ Open Connect Servers}}$ deployed in the Chicago IXP rack.
4. **Storage Sizing**:
   - 14 servers $\times$ 200TB $= 2.8\text{ Petabytes}$ of local flash storage.
   - Completely holds the top 4,000 most popular movies and episodes, delivering a **$98\%$ local cache hit rate** with zero origin bandwidth consumption during prime time!

---

## ⚖️ Comparative Estimation Matrix

| Dimension | Google SRE Planning | Netflix Open Connect Planning |
|---|---|---|
| **Primary Sizing Bottleneck** | In-memory RAM for low-latency ranking (<100ms) | Egress network bandwidth (Tbps) at ISP edge |
| **Replication Overhead** | 3x synchronous Paxos replication factor | Proactive overnight push replication to edge OCAs |
| **Safety Headroom Factor** | $1.5\times$ to $2.0\times$ peak traffic headroom | Provisioned for $N+2$ server rack failures |
| **Cost Tradeoff** | RAM vs NVMe Flash for search indexing | Transit ISP peering fees vs Hardware CapEx |

---

## 🎯 System Design Interview Takeaways
1. **Memorize the Rule of Thumb**: Remember that $1\text{M requests/day} \approx 12\text{ QPS}$ and $1\text{B requests/day} \approx 12,000\text{ QPS}$. It allows you to produce immediate QPS answers in seconds.
2. **Always Account for Replication Overhead**: When calculating storage, never stop at raw data size. Always multiply by $3\times$ for distributed replication (e.g. S3, GFS, Cassandra).
3. **Buffer for Caching Overhead**: In RAM estimation, always add a 20–30% memory buffer for data structure pointers, slab fragmentation, and hash map overhead.
