"""CS2141202E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class LetterSpacingControlled(Rule):
    """CS2141202E — letter-spacing must be in CSS, not hard-coded inline (similar to 202E)."""

    meta = RuleMeta(rule_id="CS2141202E", guideline="1.4.12", level=Level.AA,
        desc="使用CSS letter-spacing來控制單字內空格",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(style=True):
            if isinstance(el, Tag) and re.search(r"letter-spacing", el.get("style") or "", re.IGNORECASE):
                report.add(self._issue(
                    message="inline letter-spacing 違反 1.4.12 — 請改 CSS 樣式表，並避免絕對值。",
                    snippet=truncate(str(el), 200),
                    status="info",
                ))
                return
