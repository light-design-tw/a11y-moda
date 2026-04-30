"""HM1110104E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class GlyphImageAlt(Rule):
    """HM1110104E — character art / emoji used as text needs alt."""

    meta = RuleMeta(rule_id="HM1110104E", guideline="1.1.1", level=Level.A,
        desc="提供字符圖案、表情符號、其他挪用文字外型作為表意功能之語言形式的替代文字",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷頁面是否將字符圖案 / 表情符號 / 特殊符號作為意義表達但缺文字替代。

判斷標準：
- pass：符號搭配文字、純裝飾無意義、或單一表情融入文意
- fail：符號獨立承載意義（如純 emoji 串、星級評分）但無文字補充

{OUTPUT_INSTRUCTIONS}"""

    _SUSPECT_RE = re.compile(r"[☀-⛿✀-➿\U0001F300-\U0001F9FF]{3,}|★+|☆+|【|】|◆|◇|●|○")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        text = soup.get_text() or ""
        m = self._SUSPECT_RE.search(text)
        if not m:
            return
        excerpt = text[max(0, m.start() - 30): m.end() + 30]
        v = judge_or_caveat(self, ctx, report, self.SYSTEM, f"text excerpt: {excerpt}")
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"字符圖案/表情符號當意義使用但缺替代：{v[1]}",
                snippet=truncate(excerpt, 200), status="info"))
