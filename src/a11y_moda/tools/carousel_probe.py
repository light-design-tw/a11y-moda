"""Carousel auto-rotation probe via Playwright.

Static class-name heuristics (carousel/swiper/slick) miss custom and
no-code-builder carousels (Wix/Webflow build their own with arbitrary
classes). This probe observes DOM motion: snapshot transform / scrollLeft
of likely carousel containers, wait, snapshot again. If anything moved
without user interaction, we treat it as auto-rotating.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CarouselProbeResult:
    selector: str
    auto_rotates: bool
    has_pause_control: bool
    seconds_observed: float
    error: str = ""


# Find candidates by structure (siblings of similar size in a horizontal
# row, common in carousels) plus class-name hints. We snapshot transform
# of the children and scrollLeft of the parent — both are how 99% of
# carousels animate.
_FIND_CAROUSEL_CANDIDATES_JS = r"""
() => {
    const HINTS = /(carousel|slider|slick|swiper|owl-carousel|glide|splide|flickity|rotator)/i;
    const out = [];
    const seen = new Set();
    // Class-hint candidates first.
    document.querySelectorAll('*').forEach(el => {
        if (!(el instanceof Element)) return;
        if (seen.has(el)) return;
        const cls = el.className && typeof el.className === 'string' ? el.className : '';
        if (!HINTS.test(cls)) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 200 || rect.height < 80) return;
        seen.add(el);
        out.push(el);
    });
    // Structural candidate: a parent whose direct children are 3+ same-tag
    // elements of similar height arranged horizontally — typical carousel
    // layout. Limit to first 30 candidates to keep eval fast.
    if (out.length < 5) {
        const all = Array.from(document.querySelectorAll('div, ul, section'));
        for (const parent of all.slice(0, 500)) {
            if (seen.has(parent)) continue;
            const kids = Array.from(parent.children).filter(c => c instanceof Element);
            if (kids.length < 3) continue;
            const heights = kids.map(k => k.getBoundingClientRect().height);
            const tops = kids.map(k => k.getBoundingClientRect().top);
            if (heights.some(h => h < 60)) continue;
            const sameRow = Math.max(...tops) - Math.min(...tops) < 20;
            if (!sameRow) continue;
            seen.add(parent);
            out.push(parent);
            if (out.length >= 8) break;
        }
    }
    return out.slice(0, 6).map((el, i) => {
        let s = el.tagName.toLowerCase();
        if (el.id) s += '#' + el.id;
        else if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\s+/).slice(0, 2).join('.');
            if (cls) s += '.' + cls;
        }
        return { idx: i, selector: s };
    });
}
"""


_SNAPSHOT_MOTION_JS = r"""
(selectors) => {
    const out = {};
    selectors.forEach(sel => {
        let el;
        try { el = document.querySelector(sel); } catch(_) { return; }
        if (!el) return;
        const transforms = Array.from(el.children)
            .slice(0, 6)
            .map(c => getComputedStyle(c).transform || '');
        out[sel] = {
            scrollLeft: el.scrollLeft,
            transforms,
        };
    });
    return out;
}
"""


_PAUSE_CONTROL_JS = r"""
(sel) => {
    const PAUSE_RE = /(pause|stop|暫停|停止)/i;
    let el;
    try { el = document.querySelector(sel); } catch(_) { return false; }
    if (!el) return false;
    // Check inside the carousel and its immediate parent (controls
    // sometimes sit beside, not inside).
    const scope = [el, el.parentElement].filter(Boolean);
    for (const root of scope) {
        const ctrls = root.querySelectorAll('button, a, [role="button"]');
        for (const b of ctrls) {
            const text = ((b.innerText || '') + ' ' +
                          (b.getAttribute('aria-label') || '') + ' ' +
                          (b.getAttribute('title') || '')).trim();
            if (PAUSE_RE.test(text)) return true;
        }
    }
    return false;
}
"""


def _diff(a: dict, b: dict) -> bool:
    """Return True if any selector's transform or scrollLeft changed."""
    for sel, before in a.items():
        after = b.get(sel) or {}
        if before.get("scrollLeft") != after.get("scrollLeft"):
            return True
        bt = before.get("transforms") or []
        at = after.get("transforms") or []
        if bt != at:
            return True
    return False


def probe_carousels_from_page(page, *, observe_seconds: float = 4.5,
                               max_candidates: int = 6
                               ) -> list[CarouselProbeResult]:
    """Probe auto-rotating carousels on an already-navigated page.

    Cost: one ~observe_seconds wait. Caller invokes this between Tab walk
    (which happens in pristine state) and form_probe (which clicks
    triggers and may dirty state).
    """
    out: list[CarouselProbeResult] = []
    try:
        cands = page.evaluate(_FIND_CAROUSEL_CANDIDATES_JS) or []
    except Exception as e:
        return [CarouselProbeResult(selector="(probe init)", auto_rotates=False,
                                     has_pause_control=False, seconds_observed=0,
                                     error=f"{type(e).__name__}: {e}")]
    if not cands:
        return out
    selectors = [c["selector"] for c in cands[:max_candidates]]
    try:
        snap1 = page.evaluate(_SNAPSHOT_MOTION_JS, selectors) or {}
        page.wait_for_timeout(int(observe_seconds * 1000))
        snap2 = page.evaluate(_SNAPSHOT_MOTION_JS, selectors) or {}
    except Exception as e:
        return [CarouselProbeResult(selector="(snapshot)", auto_rotates=False,
                                     has_pause_control=False,
                                     seconds_observed=observe_seconds,
                                     error=f"{type(e).__name__}: {e}")]
    for sel in selectors:
        before = snap1.get(sel) or {}
        after = snap2.get(sel) or {}
        moved = _diff({sel: before}, {sel: after})
        if not moved:
            continue
        try:
            has_pause = bool(page.evaluate(_PAUSE_CONTROL_JS, sel))
        except Exception:
            has_pause = False
        out.append(CarouselProbeResult(
            selector=sel,
            auto_rotates=True,
            has_pause_control=has_pause,
            seconds_observed=observe_seconds,
        ))
    return out


def probe_carousels(page_url: str, *, ua: str | None = None,
                    observe_seconds: float = 4.5, timeout_ms: int = 30000,
                    color_scheme: str | None = None
                    ) -> list[CarouselProbeResult]:
    """Standalone: open own browser, navigate, probe carousels."""
    from ._session import standalone_page
    from .._security import require_safe_http_url
    with standalone_page(ua=ua, color_scheme=color_scheme) as page:
        page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
        require_safe_http_url(page.url)  # redirect may have landed on an internal host
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        return probe_carousels_from_page(page, observe_seconds=observe_seconds)
