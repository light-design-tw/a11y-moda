"""Shared Playwright browser session for site scans.

A single chromium process serves the whole site; each URL gets a fresh
browser context (= incognito profile) so cookies/storage/SPA state never
leak between pages. Within one URL all probes share the same page so
goto + networkidle waits aren't paid 4 times.
"""
from __future__ import annotations
from contextlib import contextmanager


from .. import USER_AGENT as _DEFAULT_UA

_DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
# Page-wide ceiling so a hung evaluate / Tab-press / locator action can't
# block the whole site scan. Individual goto calls override with longer values.
_DEFAULT_PAGE_TIMEOUT_MS = 15000


@contextmanager
def shared_browser():
    """Launch chromium once for the lifetime of the with-block."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            try:
                browser.close()
            except Exception:
                pass


@contextmanager
def page_session(browser, *, ua: str | None = None, viewport: dict | None = None):
    """Open a fresh context+page for one URL; cleans up on exit."""
    ctx = browser.new_context(user_agent=ua or _DEFAULT_UA, viewport=viewport or _DEFAULT_VIEWPORT)
    page = ctx.new_page()
    page.set_default_timeout(_DEFAULT_PAGE_TIMEOUT_MS)
    try:
        yield page
    finally:
        try:
            ctx.close()
        except Exception:
            pass


@contextmanager
def standalone_page(*, ua: str | None = None, viewport: dict | None = None):
    """One-shot browser+context+page for callers without a shared session.

    Used by `fetch_rendered` and the `*_url` probe wrappers — anywhere the
    caller does not already hold a Browser. Cleans both layers on exit.
    """
    with shared_browser() as browser:
        with page_session(browser, ua=ua, viewport=viewport) as page:
            yield page
