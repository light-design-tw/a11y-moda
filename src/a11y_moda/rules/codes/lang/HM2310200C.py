"""HM2310200C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class LangSwitch(Rule):
    """HM2310200C — inline lang attributes in <body> must be non-empty and differ from <html lang>."""

    meta = RuleMeta(
        rule_id="HM2310200C",
        guideline="3.1.2",
        level=Level.AA,
        desc="網頁內容中，使用不同人類語言的內容區段，必須以合於語意的組件標記，該組件並要有語言(lang)屬性",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        root = soup.find("html")
        if not isinstance(root, Tag):
            return
        page_lang = (root.get("lang") or "").strip()
        if not page_lang:
            return
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        for el in body.select("[lang]"):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            lang = (el.get("lang") or "").strip()
            if lang == "":
                report.add(self._issue(
                    message="宣告為不同語系的文字內容，其語系宣告值不可為空值。",
                    snippet=truncate(str(el)),
                ))
                return
            if lang == page_lang:
                report.add(self._issue(
                    message="宣告為不同語系的文字內容，其語系宣告值不可與網頁宣告相同。",
                    snippet=truncate(str(el)),
                ))
                return
