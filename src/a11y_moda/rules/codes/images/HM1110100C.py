"""HM1110100C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.img_alt import _has_referenced_label


@register
class ImgAltRequired(Rule):
    """HM1110100C — <img> needs alt attribute."""

    meta = RuleMeta(
        rule_id="HM1110100C",
        guideline="1.1.1",
        level=Level.A,
        desc="圖片<img>組件需有替代文字(alt)屬性",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            snippet = truncate(str(img))
            if not img.has_attr("alt"):
                report.add(self._issue(message="img元素中，alt屬性為必要屬性。", snippet=snippet))
                return
            if img.get("src") and img.get("src") == img.get("alt"):
                report.add(self._issue(message="img元素中，alt屬性的值不可與圖片檔案名稱相同。", snippet=snippet))
                return
            if img.has_attr("usemap") and img.get("alt", "").strip() == "":
                report.add(self._issue(message="作為影像地圖的圖片元素，alt屬性不可為空值。", snippet=snippet))
                return

        for el in soup.select("[role='img']"):
            if not isinstance(el, Tag) or should_skip(el) or el.name in ("img", "svg"):
                continue
            if (el.get("aria-label") or "").strip() or (el.get("title") or "").strip() or _has_referenced_label(el, soup):
                continue
            report.add(self._issue(
                message="在非img元素使用role=img角色時，應有該角色的替代文字內容，供螢幕報讀軟體辨識。",
                snippet=truncate(str(el)),
            ))
            return
