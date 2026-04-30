"""HM1240200E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class PageTitleDescriptive(Rule):
    """HM1240200E — page title should describe content, not just brand."""

    meta = RuleMeta(
        rule_id="HM1240200E",
        guideline="2.4.2",
        level=Level.A,
        desc="提供網頁的描述性標題",
        source="extension",
    )

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.2 判斷 <title> 是否為描述性標題。

判斷標準（最低合規門檻）：
- pass：title 含可識別的網頁主題詞（即使含品牌名）
- fail：title 為空、僅為「Untitled」「Document」「Page」等預設值，或與 H1/內文主題完全無關
- unsure：判斷邊界

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        title_el = soup.find("title")
        title = title_el.get_text(strip=True) if isinstance(title_el, Tag) else ""
        if not title:
            return
        h1 = soup.find("h1")
        h1_text = h1.get_text(" ", strip=True) if isinstance(h1, Tag) else ""
        body = soup.find("body")
        body_text = (body.get_text(" ", strip=True) if isinstance(body, Tag) else "")[:600]
        msg = f"url: {url}\ntitle: {title}\nh1: {h1_text or '(none)'}\nbody excerpt: {body_text}"
        v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"網頁標題不夠描述性：{v[1]}",
                snippet=f"<title>{title}</title>", status="info"))
