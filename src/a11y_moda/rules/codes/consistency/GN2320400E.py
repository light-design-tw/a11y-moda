"""GN2320400E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class ConsistentLabels(Rule):
    """GN2320400E — same-function controls use the same label across pages."""

    meta = RuleMeta(rule_id="GN2320400E", guideline="3.2.4", level=Level.AA,
        desc="按照具有相同功能的內容，一致地使用標籤、名稱、替代文字",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        prev = ctx.state.setdefault("label_by_href", {})
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = (a.get("href") or "").strip()
            text = a.get_text(strip=True)
            if not href or not text or href.startswith("#"):
                continue
            existing = prev.get(href)
            if existing is None:
                prev[href] = text
            elif existing != text and len(existing) > 3 and len(text) > 3:
                report.add(self._issue(
                    message=f"同一 href「{href}」在不同頁面使用不同文字：「{existing}」 vs 「{text}」", status="info"))
                return
