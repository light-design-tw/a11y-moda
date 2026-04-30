"""HM1130110E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.structure import _direct_child_of


@register
class ComplexTableAssociation(Rule):
    """HM1130110E — complex tables (multi-row/col headers) need scope or id/headers."""

    meta = RuleMeta(
        rule_id="HM1130110E",
        guideline="1.3.1",
        level=Level.A,
        desc="多重標題行列的複雜資料表格須以scope或id/headers屬性建立標題與資料儲存格之關聯",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for tbl in soup.find_all("table"):
            if not isinstance(tbl, Tag) or should_skip(tbl):
                continue
            ths = [t for t in tbl.find_all("th") if _direct_child_of(t, tbl)]
            if not ths:
                continue
            spanning = [th for th in ths if th.has_attr("colspan") or th.has_attr("rowspan")]
            if not spanning:
                continue
            for th in spanning:
                if th.has_attr("scope") or th.has_attr("id"):
                    continue
                report.add(self._issue(
                    message="複雜資料表格的合併標題格未設 scope 或 id/headers，請補上以建立標題與資料格的關聯。",
                    snippet=truncate(str(tbl)),
                ))
                return
