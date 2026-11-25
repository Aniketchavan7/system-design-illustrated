"""Build cards-data.js, index.html, and docs/flashcards.html from repository modules."""
from argparse import ArgumentParser
from collections import Counter
from html import escape
import json
import os
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parent

CATEGORY_MAP = {
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
    "45": ("Full System Designs", "system_design"),
}

CATEGORY_ORDER = (
    ("foundations", "Foundations"),
    ("networking", "Networking & Traffic"),
    ("storage", "Storing Data"),
    ("caching", "Caching & Edge"),
    ("distributed", "Distributed Systems"),
    ("async", "Async & Microservices"),
    ("system_design", "Full System Designs"),
)

KEY_NUMBERS_MAP = {
    "01": "TCP 3-way handshake adds 1 RTT (40–100ms) before 1st byte; TLS 1.3 adds +1 RTT; QUIC 0-RTT enables instant data exchange.",
    "02": "DNS resolution over UDP: 10–50ms; TTL commonly 300s (5m); Anycast BGP routes to closest of 100+ global edge POPs in <15ms.",
    "03": "L4 load balancing (Maglev/IPVS): >10M packets/sec per commodity server; L7 proxy (Envoy): 50k–100k RPS with TLS termination.",
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
    "31": "NTP network drift: up to 100–250ms over public internet; Google TrueTime GPS + Rubidium atomic clock drift: ε < 7ms.",
    "32": "Idempotency key TTL: 24 hours in Redis/DynamoDB; Status 409 Conflict / 422 Unprocessable vs 200 OK idempotent replay.",
    "33": "gRPC RPC call: <1ms internal latency with HTTP/2 binary framing; Service mesh Envoy sidecar proxy hop: ~0.5–1ms p99.",
    "34": "Hybrid Feed generation: Push for users <10k followers (<10ms fanout); Pull for celebrities (>1M followers) merged at read-time.",
    "35": "APNs/FCM delivery: >1M push notifications/sec; Rate limiting: 50 notifications/user/day to avoid fatigue; Kafka queue buffer.",
    "36": "Planetary crawler: 1 billion pages/month = ~400 pages/sec; Politeness delay: 100–500ms per domain; Robots.txt cache TTL: 24h.",
    "37": "Typeahead p99 latency SLA: <50ms; Trie in-memory traversal: O(K) where K is prefix length (~5 steps); Top 10 queries cached.",
    "38": "Block-level deduplication: 4MB chunk size; Chunk SHA-256 hash lookup: O(1); S3 multipart upload for files >100MB.",
    "39": "Uber H3 hexagon resolution 8: ~460m edge length; GeoHash 6 chars: ±0.6km box; S2 cell level 13: ~1.2 km² area.",
    "40": "Payment idempotency: 100% deduplication guarantee; Double-entry ledger: credits must equal debits; Dual-phase commit / Saga pattern.",
    "41": "Hotel room reservation hold TTL: 10–15 minutes; Optimistic concurrency control (version column) prevents double booking.",
    "42": "Redis Sorted Set (ZSET): ZADD / ZRANK in O(log N); 10M players lookup in <1ms; Score tie-breaker: (score * 10^10) + (10^10 - timestamp).",
    "43": "Distributed cron: 100k scheduled jobs/sec; Two-phase dispatch with Redis lease locks (30s TTL); Heartbeat every 5s.",
    "44": "Metrics collection: 10M time-series samples/sec; Influx/Prometheus gorilla compression: 16 bytes reduced to 1.37 bytes/datapoint.",
    "45": "Real-time ad click counting: Exactly-once stream processing; Flink tumbling 10s windows; Redis sliding counter for fraud detection.",
}


def latex_to_plain(text):
    """Convert inline and block LaTeX commands to clean Unicode text."""
    def replace_tex_body(expr):
        # Convert simple brace scripts first so outer \frac/\text can match nested expressions
        expr = re.sub(r"\^\{([^{}]+)\}", r"^\1", expr)
        expr = re.sub(r"_\{([^{}]+)\}", r"_\1", expr)
        for _ in range(4):
            expr = re.sub(r"\\(?:text|mathbf|mathrm|mathit|operatorname)\{([^{}]*)\}", r"\1", expr)
            expr = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1) / (\2)", expr)
        replacements = (
            (r"\left\lfloor", "⌊"), (r"\right\rfloor", "⌋"),
            (r"\lfloor", "⌊"), (r"\rfloor", "⌋"),
            (r"\left(", "("), (r"\right)", ")"),
            (r"\times", "×"), (r"\cdot", "·"),
            (r"\rightarrow", "→"), (r"\to", "→"),
            (r"\leftrightarrow", "↔"), (r"\implies", "⇒"),
            (r"\approx", "≈"), (r"\sim", "~"),
            (r"\le", "≤"), (r"\ge", "≥"), (r"\neq", "≠"),
            (r"\pm", "±"), (r"\forall", "∀"), (r"\in", "∈"),
            (r"\sum", "Σ"), (r"\gg", ">>"), (r"\ll", "<<"),
            (r"\epsilon", "ε"), (r"\mu", "μ"), (r"\lambda", "λ"),
            (r"\alpha", "α"), (r"\beta", "β"), (r"\Delta", "Δ"),
            (r"\pmod", " mod "), (r"\quad", " "), (r"\dots", "…"),
            (r"\#", "#"), (r"\%", "%"), (r"\_", "_"), (r"\{", "{"), (r"\}", "}"),
        )
        for src, dst in replacements:
            expr = expr.replace(src, dst)
        expr = re.sub(r"\s+", " ", expr).strip()
        return expr

    # Display math $$...$$
    text = re.sub(r"\$\$(.*?)\$\$", lambda m: replace_tex_body(m.group(1)), text, flags=re.DOTALL)

    # Inline math $...$ (skip literal currency ranges like $0.08 per GB ... $8,000)
    def replace_inline(m):
        inner = m.group(1)
        has_math_sym = any(tok in inner for tok in ("\\", "^", "_", "=", "+", "×", "≈", "→", "<", ">", "/"))
        if not has_math_sym and (" " in inner or "costs" in inner or "from" in inner):
            return m.group(0)
        return replace_tex_body(inner)

    text = re.sub(r"\$([^$\n]+)\$", replace_inline, text)
    # Catch stray backslash commands outside $ delimiters
    if "\\" in text:
        text = text.replace(r"\text{", "").replace(r"\times", "×").replace(r"\to", "→").replace(r"\approx", "≈")
    return text


def clean_section(text, max_len=850):
    text = re.sub(r"<summary>.*?</summary>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"💡\s*Click to reveal[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = latex_to_plain(text)

    lines = []
    for raw_line in text.split("\n"):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("[Return to") or stripped.startswith("---"):
            continue
        if stripped.startswith("|-") or stripped.startswith("| :"):
            continue
        if stripped.startswith("|"):
            parts = [p.strip() for p in stripped.split("|")[1:-1] if p.strip()]
            if len(parts) >= 2 and not any(k in parts[0] for k in ("Concept", "Term", "Feature")):
                clean_term = parts[0].strip("*")
                clean_desc = " ".join(parts[1:]).replace("**", "")
                lines.append(f"- **{clean_term}**: {clean_desc}")
            continue
        # Convert nested/sub-bullets or headings cleanly
        if raw_line.lstrip().startswith(("- ", "* ")):
            lines.append("- " + raw_line.lstrip()[2:].strip())
            continue
        if stripped.startswith(("### ", "#### ")):
            # Drop boilerplate section titles, turn substantive subsections into bold labels
            h_text = re.sub(r"^#{3,4}\s*", "", stripped).strip()
            if re.match(r"^(?:1\.\s*Production Context|2\.\s*The Core Problem|3\.\s*.*Architecture|The Architecture|Key Technical Mechanisms)\b", h_text):
                if ":" in h_text and not h_text.endswith(":"):
                    h_text = h_text.split(":", 1)[1].strip()
                else:
                    continue
            h_text = re.sub(r"^[A-Z]\.\s+", "", h_text)
            lines.append(f"### {h_text}")
            continue
        lines.append(stripped)

    combined = "\n\n".join(lines)
    # Collapse excess gap inside bullet runs so lists group cleanly
    combined = re.sub(r"(?m)(^- .+)\n\n(?=- )", r"\1\n", combined)
    combined = re.sub(r"(?m)(^\d+\. .+)\n\n(?=\d+\. )", r"\1\n", combined)

    if len(combined) > max_len:
        cut = combined[:max_len]
        # Prefer ending at a clean line or sentence boundary when possible
        last_nl = cut.rfind("\n")
        if last_nl > max_len * 0.65:
            cut = cut[:last_nl]
        else:
            cut = cut.rsplit(" ", 1)[0]
        combined = cut.rstrip(" ,;:-") + "..."
    return combined


def clean_dive_label(header):
    lbl = re.sub(
        r"^(?:[^\w\s]+|\d+\.|Deep Dive \d+:?\s*(?:How\s+)?|\s)+",
        "",
        header,
    ).strip()
    lbl = re.sub(r"\s*·\s*", " — ", lbl)
    if " Uses " in lbl:
        left, right = lbl.split(" Uses ", 1)
        topic = right.split("(")[0].split(":")[0].strip()
        lbl = f"{left.strip()} — {topic}"
    elif " Implements " in lbl:
        left, right = lbl.split(" Implements ", 1)
        topic = right.split("(")[0].split(":")[0].strip()
        lbl = f"{left.strip()} — {topic}"
    else:
        lbl = re.sub(r"\s*\([^)]*$", "", lbl)
        lbl = lbl.split(":")[0].strip()
        # "Uber Schemaless, Hashing into a Fixed Set of Shards" -> "Uber Schemaless"
        lbl = lbl.split(", ")[0].strip()

    # Keep short without cutting mid-phrase or leaving trailing conjunctions
    words = lbl.split()
    if len(lbl) > 44:
        acc = []
        for w in words:
            candidate = " ".join([*acc, w])
            if len(candidate) > 44 and acc:
                break
            acc.append(w)
        while len(acc) > 2 and acc[-1].lower() in {"and", "&", "or", "the", "a", "in", "of", "to", "for", "at"}:
            acc.pop()
        lbl = " ".join(acc)
    lbl = re.sub(r"[\s—\-(&]+$", "", lbl).strip()
    return lbl or "Production Architecture"


def parse_dive(header, body):
    lbl = clean_dive_label(header)
    # Source lines and "earlier version" notes belong on the full page, not the card.
    body = re.sub(r"^> (?:\*\*Sources?:\*\*|ℹ️).*\n?", "", body, flags=re.MULTILINE)
    idx1 = body.find("### 1.")
    idx2 = body.find("### 2.")
    idx3 = body.find("### 3.")
    idx4 = body.find("### 4.")

    if idx3 != -1 and idx4 != -1:
        sec_text = body[idx3:idx4]
    elif idx3 != -1:
        sec_text = body[idx3:]
    elif idx2 != -1 and idx4 != -1:
        sec_text = body[idx2:idx4]
    else:
        sec_text = body

    ctx = ""
    if idx1 != -1:
        end_idx = idx2 if idx2 != -1 else (idx3 if idx3 != -1 else len(body))
        sec1_lines = [line.strip() for line in body[idx1:end_idx].split("\n") if line.strip().startswith("-")][:2]
        if sec1_lines:
            ctx = "\n".join(sec1_lines)

    full_text = (ctx + "\n\n" + sec_text).strip() if ctx else sec_text.strip()
    return lbl, clean_section(full_text, 850)


def build_cards():
    folders = [
        d.name for d in sorted(REPO_ROOT.iterdir())
        if d.is_dir() and re.match(r"^\d{2}-", d.name)
    ]
    cards = []
    for idx, fld in enumerate(folders, 1):
        num = fld.split("-")[0]
        readme_txt = (REPO_ROOT / fld / "README.md").read_text(encoding="utf-8")
        rwe_txt = (REPO_ROOT / fld / "REAL_WORLD_EXAMPLES.md").read_text(encoding="utf-8")

        m_title = re.search(r"^#\s+\d+\s*[·\-:]\s*(.+)$", readme_txt, re.MULTILINE)
        title = m_title.group(1).strip() if m_title else fld[3:].replace("-", " ").title()
        cat_name, cat_id = CATEGORY_MAP.get(num, ("Foundations", "foundations"))

        m_eli5 = re.search(r"##\s*🧒\s*The 30-second version.*?\n(.*?)(?=\n##|\Z)", readme_txt, re.DOTALL)
        if not m_eli5:
            m_eli5 = re.search(r"##\s*.*?(?:30-second|ELI5).*?\n(.*?)(?=\n##|\Z)", readme_txt, re.DOTALL | re.IGNORECASE)
        eli5_txt = clean_section(m_eli5.group(1), 850) if m_eli5 else "Core architectural building block for distributed systems."

        m_ana = re.search(r"##\s*.*?(?:analogy|Everyday Analogy|Physical Analogy).*?\n(.*?)(?=\n##|\Z)", readme_txt, re.DOTALL | re.IGNORECASE)
        ana_txt = clean_section(m_ana.group(1), 750) if m_ana else ""
        if not ana_txt.strip():
            ana_txt = f"Think of {title} like a real-world coordinator ensuring high throughput, fault isolation, and low latency across requests."

        m_q = re.search(r"###\s*Q1[:\s*]*(.*?)\n(.*?)(?=\n###|\n##|\Z)", readme_txt, re.DOTALL)
        if not m_q:
            m_q = re.search(r"###\s*.*?(?:Question 1|Q1|Question).*?\n(.*?)(?=\n###|\n##|\Z)", readme_txt, re.DOTALL | re.IGNORECASE)

        q_title = "Top Senior Engineering Interview Question"
        q_ans = "Detailed architectural tradeoff analysis in module README."
        if m_q:
            q_raw = latex_to_plain(m_q.group(1).strip().strip('"').strip("'"))
            if q_raw:
                q_title = q_raw
            q_ans = clean_section(m_q.group(2), 850)

        dives = re.findall(r"^##\s+([^\n]+)\n(.*?)(?=^##\s+|\Z)", rwe_txt, re.MULTILINE | re.DOTALL)
        primary_label, primary_desc = (
            parse_dive(dives[0][0], dives[0][1])
            if len(dives) >= 1
            else ("Google Production Scale", "Powers planetary scale infrastructure with ultra-low latency guarantees.")
        )
        secondary_label, secondary_desc = (
            parse_dive(dives[1][0], dives[1][1])
            if len(dives) >= 2
            else ("Netflix Production Scale", "Deploys fault-tolerant microservices across global AWS multi-region clusters.")
        )

        cards.append({
            "id": idx,
            "number": num,
            "folder": fld,
            "title": title,
            "category": cat_name,
            "category_id": cat_id,
            "eli5": eli5_txt,
            "analogy": ana_txt,
            "key_numbers": KEY_NUMBERS_MAP.get(num, "Sub-millisecond memory latency vs 10ms disk latency."),
            "primary_case_label": primary_label,
            "google_example": primary_desc,
            "secondary_case_label": secondary_label,
            "netflix_example": secondary_desc,
            "interview_question": q_title,
            "interview_answer": q_ans,
        })
    return cards


def render_flashcard_html(cards, *, in_docs):
    counts = Counter(c["category_id"] for c in cards)
    total = len(cards)
    home_href = "./" if in_docs else "docs/index.html"
    lib_href = "library.html" if in_docs else "docs/library.html"
    guide_href = "./guides/study-guide.html" if in_docs else "./STUDY_GUIDE.md"
    cs_href = "./guides/cheatsheet.html" if in_docs else "./CHEATSHEET.md"
    fc_href = "./guides/decision-flowcharts.html" if in_docs else "./DECISION_FLOWCHARTS.md"
    contrib_href = "./guides/contributing.html" if in_docs else "./CONTRIBUTING.md"

    chips = [f'      <button class="category-chip active" data-cat="all">All Topics <span class="chip-count">{total}</span></button>']
    for cid, label in CATEGORY_ORDER:
        chips.append(
            f'      <button class="category-chip" data-cat="{cid}">{escape(label)} '
            f'<span class="chip-count">{counts.get(cid, 0)}</span></button>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Design Illustrated — Interactive Flashcards</title>
  <meta name="description" content="Master {total} core system design concepts, real numbers math, and FAANG case studies (Google, Netflix, Meta, Uber, Stripe) with interactive flashcards.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="app.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220%200%20100%20100%22><text y=%22.9em%22 font-size=%2290%22>§</text></svg>">
</head>
<body>

  <!-- Top App Navigation -->
  <header>
    <div class="header-container">
      <a href="{home_href}" class="brand">
        <span class="brand-icon">§</span>
        <div>
          <span class="brand-title">System Design Illustrated</span>
          <span class="brand-badge">Flashcards</span>
        </div>
      </a>

      <div class="header-actions">
        <a id="link-course" href="{home_href}" class="btn-secondary">Start learning</a>
        <a id="link-library" href="{lib_href}" class="btn-secondary">Topic library</a>
        <a id="link-study-guide" href="{guide_href}" class="btn-secondary">Study Guide</a>
        <a id="link-cheatsheet" href="{cs_href}" class="btn-secondary" title="View Back-of-the-Envelope Master Cheat Sheet">Cheat Sheet</a>
        <a id="link-flowcharts" href="{fc_href}" class="btn-secondary" title="View Master Architectural Decision Flowcharts">Flowcharts</a>
        <a id="link-contribute" href="{contrib_href}" class="btn-secondary" title="Contribute and share knowledge">Contribute</a>
        <a id="link-reddit" href="https://www.reddit.com/r/systemdesign/" target="_blank" rel="noopener" class="btn-secondary" title="Join Reddit discussions and share feedback">Reddit</a>
        <a href="https://github.com/Aniketchavan7/system-design-illustrated" target="_blank" rel="noopener" class="btn-secondary">GitHub Repo</a>
        <button id="btn-theme" class="btn-secondary" title="Toggle Obsidian / Warm Paper reading theme">Paper Theme</button>
        <button id="btn-reset" class="btn-secondary" title="Reset all mastery and study status">Reset Progress</button>
      </div>
    </div>
  </header>

  <!-- Progress Bar Section -->
  <section class="progress-section">
    <div class="progress-header">
      <span id="progress-text">Card 1 of {total}</span>
      <span id="progress-percentage">0/{total} Mastered (0%)</span>
    </div>
    <div class="progress-track">
      <div id="progress-fill" class="progress-fill"></div>
    </div>
  </section>

  <!-- Search and Filtering Section -->
  <section class="controls-section">
    <div class="search-and-status">
      <div class="search-input-wrapper">
        <span class="search-icon">/</span>
        <input type="text" id="search-input" class="search-input" placeholder="Search architectural topics, FAANG systems, latency figures... (/)" autocomplete="off">
      </div>

      <div id="status-filters" class="status-filters">
        <button class="status-pill active" data-status="all">All Cards</button>
        <button class="status-pill" data-status="unseen">Unseen</button>
        <button class="status-pill" data-status="review">Review Later</button>
        <button class="status-pill" data-status="mastered">Mastered</button>
      </div>

      <button id="btn-shuffle" class="btn-secondary" title="Shuffle Card Deck (S)">Shuffle Deck</button>
    </div>

    <!-- Category Filter Chips -->
    <div id="category-chips" class="category-chips">
{chr(10).join(chips)}
    </div>
  </section>

  <!-- Main Flashcard Stage -->
  <main>
    <div id="flashcard-container" class="flashcard-container">
      <div id="flashcard" class="flashcard">

        <!-- Front of Card: Concept, Analogy & Latency Numbers -->
        <div class="card-face card-front">
          <div class="card-header">
            <div class="card-meta">
              <span id="card-number" class="card-number">Module 01</span>
              <span id="card-category" class="card-category-badge">Networking &amp; Traffic</span>
              <span id="card-status" class="card-status-badge status-unseen">Unseen</span>
            </div>
            <span class="flip-prompt">Space / Click to Flip ↵</span>
          </div>

          <h2 id="card-title-front" class="card-title">Client–Server Networking</h2>

          <div class="section-label">Core Architectural Concept</div>
          <div id="card-eli5" class="card-body-text">
            Every digital product is a conversation between a client (your phone or browser) asking for something, and a server (a machine in a datacenter) answering.
          </div>

          <div class="section-label">Physical Intuition &amp; Analogy</div>
          <div id="card-analogy" class="analogy-box">
            Think of ordering at a drive-thru window versus mailing a registered postal letter.
          </div>

          <div class="section-label">Latency Budget &amp; Hardware Reality</div>
          <div id="card-numbers" class="numbers-box">
            TCP 3-way handshake adds 1 RTT (40–100ms) before 1st byte; TLS 1.3 adds +1 RTT; QUIC 0-RTT enables instant data exchange.
          </div>

          <div class="card-footer">
            <div class="card-links">
              <a id="link-readme" href="#" target="_blank" class="card-link">Chapter Readme</a>
              <a id="link-examples" href="#" target="_blank" class="card-link">FAANG Case Studies</a>
              <a id="link-demo" href="#" target="_blank" class="card-link">Python Simulation</a>
            </div>
            <span class="flip-prompt">Flip for Case Studies &amp; Interview ↵</span>
          </div>
        </div>

        <!-- Back of Card: Deep Dive, FAANG & Interview QA -->
        <div class="card-face card-back">
          <div class="card-header">
            <div class="card-meta">
              <span class="card-number">Production Architecture</span>
              <span class="card-category-badge">Deep Dive</span>
            </div>
            <span class="flip-prompt">Space / Click to Flip Back ↵</span>
          </div>

          <h2 id="card-title-back" class="card-title">Client–Server Networking</h2>

          <div class="section-label">FAANG Production Case Studies</div>
          <div class="case-studies-grid">
            <div class="company-card">
              <div id="primary-case-label" class="company-name">Google — QUIC deployment</div>
              <div id="google-desc" class="company-desc">
                Pioneered QUIC / HTTP/3 over UDP to eliminate head-of-line blocking and achieve 0-RTT handshakes.
              </div>
            </div>

            <div class="company-card">
              <div id="secondary-case-label" class="company-name">Netflix — A gateway proxies the request</div>
              <div id="netflix-desc" class="company-desc">
                Processes tens of billions of requests through Netty-based Zuul 2 edge proxies with TLS session tickets.
              </div>
            </div>
          </div>

          <div class="section-label">Senior Interview Question &amp; Model Answer</div>
          <div class="qa-card">
            <div id="interview-q" class="qa-question">
              Why does HTTP/3 run over UDP instead of TCP?
            </div>
            <div id="interview-a" class="qa-answer">
              TCP enforces strict byte-stream ordering. If one packet drops, all streams pause (head-of-line blocking). HTTP/3 uses QUIC over UDP so dropped packets only pause that specific stream.
            </div>
          </div>

          <div class="card-footer">
            <div class="card-links">
              <a id="link-readme-back" href="#" target="_blank" class="card-link">Chapter Readme</a>
              <a id="link-examples-back" href="#" target="_blank" class="card-link">FAANG Case Studies</a>
              <a id="link-demo-back" href="#" target="_blank" class="card-link">Python Simulation</a>
            </div>
            <span class="flip-prompt">Space to Flip ↵</span>
          </div>
        </div>

      </div>
    </div>

    <!-- Bottom Study Action Bar -->
    <div class="action-bar">
      <button id="btn-prev" class="nav-btn" title="Previous Card (Left Arrow)">← Previous</button>

      <button id="btn-flip" class="btn-flip" title="Flip Card (Spacebar / Up / Down)">Flip Card</button>

      <div class="study-buttons">
        <button id="btn-review" class="btn-review" title="Mark for Review Later (2 or R)">Review Later</button>
        <button id="btn-master" class="btn-master" title="Mark as Mastered (1 or M)">✓ Mastered</button>
      </div>

      <button id="btn-next" class="nav-btn" title="Next Card (Right Arrow)">Next →</button>
    </div>
  </main>

  <!-- Keyboard Shortcuts Footer -->
  <footer>
    <p>
      Shortcuts:
      <span class="kbd-shortcut">Space</span> Flip &nbsp;·&nbsp;
      <span class="kbd-shortcut">←</span> <span class="kbd-shortcut">→</span> Navigate &nbsp;·&nbsp;
      <span class="kbd-shortcut">1</span> Mastered &nbsp;·&nbsp;
      <span class="kbd-shortcut">2</span> Review &nbsp;·&nbsp;
      <span class="kbd-shortcut">S</span> Shuffle &nbsp;·&nbsp;
      <span class="kbd-shortcut">/</span> Search
    </p>
  </footer>

  <!-- App Data and Controller Scripts -->
  <script src="cards-data.js"></script>
  <script src="app.js"></script>
</body>
</html>
"""


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated flashcard files would change")
    args = parser.parse_args()

    cards = build_cards()
    out_js = (
        "// System Design Illustrated - Flashcards Dataset (45 Modules)\n"
        f"window.SYSTEM_DESIGN_FLASHCARDS = {json.dumps(cards, indent=2)};\n"
    )
    outputs = {
        REPO_ROOT / "cards-data.js": out_js,
        REPO_ROOT / "docs" / "cards-data.js": out_js,
        REPO_ROOT / "index.html": render_flashcard_html(cards, in_docs=False),
        REPO_ROOT / "docs" / "flashcards.html": render_flashcard_html(cards, in_docs=True),
    }

    stale = []
    for path, content in outputs.items():
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current is not None:
                current = current.replace("\r\n", "\n")
            if current != content.replace("\r\n", "\n"):
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if stale:
        parser.exit(1, "Regenerate with python build_rich_flashcards.py: " + ", ".join(stale) + "\n")
    if not args.check:
        print(f"Generated {len(cards)} clean flashcards and synchronized index.html + docs/flashcards.html!")


if __name__ == "__main__":
    main()
