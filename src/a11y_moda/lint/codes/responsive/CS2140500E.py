"""CS2140500E lint — `text-indent:-` + `background` inline style is image-text replacement
without toggle control."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr


@register
class TextImageReplaceLint(LintRule):
    meta = RuleMeta(
        rule_id="CS2140500E",
        guideline="1.4.5",
        level=Level.AA,
        desc="疑似將文字替換為背景圖片 (text-indent:- + background) 但無切換控制",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                style = get_html_attr(el, "style")
                if style.kind != "literal" or not style.value:
                    continue
                normalised = style.value.lower().replace(" ", "")
                if "text-indent:-" in normalised and "background" in normalised:
                    yield self._issue(status="info",
                        message="疑似文字替換為背景圖片 — 應提供切換控制",
                        node=el)
                    return
            return

        for el in find_jsx_elements(parsed.tree):
            style = get_attr(el, "style")
            text = ""
            if style.kind == "literal" and style.value:
                text = style.value
            elif style.kind == "dynamic" and style.raw:
                text = style.raw
            if not text:
                continue
            normalised = text.lower().replace(" ", "")
            if "text-indent:-" in normalised and "background" in normalised:
                yield self._issue(status="info",
                    message="疑似文字替換為背景圖片 — 應提供切換控制",
                    node=el)
                return
