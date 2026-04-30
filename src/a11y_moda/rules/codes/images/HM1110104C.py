"""HM1110104C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.img_alt import _has_referenced_label


@register
class InputImageAlt(Rule):
    """HM1110104C — <input type=image> needs non-empty alt or aria label."""

    meta = RuleMeta(
        rule_id="HM1110104C",
        guideline="1.1.1",
        level=Level.A,
        desc="型別(type)屬性值為圖片<img>之輸入<input>組件，需有替代文字(alt)屬性，且其值不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            if (inp.get("type") or "").strip().lower() != "image":
                continue
            snippet = truncate(str(inp))
            if not inp.has_attr("alt"):
                report.add(self._issue(message="型別為image的input元素，alt屬性為必要屬性。", snippet=snippet))
                return
            if inp.get("alt", "").strip():
                continue
            if (inp.get("aria-label") or "").strip() or _has_referenced_label(inp, soup):
                continue
            report.add(self._issue(
                message="型別為image的input元素，alt屬性不可以為空值，或另外提供可為螢幕報讀軟體讀取之替代文字內容。",
                snippet=snippet,
            ))
            return
