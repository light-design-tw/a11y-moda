"""HM1110103E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class LongDescNeeded(Rule):
    """HM1110103E — complex images need a longdesc / fuller description."""

    meta = RuleMeta(rule_id="HM1110103E", guideline="1.1.1", level=Level.A,
        desc="圖片無法以替代文字清晰表達時，利用長描述提供更詳盡的說明網頁網址",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷複雜圖片（圖表、流程圖、地圖）的 alt 是否需要更長的描述補充。

判斷標準：
- pass：alt 充分傳達圖片資訊，或圖片簡單不需長描述
- fail：圖片明顯複雜（多元素、多關係）但 alt 過短且未提供 longdesc / aria-describedby

{OUTPUT_INSTRUCTIONS}"""

    _SUSPECT_KW = ("圖表", "流程", "示意", "地圖", "組織", "架構", "示意圖", "chart", "diagram", "graph")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            alt = (img.get("alt") or "").strip()
            if not alt or len(alt) > 50:
                continue
            if not any(kw in alt.lower() for kw in self._SUSPECT_KW):
                continue
            if img.has_attr("longdesc") or img.has_attr("aria-describedby"):
                continue
            msg = f"alt: {alt}\nsrc: {img.get('src','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"複雜圖片 alt 過短未提供長描述：{v[1]}",
                    snippet=truncate(str(img), 200), status="info"))
                return
