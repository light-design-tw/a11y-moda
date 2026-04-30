"""CS2141006E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class StickyHeaderUnstick(Rule):
    """CS2141006E — sticky header/footer should release on small viewports."""

    meta = RuleMeta(rule_id="CS2141006E", guideline="1.4.10", level=Level.AA,
        desc="使用媒體查詢來解除粘滯的頁首/頁尾",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        sticky_count = sum(1 for d in decls if d.prop == "position" and d.value.lower() in ("sticky", "fixed"))
        if sticky_count > 0:
            css_blobs = [s.get_text() or "" for s in soup.find_all("style") if isinstance(s, Tag)]
            joined = "\n".join(css_blobs).lower()
            if "@media" in joined and "position" in joined and ("static" in joined or "relative" in joined):
                return
            report.add(self._issue(
                message=f"頁面含 {sticky_count} 處 sticky/fixed 定位但未在小螢幕用 @media 解除。",
                status="info",
            ))
