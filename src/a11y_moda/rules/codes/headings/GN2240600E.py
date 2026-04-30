"""GN2240600E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class HeadingTextDescriptive(Rule):
    """GN2240600E — section headings must describe content of the section."""

    meta = RuleMeta(rule_id="GN2240600E", guideline="2.4.6", level=Level.AA,
        desc="提供描述性的標頭",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.6 判斷標頭是否描述其區段主題。

判斷標準（最低合規門檻，不要求完美或詳盡）：
- pass：標頭含主題詞、品牌名、產品名、方案名、或任何能讓使用者大致辨識區段內容的字詞
- fail：標頭與內容主題明顯衝突，或為純編號（Section 1、項目 A、Title）
- unsure：標頭簡短但主題可能成立時必選 unsure

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        candidates = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if not isinstance(h, Tag) or should_skip(h):
                continue
            text = h.get_text(strip=True)
            if not text:
                continue
            following = ""
            sib = h.find_next_sibling()
            while sib and isinstance(sib, Tag) and sib.name not in ("h1", "h2", "h3", "h4", "h5", "h6"):
                following += sib.get_text(" ", strip=True) + " "
                if len(following) > 200:
                    break
                sib = sib.find_next_sibling()
            if not following.strip():
                continue
            candidates.append((h, text, following[:200]))
            if len(candidates) >= 5:
                break
        for h, text, follow in candidates:
            msg = f"heading: {text}\ncontent below: {follow}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"標頭未描述內容：「{text}」 — {v[1]}",
                    snippet=truncate(str(h), 200), status="info"))
                return
