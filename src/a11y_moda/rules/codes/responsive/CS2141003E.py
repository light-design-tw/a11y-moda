"""CS2141003E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FormControlMaxWidth(Rule):
    """CS2141003E — form labels/inputs should adapt with max-width / flex."""

    meta = RuleMeta(rule_id="CS2141003E", guideline="1.4.10", level=Level.AA,
        desc="使用CSS寬度、最大寬度和彈性容器屬性調適標籤和輸入",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        inputs = [i for i in soup.find_all(["input", "textarea", "select"]) if isinstance(i, Tag)]
        if len(inputs) < 3:
            return
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        for d in decls:
            if d.prop in ("max-width", "width") and d.value.endswith(("%", "em", "rem", "ch")):
                return
        report.add(self._issue(
            message="頁面含表單元件但未發現相對寬度設定，行動裝置上可能溢出。",
            status="info",
        ))
