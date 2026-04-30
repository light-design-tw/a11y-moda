"""GN2140401E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FluidLayout(Rule):
    """GN2140401E — fluid layout / no content loss when text resized."""

    meta = RuleMeta(rule_id="GN2140401E", guideline="1.4.4", level=Level.AA,
        desc="使用流動版面設計，或者確認當文字尺寸變更而文字容器尺寸並未變更時，不會喪失任何內容或功能",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        fluid = sum(1 for d in decls if d.prop in ("width", "max-width") and ("%" in d.value or "vw" in d.value))
        fixed = sum(1 for d in decls if d.prop == "width" and re.search(r"\dpx\b", d.value))
        if fixed > fluid * 3 and fixed > 10:
            report.add(self._issue(
                message=f"width 設定大量使用 px ({fixed} 處 vs {fluid} 流動)，文字放大可能溢出。",
                status="info",
            ))
