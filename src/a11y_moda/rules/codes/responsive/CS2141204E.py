"""CS2141204E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TextContainerEmUnit(Rule):
    """CS2141204E — text containers should be sized in em so spacing scales."""

    meta = RuleMeta(rule_id="CS2141204E", guideline="1.4.12", level=Level.AA,
        desc="以em單位為單位設定文字容器的大小",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        em_count = 0
        px_count = 0
        for d in decls:
            if d.prop in ("width", "max-width", "height"):
                v = d.value.lower()
                if "em" in v or "rem" in v:
                    em_count += 1
                elif re.search(r"\dpx\b", v):
                    px_count += 1
        if px_count > 5 and em_count == 0:
            report.add(self._issue(
                message=f"文字容器尺寸全用 px ({px_count} 處)，建議混用 em/rem。",
                status="info",
            ))
