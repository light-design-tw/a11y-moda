"""GN1330200E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class FormSubmitWarning(Rule):
    """GN1330200E — describe what happens before user submits."""

    meta = RuleMeta(rule_id="GN1330200E", guideline="3.3.2", level=Level.A,
        desc="在使用者送出資料前，先描述會發生什麼事",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.3.2 判斷表單在送出前是否說明送出後會發生什麼事。

判斷標準：
- pass：表單周圍有說明送出去向、後續流程
- fail：完全無任何送出後行為說明

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for form in soup.find_all("form"):
            if not isinstance(form, Tag) or should_skip(form):
                continue
            submits = form.find_all(attrs={"type": "submit"}) + form.find_all("button", type=False)
            if not submits:
                continue
            ctx_text = form.get_text(" ", strip=True)[:600]
            msg = f"action: {form.get('action','')}\nmethod: {form.get('method','')}\nform text: {ctx_text}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"送出前說明不足：{v[1]}",
                    snippet=truncate(str(form)[:200]), status="info"))
                return
