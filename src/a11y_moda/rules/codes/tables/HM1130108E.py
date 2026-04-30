"""HM1130108E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class TableCaptionDescriptive(Rule):
    """HM1130108E — data tables should have caption + summary describing intent."""

    meta = RuleMeta(rule_id="HM1130108E", guideline="1.3.1", level=Level.A,
        desc="以有意義的標記來提供資料表格的概觀",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.3.1 判斷資料表格的 caption 是否描述表格主旨。

判斷標準：
- pass：caption 含主題詞或表格目的描述
- fail：caption 為純通用詞（「表格」「資料」「Table」）或編號

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for table in soup.find_all("table"):
            if not isinstance(table, Tag) or should_skip(table):
                continue
            rows = table.find_all("tr")
            cols = max((len(r.find_all(["td", "th"])) for r in rows), default=0)
            if len(rows) < 5 or cols < 4:
                continue
            cap = table.find("caption")
            if cap and cap.get_text(strip=True):
                msg = f"caption: {cap.get_text(strip=True)}\nrows: {len(rows)}, cols: {cols}"
                v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
                if v is None:
                    return
                if v[0] == "fail":
                    report.add(self._issue(
                        message=f"表格 caption 不夠描述性：{v[1]}",
                        snippet=truncate(str(cap), 200), status="info"))
                    return
            else:
                report.add(self._issue(
                    message=f"資料表 ({len(rows)}列×{cols}欄) 缺 <caption>，無法快速理解表格主旨。",
                    snippet=truncate(str(table)[:200]), status="info"))
                return
