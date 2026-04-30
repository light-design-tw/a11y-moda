"""HM1240400C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class AdjacentImgTextLink(Rule):
    """HM1240400C — adjacent img+text in same <a>: img.alt must not equal link text."""

    meta = RuleMeta(
        rule_id="HM1240400C",
        guideline="2.4.4",
        level=Level.A,
        desc="連往相同資源的毗鄰圖片與文字，其由替代文字及文字內容產生之鏈結文字只能有一份",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            if not (a.get("href") or "").strip():
                continue
            link_text = a.get_text().strip()
            if not link_text:
                continue
            for img in a.find_all("img"):
                if not isinstance(img, Tag) or should_skip(img):
                    continue
                alt = (img.get("alt") or "").strip()
                if alt and alt == link_text:
                    report.add(self._issue(
                        message="當文字與圖片同時做為一個超連結時，圖片的替代文字可以留空，或不可與連結文字相同。",
                        snippet=truncate(str(a)),
                    ))
                    return
