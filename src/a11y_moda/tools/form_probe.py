"""Form submission probe via Playwright. Checks whether forms with required
fields move focus to the first invalid field on empty submit. Also opens
modal-mounted forms by clicking likely trigger buttons.
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
    input_count: int = 0
    error: str = ""


_FORM_SELECTORS_JS = r"""
() => {
    const SKIP_TYPES = new Set(['hidden', 'submit', 'button', 'reset', 'image']);
    const forms = Array.from(document.querySelectorAll('form'));
    return forms.map((f, i) => {
        const required = f.querySelectorAll('[required], [aria-required="true"]');
        const submitBtn = f.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
        let userInputs = 0;
        f.querySelectorAll('input, textarea, select').forEach(el => {
            const t = (el.getAttribute('type') || el.type || '').toLowerCase();
            if (!SKIP_TYPES.has(t)) userInputs++;
        });
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
            inputCount: userInputs,
        };
    });
}
"""


_STRUCTURAL_TRIGGER_SELECTORS = (
    '[aria-haspopup="dialog"]',
    '[aria-haspopup="true"]',
    '[data-bs-toggle="modal"]',
    '[data-toggle="modal"]',
    '[data-modal-target]',
    '[data-modal-trigger]',
    '[data-trigger="modal"]',
    '[data-open="modal"]',
    '[data-open-modal]',
)


_FIND_STRUCTURAL_TRIGGERS_JS = r"""
(selectors) => {
    const seen = new Set();
    const out = [];
    selectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            // map element to its index in our universal list
            const all = Array.from(document.querySelectorAll('button, a, [role="button"], [aria-haspopup], [data-bs-toggle], [data-toggle], [data-modal-target], [data-modal-trigger]'));
            const idx = all.indexOf(el);
            if (idx < 0 || seen.has(idx)) return;
            seen.add(idx);
            const text = (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 30);
            out.push({ idx, tag: el.tagName.toLowerCase(), text, why: 'structural:' + sel });
        });
    });
    return out;
}
"""


_MODAL_TRIGGER_HINTS = (
    "預約", "諮詢", "聯絡我們", "聯繫我們", "聯絡", "聯繫",
    "預定", "報名", "申請", "我要詢問", "詢問",
    "立即諮詢", "馬上預約", "免費諮詢",
    "掛號", "看診", "訂位",
    "索取", "試聽", "試讀", "試用", "Demo",
    "應徵", "投遞", "報價",
    "申辦", "意見", "問卷", "意見回饋", "回饋",
    "我有興趣", "來電", "線上", "立即報名",
    "contact us", "contact", "get in touch", "request",
    "book now", "book a", "enquire", "inquiry", "demo",
    "subscribe", "register", "sign up",
)


_FIND_TEXT_TRIGGERS_JS = r"""
(hints) => {
    const out = [];
    const all = Array.from(document.querySelectorAll('button, a, [role="button"], [aria-haspopup], [data-bs-toggle], [data-toggle], [data-modal-target], [data-modal-trigger]'));
    all.forEach((el, i) => {
        const text = (el.innerText || el.getAttribute('aria-label') || '').trim();
        if (!text || text.length > 30) return;
        const lower = text.toLowerCase();
        for (const h of hints) {
            if (text.includes(h) || lower.includes(h.toLowerCase())) {
                out.push({ idx: i, tag: el.tagName.toLowerCase(), text: text.slice(0, 30), why: 'text:' + h });
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


_CLICK_BY_INDEX_JS = r"""
(idx) => {
    const all = Array.from(document.querySelectorAll('button, a, [role="button"], [aria-haspopup], [data-bs-toggle], [data-toggle], [data-modal-target], [data-modal-trigger]'));
    const el = all[idx];
    if (!el) return false;
    el.click();
    return true;
}
"""


def _has_usable_form(forms_meta: list) -> bool:
    return any(f.get("requiredCount", 0) > 0 and f.get("hasSubmit") for f in forms_meta)


def _try_open_modal_forms(page, original_url: str, *, max_attempts: int = 3) -> None:
    """Try structural triggers first (ARIA / data attributes), then text hints.
    Click up to max_attempts candidates; revert if URL navigates away.
    """
    structural = page.evaluate(_FIND_STRUCTURAL_TRIGGERS_JS, list(_STRUCTURAL_TRIGGER_SELECTORS)) or []
    text_based = page.evaluate(_FIND_TEXT_TRIGGERS_JS, list(_MODAL_TRIGGER_HINTS)) or []
    seen_idx: set[int] = set()
    candidates: list[dict] = []
    for c in structural:
        if c["idx"] not in seen_idx:
            seen_idx.add(c["idx"])
            candidates.append(c)
    for c in text_based:
        if c["idx"] not in seen_idx:
            seen_idx.add(c["idx"])
            candidates.append(c)

    attempts = 0
    for cand in candidates:
        if attempts >= max_attempts:
            return
        attempts += 1
        try:
            clicked = page.evaluate(_CLICK_BY_INDEX_JS, cand["idx"])
            if not clicked:
                continue
            page.wait_for_timeout(600)
            if page.url != original_url:
                page.goto(original_url, wait_until="domcontentloaded", timeout=15000)
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass
                continue
            forms_now = page.evaluate(_FORM_SELECTORS_JS) or []
            if _has_usable_form(forms_now):
                return
        except Exception:
            continue


def probe_forms(page_url: str, *, max_forms: int = 5, timeout_ms: int = 30000,
                 ua: str = "Mozilla/5.0 a11y-moda", try_modal_triggers: bool = True
                 ) -> list[FormProbeResult]:
    """For each form: record input count, has_required, and (when applicable)
    simulate empty submit and report focus behaviour.

    When try_modal_triggers is True and no usable forms are found on initial
    load, attempt to click likely modal-opening triggers (ARIA / data
    attributes first, then text hints like 預約諮詢 / contact us) and re-probe
    so that forms inside dialogs are also covered.
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
                input_count = int(meta.get("inputCount", 0))
                if not has_req or not meta["hasSubmit"]:
                    out.append(FormProbeResult(
                        index=idx, selector=selector, has_required=has_req,
                        submit_clicked=False, error_focus_jumped=False,
                        focus_after_submit_tag="", focus_after_submit_selector="",
                        input_count=input_count,
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
                        input_count=input_count,
                    ))
                except Exception as e:
                    out.append(FormProbeResult(
                        index=idx, selector=selector, has_required=True,
                        submit_clicked=False, error_focus_jumped=False,
                        focus_after_submit_tag="", focus_after_submit_selector="",
                        input_count=input_count,
                        error=f"{type(e).__name__}: {e}",
                    ))
        finally:
            browser.close()
    return out
