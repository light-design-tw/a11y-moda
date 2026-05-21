"""MT309203 — 網站導覽 (sitemap) 頁面提供 accesskey 對應表與 Firefox 操作說明。

a11y-moda 在地化規則 (MODA-Taiwan extension; 非 WCAG normative)。

MODA AAA 標章評核慣例：sitemap 頁面除了列出網站結構外，必須附：
  1. 常用 accesskey 對應表 (Alt+U 跳右上、Alt+C 跳中央內容、Alt+N 跳搜尋…)
  2. Firefox 操作差異說明 (Firefox 需 Shift+Alt+key 觸發，非 Alt+key)

本規則無對應 WCAG SC — 屬 MODA reviewer 在地稽核要求。Rule ID 前綴 "MT"
表示 a11y-moda 為 MODA-Taiwan 標章新增的擴充規則，非 MODA 90 條 H 體系
的官方編號。

觸發條件 (page = sitemap 頁)：
  - URL path 含 /sitemap (case-insensitive)
  - 或 <title> / H1 文字含「網站導覽」/「網站地圖」/「sitemap」

判定：
  含 accesskey 對應表 + Firefox 說明 → silent pass
  缺其一                              → caveat
  兩者皆缺                            → fail
非 sitemap 頁 → 不觸發
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


_SITEMAP_URL_RE = re.compile(r"/(sitemap|site-map|網站導覽|網站地圖)/?$", re.IGNORECASE)
_SITEMAP_TITLE_RE = re.compile(r"(網站導覽|網站地圖|sitemap|site\s*map)", re.IGNORECASE)

_ACCESSKEY_DOC_RE = re.compile(
    r"accesskey|快捷鍵|快速鍵|Alt\s*[\+＋]\s*[A-Za-z]",
    re.IGNORECASE,
)
_FIREFOX_NOTE_RE = re.compile(
    r"firefox|Shift\s*[\+＋]\s*Alt",
    re.IGNORECASE,
)


def _is_sitemap_page(soup: BeautifulSoup, url: str) -> bool:
    if url and _SITEMAP_URL_RE.search(url.split("?", 1)[0]):
        return True
    title_tag = soup.find("title")
    if title_tag and _SITEMAP_TITLE_RE.search(title_tag.get_text(" ", strip=True)):
        return True
    h1 = soup.find(["h1", "h2"])
    if h1 and _SITEMAP_TITLE_RE.search(h1.get_text(" ", strip=True)):
        return True
    return False


@register
class SitemapKeyboardDoc(Rule):
    """MT309203 — sitemap page must document accesskey shortcuts + Firefox usage."""

    meta = RuleMeta(
        rule_id="MT309203",
        guideline="2.4.5",
        level=Level.AAA,
        desc=(
            "網站導覽 (sitemap) 頁面須提供常用 accesskey 對應表與 Firefox "
            "操作說明 (Shift+Alt+key)。MODA AAA 在地稽核慣例，無對應 WCAG SC。"
        ),
        source="moda-tw",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not _is_sitemap_page(soup, url):
            return

        text = soup.get_text(" ", strip=True)
        has_accesskey_doc = bool(_ACCESSKEY_DOC_RE.search(text))
        has_firefox_note = bool(_FIREFOX_NOTE_RE.search(text))

        if has_accesskey_doc and has_firefox_note:
            return  # silent pass

        if not has_accesskey_doc and not has_firefox_note:
            report.add(self._issue(
                message=(
                    "網站導覽頁缺少 accesskey 快捷鍵對應表與 Firefox 操作說明。"
                    "MODA AAA 評核慣例：sitemap 頁須列出 Alt+U/C/N… 對應區塊，"
                    "並註明 Firefox 需以 Shift+Alt+key 觸發。"
                ),
                snippet=f"sitemap_url={url}",
            ))
            return

        missing = "Firefox 操作說明" if has_accesskey_doc else "accesskey 對應表"
        report.add(self._issue(
            message=(
                f"網站導覽頁缺少「{missing}」。MODA AAA 評核慣例：sitemap 頁須同時列出 "
                f"accesskey 對應 (Alt+U/C/N…) + Firefox 觸發鍵差異 (Shift+Alt+key)。"
            ),
            snippet=f"sitemap_url={url}",
            status="caveat",
        ))
