"""AR2410300E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class StatusRoleStatus(Rule):
    """AR2410300E — pages that show status-y content should expose role=status."""

    meta = RuleMeta(rule_id="AR2410300E", guideline="4.1.3", level=Level.AA,
        desc="使用ARIA role=status顯示狀態訊息",
        source="extension")

    _STATUS_HINT = re.compile(r"(status|loading|saving|saved|loaded|complete|completed|成功|完成|載入)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if not self._STATUS_HINT.search(cls):
                continue
            if not el.get_text(strip=True):
                continue
            role = (el.get("role") or "").lower()
            live = (el.get("aria-live") or "").lower()
            if role in ("status", "alert", "log") or live:
                continue
            report.add(self._issue(
                message=f"疑似狀態訊息元件（class=\"{cls[:60]}\"）未設 role=status / aria-live。",
                snippet=truncate(str(el), 200),
                status="info",
            ))
            return
