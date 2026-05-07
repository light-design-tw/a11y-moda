"""Source-level a11y lint for JSX/TSX/HTML.

Companion to the rendered-DOM `scan` / `site` commands. Where scan walks
a Playwright-rendered DOM and produces full-fidelity findings, lint
walks the static AST of source files (JSX, TSX, HTML) before the page
is built — fast, deterministic, no LLM, no browser.

Three-tier issue status (same enum as scan):

    fail    AST confirmed a violation (e.g. <img> with no alt attribute at all).
    caveat  AST sees a relevant pattern but cannot statically confirm the
            outcome — typical for dynamic values (`alt={someVar}`), component
            abstraction (`<MyImage />`), or rules whose verdict requires
            runtime CSS / DOM. LLM agents reading the report decide whether
            to act on these.
    info    AST advisory only — pattern is borderline, depends on intent
            (e.g. `alt=""` may be correct for decorative images).

Rules share rule_id with the scan stage so a finding's identity stays
stable across the whole pipeline (lint → build → scan → MODA submission).
"""
