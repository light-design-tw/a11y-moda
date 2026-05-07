"""HM1110100C lint — `<img>` elements must have an `alt` attribute.

Three-tier verdict:
- fail   : alt attribute is entirely missing
- caveat : alt is bound to a dynamic expression — can't statically verify text quality
- info   : alt is an empty string — acceptable for purely decorative images,
           but the AST can't determine intent; surfaced for human/LLM review
- pass   : alt is a non-empty literal string (rule satisfied)

Mirrors the scan-time `HM1110100C` rule. Same rule_id; lint catches the
common cases at write time, scan catches everything (including DOM
emitted by component abstractions that lint can't trace).
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
class ImgAltLint(LintRule):
    meta = RuleMeta(
        rule_id="HM1110100C",
        guideline="1.1.1",
        level=Level.A,
        desc="圖片<img>元件需有替代文字(alt)屬性",
        source="freego",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_jsx(self, parsed) -> Iterable[LintIssue]:
        for img in find_jsx_elements(parsed.tree, "img"):
            attr = get_attr(img, "alt")
            # Spread props: alt could come from {...rest}. Don't false-positive.
            if attr.kind == "missing" and has_spread_props(img):
                yield self._issue(
                    status="caveat",
                    message="<img> 透過 {...spread} 帶屬性 — alt 可能在 spread 內，無法靜態驗證",
                    node=img,
                )
                continue
            if attr.kind == "missing":
                yield self._issue(
                    status="fail",
                    message="<img> 缺 alt 屬性 — 必須提供替代文字 (裝飾性圖片用 alt=\"\")",
                    node=img,
                )
            elif attr.kind == "boolean":
                # `<img alt />` — alt with no value renders as alt="true" in React.
                # Almost certainly a typo / unfinished code.
                yield self._issue(
                    status="caveat",
                    message="<img alt /> alt 屬性無賦值 — React 會渲染為 alt=\"true\"，疑似遺漏寫值",
                    node=img,
                )
            elif attr.kind == "dynamic":
                yield self._issue(
                    status="caveat",
                    message=f"<img> alt 為動態值 ({attr.raw}) — 無法靜態驗證內容品質，請確認 runtime 給的是有意義的描述",
                    node=img,
                )
            elif attr.kind == "empty":
                yield self._issue(
                    status="info",
                    message="<img> alt 為空字串 — 若為純裝飾性圖片正確；若為內容圖請補敘述",
                    node=img,
                )
            # literal non-empty → pass (don't emit)

    def _check_html(self, parsed) -> Iterable[LintIssue]:
        for img in find_html_elements(parsed.tree, "img"):
            attr = get_html_attr(img, "alt")
            if attr.kind == "missing":
                yield self._issue(
                    status="fail",
                    message="<img> 缺 alt 屬性 — 必須提供替代文字 (裝飾性圖片用 alt=\"\")",
                    node=img,
                )
            elif attr.kind == "empty":
                yield self._issue(
                    status="info",
                    message="<img> alt 為空字串 — 若為純裝飾性圖片正確；若為內容圖請補敘述",
                    node=img,
                )
            # literal non-empty → pass; HTML has no dynamic case
