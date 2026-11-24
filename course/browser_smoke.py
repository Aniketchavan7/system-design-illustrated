"""Exercise the static course with a real browser and a project URL prefix."""
from argparse import ArgumentParser
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parent.parent
MOBILE = {"width": 390, "height": 844}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


@contextmanager
def local_site():
    handler = partial(QuietHandler, directory=str(ROOT))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/docs/"
        finally:
            server.shutdown()
            thread.join()


def open_page(page, url):
    response = page.goto(url, wait_until="domcontentloaded")
    assert response and response.ok, url
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), url


def complete_lesson(page):
    page.get_by_role("button", name="Mark complete", exact=True).click()
    expect(page.get_by_role("status")).to_have_text("Lesson complete. Saved on this browser.")
    expect(page.get_by_role("button", name="Lesson complete", exact=True)).to_be_disabled()


def test_resume(browser_type, base_url, launch, backup):
    with TemporaryDirectory() as profile:
        context = browser_type.launch_persistent_context(profile, viewport=MOBILE, **launch)
        page = context.pages[0]
        open_page(page, base_url)
        page.get_by_role("link", name="Start learning").click()
        expect(page.get_by_role("heading", name="Ask for a page")).to_be_visible()
        page.get_by_text("Reveal the answer", exact=True).click()
        expect(page.get_by_text("70 ms", exact=True)).to_be_visible()
        complete_lesson(page)
        context.close()

        context = browser_type.launch_persistent_context(profile, viewport=MOBILE, **launch)
        page = context.pages[0]
        open_page(page, base_url)
        expect(page.get_by_text("1 of 6 lessons complete")).to_be_visible()
        page.get_by_role("link", name="Continue learning").click()
        expect(page.get_by_role("heading", name="Find the website’s address")).to_be_visible()
        complete_lesson(page)
        do_remaining_lessons(page)
        open_page(page, base_url)
        expect(page.get_by_text("6 of 6 lessons complete")).to_be_visible()
        expect(page.locator("[data-resume]")).to_have_text("Take the capstone")
        with page.expect_download() as download:
            page.get_by_role("button", name="Export progress").click()
        download.value.save_as(backup)
        context.close()


def do_remaining_lessons(page):
    for title in ("Keep the site online", "Cache popular guides",
                  "Queue photo previews", "Recover from a regional outage"):
        page.get_by_role("link", name="Next lesson", exact=True).click()
        expect(page.get_by_role("heading", name=title, level=1)).to_be_visible()
        if title == "Keep the site online":
            page.get_by_text("Reveal the walkthrough", exact=True).click()
            expect(page.get_by_text("1,800 requests per second", exact=True)).to_be_visible()
        complete_lesson(page)


def test_import_and_simulator(browser, base_url, backup):
    page = browser.new_page(viewport=MOBILE)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_page(page, base_url)
    page.get_by_label("Import progress").set_input_files(
        {"name": "invalid.json", "mimeType": "application/json", "buffer": b"{}"}
    )
    expect(page.get_by_role("status")).to_contain_text("Could not read")
    expect(page.get_by_text("0 of 6 lessons complete")).to_be_visible()
    page.get_by_role("link", name="Start learning").click()
    complete_lesson(page)
    open_page(page, base_url)
    page.get_by_label("Import progress").set_input_files({
        "name": "partial.json",
        "mimeType": "application/json",
        "buffer": b'{"version":1,"completed":["dns"],"lastLesson":"load-balancing"}',
    })
    expect(page.get_by_text("2 of 6 lessons complete")).to_be_visible()
    page.get_by_label("Import progress").set_input_files(backup)
    expect(page.get_by_role("status")).to_contain_text("Progress imported")
    expect(page.get_by_text("6 of 6 lessons complete")).to_be_visible()
    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_text("6 of 6 lessons complete")).to_be_visible()

    page.get_by_role("link", name="Simulator", exact=True).click()
    page.get_by_role("button", name="Fail one server").click()
    expect(page.locator("[data-capacity]")).to_have_text("1,800")
    expect(page.locator("[data-shortfall]")).to_have_text("200")
    hit_rate = page.get_by_role("slider", name="Cache hit rate")
    for _ in range(35):
        hit_rate.press("ArrowRight")
    expect(page.locator("[data-hits]")).to_have_text("1,400")
    expect(page.locator("[data-origin]")).to_have_text("600")
    expect(page.locator("[data-served]")).to_have_text("2,000")
    outage = page.get_by_role("checkbox", name="Cache outage", exact=False)
    outage.check()
    expect(page.locator("[data-shortfall]")).to_have_text("200")
    expect(hit_rate).to_be_disabled()
    outage.uncheck()
    expect(hit_rate).to_have_value("70")
    expect(page.locator("[data-shortfall]")).to_have_text("0")
    hit_rate.press("End")
    page.get_by_role("slider", name="Failed servers").press("End")
    expect(page.locator("[data-served]")).to_have_text("2,000")
    hit_rate.press("Home")
    expect(page.locator("[data-healthy]")).to_have_text("0")
    expect(page.locator("[data-shortfall]")).to_have_text("2,000")
    page.get_by_role("slider", name="Total servers").press("Home")
    expect(page.get_by_role("slider", name="Failed servers")).to_have_value("1")
    page.get_by_role("button", name="Restore all servers").click()
    expect(page.locator("[data-capacity]")).to_have_text("900")
    page.get_by_role("slider", name="Incoming requests per second").press("Home")
    expect(page.locator("[data-shortfall]")).to_have_text("0")
    page.get_by_role("link", name="Flashcards", exact=True).click()
    expect(page.locator("#search-input")).to_be_visible()
    assert not errors, errors
    page.close()


def test_library(browser, base_url):
    page = browser.new_page(viewport=MOBILE)
    open_page(page, base_url + "library.html?q=client%20server&topic=networking")
    expect(page.get_by_role("status")).to_have_text("1 of 45 topics")
    guided = page.locator("[data-topic-row]:visible a")
    expect(guided).to_have_attribute("href", "learn/networking.html")

    page.get_by_label("Category").select_option("storage")
    expect(page.get_by_role("status")).to_have_text("0 of 45 topics")
    expect(page.get_by_text("No topics match", exact=False)).to_be_visible()
    page.get_by_role("button", name="Clear filters").click()
    expect(page.get_by_role("status")).to_have_text("45 of 45 topics")

    page.get_by_role("searchbox", name="Search topics").fill("idempotency")
    expect(page.get_by_role("status")).to_have_text("1 of 45 topics")
    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_role("searchbox", name="Search topics")).to_have_value("idempotency")
    expect(page.locator("[data-topic-row]:visible a")).to_have_attribute(
        "href",
        "chapters/32-rest-api-design-and-idempotency/index.html",
    )
    page.locator("[data-topic-row]:visible a").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Idempotency")
    page.get_by_role("link", name="Back to topic library").click()
    expect(page.get_by_role("heading", name="Topic library")).to_be_visible()
    page.close()


def test_capstone(browser, base_url, backup):
    page = browser.new_page(viewport=MOBILE)
    open_page(page, base_url + "learn/regional-recovery.html")
    page.get_by_role("link", name="Take the capstone", exact=True).click()
    expect(page.get_by_role("heading", name="Trail Notes capstone")).to_be_visible()
    questions = page.locator("[data-question]")
    expect(questions).to_have_count(6)
    page.get_by_role("button", name="Check answers").click()
    expect(page.locator("[data-capstone-result]")).to_be_hidden()

    for index, answer in enumerate((1, 2, 1, 1, 2, 0)):
        questions.nth(index).get_by_role("radio").nth(answer).check()
    page.get_by_role("button", name="Check answers").click()
    expect(page.locator("[data-capstone-result]")).to_contain_text("5 of 6 correct")
    expect(questions.nth(2).locator("[data-feedback]")).to_have_text("Review this question")
    expect(questions.nth(2).get_by_text("250 requests per second.", exact=True)).to_be_visible()
    expect(questions.nth(2).get_by_role("link", name="Review the lesson")).to_have_attribute(
        "href", "load-balancing.html",
    )

    expect(page.locator("[data-save-status]")).to_have_text("Capstone result saved on this browser.")
    expect(page.locator("[data-capstone-scores]")).to_have_text("Latest: 5 of 6. Best: 5 of 6.")
    expect(page.locator("[data-capstone-review]")).to_contain_text("Keep the site online")

    questions.nth(2).get_by_role("radio").first.check()
    expect(page.locator("[data-capstone-result]")).to_be_hidden()
    page.get_by_role("button", name="Check answers").click()
    expect(page.locator("[data-capstone-result]")).to_contain_text("6 of 6 correct")
    expect(page.locator("[data-capstone-review]")).to_be_hidden()
    page.get_by_role("button", name="Try again").click()
    expect(page.locator("input:checked")).to_have_count(0)
    expect(page.locator("[data-capstone-result]")).to_be_hidden()

    for index, answer in enumerate((0, 0, 0, 1, 2, 0)):
        questions.nth(index).get_by_role("radio").nth(answer).check()
    page.get_by_role("button", name="Check answers").click()
    expected_scores = "Latest: 4 of 6. Best: 6 of 6."
    expect(page.locator("[data-capstone-scores]")).to_have_text(expected_scores)
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("[data-capstone-scores]")).to_have_text(expected_scores)
    with page.expect_download() as download:
        page.get_by_role("button", name="Export progress").click()
    download.value.save_as(backup)
    page.close()

    fresh = browser.new_page(viewport=MOBILE)
    open_page(fresh, base_url)
    expect(fresh.locator("[data-capstone-history]")).to_be_hidden()
    fresh.get_by_label("Import progress").set_input_files(backup)
    expect(fresh.locator("[data-capstone-scores]")).to_have_text(expected_scores)
    fresh.get_by_label("Import progress").set_input_files({
        "name": "older.json",
        "mimeType": "application/json",
        "buffer": b'{"version":1,"completed":[],"lastLesson":null,'
                  b'"capstone":{"best":5,"missed":["queues"],"attemptedAt":1}}',
    })
    expect(fresh.locator("[data-save-status]")).to_contain_text("Progress imported")
    expect(fresh.locator("[data-capstone-scores]")).to_have_text(expected_scores)
    links = fresh.locator("[data-capstone-review-list] a")
    expect(links).to_have_text(["Ask for a page", "Find the website’s address"])
    links.nth(1).click()
    expect(fresh.get_by_role("heading", name="Find the website’s address")).to_be_visible()
    fresh.close()


def test_queue_lab(browser, base_url):
    page = browser.new_page(viewport=MOBILE)
    open_page(page, base_url + "learn/queues.html")
    page.get_by_role("link", name="Try the queue backlog simulator").click()
    expect(page.locator("#pending")).to_have_text("800")
    expect(page.locator("#recovery")).to_contain_text("40 seconds")
    after = page.locator("#after")
    after.press("ArrowRight")
    after.press("ArrowRight")
    expect(page.locator("#recovery")).to_contain_text("stays at 800")
    after.press("ArrowRight")
    expect(page.locator("#recovery")).to_contain_text("grows by 10")
    page.locator("#duration").press("Home")
    expect(page.locator("#pending")).to_have_text("0")
    after.press("Home")
    expect(page.locator("#recovery")).to_contain_text("stays empty")
    page.close()


def test_dns_lab(browser, base_url):
    page = browser.new_page(viewport=MOBILE)
    open_page(page, base_url + "learn/dns.html")
    page.get_by_role("link", name="Try the DNS cache lab").click()
    expect(page.get_by_role("heading", name="When does DNS catch up?")).to_be_visible()
    time = page.locator("#dns-time")
    first = page.locator('[data-dns-address="a"]')
    second = page.locator('[data-dns-address="b"]')
    expect(time).to_have_value("30")
    expect(first).to_have_text("192.0.2.10")
    expect(second).to_have_text("192.0.2.10")

    page.get_by_role("button", name="Address changes").click()
    expect(time).to_have_value("15")
    expect(page.locator("[data-dns-authority]")).to_have_text("192.0.2.20")
    page.get_by_role("button", name="Resolver A expires").click()
    expect(time).to_have_value("60")
    expect(first).to_have_text("192.0.2.20")
    expect(second).to_have_text("192.0.2.10")
    page.get_by_role("button", name="Resolver B expires").click()
    expect(time).to_have_value("70")
    expect(second).to_have_text("192.0.2.20")

    page.locator("#dns-ttl").press("ArrowRight")
    page.get_by_role("button", name="Resolver A expires").click()
    expect(time).to_have_value("75")
    expect(second).to_have_text("192.0.2.10")
    time.press("Home")
    expect(page.locator('[data-dns-detail="b"]')).to_have_text("First lookup has not happened")
    page.close()


def test_storage_denied(browser, base_url):
    context = browser.new_context(viewport=MOBILE)
    context.add_init_script(
        "Storage.prototype.setItem = () => { throw new Error('Storage is blocked'); };"
    )
    page = context.new_page()
    open_page(page, base_url + "learn/networking.html")
    expect(page.get_by_role("status")).to_contain_text("Could not save on this browser")
    page.get_by_role("button", name="Mark complete", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Export your progress")
    expect(page.get_by_role("button", name="Export progress")).to_be_visible()
    context.close()


def test_no_script(browser, base_url):
    page = browser.new_page(java_script_enabled=False, viewport=MOBILE, reduced_motion="reduce")
    open_page(page, base_url)
    page.get_by_role("link", name="Start learning").click()
    page.get_by_text("Reveal the answer", exact=True).click()
    expect(page.get_by_text("70 ms", exact=True)).to_be_visible()
    page.get_by_role("link", name="Next lesson", exact=True).click()
    expect(page.get_by_role("heading", name="Find the website’s address")).to_be_visible()
    open_page(page, base_url + "library.html")
    expect(page.locator("[data-topic-row]:visible")).to_have_count(45)
    open_page(page, base_url + "learn/capstone.html")
    expect(page.get_by_role("button", name="Check answers")).to_be_hidden()
    page.get_by_text("Reveal explanation", exact=True).first.click()
    expect(page.get_by_text("75 ms.", exact=True)).to_be_visible()
    open_page(page, base_url + "learn/dns-lab.html")
    expect(page.locator("#dns-time")).to_be_disabled()
    page.get_by_text("Reveal the worked example", exact=True).click()
    expect(page.get_by_text("Resolver A’s old answer expired", exact=False)).to_be_visible()
    page.close()


def run(base_url, chrome):
    launch = {"executable_path": chrome} if chrome else {}
    with sync_playwright() as playwright, TemporaryDirectory() as directory:
        chromium = playwright.chromium
        backup = Path(directory) / "progress.json"
        test_resume(chromium, base_url, launch, backup)
        browser = chromium.launch(**launch)
        try:
            test_import_and_simulator(browser, base_url, backup)
            test_storage_denied(browser, base_url)
            test_no_script(browser, base_url)
            test_library(browser, base_url)
            test_capstone(browser, base_url, Path(directory) / "capstone.json")
            test_queue_lab(browser, base_url)
            test_dns_lab(browser, base_url)
        finally:
            browser.close()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", help="Path to an installed Chromium or Chrome executable")
    parser.add_argument("--url", help="Optional published or preview course base URL")
    args = parser.parse_args()
    if args.url:
        run(args.url.rstrip("/") + "/", args.chrome)
    else:
        with local_site() as base_url:
            run(base_url, args.chrome)
    print("Verified six lessons, browser restart, progress transfer, blocked storage, capacity and DNS labs, flashcards, library, and capstone review.")
