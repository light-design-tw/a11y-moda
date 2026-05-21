"""H309204 — 對經常使用的超連結，增加快速鍵的操作。

MODA 110.07 規範 90 條檢測碼第 H309204 條。對應 WCAG 2.4.1 Bypass Blocks。
AAA 標章評核常見要求項，惟 WCAG 2.1 sufficient techniques 已不再收
accesskey（因瀏覽器熱鍵衝突），故 E/C 主體系未列。MODA 仍要求 AAA
申請站台提供常用區塊快捷鍵 + Firefox (Shift+Alt+key) 操作說明。

典型 accesskey letters：
  U = 右上方功能區塊      S = 側邊欄
  C = 中央內容區          Z = 底部 / 頁尾
  H = 主標題 / 首頁       N = 網站搜尋

判定：
  0 個 accesskey                       → fail
  1 個 accesskey                       → caveat (建議補齊)
  2+ 個 accesskey + 有孤兒 (anchor 失聯) → caveat (列出孤兒)
  2+ 個 accesskey + 全部有效            → pass (silent)

孤兒 accesskey = `<a accesskey="X">` 但 (a) 無 href，或 (b) href="#Y"
但頁面找不到 id="Y" / name="Y"。`<input accesskey>` 不檢 anchor (它自身
即跳轉目標)，跳過。
"""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate


@register
class AccesskeyShortcut(Rule):
    """H309204 — accesskey keyboard shortcuts on common navigation links."""

    meta = RuleMeta(
        rule_id="H309204",
        guideline="2.4.1",
        level=Level.AAA,
        desc=(
            "對經常使用的超連結，增加快速鍵的操作。典型 accesskey："
            "U=右上、C=中央、H=主標題、N=搜尋、S=側邊、Z=頁尾。"
        ),
        source="moda-tw",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        nodes = soup.find_all(attrs={"accesskey": True})
        keys: set[str] = set()
        samples: list[str] = []
        orphans: list[tuple[str, str]] = []
        for el in nodes:
            raw = el.get("accesskey")
            if raw is None:
                continue
            tokens = raw if isinstance(raw, list) else str(raw).split()
            el_keys = {tok.strip().upper() for tok in tokens if tok and tok.strip()}
            if not el_keys:
                continue
            keys |= el_keys
            if len(samples) < 3:
                tag = el.name or "?"
                samples.append(f'<{tag} accesskey="{" ".join(sorted(el_keys))}">')

            if el.name == "a":
                href = (el.get("href") or "").strip()
                first_key = sorted(el_keys)[0]
                if not href:
                    orphans.append((first_key, "<a> 無 href，無跳轉目標"))
                elif href.startswith("#") and len(href) > 1:
                    tgt = href[1:]
                    found = soup.find(id=tgt) or soup.find(attrs={"name": tgt})
                    if not found:
                        orphans.append((first_key, f'href="{href}" 在頁面找不到對應 id / name'))

        if not keys:
            report.add(self._issue(
                message=(
                    "頁面未提供任何 accesskey 快捷鍵。MODA AAA 標章慣例要求政府 / 組織"
                    "網站對常用導覽區塊提供鍵盤快捷鍵（典型 U/C/N），並於網站導覽頁"
                    "說明 Firefox 需以 Shift+Alt+key 觸發。"
                ),
                snippet="no [accesskey] attribute found on this page",
            ))
            return

        if len(keys) == 1:
            only = sorted(keys)[0]
            report.add(self._issue(
                message=(
                    f"頁面僅 1 個 accesskey ({only})。建議至少 2 個常用區塊快捷鍵 "
                    f"(典型 U=右上、C=中央、N=搜尋)，並於網站導覽頁列出全部對應鍵位。"
                ),
                snippet=truncate(" ".join(samples), 200),
                status="caveat",
            ))
            return

        if orphans:
            details = "；".join(f"{ak}：{reason}" for ak, reason in orphans[:3])
            extra = f" (另 {len(orphans) - 3} 個略)" if len(orphans) > 3 else ""
            report.add(self._issue(
                message=(
                    f"accesskey 共 {len(keys)} 個，其中 {len(orphans)} 個為孤兒 "
                    f"(無 href 或 href anchor 找不到對應 id / name)：{details}{extra}。"
                    f"孤兒 accesskey 按下無效果，等同未提供。"
                ),
                snippet=truncate(" ".join(samples), 200),
                status="caveat",
            ))
            return
