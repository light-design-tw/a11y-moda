"""GN3241302E rule (was GN2141100E/1.4.11 under 110.07; remapped to 2.4.13 for 115.11)."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FocusIndicatorAuthored(Rule):
    """GN3241302E — author should provide a visible focus indicator (2.4.13)."""

    meta = RuleMeta(rule_id="GN3241302E", guideline="2.4.13", level=Level.AAA,
        desc="使用作者提供的可見焦點指示框線",
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
