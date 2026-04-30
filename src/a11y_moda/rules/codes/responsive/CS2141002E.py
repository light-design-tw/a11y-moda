"""CS2141002E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class WordBreakSafe(Rule):
    """CS2141002E — long URLs/strings should break to avoid horizontal scroll."""

    meta = RuleMeta(rule_id="CS2141002E", guideline="1.4.10", level=Level.AA,
        desc="針對長網址跟文字字符串可以進行重排",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        for d in decls:
            if d.prop in ("word-break", "overflow-wrap", "word-wrap") and d.value.lower() not in ("normal", ""):
                return
        text = soup.get_text() or ""
        if any(len(token) > 60 for token in text.split()):
            report.add(self._issue(
                message="頁面含長字串但未發現 word-break / overflow-wrap CSS 規則。",
                status="info",
            ))
