"""CS1130103E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NoDeprecatedFontTag(Rule):
    """CS1130103E — text presentation should be CSS-driven, not <font>/legacy."""

    meta = RuleMeta(rule_id="CS1130103E", guideline="1.3.1", level=Level.A,
        desc="文字的視覺呈現均以CSS來控制", source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for tag in soup.find_all(["font", "basefont", "marquee", "blink"]):
            if not isinstance(tag, Tag):
                continue
            report.add(self._issue(
                message=f"使用已淘汰的 <{tag.name}> 元素呈現文字，請改用 CSS。",
                snippet=truncate(str(tag), 200),
            ))
            return
        for el in soup.find_all(attrs={"color": True}):
            if isinstance(el, Tag) and el.name not in ("hr",):
                report.add(self._issue(
                    message=f"<{el.name}> 使用 color 屬性，請改用 CSS color 屬性。",
                    snippet=truncate(str(el), 200),
                    status="info",
                ))
                return
