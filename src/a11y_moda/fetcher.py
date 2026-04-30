"""HTTP fetch + parse. Static httpx by default; Playwright when --render given."""
from __future__ import annotations
from bs4 import BeautifulSoup
import httpx

from .models import PageReport


_DEFAULT_UA = "Mozilla/5.0 (compatible; a11y-moda/0.1; +https://github.com/)"


def fetch_static(url: str, *, timeout: float = 30.0, ua: str = _DEFAULT_UA) -> tuple[PageReport, BeautifulSoup | None, str]:
    report = PageReport(url=url)
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": ua}) as cli:
            r = cli.get(url)
        report.status_code = r.status_code
        if r.status_code >= 400:
            report.fetch_error = f"HTTP {r.status_code}"
            return report, None, ""
        html = r.text
        soup = BeautifulSoup(html, "lxml")
        return report, soup, html
    except Exception as e:
        report.fetch_error = f"{type(e).__name__}: {e}"
        return report, None, ""


def fetch_rendered(url: str, *, timeout_ms: int = 30000, ua: str = _DEFAULT_UA,
                    wait_until: str = "domcontentloaded", capture_screenshot: bool = False
                    ) -> tuple[PageReport, BeautifulSoup | None, str, bytes | None, bytes | None]:
    """Fetch via headless Chromium; needed for SPA / JS-rendered pages.

    Returns (report, soup, html, full_screenshot_png, viewport_screenshot_png).
    Screenshot bytes are None unless capture_screenshot=True.
    """
    report = PageReport(url=url)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        report.fetch_error = "playwright not installed (pip install playwright && playwright install chromium)"
        return report, None, "", None, None
    full_png: bytes | None = None
    viewport_png: bytes | None = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 800})
            page = ctx.new_page()
            resp = page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            report.status_code = resp.status if resp else 0
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # tracker-heavy sites never reach idle; proceed with what we have
            html = page.content()
            if capture_screenshot:
                viewport_png = page.screenshot(full_page=False, type="png")
                full_png = page.screenshot(full_page=True, type="png")
            browser.close()
        soup = BeautifulSoup(html, "lxml")
        return report, soup, html, full_png, viewport_png
    except Exception as e:
        report.fetch_error = f"{type(e).__name__}: {e}"
        return report, None, "", None, None


def fetch(url: str, *, render: bool = False, timeout: float = 30.0, ua: str = _DEFAULT_UA,
          capture_screenshot: bool = False) -> tuple[PageReport, BeautifulSoup | None, str, bytes | None, bytes | None]:
    """Returns (report, soup, html, full_png, viewport_png). PNGs only when render+capture."""
    if render:
        return fetch_rendered(url, timeout_ms=int(timeout * 1000), ua=ua,
                              capture_screenshot=capture_screenshot)
    report, soup, html = fetch_static(url, timeout=timeout, ua=ua)
    return report, soup, html, None, None
