"""HM1110108E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class ObjectFallbackComplete(Rule):
    """HM1110108E — object fallback should fully convey purpose & content."""

    meta = RuleMeta(rule_id="HM1110108E", guideline="1.1.1", level=Level.A,
        desc="提供物件的文字替代內容與非文字替代內容，且要能完整表達該物件的意義與功能",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷 <object> 的替代內容是否表達其意義與功能（不只是名稱）。

判斷標準：
- pass：替代內容含功能描述或具體說明
- fail：替代內容僅為名稱或標籤

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for el in soup.find_all("object"):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            fallback = el.get_text(" ", strip=True)
            if not fallback:
                continue
            msg = f"object data: {el.get('data','')}\ntype: {el.get('type','')}\nfallback: {fallback[:300]}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"object 替代內容不完整：{v[1]}",
                    snippet=truncate(str(el), 200), status="info"))
                return
