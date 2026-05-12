"""HTTP fetch + parse. Static httpx by default; Playwright when --render given.

`file://` URLs are allowed when `--allow-file` (CLI) or `A11Y_ALLOW_FILE=1`
(env) is set — used to audit local build output without spinning up a
dev server. The static path reads from disk via Path; the rendered path
hands the URL to Playwright which natively handles `file://`.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from bs4 import BeautifulSoup
import httpx

from .models import PageReport
from ._security import require_safe_http_url, UnsafeURLError


from . import USER_AGENT as _DEFAULT_UA


def ensure_playwright_or_die(reason: str = "this command") -> None:
    """Verify playwright is importable. Exit with friendly install message if not.

    Used by CLI when a render-requiring path is selected (--render / --render-crawl)
    so users see a single clear install instruction rather than N per-page
    `fetch_error: playwright not installed` lines.
    """
    try:
        import playwright  # noqa: F401
    except ImportError:
        import sys
        sys.stderr.write(
            f"\nERROR: {reason} needs Playwright + Chromium (not installed).\n\n"
            "Since v0.3.0, Playwright is an optional dependency to keep the\n"
            "default install lightweight (lint command needs none of it).\n\n"
            "Install (one-time, ~290MB):\n"
            "    pip install 'a11y-moda[scan]'\n"
            "    playwright install chromium\n\n"
            "Or skip rendering (some checks won't run):\n"
            "    a11y-moda scan <URL>          (no --render)\n"
            "    a11y-moda site <URL>          (no --render / --render-crawl)\n"
            "    a11y-moda lint <PATH>         (source-level, no browser ever)\n"
        )
        sys.exit(2)


def _read_local_file(url: str) -> tuple[int, str, str]:
    """Read a file:// URL from disk. Returns (status_code, html, error).

    status_code: 200 on success, 404 on missing, 0 on read error.
    """
    p_url = urlparse(url)
    # url2pathname handles the Windows drive-letter case correctly:
    #   file:///D:/x/y.html  → D:\x\y.html
    #   file:///home/u/x.html → /home/u/x.html
    fs_path = Path(url2pathname(p_url.path))
    if not fs_path.exists():
        return 0, "", f"file not found: {fs_path}"
    if not fs_path.is_file():
        return 0, "", f"not a file (is it a directory?): {fs_path}"
    try:
        return 200, fs_path.read_text(encoding="utf-8", errors="replace"), ""
    except Exception as e:
        return 0, "", f"{type(e).__name__}: {e}"


def fetch_static(url: str, *, timeout: float = 30.0, ua: str = _DEFAULT_UA) -> tuple[PageReport, BeautifulSoup | None, str]:
    report = PageReport(url=url)
    try:
        require_safe_http_url(url)
    except UnsafeURLError as e:
        report.fetch_error = str(e)
        return report, None, ""
    if url.startswith("file://"):
        status, html, err = _read_local_file(url)
        if err:
            report.fetch_error = err
            return report, None, ""
        report.status_code = status
        soup = BeautifulSoup(html, "lxml")
        return report, soup, html
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": ua}) as cli:
            r = cli.get(url)
        # Re-validate after redirects — server may bounce us at internal hosts.
        try:
            require_safe_http_url(str(r.url))
        except UnsafeURLError as e:
            report.fetch_error = f"redirect to unsafe URL: {e}"
            return report, None, ""
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


def fetch_with_page(page, url: str, *, timeout_ms: int = 30000,
                     wait_until: str = "domcontentloaded", capture_screenshot: bool = False
                     ) -> tuple[PageReport, BeautifulSoup | None, str, bytes | None, bytes | None]:
    """Navigate an already-created Playwright page to URL; capture html + optional screenshots."""
    report = PageReport(url=url)
    try:
        require_safe_http_url(url)
    except UnsafeURLError as e:
        report.fetch_error = str(e)
        return report, None, "", None, None
    full_png: bytes | None = None
    viewport_png: bytes | None = None
    try:
        resp = page.goto(url, timeout=timeout_ms, wait_until=wait_until)
        # Playwright may have followed redirects to file:// or a private host.
        try:
            require_safe_http_url(page.url)
        except UnsafeURLError as e:
            report.fetch_error = f"redirect to unsafe URL: {e}"
            return report, None, "", None, None
        report.status_code = resp.status if resp else 0
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        html = page.content()
        if capture_screenshot:
            viewport_png = page.screenshot(full_page=False, type="png")
            full_png = page.screenshot(full_page=True, type="png")
        soup = BeautifulSoup(html, "lxml")
        return report, soup, html, full_png, viewport_png
    except Exception as e:
        report.fetch_error = f"{type(e).__name__}: {e}"
        return report, None, "", None, None


def fetch_rendered(url: str, *, timeout_ms: int = 30000, ua: str = _DEFAULT_UA,
                    wait_until: str = "domcontentloaded", capture_screenshot: bool = False,
                    color_scheme: str | None = None
                    ) -> tuple[PageReport, BeautifulSoup | None, str, bytes | None, bytes | None]:
    """Standalone: open own browser, navigate, capture. Used when no shared session."""
    report = PageReport(url=url)
    try:
        from .tools._session import standalone_page
    except ImportError:
        report.fetch_error = (
            "playwright not installed — install: "
            "pip install 'a11y-moda[scan]' && playwright install chromium"
        )
        return report, None, "", None, None
    try:
        with standalone_page(ua=ua, color_scheme=color_scheme) as page:
            return fetch_with_page(page, url, timeout_ms=timeout_ms,
                                    wait_until=wait_until, capture_screenshot=capture_screenshot)
    except Exception as e:
        report.fetch_error = f"{type(e).__name__}: {e}"
        return report, None, "", None, None


def fetch(url: str, *, render: bool = False, timeout: float = 30.0, ua: str = _DEFAULT_UA,
          capture_screenshot: bool = False, color_scheme: str | None = None
          ) -> tuple[PageReport, BeautifulSoup | None, str, bytes | None, bytes | None]:
    """Returns (report, soup, html, full_png, viewport_png). PNGs only when render+capture."""
    if render:
        return fetch_rendered(url, timeout_ms=int(timeout * 1000), ua=ua,
                              capture_screenshot=capture_screenshot,
                              color_scheme=color_scheme)
    report, soup, html = fetch_static(url, timeout=timeout, ua=ua)
    return report, soup, html, None, None
