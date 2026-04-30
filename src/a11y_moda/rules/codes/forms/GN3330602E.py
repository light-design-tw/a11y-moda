"""GN3330602E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


_SKIP_FORM_HINT_RE = re.compile(
    r"search|login|signin|sign-in|signup|sign-up|register|subscribe|newsletter"
    r"|搜尋|搜索|查詢|登入|登錄|註冊|訂閱",
    re.IGNORECASE,
)


@register
class SubmitConfirmationStep(Rule):
    """GN3330602E — substantial forms should provide confirmation/preview before submit."""

    meta = RuleMeta(
        rule_id="GN3330602E",
        guideline="3.3.6",
        level=Level.AAA,
        desc="法律、財務、個資等表單於送出前應提供確認、預覽或可修改機會",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        if self._check_static_dom(soup, report):
            return
        self._check_modal_forms(ctx, report)

    def _check_static_dom(self, soup: BeautifulSoup, report: PageReport) -> bool:
        for form in soup.find_all("form"):
            if not isinstance(form, Tag) or should_skip(form):
                continue
            inputs = []
            for tag in ("input", "textarea", "select"):
                for el in form.find_all(tag):
                    if not isinstance(el, Tag):
                        continue
                    t = (el.get("type") or "").lower()
                    if t in ("hidden", "submit", "button", "reset", "image"):
                        continue
                    inputs.append(el)
            if len(inputs) < 3:
                continue
            blob = " ".join([
                form.get("id") or "",
                form.get("name") or "",
                form.get("action") or "",
                " ".join(form.get("class") or []),
                form.get("aria-label") or "",
            ])
            if _SKIP_FORM_HINT_RE.search(blob):
                continue
            ident = form.get("id") or form.get("name") or "(無 id)"
            report.add(self._issue(
                message=f"表單 form#{ident} 有 {len(inputs)} 個輸入欄位，請人工確認送出前是否提供預覽／確認步驟。",
                snippet=truncate(str(form), 200),
                status="info",
            ))
            return True
        return False

    def _check_modal_forms(self, ctx, report: PageReport) -> None:
        if not ctx.form_sims:
            return
        for s in ctx.form_sims:
            if s.input_count < 3 or not s.has_required:
                continue
            report.add(self._issue(
                message=(
                    f"互動式表單 {s.selector} 有 {s.input_count} 個輸入欄位（modal 內，初始 DOM 不存在），"
                    "請人工確認送出前是否提供預覽／確認步驟。"
                ),
                status="info",
            ))
            return
