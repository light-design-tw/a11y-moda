"""FA2240701E rule (was FA2141104E under 110.07; renamed for 115.11)."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class OutlineNoneNoFallback(Rule):
    """FA2240701E — outline:none must come with a :focus visual replacement."""

    meta = RuleMeta(rule_id="FA2240701E", guideline="2.4.7", level=Level.AA,
        desc="樣式元素的輪廓和邊框會消除或使視覺焦點指示器不可見",
        source="extension")

    _OUTLINE_NONE = re.compile(r"outline\s*:\s*(none|0(\s*px)?)\s*[;}]", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        css_blobs = []
        for s in soup.find_all("style"):
            if isinstance(s, Tag):
                css_blobs.append(s.get_text() or "")
        for blob in css_blobs:
            if self._OUTLINE_NONE.search(blob):
                if ":focus" not in blob and ":focus-visible" not in blob:
                    report.add(self._issue(
                        message="CSS outline:none / outline:0 但未提供 :focus 替代視覺，鍵盤焦點將不可見。",
                    ))
                    return
