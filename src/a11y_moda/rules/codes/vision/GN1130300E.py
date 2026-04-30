"""GN1130300E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class SensoryReplacement(Rule):
    """GN1130300E — instructions don't rely solely on sensory characteristics."""

    meta = RuleMeta(rule_id="GN1130300E", guideline="1.3.3", level=Level.A,
        desc="針對若無文字項目識別則必須仰賴感官資訊才能理解的內容，提供文字項目識別",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面文字指示是否「僅靠感官資訊」（位置、形狀、大小、顏色、聲音）。

【fail】
- 「點擊右上方藍色按鈕」
- 「選擇圓形圖示」
- 「藍色標的代表新訊息」
- 任何僅靠位置 / 顏色 / 形狀的指示

【pass】
- 「點擊『儲存』按鈕」
- 「選擇右側『付款』選項」（位置 + 文字標籤）
- 截圖無感官指示

{_VISION_OUTPUT}"""

    _SENSORY_KW = ("右側", "左側", "右上", "左上", "右下", "左下", "藍色", "紅色", "綠色", "黃色",
                    "圓形", "方形", "三角", "上方", "下方")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        text = soup.get_text() or ""
        if not any(kw in text for kw in self._SENSORY_KW):
            return  # no sensory wording = nothing to check
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷頁面文字指示是否仰賴感官資訊",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(message=f"指示僅靠感官資訊：{v[1]}", status="info"))
