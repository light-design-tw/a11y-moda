"""CS1130202E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NoInlineLetterSpacing(Rule):
    """CS1130202E — letter-spacing should live in CSS, not inline style."""

    meta = RuleMeta(rule_id="CS1130202E", guideline="1.3.2", level=Level.A,
        desc="使用CSS來控制字詞內的字母間距", source="extension")

    _RE = re.compile(r"letter-spacing\s*:", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(style=True):
            if not isinstance(el, Tag):
                continue
            if self._RE.search(el.get("style") or ""):
                report.add(self._issue(
                    message="inline style 含 letter-spacing，建議移到 CSS 樣式表。",
                    snippet=truncate(str(el), 200),
                    status="info",
                ))
                return
