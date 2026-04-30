"""CS2141000E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class HasMediaQueries(Rule):
    """CS2141000E — page CSS should use media queries to reflow."""

    meta = RuleMeta(rule_id="CS2141000E", guideline="1.4.10", level=Level.AA,
        desc="使用媒體查詢和CSS網格重排網頁欄格",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import _fetch
        from urllib.parse import urljoin
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
        if any("@media" in blob for blob in css_blobs):
            return
        report.add(self._issue(
            message="未發現任何 @media query，響應式設計可能不足。",
            status="info",
        ))
