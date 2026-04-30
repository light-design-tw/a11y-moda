"""GN1330100E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class RequiredFieldMessage(Rule):
    """GN1330100E + GN2330300E — text describes which required fields are missing."""

    meta = RuleMeta(rule_id="GN1330100E", guideline="3.3.1", level=Level.A,
        desc="提供文字描述以指明未完成的必填欄位",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.3.1 判斷表單錯誤訊息或必填欄位提示文字是否清楚指明哪些欄位有問題。

判斷標準：
- pass：訊息含具體欄位名與動作（「姓名為必填」「Email 格式錯誤」）
- fail：訊息僅為通用詞（「請完整填寫」「資料有誤」）

{OUTPUT_INSTRUCTIONS}"""

    _ERR_HINT = re.compile(r"(error|required|必填|錯誤|missing|請輸入|請填)", re.IGNORECASE)

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        msgs = []
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if not self._ERR_HINT.search(cls) and "form" not in cls.lower():
                continue
            text = el.get_text(" ", strip=True)
            if 5 < len(text) < 300:
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
                message=f"必填欄位提示不夠清楚：{v[1]}",
                snippet=truncate(joined, 300), status="info"))
