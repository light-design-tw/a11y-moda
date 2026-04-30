"""GN1250201E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class MouseDownActivation(Rule):
    """GN1250201E — activation should fire on mouseup (or click), not mousedown."""

    meta = RuleMeta(
        rule_id="GN1250201E",
        guideline="2.5.2",
        level=Level.A,
        desc="使用網頁規範原生控制元件來確保在向上事件發生時可觸發功能",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for el in soup.find_all(attrs={"onmousedown": True}):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            handler = (el.get("onmousedown") or "").strip()
            if handler and handler not in ("return false;", "return false"):
                report.add(self._issue(
                    message="使用 onmousedown 啟動行為，建議改用 onmouseup / onclick 以允許取消。",
                    snippet=truncate(str(el), 200),
                ))
                return
