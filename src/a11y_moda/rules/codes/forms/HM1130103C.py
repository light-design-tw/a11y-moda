"""HM1130103C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FieldsetHasLegend(Rule):
    """HM1130103C — <fieldset> must have <legend> as first child with text."""

    meta = RuleMeta(
        rule_id="HM1130103C",
        guideline="1.3.1",
        level=Level.A,
        desc="表單控制元件需以欄位組<fieldset>組件來分群，並以說明<legend>組件來提供標題",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for f in soup.find_all("fieldset"):
            if not isinstance(f, Tag) or should_skip(f):
                continue
            children = [c for c in f.find_all(recursive=False) if isinstance(c, Tag)]
            if not children:
                report.add(self._issue(
                    message="fieldset元素具有結構性，請不要將其做為視覺效果的用途，以免影響螢幕報讀軟體的不必要的報讀結果。",
                    snippet=truncate(str(f)),
                ))
                return
            first = children[0]
            if first.name and first.name.lower() != "legend":
                report.add(self._issue(
                    message="fieldset元素區塊內的第一個子元素應為legend元素。",
                    snippet=truncate(str(f)),
                ))
                return
            if not first.get_text(strip=True):
                report.add(self._issue(
                    message="以legend元素做為fieldset元素的群組標籤，其值不可以是空值。",
                    snippet=truncate(str(first)),
                ))
                return
