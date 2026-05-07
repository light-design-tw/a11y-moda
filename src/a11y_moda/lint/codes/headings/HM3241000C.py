"""HM3241000C lint — page should organize content with headings (AAA).

HTML only. Skips if doctype is HTML5 (typical modern pages assumed
to use HTML5 semantic structure). Otherwise fail when no headings exist.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, _html_tag_name


_HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")


@register
class HeadingOrganizeLint(LintRule):
    meta = RuleMeta(
        rule_id="HM3241000C",
        guideline="2.4.10",
        level=Level.AAA,
        desc="使用 <h1>-<h6> 組織網頁內容 (非 HTML5 時必要)",
        source="freego",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        # Treat HTML5 doctype as automatic pass — modern pages have semantic
        # structure even when <hN> is sparse.
        text = parsed.source[:200].decode("utf-8", errors="replace").lstrip().lower()
        if text.startswith("<!doctype html>"):
            return
        # Look for any heading in the document.
        for tag in _HEADINGS:
            if find_html_elements(parsed.tree, tag):
                return
        # No headings, no HTML5 doctype.
        bodies = find_html_elements(parsed.tree, "body")
        target = bodies[0] if bodies else parsed.tree.root_node
        yield self._issue(status="fail",
            message="非 HTML5 文件但缺所有標題 <h1>-<h6>",
            node=target)
