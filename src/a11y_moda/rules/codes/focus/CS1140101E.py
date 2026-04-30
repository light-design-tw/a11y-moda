"""CS1140101E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FocusVisibleCssRule(Rule):
    """CS1140101E — at least one CSS rule must style :focus / :focus-visible."""

    meta = RuleMeta(
        rule_id="CS1140101E",
        guideline="1.4.1",
        level=Level.A,
        desc="當使用者介面元件取得焦點時，使用CSS變更其呈現方式",
        source="extension",
    )

    _FOCUS_RE = re.compile(r":focus(-visible|-within)?\b")

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        from ....css_utils import _fetch
        from urllib.parse import urljoin
        css_blobs: list[str] = []
        for s in soup.find_all("style"):
            if isinstance(s, Tag):
                css_blobs.append(s.get_text() or "")
        for el in soup.find_all(style=True):
            css_blobs.append(el.get("style") or "")
        for blob in css_blobs:
            if self._FOCUS_RE.search(blob):
                return
        for link in soup.find_all("link"):
            if not isinstance(link, Tag):
                continue
            rel = " ".join(link.get("rel") or []).lower()
            if "stylesheet" not in rel:
                continue
            href = (link.get("href") or "").strip()
            if not href:
                continue
            full = urljoin(url, href)
            if not full.startswith(("http://", "https://")):
                continue
            text = _fetch(full)
            if text and self._FOCUS_RE.search(text):
                return
        report.add(self._issue(
            message="未發現任何針對 :focus / :focus-visible 設定樣式的 CSS 規則。",
        ))
