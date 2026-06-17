"""Reflow probe via Playwright — checks 320px CSS-width reflow (WCAG 1.4.10).

At 320 CSS px width a vertically-scrolling page should reflow without
requiring horizontal (two-dimensional) scrolling. We resize the viewport to
320px wide and compare ``documentElement.scrollWidth`` against ``clientWidth``
— a meaningful excess means horizontal scroll is required.
"""
from __future__ import annotations
from dataclasses import dataclass

_REFLOW_WIDTH = 320
_REFLOW_HEIGHT = 512
_TOLERANCE_PX = 1  # absorb sub-pixel rounding


@dataclass
class ReflowResult:
    has_horizontal_scroll: bool
    scroll_width: int
    client_width: int
    width_tested: int = _REFLOW_WIDTH
    error: str = ""


_MEASURE_JS = r"""
() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
})
"""


def probe_reflow_from_page(page, *, width: int = _REFLOW_WIDTH,
                           height: int = _REFLOW_HEIGHT) -> ReflowResult:
    """Measure reflow on an already-navigated page. Restores the original
    viewport afterwards so probe ordering on a shared page doesn't matter."""
    original = page.viewport_size
    try:
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(300)  # let layout settle after the resize
        m = page.evaluate(_MEASURE_JS) or {}
    except Exception as e:
        return ReflowResult(False, 0, 0, width, error=f"{type(e).__name__}: {e}")
    finally:
        if original:
            try:
                page.set_viewport_size(original)
            except Exception:
                pass
    sw = int(m.get("scrollWidth", 0))
    cw = int(m.get("clientWidth", 0))
    return ReflowResult(
        has_horizontal_scroll=cw > 0 and sw - cw > _TOLERANCE_PX,
        scroll_width=sw, client_width=cw, width_tested=width,
    )


def probe_reflow(page_url: str, *, ua: str | None = None,
                 color_scheme: str | None = None,
                 width: int = _REFLOW_WIDTH, height: int = _REFLOW_HEIGHT) -> ReflowResult:
    """Standalone: open own browser, navigate, measure reflow."""
    from ._session import standalone_page
    from .._security import require_safe_http_url
    with standalone_page(ua=ua, color_scheme=color_scheme) as page:
        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        require_safe_http_url(page.url)  # redirect may have landed on an internal host
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        return probe_reflow_from_page(page, width=width, height=height)
