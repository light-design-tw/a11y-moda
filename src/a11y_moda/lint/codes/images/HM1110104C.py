"""HM1110104C lint — `<input type="image">` needs non-empty alt.

The `type` attribute itself can be dynamic in JSX; in that case we can't
know whether the input renders as an image or a text/checkbox/etc., so
we emit a caveat. When type is a literal "image", we apply the same
fail/caveat/info pattern as HM1110100C.
"""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements, get_attr, has_spread_props,
    find_html_elements, get_html_attr,
)


@register
class InputImageAltLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1110104C",
        guideline="1.1.1",
        level=Level.A,
        desc='型別(type)為 "image" 的 <input> 需有 alt 屬性，且其值不得為空',
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for inp in find_html_elements(parsed.tree, "input"):
                t = get_html_attr(inp, "type")
                if t.kind != "literal" or (t.value or "").lower() != "image":
                    continue
                alt = get_html_attr(inp, "alt")
                if alt.kind == "missing":
                    yield self._issue(status="fail",
                        message='<input type="image"> 缺 alt 屬性 — 必須提供替代文字',
                        node=inp)
                elif alt.kind == "empty":
                    yield self._issue(status="fail",
                        message='<input type="image"> alt 為空 — 必須提供非空替代文字',
                        node=inp)
            return

        for inp in find_jsx_elements(parsed.tree, "input"):
            t = get_attr(inp, "type")
            # If type is dynamic, we can't statically know it's an image input.
            # Don't emit issues — defer to scan stage.
            if t.kind == "dynamic":
                continue
            if t.kind != "literal" or (t.value or "").lower() != "image":
                continue
            alt = get_attr(inp, "alt")
            if alt.kind == "missing" and has_spread_props(inp):
                yield self._issue(status="caveat",
                    message='<input type="image"> 透過 {...spread} 帶屬性 — alt 可能在 spread 內',
                    node=inp)
                continue
            if alt.kind == "missing":
                yield self._issue(status="fail",
                    message='<input type="image"> 缺 alt 屬性 — 必須提供替代文字',
                    node=inp)
            elif alt.kind in ("empty", "boolean"):
                yield self._issue(status="fail",
                    message='<input type="image"> alt 為空 — 必須提供非空替代文字',
                    node=inp)
            elif alt.kind == "dynamic":
                yield self._issue(status="caveat",
                    message=f'<input type="image"> alt 為動態值 ({alt.raw}) — 無法靜態驗證',
                    node=inp)
