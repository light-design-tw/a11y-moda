"""GN1240101E lint — repeated link blocks (nav/header/aside) with many links
should expose an in-block skip link.

HTML and JSX both. Threshold: ≥5 anchors with no `#` skip link → info.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr, _html_tag_name,
)


_SECTION_TAGS = ("nav", "header", "aside")


@register
class SectionSkipLinkLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1240101E",
        guideline="2.4.1",
        level=Level.A,
        desc="重複內容區塊 (nav/header/aside) 含多個鏈結時，應提供區塊內 skip link",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed):
        for tag in _SECTION_TAGS:
            for block in find_html_elements(parsed.tree, tag):
                hashes, total = self._html_anchor_counts(block)
                if total >= 5 and hashes == 0:
                    yield self._issue(status="info",
                        message=f'<{tag}> 含 {total} 個鏈結但無 skip link',
                        node=block)

    @staticmethod
    def _html_anchor_counts(block):
        hashes = total = 0
        def walk(n):
            nonlocal hashes, total
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == "a":
                href = get_html_attr(n, "href")
                if href.kind == "literal" and href.value:
                    total += 1
                    if href.value.strip().startswith("#"):
                        hashes += 1
            for c in n.children:
                walk(c)
        walk(block)
        return hashes, total

    def _check_jsx(self, parsed):
        for block in find_jsx_elements_any(parsed.tree, _SECTION_TAGS):
            parent = block.parent if block.type == "jsx_opening_element" else block
            hashes, total = self._jsx_anchor_counts(parent)
            if total >= 5 and hashes == 0:
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in block.children if c.type == "identifier"), "?")
                yield self._issue(status="info",
                    message=f'<{tag}> 含 {total} 個靜態鏈結但無 skip link',
                    node=block)

    @staticmethod
    def _jsx_anchor_counts(jsx_element):
        hashes = total = 0
        def walk(n):
            nonlocal hashes, total
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for c in n.children:
                    if c.type == "identifier" and c.text.decode("utf-8", errors="replace") == "a":
                        href = get_attr(n, "href")
                        if href.kind == "literal" and href.value:
                            total += 1
                            if href.value.strip().startswith("#"):
                                hashes += 1
                        break
            for c in n.children:
                walk(c)
        walk(jsx_element)
        return hashes, total
