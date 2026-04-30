"""Aggregation helpers — group issues by rule / WCAG guideline / URL."""
from __future__ import annotations

from ..models import ScanReport


def aggregate_by_rule(scan: ScanReport) -> list[dict]:
    """One entry per rule_id with affected pages and counts."""
    agg: dict[str, dict] = {}
    for page in scan.pages:
        for issue in page.issues:
            rec = agg.setdefault(issue.rule_id, {
                "rule_id": issue.rule_id,
                "guideline": issue.guideline,
                "level": int(issue.level),
                "desc": issue.desc,
                "status": issue.status,
                "pages": [],
            })
            rec["pages"].append((page.url, issue.message, issue.snippet))
    rows = list(agg.values())
    status_order = {"fail": 0, "info": 1, "caveat": 2, "pass": 3}
    rows.sort(key=lambda r: (status_order.get(r["status"], 9), -len(r["pages"]), r["rule_id"]))
    return rows


def aggregate_by_wcag(scan: ScanReport) -> list[dict]:
    """Group by WCAG guideline (e.g. 1.4.3, 2.4.4)."""
    agg: dict[str, dict] = {}
    for page in scan.pages:
        for issue in page.issues:
            rec = agg.setdefault(issue.guideline, {
                "guideline": issue.guideline,
                "level": int(issue.level),
                "rule_ids": set(),
                "pages": set(),
                "fail_count": 0,
                "info_count": 0,
                "caveat_count": 0,
            })
            rec["rule_ids"].add(issue.rule_id)
            rec["pages"].add(page.url)
            if issue.status == "fail":
                rec["fail_count"] += 1
            elif issue.status == "info":
                rec["info_count"] += 1
            elif issue.status == "caveat":
                rec["caveat_count"] += 1
    rows = list(agg.values())
    for r in rows:
        r["rule_ids"] = sorted(r["rule_ids"])
        r["pages"] = sorted(r["pages"])
    rows.sort(key=lambda r: (-r["fail_count"], -r["info_count"], r["guideline"]))
    return rows


def aggregate_by_url(scan: ScanReport) -> list[dict]:
    """Per-page summary with rule IDs only (compact)."""
    out = []
    for p in scan.pages:
        rule_ids = sorted({i.rule_id for i in p.issues})
        out.append({
            "url": p.url,
            "status_code": p.status_code,
            "fetch_error": p.fetch_error,
            "fail": sum(1 for i in p.issues if i.status == "fail"),
            "info": sum(1 for i in p.issues if i.status == "info"),
            "caveat": sum(1 for i in p.issues if i.status == "caveat"),
            "issues": p.issues,
            "rule_ids": rule_ids,
        })
    out.sort(key=lambda r: (-r["fail"], -r["info"], r["url"]))
    return out
