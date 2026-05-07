"""GN2140400E lint — viewport meta should not block user scaling."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_BAD_PATTERNS = ("user-scalable=no", "maximum-scale=1", "maximum-scale=1.0")


@register
class ViewportScalableLint(LintRule):
    meta = RuleMeta(
        rule_id="GN2140400E",
        guideline="1.4.4",
        level=Level.AA,
        desc="viewport meta 不應阻擋使用者縮放",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        for meta in find_html_elements(parsed.tree, "meta"):
            name = get_html_attr(meta, "name")
            if name.kind != "literal" or (name.value or "").lower() != "viewport":
                continue
            content = get_html_attr(meta, "content")
            if content.kind != "literal" or not content.value:
                continue
            normalised = content.value.lower().replace(" ", "")
            if any(p in normalised for p in _BAD_PATTERNS):
                yield self._issue(status="fail",
                    message='viewport meta 阻擋使用者縮放 (user-scalable=no 或 maximum-scale=1)',
                    node=meta)
                return
