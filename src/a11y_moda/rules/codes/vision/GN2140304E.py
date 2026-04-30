"""GN2140304E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class TextLegibility(Rule):
    """Replaces previous CS2240700E_V — judges general text legibility instead.

    Vision augment for visual legibility issues programmatic checks miss:
    text on busy backgrounds, very small fonts, low-contrast accents.
    """

    meta = RuleMeta(rule_id="GN2140304E", guideline="1.4.3", level=Level.AA,
        desc="文字易讀性整體視覺判斷",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面整體文字易讀性。

【fail】
- 文字疊在繁忙圖片背景上難以閱讀
- 大量極小字（< 12px 視覺判斷）
- 文字與背景顏色相近難以分辨
- 灰字 on 灰底 / 白字 on 淺背景

【pass】
- 主要文字清晰可讀
- 字級適中
- 對比充足

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷頁面整體文字易讀性",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"文字易讀性整體疑慮：{v[1]}",
                status="info",
            ))
