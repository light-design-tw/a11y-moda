"""HM3240800E rule."""
from __future__ import annotations
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip


_BREADCRUMB_CLASS_RE = re.compile(r"breadcrumb", re.IGNORECASE)
_BREADCRUMB_LABEL_RE = re.compile(r"breadcrumb|麵包屑|路徑", re.IGNORECASE)


@register
class BreadcrumbPresent(Rule):
    """HM3240800E — non-home pages should provide breadcrumb (path) navigation."""

    meta = RuleMeta(
        rule_id="HM3240800E",
        guideline="2.4.8",
        level=Level.AAA,
        desc="網頁應提供路徑連結列指明使用者目前所在位置（麵包屑）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if urlparse(url).path.strip("/") == "":
            return
        body = soup.find("body")
        if not isinstance(body, Tag):
            return
        if self._has_labelled_breadcrumb_nav(body):
            return
        if self._has_breadcrumb_class(body):
            return
        report.add(self._issue(
            message="頁面未提供麵包屑路徑導覽（nav[aria-label*=breadcrumb]、.breadcrumb 等），使用者不易辨識所在位置。",
            status="info",
        ))

    @staticmethod
    def _has_labelled_breadcrumb_nav(body: Tag) -> bool:
        for nav in body.find_all(["nav"]):
            if not isinstance(nav, Tag) or should_skip(nav):
                continue
            label = " ".join([nav.get("aria-label") or "", nav.get("aria-labelledby") or ""])
            if _BREADCRUMB_LABEL_RE.search(label) and len(nav.find_all("a")) >= 1:
                return True
        for el in body.find_all(attrs={"role": "navigation"}):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            label = el.get("aria-label") or ""
            if _BREADCRUMB_LABEL_RE.search(label) and len(el.find_all("a")) >= 1:
                return True
        return False

    @staticmethod
    def _has_breadcrumb_class(body: Tag) -> bool:
        for el in body.find_all(class_=_BREADCRUMB_CLASS_RE):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            if len(el.find_all("a")) >= 1:
                return True
        return False
