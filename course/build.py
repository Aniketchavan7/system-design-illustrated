"""Render the Trail Notes course, rendered reference chapters, guides, and labs."""
from argparse import ArgumentParser
from dataclasses import dataclass
from html import escape
import json
import re
from pathlib import Path, PurePosixPath
from posixpath import normpath
from string import Template
from urllib.parse import quote, unquote, urlsplit

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "course"
PAGES = ROOT / "docs"
REPO = "https://github.com/Aniketchavan7/system-design-illustrated"


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    description: str
    source: str
    heading: str


@dataclass(frozen=True)
class Guide:
    slug: str
    title: str
    description: str
    source: str


FIRST_PASS = "## First pass"
EXERCISE = "## Trail Notes exercise"
LESSONS = (
    Lesson("networking", "Ask for a page", "Follow an HTTPS request from the browser to the server.",
           "01-client-server-networking/README.md", FIRST_PASS),
    Lesson("dns", "Find the website’s address", "See how a name becomes an address and why DNS answers can go stale.",
           "02-domain-name-system/README.md", FIRST_PASS),
    Lesson("load-balancing", "Keep the site online", "Predict what happens when one of three backends fails.",
           "03-load-balancing/README.md", FIRST_PASS),
    Lesson("caching", "Cache popular guides", "Estimate how many requests reach the origin when the cache fails.",
           "10-caching-patterns/README.md", EXERCISE),
    Lesson("queues", "Queue photo previews", "Work out how much a burst adds to a queue and when it drains.",
           "17-message-queues/README.md", EXERCISE),
    Lesson("regional-recovery", "Recover from a regional outage", "Check whether Trail Notes meets its recovery targets.",
           "advanced/multi-region-recovery.md", EXERCISE),
)

GUIDES = (
    Guide("cheatsheet", "Back-of-the-Envelope Master Cheat Sheet",
          "Powers of 2, hardware latency budget, QPS sizing formulas, and availability nines.",
          "CHEATSHEET.md"),
    Guide("decision-flowcharts", "Master Architectural Decision Flowcharts",
          "Visual decision trees for databases, consistency, caching, protocols, and distributed transactions.",
          "DECISION_FLOWCHARTS.md"),
    Guide("study-guide", "System Design Interview Study Guide",
          "Structured prep tracks, timed mock interview rubrics, and whiteboarding checklist.",
          "STUDY_GUIDE.md"),
    Guide("resource-reading-map", "Book-to-Course Reading Map",
          "Chapter-by-chapter mapping to Designing Data-Intensive Applications and System Design Interview.",
          "advanced/resource-reading-map.md"),
    Guide("durable-key-value-store", "Design a Durable Key-Value Store",
          "Replicated logs, majority commits, snapshots, and partition reconciliation.",
          "advanced/durable-key-value-store.md"),
    Guide("batch-stream-and-derived-data", "Batch, Stream, and Derived Views",
          "Building deterministic reports, event-time watermarks, and safe view rebuilds.",
          "advanced/batch-stream-and-derived-data.md"),
    Guide("multi-region-recovery", "Multi-Region Failover & Disaster Recovery",
          "RTO/RPO targets, failover topologies, single-writer fencing, and restore verification.",
          "advanced/multi-region-recovery.md"),
    Guide("authentication-and-authorization", "Authentication & Tenant Authorization",
          "OpenID Connect PKCE flow, session revocation, RBAC/ReBAC, and workload identity.",
          "advanced/authentication-and-authorization.md"),
    Guide("order-processing-lab", "Order Processing Crash-Recovery Lab",
          "Runnable Postgres + RabbitMQ transactional outbox and idempotent consumer lab.",
          "labs/order-processing/README.md"),
    Guide("contributing", "Contributing Guide",
          "How to contribute fixes, diagrams, case studies, and simulations.",
          "CONTRIBUTING.md"),
    Guide("community", "Community & Reddit Discussions",
          "Share feedback, post-mortem insights, and architectural debates on Reddit.",
          "COMMUNITY.md"),
    Guide("code-of-conduct", "Code of Conduct",
          "Our shared community standards and constructive learning values.",
          "CODE_OF_CONDUCT.md"),
)

GUIDE_MAP = {g.source: f"guides/{g.slug}.html" for g in GUIDES}
GUIDE_MAP["labs/order-processing"] = "guides/order-processing-lab.html"

MODULE_LABS = {
    "01-client-server-networking": ("learn/simulator.html", "Traffic & cache outage simulator"),
    "02-domain-name-system": ("learn/dns-lab.html", "DNS cache & TTL cutover lab"),
    "03-load-balancing": ("learn/simulator.html", "Traffic & server failure simulator"),
    "07-database-replication": ("learn/quorum-lab.html", "Quorum replication (N, W, R) lab"),
    "10-caching-patterns": ("learn/simulator.html", "Cache hit & outage simulator"),
    "13-cap-and-pacelc-theorems": ("learn/quorum-lab.html", "Quorum & CAP trade-off lab"),
    "14-consistency-models": ("learn/quorum-lab.html", "Quorum overlap & stale read lab"),
    "15-consensus-and-leader-election": ("learn/quorum-lab.html", "Majority quorum simulator"),
    "16-consistent-hashing": ("learn/hashing-lab.html", "Consistent hashing ring lab"),
    "17-message-queues": ("learn/queue-lab.html", "Queue backlog & drain simulator"),
}

DIAGRAMS = {
    "networking": (
        ("Browser", "Trail Notes server"),
        "The browser sends GET /guide. The server returns 200 OK and the guide HTML.",
    ),
    "dns": (
        ("Browser", "Recursive resolver", "Authoritative DNS"),
        "The resolver returns a cached address or follows referrals on a miss. The browser then connects to the site.",
    ),
    "load-balancing": (
        ("Browser", "Load balancer", "Server A, B, or C"),
        "The load balancer forwards the HTTPS request to one eligible server.",
    ),
}

STORY_HEADINGS = {"first-pass", "trail-notes-exercise"}
LOCAL_TARGETS = {
    alias: f"{lesson.id}.html"
    for lesson in LESSONS
    for alias in (
        [lesson.source, str(PurePosixPath(lesson.source).parent)]
        if lesson.source.endswith("/README.md") else [lesson.source]
    )
}

MERMAID_PROGRESSIVE_SCRIPT = """  <script type="module">
    if (document.querySelector('.mermaid')) {
      import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs')
        .then((mod) => {
          mod.default.initialize({ startOnLoad: false, theme: 'neutral' });
          return mod.default.run({ querySelector: '.mermaid' });
        })
        .catch(() => {});
    }
  </script>"""


def convert_tex_to_html(text):
    """Convert inline and block LaTeX math outside code blocks to offline-safe HTML."""
    placeholders = []

    def mask(match):
        placeholders.append(match.group(0))
        return f"@@CODEMASK_{len(placeholders) - 1}@@"

    masked = re.sub(r"(?:```|~~~).*?(?:```|~~~)", mask, text, flags=re.DOTALL)
    masked = re.sub(r"`[^`\n]+`", mask, masked)

    def render_expr(expr):
        expr = expr.strip()
        for _ in range(4):
            expr = re.sub(r"\\(?:text|mathbf|mathrm|mathit|operatorname)\{([^{}]*)\}", r"\1", expr)
            expr = re.sub(r"\\left\\lfloor", "⌊", expr)
            expr = re.sub(r"\\right\\rfloor", "⌋", expr)
            expr = re.sub(r"\\lfloor", "⌊", expr)
            expr = re.sub(r"\\rfloor", "⌋", expr)
            expr = re.sub(r"\\left\(", "(", expr)
            expr = re.sub(r"\\right\)", ")", expr)
        # Convert scripts before fraction replacement
        expr = re.sub(r"\^\{([^{}]+)\}", lambda m: f"<sup>{escape(m.group(1))}</sup>", expr)
        expr = re.sub(r"_\{([^{}]+)\}", lambda m: f"<sub>{escape(m.group(1))}</sub>", expr)
        expr = re.sub(r"\b([A-Za-z])_([A-Za-z0-9])\b", lambda m: f"{m.group(1)}<sub>{m.group(2)}</sub>", expr)
        expr = re.sub(r"(\d|[A-Za-z])\^(\d+)\b", lambda m: f"{m.group(1)}<sup>{m.group(2)}</sup>", expr)

        for _ in range(3):
            expr = re.sub(
                r"\\frac\{([^{}]*)\}\{([^{}]*)\}",
                lambda m: f"({m.group(1)}) / ({m.group(2)})",
                expr,
            )

        symbol_map = (
            (r"\times", "×"), (r"\cdot", "·"),
            (r"\rightarrow", "→"), (r"\to", "→"),
            (r"\leftrightarrow", "↔"), (r"\implies", "⇒"),
            (r"\approx", "≈"), (r"\sim", "~"),
            (r"\le", "≤"), (r"\ge", "≥"), (r"\neq", "≠"),
            (r"\pm", "±"), (r"\forall", "∀"), (r"\in", "∈"),
            (r"\sum", "Σ"), (r"\gg", "≫"), (r"\ll", "≪"),
            (r"\epsilon", "ε"), (r"\mu", "μ"), (r"\lambda", "λ"),
            (r"\alpha", "α"), (r"\beta", "β"), (r"\Delta", "Δ"),
            (r"\pmod", " mod "), (r"\quad", " "), (r"\dots", "…"),
            (r"\mid", "|"), (r"\#", "#"), (r"\%", "%"),
            (r"\_", "_"), (r"\{", "{"), (r"\}", "}"), (r"\,", " "), (r"\ ", " "),
        )
        for src, dst in symbol_map:
            expr = expr.replace(src, dst)
        expr = re.sub(r"\s+", " ", expr).strip()
        return expr

    # Escape literal dollar amounts first only conceptually; distinguish math vs currency:
    masked = re.sub(
        r"\$\$(.*?)\$\$",
        lambda m: f'\n<div class="math-block">{render_expr(m.group(1))}</div>\n',
        masked,
        flags=re.DOTALL,
    )

    def replace_inline(m):
        inner = m.group(1)
        has_math_sym = any(tok in inner for tok in ("\\", "^", "_", "=", "+", "×", "≈", "→", "<", ">", "/"))
        if not has_math_sym and (" " in inner or "costs" in inner or "from" in inner):
            return m.group(0)
        return f'<span class="math-inline">{render_expr(inner)}</span>'

    masked = re.sub(r"\$([^$\n]+)\$", replace_inline, masked)

    for idx, original in enumerate(placeholders):
        masked = masked.replace(f"@@CODEMASK_{idx}@@", original)
    return masked


def outline(start="", current=None):
    rows = []
    for index, lesson in enumerate(LESSONS, 1):
        selected = ' aria-current="page"' if lesson.id == current else ""
        rows.append(
            f'<li><a href="{start}{lesson.id}.html" data-lesson-link="{lesson.id}" '
            f'data-lesson-title="{escape(lesson.title)}"{selected}>'
            f'<span class="lesson-index" aria-hidden="true">{index:02}</span>'
            f'<span class="lesson-label">{escape(lesson.title)}</span>'
            '<span class="lesson-completed" data-lesson-status></span></a></li>'
        )
    return '<ol class="course-outline">\n' + "\n".join(rows) + "\n</ol>"


def progress_controls():
    return """<div class="save-tools" data-requires-progress hidden>
          <p role="status" data-save-status></p>
          <div class="file-tools">
            <button class="text-link" type="button" data-export>Export progress</button>
            <label class="file-label">
              <span>Import progress</span>
              <input type="file" accept=".json,application/json" data-import>
            </label>
          </div>
        </div>"""


def capstone_history(heading):
    return f"""<section class="capstone-history" data-capstone-history hidden>
      <{heading}>Capstone results</{heading}>
      <p data-capstone-scores></p>
      <div data-capstone-review>
        <p>Review these lessons</p>
        <ul data-capstone-review-list></ul>
      </div>
    </section>"""


def selected_content(lesson):
    lines = (ROOT / lesson.source).read_text(encoding="utf-8").splitlines()
    first = lines.index(lesson.heading)
    excerpt = []
    for line in lines[first + 1:]:
        if line.startswith("## "):
            break
        if line.startswith(("**Next lesson**", "**Next exercise**", "**Continue learning**",
                            "Use the existing [Python simulator]")) or line == "---":
            continue
        excerpt.append(line)
    if not any(line.strip() for line in excerpt):
        raise ValueError(f"Missing teaching content in {lesson.source}")
    return "\n".join(excerpt).strip()


def link_target(lesson, href):
    url = urlsplit(href)
    if url.scheme or url.netloc or not url.path:
        return href
    parent = PurePosixPath(lesson.source).parent
    target = normpath(str(parent / unquote(url.path)))
    if target in LOCAL_TARGETS and url.fragment in STORY_HEADINGS:
        return LOCAL_TARGETS[target]
    if target.startswith("../") or target.startswith("/"):
        raise ValueError(f"Link exits repository: {href} in {lesson.source}")
    if target in GUIDE_MAP:
        fragment = f"#{url.fragment}" if url.fragment else ""
        return f"../{GUIDE_MAP[target]}{fragment}"
    repo_path = f"{target}/README.md" if (ROOT / target).is_dir() else target
    if not (ROOT / repo_path).is_file():
        repo_path = target
    fragment = f"#{url.fragment}" if url.fragment else ""
    return f"{REPO}/blob/main/{quote(repo_path, safe='/')}{fragment}"


def diagram(lesson):
    stations, caption = DIAGRAMS[lesson.id]
    items = "".join(f"<li>{escape(station)}</li>" for station in stations)
    return (
        f'<figure class="lesson-map"><ol aria-label="Request path">{items}</ol>'
        f'<figcaption>{escape(caption)}</figcaption></figure>\n'
    )


def render_lesson_content(lesson):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = md.parse(convert_tex_to_html(selected_content(lesson)))
    for token in tokens:
        if token.type == "fence" and token.info.strip() == "mermaid":
            token.type = "html_block"
            token.content = diagram(lesson)
        if token.type in {"heading_open", "heading_close"} and token.tag == "h3":
            token.tag = "h2"
        if token.children:
            for child in token.children:
                if child.type == "link_open":
                    child.attrSet("href", link_target(lesson, child.attrGet("href")))
    return md.renderer.render(tokens, md.options, {})


def lesson_page(index, lesson):
    following = LESSONS[index + 1] if index + 1 < len(LESSONS) else None
    previous = LESSONS[index - 1] if index else None
    sections = []
    if lesson.id == "load-balancing":
        sections.append(
            '<details class="animation" id="routing-animation"><summary>Watch the routing animation</summary>'
            '<img src="../course/load-balancer.gif" loading="lazy" width="960" height="440" '
            'alt="Requests pass from the client through the balancer to servers 1 and 2. Server 3 is unavailable.">'
            '<p><a href="simulator.html">Try the capacity simulator</a></p></details>'
        )
    if lesson.id == "caching":
        sections.append('<p><a href="simulator.html">Test a cache outage in the traffic simulator</a></p>')
    if lesson.id == "dns":
        sections.append('<p><a href="dns-lab.html">Try the DNS cache lab</a></p>')
    if lesson.id == "queues":
        sections.append('<p><a href="queue-lab.html">Try the queue backlog simulator</a></p>')
        sections.append('<p><a href="../guides/order-processing-lab.html">Try the order-processing lab</a></p>')
    if lesson.id == "regional-recovery":
        sections.append('<p><a href="quorum-lab.html">Test quorum tolerance in the Quorum Lab</a></p>')
        sections.append('<p><a href="../guides/study-guide.html#timed-mock-interviews">Try a timed design interview</a></p>')
    folder = PurePosixPath(lesson.source).parent
    full_chapter = (f"../chapters/{folder}/index.html" if lesson.source.endswith("/README.md")
                    else "../guides/multi-region-recovery.html")
    sections.append(
        f'<p class="reference-link"><a href="{full_chapter}">Read the full technical chapter</a></p>'
    )
    return Template((COURSE / "lesson.html").read_text(encoding="utf-8")).substitute(
        navigation=site_navigation("../"),
        id=lesson.id,
        title=escape(lesson.title),
        description=escape(lesson.description),
        number=index + 1,
        total=len(LESSONS),
        content=render_lesson_content(lesson),
        resources="\n".join(sections),
        next_url=f"{following.id}.html" if following else "capstone.html",
        next_label="Next lesson" if following else "Take the capstone",
        previous=(f'<a class="previous-link" href="{previous.id}.html">Previous lesson</a>' if previous else ""),
        outline=outline(current=lesson.id),
        progress_controls=progress_controls(),
    )


def site_navigation(prefix="./", current=None):
    destinations = (
        ("lessons", f"{prefix}#lessons", "Lessons"),
        ("library", f"{prefix}library.html", "Library"),
        ("simulator", f"{prefix}learn/simulator.html", "Simulator"),
        ("flashcards", f"{prefix}flashcards.html", "Flashcards"),
    )
    links = []
    for key, href, title in destinations:
        active = ' aria-current="page"' if key == current else ""
        links.append(f'      <a href="{href}"{active}>{title}</a>')
    return '<nav aria-label="Main navigation">\n' + "\n".join(links) + "\n    </nav>"


def tool_page(title, description, prefix, script, content, current=None, before=(), extra_body=""):
    template = Template((COURSE / "tool.html").read_text(encoding="utf-8"))
    return template.substitute(
        title=escape(title),
        description=escape(description),
        prefix=prefix,
        scripts="\n".join(f'  <script src="{prefix}course/{item}" defer></script>'
                          for item in (*before, script) if item),
        navigation=site_navigation(prefix, current),
        content=content,
        extra_body=extra_body,
    )


def catalog_rows():
    source = (PAGES / "cards-data.js").read_text(encoding="utf-8")
    _, separator, payload = source.partition("window.SYSTEM_DESIGN_FLASHCARDS = ")
    if not separator:
        raise ValueError("Missing flashcard dataset")
    return json.loads(payload.strip().removesuffix(";"))


def library_page(rows):
    groups = {}
    labels = {}
    for row in rows:
        key = row["category_id"]
        labels[key] = row["category"]
        groups.setdefault(key, []).append(row)
    category_order = ("foundations", "networking", "storage", "caching",
                      "distributed", "async", "system_design")
    categories = sorted(groups, key=lambda key: category_order.index(key)
                        if key in category_order else len(category_order))
    sections = []
    for key in categories:
        items = []
        for row in groups[key]:
            folder = row["folder"]
            guided = LOCAL_TARGETS.get(folder)
            href = f"learn/{guided}" if guided else f"chapters/{folder}/index.html"
            badge = '<span class="catalog-kind">Guided lesson</span>' if guided else ""
            search = " ".join((row["number"], row["title"], row["category"], folder))
            items.append(
                f'<li data-topic-row data-search="{escape(search)}"><a href="{href}">'
                f'<span class="lesson-index" aria-hidden="true">{escape(row["number"])}</span>'
                f'<span>{escape(row["title"])}</span>{badge}</a></li>'
            )
        sections.append(
            f'<section class="catalog-group" data-topic-group="{escape(key)}">'
            f'<h2>{escape(labels[key])}</h2><ul>\n' + "\n".join(items) + "\n</ul></section>"
        )

    content = Template((COURSE / "library.html").read_text(encoding="utf-8")).substitute(
        total=len(rows),
        options="\n".join(f'<option value="{escape(key)}">{escape(labels[key])}</option>'
                          for key in categories),
        groups="\n".join(sections),
    )
    return tool_page("Topic library", "Search the system design curriculum by topic or category.",
                     "./", "library.js", content, "library")


def resolve_site_link(source_posix_path, href, folders, prefix):
    """Map relative repository markdown/URL links to rendered docs/ pages when possible."""
    url = urlsplit(href)
    if url.scheme or url.netloc or not url.path:
        return href
    parent = PurePosixPath(source_posix_path).parent
    joined = normpath(str(parent / unquote(url.path)))
    frag = f"#{url.fragment}" if url.fragment else ""

    if joined in GUIDE_MAP:
        return f"{prefix}{GUIDE_MAP[joined]}{frag}"

    target = PurePosixPath(joined)
    if str(target) in folders:
        target /= "README.md"
    names = {"README.md": "index.html", "REAL_WORLD_EXAMPLES.md": "examples.html"}
    if str(target.parent) in folders and target.name in names:
        return f"{prefix}chapters/{target.parent}/{names[target.name]}{frag}"

    # Fallback to GitHub for runnable Python files / assets not hosted natively as HTML
    repo_target = f"{joined}/README.md" if (ROOT / joined).is_dir() and (ROOT / joined / "README.md").is_file() else joined
    return f"{REPO}/blob/main/{quote(repo_target, safe='/')}{frag}"


def render_reader_article(source_posix_path, md_text, folders, prefix):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    processed = convert_tex_to_html(md_text)
    tokens = md.parse(processed)
    has_mermaid = False
    for index, token in enumerate(tokens):
        if token.type == "fence" and token.info.strip() == "mermaid":
            has_mermaid = True
            token.type = "html_block"
            token.content = f'<figure class="chapter-diagram"><pre class="mermaid">{escape(token.content.strip())}</pre></figure>\n'
            continue
        if token.type == "heading_open":
            slug = re.sub(r"[^\w -]", "", tokens[index + 1].content.lower()).strip().replace(" ", "-")
            token.attrSet("id", slug)
        for child in token.children or ():
            if child.type == "link_open":
                href = child.attrGet("href")
                child.attrSet("href", resolve_site_link(source_posix_path, href, folders, prefix))
            elif child.type == "image":
                # Keep relative ./assets/ images intact for chapters
                pass
    html_body = md.renderer.render(tokens, md.options, {})
    return html_body, has_mermaid


def chapter_outputs(rows):
    folders = {row["folder"] for row in rows}
    for row in rows:
        folder = row["folder"]
        destination = PAGES / "chapters" / folder
        for source in ("README.md", "REAL_WORLD_EXAMPLES.md"):
            rel_src = f"{folder}/{source}"
            raw_md = (ROOT / rel_src).read_text(encoding="utf-8")
            article, has_mermaid = render_reader_article(rel_src, raw_md, folders, "../../")

            actions = ['<a href="../../library.html">Back to topic library</a>']
            if source == "README.md":
                actions.append('<a href="examples.html">FAANG case studies</a>')
            else:
                actions.append('<a href="index.html">Back to chapter</a>')
            if folder in MODULE_LABS:
                lab_href, lab_label = MODULE_LABS[folder]
                actions.append(f'<a href="../../{lab_href}">{escape(lab_label)}</a>')
            actions.append('<a href="../../flashcards.html">Practice in Flashcards</a>')

            content = (
                '<main id="main" class="container chapter-reader">'
                f'<nav class="chapter-actions" aria-label="Chapter links">{" · ".join(actions)}</nav>'
                f"<article>{article}</article></main>"
            )
            filename = "index.html" if source == "README.md" else "examples.html"
            extra = MERMAID_PROGRESSIVE_SCRIPT if has_mermaid else ""
            yield destination / filename, tool_page(
                row["title"], row["title"], "../../", None, content, extra_body=extra,
            ).encode()
        for asset in sorted((ROOT / folder / "assets").glob("*")):
            if asset.is_file():
                yield destination / "assets" / asset.name, asset.read_bytes()


def guide_outputs(rows):
    folders = {row["folder"] for row in rows}
    for guide in GUIDES:
        raw_md = (ROOT / guide.source).read_text(encoding="utf-8")
        # Normalize local GitHub pages flashcards link when inside docs/
        article, has_mermaid = render_reader_article(guide.source, raw_md, folders, "../")
        actions = [
            '<a href="../library.html">Topic library</a>',
            '<a href="../">Trail Notes course</a>',
            '<a href="../flashcards.html">Flashcards</a>',
        ]
        if guide.slug in ("durable-key-value-store", "multi-region-recovery"):
            actions.append('<a href="../learn/quorum-lab.html">Quorum replication lab</a>')
        content = (
            '<main id="main" class="container chapter-reader">'
            f'<nav class="chapter-actions" aria-label="Guide links">{" · ".join(actions)}</nav>'
            f"<article>{article}</article></main>"
        )
        extra = MERMAID_PROGRESSIVE_SCRIPT if has_mermaid else ""
        yield PAGES / "guides" / f"{guide.slug}.html", tool_page(
            guide.title, guide.description, "../", None, content, extra_body=extra,
        ).encode()


def capstone_page():
    questions = json.loads((COURSE / "capstone.json").read_text(encoding="utf-8"))
    items = []
    for number, (lesson, item) in enumerate(zip(LESSONS, questions, strict=True), 1):
        correct = item["correct"]
        options = item["options"]
        if len(options) < 2 or not 0 <= correct < len(options):
            raise ValueError(f"Question {number} must have options and a valid answer")
        choices = []
        for index, option in enumerate(options):
            choices.append(
                f'<label><input type="radio" name="{lesson.id}" value="{index}" required>'
                f'<span>{escape(option)}</span></label>'
            )
        items.append(f'''
      <div class="capstone-question" data-question="{lesson.id}" data-correct="{correct}">
        <fieldset disabled>
          <legend><span class="question-number">Question {number}</span>{escape(item["prompt"])}</legend>
          <div class="answer-options">
            {"".join(choices)}
          </div>
        </fieldset>
        <p class="question-feedback" data-feedback hidden></p>
        <details>
          <summary>Reveal explanation</summary>
          <p><strong>{escape(options[correct])}.</strong> {escape(item["explanation"])}</p>
          <p><a href="{lesson.id}.html" data-lesson-link="{lesson.id}"
            data-lesson-title="{escape(lesson.title)}">Review the lesson</a></p>
        </details>
      </div>''')
    content = Template((COURSE / "capstone.html").read_text(encoding="utf-8")).substitute(
        questions="\n".join(items),
        capstone_history=capstone_history("h2"), progress_controls=progress_controls(),
    )
    return tool_page("Trail Notes capstone", "Practice six system design decisions and check your answers.",
                     "../", "capstone.js", content, before=("progress.js",))


def outputs():
    banner = "<!-- Generated by course/build.py. Edit the course templates or source lessons. -->\n"
    home = Template((COURSE / "home.html").read_text(encoding="utf-8")).substitute(
        navigation=site_navigation(), outline=outline("learn/"),
        capstone_history=capstone_history("h3"), progress_controls=progress_controls(),
    )
    yield PAGES / "index.html", (banner + home).encode()
    for index, lesson in enumerate(LESSONS):
        yield PAGES / "learn" / f"{lesson.id}.html", (banner + lesson_page(index, lesson)).encode()
    rows = catalog_rows()
    yield PAGES / "library.html", (banner + library_page(rows)).encode()
    yield from chapter_outputs(rows)
    yield from guide_outputs(rows)
    yield PAGES / "learn/capstone.html", (banner + capstone_page()).encode()

    labs = (
        ("simulator", "simulator.js", "Traffic simulator",
         "Change request volume and simulate server failures.", "simulator"),
        ("queue-lab", "queue-lab.js", "Queue backlog simulator",
         "Predict when a worker pool will clear a burst of photo jobs.", None),
        ("dns-lab", "dns-lab.js", "DNS cache lab",
         "Explore a DNS change and resolver cache expiry on an interactive timeline.", None),
        ("hashing-lab", "hashing-lab.js", "Consistent hashing ring lab",
         "Compare key movement and load skew across consistent hashing and modulo sharding.", None),
        ("quorum-lab", "quorum-lab.js", "Quorum replication lab",
         "Explore Dynamo-style N, W, R quorums and replica failures.", None),
    )
    for slug, script, title, desc, current_nav in labs:
        body = (COURSE / f"{slug}.html").read_text(encoding="utf-8").strip()
        yield PAGES / f"learn/{slug}.html", (banner + tool_page(
            title, desc, "../", script, body, current_nav,
        )).encode()

    source = ROOT / "03-load-balancing/assets/load_balancer.gif"
    yield PAGES / "course/load-balancer.gif", source.read_bytes()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files would change")
    args = parser.parse_args()
    stale = []
    for path, content in outputs():
        if args.check:
            current = path.read_bytes() if path.exists() else None
            if current is not None and path.suffix == ".html":
                current = current.replace(b"\r\n", b"\n")
            if current != content:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if stale:
        parser.exit(1, "Regenerate with python course/build.py: " + ", ".join(stale) + "\n")


if __name__ == "__main__":
    main()
