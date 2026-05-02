"""Scan orchestrator — run all registered rules against pages."""
from __future__ import annotations
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from .fetcher import fetch, fetch_with_page
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


def _run_rules(rules, soup, report, *, html, url, ctx, llm_workers: int = 1) -> None:
    """Run rules on a page. Non-LLM rules go first sequentially (some share
    ctx.state across rules); LLM rules then fan out to a thread pool when
    llm_workers > 1 (LLM calls are I/O bound).
    """
    non_llm = [r for r in rules if not getattr(r, "uses_llm", False)]
    llm_rules = [r for r in rules if getattr(r, "uses_llm", False)]
    for r in non_llm:
        r.check(soup, report, html=html, url=url, ctx=ctx)
    if llm_workers > 1 and llm_rules:
        with ThreadPoolExecutor(max_workers=llm_workers) as ex:
            list(ex.map(lambda r: r.check(soup, report, html=html, url=url, ctx=ctx), llm_rules))
    else:
        for r in llm_rules:
            r.check(soup, report, html=html, url=url, ctx=ctx)


def scan_page(
    url: str,
    *,
    level: Level = Level.AA,
    render: bool = False,
    freego_compat: bool = False,
    ignore: Iterable[str] = (),
    sources: set[str] | None = None,
    llm=None,
    browser=None,
    llm_workers: int = 1,
    probe_modals: bool = False,
) -> PageReport:
    """Scan one URL.

    When `browser` is given (a Playwright Browser), open a fresh context+page
    from it and reuse that page for fetch + all probes — saves repeated
    chromium spawns and goto/networkidle waits across the 4 distinct sessions
    the standalone path uses.

    llm_workers controls per-page LLM rule concurrency (1 = serial; default).
    Set higher when the LLM endpoint can serve concurrent requests.
    """
    capture_shots = bool(llm and render and llm.supports_vision())
    if render and browser is not None:
        return _scan_page_with_browser(url, browser=browser, level=level,
                                        freego_compat=freego_compat, ignore=ignore,
                                        sources=sources, llm=llm, capture_shots=capture_shots,
                                        llm_workers=llm_workers, probe_modals=probe_modals)
    # Standalone path — used for static scans and single-URL render scans.
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
            from .tools.form_probe import probe_forms
            ctx.text_samples = collect_text_samples(url)
            ctx.tab_stops = walk_tab_stops(url)
            ctx.form_sims = probe_forms(url, try_modal_triggers=probe_modals)
            ctx.browser_used = True
        except Exception as e:
            ctx.state["browser_error"] = f"{type(e).__name__}: {e}"
    _run_rules(list(all_rules(level=level, sources=sources)), soup, report,
                html=html, url=url, ctx=ctx, llm_workers=llm_workers)
    return report


def _scan_page_with_browser(url, *, browser, level, freego_compat, ignore, sources, llm, capture_shots, llm_workers: int = 1, probe_modals: bool = False) -> PageReport:
    """Render path using a shared browser. Fresh context per URL (incognito
    isolation), shared page across fetch + 3 probes (contrast/tab_walk/form).
    Form probe runs LAST because it mutates page state (clicks modal triggers).
    """
    from .tools._session import page_session
    from .tools.contrast import collect_text_samples_from_page
    from .tools.tab_walk import walk_tab_stops_from_page
    from .tools.form_probe import probe_forms_from_page
    with page_session(browser) as page:
        report, soup, html, full_png, vp_png = fetch_with_page(
            page, url, capture_screenshot=capture_shots,
        )
        if soup is None:
            return report
        ctx = RuleContext(freego_compat=freego_compat, ignore=set(ignore), llm=llm,
                          full_screenshot=full_png, viewport_screenshot=vp_png)
        if level == Level.AAA:
            ctx.state["strict_aaa"] = True
        try:
            ctx.text_samples = collect_text_samples_from_page(page)
            ctx.tab_stops = walk_tab_stops_from_page(page)
            ctx.form_sims = probe_forms_from_page(page, url, try_modal_triggers=probe_modals)
            ctx.browser_used = True
        except Exception as e:
            ctx.state["browser_error"] = f"{type(e).__name__}: {e}"
        _run_rules(list(all_rules(level=level, sources=sources)), soup, report,
                    html=html, url=url, ctx=ctx, llm_workers=llm_workers)
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
    llm_workers: int = 1,
    probe_modals: bool = False,
) -> ScanReport:
    """Parallel scan of many URLs.

    delay: per-request sleep before each scan (seconds, applies even with workers=1).
    rps  : global cap on requests-per-second across all workers (0 = no limit).
    Browser scans serialised (Playwright is heavy).
    """
    out = ScanReport()
    limiter = _RateLimiter(rps) if rps > 0 else None

    def _one(u: str, browser=None) -> PageReport:
        if limiter:
            limiter.wait()
        if delay > 0:
            time.sleep(delay)
        return scan_page(u, level=level, render=render,
                         freego_compat=freego_compat, ignore=ignore, sources=sources,
                         llm=llm, browser=browser, llm_workers=llm_workers,
                         probe_modals=probe_modals)

    if render:
        # Serial when rendering. Share one chromium across the whole site;
        # each URL still gets a fresh incognito context for clean isolation.
        from .tools._session import shared_browser
        with shared_browser() as browser:
            for i, url in enumerate(urls, 1):
                if progress:
                    print(f"[{i}/{len(urls)}] {url}", file=sys.stderr)
                try:
                    out.add(_one(url, browser=browser))
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
