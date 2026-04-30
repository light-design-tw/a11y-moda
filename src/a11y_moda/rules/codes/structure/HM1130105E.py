"""HM1130105E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class SemanticEmphasisMarkup(Rule):
    """HM1130105/106E — strong/em should be used for semantic emphasis (not just b/i)."""

    meta = RuleMeta(rule_id="HM1130105E", guideline="1.3.1", level=Level.A,
        desc="使用語意組件來標記強調的文字或特殊文字",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        b_count = len(soup.find_all(["b", "i"]))
        sem_count = len(soup.find_all(["strong", "em"]))
        if b_count >= 5 and sem_count == 0:
            report.add(self._issue(
                message=f"頁面使用 {b_count} 個 <b>/<i> 但無 <strong>/<em> 語意元件，建議混用以表強調語意。", status="info"))
