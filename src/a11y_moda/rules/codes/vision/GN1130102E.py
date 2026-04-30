"""GN1130102E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class StructureSeparation(Rule):
    """GN1130102E — content structure should be separable from presentation."""

    meta = RuleMeta(rule_id="GN1130102E", guideline="1.3.1", level=Level.A,
        desc="從呈現當中抽離資訊與結構，以便啟用不同的呈現",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面結構是否清晰可分（標題 / 段落 / 清單 / 區塊明確）。

【fail（明顯）】
- 大字粗體段落但顯然不是真 heading（無階層感）
- 用空格 / 換行模擬列表
- 用圖片代文字標題

【pass】
- 標題層次清楚
- 段落 / 清單 / 區塊井然
- 有視覺結構

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷頁面結構是否清晰",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"結構與呈現未分離：{v[1]}",
                status="info",
            ))
