"""HM2130500E lint — `autocomplete` attribute must use HTML 5.2 valid tokens.

Tokens (case-insensitive): one of the predefined HTML 5.2 set, or
`section-...` prefix, or grouping qualifiers (billing/shipping/home/work
/mobile/fax/pager). Anything else is a fail (e.g. `autocomplete="username2"`).
Dynamic JSX values (`autocomplete={x}`) emit caveat.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_ALLOWED = {
    "on", "off",
    "name", "honorific-prefix", "given-name", "additional-name", "family-name",
    "honorific-suffix", "nickname",
    "email", "username", "new-password", "current-password", "one-time-code",
    "organization-title", "organization", "street-address",
    "address-line1", "address-line2", "address-line3",
    "address-level1", "address-level2", "address-level3", "address-level4",
    "country", "country-name", "postal-code",
    "cc-name", "cc-given-name", "cc-additional-name", "cc-family-name",
    "cc-number", "cc-exp", "cc-exp-month", "cc-exp-year", "cc-csc", "cc-type",
    "transaction-currency", "transaction-amount",
    "language", "bday", "bday-day", "bday-month", "bday-year", "sex",
    "url", "photo",
    "tel", "tel-country-code", "tel-national", "tel-area-code", "tel-local",
    "tel-extension",
    "impp",
}
_QUALIFIERS = {"billing", "shipping", "home", "work", "mobile", "fax", "pager"}


def _is_token_valid(tok: str) -> bool:
    t = tok.lower()
    if t in _ALLOWED or t in _QUALIFIERS:
        return True
    if t.startswith("section-"):
        return True
    return False


@register
class AutocompleteValidLint(LintRule):
    meta = RuleMeta(
        rule_id="HM2130500E",
        guideline="1.3.5",
        level=Level.AA,
        desc="autocomplete 屬性值需使用 HTML 5.2 合法 token",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed) -> Iterable[LintIssue]:
        # Walk all elements; check those with autocomplete attribute.
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                a = get_html_attr(n, "autocomplete")
                if a.kind == "literal" and a.value:
                    for tok in a.value.split():
                        if not _is_token_valid(tok):
                            yield self._issue(status="fail",
                                message=f'autocomplete="{a.value}" — token "{tok}" 非 HTML5.2 合法',
                                node=n)
                            return
            for c in n.children:
                yield from walk(c)
        yield from walk(parsed.tree.root_node)

    def _check_jsx(self, parsed) -> Iterable[LintIssue]:
        from ...helpers import find_jsx_elements_any, get_attr
        # Form-relevant elements that commonly carry autocomplete.
        targets = ("input", "select", "textarea", "form")
        for el in find_jsx_elements_any(parsed.tree, targets):
            a = get_attr(el, "autocomplete")
            if a.kind == "dynamic":
                yield self._issue(status="caveat",
                    message=f"autocomplete 為動態值 ({a.raw}) — 無法靜態驗證 token 合法性",
                    node=el)
                continue
            if a.kind == "literal" and a.value:
                for tok in a.value.split():
                    if not _is_token_valid(tok):
                        yield self._issue(status="fail",
                            message=f'autocomplete="{a.value}" — token "{tok}" 非 HTML5.2 合法',
                            node=el)
                        break
