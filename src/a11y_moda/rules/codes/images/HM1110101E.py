"""HM1110101E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class GroupedImagesSingleAlt(Rule):
    """HM1110101E — when many images form one logical group, only one should carry alt."""

    meta = RuleMeta(rule_id="HM1110101E", guideline="1.1.1", level=Level.A,
        desc="僅在一組緊連圖片中的其中一個項目使用替代文字，描述該組圖片的所有項目",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷一組相鄰 <img> 的 alt 是否冗餘（多張有相似/相同 alt，造成螢幕閱讀器重複報讀）。

判斷標準：
- pass：每張 alt 描述不同內容，或整組僅一張帶 alt 其餘空
- fail：多張 alt 相同或相似度極高

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for parent in soup.find_all(True):
            if not isinstance(parent, Tag):
                continue
            siblings = [c for c in parent.find_all(recursive=False) if isinstance(c, Tag) and c.name == "img"]
            if len(siblings) < 3:
                continue
            alts = [(i.get("alt") or "").strip() for i in siblings]
            non_empty = [a for a in alts if a]
            if len(non_empty) < 2:
                continue
            if len(set(non_empty)) == 1:
                report.add(self._issue(
                    message=f"連續 {len(siblings)} 張 <img> 共用相同 alt「{non_empty[0]}」，造成螢幕閱讀器重複報讀。",
                    snippet=truncate(str(parent), 200), status="info"))
                return
            msg = f"alts: {non_empty}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"圖組 alt 設定不當：{v[1]}",
                    snippet=truncate(str(parent), 200), status="info"))
                return
