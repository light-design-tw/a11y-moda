"""GN1210200E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class NoKeyboardTrapHints(Rule):
    """GN1210200E — heuristic for likely keyboard traps (modals without close shortcut)."""

    meta = RuleMeta(rule_id="GN1210200E", guideline="2.1.2", level=Level.A,
        desc="確認使用者不會困在內容中",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for dlg in soup.find_all(attrs={"role": "dialog"}):
            if not isinstance(dlg, Tag) or should_skip(dlg):
                continue
            close_btn = dlg.find(["button", "a"], string=re.compile(r"close|關閉|cancel|取消|×|✕", re.IGNORECASE))
            has_aria_close = dlg.find(attrs={"aria-label": re.compile(r"close|關閉", re.IGNORECASE)})
            if not close_btn and not has_aria_close:
                report.add(self._issue(
                    message="role=dialog 元件缺少明確的關閉按鈕，可能造成鍵盤焦點受困。",
                    snippet=truncate(str(dlg)[:200]),
                    status="info",
                ))
                return
