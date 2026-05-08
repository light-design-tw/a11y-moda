# a11y-moda — Generic AI Agent Integration

Platform-agnostic instructions for any LLM-based coding agent that can
shell out to `a11y-moda`. Tested patterns: Claude Code, Cursor, Copilot,
Aider, Cline, Continue, RooCode, custom MCP / OpenAI-tool agents.

Pin this file (or its content) into your agent's system prompt /
instructions / context.

---

## What `a11y-moda` is

CLI for **Taiwan MODA accessibility audits**. Three subcommands:

| Stage | Command | What |
|---|---|---|
| **Pre-write** | `a11y-moda rules ...` | Query MODA rule knowledge (no audit) |
| **Source** | `a11y-moda lint <paths>` | Tree-sitter AST checks on JSX/TSX/JS/HTML — no browser, no LLM, no network |
| **Rendered** | `a11y-moda scan <URL>` / `site <URL>` | Playwright + DOM probes, optional LLM judgement |

All three share the same `rule_id` namespace (HM/GN/CS/AR/FA/SC).

Authoritative spec: <https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md>

## Install (one-time)

```
pip install a11y-moda                 # lint + rules (lightweight, ~30MB)
pip install 'a11y-moda[scan]'         # add browser-based scan/site
playwright install chromium           # required for --render (~200MB binary)
```

If `a11y-moda` is missing, instruct the user to run the relevant install
command. **Do not auto-install.** The CLI emits a clear install message
when a missing-dependency code path is hit.

---

## Pre-write: query MODA rules before writing accessibility-sensitive code

Before generating or modifying any of these elements, **call `a11y-moda
rules search`** to load the relevant MODA rules:

```
<button>, <a href|onClick>, <form>, <input>, <textarea>, <select>, <label>,
<img>, <video>, <audio>, <iframe>, <picture>, <source>,
<table> (data tables), <dialog>, <details>, <summary>,
<svg> (interactive only),
ANY element with role=*, aria-*, tabindex
```

Query patterns:

```bash
# By element keyword (English aliases work — searches Chinese descriptions)
a11y-moda rules search button   --format json
a11y-moda rules search form     --format json
a11y-moda rules search image    --format json

# By WCAG SC
a11y-moda rules search 1.1.1    --format json

# By rule_id (full detail)
a11y-moda rules show HM1110100C --format json
a11y-moda explain HM1110100C    --format json   # short alias

# Filtered list
a11y-moda rules list --topic forms --level AA --format json
a11y-moda rules list --scope lint --format json    # lint-implementable
```

Each rule returns:

```json
{
  "rule_id": "HM1110100C",
  "guideline": "1.1.1",
  "level": 1,
  "level_name": "A",
  "desc": "圖片<img>組件需有替代文字(alt)屬性",
  "source": "freego",
  "runtime_authoritative": false,
  "wcag_url": "https://www.w3.org/WAI/WCAG21/quickref/#sc-1-1-1",
  "topic": "images",
  "scope": ["scan", "lint"]
}
```

Use the rule list to write code that satisfies them from the start.
**This is the proactive query pattern**: query rules → understand
constraints → write compliant code → verify with lint.

---

## Reactive: audit existing code

### Source-level lint (fastest, no browser)

```
a11y-moda lint <paths> --level AA --format json
```

Returns per-file `issues[]` with `rule_id`, `status`, `line`, `col`,
`message`. Use this between edits.

### Rendered-DOM scan (catches runtime issues)

```
a11y-moda scan <URL> --level AA --render --format json
a11y-moda scan <URL> --allow-private-hosts        # for localhost
a11y-moda scan <URL> --allow-file ./dist/index.html   # for build output
```

### Whole site

```
a11y-moda site <URL> --level AA --max-pages 30 --render --render-crawl --format json
```

Always parse JSON. Never rely on exit code (CLI exits 0 even with
issues); read `summary.fail` from the JSON.

---

## Triage status enum

| `status` | Meaning | Agent action |
|---|---|---|
| `fail` | AST or runtime confirmed violation | Suggest a code fix |
| `caveat` | Tool can't conclude — needs human / runtime / cross-file context | Surface as "needs review"; do NOT auto-fix |
| `needs_human` | Older alias for `caveat` | Same handling |
| `info` | Stylistic / borderline | Mention only if relevant |
| `pass` | Rule passed | Don't surface |
| `not_applicable` | Rule doesn't apply | Don't surface |

Common `caveat` causes:

1. **Cross-file wiring** — lint sees `<div onClick>` but not the
   sibling `useHotkeys("esc")` (since 0.2.1, lint downgrades these
   `runtime_authoritative` rules to `caveat` automatically with a
   note in the message)
2. **Third-party origin** — message starts with `[third-party: <origin>]`.
   Violation is in code from `<origin>` (e.g. `googleapis.com`). User
   declares in MODA 申請備註欄 (WCAG 2.1 §5.4 Partial Conformance);
   does NOT edit `node_modules/<origin>/...`.
3. **LLM unavailable** — rule needs LLM judgement, none configured. Don't
   suggest setting up LLM unless user asks.

---

## Anti-patterns

- ❌ Auto-installing playwright. Let user run the printed install command.
- ❌ Adding `--probe-modals` on production URLs (triggers booking /
  billing / analytics events).
- ❌ Treating `caveat` as `fail` and auto-editing.
- ❌ Recommending edits to third-party CDN code.
- ❌ Suggesting LLM endpoint setup before scanning.
- ❌ Recommending `eslint-plugin-jsx-a11y` *instead of* `a11y-moda lint`.
  They are complements — eslint plugin lacks MODA rule_id mapping.

---

## Suggested workflow loop

```
1. About to write/modify a11y-sensitive element
   → a11y-moda rules search <element> --format json
2. Write code informed by the rules
3. After save / before commit
   → a11y-moda lint <changed files> --level AA --format json
4. After deploy / dev server up
   → a11y-moda scan <URL> --render --format json
5. Pre-MODA submission
   → a11y-moda site <prod URL> --level AAA --render --render-crawl --format json
```

Steps 1, 3, 4, 5 all share the same MODA `rule_id` namespace — issues
can be reconciled across stages.

---

## When users ask about a11y in any language

Trigger words / phrases (any language) that mean "use a11y-moda":

```
"check a11y" / "audit accessibility" / "WCAG check" / "MODA 標章" /
"AAA 自評" / "無障礙檢查" / "accessibility audit" / "a11y review"
```

Default response template:

```
1. Detect SPA framework (next.config / vite.config / astro.config / etc.)
   → if SPA, plan to use --render
2. Detect dev server URL or production URL or local build
   → pick scan / site / lint accordingly
3. Pick level: default AA; AAA if user mentions "AAA" / "AAA 自評"
4. Run with --format json; parse output per triage rules
5. Surface fail items grouped by rule_id; list caveats separately
```
