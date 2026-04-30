"""HM1240400E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, is_definitely_vague, is_standard_pattern, judge_or_caveat


@register
class AdjacentImageTextLinkClean(Rule):
    """HM1240400E (E variant) — combined adjacent img+text link reads cleanly."""

    meta = RuleMeta(rule_id="HM1240400E", guideline="2.4.4", level=Level.A,
        desc="使用鏈結文字及前後的脈絡情境來指明鏈結目的",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.4 判斷含 <img> + 文字的鏈結，組合後的無障礙名稱是否清楚。

判斷標準：
- pass：alt 與文字互補，或 alt 為空（裝飾），或 alt 與文字相同（可清晰被讀為單一名稱）
- fail：alt 與文字明顯衝突或語意不連貫

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            imgs = [i for i in a.find_all("img") if isinstance(i, Tag) and not should_skip(i)]
            if not imgs:
                continue
            text = a.get_text(strip=True)
            if not text:
                continue
            alts = [(i.get("alt") or "").strip() for i in imgs if i.has_attr("alt")]
            msg = f"link text: {text}\nimg alts: {alts}\nhref: {a.get('href')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"圖文鏈結組合不清：{v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                return
