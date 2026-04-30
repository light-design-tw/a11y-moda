"""FA1250202E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class MouseDownActivation_FA(Rule):
    """FA1250202E — same root cause as GN1250201E but logged separately for traceability."""

    meta = RuleMeta(rule_id="FA1250202E", guideline="2.5.2", level=Level.A,
        desc="由於向下事件啟動一個控制元件而導致成功準則2.5.2失敗",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(attrs={"onmousedown": True}):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            handler = (el.get("onmousedown") or "").strip()
            if handler and "return false" not in handler:
                if re.search(r"\(\)|location|window\.|submit|navigate", handler):
                    report.add(self._issue(
                        message="onmousedown 直接執行啟動行為，無法由使用者取消。",
                        snippet=truncate(str(el), 200),
                    ))
                    return
