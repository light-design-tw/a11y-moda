"""CS1110113E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class DecorativeImageViaCss(Rule):
    """CS1110113E — decorative imagery should be CSS background, not <img>."""

    meta = RuleMeta(rule_id="CS1110113E", guideline="1.1.1", level=Level.A,
        desc="裝飾性圖片均透過CSS來置入",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        decorative = []
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            alt = (img.get("alt") or "").strip()
            if alt == "" and img.has_attr("alt"):
                decorative.append(img)
        if len(decorative) >= 5:
            report.add(self._issue(
                message=f"頁面含 {len(decorative)} 張裝飾性 <img>（empty alt），建議改用 CSS background-image。",
                status="info",
            ))
