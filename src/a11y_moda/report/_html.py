"""HTML renderer — interactive 3-tab view (rule / WCAG / page)."""
from __future__ import annotations
import html
from datetime import datetime

from ..models import PageReport, ScanReport
from ._aggregate import aggregate_by_rule, aggregate_by_wcag
from ._common import STATUS_COLOR, site_totals


def _badge(status: str) -> str:
    return f'<span class="badge" style="background:{STATUS_COLOR.get(status, "#888")}">{status}</span>'


def page_to_html_block(p: PageReport, *, default_open: bool = False) -> str:
    counts = {"fail": 0, "info": 0, "caveat": 0}
    for i in p.issues:
        counts[i.status] = counts.get(i.status, 0) + 1
    summary_label = (
        f"<span class='url'>{html.escape(p.url)}</span> "
        f"&nbsp; HTTP {p.status_code} "
        f"&nbsp; {_badge('fail') if counts['fail'] else ''} {counts['fail']} fail "
        f"· {counts['info']} info · {counts['caveat']} caveat"
    )
    open_attr = " open" if default_open or counts["fail"] > 0 else ""
    rows = []
    for i in p.issues:
        rows.append(
            "<tr>"
            f"<td>{_badge(i.status)}</td>"
            f"<td><code>{html.escape(i.rule_id)}</code></td>"
            f"<td>{html.escape(i.guideline)}</td>"
            f"<td>{i.level}</td>"
            f"<td>{html.escape(i.message)}<div class='snippet'>{html.escape(i.snippet)}</div></td>"
            "</tr>"
        )
    table = (
        "<table><thead><tr><th>Status</th><th>Rule</th><th>WCAG</th><th>Lv</th><th>Detail</th></tr></thead>"
        f"<tbody>{''.join(rows) or '<tr><td colspan=5>No issues</td></tr>'}</tbody></table>"
    )
    return f"<details{open_attr}><summary>{summary_label}</summary>{table}</details>"


_HTML_TEMPLATE = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<title>{title_html}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 14px/1.55 -apple-system, "Segoe UI", "Noto Sans TC", sans-serif; max-width: 1280px; margin: 1em auto; padding: 0 1em; color: #1d1d1d; background: #fafafa; }}
  h1, h2 {{ border-bottom: 1px solid #d8d8d8; padding-bottom: .3em; margin-top: 1.5em; }}
  table {{ border-collapse: collapse; width: 100%; margin: .8em 0; background: #fff; }}
  th, td {{ border: 1px solid #e0e0e0; padding: .45em .65em; text-align: left; vertical-align: top; }}
  th {{ background: #f3f3f3; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  code {{ background: #eef0f2; padding: 1px 5px; border-radius: 3px; font-family: "JetBrains Mono", Consolas, monospace; font-size: 12.5px; }}
  .badge {{ display: inline-block; padding: 2px 7px; border-radius: 10px; color: #fff; font-size: 11.5px; font-weight: 600; text-transform: uppercase; }}
  .summary-card {{ display: inline-block; background: #fff; border-radius: 8px; padding: .7em 1.2em; margin: 0 .5em .5em 0; border: 1px solid #e0e0e0; }}
  .summary-card strong {{ display: block; font-size: 22px; margin-top: .2em; }}
  details {{ margin: .6em 0; background: #fff; border-radius: 6px; border: 1px solid #e0e0e0; }}
  summary {{ cursor: pointer; padding: .55em .8em; font-weight: 500; }}
  summary:hover {{ background: #f6f6f6; }}
  .url {{ font-family: monospace; word-break: break-all; }}
  .small {{ color: #666; font-size: 12px; }}
  .snippet {{ background: #fff7e0; padding: .3em .5em; border-left: 3px solid #fbc02d; margin: .3em 0 0; font-family: monospace; font-size: 12px; word-break: break-all; }}
  .tabs {{ display: flex; gap: 4px; margin: 1.2em 0 0; border-bottom: 2px solid #d8d8d8; }}
  .tab-btn {{ padding: .55em 1.1em; cursor: pointer; border: none; background: none; font-size: 14px; color: #666; border-bottom: 3px solid transparent; margin-bottom: -2px; font-weight: 500; }}
  .tab-btn:hover {{ color: #1565c0; }}
  .tab-btn.active {{ color: #1565c0; border-color: #1565c0; }}
  .tab-panel {{ display: none; padding-top: 1em; }}
  .tab-panel.active {{ display: block; }}
  .filter-bar {{ display: flex; gap: 8px; align-items: center; margin: .8em 0; }}
  .filter-bar input, .filter-bar select {{ padding: .35em .5em; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1a1a1a; color: #e8e8e8; }}
    h1, h2 {{ border-color: #333; }}
    table, .summary-card, details, th {{ background: #222; border-color: #333; }}
    th {{ background: #2a2a2a; }}
    tr:nth-child(even) td {{ background: #1f1f1f; }}
    code {{ background: #2a2a2a; }}
    summary:hover {{ background: #2a2a2a; }}
    .snippet {{ background: #3a2f10; color: #f8d878; }}
    .tab-btn {{ color: #aaa; }}
    .tab-btn.active {{ color: #6cb1ff; border-color: #6cb1ff; }}
  }}
</style>
</head>
<body>
<h1>{title_html}</h1>
<p class="small">Generated {now}</p>

<h2>Site summary</h2>
<div>
  <span class="summary-card">Pages<strong>{pages_count}</strong></span>
  <span class="summary-card" style="background:#fde7e7;color:#c62828">fail<strong>{site_fail}</strong></span>
  <span class="summary-card" style="background:#fff8e1;color:#f57f17">info<strong>{site_info}</strong></span>
  <span class="summary-card" style="background:#fff0e0;color:#ed6c02">caveat<strong>{site_caveat}</strong></span>
</div>

<div class="tabs">
  <button class="tab-btn active" data-tab="rule">By rule</button>
  <button class="tab-btn" data-tab="wcag">By WCAG guideline</button>
  <button class="tab-btn" data-tab="url">By page</button>
</div>

<div id="tab-rule" class="tab-panel active">
{by_rule_html}
</div>

<div id="tab-wcag" class="tab-panel">
{by_wcag_html}
</div>

<div id="tab-url" class="tab-panel">
{by_url_html}
</div>

<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>
"""


def _html_by_rule(scan: ScanReport) -> str:
    rows = aggregate_by_rule(scan)
    if not rows:
        return "<p>No issues.</p>"
    out = []
    for r in rows:
        sample_pages = "<br>".join(f"<code>{html.escape(u)}</code>" for u, _, _ in r["pages"][:5])
        more = f"<br><em class='small'>+{len(r['pages']) - 5} more</em>" if len(r["pages"]) > 5 else ""
        sample_msg = ""
        if r["pages"]:
            _, msg, snippet = r["pages"][0]
            sample_msg = f"<div class='small'>例: {html.escape(msg[:200])}</div>"
            if snippet:
                sample_msg += f"<div class='snippet'>{html.escape(snippet[:200])}</div>"
        out.append(
            f"<details{' open' if r['status'] == 'fail' else ''}>"
            f"<summary>{_badge(r['status'])} <code>{html.escape(r['rule_id'])}</code> — WCAG {html.escape(r['guideline'])} (Lv {r['level']}) "
            f"· <strong>{len(r['pages'])} pages</strong> · {html.escape(r['desc'])}</summary>"
            f"<div style='padding:.5em .8em'>{sample_msg}<div class='small' style='margin-top:.5em'>"
            f"<strong>Affected pages ({len(r['pages'])}):</strong><br>{sample_pages}{more}</div></div>"
            f"</details>"
        )
    return "".join(out)


def _html_by_wcag(scan: ScanReport) -> str:
    rows = aggregate_by_wcag(scan)
    if not rows:
        return "<p>No issues.</p>"
    body = []
    body.append("<table><thead><tr><th>WCAG</th><th>Lv</th><th>Rules</th><th>Pages</th><th>🔴 fail</th><th>🟡 info</th><th>⚠️ caveat</th></tr></thead><tbody>")
    for r in rows:
        rids = "<br>".join(f"<code>{html.escape(x)}</code>" for x in r["rule_ids"])
        body.append(
            f"<tr><td><strong>{html.escape(r['guideline'])}</strong></td>"
            f"<td>{r['level']}</td>"
            f"<td>{rids}</td>"
            f"<td>{len(r['pages'])}</td>"
            f"<td>{r['fail_count']}</td>"
            f"<td>{r['info_count']}</td>"
            f"<td>{r['caveat_count']}</td></tr>"
        )
    body.append("</tbody></table>")
    return "".join(body)


def _html_by_url(scan: ScanReport) -> str:
    if not scan.pages:
        return "<p>No pages scanned.</p>"
    out = []
    for p in sorted(scan.pages, key=lambda x: (-sum(1 for i in x.issues if i.status == "fail"), x.url)):
        out.append(page_to_html_block(p))
    return "".join(out)


def scan_to_html(scan: ScanReport, *, title: str = "Accessibility Scan Report") -> str:
    site = site_totals(scan)
    return _HTML_TEMPLATE.format(
        title_html=html.escape(title),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        pages_count=len(scan.pages),
        site_fail=site["fail"],
        site_info=site["info"],
        site_caveat=site["caveat"],
        by_rule_html=_html_by_rule(scan),
        by_wcag_html=_html_by_wcag(scan),
        by_url_html=_html_by_url(scan),
    )
