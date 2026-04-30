"""HM1130109E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class TableHeaderDataAssociation(Rule):
    """HM1130109E — table header/data association should be clear."""

    meta = RuleMeta(rule_id="HM1130109E", guideline="1.3.1", level=Level.A,
        desc="以有意義的標記來建立表格標題與資料表格的關連",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for table in soup.find_all("table"):
            if not isinstance(table, Tag) or should_skip(table):
                continue
            ths = table.find_all("th")
            if not ths:
                continue
            no_scope = [th for th in ths if not th.has_attr("scope") and not th.has_attr("id")]
            if len(no_scope) >= 2:
                report.add(self._issue(
                    message=f"表格 {len(no_scope)} 個 <th> 無 scope/id 屬性，輔助科技無法明確關聯資料儲存格。",
                    snippet=truncate(str(table)[:200]), status="info"))
                return
