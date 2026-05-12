"""CS2240700E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register


@register
class FocusVisible(Rule):
    """CS2240700E — focused element must show a visible focus indicator."""

    meta = RuleMeta(
        rule_id="CS2240700E",
        guideline="2.4.7",
        level=Level.AA,
        desc="使用者介面取得焦點時，使其鍵盤焦點指示具高可見度",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used:
            return

        # Skip-link target visibility — when user activates "跳至主要內容",
        # the destination element should show a focus indicator. MODA flags
        # silent skip targets under 2.4.7.
        for d in getattr(ctx, "dialog_probes", []) or []:
            if d.kind != "skip-link":
                continue
            if d.opened and not d.skip_target_visible_focus:
                report.add(self._issue(
                    message=(
                        f"跳到主要內容連結「{d.trigger_text}」啟用後，目標位置無可見焦點指示，"
                        f"使用者不知道焦點已跳至何處。請在跳轉目標元素加上 :focus-visible 樣式。"
                    ),
                    snippet=f"trigger={d.trigger_selector}",
                ))
                break

        if not ctx.tab_stops:
            return
        invisible = [s for s in ctx.tab_stops if not s.has_visible_outline]
        if not invisible:
            return
        sample = invisible[0]
        report.add(self._issue(
            message=f"鍵盤焦點不可見 — {len(invisible)}/{len(ctx.tab_stops)} 個 focusable 元素缺 :focus-visible 樣式。",
            snippet=f"{sample.selector} text={sample.text!r}",
        ))
