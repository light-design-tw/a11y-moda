"""GN1240500E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class NavigationMechanismVision(Rule):
    """GN1240500E — site provides navigation / search mechanism."""

    meta = RuleMeta(rule_id="GN1240500E", guideline="2.4.5", level=Level.A,
        desc="提供網站導覽、導覽工具或機制、搜尋功能、網頁清單鏈結等功能",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面是否提供清楚的導覽機制。

【pass（任一即可）】
- 可見的主選單（水平 / 垂直 / 漢堡選單已展開）
- 搜尋框
- 麵包屑導覽
- 頁腳網站地圖鏈結

【fail】
- 整頁找不到任何導覽元素
- 漢堡選單在那但完全展不開（無文字輔助）

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        if soup.find("nav") or soup.find(attrs={"role": "navigation"}):
            return  # programmatic nav exists; trust it
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷頁面導覽機制是否充足",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(message=f"頁面缺少明顯導覽機制：{v[1]}", status="info"))
