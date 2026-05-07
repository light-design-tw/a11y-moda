"""AR3130600E lint — page must expose at least one landmark.

HTML landmark tags: <main>/<header>/<nav>/<aside>/<footer>/<section>.
ARIA landmark roles: main/banner/navigation/contentinfo/complementary/
search/region.

HTML only at lint time. JSX cannot be reasoned about file-by-file —
landmarks usually live in a root layout component (Next App Router
`layout.tsx`, Astro `Layout.astro`, etc.) that's not the file the user
is currently linting. Defer JSX detection to scan stage where the full
rendered DOM is available.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr, _html_tag_name


_LANDMARK_TAGS = ("main", "header", "nav", "aside", "footer", "section")
_LANDMARK_ROLES = {"main", "banner", "navigation", "contentinfo",
                    "complementary", "search", "region"}


@register
class PageLandmarkLint(LintRule):
    meta = RuleMeta(
        rule_id="AR3130600E",
        guideline="1.3.1",
        level=Level.AAA,
        desc="網頁需至少使用一個 HTML5 landmark 或 ARIA landmark role",
        source="extension",
    )
    applies_to = ("html",)

    def _check(self, parsed) -> Iterable[LintIssue]:
        bodies = find_html_elements(parsed.tree, "body")
        # If no <body>, this isn't a full page — skip.
        if not bodies:
            return
        body = bodies[0]
        # Look for any landmark tag descendant.
        if self._has_landmark_tag(body):
            return
        if self._has_landmark_role(body):
            return
        yield self._issue(status="fail",
            message=f"<body> 未使用 HTML5 landmark ({'/'.join(_LANDMARK_TAGS)}) "
                    f"或 ARIA landmark role — 輔助科技難以辨識主要區塊",
            node=body)

    @staticmethod
    def _has_landmark_tag(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) in _LANDMARK_TAGS:
                return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _has_landmark_role(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag"):
                role = get_html_attr(n, "role")
                if role.kind == "literal" and role.value:
                    if any(r in _LANDMARK_ROLES for r in role.value.lower().split()):
                        return True
            return any(walk(c) for c in n.children)
        return walk(node)
