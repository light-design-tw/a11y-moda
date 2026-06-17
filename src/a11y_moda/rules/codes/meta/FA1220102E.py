"""FA1220102E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate


@register
class MetaRefreshTimedRedirect(Rule):
    """FA1220102E — timed <meta http-equiv="refresh"> auto-redirect fails 2.2.1."""

    meta = RuleMeta(
        rule_id="FA1220102E",
        guideline="2.2.1",
        level=Level.A,
        desc="使用逾時後自動將頁面重新整理或轉向的機制，使用者無法關閉、調整或延長，導致計時調整(2.2.1)失敗",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for m in soup.find_all("meta"):
            if not isinstance(m, Tag):
                continue
            if (m.get("http-equiv") or "").strip().lower() != "refresh":
                continue
            content = (m.get("content") or "").strip()
            # content is "<seconds>" or "<seconds>; url=<target>"
            head = content.split(";", 1)[0].strip()
            try:
                delay = float(head)
            except ValueError:
                continue
            if delay <= 0:
                continue  # instant redirect is a different concern, not a timeout
            has_url = "url=" in content.lower()
            action = "自動轉向其他頁面" if has_url else "自動重新整理頁面"
            report.add(self._issue(
                message=(
                    f"頁面以 meta refresh 在 {delay:g} 秒後{action}，使用者無法關閉、調整或延長此計時，"
                    f"未符合計時調整(2.2.1)。請移除自動轉向，或提供使用者控制（暫停 / 延長 / 關閉）。"
                ),
                snippet=truncate(str(m)),
            ))
            return
