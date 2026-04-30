"""GN1140100E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class ColorConveysInfo(Rule):
    """GN1140100E — info conveyed by colour alone (e.g. red = error, no icon/text)."""

    meta = RuleMeta(rule_id="GN1140100E", guideline="1.4.1", level=Level.A,
        desc="確保所有藉由顏色所傳達出來的訊息，在沒有顏色後仍然能夠傳達出來",
        source="extension")

    SYSTEM = f"""你是台灣無障礙網頁稽核員，僅根據視覺截圖判斷。

【任務】判斷頁面是否有「僅靠顏色」傳達狀態 / 分類 / 重要性，且無圖示 / 文字 / 形狀補強。

【fail（明確違規）】
- 必填欄位僅紅星或紅框，沒有「必填」字樣
- 錯誤訊息僅紅字，沒有 ❌ icon 或「錯誤：」前綴
- 圖表分類僅靠顏色區別，沒有圖例 / 標籤
- 進度條僅靠紅綠表示成功失敗，無文字
- 連結僅靠下劃線移除後的顏色區別於內文（無底線）

【pass】
- 顏色搭配 icon、文字、形狀
- 圖表有完整圖例與標籤
- 連結有下劃線
- 截圖中無明顯顏色傳訊息情境

【unsure】
- 圖示細節難判斷
- 截圖只看到部分版面

【few-shot】
INPUT: 表單欄位旁有紅色 * 號和「必填」字樣
OUTPUT: VERDICT: pass / REASON: 紅色配合「必填」文字輔助

INPUT: 圓餅圖各區僅顏色不同，無標籤
OUTPUT: VERDICT: fail / REASON: 圖表分類僅靠顏色，缺圖例標籤

{_VISION_OUTPUT}"""

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷此截圖是否有純色傳達資訊的情況",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(message=f"疑似僅用顏色傳達訊息：{v[1]}", status="info"))
