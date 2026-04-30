"""CS1110114E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NoSpacerImage(Rule):
    """CS1110114E — no spacer GIFs / placeholder images for layout."""

    meta = RuleMeta(rule_id="CS1110114E", guideline="1.1.1", level=Level.A,
        desc="使用CSS方塊模型來處理版面設計，不要用佔位圖片",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for img in soup.find_all("img"):
            if not isinstance(img, Tag):
                continue
            src = (img.get("src") or "").lower()
            w = (img.get("width") or "").strip()
            h = (img.get("height") or "").strip()
            if "spacer" in src or "blank.gif" in src or "1x1" in src or "pixel.gif" in src:
                report.add(self._issue(
                    message="疑似 spacer 圖片用於版面，請改用 CSS。",
                    snippet=truncate(str(img), 200),
                ))
                return
            if (w in ("1", "0") or h in ("1", "0")) and src.endswith(".gif"):
                report.add(self._issue(
                    message="1x1 透明 GIF 用於版面，請改用 CSS。",
                    snippet=truncate(str(img), 200),
                ))
                return
