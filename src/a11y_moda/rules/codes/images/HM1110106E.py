"""HM1110106E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class SubmitButtonImageAlt(Rule):
    """HM1110106E — input[type=image] / image button needs descriptive alt."""

    meta = RuleMeta(rule_id="HM1110106E", guideline="1.1.1", level=Level.A,
        desc="作為「送出」按鈕之用的圖片需提供替代文字",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷 <input type=image> 的 alt 是否傳達按鈕功能。

判斷標準：
- pass：alt 含動作詞或具體功能名
- fail：alt 為「button」「圖片」「submit」等通用詞或為檔名

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for inp in soup.find_all("input", type="image"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            alt = (inp.get("alt") or "").strip()
            if not alt:
                continue
            msg = f"input type=image alt: {alt}\nsrc: {inp.get('src','')}\nname: {inp.get('name','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"送出按鈕圖片 alt 不適切：{v[1]}",
                    snippet=truncate(str(inp), 200), status="info"))
                return
