"""GN1240104E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class SectionsHaveHeadings(Rule):
    """GN1240104E — sectioning elements should contain a heading."""

    meta = RuleMeta(
        rule_id="GN1240104E",
        guideline="2.4.1",
        level=Level.A,
        desc="在每一個內容區段開頭處提供標頭組件",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for sec in soup.find_all(["section", "article", "aside"]):
            if not isinstance(sec, Tag) or should_skip(sec):
                continue
            if sec.has_attr("aria-label") or sec.has_attr("aria-labelledby"):
                continue
            if not sec.find(["h1", "h2", "h3", "h4", "h5", "h6"]):
                report.add(self._issue(
                    message=f"<{sec.name}> 區段未提供標頭也未指定 aria-label。",
                    snippet=truncate(str(sec)[:200]),
                ))
                return
