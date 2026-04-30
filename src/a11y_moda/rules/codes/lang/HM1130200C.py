"""HM1130200C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class BidiTextLang(Rule):
    """HM1130200C — dir=rtl elements should expose lang nearby."""

    meta = RuleMeta(
        rule_id="HM1130200C",
        guideline="1.3.2",
        level=Level.A,
        desc="混用多國語言內容，出現已知文字走向不同的內容時，需有萬國碼的右至左標記(RLM)或左至右標記(LRM)，或以行內組件搭配使用文字方向(dir)屬性",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for el in soup.select("[dir]"):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            if (el.get("dir") or "").strip().lower() != "rtl" or el.has_attr("lang"):
                continue
            siblings_have_lang = False
            for sib in (el.find_previous_sibling(), el.find_next_sibling()):
                if isinstance(sib, Tag) and sib.has_attr("lang"):
                    siblings_have_lang = True
                    break
            if siblings_have_lang or any(isinstance(c, Tag) and c.has_attr("lang") for c in el.find_all(recursive=False)):
                continue
            report.add(self._issue(
                message="網頁內如有使用不同閱讀方向之文字內容時，請使用dir屬性標示閱讀方向並以lang屬性標示該段文字之語系。",
                snippet=truncate(str(el)),
            ))
            return
