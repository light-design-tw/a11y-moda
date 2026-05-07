"""GN1130201E lint — pages with RTL text should use dir attribute or RLM/LRM unicode marks."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_RTL_RE = re.compile(r"[֐-׿؀-ۿ܀-ݏ]")
_BIDI_MARKS = "‎‏‪‫‬‭‮"


@register
class BidiUnicodeMarksLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1130201E",
        guideline="1.3.2",
        level=Level.A,
        desc="頁面含 RTL 文字但未使用 dir 或 RLM/LRM unicode 標記",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        text = parsed.source.decode("utf-8", errors="replace")
        if not _RTL_RE.search(text):
            return
        if any(c in text for c in _BIDI_MARKS):
            return
        # Any element with dir attribute?
        for el in find_html_elements(parsed.tree):
            if get_html_attr(el, "dir").kind != "missing":
                return
        bodies = find_html_elements(parsed.tree, "body")
        target = bodies[0] if bodies else parsed.tree.root_node
        yield self._issue(status="fail",
            message="頁面含 RTL 文字但未使用 dir 屬性或 RLM/LRM unicode 標記",
            node=target)
