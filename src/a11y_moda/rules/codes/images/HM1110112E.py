"""HM1110112E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class DecorativeImgAltCorrect(Rule):
    """HM1110112E — decorative img must use empty alt without title attr."""

    meta = RuleMeta(rule_id="HM1110112E", guideline="1.1.1", level=Level.A,
        desc="對於輔助科技應當要忽略的圖片，使用空字串作為替代文字，並且不可使用標題屬性",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷一張空 alt 的 <img> 是否真的純裝飾。

判斷標準（嚴格遵守，因易主觀）：
- pass：圖片明顯純裝飾（背景、紋理、與內文重複的視覺輔助）
- fail：周遭脈絡明確暗示圖片承載重要資訊（如人物頭像、商品圖、流程圖）但 alt 為空
- unsure：無法從脈絡判斷時必選 unsure（不要硬判 fail）

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        candidates = []
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            if not img.has_attr("alt") or (img.get("alt") or "").strip() != "":
                continue
            parent_text = (img.parent.get_text(" ", strip=True) if isinstance(img.parent, Tag) else "")[:200]
            candidates.append((img, parent_text))
            if len(candidates) >= _SAMPLE_LIMIT:
                break
        for img, ctxt in candidates:
            msg = f"src: {img.get('src','')}\nalt: (empty)\nsurrounding: {ctxt or '(none)'}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"標 alt='' 但疑似帶資訊：{v[1]}",
                    snippet=truncate(str(img), 200), status="info"))
                return
