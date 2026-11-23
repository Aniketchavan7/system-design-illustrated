import os
import re
import json

repo = '.'
folders = [d for d in sorted(os.listdir(repo)) if os.path.isdir(os.path.join(repo, d)) and re.match(r'^\d{2}-', d)]

category_map = {
    "01": ("Networking & Traffic", "networking"),
    "02": ("Networking & Traffic", "networking"),
    "03": ("Networking & Traffic", "networking"),
    "04": ("Networking & Traffic", "networking"),
    "05": ("Networking & Traffic", "networking"),
    "06": ("Storing Data", "storage"),
    "07": ("Storing Data", "storage"),
    "08": ("Storing Data", "storage"),
    "09": ("Storing Data", "storage"),
    "10": ("Caching & Edge", "caching"),
    "11": ("Caching & Edge", "caching"),
    "12": ("Caching & Edge", "caching"),
    "13": ("Distributed Systems", "distributed"),
    "14": ("Distributed Systems", "distributed"),
    "15": ("Distributed Systems", "distributed"),
    "16": ("Distributed Systems", "distributed"),
    "17": ("Distributed Systems", "distributed"),
    "18": ("Async & Microservices", "async"),
    "19": ("Async & Microservices", "async"),
    "20": ("Async & Microservices", "async"),
    "21": ("Full System Designs", "system_design"),
    "22": ("Full System Designs", "system_design"),
    "23": ("Full System Designs", "system_design"),
    "24": ("Full System Designs", "system_design"),
    "25": ("Full System Designs", "system_design"),
    "26": ("Foundations", "foundations"),
    "27": ("Foundations", "foundations"),
    "28": ("Distributed Systems", "distributed"),
    "29": ("Storing Data", "storage"),
    "30": ("Async & Microservices", "async"),
    "31": ("Distributed Systems", "distributed"),
    "32": ("Async & Microservices", "async"),
    "33": ("Async & Microservices", "async"),
    "34": ("Full System Designs", "system_design"),
    "35": ("Full System Designs", "system_design"),
    "36": ("Full System Designs", "system_design"),
    "37": ("Full System Designs", "system_design"),
    "38": ("Full System Designs", "system_design"),
    "39": ("Full System Designs", "system_design"),
    "40": ("Full System Designs", "system_design"),
    "41": ("Full System Designs", "system_design"),
    "42": ("Full System Designs", "system_design"),
    "43": ("Full System Designs", "system_design"),
    "44": ("Full System Designs", "system_design"),
    "45": ("Full System Designs", "system_design")
}

key_numbers_map = {
    "01": "Practice workload: 50 ms network round trip + 20 ms server work = about 70 ms on an established connection.",
    "02": "Practice workload: a record cached at 09:00:00 with a 60-second TTL has 30 seconds left at 09:00:30.",
    "03": "Practice workload: three servers at 900 requests per second offer 2,700 in total. One failure leaves capacity for 1,800 against demand of 2,000.",
    "04": "API Gateway adds 2–5ms hop latency; JWT signature verification takes ~50μs; Zuul/Envoy processes 50,000+ RPS per node.",
    "05": "Redis sliding window log: 1–2ms per check; Token bucket in memory: <10μs; Stripe distributed rate limiter handles >100M API calls/day.",
    "06": "Postgres B-Tree read: 1–5ms; Cassandra partition write: <1ms; DynamoDB p99: <10ms single-digit millisecond latency.",
    "07": "Multi-Paxos replication: 50–150ms cross-region commit; Async replica lag: typically 100ms – 2s under heavy write spikes.",
    "08": "Consistent hashing shard lookup: O(1) <1μs; Shard range splits triggered at ~64MB–1GB boundaries in Bigtable/Spanner.",
    "09": "LSM-Tree write (append log): 100μs; LSM read with Bloom filter: 1–2 disk seeks (1–5ms); B+Tree random write: 10ms without SSD.",
    "10": "Redis in-memory read: 0.1–0.5ms; Cache hit ratio target: >95%; Cache stampede mitigation reduces DB write surges by 99%.",
    "11": "W-TinyLFU eviction: 98% hit rate with O(1) cost; TTL jitter (± 10–20%) prevents synchronized thundering herds.",
    "12": "CDN edge cache hit latency: 5–20ms vs 150–300ms origin round trip; Netflix Open Connect serves >95% traffic from inside ISPs.",
    "13": "Spanner 99.999% availability (CP); TrueTime atomic clock uncertainty bound: ε < 7ms; Amazon Dynamo 99.999% write availability (AP).",
    "14": "Linearizable read requires quorum / consensus (~50ms); Eventual consistency read returns local replica state in <1ms.",
    "15": "Raft/Paxos leader election timeout: 150–300ms; Heartbeat interval: 50ms; Majority quorum size = 2F + 1 nodes (e.g., 3 of 5).",
    "16": "Ring hash space: 2^32 or 2^64 slots; 100–250 virtual nodes (vnodes) per physical machine balances load variance within 5%.",
    "17": "Kafka sequential append throughput: >100MB/sec per disk broker; Zero-copy OS sendfile eliminates user-space context switches.",
    "18": "Two-Phase Commit (2PC) write latency: 2–3 network RTTs with blocking coordinator; Sagas replace 2PC using async compensations.",
    "19": "2PC coordinator failure blocks participants indefinitely; Sagas achieve eventual consistency with local ACID transactions.",
    "20": "Circuit breaker failure rate threshold: 50% errors over 10s sliding window; Sleep window before half-open retry: 5000ms.",
    "21": "Short URL length: 7 Base62 chars (62^7 = 3.5 trillion URLs); Cache 20% hottest URLs (80/20 Pareto principle) in Redis.",
    "22": "Bloom filter: 1% false positive rate requires only 9.6 bits per key and 7 hash functions; 0% false negative rate.",
    "23": "WebSocket connection footprint: ~10KB RAM/socket; Epoll handles 100k+ concurrent sockets per Linux box; Redis PubSub fanout.",
    "24": "4K video stream: 15–25 Mbps; HLS/DASH chunk size: 2–6 seconds; Transcoding pipeline splits video into 10+ bitrates/resolutions.",
    "25": "Doorman / Token Bucket: 10,000 tokens/sec capacity; Sliding window counter: 1 counter per second slot across 60 seconds.",
    "26": "From 1 to 10M users: Single server (1k users) -> DB replica (100k) -> CDN + Redis (1M) -> Sharded multi-region (>10M).",
    "27": "Powers of two: 2^10 = 1KB, 2^20 = 1MB, 2^30 = 1GB, 2^40 = 1TB; 100k QPS @ 1KB payload = 100MB/s = 800 Mbps network bandwidth.",
    "28": "Snowflake ID: 64-bit integer (41-bit ms timestamp = 69 years, 10-bit machine ID = 1024 nodes, 12-bit sequence = 4096 IDs/ms/node).",
    "29": "ACID Isolation levels: Read Uncommitted -> Read Committed -> Repeatable Read -> Serializable; SSI has <1% overhead vs 2PL locks.",
    "30": "Protobuf serialization: 3–5x smaller payload and 10–20x faster deserialization than JSON; Zero-copy buffer parsing.",
    "31": "NTP network drift: up to 100–250ms over public internet; Google TrueTime GPS + Rubidium atomic clock drift: epsilon < 7ms.",
    "32": "Idempotency key TTL: 24 hours in Redis/DynamoDB; Status 409 Conflict / 422 Unprocessable vs 200 OK idempotent replay.",
    "33": "gRPC RPC call: <1ms internal latency with HTTP/2 binary framing; Service mesh Envoy sidecar proxy hop: ~0.5–1ms p99.",
    "34": "Hybrid Feed generation: Push for users <10k followers (<10ms fanout); Pull for celebrities (>1M followers) merged at read-time.",
    "35": "APNs/FCM delivery: >1M push notifications/sec; Rate limiting: 50 notifications/user/day to avoid fatigue; Kafka queue buffer.",
    "36": "Planetary crawler: 1 billion pages/month = ~400 pages/sec; Politeness delay: 100–500ms per domain; Robots.txt cache TTL: 24h.",
    "37": "Typeahead p99 latency SLA: <50ms; Trie in-memory traversal: O(K) where K is prefix length (~5 steps); Top 10 queries cached.",
    "38": "Block-level deduplication: 4MB chunk size; Chunk SHA-256 hash lookup: O(1); S3 multipart upload for files >100MB.",
    "39": "Uber H3 hexagon resolution 8: ~460m edge length; GeoHash 6 chars: ±0.6km box; S2 cell level 13: ~1.2 km^2 area.",
    "40": "Payment idempotency: 100% deduplication guarantee; Double-entry ledger: credits must equal debits; Dual-phase commit / Saga pattern.",
    "41": "Hotel room reservation hold TTL: 10–15 minutes; Optimistic concurrency control (version column) prevents double booking.",
    "42": "Redis Sorted Set (ZSET): ZADD / ZRANK in O(log N); 10M players lookup in <1ms; Score tie-breaker: (score * 10^10) + (10^10 - timestamp).",
    "43": "Distributed cron: 100k scheduled jobs/sec; Two-phase dispatch with Redis lease locks (30s TTL); Heartbeat every 5s.",
    "44": "Metrics collection: 10M time-series samples/sec; Influx/Prometheus gorilla compression: 16 bytes reduced to 1.37 bytes/datapoint.",
    "45": "Real-time ad click counting: Exactly-once stream processing; Flink tumbling 10s windows; Redis sliding counter for fraud detection."
}

def clean_section(text, max_len=900):
    text = re.sub(r'<summary>.*?</summary>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'💡\s*Click to reveal[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\$([^\$]+)\$', r'\1', text)
    text = re.sub(r'\\times', 'x', text)
    text = re.sub(r'\\to', '->', text)
    text = re.sub(r'\\approx', '~', text)
    lines = []
    for l in text.split('\n'):
        s = l.strip()
        if not s or s.startswith('[Return to') or s.startswith('---'):
            continue
        if s.startswith('|-') or s.startswith('| :'):
            continue
        if s.startswith('|'):
            parts = [p.strip() for p in s.split('|')[1:-1] if p.strip()]
            if len(parts) >= 2 and not ('Concept' in parts[0] or 'Term' in parts[0] or 'Feature' in parts[0]):
                clean_term = parts[0].strip('*')
                clean_desc = ' '.join(parts[1:]).replace('**', '')
                lines.append(f"- **{clean_term}**: {clean_desc}")
            continue
        lines.append(s)
    combined = '\n\n'.join(lines)
    if len(combined) > max_len:
        combined = combined[:max_len].rsplit(' ', 1)[0] + '...'
    return combined

def parse_dive(h, b):
    lbl = re.sub(r'^(?:🏢|🎬|💳|🌐|🍿|👥|🎮|📦|🛳️|🚙|🔬|⚓|🔗|🛡️|🐦|📺|1\.|2\.|3\.|4\.|\s*Deep Dive \d+:?\s*How\s*)+', '', h).strip()
    lbl = re.sub(r'\s*·\s*', ' — ', lbl)
    if ' Uses ' in lbl:
        parts = lbl.split(' Uses ')
        lbl = f"{parts[0].strip()} · {parts[1].split('(')[0].strip()}"
    elif ' Implements ' in lbl:
        parts = lbl.split(' Implements ')
        lbl = f"{parts[0].strip()} · {parts[1].split('(')[0].strip()}"
    elif ' Architecture' in lbl:
        lbl = lbl.split(' Architecture')[0].strip()
    lbl = lbl.split(':')[0].strip()
    if len(lbl) > 42:
        lbl = lbl[:42].rsplit(' ', 1)[0]
    if not lbl:
        lbl = "Production Architecture"
    
    idx1 = b.find('### 1.')
    idx2 = b.find('### 2.')
    idx3 = b.find('### 3.')
    idx4 = b.find('### 4.')
    
    if idx3 != -1 and idx4 != -1:
        sec_text = b[idx3:idx4]
    elif idx3 != -1:
        sec_text = b[idx3:]
    elif idx2 != -1 and idx4 != -1:
        sec_text = b[idx2:idx4]
    else:
        sec_text = b
            
    ctx = ''
    if idx1 != -1:
        end_idx = idx2 if idx2 != -1 else (idx3 if idx3 != -1 else len(b))
        sec1_lines = [l.strip() for l in b[idx1:end_idx].split('\n') if l.strip().startswith('-')][:2]
        if sec1_lines:
            ctx = '\n'.join(sec1_lines)
            
    full_text = (ctx + '\n\n' + sec_text).strip() if ctx else sec_text.strip()
    return lbl, clean_section(full_text, 850)

cards = []

for idx, fld in enumerate(folders, 1):
    num = fld.split('-')[0]
    readme_path = os.path.join(repo, fld, 'README.md')
    rwe_path = os.path.join(repo, fld, 'REAL_WORLD_EXAMPLES.md')
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_txt = f.read()
    with open(rwe_path, 'r', encoding='utf-8') as f:
        rwe_txt = f.read()

    # Title
    m_title = re.search(r'^#\s+\d+\s*[·\-:]\s*(.+)$', readme_txt, re.MULTILINE)
    title = m_title.group(1).strip() if m_title else fld[3:].replace('-', ' ').title()

    cat_name, cat_id = category_map.get(num, ("Foundations", "foundations"))

    # ELI5
    m_eli5 = re.search(r'##\s*🧒\s*The 30-second version.*?\n(.*?)(?=\n##|\Z)', readme_txt, re.DOTALL)
    if not m_eli5:
        m_eli5 = re.search(r'##\s*.*?(?:30-second|ELI5).*?\n(.*?)(?=\n##|\Z)', readme_txt, re.DOTALL | re.IGNORECASE)
    eli5_txt = clean_section(m_eli5.group(1), 850) if m_eli5 else 'Core architectural building block for distributed systems.'

    # Analogy
    m_ana = re.search(
        r'^##[ \t]+[^\n]*analogy[^\n]*\n(.*?)(?=^#{1,2}[ \t]|\Z)',
        readme_txt, re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    ana_txt = clean_section(m_ana.group(1), 750) if m_ana else 'Physical world intuition for distributed systems.'
    if not ana_txt.strip():
        # Fallback if empty
        ana_txt = f"Think of {title} like a real-world coordinator ensuring high throughput, fault isolation, and low latency across requests."

    # Interview Q & A
    m_q = re.search(r'###\s*Q1[:\s*]*(.*?)\n(.*?)(?=\n###|\n##|\Z)', readme_txt, re.DOTALL)
    if not m_q:
        m_q = re.search(r'###\s*.*?(?:Question 1|Q1|Question).*?\n(.*?)(?=\n###|\n##|\Z)', readme_txt, re.DOTALL | re.IGNORECASE)
    
    q_title = 'Top Senior Engineering Interview Question'
    q_ans = 'Detailed architectural tradeoff analysis in module README.'
    if m_q:
        q_raw = m_q.group(1).strip().strip('"').strip("'")
        if q_raw:
            q_title = q_raw
        q_ans = clean_section(m_q.group(2), 850)

    # Prefer the prediction and answer from a first-pass lesson when supplied.
    lesson = re.search(r"^## First pass\n(.*?)(?=^## |\Z)", readme_txt, re.MULTILINE | re.DOTALL)
    if lesson:
        exercise = re.search(
            r"^\*\*Predict\.\*\* ([^\n]+)\n\s*<details>\s*"
            r"<summary>Reveal the answer</summary>(.*?)</details>",
            lesson[1],
            re.MULTILINE | re.DOTALL,
        )
        if exercise:
            q_title = exercise[1]
            q_ans = clean_section(exercise[2], 850)

    # Real-World Production Dives
    dives = re.findall(r'^##\s+([^\n]+)\n(.*?)(?=^##\s+|\Z)', rwe_txt, re.MULTILINE | re.DOTALL)
    
    primary_label = "Google Production Scale"
    primary_desc = "Powers planetary scale infrastructure with ultra-low latency guarantees."
    secondary_label = "Netflix Production Scale"
    secondary_desc = "Deploys fault-tolerant microservices across global AWS multi-region clusters."

    if len(dives) >= 1:
        primary_label, primary_desc = parse_dive(dives[0][0], dives[0][1])

    if len(dives) >= 2:
        secondary_label, secondary_desc = parse_dive(dives[1][0], dives[1][1])

    card = {
        "id": idx,
        "number": num,
        "folder": fld,
        "title": title,
        "category": cat_name,
        "category_id": cat_id,
        "eli5": eli5_txt,
        "analogy": ana_txt,
        "key_numbers": key_numbers_map.get(num, "Sub-millisecond memory latency vs 10ms disk latency."),
        "primary_case_label": primary_label,
        "google_example": primary_desc,
        "secondary_case_label": secondary_label,
        "netflix_example": secondary_desc,
        "interview_question": q_title,
        "interview_answer": q_ans
    }
    cards.append(card)

out_js = "// System Design Illustrated - Flashcards Dataset (45 Modules)\nwindow.SYSTEM_DESIGN_FLASHCARDS = " + json.dumps(cards, indent=2) + ";\n"

with open(os.path.join(repo, 'cards-data.js'), 'w', encoding='utf-8') as f:
    f.write(out_js)

with open(os.path.join(repo, 'docs', 'cards-data.js'), 'w', encoding='utf-8') as f:
    f.write(out_js)

print(f"Generated {len(cards)} rich reading flashcards!")
