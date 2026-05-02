"""Shared Playwright browser session for site scans.

A single chromium process serves the whole site; each URL gets a fresh
browser context (= incognito profile) so cookies/storage/SPA state never
leak between pages. Within one URL all probes share the same page so
goto + networkidle waits aren't paid 4 times.
"""
from __future__ import annotations
from contextlib import contextmanager


from .. import USER_AGENT as _DEFAULT_UA


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
def page_session(browser, *, ua: str = _DEFAULT_UA, viewport: dict | None = None):
    """Open a fresh context+page for one URL; cleans up on exit."""
    ctx = browser.new_context(user_agent=ua, viewport=viewport or {"width": 1280, "height": 800})
    page = ctx.new_page()
    try:
        yield page
    finally:
        try:
            ctx.close()
        except Exception:
            pass
