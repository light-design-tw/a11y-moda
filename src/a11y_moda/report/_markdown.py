"""Markdown renderer — supports group-by rule / wcag / url."""
from __future__ import annotations
from datetime import datetime

from ..models import PageReport, ScanReport
from ._aggregate import aggregate_by_rule, aggregate_by_url, aggregate_by_wcag
from ._common import GroupBy, STATUS_BADGE, site_totals


def page_to_markdown(p: PageReport) -> str:
    """Single-page report (used by `scan` command, not `site`)."""
    lines: list[str] = [f"## {p.url}"]
    lines.append(f"- HTTP: `{p.status_code}`")
    if p.fetch_error:
        lines.append(f"- Fetch error: `{p.fetch_error}`")
    counts = {"fail": 0, "info": 0, "caveat": 0}
    for i in p.issues:
        counts[i.status] = counts.get(i.status, 0) + 1
    lines.append(f"- Counts: 🔴 {counts['fail']} fail · 🟡 {counts['info']} info · ⚠️ {counts['caveat']} caveat")
    if not p.issues:
        lines.append("\n_No issues._")
        return "\n".join(lines)
    lines.append("")
    lines.append("| Status | Rule | WCAG | Level | Message |")
    lines.append("|---|---|---|---|---|")
    for i in p.issues:
        msg = i.message.replace("|", r"\|").replace("\n", " ")
        lines.append(f"| {STATUS_BADGE.get(i.status, i.status)} | `{i.rule_id}` | {i.guideline} | {i.level} | {msg} |")
    return "\n".join(lines)


def scan_to_markdown(scan: ScanReport, *, title: str = "Accessibility Scan Report",
                     group_by: GroupBy = "rule") -> str:
    site = site_totals(scan)
    lines: list[str] = [
        f"# {title}",
        "",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "## Site summary",
        f"- Pages scanned: **{len(scan.pages)}**",
        f"- 🔴 fail: **{site['fail']}** · 🟡 info: **{site['info']}** · ⚠️ caveat: **{site['caveat']}**",
        "",
    ]
    if group_by == "rule":
        lines.extend(_md_by_rule(scan))
        lines.append("")
        lines.extend(_md_by_wcag(scan, condensed=True))
        lines.append("")
        lines.extend(_md_by_url(scan, condensed=True))
    elif group_by == "wcag":
        lines.extend(_md_by_wcag(scan))
        lines.append("")
        lines.extend(_md_by_rule(scan, condensed=True))
        lines.append("")
        lines.extend(_md_by_url(scan, condensed=True))
    else:  # url
        lines.extend(_md_by_url(scan))
        lines.append("")
        lines.extend(_md_by_rule(scan, condensed=True))
    return "\n".join(lines)


def _md_by_rule(scan: ScanReport, *, condensed: bool = False) -> list[str]:
    rows = aggregate_by_rule(scan)
    if not rows:
        return []
    lines = ["## Issues by rule", ""]
    if condensed:
        lines.append("| Status | Rule | WCAG | Lv | Pages | Description |")
        lines.append("|---|---|---|---|---|---|")
        for r in rows:
            desc = r["desc"].replace("|", r"\|")
            lines.append(
                f"| {STATUS_BADGE.get(r['status'], r['status'])} | `{r['rule_id']}` | {r['guideline']} "
                f"| {r['level']} | {len(r['pages'])} | {desc} |"
            )
        return lines
    for r in rows:
        lines.append(f"### {STATUS_BADGE.get(r['status'], r['status'])} `{r['rule_id']}` — WCAG {r['guideline']} (Level {r['level']})")
        lines.append(f"_{r['desc']}_")
        lines.append("")
        lines.append(f"**Pages affected: {len(r['pages'])}**")
        sample = r['pages'][:3]
        for url, msg, snippet in sample:
            short_msg = msg.replace("\n", " ").strip()[:160]
            lines.append(f"- `{url}`")
            lines.append(f"  - {short_msg}")
            if snippet:
                snip = snippet.replace("`", "'").replace("\n", " ")[:140]
                lines.append(f"  - 證據：`{snip}`")
        if len(r['pages']) > 3:
            lines.append(f"- _…還有 {len(r['pages']) - 3} 個頁面_")
        lines.append("")
    return lines


def _md_by_wcag(scan: ScanReport, *, condensed: bool = False) -> list[str]:
    rows = aggregate_by_wcag(scan)
    if not rows:
        return []
    if condensed:
        lines = ["## WCAG guideline summary", "", "| WCAG | Lv | Rules | Pages | Fail | Info |", "|---|---|---|---|---|---|"]
        for r in rows:
            rids = ", ".join(r["rule_ids"][:4])
            if len(r["rule_ids"]) > 4:
                rids += f" (+{len(r['rule_ids']) - 4})"
            lines.append(f"| {r['guideline']} | {r['level']} | {rids} | {len(r['pages'])} | {r['fail_count']} | {r['info_count']} |")
        return lines
    lines = ["## Issues by WCAG guideline", ""]
    for r in rows:
        lines.append(f"### WCAG {r['guideline']} (Level {r['level']})")
        rids = ", ".join(f"`{x}`" for x in r["rule_ids"])
        lines.append(f"- 規則: {rids}")
        lines.append(f"- 影響頁數: {len(r['pages'])}")
        lines.append(f"- 🔴 fail: {r['fail_count']} · 🟡 info: {r['info_count']} · ⚠️ caveat: {r['caveat_count']}")
        lines.append("")
    return lines


def _md_by_url(scan: ScanReport, *, condensed: bool = False) -> list[str]:
    rows = aggregate_by_url(scan)
    if not rows:
        return []
    lines = ["## Per-page summary" if condensed else "## Per-page detail", ""]
    if condensed:
        lines.append("| URL | HTTP | 🔴 | 🟡 | ⚠️ | Rules |")
        lines.append("|---|---|---|---|---|---|")
        for r in rows:
            rids = ", ".join(f"`{x}`" for x in r["rule_ids"][:5])
            if len(r["rule_ids"]) > 5:
                rids += f" (+{len(r['rule_ids']) - 5})"
            url_disp = r["url"]
            if len(url_disp) > 60:
                url_disp = "…" + url_disp[-58:]
            lines.append(f"| `{url_disp}` | {r['status_code']} | {r['fail']} | {r['info']} | {r['caveat']} | {rids} |")
        return lines
    for r in rows:
        lines.append(f"### {r['url']}")
        lines.append(f"- HTTP `{r['status_code']}` · 🔴 {r['fail']} · 🟡 {r['info']} · ⚠️ {r['caveat']}")
        if r["fetch_error"]:
            lines.append(f"- Fetch error: `{r['fetch_error']}`")
        if not r["issues"]:
            lines.append("- _No issues._")
            lines.append("")
            continue
        lines.append("")
        lines.append("| Status | Rule | WCAG | Lv | Message |")
        lines.append("|---|---|---|---|---|")
        for i in r["issues"]:
            msg = i.message.replace("|", r"\|").replace("\n", " ")
            lines.append(f"| {STATUS_BADGE.get(i.status, i.status)} | `{i.rule_id}` | {i.guideline} | {i.level} | {msg} |")
        lines.append("")
    return lines
