"""GN1410200E rule — UI components must expose name and role."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ..._lib.tab_pattern import find_suspected_tab_groups, labels_of


@register
class TabRoleExposure(Rule):
    """GN1410200E — UI components must expose name + role to AT.

    Cross-checks the same suspected tab pattern detected by GN1240300E,
    but reports it from the role/name exposure angle (4.1.2) instead of
    focus order (2.4.3). Both rules can fire on the same group — they
    are complementary, not duplicate.
    """

    meta = RuleMeta(
        rule_id="GN1410200E",
        guideline="4.1.2",
        level=Level.A,
        desc="使用者介面元件應暴露名稱與角色（EV1120200）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for group in find_suspected_tab_groups(soup):
            labels = labels_of(group)
            cls = " ".join(group.get("class") or [])[:60]
            report.add(self._issue(
                message=(
                    f"頁籤群組「{', '.join(labels)}」未暴露角色：建議外層加 role=\"tablist\"、"
                    f"子元素加 role=\"tab\" 與 aria-selected，使語音輔具能識別此為頁籤切換而非獨立連結。"
                ),
                snippet=f"<{group.name} class=\"{cls}\"> ...",
                status="caveat",
            ))
            return
