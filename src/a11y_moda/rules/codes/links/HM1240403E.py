"""HM1240403E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, is_definitely_vague, is_standard_pattern, judge_or_caveat


@register
class LinkTextDescribesPurpose(Rule):
    """HM1240403E — link text alone should describe link purpose."""

    meta = RuleMeta(rule_id="HM1240403E", guideline="2.4.4", level=Level.A,
        desc="提供描述鏈結組件鏈結目的的鏈結文字",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.4 判斷鏈結文字「單獨」是否能讓使用者理解連結目的（不依賴周圍脈絡）。

判斷標準：
- pass：含具體名詞、動詞、或可識別的標的（即使簡短）
- fail：純通用詞（點此、了解更多、more、click here、link、here、按鈕）或純標點
- unsure：邊界

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
                    message=f"鏈結文字單獨無法理解：「{text}」— 通用模糊詞",
                    snippet=truncate(str(a), 200), status="info"))
                flagged_texts.add(text)
                if len(flagged_texts) >= 3:
                    return
                continue
            if len(text) > 10:
                continue
            msg = f"link text alone: {text}\nhref: {a.get('href')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"鏈結文字單獨無法理解：「{text}」 — {v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                flagged_texts.add(text)
                if len(flagged_texts) >= 3:
                    return
