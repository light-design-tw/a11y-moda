"""GN1330205E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class FormInstructionsAtTop(Rule):
    """GN1330205E — instructions describing required fields appear at form start."""

    meta = RuleMeta(rule_id="GN1330205E", guideline="3.3.2", level=Level.A,
        desc="在表單或一組表單欄位開頭處提供文字指示來描述必要的輸入欄位",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for form in soup.find_all("form"):
            if not isinstance(form, Tag):
                continue
            req = [i for i in form.find_all(["input", "select", "textarea"]) if isinstance(i, Tag) and i.has_attr("required")]
            if not req:
                continue
            head_text = ""
            for child in form.children:
                if isinstance(child, Tag) and child.name in ("input", "select", "textarea"):
                    break
                if isinstance(child, Tag):
                    head_text += child.get_text(" ", strip=True) + " "
                if len(head_text) > 200:
                    break
            if "必填" in head_text or "required" in head_text.lower() or "*" in head_text:
                continue
            report.add(self._issue(
                message="<form> 開頭未發現必填欄位的整體說明（如「* 為必填」）。", status="info"))
            return
