"""HM1110102E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class ImageMapAreaAltAppropriate(Rule):
    """HM1110102E — area alt should describe area's purpose, not generic."""

    meta = RuleMeta(rule_id="HM1110102E", guideline="1.1.1", level=Level.A,
        desc="提供影像地圖區域的替代文字，並要能確實表達這些地圖區域的功能與目的",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷 <area> 的 alt 是否描述該地圖區域的目的或目的地。

判斷標準：
- pass：alt 含可識別的目的或目的地名稱
- fail：alt 為通用詞（area、image）、檔名、或與 href 完全無關

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for a in soup.find_all("area"):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            alt = (a.get("alt") or "").strip()
            if not alt:
                continue
            msg = f"alt: {alt}\nhref: {a.get('href','')}\ncoords: {a.get('coords','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"area alt 不適切：{v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                return
