"""GN1130200E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class MeaningfulSequence(Rule):
    """GN1130200E — content is in a meaningful reading order."""

    meta = RuleMeta(rule_id="GN1130200E", guideline="1.3.2", level=Level.A,
        desc="將內容依據有意義的序列來排序",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.3.2 判斷頁面文字 DOM 順序是否流暢可閱讀。

判斷標準（嚴格遵守，因易主觀）：
- pass：閱讀順序流暢，主題連貫
- fail：明顯主題跳躍、片段斷裂、區塊順序不合常理
- unsure：邊界情境必選 unsure

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        text = body.get_text(" ", strip=True)
        if len(text) < 200:
            return
        excerpt = text[:1500]
        v = judge_or_caveat(self, ctx, report, self.SYSTEM, excerpt)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"DOM 順序的閱讀流程疑有問題：{v[1]}",
                snippet=truncate(excerpt, 300), status="info"))
