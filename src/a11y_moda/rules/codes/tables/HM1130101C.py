"""HM1130101C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.structure import _direct_child_of


@register
class TableScopeOrId(Rule):
    """HM1130101C — data tables need scope or id/headers association."""

    meta = RuleMeta(
        rule_id="HM1130101C",
        guideline="1.3.1",
        level=Level.A,
        desc="使用範疇(scope)屬性，來建立表格行列標題儲存格與資料儲存格之間的關連",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for tbl in soup.find_all("table"):
            if not isinstance(tbl, Tag) or should_skip(tbl):
                continue
            ths = [t for t in tbl.find_all("th") if _direct_child_of(t, tbl)]
            if not ths:
                continue
            for th in ths:
                if th.has_attr("scope") or th.has_attr("id"):
                    continue
                if th.has_attr("colspan") or th.has_attr("rowspan"):
                    report.add(self._issue(
                        message="資料表格的如有行、列標題並存或複數行、列標題與合併資料格時，請使用scope屬性標示關聯範圍。",
                        snippet=truncate(str(tbl)),
                    ))
                    return
