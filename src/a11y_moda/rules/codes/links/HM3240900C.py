"""HM3240900C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class StandaloneLinkTitle(Rule):
    """HM3240900C — link's title attribute must not duplicate link text or img alt."""

    meta = RuleMeta(
        rule_id="HM3240900C",
        guideline="2.4.9",
        level=Level.AAA,
        desc="任何具有連結目的之鏈結組件均需有鏈結文字及標題屬性，且鏈結文字之內容及標題屬性之值均不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            if not (a.get("href") or "").strip():
                continue
            title = a.get("title")
            if title is None:
                continue
            text = a.get_text().strip()
            if text and text == title:
                report.add(self._issue(
                    message="文字超連結如使用title屬性，內容應做為連結用途的補充說明或幫助操作的提示說明，不應該重複連結文字。",
                    snippet=truncate(str(a)),
                ))
                ctx.state["HM3240900C_ok"] = False
                ctx.state["HM3240900C_error"] = "title重複連結文字"
                return
            for img in a.find_all("img"):
                if not isinstance(img, Tag) or should_skip(img):
                    continue
                alt = img.get("alt")
                if alt is not None and alt == title:
                    report.add(self._issue(
                        message="圖片超連結如使用title屬性，內容應做為連結用途的補充說明，不應該重複alt屬性內容。",
                        snippet=truncate(str(a)),
                    ))
                    ctx.state["HM3240900C_ok"] = False
                    ctx.state["HM3240900C_error"] = "title重複alt屬性"
                    return
        ctx.state["HM3240900C_ok"] = True
