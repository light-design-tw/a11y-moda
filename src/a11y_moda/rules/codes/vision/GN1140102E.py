"""GN1140102E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class FormColorIndicatorWithText(Rule):
    """GN1140102E — form fields highlighted by colour need text cue too."""

    meta = RuleMeta(rule_id="GN1140102E", guideline="1.4.1", level=Level.A,
        desc="對有顏色的表單控制標題，提供文字線索提示",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷表單欄位的顏色提示是否伴隨文字。

【fail】
- 紅星 * 但無「必填」字樣
- 紅框驗證錯誤但無錯誤訊息文字
- 綠勾驗證成功但無「驗證成功」文字

【pass】
- 紅星 + 「* 為必填」說明
- 紅框 + 錯誤文字
- 截圖無表單，自動 pass

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        if not soup.find(["form", "input", "textarea", "select"]):
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷表單欄位顏色提示是否伴隨文字",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(message=f"表單顏色標示缺文字輔助：{v[1]}", status="info"))
