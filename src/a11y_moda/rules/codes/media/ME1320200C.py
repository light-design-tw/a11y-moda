"""ME1320200C rule."""
from __future__ import annotations
from urllib.parse import urlsplit
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

# Spec lists ODF / PDF / HTML as the expected open formats for downloads.
# Flag the unambiguously proprietary document/office formats; leave anything
# open or non-document (images, archives, media) alone to avoid false fails.
_PROPRIETARY_EXT = {
    "doc", "docx", "xls", "xlsx", "ppt", "pptx", "pps", "ppsx",
    "hwp", "wpd", "pages", "key", "numbers",
}


def _ext(href: str) -> str:
    path = urlsplit(href).path
    dot = path.rfind(".")
    return path[dot + 1:].lower() if dot >= 0 else ""


@register
class DownloadsUseOpenFormat(Rule):
    """ME1320200C — downloadable files should be an open format (ODF/PDF/HTML)."""

    meta = RuleMeta(
        rule_id="ME1320200C",
        guideline="3.2.2",
        level=Level.A,
        desc="提供下載之檔案格式應為開放格式，如ODF、PDF、HTML等檔案格式",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for a in soup.find_all("a"):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            href = (a.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            ext = _ext(href)
            if ext in _PROPRIETARY_EXT:
                report.add(self._issue(
                    message=(
                        f"提供下載的檔案為非開放格式（.{ext}）。"
                        "建議改提供開放格式（ODF、PDF、HTML 等）版本，或同時併陳開放格式。"
                    ),
                    snippet=truncate(str(a)),
                ))
