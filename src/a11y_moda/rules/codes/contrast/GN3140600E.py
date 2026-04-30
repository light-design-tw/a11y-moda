"""GN3140600E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ..._lib.contrast_focus import _contrast_issues, _unmeasurable_samples, _AAA_NORMAL, _AAA_LARGE


@register
class ContrastAAA(Rule):
    """GN3140600E — text contrast 7:1 / large text 4.5:1."""

    meta = RuleMeta(
        rule_id="GN3140600E",
        guideline="1.4.6",
        level=Level.AAA,
        desc="文字(及影像文字)與文字後面的背景間，至少有7:1的對比值；大尺寸文字至少4.5:1",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used or not ctx.text_samples:
            return
        bad = _contrast_issues(ctx.text_samples, _AAA_NORMAL, _AAA_LARGE)
        if bad:
            first, threshold = bad[0]
            # AAA contrast is treated as info by default — many designs intentionally ship to AA only.
            status = "info" if not ctx.state.get("strict_aaa") else "fail"
            report.add(self._issue(
                message=f"AAA 對比 — 「{first.text[:30]}」 ratio={first.ratio:.2f}（要求 ≥{threshold}），共 {len(bad)} 處。",
                snippet=f"{first.selector} fg={first.fg} bg={first.bg}",
                status=status,
            ))
        # Caveat for samples we cannot measure (gradient/img bg, blend, filter, etc.)
        if ctx.state.get("strict_aaa"):
            unmeas = _unmeasurable_samples(ctx.text_samples)
            if unmeas:
                sample = unmeas[0]
                report.add(self._issue(
                    message=f"AAA 對比無法量測（{sample.unmeasurable_reason}）— 共 {len(unmeas)} 處需人工 review。",
                    snippet=f"{sample.selector} text={sample.text[:30]!r}",
                    status="caveat",
                ))
