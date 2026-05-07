"""HM1130105E lint — <b>/<i> overuse without <strong>/<em>.

If a page has many <b> or <i> presentational tags but zero <strong>/<em>
semantic counterparts, the user is treating styling as semantics. Info
status — could be intentional (legacy, design choice).
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any,
    find_html_elements,
)


@register
class SemanticEmphasisLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130105E",
        guideline="1.3.1",
        level=Level.A,
        desc="重度使用 <b>/<i> 但缺 <strong>/<em> — 建議用語意元件表強調",
        source="extension",
    )

    _PRES = ("b", "i")
    _SEM = ("strong", "em")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            pres = sum(len(find_html_elements(parsed.tree, t)) for t in self._PRES)
            sem = sum(len(find_html_elements(parsed.tree, t)) for t in self._SEM)
        else:
            pres = len(find_jsx_elements_any(parsed.tree, self._PRES))
            sem = len(find_jsx_elements_any(parsed.tree, self._SEM))
        if pres >= 5 and sem == 0:
            yield self._issue(status="info",
                message=f"頁面使用 {pres} 個 <b>/<i> 但無 <strong>/<em> — 建議混用語意元件",
                node=parsed.tree.root_node)
