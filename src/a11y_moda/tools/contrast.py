"""WCAG color contrast ratio computation + per-element sampling via Playwright.

Implements the WCAG 2.1 relative-luminance formula directly so we don't depend on
the small `wcag-contrast-ratio` package (which doesn't handle alpha blending).
"""
from __future__ import annotations
import re
from dataclasses import dataclass


_RGB_FN = re.compile(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s]+([\d.]+))?\s*\)")


@dataclass
class TextSample:
    selector: str
    text: str
    fg: tuple[float, float, float]
    bg: tuple[float, float, float]
    font_size_px: float
    font_weight: int
    ratio: float
    is_large_text: bool
    unmeasurable: bool = False
    unmeasurable_reason: str = ""


def parse_css_color(value: str) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    v = value.strip().lower()
    if v in ("transparent", "none", "currentcolor"):
        return None
    m = _RGB_FN.match(v)
    if not m:
        return None
    r, g, b = (float(m.group(i)) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) else 1.0
    return r, g, b, a


def _channel(c: float) -> float:
    s = c / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def composite_over(fg_rgba: tuple[float, float, float, float], bg_rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Alpha-blend foreground RGBA over solid background."""
    r1, g1, b1, a = fg_rgba
    r2, g2, b2 = bg_rgb
    return (
        r1 * a + r2 * (1 - a),
        g1 * a + g2 * (1 - a),
        b1 * a + b2 * (1 - a),
    )


# Auto-scroll to trigger IntersectionObserver / lazy-mounted elements before sampling.
WARMUP_JS = r"""
async () => {
    const step = window.innerHeight;
    const max = document.body.scrollHeight;
    for (let y = 0; y < max; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 200));
    }
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 500));
    if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (e) {} }
}
"""


# JavaScript executed inside Playwright — extracts text-bearing elements with
# their computed colors and font metrics. Returned as a JSON-serialisable list.
SAMPLE_JS = r"""
() => {
    const out = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT, {
        acceptNode(el) {
            if (!el || !el.tagName) return NodeFilter.FILTER_SKIP;
            if (['SCRIPT','STYLE','NOSCRIPT','TEMPLATE','SVG','IFRAME'].includes(el.tagName)) return NodeFilter.FILTER_REJECT;
            const txt = (el.textContent || '').trim();
            if (!txt) return NodeFilter.FILTER_SKIP;
            const directText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.nodeValue.trim());
            return directText ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
        }
    });
    function effectiveBg(el) {
        let cur = el;
        while (cur && cur !== document.documentElement) {
            const cs = getComputedStyle(cur);
            const bg = cs.backgroundColor;
            const m = bg.match(/rgba?\(([^)]+)\)/);
            if (m) {
                const parts = m[1].split(/[,\s]+/).map(Number);
                const a = parts.length === 4 ? parts[3] : 1;
                if (a > 0.05) return `rgba(${parts.slice(0,3).join(',')},${a})`;
            }
            cur = cur.parentElement;
        }
        return 'rgb(255,255,255)';
    }
    function effectiveOpacity(el) {
        let a = 1, cur = el;
        while (cur && cur !== document.documentElement) {
            a *= parseFloat(getComputedStyle(cur).opacity || '1');
            cur = cur.parentElement;
        }
        return a;
    }
    function unmeasurableReason(el) {
        let cur = el;
        while (cur && cur !== document.documentElement) {
            const cs = getComputedStyle(cur);
            if (cs.backgroundImage && cs.backgroundImage !== 'none') {
                const v = cs.backgroundImage;
                if (v.startsWith('linear-gradient') || v.startsWith('radial-gradient') || v.startsWith('conic-gradient')) return 'gradient bg on ancestor';
                if (v.startsWith('url(')) return 'image bg on ancestor';
                return 'background-image on ancestor';
            }
            if (cs.mixBlendMode && cs.mixBlendMode !== 'normal') return `mix-blend-mode=${cs.mixBlendMode}`;
            const f = cs.filter;
            if (f && f !== 'none') return `filter=${f}`;
            const bd = cs.backdropFilter || cs.webkitBackdropFilter;
            if (bd && bd !== 'none') return `backdrop-filter=${bd}`;
            cur = cur.parentElement;
        }
        return '';
    }
    function selectorOf(el) {
        if (el.id) return '#' + el.id;
        let path = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') {
            path += '.' + el.className.trim().split(/\s+/).slice(0,2).join('.');
        }
        return path;
    }
    let n;
    while ((n = walker.nextNode())) {
        const cs = getComputedStyle(n);
        if (cs.visibility === 'hidden' || cs.display === 'none') continue;
        const rect = n.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        const eff_op = effectiveOpacity(n);
        if (eff_op <= 0.05) continue;  // hidden via opacity (drawers, animations)
        const ownText = Array.from(n.childNodes).filter(x => x.nodeType === 3).map(x => x.nodeValue).join('').trim();
        if (!ownText) continue;
        out.push({
            selector: selectorOf(n),
            text: ownText.slice(0, 80),
            fg: cs.color,
            bg: effectiveBg(n),
            opacity: eff_op,
            unmeasurable: unmeasurableReason(n),
            fontSize: parseFloat(cs.fontSize),
            fontWeight: parseInt(cs.fontWeight, 10) || 400,
        });
    }
    return out;
}
"""


def is_large_text(font_size_px: float, font_weight: int) -> bool:
    """WCAG 2.1: >=18pt (24px) OR >=14pt (18.66px) bold counts as large text."""
    if font_size_px >= 24.0:
        return True
    if font_size_px >= 18.66 and font_weight >= 700:
        return True
    return False


def collect_text_samples(page_url: str, *, ua: str = "Mozilla/5.0 a11y-moda") -> list[TextSample]:
    from playwright.sync_api import sync_playwright
    samples: list[TextSample] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        page.goto(page_url, wait_until="networkidle", timeout=30000)
        try:
            page.evaluate(WARMUP_JS)  # scroll-warmup + font-ready
        except Exception:
            pass
        raw = page.evaluate(SAMPLE_JS)
        browser.close()
    for r in raw:
        fg_parsed = parse_css_color(r["fg"])
        bg_parsed = parse_css_color(r["bg"])
        if not fg_parsed or not bg_parsed:
            continue
        bg_solid = (bg_parsed[0], bg_parsed[1], bg_parsed[2])
        # Apply cumulative ancestor opacity to fg alpha before compositing.
        eff_op = float(r.get("opacity", 1.0))
        fg_with_op = (fg_parsed[0], fg_parsed[1], fg_parsed[2], fg_parsed[3] * eff_op)
        fg_solid = composite_over(fg_with_op, bg_solid)
        ratio = contrast_ratio(fg_solid, bg_solid)
        unmeas = r.get("unmeasurable") or ""
        samples.append(TextSample(
            selector=r["selector"],
            text=r["text"],
            fg=fg_solid,
            bg=bg_solid,
            font_size_px=r["fontSize"],
            font_weight=r["fontWeight"],
            ratio=ratio,
            is_large_text=is_large_text(r["fontSize"], r["fontWeight"]),
            unmeasurable=bool(unmeas),
            unmeasurable_reason=unmeas,
        ))
    return samples
