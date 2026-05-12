"""GN1240301E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class TabOrderHasFocusables(Rule):
    """GN1240301E — page must have focusable elements with logical tab order."""

    meta = RuleMeta(
        rule_id="GN1240301E",
        guideline="2.4.3",
        level=Level.A,
        desc="在鏈結、表單控制元件、物件間建立合乎邏輯的跳位順序",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used:
            return

        # Modal / menu without focus trap → next Tab leaves the dialog and
        # walks the underlying page. MODA AAA flags this under 2.4.3.
        for d in getattr(ctx, "dialog_probes", []) or []:
            if d.kind == "skip-link":
                continue  # handled by CS2240700E
            if d.opened and not d.focus_trapped:
                report.add(self._issue(
                    message=(
                        f"觸發「{d.trigger_text}」開啟後，下一個焦點未進入該容器內，"
                        f"鍵盤跳位順序與視覺結構不符。建議於開啟時將焦點移入容器，"
                        f"關閉時將焦點還回觸發元件。"
                    ),
                    snippet=f"trigger={d.trigger_selector}",
                ))
                break

        if not ctx.tab_stops:
            report.add(self._issue(message="頁面無任何可由鍵盤聚焦之元件，鍵盤使用者無法操作。"))
            return
        out_of_viewport = [s for s in ctx.tab_stops if not s.in_viewport]
        # Only flag if more than half of stops are off-screen — usually a sign of broken order.
        if len(out_of_viewport) > len(ctx.tab_stops) / 2 > 0:
            sample = out_of_viewport[0]
            report.add(self._issue(
                message=f"超過半數 tab 焦點落在視窗外（{len(out_of_viewport)}/{len(ctx.tab_stops)}），可能是 tab 順序與視覺順序不一致。",
                snippet=f"{sample.selector} text={sample.text!r}",
            ))
