"""HM1130107E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class TableSemantics(Rule):
    """HM1130107E — tables should be used for tabular data, not layout."""

    meta = RuleMeta(rule_id="HM1130107E", guideline="1.3.1", level=Level.A,
        desc="使用表格標記來呈現表格資訊",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for table in soup.find_all("table"):
            if not isinstance(table, Tag):
                continue
            role = (table.get("role") or "").lower()
            if role in ("presentation", "none"):
                continue
            ths = table.find_all("th")
            rows = table.find_all("tr")
            if not ths and len(rows) >= 3:
                report.add(self._issue(
                    message=f"表格 ({len(rows)} 列) 無任何 <th> 也未標 role=presentation，疑似排版用表格。",
                    snippet=truncate(str(table)[:200]), status="info"))
                return
