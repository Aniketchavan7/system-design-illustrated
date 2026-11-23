"""Render the Trail Notes course from the repository lessons."""
from argparse import ArgumentParser
from dataclasses import dataclass
from html import escape
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
    if url.scheme or url.netloc:
        return href
    if not url.path:
        return href
    parent = PurePosixPath(lesson.source).parent
    target = normpath(str(parent / unquote(url.path)))
    if target in LOCAL_TARGETS and url.fragment in STORY_HEADINGS:
        return LOCAL_TARGETS[target]
    if target.startswith("../") or target.startswith("/"):
        raise ValueError(f"Link exits repository: {href} in {lesson.source}")
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
    tokens = md.parse(selected_content(lesson))
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
    if lesson.id == "queues":
        sections.append(f'<p><a href="{REPO}/tree/main/labs/order-processing">Try the order-processing lab</a></p>')
    if lesson.id == "regional-recovery":
        sections.append(f'<p><a href="{REPO}/blob/main/STUDY_GUIDE.md#timed-mock-interviews">Try a timed design interview</a></p>')
    sections.append(
        f'<p class="reference-link"><a href="{REPO}/blob/main/{lesson.source}">Read the full technical chapter</a></p>'
    )
    return Template((COURSE / "lesson.html").read_text(encoding="utf-8")).substitute(
        id=lesson.id,
        title=escape(lesson.title),
        description=escape(lesson.description),
        number=index + 1,
        total=len(LESSONS),
        content=render_lesson_content(lesson),
        resources="\n".join(sections),
        next_url=f"{following.id}.html" if following else "../#lessons",
        next_label="Next lesson" if following else "Back to all lessons",
        previous=(f'<a class="previous-link" href="{previous.id}.html">Previous lesson</a>' if previous else ""),
        outline=outline(current=lesson.id),
        progress_controls=progress_controls(),
    )


def outputs():
    banner = "<!-- Generated by course/build.py. Edit the course templates or source lessons. -->\n"
    home = Template((COURSE / "home.html").read_text(encoding="utf-8")).substitute(
        outline=outline("learn/"), progress_controls=progress_controls(),
    )
    yield PAGES / "index.html", (banner + home).encode()
    for index, lesson in enumerate(LESSONS):
        yield PAGES / "learn" / f"{lesson.id}.html", (banner + lesson_page(index, lesson)).encode()
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
