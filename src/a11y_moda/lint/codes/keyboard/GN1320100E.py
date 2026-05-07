"""GN1320100E lint — `onFocus` handler must not trigger context changes
(window navigation, form submit, history mutation).

JSX inline handler (`onFocus={handler}`) is dynamic — can't statically
analyse the function body. Pattern matching only on inline string
handlers (HTML onfocus="..." or JSX onFocus="literal-string").
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr,
    find_html_elements, get_html_attr,
)


_BAD_HANDLER = re.compile(
    r"location\.(href|replace|assign)|window\.open|\.submit\(|history\.(push|replace)"
)


@register
class FocusNoContextChangeLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1320100E",
        guideline="3.2.1",
        level=Level.A,
        desc="onFocus 處理函式不應觸發頁面跳轉/送出 (脈絡變更)",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                attr = get_html_attr(el, "onfocus")
                if attr.kind != "literal" or not attr.value:
                    continue
                if _BAD_HANDLER.search(attr.value):
                    yield self._issue(status="fail",
                        message="onfocus 含會變更脈絡的呼叫 (location/window.open/submit)",
                        node=el)
                    return
            return

        for el in find_jsx_elements(parsed.tree):
            # JSX uses onFocus (camelCase). Only literal string handlers are
            # statically inspectable; arrow functions/refs need scan.
            attr = get_attr(el, "onFocus")
            if attr.kind != "literal" or not attr.value:
                continue
            if _BAD_HANDLER.search(attr.value):
                yield self._issue(status="fail",
                    message="onFocus 含會變更脈絡的呼叫 (location/window.open/submit)",
                    node=el)
                return
