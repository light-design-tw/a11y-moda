"""CS1130202E lint — inline `style="letter-spacing: ..."` should move to CSS."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr


_RE = re.compile(r"letter-spacing\s*:", re.IGNORECASE)


@register
class InlineLetterSpacingLint(LintRule):
    meta = RuleMeta(
        rule_id="CS1130202E",
        guideline="1.3.2",
        level=Level.A,
        desc="inline style 含 letter-spacing — 建議移至 CSS 樣式表",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                style = get_html_attr(el, "style")
                if style.kind == "literal" and style.value and _RE.search(style.value):
                    yield self._issue(status="info",
                        message="inline style 含 letter-spacing — 建議移至 CSS 樣式表",
                        node=el)
                    return
            return

        # JSX style is dict: style={{ letterSpacing: '0.1em' }} (camelCase). Detect literal.
        for el in find_jsx_elements(parsed.tree):
            style = get_attr(el, "style")
            if style.kind == "dynamic" and style.raw and "letterSpacing" in style.raw:
                yield self._issue(status="info",
                    message="inline style 含 letterSpacing — 建議移至 CSS 樣式表",
                    node=el)
                return
            # Check string-form style="letter-spacing: ..." for raw HTML-style JSX
            if style.kind == "literal" and style.value and _RE.search(style.value):
                yield self._issue(status="info",
                    message="inline style 含 letter-spacing — 建議移至 CSS 樣式表",
                    node=el)
                return
