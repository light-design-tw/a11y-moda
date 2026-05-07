"""GN1250201E lint — `onmousedown` activation should switch to `onmouseup`/`onclick`."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr, _html_tag_name


_NOOP = ("return false;", "return false")


@register
class MouseDownActivationLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1250201E",
        guideline="2.5.2",
        level=Level.A,
        desc="onMouseDown 啟動行為建議改用 onMouseUp / onClick",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                attr = get_html_attr(el, "onmousedown")
                if attr.kind != "literal" or not attr.value:
                    continue
                if attr.value.strip() in _NOOP:
                    continue
                yield self._issue(status="fail",
                    message=f'<{_html_tag_name(el)}> 使用 onmousedown 啟動行為 — 應改 onmouseup/onclick',
                    node=el)
                return
            return

        for el in find_jsx_elements(parsed.tree):
            attr = get_attr(el, "onMouseDown")
            if attr.kind == "missing":
                continue
            # JSX onMouseDown almost always passes a function reference; literal
            # string body is unusual. We flag presence as info (defer to scan).
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in el.children if c.type == "identifier"), "?")
            if attr.kind == "literal" and attr.value.strip() in _NOOP:
                continue
            yield self._issue(status="info",
                message=f'<{tag}> 使用 onMouseDown — 確認改 onClick / onMouseUp 行為',
                node=el)
            return
