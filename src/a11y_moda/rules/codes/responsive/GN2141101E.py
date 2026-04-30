"""GN2141101E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class IconContrast(Rule):
    """GN2141101E — icons should have ≥3:1 contrast (heuristic via SVG fills)."""

    meta = RuleMeta(rule_id="GN2141101E", guideline="1.4.11", level=Level.AA,
        desc="確保圖示的對比度為3：1",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for svg in soup.find_all("svg"):
            if not isinstance(svg, Tag) or should_skip(svg):
                continue
            for el in svg.find_all(True):
                if not isinstance(el, Tag):
                    continue
                fill = (el.get("fill") or "").lower()
                if re.match(r"#([cdef])\1\1", fill) or re.match(r"#[cdef]{2}[cdef]{2}[cdef]{2}", fill):
                    report.add(self._issue(
                        message=f"SVG icon 含淺色 fill={fill}，對比度可能不足。",
                        snippet=truncate(str(el), 200),
                        status="info",
                    ))
                    return
