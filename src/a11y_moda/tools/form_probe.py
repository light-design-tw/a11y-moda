"""Form submission probe via Playwright. Checks whether forms with required
fields move focus to the first invalid field on empty submit.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FormProbeResult:
    index: int
    selector: str
    has_required: bool
    submit_clicked: bool
    error_focus_jumped: bool
    focus_after_submit_tag: str
    focus_after_submit_selector: str
    error: str = ""


_FORM_SELECTORS_JS = r"""
() => {
    const forms = Array.from(document.querySelectorAll('form'));
    return forms.map((f, i) => {
        const required = f.querySelectorAll('[required], [aria-required="true"]');
        const submitBtn = f.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
        let sel = 'form';
        if (f.id) sel = `form#${f.id}`;
        else if (f.name) sel = `form[name="${f.name}"]`;
        else if (f.className && typeof f.className === 'string') {
            const cls = f.className.trim().split(/\s+/).slice(0, 1).join('.');
            if (cls) sel = `form.${cls}`;
        }
        sel += `:nth-of-type(${i + 1})`;
        return {
            index: i,
            selector: sel,
            requiredCount: required.length,
            hasSubmit: !!submitBtn,
        };
    });
}
"""


_MODAL_TRIGGER_HINTS = (
    "預約", "諮詢", "聯絡我們", "聯繫我們", "聯繫", "預定", "報名", "申請",
    "我要詢問", "詢問", "立即諮詢", "馬上預約", "免費諮詢",
    "contact us", "contact", "get in touch", "request", "book now", "enquire", "inquiry",
)


_FIND_TRIGGERS_JS = r"""
(hints) => {
    const out = [];
    const candidates = Array.from(document.querySelectorAll('button, a, [role="button"]'));
    candidates.forEach((el, i) => {
        const text = (el.innerText || el.getAttribute('aria-label') || '').trim();
        if (!text || text.length > 30) return;
        const lower = text.toLowerCase();
        for (const h of hints) {
            if (text.includes(h) || lower.includes(h.toLowerCase())) {
                let sel = el.tagName.toLowerCase();
                if (el.id) sel += '#' + el.id;
                out.push({ idx: i, tag: el.tagName.toLowerCase(), text: text.slice(0, 30), selector: sel });
                break;
            }
        }
    });
    return out;
}
"""

_FOCUS_AFTER_JS = r"""
() => {
    const ae = document.activeElement;
    if (!ae || ae === document.body) {
        return { tag: 'body', selector: 'body', isInvalidRequired: false };
    }
    const isRequired = ae.matches && (ae.matches('[required]') || ae.getAttribute('aria-required') === 'true');
    let isInvalid = false;
    try {
        if (ae.matches(':invalid')) isInvalid = true;
    } catch (e) {}
    if (ae.getAttribute('aria-invalid') === 'true') isInvalid = true;
    let sel = ae.tagName.toLowerCase();
    if (ae.id) sel += '#' + ae.id;
    else if (ae.name) sel += '[name="' + ae.name + '"]';
    return {
        tag: ae.tagName.toLowerCase(),
        selector: sel,
        isInvalidRequired: isRequired && isInvalid,
    };
}
"""


def _has_usable_form(forms_meta: list) -> bool:
    return any(f.get("requiredCount", 0) > 0 and f.get("hasSubmit") for f in forms_meta)


def _try_open_modal_forms(page, original_url: str, *, max_attempts: int = 3) -> None:
    """Click up to max_attempts modal-trigger candidates; abort if URL navigates away."""
    triggers = page.evaluate(_FIND_TRIGGERS_JS, list(_MODAL_TRIGGER_HINTS)) or []
    seen_idx: set[int] = set()
    for cand in triggers[:max_attempts * 2]:
        idx = cand.get("idx")
        if idx in seen_idx:
            continue
        seen_idx.add(idx)
        if len(seen_idx) > max_attempts:
            return
        try:
            clicked = page.evaluate(f"""
                () => {{
                    const all = Array.from(document.querySelectorAll('button, a, [role="button"]'));
                    const el = all[{idx}];
                    if (!el) return false;
                    el.click();
                    return true;
                }}
            """)
            if not clicked:
                continue
            page.wait_for_timeout(600)
            if page.url != original_url:
                page.goto(original_url, wait_until="domcontentloaded", timeout=15000)
                continue
            forms_now = page.evaluate(_FORM_SELECTORS_JS) or []
            if _has_usable_form(forms_now):
                return
        except Exception:
            continue


def probe_forms(page_url: str, *, max_forms: int = 5, timeout_ms: int = 30000,
                 ua: str = "Mozilla/5.0 a11y-moda", try_modal_triggers: bool = True
                 ) -> list[FormProbeResult]:
    """For each form with required fields: trigger empty submit, record focus.

    When try_modal_triggers is True and no usable forms are found on initial load,
    attempt to click likely modal-opening buttons (e.g. 預約諮詢, contact us)
    and re-probe so that forms inside dialogs are also covered.
    """
    from playwright.sync_api import sync_playwright
    out: list[FormProbeResult] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            forms_meta = page.evaluate(_FORM_SELECTORS_JS) or []
            if try_modal_triggers and not _has_usable_form(forms_meta):
                _try_open_modal_forms(page, page_url)
                forms_meta = page.evaluate(_FORM_SELECTORS_JS) or []
            for meta in forms_meta[:max_forms]:
                idx = meta["index"]
                selector = meta["selector"]
                has_req = meta["requiredCount"] > 0
                if not has_req or not meta["hasSubmit"]:
                    out.append(FormProbeResult(
                        index=idx, selector=selector, has_required=has_req,
                        submit_clicked=False, error_focus_jumped=False,
                        focus_after_submit_tag="", focus_after_submit_selector="",
                    ))
                    continue
                try:
                    page.evaluate(f"""
                        () => {{
                            const f = document.querySelectorAll('form')[{idx}];
                            if (!f) return;
                            const sb = f.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
                            if (sb) sb.click();
                        }}
                    """)
                    page.wait_for_timeout(300)
                    focus = page.evaluate(_FOCUS_AFTER_JS) or {}
                    out.append(FormProbeResult(
                        index=idx,
                        selector=selector,
                        has_required=True,
                        submit_clicked=True,
                        error_focus_jumped=bool(focus.get("isInvalidRequired")),
                        focus_after_submit_tag=focus.get("tag", ""),
                        focus_after_submit_selector=focus.get("selector", ""),
                    ))
                except Exception as e:
                    out.append(FormProbeResult(
                        index=idx, selector=selector, has_required=True,
                        submit_clicked=False, error_focus_jumped=False,
                        focus_after_submit_tag="", focus_after_submit_selector="",
                        error=f"{type(e).__name__}: {e}",
                    ))
        finally:
            browser.close()
    return out
