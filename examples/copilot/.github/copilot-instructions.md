# a11y-moda — GitHub Copilot integration

GitHub Copilot Chat auto-loads `.github/copilot-instructions.md` when
chatting in this repo. Place this file there.

Use the `a11y-moda` Python CLI for Taiwan MODA accessibility checks.
Audits **rendered DOM** (`scan` / `site`) and **source code** (`lint`)
against MODA rule_id (HM/GN/CS/AR/FA/SC) mapped to WCAG 2.1.

Authoritative spec: [`docs/AI_INTEGRATION.md`](https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md).

## Pre-flight (one-time)

```
pip install a11y-moda                 # lint + rules subcommand only
pip install 'a11y-moda[scan]'         # add browser-based scan/site
playwright install chromium           # required for --render
```

If `a11y-moda` not installed, instruct the user to run the first line.
Do not auto-install.

## Proactive rule lookup — call BEFORE writing accessible elements

When about to write or modify these JSX/TSX/HTML elements, **first call**
`a11y-moda rules search` to load relevant MODA rules, then write code
that satisfies them:

```
<button>, <a> with onClick or href
<form>, <input>, <textarea>, <select>, <label>
<img>, <video>, <audio>, <iframe>, <picture>, <source>
<table> (data, not layout)
<dialog>, <details>, <summary>
<svg> with onClick or interactive role
Anything with role=*, aria-*, tabindex
```

Common queries:

```bash
a11y-moda rules search button --format json    # English aliases work
a11y-moda rules search 1.1.1  --format json    # by WCAG SC
a11y-moda rules show HM1110100C --format json  # full metadata
a11y-moda explain HM1110100C --format json     # short alias
a11y-moda rules list --topic forms --level AA --format json
```

JSON includes `rule_id`, `guideline`, `level`, `level_name`, `desc`,
`source`, `topic`, `scope`, `runtime_authoritative`, `wcag_url`.

## Reactive audit

Single page (dev server running):

```
a11y-moda scan http://localhost:3000/path \
  --level AA --render --allow-private-hosts --format json
```

Source lint (no browser, no LLM, no network):

```
a11y-moda lint src/ --level AA --format json
```

Whole site (CI / pre-deploy):

```
a11y-moda site https://example.com --level AA --max-pages 30 \
  --render --render-crawl --format json
```

Always use `--format json` and parse output. Never rely on exit code to
detect violations (CLI exits 0 even when issues found); read
`summary.fail` from JSON.

## Triage

| `status` | Action |
|---|---|
| `fail` | Suggest a code fix. |
| `caveat` / `needs_human` | "Needs review"; do NOT auto-fix. Possible causes: cross-file wiring lint can't see; third-party violation; LLM unavailable. |
| `info` | Mention only if relevant. |
| `pass` / `not_applicable` | Don't surface. |

`[third-party: <origin>] ...` caveats: violation in `<origin>` code (e.g.
`googleapis.com`). User declares in MODA 申請備註欄 (WCAG 2.1 §5.4
Partial Conformance), NOT edit their codebase.

## Anti-patterns (do NOT)

- Auto-install playwright. Let user run the printed install command.
- Add `--probe-modals` on production URLs (triggers booking / billing).
- Recommend editing JSX for `scan` issues without first running `lint`.
- Suggest LLM endpoint setup before scanning. LLM is optional.
- Recommend `eslint-plugin-jsx-a11y` over `a11y-moda lint`. Use together —
  eslint plugin has no MODA rule_id mapping; a11y-moda does.

## Note on Copilot mechanism

- `.github/copilot-instructions.md` is auto-loaded by Copilot Chat for
  this repo. No skill / extension install needed.
- For Copilot Workspace and Copilot Skillsets (REST-endpoint
  integrations), see [`docs/AI_INTEGRATION.md`](https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md)
  §11.4. Currently this file (chat instructions) is the supported path.

For full reference: <https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md>
