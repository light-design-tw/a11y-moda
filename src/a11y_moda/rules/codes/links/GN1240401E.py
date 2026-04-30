"""GN1240401E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, is_definitely_vague, is_standard_pattern, judge_or_caveat


@register
class LinkPurposeFromContext(Rule):
    """GN1240401E / HM1240403E — link text + immediate context must convey purpose."""

    meta = RuleMeta(
        rule_id="GN1240401E",
        guideline="2.4.4",
        level=Level.A,
        desc="針對脈絡中的鏈結，提供描述鏈結目的的鏈結文字",
        source="extension",
    )

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.4 判斷鏈結文字（連同一句脈絡）能否讓使用者理解連結目的。

判斷標準（最低合規門檻）：
- pass：鏈結文字含具體目的（即使簡短），或脈絡能補足
- fail：純通用詞無脈絡（click here、點此、了解更多、more、here、link）
- unsure：邊界情境

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        flagged_texts: set[str] = set()
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            text = a.get_text(strip=True)
            if not text or text in flagged_texts:
                continue
            if is_standard_pattern(text):
                continue
            if is_definitely_vague(text):
                report.add(self._issue(
                    message=f"鏈結目的不明：「{text}」— 通用模糊詞",
                    snippet=truncate(str(a), 200), status="info"))
                flagged_texts.add(text)
                if len(flagged_texts) >= 3:
                    return
                continue
            if len(text) > 8:
                continue
            parent_text = (a.parent.get_text(" ", strip=True) if isinstance(a.parent, Tag) else "")[:200]
            msg = f"link text: {text}\nhref: {a.get('href')}\ncontext: {parent_text}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"鏈結目的不明：「{text}」— {v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                flagged_texts.add(text)
                if len(flagged_texts) >= 3:
                    return
