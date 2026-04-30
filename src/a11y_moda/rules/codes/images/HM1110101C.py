"""HM1110101C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.img_alt import _has_referenced_label


@register
class ImageMapAreaAlt(Rule):
    """HM1110101C — <area> inside <map> needs non-empty alt."""

    meta = RuleMeta(
        rule_id="HM1110101C",
        guideline="1.1.1",
        level=Level.A,
        desc="影像地圖<map>的區域<area>組件需有替代文字(alt)屬性，且其值不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for m in soup.find_all("map"):
            if not isinstance(m, Tag) or should_skip(m):
                continue
            for a in m.find_all("area"):
                if not isinstance(a, Tag) or should_skip(a):
                    continue
                snippet = truncate(str(a))
                if not a.has_attr("alt"):
                    report.add(self._issue(message="影像地圖裡的area元素中，alt屬性為必要屬性。", snippet=snippet))
                    return
                if a.get("alt", "").strip():
                    continue
                has_aria = (a.get("aria-label") or "").strip() != "" or _has_referenced_label(a, soup)
                if has_aria:
                    continue
                report.add(self._issue(
                    message="影像地圖裡的area元素中，alt屬性不可為空值，或另外提供可為螢幕報讀軟體讀取之替代文字內容。",
                    snippet=snippet,
                ))
                return
