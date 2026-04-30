"""HM1240402E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, is_definitely_vague, is_standard_pattern, judge_or_caveat


@register
class CombineSameTargetLinks(Rule):
    """HM1240402E — same-href adjacent img+text should be a single combined link."""

    meta = RuleMeta(rule_id="HM1240402E", guideline="2.4.4", level=Level.A,
        desc="合併相同資源的毗鄰圖片與文字鏈結",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        offenders = []
        for parent in soup.find_all(True):
            if not isinstance(parent, Tag):
                continue
            anchors = [c for c in parent.find_all("a", href=True, recursive=False) if isinstance(c, Tag)]
            for i in range(len(anchors) - 1):
                a, b = anchors[i], anchors[i + 1]
                if (a.get("href") or "") != (b.get("href") or ""):
                    continue
                if not a.find("img") and b.get_text(strip=True):
                    offenders.append((a, b))
                elif a.get_text(strip=True) and b.find("img"):
                    offenders.append((a, b))
                if len(offenders) >= 3:
                    break
        if not offenders:
            return
        a, b = offenders[0]
        report.add(self._issue(
            message=f"相同 href 連續兩個鏈結（共 {len(offenders)} 對）— 建議合併避免重複報讀。",
            snippet=truncate(f"{a}\n{b}", 300), status="info"))
