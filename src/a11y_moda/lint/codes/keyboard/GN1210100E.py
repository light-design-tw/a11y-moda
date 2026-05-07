"""GN1210100E lint — interactive mouse handler should pair with keyboard equivalent.

HTML uses lowercase (onclick/onmousedown/etc).
JSX uses camelCase (onClick/onMouseDown/etc).

For native focusable elements (<a>, <button>, <input> etc) onclick is
fine even without explicit keyboard handler — the element gets keyboard
activation for free.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr, _html_tag_name


_FOCUSABLE_NATIVES = ("a", "button", "input", "select", "textarea", "details")

_KEY_EQUIV_HTML = {
    "onclick": ("onkeydown", "onkeyup", "onkeypress"),
    "onmousedown": ("onkeydown",),
    "onmouseup": ("onkeyup",),
    "onmouseover": ("onfocus",),
    "onmouseout": ("onblur",),
}

_KEY_EQUIV_JSX = {
    "onClick": ("onKeyDown", "onKeyUp", "onKeyPress"),
    "onMouseDown": ("onKeyDown",),
    "onMouseUp": ("onKeyUp",),
    "onMouseOver": ("onFocus",),
    "onMouseOut": ("onBlur",),
}


@register
class KeyboardEventCounterpartLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1210100E",
        guideline="2.1.1",
        level=Level.A,
        desc="互動性滑鼠事件 (onClick/onMouseDown 等) 應提供鍵盤等效事件",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for mouse_evt, key_evts in _KEY_EQUIV_HTML.items():
                for el in find_html_elements(parsed.tree):
                    if get_html_attr(el, mouse_evt).kind == "missing":
                        continue
                    if mouse_evt == "onclick" and _html_tag_name(el) in _FOCUSABLE_NATIVES:
                        continue
                    if any(get_html_attr(el, k).kind != "missing" for k in key_evts):
                        continue
                    yield self._issue(status="fail",
                        message=f'<{_html_tag_name(el)}> 使用 {mouse_evt} 但未提供鍵盤等效 ({"/".join(key_evts)})',
                        node=el)
                    return
            return

        for mouse_evt, key_evts in _KEY_EQUIV_JSX.items():
            for el in find_jsx_elements(parsed.tree):
                if get_attr(el, mouse_evt).kind == "missing":
                    continue
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in el.children if c.type == "identifier"), "?")
                if mouse_evt == "onClick" and tag in _FOCUSABLE_NATIVES:
                    continue
                if any(get_attr(el, k).kind != "missing" for k in key_evts):
                    continue
                # Capital-first tag → custom React component. Library components
                # (shadcn/ui Button, Radix Primitive.button, HeadlessUI, ARK …)
                # commonly render a native <button> internally with full keyboard
                # support that lint can't trace through. Don't fail-spam these;
                # surface as caveat for the caller to verify.
                if tag and tag[0].isupper():
                    yield self._issue(status="caveat",
                        message=f'<{tag}> 自訂元件使用 {mouse_evt} 但未顯式 {"/".join(key_evts)} — 元件內部可能已處理鍵盤',
                        node=el)
                    return
                yield self._issue(status="fail",
                    message=f'<{tag}> 使用 {mouse_evt} 但未提供鍵盤等效 ({"/".join(key_evts)})',
                    node=el)
                return
