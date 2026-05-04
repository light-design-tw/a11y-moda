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

    _LIGHT_FILL = re.compile(r"^#([cdef])\1\1$|^#[cdef]{2}[cdef]{2}[cdef]{2}$|^white$")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for svg in soup.find_all("svg"):
            if not isinstance(svg, Tag) or should_skip(svg):
                continue
            # Skip SVGs whose colour follows the parent (currentColor) or is
            # controlled by CSS — static fill check can't see the final colour.
            svg_fill = (svg.get("fill") or "").lower()
            if "currentcolor" in svg_fill:
                continue
            fills: list[str] = []
            uses_current = False
            for el in svg.find_all(True):
                if not isinstance(el, Tag):
                    continue
                f = (el.get("fill") or "").lower().strip()
                if not f or f == "none":
                    continue
                if "currentcolor" in f:
                    uses_current = True
                    break
                fills.append(f)
            if uses_current or not fills:
                continue
            # Only flag when *every* visible fill is light — mixed-colour icons
            # likely have darker accent lines providing contrast.
            if all(self._LIGHT_FILL.match(f) for f in fills):
                # caveat, not info: final rendered colour depends on background +
                # CSS override. Tool can't determine pass/fail, only flag for human.
                report.add(self._issue(
                    message=f"SVG 全部 fill 為淺色（{', '.join(sorted(set(fills))[:3])}），需人工確認與背景對比。",
                    snippet=truncate(str(svg), 200),
                    status="caveat",
                ))
                return
