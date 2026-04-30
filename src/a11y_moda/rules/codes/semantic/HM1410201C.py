"""HM1410201C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class FrameTitle(Rule):
    """HM1410201C — <frame>/<iframe> need non-empty title."""

    meta = RuleMeta(
        rule_id="HM1410201C",
        guideline="4.1.2",
        level=Level.A,
        desc="頁框<frame>組件及內嵌式頁框<iframe>組件需有標題(title)屬性，且其值不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        frames = soup.find_all("frame")
        head = soup.find("head")
        body = soup.find("body")
        frameset = soup.find("frameset")
        is_frameset = head is not None and frameset is not None and body is None
        targets = frames if is_frameset else soup.find_all("iframe")
        for f in targets:
            if not isinstance(f, Tag) or should_skip(f):
                continue
            if not f.has_attr("title") or (f.get("title") or "").strip() == "":
                tag = "frame元素、frameset" if is_frameset else "iframe元素"
                report.add(self._issue(
                    message=f"使用{tag}等頁框組件，應以title屬性提供該頁框名稱幫助辨識。",
                    snippet=truncate(str(f)),
                ))
                return
