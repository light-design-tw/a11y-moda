"""AR2410301E lint — error/warning components should expose role=alert / aria-live."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_ERR_HINT = re.compile(r"(error|warn|alert|invalid|錯誤|警告)", re.IGNORECASE)
_ALLOWED_ROLES = ("alert", "status", "log")


@register
class ErrorRoleLint(LintRule):
    meta = RuleMeta(
        rule_id="AR2410301E",
        guideline="4.1.3",
        level=Level.AA,
        desc="疑似錯誤/警告元件應使用 ARIA role=alert / aria-live",
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
            if not _ERR_HINT.search(cls.value):
                continue
            role = get_html_attr(el, "role")
            live = get_html_attr(el, "aria-live")
            if role.kind == "literal" and role.value and role.value.lower() in _ALLOWED_ROLES:
                continue
            if live.kind == "literal" and live.value and live.value.lower() in ("polite", "assertive"):
                continue
            yield self._issue(
                status="info",
                message=f'class="{cls.value[:60]}" 含錯誤詞 — 缺 role=alert 或 aria-live',
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
            if not _ERR_HINT.search(cls.value):
                continue
            role = get_attr(el, "role")
            live = get_attr(el, "aria-live")
            if role.kind == "literal" and role.value and role.value.lower() in _ALLOWED_ROLES:
                continue
            if live.kind == "literal" and live.value and live.value.lower() in ("polite", "assertive"):
                continue
            yield self._issue(
                status="info",
                message=f'className="{cls.value[:60]}" 含錯誤詞 — 缺 role=alert / aria-live',
                node=el)
            return
