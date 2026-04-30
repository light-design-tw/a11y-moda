"""AR2410302E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class LogRoleLog(Rule):
    """AR2410302E — chat logs / activity feeds should be role=log."""

    meta = RuleMeta(rule_id="AR2410302E", guideline="4.1.3", level=Level.AA,
        desc="使用ARIA role=log識別順序訊息更新",
        source="extension")

    _LOG_HINT = re.compile(r"(log|chat|message-list|activity-feed|notifications|聊天)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if not self._LOG_HINT.search(cls):
                continue
            role = (el.get("role") or "").lower()
            if role == "log":
                continue
            children = el.find_all(recursive=False)
            if len(children) >= 3:
                report.add(self._issue(
                    message=f"疑似訊息日誌元件（class=\"{cls[:60]}\"）未設 role=log。",
                    snippet=truncate(str(el)[:200]),
                    status="info",
                ))
                return
