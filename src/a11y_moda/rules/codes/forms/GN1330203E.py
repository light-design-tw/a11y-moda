"""GN1330203E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class LabelPositioning(Rule):
    """GN1330203E — labels are placed close to their controls."""

    meta = RuleMeta(rule_id="GN1330203E", guideline="3.3.2", level=Level.A,
        desc="妥善定位描述性標籤的位置，使關連性的可預期性最大化",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        offenders = 0
        for inp in soup.find_all(["input", "select", "textarea"]):
            if not isinstance(inp, Tag):
                continue
            iid = (inp.get("id") or "").strip()
            if not iid:
                continue
            lbl = soup.find("label", attrs={"for": iid})
            if not isinstance(lbl, Tag):
                continue
            depth = 0
            cur = inp
            while isinstance(cur, Tag) and depth < 6:
                cur = cur.parent
                if isinstance(cur, Tag) and lbl in cur.descendants:
                    break
                depth += 1
            if depth >= 5:
                offenders += 1
        if offenders >= 3:
            report.add(self._issue(
                message=f"{offenders} 個 label 與其控制元件相隔 ≥5 層 DOM，建議拉近以提升關聯性。", status="info"))
