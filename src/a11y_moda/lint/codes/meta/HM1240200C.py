"""HM1240200C lint — page must have a non-empty `<title>`.

Only HTML files are linted directly. JSX page titles are framework-
dependent (next/head, Astro <title>, react-helmet, App Router metadata
export) and the rendered DOM is what matters — defer JSX detection to
the scan stage.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements


@register
class PageTitleLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1240200C",
        guideline="2.4.2",
        level=Level.A,
        desc="網頁需有 <title>，且其值不得為空字串",
        source="freego",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        # Find <head> first, then look for <title> children. Top-level <title>
        # outside <head> doesn't count for the rule, and <title> inside <svg>
        # is a different element.
        heads = find_html_elements(parsed.tree, "head")
        # If no <head> at all, fragment HTML — no judgement.
        if not heads:
            return
        # Find <title> inside any <head>.
        for head in heads:
            for title in self._direct_title_children(head):
                # Got a <title> inside <head>. Verify non-empty content.
                text = self._inner_text(title)
                if text.strip():
                    return  # success — non-empty title found
                yield self._issue(
                    status="fail",
                    message="<title> 為空字串 — 必須提供網頁標題",
                    node=title,
                )
                return
        # No <title> found in any <head>.
        yield self._issue(
            status="fail",
            message="<head> 內缺 <title> — 每個網頁需在 <head> 提供 <title> 標題",
            node=heads[0],
        )

    @staticmethod
    def _direct_title_children(head_node):
        """Yield <title> elements that are direct children of <head> (not inside
        <svg> or other nested elements within head)."""
        out = []
        def walk(node, in_svg=False):
            if node.type == "element":
                # Detect tag name
                from ...helpers import _html_tag_name  # type: ignore
                name = _html_tag_name(node)
                if name == "svg":
                    in_svg = True
                elif name == "title" and not in_svg:
                    out.append(node)
            for child in node.children:
                walk(child, in_svg)
        walk(head_node)
        return out

    @staticmethod
    def _inner_text(element_node) -> str:
        """Concatenate all text content nodes inside the element."""
        chunks: list[str] = []
        def walk(node):
            if node.type == "text":
                chunks.append(node.text.decode("utf-8", errors="replace"))
            for child in node.children:
                walk(child)
        walk(element_node)
        return "".join(chunks)
