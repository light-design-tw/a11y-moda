"""GN1110111E lint — CAPTCHA must offer at least one alternative.

The scan-time rule walks the DOM looking for CAPTCHA-like elements
(keywords in alt/src/class/id) and then checks for alternatives
(audio elements, mailto/tel links, or alternative-method text) in the
same scope.

At lint time we can detect the CAPTCHA candidate, but checking for
"alternatives nearby" is too brittle in source — the alternative may be
in a sibling component, an i18n string, or rendered conditionally.
We emit `caveat` whenever a CAPTCHA-like element is detected, asking the
human/LLM (or the scan stage) to verify alternatives are present.
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr,
)


_CAPTCHA_HINT_RE = re.compile(
    r"captcha|驗證碼|驗證圖|圖形驗證|recaptcha|hcaptcha|turnstile|geetest",
    re.IGNORECASE,
)


def _attr_blob_jsx(elem) -> str:
    """Concatenate selected attribute values for keyword scanning. Dynamic
    values contribute their raw text (which may include the variable name
    that often hints at CAPTCHA usage)."""
    parts: list[str] = []
    for name in ("alt", "src", "title", "aria-label", "class", "className", "id"):
        a = get_attr(elem, name)
        if a.value:
            parts.append(a.value)
        elif a.raw:
            parts.append(a.raw)
    return " ".join(parts)


def _attr_blob_html(elem) -> str:
    parts: list[str] = []
    for name in ("alt", "src", "title", "aria-label", "class", "id"):
        a = get_html_attr(elem, name)
        if a.value:
            parts.append(a.value)
    return " ".join(parts)


@register
class CaptchaAlternativeLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1110111E",
        guideline="1.1.1",
        level=Level.A,
        desc="疑似 CAPTCHA 元素需提供替代驗證方式 (語音 / 電子郵件 / 客服等)",
        source="extension",
    )

    _TARGETS = ("img", "input", "canvas", "iframe")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in self._TARGETS:
                for el in find_html_elements(parsed.tree, tag):
                    if _CAPTCHA_HINT_RE.search(_attr_blob_html(el)):
                        yield self._issue(
                            status="caveat",
                            message="疑似 CAPTCHA 元素 — 請確認頁面提供替代驗證方式 "
                                    "(scan 階段會檢查 audio / mailto / tel)",
                            node=el)
                        return
            return

        for el in find_jsx_elements_any(parsed.tree, self._TARGETS):
            if _CAPTCHA_HINT_RE.search(_attr_blob_jsx(el)):
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in el.children if c.type == "identifier"), "?")
                yield self._issue(
                    status="caveat",
                    message=f"疑似 CAPTCHA <{tag}> — 請確認替代驗證方式 "
                            "(scan 階段會檢查 audio / mailto / tel)",
                    node=el)
                return
