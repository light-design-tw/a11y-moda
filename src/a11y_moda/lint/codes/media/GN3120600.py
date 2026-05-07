"""GN3120600 lint — page has video, sign-language interpretation needs human verification (AAA).

Lint can't judge video content; just surfaces info when video elements
or known video-host iframes are present.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr,
)


_VIDEO_HOSTS = ("youtube.com", "youtu.be", "youtube-nocookie.com",
                "vimeo.com", "player.vimeo.com", "dailymotion.com")


@register
class VideoSignLanguageLint(LintRule):
    meta = RuleMeta(
        rule_id="GN3120600",
        guideline="1.2.6",
        level=Level.AAA,
        desc="頁面含影片 — 請人工確認對白旁白是否提供手語翻譯",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        videos = []
        if parsed.language == "html":
            videos.extend(find_html_elements(parsed.tree, "video"))
            for f in find_html_elements(parsed.tree, "iframe"):
                src = get_html_attr(f, "src")
                if src.kind == "literal" and src.value:
                    if any(host in src.value.lower() for host in _VIDEO_HOSTS):
                        videos.append(f)
        else:
            videos.extend(find_jsx_elements(parsed.tree, "video"))
            for f in find_jsx_elements(parsed.tree, "iframe"):
                src = get_attr(f, "src")
                if src.kind == "literal" and src.value:
                    if any(host in src.value.lower() for host in _VIDEO_HOSTS):
                        videos.append(f)
        if videos:
            yield self._issue(status="info",
                message=f"頁面含 {len(videos)} 個影片 — 請人工確認手語翻譯 (lint 無法判斷影片內容)",
                node=videos[0])
