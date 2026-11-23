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
        expect(page.get_by_role("link", name="Practice failures")).to_be_visible()
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

    page.get_by_role("link", name="Practice failures").click()
    page.get_by_role("button", name="Fail one server").click()
    expect(page.locator("[data-capacity]")).to_have_text("1,800")
    expect(page.locator("[data-shortfall]")).to_have_text("200")
    page.get_by_role("slider", name="Failed servers").press("End")
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
    print("Verified six lessons, browser restart, progress transfer, blocked storage, simulator, and flashcards.")
