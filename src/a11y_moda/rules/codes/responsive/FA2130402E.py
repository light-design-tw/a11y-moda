"""FA2130402E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ReorientationMessage(Rule):
    """FA2130402E — page should not instruct users to reorient device."""

    meta = RuleMeta(rule_id="FA2130402E", guideline="1.3.4", level=Level.AA,
        desc="有訊息顯示要求重新定向裝置設備，導致成功準則1.3.4失敗",
        source="extension")

    _REORIENT = re.compile(r"(rotate|landscape|portrait|請旋轉|請改為橫向|請改為直向)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        text = soup.get_text() or ""
        if self._REORIENT.search(text):
            report.add(self._issue(
                message="頁面包含請使用者旋轉裝置的字句，違反 1.3.4。",
                status="info",
            ))
