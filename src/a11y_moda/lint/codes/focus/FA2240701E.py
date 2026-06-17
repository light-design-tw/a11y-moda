"""FA2240701E lint — `<style>` with outline:none must also have :focus rule.

Examines inline <style> blocks; doesn't fetch external CSS. JSX `<style>`
JSX expressions are also extractable when their content is a literal
string template.
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, find_html_elements


_OUTLINE_NONE = re.compile(r"outline\s*:\s*(none|0(\s*px)?)\s*[;}]", re.IGNORECASE)


@register
class OutlineNoneNoFallbackLint(LintRule):
    meta = RuleMeta(
        rule_id="FA2240701E",
        guideline="2.4.7",
        level=Level.AA,
        desc="<style> 含 outline:none 但無 :focus / :focus-visible 替代",
        source="extension",
        runtime_authoritative=True,
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            elements = find_html_elements(parsed.tree, "style")
            text_extractor = self._html_inner_text
        else:
            elements = find_jsx_elements(parsed.tree, "style")
            text_extractor = self._jsx_inner_text

        for s in elements:
            blob = text_extractor(s)
            if _OUTLINE_NONE.search(blob) and ":focus" not in blob:
                yield self._issue(status="fail",
                    message="<style> outline:none 但無 :focus 替代 — 鍵盤焦點將不可見",
                    node=s)
                return

    @staticmethod
    def _html_inner_text(node) -> str:
        chunks: list[str] = []
        def walk(n):
            if n.type == "text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(node)
        return "".join(chunks)

    @staticmethod
    def _jsx_inner_text(jsx_element) -> str:
        # For paired <style>{...}</style>, walk the parent jsx_element body.
        parent = jsx_element.parent if jsx_element.type == "jsx_opening_element" else jsx_element
        chunks: list[str] = []
        def walk(n):
            if n.type == "jsx_text":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            if n.type == "string_fragment":
                chunks.append(n.text.decode("utf-8", errors="replace"))
            for c in n.children:
                walk(c)
        walk(parent)
        return "".join(chunks)
