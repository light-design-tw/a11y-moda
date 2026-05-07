"""GN1240104E lint — sectioning elements (section/article/aside) should
contain a heading h1-h6, OR be aria-labelled.
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


_SECTION_TAGS = ("section", "article", "aside")
_HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")


@register
class SectionHeadingLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1240104E",
        guideline="2.4.1",
        level=Level.A,
        desc="<section>/<article>/<aside> 區段需提供標頭或 aria-label",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in _SECTION_TAGS:
                for sec in find_html_elements(parsed.tree, tag):
                    if self._has_html_label(sec):
                        continue
                    if self._has_html_heading(sec):
                        continue
                    yield self._issue(status="info",
                        message=f"<{tag}> 區段未提供標頭或 aria-label",
                        node=sec)
            return

        for sec in find_jsx_elements_any(parsed.tree, _SECTION_TAGS):
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in sec.children if c.type == "identifier"), "?")
            if self._has_jsx_label(sec):
                continue
            parent = sec.parent if sec.type == "jsx_opening_element" else sec
            if self._has_jsx_heading(parent):
                continue
            yield self._issue(status="info",
                message=f"<{tag}> 區段未發現靜態標頭或 aria-label (動態渲染請於 scan 階段確認)",
                node=sec)

    @staticmethod
    def _has_html_label(sec):
        for attr in ("aria-label", "aria-labelledby"):
            a = get_html_attr(sec, attr)
            if a.kind in ("literal", "boolean"):
                return True
        return False

    @staticmethod
    def _has_html_heading(sec):
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) in _HEADINGS:
                return True
            return any(walk(c) for c in n.children)
        return walk(sec)

    @staticmethod
    def _has_jsx_label(sec):
        for attr in ("aria-label", "aria-labelledby"):
            a = get_attr(sec, attr)
            if a.kind in ("literal", "boolean", "dynamic"):
                # Even dynamic counts — defer to runtime
                return True
        return False

    @staticmethod
    def _has_jsx_heading(jsx_element):
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for c in n.children:
                    if c.type == "identifier":
                        name = c.text.decode("utf-8", errors="replace")
                        if name.lower() in _HEADINGS:
                            return True
                        break
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
