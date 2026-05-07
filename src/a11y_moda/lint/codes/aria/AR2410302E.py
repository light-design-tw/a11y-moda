"""AR2410302E lint — chat / activity log components should be role=log.

Negative regex first to skip false matches: blog, catalog, dialog,
prologue, epilogue, login, logo all contain `log` substring but aren't
log components.
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_LOG_NEGATIVE = re.compile(r"(blog|catalog|dialog|prologue|epilogue|login|logo)", re.IGNORECASE)
_LOG_HINT = re.compile(r"(log|chat|message-?list|activity-?feed|notifications|聊天)", re.IGNORECASE)


@register
class LogRoleLint(LintRule):
    meta = RuleMeta(
        rule_id="AR2410302E",
        guideline="4.1.3",
        level=Level.AA,
        desc="疑似訊息日誌元件應使用 ARIA role=log",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed):
        for el in find_html_elements(parsed.tree):
            cls = get_html_attr(el, "class")
            if cls.kind != "literal" or not cls.value:
                continue
            if _LOG_NEGATIVE.search(cls.value):
                continue
            if not _LOG_HINT.search(cls.value):
                continue
            role = get_html_attr(el, "role")
            if role.kind == "literal" and role.value and role.value.lower() == "log":
                continue
            live = get_html_attr(el, "aria-live")
            has_live = live.kind == "literal" and live.value and live.value.lower() in ("polite", "assertive")
            # Only fire if there's a strong signal (aria-live or many children).
            # Children count is hard to infer cheaply at lint; rely on aria-live.
            if not has_live:
                continue
            yield self._issue(
                status="info",
                message=f'class="{cls.value[:60]}" 含日誌詞且有 aria-live — 缺 role=log',
                node=el)
            return

    def _check_jsx(self, parsed):
        from ...helpers import find_jsx_elements, get_attr
        for el in find_jsx_elements(parsed.tree):
            cls = get_attr(el, "className")
            if cls.kind == "missing":
                cls = get_attr(el, "class")
            if cls.kind != "literal" or not cls.value:
                continue
            if _LOG_NEGATIVE.search(cls.value):
                continue
            if not _LOG_HINT.search(cls.value):
                continue
            role = get_attr(el, "role")
            if role.kind == "literal" and role.value and role.value.lower() == "log":
                continue
            live = get_attr(el, "aria-live")
            has_live = live.kind == "literal" and live.value and live.value.lower() in ("polite", "assertive")
            if not has_live:
                continue
            yield self._issue(
                status="info",
                message=f'className="{cls.value[:60]}" 含日誌詞且有 aria-live — 缺 role=log',
                node=el)
            return
