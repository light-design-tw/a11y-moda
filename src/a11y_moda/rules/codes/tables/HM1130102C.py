"""HM1130102C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.structure import _direct_child_of


@register
class TableHeadersIdMatch(Rule):
    """HM1130102C — id/headers attribute pairs must reference each other."""

    meta = RuleMeta(
        rule_id="HM1130102C",
        guideline="1.3.1",
        level=Level.A,
        desc="使用對應識別碼(id)與標頭(headers)屬性，來建立表格行列標題儲存格與資料儲存格之間的關連",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for tbl in soup.find_all("table"):
            if not isinstance(tbl, Tag) or should_skip(tbl):
                continue
            ths = [t for t in tbl.find_all("th") if _direct_child_of(t, tbl)]
            tds = [t for t in tbl.find_all("td") if _direct_child_of(t, tbl)]
            if not ths and any(td.has_attr("headers") for td in tds):
                ids = {td.get("id", "").strip() for td in tds if td.has_attr("id")}
                ref = set()
                for td in tds:
                    if td.has_attr("headers"):
                        ref.update(h.strip() for h in (td.get("headers") or "").split())
                if ids & ref:
                    report.add(self._issue(
                        message="排版表格請不要使用id/headers屬性。",
                        snippet=truncate(str(tbl)),
                    ))
                    return
            seen: set[str] = set()
            id_list: list[str] = []
            for th in ths:
                if not th.has_attr("id"):
                    continue
                v = (th.get("id") or "").strip()
                if v == "":
                    report.add(self._issue(message="行列標題格之id屬性，其值不可以是空值。", snippet=truncate(str(tbl))))
                    return
                if v in seen:
                    report.add(self._issue(message="行列標題格之id屬性，其值不可以重複。", snippet=truncate(str(tbl))))
                    return
                seen.add(v)
                id_list.append(v)
            if not id_list:
                continue
            headers_refs: set[str] = set()
            for cell in ths + tds:
                if cell.has_attr("headers"):
                    headers_refs.update(h.strip() for h in (cell.get("headers") or "").split())
            unmatched = [i for i in id_list if i not in headers_refs]
            if unmatched and not all(th.has_attr("scope") for th in ths):
                report.add(self._issue(
                    message="具有複雜或不規則的行、列標題的資料表格，請以id/headers屬性建立標題與資料儲存格之間的關聯。",
                    snippet=truncate(str(tbl)),
                ))
                return
