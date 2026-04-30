"""FA2410303E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class ProgrammaticStatusMessage(Rule):
    """FA2410303E — status messages must be programmatically determinable."""

    meta = RuleMeta(rule_id="FA2410303E", guideline="4.1.3", level=Level.AA,
        desc="提供無法通過角色或屬性以程式化確定的狀態消息",
        source="extension")

    _STATUS_TXT = re.compile(r"(loading|saving|saved|done|complete|fail|error|成功|失敗|錯誤|完成|載入)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(["div", "span", "p"]):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            text = el.get_text(strip=True)
            if not text or len(text) > 80:
                continue
            if not self._STATUS_TXT.search(text):
                continue
            role = (el.get("role") or "").lower()
            live = (el.get("aria-live") or "").lower()
            if role in ("status", "alert", "log") or live:
                continue
            cls = " ".join(el.get("class") or "").lower()
            if any(k in cls for k in ("status", "toast", "notice", "alert", "snackbar", "banner")):
                report.add(self._issue(
                    message=f"狀態訊息「{text[:30]}」未透過 role / aria-live 程式化暴露。",
                    snippet=truncate(str(el), 200),
                    status="info",
                ))
                return
