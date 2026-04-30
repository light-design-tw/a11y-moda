"""AR3130600E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


_LANDMARK_TAGS = ["main", "header", "nav", "aside", "footer", "section"]
_LANDMARK_ROLES = {"main", "banner", "navigation", "contentinfo", "complementary", "search", "region"}


@register
class PageHasLandmark(Rule):
    """AR3130600E — page should expose at least one landmark for assistive tech."""

    meta = RuleMeta(
        rule_id="AR3130600E",
        guideline="1.3.1",
        level=Level.AAA,
        desc="使用ARIA標誌(landmark)或HTML5語意標籤標示網頁主要區塊",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        if body.find(_LANDMARK_TAGS):
            return
        for el in body.find_all(attrs={"role": True}):
            if not isinstance(el, Tag):
                continue
            roles = (el.get("role") or "").lower().split()
            if any(r in _LANDMARK_ROLES for r in roles):
                return
        report.add(self._issue(
            message="頁面未使用任何 HTML5 landmark（main/header/nav/aside/footer/section）或 ARIA landmark role，輔助科技難以辨識主要區塊。",
        ))
