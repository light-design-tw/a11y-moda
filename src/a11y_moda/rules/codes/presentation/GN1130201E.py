"""GN1130201E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class BidiUnicodeMarks(Rule):
    """GN1130201E — RLM/LRM unicode markers used for nested directionality."""

    meta = RuleMeta(rule_id="GN1130201E", guideline="1.3.2", level=Level.A,
        desc="使用萬國碼的右至左標記(RLM)或左至右標記(LRM)來即席混用文字走向",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        text = soup.get_text() or ""
        has_rtl = bool(re.search(r"[֐-׿؀-ۿ܀-ݏ]", text))
        if not has_rtl:
            return
        has_bidi_mark = any(c in text for c in "‎‏‪‫‬‭‮")
        has_dir = bool(soup.find(attrs={"dir": True}))
        if not has_bidi_mark and not has_dir:
            report.add(self._issue(
                message="頁面含 RTL 文字但未使用 dir 屬性或 RLM/LRM unicode 標記。",
            ))
