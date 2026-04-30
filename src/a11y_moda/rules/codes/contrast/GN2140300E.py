"""GN2140300E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ..._lib.contrast_focus import _contrast_issues, _unmeasurable_samples, _AA_NORMAL, _AA_LARGE


@register
class ContrastAA(Rule):
    """GN2140300E — text contrast 4.5:1 / large text 3:1."""

    meta = RuleMeta(
        rule_id="GN2140300E",
        guideline="1.4.3",
        level=Level.AA,
        desc="文字(及影像文字)與文字後面的背景間，至少有4.5:1的對比值；大尺寸文字至少3:1",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if not ctx.browser_used or not ctx.text_samples:
            return  # static-only scan; skip silently
        bad = _contrast_issues(ctx.text_samples, _AA_NORMAL, _AA_LARGE)
        if bad:
            first, threshold = bad[0]
            report.add(self._issue(
                message=f"對比值不足 — 「{first.text[:30]}」 ratio={first.ratio:.2f}（要求 ≥{threshold}），共 {len(bad)} 處。",
                snippet=f"{first.selector} fg={first.fg} bg={first.bg}",
            ))
        unmeas = _unmeasurable_samples(ctx.text_samples)
        if unmeas:
            sample = unmeas[0]
            report.add(self._issue(
                message=f"對比無法量測（{sample.unmeasurable_reason}）— 共 {len(unmeas)} 處需人工 review。",
                snippet=f"{sample.selector} text={sample.text[:30]!r}",
                status="caveat",
            ))
