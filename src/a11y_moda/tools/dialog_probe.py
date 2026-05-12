"""Focus-trap probe via Playwright.

Real MODA AAA audits flag three failure modes that pure tab-walk on the
default page state cannot catch:

1. Hamburger / drop-down menu opens but Tab moves focus OUT of the menu
   while the menu is still visible on screen (no focus trap).
2. Modal / dialog opens but next Tab leaves the dialog and walks the
   underlying page (no focus trap).
3. Skip-link target receives focus on activation but has no visible
   focus indicator at the destination.

This probe clicks each candidate trigger, then walks Tab inside the
opened state, recording whether focus stayed inside the opened
container (= trap works) or escaped to siblings/body (= no trap).

Mutates page state. Caller treats page as dirty afterwards.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DialogProbeResult:
    trigger_text: str
    trigger_selector: str
    kind: str           # "menu" | "modal" | "skip-link"
    opened: bool        # click visibly changed page state
    focus_trapped: bool # all Tab stops stayed inside opened container
    escape_closes: bool # Esc returned focus to trigger AND closed
    skip_target_visible_focus: bool = False  # only for skip-link
    container_selector: str = ""
    tab_stops_inside: int = 0
    tab_stops_outside: int = 0
    error: str = ""


_HAMBURGER_HINTS = (
    "選單", "目錄", "menu", "navigation", "主選單",
    "漢堡", "hamburger",
)


# Find buttons / links that look like menu or dialog triggers.
# Returns each as { idx, kind, text }. idx points into a stable list so we
# can click without holding stale element handles across Playwright JSON
# round-trips (handles sometimes invalidate after the page mutates).
_FIND_TRIGGERS_JS = r"""
(hints) => {
    const out = [];
    const all = Array.from(document.querySelectorAll(
        'button, a, [role="button"], [aria-haspopup], [aria-expanded]'
    ));
    all.forEach((el, i) => {
        const text = [el.innerText, el.getAttribute('aria-label'),
                      el.getAttribute('title')]
            .filter(Boolean).join(' ').trim().slice(0, 60);
        const haspopup = (el.getAttribute('aria-haspopup') || '').toLowerCase();
        const expanded = el.getAttribute('aria-expanded');
        const lower = text.toLowerCase();
        let kind = null;
        // Strong signals first.
        if (haspopup === 'dialog') kind = 'modal';
        else if (haspopup === 'menu' || haspopup === 'true') kind = 'menu';
        else if (expanded === 'false' && hints.some(h => lower.includes(h.toLowerCase()) || text.includes(h))) {
            kind = 'menu';
        }
        // Hamburger usually has aria-label only (no innerText).
        else if (!text && el.querySelector('svg, [class*="hamburger"], [class*="burger"]')) {
            kind = 'menu';
        }
        else if (hints.some(h => lower.includes(h.toLowerCase()) || text.includes(h))) {
            kind = 'menu';
        }
        if (kind) {
            let sel = el.tagName.toLowerCase();
            if (el.id) sel += '#' + el.id;
            else if (el.className && typeof el.className === 'string') {
                const cls = el.className.trim().split(/\s+/).slice(0, 1).join('.');
                if (cls) sel += '.' + cls;
            }
            out.push({ idx: i, kind, text, selector: sel });
        }
    });
    // De-dup by idx (a single el can match multiple signals).
    const seen = new Set();
    return out.filter(c => { if (seen.has(c.idx)) return false; seen.add(c.idx); return true; });
}
"""


_CLICK_TRIGGER_JS = r"""
(idx) => {
    const all = Array.from(document.querySelectorAll(
        'button, a, [role="button"], [aria-haspopup], [aria-expanded]'
    ));
    const el = all[idx];
    if (!el) return null;
    el.scrollIntoView({block: 'center'});
    el.click();
    return true;
}
"""


# After clicking the trigger, walk Tab N times and report:
# - container we'll consider "the open dialog" = closest [role=dialog] /
#   [role=menu] / dialog / nav.is-open / aside.is-open ancestor of the
#   first tab stop. If none, fall back to nearest sibling-of-trigger that
#   is now display:block.
# - For each Tab, was activeElement still inside that container?
_WALK_TAB_INSIDE_JS = r"""
(maxStops) => {
    const out = { containerSelector: '', stopsInside: 0, stopsOutside: 0, opened: false };
    function dialogAncestor(el) {
        let cur = el;
        while (cur && cur !== document.body) {
            if (!(cur instanceof Element)) { cur = cur.parentNode; continue; }
            const role = (cur.getAttribute && cur.getAttribute('role')) || '';
            if (cur.tagName === 'DIALOG' || role === 'dialog' || role === 'menu' ||
                role === 'navigation' || cur.tagName === 'NAV' ||
                (cur.className && typeof cur.className === 'string' &&
                 /\b(modal|dialog|drawer|popover|menu|nav-open|menu-open|is-open|active)\b/i.test(cur.className))) {
                return cur;
            }
            cur = cur.parentElement;
        }
        return null;
    }
    function describe(el) {
        if (!el) return '';
        let s = el.tagName ? el.tagName.toLowerCase() : '';
        if (el.id) s += '#' + el.id;
        else if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\s+/).slice(0,2).join('.');
            if (cls) s += '.' + cls;
        }
        return s;
    }
    // First Tab to find where focus lands.
    return new Promise(async (resolve) => {
        // Yield once to let any open animation settle.
        await new Promise(r => setTimeout(r, 200));
        // Use a synthetic key event isn't reliable across browsers; rely on
        // Playwright pressing Tab. We just observe activeElement here.
        resolve(out);
    });
}
"""


# We avoid evaluate-driven Tab presses (focus/keydown synthesis is flaky in
# Playwright). Instead caller uses page.keyboard.press("Tab") and we
# re-evaluate this JS each press to get current activeElement state.
_OBSERVE_FOCUS_JS = r"""
(containerSelector) => {
    const ae = document.activeElement;
    if (!ae || ae === document.body) return { tag: 'body', inside: false, selector: 'body' };
    let inside = false;
    if (containerSelector) {
        try {
            const container = document.querySelector(containerSelector);
            if (container && container.contains(ae)) inside = true;
        } catch(e) {}
    }
    let s = ae.tagName.toLowerCase();
    if (ae.id) s += '#' + ae.id;
    else if (ae.className && typeof ae.className === 'string') {
        const cls = ae.className.trim().split(/\s+/).slice(0,2).join('.');
        if (cls) s += '.' + cls;
    }
    return { tag: ae.tagName.toLowerCase(), inside, selector: s };
}
"""


_FIND_OPEN_CONTAINER_JS = r"""
() => {
    // Heuristic: look for newly visible container with dialog/menu signals.
    // We don't track diff — just find the topmost likely-open container.
    const candidates = Array.from(document.querySelectorAll(
        '[role="dialog"], [role="menu"], dialog[open], ' +
        '[class*="modal"], [class*="dialog"], [class*="drawer"], [class*="popover"], ' +
        '[class*="menu-open"], [class*="nav-open"], .is-open, [aria-modal="true"]'
    ));
    for (const el of candidates) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const rect = el.getBoundingClientRect();
        if (rect.width < 50 || rect.height < 50) continue;
        // Build a unique-enough selector.
        let s = el.tagName.toLowerCase();
        if (el.id) return s + '#' + el.id;
        if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\s+/).slice(0,2).join('.');
            if (cls) return s + '.' + cls;
        }
        return s;
    }
    return '';
}
"""


_SKIP_LINK_JS = r"""
() => {
    const PATTERNS = [
        '跳至主要內容', '跳到主要內容', '跳到內容', '跳過導覽', '跳過導航', '跳至內容區',
        'skip to main content', 'skip to content', 'skip navigation', 'skip nav',
        'skip to navigation', 'jump to content', 'jump to main',
    ];
    const links = Array.from(document.querySelectorAll('a[href^="#"]'));
    for (const a of links) {
        const text = (a.innerText || a.getAttribute('aria-label') || '').trim().toLowerCase();
        if (PATTERNS.some(p => text.includes(p.toLowerCase()))) {
            const all = Array.from(document.querySelectorAll('a, button, input, select, textarea, [tabindex]'));
            return {
                idx: all.indexOf(a),
                href: a.getAttribute('href'),
                text: text.slice(0, 40),
            };
        }
    }
    return null;
}
"""


_SKIP_TARGET_FOCUS_JS = r"""
(targetId) => {
    const id = targetId.replace(/^#/, '');
    const target = document.getElementById(id);
    if (!target) return { found: false };
    const ae = document.activeElement;
    const onTarget = ae === target;
    // Check :focus-visible style on target.
    let visible = false;
    try {
        const ps = getComputedStyle(target, ':focus-visible');
        visible = (ps.outlineStyle && ps.outlineStyle !== 'none' && ps.outlineWidth !== '0px') ||
                  (ps.boxShadow && ps.boxShadow !== 'none');
    } catch (e) {}
    return { found: true, focused: onTarget, visibleFocus: visible };
}
"""


def _probe_one_trigger(page, cand: dict, *, max_tab_stops: int = 12) -> DialogProbeResult:
    """Click trigger, observe Tab traversal inside opened container."""
    text = cand.get("text") or "(no text)"
    sel = cand.get("selector", "")
    kind = cand.get("kind", "unknown")
    res = DialogProbeResult(trigger_text=text, trigger_selector=sel, kind=kind,
                            opened=False, focus_trapped=False, escape_closes=False)
    try:
        page.evaluate(_CLICK_TRIGGER_JS, cand["idx"])
        page.wait_for_timeout(400)
        container = page.evaluate(_FIND_OPEN_CONTAINER_JS) or ""
        if not container:
            # No detectable open container — either no-op click or in-place
            # nav. Caller may still want to record it.
            res.error = "no open container detected"
            return res
        res.opened = True
        res.container_selector = container
        for _ in range(max_tab_stops):
            page.keyboard.press("Tab")
            page.wait_for_timeout(40)
            obs = page.evaluate(_OBSERVE_FOCUS_JS, container)
            if obs.get("inside"):
                res.tab_stops_inside += 1
            else:
                res.tab_stops_outside += 1
                # First escape = trap broken; no point walking further.
                break
        res.focus_trapped = (res.tab_stops_outside == 0 and res.tab_stops_inside > 0)
        # Esc behaviour.
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        # Container still visible?
        still_open = page.evaluate(f"""() => {{
            try {{ const e = document.querySelector({container!r});
                   if (!e) return false;
                   const cs = getComputedStyle(e);
                   return cs.display !== 'none' && cs.visibility !== 'hidden';
            }} catch(_) {{ return false; }}
        }}""")
        res.escape_closes = not still_open
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
    return res


def _probe_skip_link(page) -> DialogProbeResult | None:
    info = page.evaluate(_SKIP_LINK_JS)
    if not info:
        return None
    res = DialogProbeResult(
        trigger_text=info.get("text", ""),
        trigger_selector="a[href^='#']",
        kind="skip-link",
        opened=False, focus_trapped=False, escape_closes=False,
    )
    try:
        # Tab from body until we land on the skip link (it's typically the
        # first focusable element). Cap at 5 to avoid infinite walks.
        page.evaluate("() => document.body.focus()")
        landed = False
        for _ in range(5):
            page.keyboard.press("Tab")
            page.wait_for_timeout(30)
            cur = page.evaluate("""() => {
                const a = document.activeElement;
                return a && a.tagName === 'A' ? (a.getAttribute('href') || '') : '';
            }""")
            if cur and cur == info["href"]:
                landed = True
                break
        if not landed:
            res.error = "could not focus skip link via Tab"
            return res
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        target = page.evaluate(_SKIP_TARGET_FOCUS_JS, info["href"])
        if not target.get("found"):
            res.error = f"skip target {info['href']} not found"
            return res
        res.opened = bool(target.get("focused"))
        res.skip_target_visible_focus = bool(target.get("visibleFocus"))
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
    return res


def probe_dialogs_from_page(page, *, max_triggers: int = 4) -> list[DialogProbeResult]:
    """Probe focus-trap behaviour on an already-navigated Playwright page.

    Each call clicks up to max_triggers candidate triggers and walks Tab
    inside what opens. Page state is mutated; caller should run this LAST
    among probes that share a page (after contrast / tab_walk).
    """
    out: list[DialogProbeResult] = []
    skip = _probe_skip_link(page)
    if skip is not None:
        out.append(skip)
    try:
        cands = page.evaluate(_FIND_TRIGGERS_JS, list(_HAMBURGER_HINTS)) or []
    except Exception as e:
        return out + [DialogProbeResult(
            trigger_text="(probe init)", trigger_selector="", kind="unknown",
            opened=False, focus_trapped=False, escape_closes=False,
            error=f"{type(e).__name__}: {e}",
        )]
    for cand in cands[:max_triggers]:
        out.append(_probe_one_trigger(page, cand))
    return out


def probe_dialogs(page_url: str, *, ua: str | None = None,
                  max_triggers: int = 4, timeout_ms: int = 30000
                  ) -> list[DialogProbeResult]:
    """Standalone: open own browser, navigate, probe dialogs."""
    from ._session import standalone_page
    with standalone_page(ua=ua) as page:
        page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        return probe_dialogs_from_page(page, max_triggers=max_triggers)
