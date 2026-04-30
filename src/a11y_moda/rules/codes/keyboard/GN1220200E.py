"""GN1220200E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class CarouselHasPause(Rule):
    """GN1220200E — auto-rotating carousels should expose a pause control."""

    meta = RuleMeta(rule_id="GN1220200E", guideline="2.2.2", level=Level.A,
        desc="讓內容能加以暫停，並可從暫停處重新開始",
        source="extension")

    _CAROUSEL_HINT = re.compile(r"(carousel|slider|slick|swiper|owl-carousel)", re.IGNORECASE)
    _PAUSE_HINT = re.compile(r"(pause|stop|暫停|停止)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if not self._CAROUSEL_HINT.search(cls):
                continue
            buttons = el.find_all(["button", "a"])
            has_pause = any(self._PAUSE_HINT.search(b.get_text() or "") or
                            self._PAUSE_HINT.search(b.get("aria-label") or "") for b in buttons)
            if not has_pause:
                report.add(self._issue(
                    message=f"疑似輪播元件（class=\"{cls[:60]}\"）未發現暫停控制，請確認可由使用者停止。",
                    snippet=truncate(str(el)[:200]),
                    status="info",
                ))
                return
