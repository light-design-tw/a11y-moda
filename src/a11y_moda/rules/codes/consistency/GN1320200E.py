"""GN1320200E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class FormBehaviorDescribed(Rule):
    """GN1320200E — form controls describe their behaviour before activation."""

    meta = RuleMeta(rule_id="GN1320200E", guideline="3.2.2", level=Level.A,
        desc="表單控制元件之行為將使網頁跳轉或變更，則在脈絡變更前需先明確描述將發生的事情",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.2.2 判斷表單控制元件（如 select onchange）觸發脈絡變更時，是否事先告知使用者。

判斷標準：
- pass：周遭有「自動跳轉」「改變後將...」等明確說明
- fail：onchange 觸發頁面跳轉或內容大幅變化但無任何提示

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        selects = [s for s in soup.find_all("select", onchange=True) if isinstance(s, Tag)]
        if not selects:
            return
        for s in selects[:2]:
            ctx_text = (s.parent.get_text(" ", strip=True) if isinstance(s.parent, Tag) else "")[:300]
            msg = f"select onchange handler: {s.get('onchange')[:120]}\nsurrounding text: {ctx_text}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"select 變更時觸發脈絡變化但未事先說明：{v[1]}",
                    snippet=truncate(str(s), 200), status="info"))
                return
