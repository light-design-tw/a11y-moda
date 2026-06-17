"""FA1130114E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate


@register
class LayoutTableHasDataMarkup(Rule):
    """FA1130114E — a presentation/layout table must not carry th/caption/summary (1.3.1)."""

    meta = RuleMeta(
        rule_id="FA1130114E",
        guideline="1.3.1",
        level=Level.A,
        desc="排版用途的表格（role=presentation/none）不應使用 th、caption 或非空 summary，以免被報讀軟體當作資料表格",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # Complements HM1130107E (which flags UNMARKED suspected layout tables);
        # here the table IS declared presentation/none yet still carries data-
        # table semantics, which contradicts the role.
        for t in soup.find_all("table"):
            if not isinstance(t, Tag):
                continue
            role = (t.get("role") or "").strip().lower()
            if role not in ("presentation", "none"):
                continue
            offenders: list[str] = []
            if t.find("th"):
                offenders.append("th")
            if t.find("caption"):
                offenders.append("caption")
            if (t.get("summary") or "").strip():
                offenders.append("summary 屬性")
            if offenders:
                report.add(self._issue(
                    message=(
                        f"排版表格（role={role}）使用了 {'、'.join(offenders)} — 這些會讓報讀軟體將其"
                        f"當成資料表格報讀。請移除，或若實為資料表格則改用正確的資料表格標記。"
                    ),
                    snippet=truncate(str(t)),
                ))
                return
