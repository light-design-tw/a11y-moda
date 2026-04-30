"""HM1310100C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class HtmlHasLang(Rule):
    """HM1310100C — <html> needs lang attribute."""

    meta = RuleMeta(
        rule_id="HM1310100C",
        guideline="3.1.1",
        level=Level.A,
        desc="網頁根組件<html>需有語言(lang)屬性，且其值必須合於規範，不得為空字串或空白",
    )

    _MSG = "網頁必須在html元素中使用lang屬性宣告該網頁正確的語系。"

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        root = soup.find("html")
        if not isinstance(root, Tag):
            return
        lang = (root.get("lang") or "").strip()
        if lang:
            return
        report.add(self._issue(message=self._MSG, snippet=truncate(str(root))[:60]))
