"""GN2141100E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FocusIndicatorAuthored(Rule):
    """GN2141100E — author should set high-contrast focus indicator."""

    meta = RuleMeta(rule_id="GN2141100E", guideline="1.4.11", level=Level.AA,
        desc="使用網頁作者設定的高可視焦點指示器",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from urllib.parse import urljoin
        from ....css_utils import _fetch
        css_blobs = [s.get_text() or "" for s in soup.find_all("style") if isinstance(s, Tag)]
        for link in soup.find_all("link"):
            if not isinstance(link, Tag):
                continue
            if "stylesheet" not in " ".join(link.get("rel") or []).lower():
                continue
            href = (link.get("href") or "").strip()
            if not href:
                continue
            full = urljoin(url, href)
            if full.startswith(("http://", "https://")):
                css_blobs.append(_fetch(full))
        joined = "\n".join(css_blobs)
        if not re.search(r":focus(-visible)?\s*\{[^}]*(outline|box-shadow|border|background)", joined, re.IGNORECASE | re.DOTALL):
            report.add(self._issue(
                message="未發現作者設定的 :focus 視覺樣式（outline/box-shadow/border/background）。",
                status="info",
            ))
