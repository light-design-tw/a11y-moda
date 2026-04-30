"""GN3120600 rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


_VIDEO_HOSTS = ("youtube.com", "youtu.be", "youtube-nocookie.com",
                "vimeo.com", "player.vimeo.com", "dailymotion.com")


@register
class SignLanguageVideo(Rule):
    """GN3120600 — prerecorded video narration should provide sign-language interpretation."""

    meta = RuleMeta(
        rule_id="GN3120600",
        guideline="1.2.6",
        level=Level.AAA,
        desc="預錄影片之對白旁白須提供手語翻譯",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        videos: list[Tag] = []
        for v in soup.find_all("video"):
            if isinstance(v, Tag) and not should_skip(v):
                videos.append(v)
        for f in soup.find_all("iframe"):
            if not isinstance(f, Tag) or should_skip(f):
                continue
            src = (f.get("src") or "").lower()
            if any(host in src for host in _VIDEO_HOSTS):
                videos.append(f)
        if not videos:
            return
        report.add(self._issue(
            message=f"頁面有 {len(videos)} 個影片，請人工確認對白旁白是否提供手語翻譯（自動工具無法判斷影片內容）。",
            snippet=truncate(str(videos[0]), 200),
            status="info",
        ))
