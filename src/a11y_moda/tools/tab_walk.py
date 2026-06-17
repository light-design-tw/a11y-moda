"""Keyboard tab traversal via Playwright. Reports focusable element order,
visible focus ring presence + geometry, and whether the focused element is
obscured by sticky/fixed content (WCAG 2.4.11 / 2.4.13 evidence).
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FocusStop:
    index: int
    tag: str
    selector: str
    text: str
    has_visible_outline: bool
    in_viewport: bool
    # Focus-indicator geometry (2.4.13). outline_width is px; 0 when the
    # indicator is box-shadow-only or absent — measure-by-outline not possible.
    outline_width: float = 0.0
    outline_color: str = ""
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h (viewport coords)
    # focused element covered by a position:sticky / fixed element. `obscured`
    # = any sample point covered (2.4.12 enhanced); `obscured_fully` = every
    # in-viewport sample point covered, i.e. entirely hidden (2.4.11 minimum).
    obscured: bool = False
    obscured_fully: bool = False


COLLECT_FOCUS_JS = r"""
() => {
    const el = document.activeElement;
    if (!el || el === document.body) return null;
    // The element IS focused right now (we just pressed Tab to it), so the
    // regular computed style already includes the :focus / :focus-visible
    // cascade. Do NOT pass ':focus-visible' as second arg — getComputedStyle
    // accepts only pseudo-ELEMENTS (::before/::after/::marker), not pseudo-
    // CLASSES. Chromium silently falls back to the non-focus style when given
    // a pseudo-class, producing false negatives ("no focus indicator" when
    // one is actually present).
    const cs = getComputedStyle(el);
    const focusOutline = cs.outlineStyle && cs.outlineStyle !== 'none' &&
                         cs.outlineWidth !== '0px' &&
                         cs.outlineColor !== 'transparent';
    const focusBoxShadow = cs.boxShadow && cs.boxShadow !== 'none';
    const rect = el.getBoundingClientRect();
    const inViewport = rect.top >= 0 && rect.bottom <= window.innerHeight && rect.width > 0;
    // 2.4.11: probe a few points on the focused element's box; if the topmost
    // element there is a different element nested under a sticky/fixed
    // ancestor, the focus is being covered (browsers scroll focus into view
    // but ignore sticky overlays).
    let obscuredCount = 0, sampledCount = 0;
    if (rect.width > 0 && rect.height > 0) {
        const pts = [
            [rect.left + rect.width / 2, rect.top + 2],
            [rect.left + 2, rect.top + 2],
            [rect.right - 2, rect.top + 2],
            [rect.left + rect.width / 2, rect.bottom - 2],
        ];
        for (const [x, y] of pts) {
            if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) continue;
            sampledCount++;
            const top = document.elementFromPoint(x, y);
            if (!top || top === el || el.contains(top) || top.contains(el)) continue;
            let p = top, hit = false;
            while (p && p !== document.body) {
                const pos = getComputedStyle(p).position;
                if (pos === 'sticky' || pos === 'fixed') { hit = true; break; }
                p = p.parentElement;
            }
            if (hit) obscuredCount++;
        }
    }
    const obscured = obscuredCount > 0;
    const obscuredFully = sampledCount > 0 && obscuredCount === sampledCount;
    let selector = el.tagName.toLowerCase();
    if (el.id) selector += '#' + el.id;
    else if (el.className && typeof el.className === 'string') {
        selector += '.' + el.className.trim().split(/\s+/).slice(0,2).join('.');
    }
    return {
        tag: el.tagName.toLowerCase(),
        selector,
        text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 60),
        hasVisibleOutline: focusOutline || focusBoxShadow,
        inViewport,
        outlineWidth: focusOutline ? (parseFloat(cs.outlineWidth) || 0) : 0,
        outlineColor: cs.outlineColor,
        bbox: [rect.left, rect.top, rect.width, rect.height],
        obscured,
        obscuredFully,
    };
}
"""


def walk_tab_stops_from_page(page, *, max_stops: int = 80) -> list[FocusStop]:
    """Walk Tab order on an already-navigated Playwright page."""
    stops: list[FocusStop] = []
    try:
        page.evaluate("document.body.focus()")
    except Exception:
        pass
    seen: set[str] = set()
    for i in range(max_stops):
        page.keyboard.press("Tab")
        info = page.evaluate(COLLECT_FOCUS_JS)
        if info is None:
            break
        key = f"{info['tag']}|{info['selector']}|{info['text']}"
        if key in seen:
            break
        seen.add(key)
        bbox = info.get("bbox") or (0, 0, 0, 0)
        stops.append(FocusStop(
            index=i,
            tag=info["tag"],
            selector=info["selector"],
            text=info["text"],
            has_visible_outline=bool(info["hasVisibleOutline"]),
            in_viewport=bool(info["inViewport"]),
            outline_width=float(info.get("outlineWidth") or 0),
            outline_color=str(info.get("outlineColor") or ""),
            bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            obscured=bool(info.get("obscured")),
            obscured_fully=bool(info.get("obscuredFully")),
        ))
    return stops


def walk_tab_stops(page_url: str, *, max_stops: int = 80, ua: str | None = None,
                    color_scheme: str | None = None) -> list[FocusStop]:
    """Standalone: open own browser. Used when no shared session."""
    from ._session import standalone_page
    from .._security import require_safe_http_url
    with standalone_page(ua=ua, color_scheme=color_scheme) as page:
        page.goto(page_url, wait_until="networkidle", timeout=30000)
        require_safe_http_url(page.url)  # redirect may have landed on an internal host
        return walk_tab_stops_from_page(page, max_stops=max_stops)
