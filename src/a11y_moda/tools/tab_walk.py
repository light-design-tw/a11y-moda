"""Keyboard tab traversal via Playwright. Reports focusable element order +
visible focus ring presence.
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
        stops.append(FocusStop(
            index=i,
            tag=info["tag"],
            selector=info["selector"],
            text=info["text"],
            has_visible_outline=bool(info["hasVisibleOutline"]),
            in_viewport=bool(info["inViewport"]),
        ))
    return stops


def walk_tab_stops(page_url: str, *, max_stops: int = 80, ua: str | None = None,
                    color_scheme: str | None = None) -> list[FocusStop]:
    """Standalone: open own browser. Used when no shared session."""
    from ._session import standalone_page
    with standalone_page(ua=ua, color_scheme=color_scheme) as page:
        page.goto(page_url, wait_until="networkidle", timeout=30000)
        return walk_tab_stops_from_page(page, max_stops=max_stops)
