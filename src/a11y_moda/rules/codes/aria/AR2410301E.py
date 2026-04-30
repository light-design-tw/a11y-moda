"""AR2410301E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class StatusMessageHasAriaLive(Rule):
    """AR2410301E — error/status messages should expose role=alert or aria-live."""

    meta = RuleMeta(
        rule_id="AR2410301E",
        guideline="4.1.3",
        level=Level.AA,
        desc="使用ARIA role=alert或aria-live來識別錯誤",
        source="extension",
    )

    _ERR_HINT = re.compile(r"(error|warn|alert|invalid|錯誤|警告)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if not self._ERR_HINT.search(cls):
                continue
            role = (el.get("role") or "").lower()
            live = (el.get("aria-live") or "").lower()
            if role in ("alert", "status", "log") or live in ("polite", "assertive"):
                continue
            text = el.get_text(strip=True)
            if not text:
                continue
            report.add(self._issue(
                message=f"疑似錯誤訊息容器（class=\"{cls[:60]}\"）未設 role=alert 或 aria-live。",
                snippet=truncate(str(el), 200),
                status="info",
            ))
            return
