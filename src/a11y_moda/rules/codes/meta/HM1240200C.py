"""HM1240200C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class PageHasTitle(Rule):
    """HM1240200C — page needs non-empty <title>."""

    meta = RuleMeta(
        rule_id="HM1240200C",
        guideline="2.4.2",
        level=Level.A,
        desc="網頁需有標題<title>組件，且其值不得為空字串或空白",
    )

    _MSG = "每個網頁請在<head>區間使用title元素標示網頁標題。"

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        head = soup.find("head")
        titles = head.find_all("title") if isinstance(head, Tag) else []
        if not titles:
            report.add(self._issue(message=self._MSG))
            return
        for t in titles:
            if not isinstance(t, Tag) or should_skip(t):
                continue
            parent_name = t.parent.name.lower() if isinstance(t.parent, Tag) else ""
            if parent_name in ("svg", "iframe"):
                continue
            text = (t.decode_contents() or "").strip()
            if text == "":
                report.add(self._issue(message=self._MSG, snippet=truncate(str(t))))
                return
