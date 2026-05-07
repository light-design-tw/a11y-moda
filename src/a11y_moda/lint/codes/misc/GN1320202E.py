"""GN1320202E lint — `<a href>` to proprietary doc formats should also offer
an open format (PDF / HTML / ODT)."""
from __future__ import annotations
from typing import Iterable
from urllib.parse import urlparse

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr,
    find_html_elements, get_html_attr,
)


_PROPRIETARY_EXT = (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx")


def _matches_proprietary(href: str) -> str | None:
    path = urlparse(href.lower()).path
    for ext in _PROPRIETARY_EXT:
        if path.endswith(ext):
            return ext
    return None


@register
class DownloadOpenFormatLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1320202E",
        guideline="3.2.2",
        level=Level.A,
        desc="下載連結指向專有格式 (.doc/.xlsx 等) 時建議同時提供開放格式",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            offenders = []
            for a in find_html_elements(parsed.tree, "a"):
                href = get_html_attr(a, "href")
                if href.kind != "literal" or not href.value:
                    continue
                ext = _matches_proprietary(href.value)
                if ext:
                    offenders.append((a, ext))
            if offenders:
                yield self._issue(status="info",
                    message=f"下載連結指向 {offenders[0][1]} 等專有格式 (共 {len(offenders)} 處)",
                    node=offenders[0][0])
            return

        offenders = []
        for a in find_jsx_elements(parsed.tree, "a"):
            href = get_attr(a, "href")
            if href.kind != "literal" or not href.value:
                continue
            ext = _matches_proprietary(href.value)
            if ext:
                offenders.append((a, ext))
        if offenders:
            yield self._issue(status="info",
                message=f"下載連結指向 {offenders[0][1]} 等專有格式 (共 {len(offenders)} 處)",
                node=offenders[0][0])
