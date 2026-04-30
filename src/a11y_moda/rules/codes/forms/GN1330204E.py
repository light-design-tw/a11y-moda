"""GN1330204E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class AdjacentSubmitLabels(Rule):
    """GN1330204E — submit buttons should sit next to the inputs they relate to."""

    meta = RuleMeta(rule_id="GN1330204E", guideline="3.3.2", level=Level.A,
        desc="使用毗鄰的按鈕來標示輸入區目的",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for form in soup.find_all("form"):
            if not isinstance(form, Tag):
                continue
            submits = [s for s in form.find_all(attrs={"type": "submit"}) if isinstance(s, Tag)]
            inputs = [i for i in form.find_all(["input", "textarea"]) if isinstance(i, Tag)]
            if len(submits) > 1 and len(inputs) <= len(submits):
                report.add(self._issue(
                    message=f"<form> 含 {len(submits)} 個 submit 但只有 {len(inputs)} 個 input — 按鈕可能與輸入區未毗鄰。", status="info"))
                return
