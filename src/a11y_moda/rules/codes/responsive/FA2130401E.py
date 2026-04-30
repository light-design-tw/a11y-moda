"""FA2130401E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ViewportNoLockOrientation(Rule):
    """FA2130401E — viewport meta should not lock orientation."""

    meta = RuleMeta(
        rule_id="FA2130401E",
        guideline="1.3.4",
        level=Level.AA,
        desc="由於將螢幕方向鎖定到橫向或直向視圖而導致失敗",
        source="extension",
    )

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for meta in soup.find_all("meta"):
            if not isinstance(meta, Tag):
                continue
            if (meta.get("name") or "").lower() != "viewport":
                continue
            content = (meta.get("content") or "").lower()
            if "orientation=" in content:
                report.add(self._issue(
                    message="viewport meta 鎖定 orientation，會影響橫直翻轉的使用者。",
                    snippet=truncate(content, 200),
                ))
                return
