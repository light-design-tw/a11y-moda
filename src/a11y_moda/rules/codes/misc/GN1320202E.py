"""GN1320202E rule."""
from __future__ import annotations
from urllib.parse import urlparse
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.extension_misc import _PROPRIETARY_EXT


@register
class DownloadsOpenFormat(Rule):
    """GN1320202E — downloadable files should prefer open formats over proprietary."""

    meta = RuleMeta(
        rule_id="GN1320202E",
        guideline="3.2.2",
        level=Level.A,
        desc="提供下載檔案格式為不需依賴特定文書商用軟體即能開啟之檔案",
        source="extension",
    )

    def _check(self, soup, report, *, html, url, ctx) -> None:
        offenders = []
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = (a.get("href") or "").strip().lower()
            path = urlparse(href).path
            for ext in _PROPRIETARY_EXT:
                if path.endswith(ext):
                    offenders.append((href, ext))
                    break
        if offenders:
            sample = offenders[0]
            report.add(self._issue(
                message=f"提供 {sample[1]} 等專有格式下載（共 {len(offenders)} 處），建議同時提供 PDF/HTML/ODT。",
                snippet=sample[0][:200],
                status="info",
            ))
