"""Scan orchestrator — run all registered rules against pages."""
from __future__ import annotations
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from .fetcher import fetch
from .models import Level, PageReport, ScanReport
from .rules import all_rules
from .rules.base import RuleContext


class _RateLimiter:
    """Simple token-bucket: allow N requests per second across all workers."""
    def __init__(self, rps: float):
        self.interval = 1.0 / rps if rps > 0 else 0
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait_for = self._last + self.interval - now
            if wait_for > 0:
                time.sleep(wait_for)
                self._last = time.monotonic()
            else:
                self._last = now


def scan_page(
    url: str,
    *,
    level: Level = Level.AA,
    render: bool = False,
    freego_compat: bool = False,
    ignore: Iterable[str] = (),
    sources: set[str] | None = None,
    llm=None,
) -> PageReport:
    # When LLM has vision support, capture screenshots so vision rules can use them.
    capture_shots = bool(llm and render and llm.supports_vision())
    report, soup, html, full_png, vp_png = fetch(url, render=render, capture_screenshot=capture_shots)
    if soup is None:
        return report
    ctx = RuleContext(freego_compat=freego_compat, ignore=set(ignore), llm=llm,
                      full_screenshot=full_png, viewport_screenshot=vp_png)
    if level == Level.AAA:
        ctx.state["strict_aaa"] = True
    if render:
        try:
            from .tools.contrast import collect_text_samples
            from .tools.tab_walk import walk_tab_stops
            ctx.text_samples = collect_text_samples(url)
            ctx.tab_stops = walk_tab_stops(url)
            ctx.browser_used = True
        except Exception as e:
            ctx.state["browser_error"] = f"{type(e).__name__}: {e}"
    for rule in all_rules(level=level, sources=sources):
        rule.check(soup, report, html=html, url=url, ctx=ctx)
    return report


def scan_urls(
    urls: list[str],
    *,
    level: Level = Level.AA,
    render: bool = False,
    freego_compat: bool = False,
    ignore: Iterable[str] = (),
    workers: int = 4,
    progress: bool = False,
    delay: float = 0.0,
    rps: float = 0.0,
    sources: set[str] | None = None,
    llm=None,
) -> ScanReport:
    """Parallel scan of many URLs.

    delay: per-request sleep before each scan (seconds, applies even with workers=1).
    rps  : global cap on requests-per-second across all workers (0 = no limit).
    Browser scans serialised (Playwright is heavy).
    """
    out = ScanReport()
    limiter = _RateLimiter(rps) if rps > 0 else None

    def _one(u: str) -> PageReport:
        if limiter:
            limiter.wait()
        if delay > 0:
            time.sleep(delay)
        return scan_page(u, level=level, render=render,
                         freego_compat=freego_compat, ignore=ignore, sources=sources, llm=llm)

    if render:
        # Serial when rendering — Playwright contexts are RAM-hungry, parallelism risks OOM.
        for i, url in enumerate(urls, 1):
            if progress:
                print(f"[{i}/{len(urls)}] {url}", file=sys.stderr)
            try:
                out.add(_one(url))
            except Exception as e:
                out.add(PageReport(url=url, fetch_error=f"{type(e).__name__}: {e}"))
        return out

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_one, u): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            url = futures[fut]
            if progress:
                print(f"[{i}/{len(urls)}] {url}", file=sys.stderr)
            try:
                out.add(fut.result())
            except Exception as e:
                out.add(PageReport(url=url, fetch_error=f"{type(e).__name__}: {e}"))
    return out
