"""GN1240300E rule — focus order on suspected tab patterns."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ..._lib.tab_pattern import find_suspected_tab_groups, labels_of


@register
class TabFocusOrder(Rule):
    """GN1240300E — interactive elements should follow content sequence.

    Surfaces suspected tab groups (filter button rows, category pills)
    that lack role=tablist/role=tab. Without those roles the group is
    traversed as N independent links instead of a single composite —
    breaking expected Tab/Arrow-key focus order for tab UIs.
    """

    meta = RuleMeta(
        rule_id="GN1240300E",
        guideline="2.4.3",
        level=Level.A,
        desc="按照內容的序列及關聯性來安排互動元件的放置順序",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for group in find_suspected_tab_groups(soup):
            labels = labels_of(group)
            cls = " ".join(group.get("class") or [])[:60]
            report.add(self._issue(
                message=(
                    f"疑似頁籤群組（{', '.join(labels)}）未使用 role=tablist / role=tab，"
                    f"鍵盤焦點順序為 N 個獨立連結而非頁籤切換，建議改採 ARIA tabs pattern。"
                ),
                snippet=f"<{group.name} class=\"{cls}\"> ...",
                status="caveat",
            ))
            return  # 一頁一個提示就夠
