"""GN1220200E lint — auto-rotating carousel should expose pause control."""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr, _html_tag_name


_CAROUSEL_HINT = re.compile(r"(carousel|slick|swiper|owl-carousel)", re.IGNORECASE)
_PAUSE_HINT = re.compile(r"(pause|stop|暫停|停止)", re.IGNORECASE)


@register
class CarouselHasPauseLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1220200E",
        guideline="2.2.2",
        level=Level.A,
        desc="疑似輪播元件應提供暫停控制",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for el in find_html_elements(parsed.tree):
                cls = get_html_attr(el, "class")
                if cls.kind != "literal" or not cls.value:
                    continue
                if not _CAROUSEL_HINT.search(cls.value):
                    continue
                if self._html_has_pause(el):
                    continue
                yield self._issue(status="info",
                    message=f'class="{cls.value[:60]}" 疑似輪播但無暫停控制',
                    node=el)
                return
            return

        for el in find_jsx_elements(parsed.tree):
            cls = get_attr(el, "className")
            if cls.kind == "missing":
                cls = get_attr(el, "class")
            if cls.kind != "literal" or not cls.value:
                continue
            if not _CAROUSEL_HINT.search(cls.value):
                continue
            parent = el.parent if el.type == "jsx_opening_element" else el
            if self._jsx_has_pause(parent):
                continue
            yield self._issue(status="info",
                message=f'className="{cls.value[:60]}" 疑似輪播但無暫停控制',
                node=el)
            return

    @staticmethod
    def _html_has_pause(node) -> bool:
        def walk(n):
            if n.type in ("element", "self_closing_tag") and _html_tag_name(n) in ("button", "a"):
                chunks: list[str] = []
                def collect(x):
                    if x.type == "text":
                        chunks.append(x.text.decode("utf-8", errors="replace"))
                    for c in x.children:
                        collect(c)
                collect(n)
                if _PAUSE_HINT.search("".join(chunks)):
                    return True
                label = get_html_attr(n, "aria-label")
                if label.kind == "literal" and label.value and _PAUSE_HINT.search(label.value):
                    return True
            return any(walk(c) for c in n.children)
        return walk(node)

    @staticmethod
    def _jsx_has_pause(jsx_element) -> bool:
        def walk(n):
            if n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                tag = next((c.text.decode("utf-8", errors="replace")
                            for c in n.children if c.type == "identifier"), "")
                if tag in ("button", "a"):
                    label = get_attr(n, "aria-label")
                    if label.kind == "literal" and label.value and _PAUSE_HINT.search(label.value):
                        return True
                    parent = n.parent
                    if parent and parent.type == "jsx_element":
                        chunks: list[str] = []
                        def collect(x):
                            if x.type == "jsx_text":
                                chunks.append(x.text.decode("utf-8", errors="replace"))
                            for c in x.children:
                                collect(c)
                        collect(parent)
                        if _PAUSE_HINT.search("".join(chunks)):
                            return True
            return any(walk(c) for c in n.children)
        return walk(jsx_element)
