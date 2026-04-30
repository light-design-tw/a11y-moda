"""GN1330101E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class FormatErrorMessage(Rule):
    """GN1330101E + GN2330301E — input format errors should be specific."""

    meta = RuleMeta(rule_id="GN1330101E", guideline="3.3.1", level=Level.A,
        desc="使用者輸入的內容不在允許清單中，或格式未符合所需時，均提供文字描述",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.3.1 判斷格式錯誤訊息是否具體（含欄位名 + 哪裡錯）。

判斷標準：
- pass：含欄位名 + 錯誤性質
- fail：僅通用詞（「格式錯誤」「無效」沒講哪個欄位）

{OUTPUT_INSTRUCTIONS}"""

    _FMT_HINT = re.compile(r"(format|invalid|格式|錯誤|無效|請以)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        msgs = []
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            text = el.get_text(" ", strip=True)
            if self._FMT_HINT.search(cls) or self._FMT_HINT.search(text[:60]):
                if 5 < len(text) < 200:
                    msgs.append(text)
            if len(msgs) >= 5:
                break
        if not msgs:
            return
        joined = "\n---\n".join(msgs)
        v = judge_or_caveat(self, ctx, report, self.SYSTEM, joined)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"格式錯誤訊息不夠具體：{v[1]}",
                snippet=truncate(joined, 300), status="info"))
