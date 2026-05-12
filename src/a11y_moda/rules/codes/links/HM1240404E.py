"""HM1240404E rule."""
from __future__ import annotations
from collections import defaultdict
from urllib.parse import urljoin
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


@register
class LinkTitleSupplements(Rule):
    """HM1240404E — title attr should add to (not duplicate) link text.

    Two failure modes covered:
    1. Has title but title duplicates visible text (original direction —
       LLM judged).
    2. Same visible text repeated across multiple links pointing at
       different hrefs, with **no** disambiguating title (the direction
       MODA actually flagged on light-design.com.tw — three "查看方案"
       links to three different plan pages, all without title).

    Direction (2) is a pure structural check — no LLM required, runs
    even without `--llm-*`.
    """

    meta = RuleMeta(rule_id="HM1240404E", guideline="2.4.4", level=Level.A,
        desc="針對脈絡中的鏈結，用標題屬性來補充鏈結文字",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.4 判斷鏈結 title 屬性是否補充而非重複視覺文字。

判斷標準：
- pass：title 補充新資訊（如「在新分頁開啟」）或為空
- fail：title 完全等於或只是視覺文字的同義改寫

{OUTPUT_INSTRUCTIONS}"""

    _MIN_REPEAT = 2  # ≥2 個相同文字連結才算疑似需要區分
    _MIN_TEXT_LEN = 2  # 過濾單字符 / 標點

    def _check(self, soup, report, *, html, url, ctx) -> None:
        # Direction 2: structural — repeated link text + different href + no title.
        groups: dict[str, list[Tag]] = defaultdict(list)
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            text = a.get_text(strip=True)
            if not text or len(text) < self._MIN_TEXT_LEN:
                continue
            groups[text].append(a)
        for text, links in groups.items():
            if len(links) < self._MIN_REPEAT:
                continue
            hrefs = {urljoin(url, (a.get("href") or "").strip()) for a in links}
            if len(hrefs) < 2:
                continue  # 同樣文字 + 同 href = 沒有區分需求
            if all((a.get("title") or "").strip() or (a.get("aria-label") or "").strip() for a in links):
                continue  # 全有 title / aria-label = 已區分
            report.add(self._issue(
                message=(
                    f"鏈結文字「{text}」重複 {len(links)} 次但指向 {len(hrefs)} 個不同網址，"
                    f"建議於各連結加上不同的 title 或 aria-label 以區分目的。"
                ),
                snippet=truncate(str(links[0]), 200),
            ))
            break  # 一頁一個提示，避免噪音

        # Direction 1: LLM-judged title-duplicates-text (original logic).
        if not have_llm(ctx):
            return
        for a in soup.find_all("a", href=True, title=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            title = (a.get("title") or "").strip()
            text = a.get_text(strip=True)
            if not title or not text:
                continue
            msg = f"link text: {text}\ntitle attr: {title}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"title 與鏈結文字重複：{v[1]}",
                    snippet=truncate(str(a), 200), status="info"))
                return
