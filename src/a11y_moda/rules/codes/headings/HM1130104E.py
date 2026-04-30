"""HM1130104E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class HeadingNestingMakesSense(Rule):
    """HM1130104E — heading hierarchy should match content nesting logically."""

    meta = RuleMeta(
        rule_id="HM1130104E",
        guideline="1.3.1",
        level=Level.A,
        desc="適當使用巢狀標頭呈現文件結構",
        source="extension",
    )

    def _check(self, soup, report, *, html, url, ctx) -> None:
        headings: list[tuple[int, str]] = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if not isinstance(h, Tag) or should_skip(h):
                continue
            text = h.get_text(strip=True)
            if not text:
                continue
            headings.append((int(h.name[1]), text[:80]))
        if len(headings) < 2:
            return
        max_seen = 0
        for lvl, text in headings:
            if max_seen and lvl > max_seen + 1:
                report.add(self._issue(
                    message=f"標題層次跳級：上一層為 h{max_seen}，但下一個是 h{lvl}（跳過 h{max_seen+1}）",
                    snippet=f"...h{max_seen} → h{lvl}: {text}", status="info"))
                return
            if lvl > max_seen:
                max_seen = lvl
