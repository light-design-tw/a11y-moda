"""FA1250202E lint — duplicate-rule_id pair of GN1250201E (down event activation)."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr, _html_tag_name


_BAD_BODY = re.compile(r"\(\)|location|window\.|submit|navigate")


@register
class MouseDownActivationFALint(LintRule):
    meta = RuleMeta(
        rule_id="FA1250202E",
        guideline="2.5.2",
        level=Level.A,
        desc="onmousedown 直接執行啟動行為 — 應改 onmouseup 讓使用者可取消",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                attr = get_html_attr(el, "onmousedown")
                if attr.kind != "literal" or not attr.value:
                    continue
                v = attr.value.strip()
                if "return false" in v.lower():
                    continue
                if not _BAD_BODY.search(v):
                    continue
                yield self._issue(status="fail",
                    message=f'<{_html_tag_name(el)}> onmousedown 直接執行啟動行為 — 無法由使用者取消',
                    node=el)
                return
            return

        for el in find_jsx_elements(parsed.tree):
            attr = get_attr(el, "onMouseDown")
            if attr.kind != "literal" or not attr.value:
                continue
            v = attr.value.strip()
            if "return false" in v.lower():
                continue
            if not _BAD_BODY.search(v):
                continue
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in el.children if c.type == "identifier"), "?")
            yield self._issue(status="fail",
                message=f'<{tag}> onMouseDown 直接執行啟動行為 — 無法由使用者取消',
                node=el)
            return
