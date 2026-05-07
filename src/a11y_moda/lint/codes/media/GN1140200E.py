"""GN1140200E lint — autoplay <audio>/<video> must be muted (or have stop control)."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr,
)


@register
class AutoplayMutedLint(LintRule):
    meta = RuleMeta(
        rule_id="GN1140200E",
        guideline="1.4.2",
        level=Level.A,
        desc="<audio>/<video> 自動播放時應靜音 (muted)",
        source="extension",
    )

    _TARGETS = ("audio", "video")

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in self._TARGETS:
                for media in find_html_elements(parsed.tree, tag):
                    autoplay = get_html_attr(media, "autoplay")
                    if autoplay.kind == "missing":
                        continue
                    muted = get_html_attr(media, "muted")
                    if muted.kind == "missing":
                        yield self._issue(status="fail",
                            message=f"<{tag} autoplay> 缺 muted 屬性 — 自動播放需靜音",
                            node=media)
            return

        for media in find_jsx_elements_any(parsed.tree, self._TARGETS):
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in media.children if c.type == "identifier"), "?")
            autoplay = get_attr(media, "autoplay")
            if autoplay.kind == "missing":
                continue
            muted = get_attr(media, "muted")
            if muted.kind == "missing":
                yield self._issue(status="fail",
                    message=f"<{tag} autoplay> 缺 muted 屬性 — 自動播放需靜音",
                    node=media)
