"""HM1130100C lint — headings must exist + each heading must have content.

Simplified vs scan: we don't try to enforce h1-only-once or full nesting
order at lint time (page-level invariants better verified at scan with
rendered DOM). We DO check:
  - role="heading" with empty/missing aria-level → fail
  - <h1>-<h6> with empty content (and no <img alt>) → fail / caveat
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


_HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")


@register
class HeadingHierarchyLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1130100C",
        guideline="1.3.1",
        level=Level.A,
        desc="標頭組件需有內容；role=\"heading\" 需有 aria-level 屬性",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed):
        for tag in _HEADINGS:
            for h in find_html_elements(parsed.tree, tag):
                if not self._html_has_content(h):
                    yield self._issue(status="fail",
                        message=f"<{tag}> 內容為空",
                        node=h)
        for el in self._find_role_heading_html(parsed.tree.root_node):
            level = get_html_attr(el, "aria-level")
            if level.kind in ("missing", "empty"):
                yield self._issue(status="fail",
                    message='role="heading" 需有 aria-level 屬性',
                    node=el)

    def _check_jsx(self, parsed):
        for h in find_jsx_elements_any(parsed.tree, _HEADINGS):
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in h.children if c.type == "identifier"), "?")
            parent = h.parent if h.type == "jsx_opening_element" else h
            if self._jsx_has_static_content(parent):
                continue
            if self._jsx_has_dynamic_content(parent):
                yield self._issue(status="caveat",
                    message=f"<{tag}> 內容為動態值 — 請確認 runtime 給的文字非空",
                    node=h)
                continue
            yield self._issue(status="fail",
                message=f"<{tag}> 內容為空",
                node=h)
        # role="heading" check
        from ...helpers import find_jsx_elements
        for el in find_jsx_elements(parsed.tree):
            role = get_attr(el, "role")
            if role.kind != "literal" or role.value != "heading":
                continue
            level = get_attr(el, "aria-level")
            if level.kind == "missing":
                yield self._issue(status="fail",
                    message='role="heading" 需有 aria-level 屬性',
                    node=el)

    @staticmethod
    def _html_has_content(node) -> bool:
        # Has text OR <img alt> with non-empty alt
        def walk(n):
            if n.type == "text" and n.text.decode("utf-8", errors="replace").strip():
                return True
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) == "img":
                alt = get_html_attr(n, "alt")
                if alt.kind == "literal" and alt.value:
                    return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _find_role_heading_html(root):
        out = []
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                role = get_html_attr(n, "role")
                if role.kind == "literal" and role.value == "heading":
                    out.append(n)
            for c in n.children:
                walk(c)
        walk(root)
        return out

    @staticmethod
    def _jsx_has_static_content(jsx_element) -> bool:
        def walk(n):
            if n.type == "jsx_text" and n.text.decode("utf-8", errors="replace").strip():
                return True
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for c in n.children:
                    if c.type == "identifier" and c.text.decode("utf-8", errors="replace") == "img":
                        alt = get_attr(n, "alt")
                        if alt.kind == "literal" and alt.value:
                            return True
                        break
            return any(walk(c) for c in n.children)
        return walk(jsx_element)

    @staticmethod
    def _jsx_has_dynamic_content(jsx_element) -> bool:
        for child in jsx_element.children:
            if child.type == "jsx_expression":
                return True
        return False
