"""GN1140200E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class AutoplayMediaMuted(Rule):
    """GN1140200E — autoplay audio/video must be muted or have stop control."""

    meta = RuleMeta(
        rule_id="GN1140200E",
        guideline="1.4.2",
        level=Level.A,
        desc="除非聲音在三秒內自動關閉，或在頁面開頭提供關閉控制元件，否則只有當使用者請求時才播放聲音",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for media in soup.find_all(["audio", "video"]):
            if not isinstance(media, Tag) or should_skip(media):
                continue
            if not media.has_attr("autoplay"):
                continue
            if media.has_attr("muted"):
                continue
            report.add(self._issue(
                message=f"<{media.name}> 自動播放但未靜音，建議加 muted 屬性或提供使用者控制。",
                snippet=truncate(str(media)),
            ))
            return
