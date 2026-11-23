# Real-World Production Deep Dives: Domain Name System (DNS)

> Deep-dive architectural dissections of how **Google** and **Netflix** use DNS for global traffic steering, Anycast routing, resilience, and rapid multi-region failover.

---

## 🏢 Deep Dive 1: How Google Uses DNS (Google Public DNS & Anycast Edge Routing)

### 1. Production Context & Scale
- **Service**: Google Public DNS (`8.8.8.8` and `8.8.4.4`).
- **Scale**: Resolves over **1 trillion DNS queries per day**, serving as the world's largest public recursive DNS service.
- **SLA**: 99.999% global availability with sub-15ms median query response latency worldwide.

### 2. The Core Problem at Google Scale
1. **DDoS Vulnerability of Static IPs**:
   - A single IP address bound to a single physical machine or data center can be trivially overwhelmed by volumetric UDP amplification attacks.
2. **Inaccurate CDN Routing (The Resolver Blindspot)**:
   - When a user in Singapore configured a third-party DNS resolver located in California, authoritative nameservers believed the user was in California and directed them to US servers, resulting in 250ms+ latency penalties.
3. **DNS Cache Poisoning (Kaminsky Attacks)**:
   - Malicious actors flood resolvers with forged UDP packets attempting to guess the 16-bit Transaction ID (`TxID`), injecting fraudulent IP records into resolver caches.

### 3. Google's Engineering Architecture

```
[ Client Query to 8.8.8.8 ]
             │
      BGP Anycast Routing
             │
      ┌──────┴──────────────────────────┐
      ▼                                 ▼
[ Tokyo POP (Anycast) ]      [ Frankfurt POP (Anycast) ]
      │                                 │
[ Maglev Load Balancer ]      [ Maglev Load Balancer ]
      │                                 │
[ Distributed Cache ]         [ Distributed Cache ]
      │ (Cache Miss)                    │ (Cache Miss)
      ▼                                 ▼
   EDNS Client Subnet (ECS) forwarded to Authoritative Nameserver
```

#### A. Global BGP Anycast Routing
- Google announces the IP prefixes `8.8.8.8/32` and `8.8.4.4/32` via Border Gateway Protocol (BGP) from **hundreds of Google Edge Points of Presence (PoPs)** across the planet.
- The internet's BGP routing table automatically directs a user's DNS query packet to the topologically closest healthy Google PoP via shortest Autonomous System (AS) path.
- **DDoS Resilience**: Volumetric attacks targeting `8.8.8.8` are naturally distributed across hundreds of global ingress data centers, absorbing terabits of attack traffic locally without degrading the rest of the world.

#### B. EDNS0 Client Subnet (ECS, RFC 7871)
- Google co-authored the **EDNS Client Subnet** standard.
- When `8.8.8.8` queries an authoritative nameserver (e.g., for `netflix.com`), it appends a truncated prefix of the client's IP (e.g., `/24` for IPv4).
- The authoritative nameserver can see where the actual end-user is located (rather than Google's resolver) and return the closest edge CDN server IP, while preserving user privacy by omitting the last 8 bits of the client address.

#### C. Defense Against Cache Poisoning
- **Port Randomization**: Uses all available source UDP ports (~60,000 possibilities), expanding the entropy space to $2^{16} 	imes 60,000 \approx 4 	ext{ billion}$ combinations.
- **DNS 0x20 Bit Encoding**: Randomizes the capitalization of domain queries (e.g., `wWw.gOOglE.cOm`). Authoritative servers must echo the exact casing in their response. An attacker cannot forge this without guessing the randomized bit pattern.

---

## 🎬 Deep Dive 2: How Netflix Uses DNS (Route 53 Latency-Based Routing & Disaster Evacuation)

### 1. Production Context & Scale
- **Cloud Infrastructure**: Netflix runs its control plane across multiple AWS regions: `us-east-1` (N. Virginia), `us-west-2` (Oregon), and `eu-west-1` (Ireland).
- **Scale**: Hundreds of millions of devices pinging Netflix API endpoints (`api-global.netflix.com`).
- **Disaster Preparedness**: Mandatory business requirement to survive complete loss of an entire AWS region (e.g., AWS us-east-1 fiber cut or control plane outage) without user disruption.

### 2. The Core Problem at Netflix Scale
- An entire AWS region can fail abruptly. Because Netflix operates active-active across multiple regions, subscriber traffic must be diverted away from the failing region to the healthy regions in under **10 minutes**.
- Standard DNS caching mechanisms honor TTL (Time to Live). If TTL is set to 24 hours, clients cache the dead region's IP for a full day. If TTL is set to 5 seconds, authoritative DNS servers get slammed by billions of requests per minute, creating enormous DNS billing costs and lookup latency.

### 3. Netflix's DNS Architecture: Automated Regional Evacuation

```
[ Subscriber Device (Smart TV / Mobile) ]
                    │
            api-global.netflix.com
                    │
                    ▼
     [ Amazon Route 53 Global DNS ]
   ├── Latency-Based Routing (LBR)
   ├── Weighted Routing Policy (Weighted CNAMEs)
   └── Route 53 Health Checks & CloudWatch Alarms
                    │
         ┌──────────┼──────────┐
   Weight: 50%  Weight: 50%  Weight: 0% (Evacuated!)
         ▼          ▼          ▼
   [ us-east-1 ] [ us-west-2 ] [ eu-west-1 ]
   (Operational) (Operational) (Degraded AWS Region)
```

#### A. Latency-Based Routing (LBR) + Weighted CNAMEs
- Netflix uses AWS Route 53 Latency-Based Routing. Route 53 measures network latency from global ISP vantage points to AWS regions and automatically maps a user in London to `eu-west-1` and a user in New York to `us-east-1`.
- Behind LBR, Netflix configures **Weighted Routing**:
  - `api-global.netflix.com` points to an intermediate CNAME layer with adjustable weights (e.g., Region A: 50, Region B: 50).

#### B. The Regional Evacuation ("Project Nimble") Automation
When Netflix detects regional degradation (e.g., elevated error rates in `us-east-1`):
1. **Step 1 (Pre-warming Destination Regions)**:
   - Before traffic is diverted, automated orchestrators scale up backend microservices in `us-west-2` and `eu-west-1` to absorb the incoming 50% traffic surge.
2. **Step 2 (DNS Weight Flipping)**:
   - The automation updates Route 53 DNS records, dialing `us-east-1` weight to 0 and increasing weights in surviving regions.
3. **Step 3 (TTL Management)**:
   - Normal operation uses a DNS TTL of **60 seconds**.
   - While some rogue ISP resolvers ignore TTLs and cache records for longer, over 95% of Netflix traffic shifts away from the dying region within **7 minutes**, keeping global streaming uninterrupted.

---

## ⚖️ Comparative Architecture Matrix

| Architectural Dimension | Google (Google Public DNS) | Netflix (Route 53 Multi-Region Traffic Steering) |
|---|---|---|
| **Role in Tech Stack** | Global Recursive Resolver & Edge Ingress | Authoritative Traffic Steering & Disaster Recovery |
| **Routing Mechanism** | BGP Anycast (L3/L4 network routing) | DNS Latency-Based Routing (LBR) & Weighted Records |
| **Cache Strategy** | Massive distributed in-memory cache with ECS | Short TTL (60s) for agility during regional failover |
| **Security Layer** | DNSSEC, 0x20 bit encoding, Port randomization | Route 53 IAM isolation, DNSSEC, DDoS shielding |
| **Failover Velocity** | Instantaneous via BGP route withdrawal (<1s) | Minutes (6-8 minutes) due to DNS TTL decay curve |

---

## 🎯 System Design Interview Takeaways
1. **Anycast vs Geolocation DNS**: Use Anycast for infrastructure IPs and recursive resolvers (network-level failover in milliseconds). Use Geo-DNS / Latency-Based Routing for steering users to multi-region cloud applications.
2. **The DNS Failover Reality Check**: Never claim in an interview that DNS failover is "instantaneous." Explain that DNS TTL guarantees a transition curve where straggler clients honor cached records for several minutes.
3. **Mitigating Resolver Mismatch**: Mention **EDNS Client Subnet (ECS)** when explaining how global CDNs accurately route users to local edges even when users use third-party DNS resolvers.
