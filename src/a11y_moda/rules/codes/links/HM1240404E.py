"""HM1240404E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, is_definitely_vague, is_standard_pattern, judge_or_caveat


@register
class LinkTitleSupplements(Rule):
    """HM1240404E — title attr should add to (not duplicate) link text."""

    meta = RuleMeta(rule_id="HM1240404E", guideline="2.4.4", level=Level.A,
        desc="針對脈絡中的鏈結，用標題屬性來補充鏈結文字",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.4 判斷鏈結 title 屬性是否補充而非重複視覺文字。

判斷標準：
- pass：title 補充新資訊（如「在新分頁開啟」）或為空
- fail：title 完全等於或只是視覺文字的同義改寫

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for a in soup.find_all("a", href=True, title=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            title = (a.get("title") or "").strip()
            text = a.get_text(strip=True)
            if not title or not text:
                continue
            msg = f"link text: {text}\ntitle attr: {title}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"title 與鏈結文字重複：{v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                return
