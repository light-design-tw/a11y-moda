"""HM1110105E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class ObjectAltAppropriate(Rule):
    """HM1110105E — non-text content (object/embed/applet) needs meaningful fallback."""

    meta = RuleMeta(rule_id="HM1110105E", guideline="1.1.1", level=Level.A,
        desc="圖片以外的非文字內容需要有替代文字或長描述",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷 <object>/<embed>/<applet> 的替代文字是否描述嵌入內容。

判斷標準：
- pass：替代文字含具體描述
- fail：替代文字為空、純物件名（object、embed）、或檔名

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for el in soup.find_all(["object", "embed", "applet"]):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            fallback = el.get_text(strip=True)
            data_src = el.get("data") or el.get("src") or ""
            if not fallback and not el.get("title"):
                continue
            msg = f"tag: <{el.name}>\nsrc/data: {data_src}\nfallback text: {fallback or el.get('title','')}\ntype: {el.get('type','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"<{el.name}> 替代內容不適切：{v[1]}",
                    snippet=truncate(str(el), 200), status="info"))
                return
