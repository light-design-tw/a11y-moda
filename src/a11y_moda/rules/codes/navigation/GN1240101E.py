"""GN1240101E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class SectionSkipLinkPresent(Rule):
    """GN1240101E — repeated content blocks should expose a skip link."""

    meta = RuleMeta(rule_id="GN1240101E", guideline="2.4.1", level=Level.A,
        desc="在重複內容的區塊開頭加入鏈結，連到該區塊結束之處",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for block in soup.find_all(["nav", "header", "aside"]):
            if not isinstance(block, Tag) or should_skip(block):
                continue
            anchors = [a for a in block.find_all("a", href=True)[:3] if isinstance(a, Tag)]
            if not anchors:
                continue
            has_skip = any((a.get("href") or "").startswith("#") for a in anchors)
            link_count = len([a for a in block.find_all("a", href=True) if isinstance(a, Tag)])
            if link_count >= 5 and not has_skip:
                report.add(self._issue(
                    message=f"<{block.name}> 含 {link_count} 個鏈結但未提供區塊內 skip link。",
                    snippet=truncate(str(block)[:200]),
                    status="info",
                ))
                return
