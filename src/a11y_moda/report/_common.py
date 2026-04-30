"""Status badges + colors shared by MD and HTML renderers."""
from __future__ import annotations
from typing import Literal

from ..models import ScanReport


GroupBy = Literal["rule", "wcag", "url"]


STATUS_BADGE = {
    "fail": "🔴 FAIL",
    "info": "🟡 INFO",
    "caveat": "⚠️ CAVEAT",
    "pass": "✅ PASS",
}

STATUS_COLOR = {
    "fail": "#d32f2f",
    "info": "#fbc02d",
    "caveat": "#ed6c02",
    "pass": "#2e7d32",
}


def site_totals(scan: ScanReport) -> dict:
    fail = info = caveat = 0
    for p in scan.pages:
        for i in p.issues:
            if i.status == "fail":
                fail += 1
            elif i.status == "info":
                info += 1
            elif i.status == "caveat":
                caveat += 1
    return {"fail": fail, "info": info, "caveat": caveat}
