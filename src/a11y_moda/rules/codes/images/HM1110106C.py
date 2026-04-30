"""HM1110106C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ImgEmptyAltNoTitle(Rule):
    """HM1110106C — img with empty alt must not carry title/aria-* (decorative)."""

    meta = RuleMeta(
        rule_id="HM1110106C",
        guideline="1.1.1",
        level=Level.A,
        desc="替代文字(alt)屬性值為空字串的圖片<img>組件，不得有標題(title)屬性",
    )

    _MSG = (
        "圖片做為裝飾用途時，img元素的alt屬性應保持空值，"
        "並不可以使用title屬性或任何aria-*屬性，以免螢幕報讀軟體讀取不必要之資訊。"
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            if not img.has_attr("alt") or img.get("alt", "").strip() != "":
                continue
            if any(img.has_attr(a) for a in ("title", "aria-label", "aria-labelledby")):
                report.add(self._issue(message=self._MSG, snippet=truncate(str(img))))
                return
