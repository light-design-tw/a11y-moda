"""GN1330201E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class RequiredFieldIndicator(Rule):
    """GN1330201E + GN1330206E — required fields are visibly marked."""

    meta = RuleMeta(rule_id="GN1330201E", guideline="3.3.2", level=Level.A,
        desc="提供文字描述以指明需填寫的必填欄位",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        required_inputs = []
        for inp in soup.find_all(["input", "select", "textarea"]):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            if inp.has_attr("required") or (inp.get("aria-required") or "").lower() == "true":
                required_inputs.append(inp)
        if not required_inputs:
            return
        body_text = (soup.get_text(" ", strip=True) or "")[:500]
        if any(kw in body_text for kw in ("必填", "required", "*", "＊")):
            return
        report.add(self._issue(
            message=f"頁面有 {len(required_inputs)} 個必填欄位但未發現「必填 / *」的整體說明文字。", status="info"))
