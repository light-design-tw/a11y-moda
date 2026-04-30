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


def probe_forms(page_url: str, *, max_forms: int = 5, timeout_ms: int = 30000,
                 ua: str = "Mozilla/5.0 a11y-moda") -> list[FormProbeResult]:
    """For each form with required fields: trigger empty submit, record focus."""
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
