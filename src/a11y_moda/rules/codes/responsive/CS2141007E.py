"""CS2141007E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ImageMaxWidth(Rule):
    """CS2141007E — images should have max-width to avoid overflow."""

    meta = RuleMeta(rule_id="CS2141007E", guideline="1.4.10", level=Level.AA,
        desc="使用CSS最大寬度和高度容納圖像",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        for d in decls:
            if d.prop == "max-width" and "%" in d.value:
                return
        wide_imgs = []
        for img in soup.find_all("img"):
            if not isinstance(img, Tag):
                continue
            w = (img.get("width") or "").strip()
            if w and w.isdigit() and int(w) > 600:
                wide_imgs.append(img)
        if wide_imgs:
            report.add(self._issue(
                message=f"頁面含 {len(wide_imgs)} 張寬度 >600px 的圖片但未在 CSS 設 max-width:100%。",
                status="info",
            ))
