"""GN2320300E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class ConsistentRelativeOrder(Rule):
    """GN2320300E — repeated components appear in same relative order across pages."""

    meta = RuleMeta(rule_id="GN2320300E", guideline="3.2.3", level=Level.AA,
        desc="每一次會重複出現的元件出現時，均按照相同的相對順序來呈現",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        nav_links = []
        for nav in soup.find_all("nav"):
            if isinstance(nav, Tag) and not should_skip(nav):
                texts = [a.get_text(strip=True) for a in nav.find_all("a") if isinstance(a, Tag)]
                if texts:
                    nav_links.append(texts[:10])
        if not nav_links:
            return
        prev = ctx.state.get("nav_order")
        if prev is None:
            ctx.state["nav_order"] = nav_links
            return
        if prev != nav_links:
            report.add(self._issue(
                message="此頁主導覽鏈結順序與先前頁面不一致。", status="info"))
