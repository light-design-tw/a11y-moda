"""HM2130500E rule."""
from __future__ import annotations
from urllib.parse import urlparse
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import truncate


@register
class AutocompleteValueValid(Rule):
    """HM2130500E / FA2130501E — autocomplete attribute must use a recognised token."""

    _ALLOWED = {
        "on", "off",
        "name", "honorific-prefix", "given-name", "additional-name", "family-name", "honorific-suffix", "nickname",
        "email", "username", "new-password", "current-password", "one-time-code",
        "organization-title", "organization", "street-address", "address-line1", "address-line2", "address-line3",
        "address-level1", "address-level2", "address-level3", "address-level4",
        "country", "country-name", "postal-code",
        "cc-name", "cc-given-name", "cc-additional-name", "cc-family-name",
        "cc-number", "cc-exp", "cc-exp-month", "cc-exp-year", "cc-csc", "cc-type",
        "transaction-currency", "transaction-amount",
        "language", "bday", "bday-day", "bday-month", "bday-year", "sex",
        "url", "photo",
        "tel", "tel-country-code", "tel-national", "tel-area-code", "tel-local", "tel-extension",
        "impp",
    }

    meta = RuleMeta(
        rule_id="HM2130500E",
        guideline="1.3.5",
        level=Level.AA,
        desc="使用HTML 5.2自動完成之屬性",
        source="extension",
    )

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(attrs={"autocomplete": True}):
            if not isinstance(el, Tag):
                continue
            tokens = (el.get("autocomplete") or "").strip().lower().split()
            if not tokens:
                continue
            for tok in tokens:
                if tok in self._ALLOWED or tok.startswith("section-") or tok in ("billing", "shipping", "home", "work", "mobile", "fax", "pager"):
                    continue
                report.add(self._issue(
                    message=f"autocomplete 屬性值「{tok}」非 HTML5.2 合法 token。",
                    snippet=truncate(str(el), 200),
                ))
                return
