"""GN1320100E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FocusNoContextChange(Rule):
    """GN1320100E — focus must not trigger context changes (location/submit/window)."""

    meta = RuleMeta(
        rule_id="GN1320100E",
        guideline="3.2.1",
        level=Level.A,
        desc="物件單純取得焦點時不要觸發脈絡變更，等使用者啟動該物件後才觸發脈絡變更",
        source="extension",
    )

    _BAD = re.compile(r"location\.(href|replace|assign)|window\.open|\.submit\(|history\.(push|replace)")

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for el in soup.find_all(attrs={"onfocus": True}):
            if not isinstance(el, Tag):
                continue
            handler = (el.get("onfocus") or "")
            if self._BAD.search(handler):
                report.add(self._issue(
                    message="onfocus 處理函式包含會變更脈絡的呼叫，請改在使用者實際啟動時觸發。",
                    snippet=truncate(handler, 200),
                ))
                return
