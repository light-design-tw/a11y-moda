"""GN2140400E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TextResize200(Rule):
    """GN2140400E — text should remain readable at 200% zoom (heuristic via overflow control)."""

    meta = RuleMeta(rule_id="GN2140400E", guideline="1.4.4", level=Level.AA,
        desc="使用具有支援縮放功能且容易取得的使用者代理的科技，或在頁面上提供可讓使用者變大文字尺寸到200%的控制元件",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for meta in soup.find_all("meta"):
            if not isinstance(meta, Tag):
                continue
            if (meta.get("name") or "").lower() != "viewport":
                continue
            content = (meta.get("content") or "").lower().replace(" ", "")
            if "user-scalable=no" in content or "maximum-scale=1" in content:
                report.add(self._issue(
                    message="viewport meta 阻擋使用者縮放（user-scalable=no 或 maximum-scale=1）。",
                    snippet=truncate(content, 200),
                ))
                return
