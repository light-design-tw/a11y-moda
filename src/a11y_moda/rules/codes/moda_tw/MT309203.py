"""MT309203 — 網站導覽 (sitemap) 頁面提供 accesskey 對應表與 Firefox 操作說明。

a11y-moda 在地化規則 (MODA-Taiwan extension; 非 WCAG normative)。

MODA AAA 標章評核慣例：sitemap 頁面除了列出網站結構外，必須附：
  1. 常用 accesskey 對應表 (Alt+U 跳右上、Alt+C 跳中央內容、Alt+N 跳搜尋…)
  2. Firefox 操作差異說明 (Firefox 需 Shift+Alt+key 觸發，非 Alt+key)
  3. 對應表文字與實際元素 aria-label / 報讀文字一致 (MODA reviewer 高頻挑項)

本規則無對應 WCAG SC — 屬 MODA reviewer 在地稽核要求。Rule ID 前綴 "MT"
表示 a11y-moda 為 MODA-Taiwan 標章新增的擴充規則，非 MODA 90 條 H 體系
的官方編號。

觸發條件 (page = sitemap 頁)：
  - URL path 含 /sitemap (case-insensitive)
  - 或 <title> / H1 文字含「網站導覽」/「網站地圖」/「sitemap」

判定：
  含 accesskey 對應表 + Firefox 說明 → 進入文字一致性比對
    表格說明 vs 同頁 accesskey 元素報讀文字一致 → silent pass
    不一致                                       → fail (列出差異)
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
_KEY_IN_CELL_RE = re.compile(r"Alt\s*[\+＋]\s*([A-Za-z])", re.IGNORECASE)


def _parse_accesskey_table(soup: BeautifulSoup) -> dict[str, str]:
    """Extract {KEY_UPPER: description_text} from accesskey documentation table."""
    mapping: dict[str, str] = {}
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            row_text = " ".join(c.get_text(" ", strip=True) for c in cells)
            m = _KEY_IN_CELL_RE.search(row_text)
            if not m:
                continue
            key = m.group(1).upper()
            desc = cells[-1].get_text(" ", strip=True)
            if desc:
                mapping[key] = desc
    return mapping


def _get_accessible_name(el) -> str:
    """Return text a screen reader would announce for *el*."""
    for attr in ("aria-label", "title"):
        val = el.get(attr, "")
        if val:
            return val.strip() if isinstance(val, str) else " ".join(val).strip()
    text = el.get_text(" ", strip=True)
    text = re.sub(r":{2,}", "", text).strip()
    return text


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
            self._cross_check_labels(soup, report, url)
            return

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

        missing = "Firefox 操作說明" if has_accesskey_doc else "accesskey 快捷鍵對應表"
        report.add(self._issue(
            message=(
                f"網站導覽頁缺少「{missing}」。MODA AAA 評核慣例：sitemap 頁須同時列出 "
                f"accesskey 對應 (Alt+U/C/N…) + Firefox 觸發鍵差異 (Shift+Alt+key)。"
            ),
            snippet=f"sitemap_url={url}",
            status="caveat",
        ))

    def _cross_check_labels(
        self, soup: BeautifulSoup, report: PageReport, url: str
    ) -> None:
        """Compare accesskey table descriptions vs actual element labels."""
        table_map = _parse_accesskey_table(soup)
        if not table_map:
            return

        all_ak_els = soup.find_all(attrs={"accesskey": True})
        el_labels: dict[str, str] = {}
        for el in all_ak_els:
            raw = el.get("accesskey")
            keys = raw if isinstance(raw, list) else str(raw).split()
            label = _get_accessible_name(el)
            for k in keys:
                k = k.strip().upper()
                if k:
                    el_labels[k] = label

        mismatches: list[str] = []
        for key, table_desc in sorted(table_map.items()):
            el_label = el_labels.get(key)
            if el_label is None:
                continue
            if not el_label:
                mismatches.append(
                    f"Alt+{key}: 導覽說明「{table_desc}」，"
                    f"但元素無報讀文字 (缺 aria-label)"
                )
            elif el_label != table_desc:
                mismatches.append(
                    f"Alt+{key}: 導覽說明「{table_desc}」，"
                    f"語音報讀「{el_label}」"
                )

        if mismatches:
            report.add(self._issue(
                message=(
                    "快捷鍵導覽說明與實際元素語音報讀文字不一致。"
                    "MODA 要求兩者相同，避免螢幕閱讀器使用者混淆。\n"
                    + "\n".join(mismatches)
                ),
                snippet=f"sitemap_url={url}",
            ))
