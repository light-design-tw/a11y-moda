"""GN1210100E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.extension_keyboard import _KEY_EQUIV


@register
class KeyboardEventCounterpart(Rule):
    """GN1210100E — interactive mouse handlers should pair with keyboard equivalents."""

    meta = RuleMeta(
        rule_id="GN1210100E",
        guideline="2.1.1",
        level=Level.A,
        desc="提供由鍵盤觸發的事件處理程式",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        focusable_natives = {"a", "button", "input", "select", "textarea", "details"}
        for mouse_evt, key_evts in _KEY_EQUIV.items():
            for el in soup.find_all(attrs={mouse_evt: True}):
                if not isinstance(el, Tag) or should_skip(el):
                    continue
                if mouse_evt == "onclick" and el.name in focusable_natives:
                    continue
                if any(el.has_attr(k) for k in key_evts):
                    continue
                report.add(self._issue(
                    message=f"<{el.name}> 使用 {mouse_evt} 但未提供鍵盤等效事件 ({'/'.join(key_evts)})。",
                    snippet=truncate(str(el), 200),
                ))
                return
