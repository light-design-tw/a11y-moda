"""CS1110113E lint — too many decorative <img alt=""> suggests using CSS bg."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr


@register
class DecorativeImgViaCssLint(LintRule):
    meta = RuleMeta(
        rule_id="CS1110113E",
        guideline="1.1.1",
        level=Level.A,
        desc="多張裝飾性 <img alt=\"\"> 建議改用 CSS background-image",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        decorative = []
        if parsed.language == "html":
            for img in find_html_elements(parsed.tree, "img"):
                alt = get_html_attr(img, "alt")
                if alt.kind == "empty":
                    decorative.append(img)
        else:
            for img in find_jsx_elements(parsed.tree, "img"):
                alt = get_attr(img, "alt")
                if alt.kind == "empty":
                    decorative.append(img)
        if len(decorative) >= 5:
            yield self._issue(status="info",
                message=f'頁面含 {len(decorative)} 張裝飾性 <img alt=""> — 建議改用 CSS background-image',
                node=decorative[0])
