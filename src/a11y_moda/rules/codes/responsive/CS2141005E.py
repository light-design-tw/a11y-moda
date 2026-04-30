"""CS2141005E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class HorizontalScrollToggle(Rule):
    """CS2141005E — large data tables should offer a horizontal-scroll toggle."""

    meta = RuleMeta(rule_id="CS2141005E", guideline="1.4.10", level=Level.AA,
        desc="在內容內提供選項以切換到不需要用戶水平滾動以閱讀文字行的佈局",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for table in soup.find_all("table"):
            if not isinstance(table, Tag) or should_skip(table):
                continue
            cols = max((len(row.find_all(["td", "th"])) for row in table.find_all("tr")), default=0)
            if cols >= 6:
                wrapper = table.parent
                if isinstance(wrapper, Tag):
                    style = (wrapper.get("style") or "").lower()
                    cls = " ".join(wrapper.get("class") or []).lower()
                    if "overflow-x" in style or "responsive" in cls or "scroll" in cls:
                        return
                report.add(self._issue(
                    message=f"含 {cols} 欄寬表格未在容器設 overflow-x，行動裝置會強制水平捲動。",
                    snippet=truncate(str(table)[:200]),
                    status="info",
                ))
                return
