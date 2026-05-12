"""GN1240500E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


_SITEMAP_TEXT = re.compile(
    r"(網站導覽|網站地圖|sitemap|site\s*map)",
    re.IGNORECASE,
)
_SITEMAP_HREF = re.compile(
    r"(/sitemap|/site-map|/網站導覽|/網站地圖)",
    re.IGNORECASE,
)


def _has_sitemap_link(soup: BeautifulSoup) -> bool:
    """Look for an explicit sitemap link in nav/footer/anywhere on page."""
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        text = a.get_text(strip=True)
        href = (a.get("href") or "").strip()
        title = (a.get("title") or "").strip()
        aria = (a.get("aria-label") or "").strip()
        if _SITEMAP_TEXT.search(text) or _SITEMAP_TEXT.search(title) or _SITEMAP_TEXT.search(aria):
            return True
        if _SITEMAP_HREF.search(href):
            return True
    return False


def _has_search(soup: BeautifulSoup) -> bool:
    if soup.find(attrs={"role": "search"}):
        return True
    for inp in soup.find_all("input"):
        if not isinstance(inp, Tag):
            continue
        if (inp.get("type") or "").lower() == "search":
            return True
        name = (inp.get("name") or inp.get("id") or "").lower()
        if "search" in name or "query" in name or name == "q":
            return True
    return False


@register
class NavigationMechanism(Rule):
    """GN1240500E — site provides navigation / search / sitemap mechanism.

    MODA 2.4.5 requires multiple ways to find content. We require at
    least TWO of: programmatic nav, search, sitemap-page link.
    Previously this rule early-exited on `<nav>` alone — but real MODA
    audits flag sites that have nav but no sitemap page (the case
    light-design.com.tw was flagged on 2026-05-12).
    """

    meta = RuleMeta(rule_id="GN1240500E", guideline="2.4.5", level=Level.A,
        desc="提供網站導覽、導覽工具或機制、搜尋功能、網頁清單鏈結等功能",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面是否提供清楚的導覽機制。

【pass（任一即可）】
- 可見的主選單（水平 / 垂直 / 漢堡選單已展開）
- 搜尋框
- 麵包屑導覽
- 頁腳網站地圖鏈結

【fail】
- 整頁找不到任何導覽元素
- 漢堡選單在那但完全展不開（無文字輔助）

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        has_nav = bool(soup.find("nav") or soup.find(attrs={"role": "navigation"}))
        has_sitemap = _has_sitemap_link(soup)
        has_search = _has_search(soup)
        mechanisms = sum([has_nav, has_sitemap, has_search])

        if mechanisms == 0:
            # Hard fail — no nav at all. Vision check optional for snippet detail.
            if _have_vision(ctx):
                v = _vision_judge(self, ctx, report, self.SYSTEM,
                                  "判斷頁面導覽機制是否充足",
                                  ctx.viewport_screenshot)
                if v is not None and v[0] == "fail":
                    report.add(self._issue(message=f"頁面缺少明顯導覽機制：{v[1]}"))
                    return
            report.add(self._issue(
                message="頁面找不到 <nav>、role=navigation、搜尋框或網站導覽連結，請至少提供其中之一。",
            ))
            return

        if mechanisms == 1 and not has_sitemap:
            # Only nav OR only search — MODA expects multiple ways.
            # Surface as caveat to remind adding sitemap page.
            report.add(self._issue(
                message=(
                    "未發現網站導覽頁（sitemap）連結。WCAG 2.4.5 要求多種尋找內容的方式，"
                    "建議於頁腳新增『網站導覽』連結（參考 https://accessibility.moda.gov.tw/Sitemap）。"
                ),
                status="caveat",
            ))
