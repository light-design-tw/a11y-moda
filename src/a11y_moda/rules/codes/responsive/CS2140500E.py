"""CS2140500E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TextSwitchControl(Rule):
    """CS2140500E — image-text-as-CSS rendering needs a toggle control."""

    meta = RuleMeta(rule_id="CS2140500E", guideline="1.4.5", level=Level.AA,
        desc="使用CSS來將文字取代成影像文字，並提供使用者介面控制元件來加以切換",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(style=True):
            if not isinstance(el, Tag):
                continue
            style = (el.get("style") or "").lower().replace(" ", "")
            if "text-indent:-" in style and "background" in style:
                report.add(self._issue(
                    message="疑似將文字替換為背景圖片但無切換控制元件。",
                    snippet=truncate(str(el), 200),
                    status="info",
                ))
                return
