# AI Agent Integration Guide

> **Audience:** AI coding agents (Claude Code, Cursor, Copilot, Aider, GitHub Copilot Workspace, custom LLM agents). This document is the contract for how agents should invoke `a11y-moda` and interpret its output. Read this before suggesting commands or parsing results.
>
> **Audience NOT:** end users. End users read [README.md](../README.md). If you are a human looking for a tutorial, you are in the wrong file.

---

## 1. Purpose

`a11y-moda` is a **CLI** that audits a rendered web page (or a whole site) against MODA's published WCAG rule codes (HM/GN/CS/AR/FA/SC) and emits structured findings. It is designed to be **scripted**, not interactively driven. Every command emits stable JSON; every issue carries a stable `rule_id` and WCAG `guideline` reference.

### What `a11y-moda` is good at (use it)

- **Knowledge service** (`a11y-moda rules`, since 0.3.0) — query MODA rule metadata (rule_id, WCAG SC, level, desc, topic, scope) for any element / keyword / WCAG SC. Use **before** writing accessibility-sensitive code so the agent writes compliant code from the start.
- **Source-level lint** (`a11y-moda lint`, since 0.2.0) — tree-sitter AST checks across JSX/TSX/JS/HTML, MODA `rule_id` annotated, three-tier status (`fail` / `caveat` / `info`). No browser, no LLM, no network. Use during write/edit/save.
- Auditing **rendered DOM** (Playwright Chromium) — catches things AST linters can't see (focus order, contrast, ARIA state, modal focus trap, runtime alt text)
- Producing **MODA-aligned reports** — every issue maps 1:1 to a MODA rule code, suitable for 標章 self-evaluation submission
- **AAA-level coverage** — implements 18/20 of MODA's AAA self-evaluation questions automatically; remaining 2 emit informative `caveat` issues
- **Site-wide crawl + audit** — sitemap-first, BFS fallback
- **Local build-output audit** (`--allow-file`, since 0.2.0) — scan `dist/` / `out/` directly from disk, no dev server required
- **Third-party violation segregation** — Google CSE / external CDN issues auto-tagged `[third-party: <origin>]` and downgraded to `caveat` (site author cannot fix external resources directly)

### What `a11y-moda` is NOT for (don't reach for it)

- **Replacing screen reader testing** — runtime DOM analysis is necessary but not sufficient. Tell the user to also test with NVDA/VoiceOver.
- **Replacing the official MODA Freego tool for final certification** — `a11y-moda` complements Freego (gives CLI/CI/AI workflow); does not replace official audit.
- **Cross-file taint / data-flow analysis** — `lint` is single-file AST. Cross-file unused-component detection or full data-flow is out of scope.

---

## 2. When to invoke

Trigger on these intents (in any language):

- "check accessibility" / "audit a11y" / "WCAG check" / "無障礙檢查"
- "MODA 標章" / "MODA certification" / "Taiwan accessibility"
- "AAA self-eval" / "AAA 自評"
- "after I deploy, verify the site" / "production a11y monitor"
- "compare a11y between branches" / "regression check"

**Do NOT** trigger when:
- User wants source-level a11y feedback while writing JSX → recommend `eslint-plugin-jsx-a11y`
- User wants to fix issues without context — first scan, then fix; don't blind-edit
- User has not deployed or run a dev server — see §4 for local workflow

---

## 3. Pick command: `rules` vs `lint` vs `scan` vs `site`

```
a11y-moda rules ...       → query MODA rule knowledge (no audit)
a11y-moda lint <paths...> → source files / dirs (tree-sitter AST, no browser)
a11y-moda scan <URL>      → one page (rendered DOM)
a11y-moda site <URL>      → whole site (sitemap → BFS, rendered DOM)
```

| Situation | Use |
|---|---|
| **Pre-write**: about to generate `<button>` / `<form>` / `<img>` / etc. | `rules search <element>` (proactive) |
| User asks about specific rule_id or WCAG SC | `rules show <RULE_ID>` or `explain <RULE_ID>` |
| User editing source, wants pre-build feedback | `lint src/` (or specific files) |
| User just saved a JSX/HTML file | `lint <file>` (single file is fine) |
| CI gating before deploy (no live URL yet) | `lint --strict` (exits non-zero on any issue) |
| User points at one page (`/about`, `/contact`) | `scan` |
| User wants whole-site audit / 標章 submission | `site --max-pages 30` (default; raise as needed) |
| Built `dist/` / `out/` ready, no server | `site ./dist --allow-file` |
| User unsure | Default `lint` first if source available, else `scan` |
| Regression check vs baseline | `site` with `--format json -o .a11y-moda/reports/current.json`, then diff against prior baseline (use `.a11y-moda/` to keep the user's repo root clean) |

### Workflow positioning

```
T0 about to write              ─→ a11y-moda rules search <element>   ← proactive
T1 write → T2 save → T3 commit ─→ a11y-moda lint
T4 build → T5 preview          ─→ a11y-moda site ./dist --allow-file
T6 dev server                  ─→ a11y-moda scan http://localhost:3000
T7 staging / prod              ─→ a11y-moda site https://...
```

All five stages share the **same `rule_id` namespace**. A `HM1110100C` answer from `rules show` is the same code as a `HM1110100C` failure from `lint` or `scan` — agents can pivot from "what should I do" (T0) to "did I do it right" (T1+) without re-mapping IDs.

---

### 3.5 `rules` subcommand (knowledge service, since 0.3.0)

```bash
# List
a11y-moda rules list                                  # all 129 rules (compact MD)
a11y-moda rules list --level AAA --format json
a11y-moda rules list --topic forms                    # by topic dir
a11y-moda rules list --source extension               # E rules only
a11y-moda rules list --scope lint                     # lint-implementable

# Show / explain (alias)
a11y-moda rules show HM1110100C --format json
a11y-moda explain HM1110100C --format json            # short alias

# Search (English aliases work; matches rule_id, desc, WCAG SC, topic)
a11y-moda rules search button --format json
a11y-moda rules search 1.1.1 --format json
a11y-moda rules search alt --format json
```

JSON shape per rule:

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

Field reference: see §5 Field reference table below; `rules` adds:
- `level_name` — `"A"` / `"AA"` / `"AAA"` string form
- `topic` — directory under `codes/` (e.g. `forms`, `aria`, `images`)
- `scope` — list of stages this rule_id is implemented in (`scan` and/or `lint`)
- `runtime_authoritative` — when `true`, lint downgrades `fail` → `caveat` (since 0.2.1) because AST cannot prove the violation; scan still emits `fail` authoritatively
- `wcag_url` — WAI Quickref anchor for the WCAG SC

**Search English aliases** (built-in mapping to zh-TW desc substrings):
`button`, `link`, `form`, `input`, `label`, `image`/`img`, `video`,
`audio`, `iframe`, `table`, `heading`, `lang`, `alt`, `aria`, `role`,
`focus`, `keyboard`, `color`/`contrast`, `modal`/`dialog`,
`navigation`/`landmark`, `skip`, `title`, `meta`. Unrecognised English
keywords fall through to literal substring search.

---

## 4. Pick flags (decision tree)

Apply rules in order. Stop at first matching rule.

### 4.0 Install variants (since 0.3.0 — lint is lightweight)

```bash
# Lightweight: lint + rules subcommand (default; ~30MB)
pip install a11y-moda

# Browser-based scan / site / --render
pip install 'a11y-moda[scan]'
playwright install chromium       # ~200MB Chromium binary
```

Since 0.3.0, Playwright is an **optional extra**. `lint` and `rules` need
none of it. `scan`, `site`, `--render`, `--render-crawl`, `--probe-modals`,
`tools/contrast.py`, `tools/tab_walk.py` all need `[scan]` extras.

**Behavior when `[scan]` not installed**:

```
$ a11y-moda scan https://example.com --render

ERROR: scan --render needs Playwright + Chromium (not installed).

Install (one-time, ~290MB):
    pip install 'a11y-moda[scan]'
    playwright install chromium

Or skip rendering:
    a11y-moda scan <URL>          (no --render)
    a11y-moda site <URL>          (no --render / --render-crawl)
    a11y-moda lint <PATH>         (source-level, no browser ever)
```

**Agents must NOT auto-install**. The user runs the printed command.

### 4.0.1 Lint flags (subset; lint is simpler than scan/site)

```
a11y-moda lint <paths...>
    [--level A|AA|AAA]       # default AA
    [--exclude PATTERN]       # repeatable; gitignore-style globs
    [--no-gitignore]          # ignore .gitignore
    [--fail-only]             # drop caveat + info
    [--strict]                # exit non-zero on any issue (CI gating)
    [--format json|md] [-o FILE]
```

`lint` does **not** have `--render`, `--allow-private-hosts`, `--probe-modals`, `--llm-*`, `--rps`, `--workers`, `--max-pages`, `--render-crawl`, `--freego-only`, `--strict-third-party` — none apply to source-level static analysis. If the user passes those, they meant `scan` or `site`.

Built-in excludes (always on): `node_modules`, `.next`, `.nuxt`, `.svelte-kit`, `.astro`, `dist`, `build`, `out`, `.vercel`, `.turbo`, `.git`, `.cache`, `__pycache__`, `.pytest_cache`, `.a11y-moda`. `.gitignore` patterns are honored by default.

Windows quirk: prefer `--exclude=docs/**` (equals form, no space) — the space-separated form may have `**` mangled by the C runtime before Click sees it. Both forms work after defensive normalisation, but the equals form is portable.

### 4.1 SPA / JS-rendered detection

```
IF target is SPA (React/Vue/Svelte/Next/Nuxt/Astro hydrated):
    add --render
    NOTE: --render forces serial scanning (Chromium is heavy)
ELSE (server-rendered or static HTML):
    skip --render (faster, parallel)
```

Detection heuristics: look for `next.config.*` / `vite.config.*` / `astro.config.*` / `nuxt.config.*` / `svelte.config.*` in the project root, or `<div id="root">`/`<div id="app">` in the served HTML with no rendered content inside.

For `site` mode, also add `--render-crawl` if the site has JS-injected navigation (otherwise crawler misses links).

### 4.2 Compliance level

```
IF user mentions "AAA" or "AAA 自評":
    --level AAA
ELIF user mentions "A only" or accessibility minimum:
    --level A
ELSE:
    --level AA   (default; matches MODA 標章 baseline)
```

### 4.3 Local development URL

```
IF URL is localhost / 127.0.0.1 / RFC1918 (10.x / 172.16-31.x / 192.168.x):
    add --allow-private-hosts
    OR set env A11Y_ALLOW_PRIVATE_HOSTS=1

IF URL is file:// OR target is a filesystem path (./out/, dist/, /var/www/site):
    add --allow-file
    OR set env A11Y_ALLOW_FILE=1
```

Both flags are opt-in to prevent SSRF / arbitrary-file-read via redirects from public sites.

`--allow-file` accepts:
- `file:///D:/dist/index.html` (Windows file URI)
- `file:///var/www/site/index.html` (POSIX file URI)
- `./dist/index.html` / `D:\dist\index.html` / `/var/www/site/` (auto-resolved to absolute file://)

For `site` mode with a `file://` target, sitemap and link-crawl don't apply — `a11y-moda` recursively walks the directory for `*.html` / `*.htm` files. This is the right behavior for build output (Astro / Next export / Hugo / Eleventy / SvelteKit-static) where there's no live server and following `<a href>` links from local files would mix routes that may not exist on disk.

### 4.4 Output format

```
IF AI parsing the result:
    --format json    (default; stable schema, see §5)
IF showing to human:
    --format md      (or omit -o, redirect to file with .md/.html ext)
IF generating shareable report:
    --format html -o report.html   (3-view: by rule, by WCAG, by URL)
```

### 4.5 Filtering

```
IF user wants only actionable items:
    --fail-only          (drops pass / caveat / info)
IF user wants Freego-only machine rules (skip E rules):
    --freego-only
IF cross-checking against official Freego tool's output:
    --freego-compat      (aligns reporting format for CS2140401C/CS3140801C/CS3140802C)
IF user explicitly wants third-party resources counted as fail:
    --strict-third-party
    (default behaviour: third-party violations become caveat with [third-party: <origin>] prefix)
```

### 4.6 Form / modal probing (production-safe defaults)

```
DO NOT add --probe-modals on production sites by default.
    Clicking modal triggers can trigger booking / billing / analytics events.
ONLY add --probe-modals if:
    - Target is dev/staging environment, OR
    - User explicitly asks ("scan modal forms too")
```

Destructive keywords (付款 / delete / unsubscribe / cancel) are always skipped even when `--probe-modals` is on.

### 4.7 LLM is invisible by default — agents ignore it

`a11y-moda` runs **without any LLM by default**. ~70% of AAA rules and 100% of A/AA DOM-checked rules need zero LLM calls.

**Default agent behavior**: pretend LLM does not exist.

- Do NOT add `--llm-*` flags to invocations.
- Do NOT check whether `A11Y_LLM_*` env vars are set.
- Do NOT ask the user about LLM before scanning.
- Do NOT block a scan because LLM is not configured.
- Do NOT volunteer LLM as a setup option in your initial output.
- If user has env vars set globally, the CLI will use them silently — you don't need to know.

The only time to mention LLM:
- User explicitly asks "why are there so many caveats" or "how do I get fewer caveats" → then explain LLM is an option (env vars below).
- Caveats with `message` containing `LLM unavailable` should be **filtered out of the surfaced caveat list** (collapse into a single line: "ℹ️ N additional rules require LLM judgement, not currently configured"). Don't enumerate them by `rule_id`.

```
env vars (lowest precedence) — user sets once globally:
    A11Y_LLM_BASE_URL    # e.g. https://api.openai.com/v1 or http://localhost:8000/v1
    A11Y_LLM_KEY         # API key (use "sk-noauth" for keyless local servers)
    A11Y_LLM_MODEL       # e.g. gpt-4o-mini, qwen3-vl-8b

per-call flags (highest precedence) — override for one run:
    --llm-base-url <URL>
    --llm-key <KEY>
    --llm-model <MODEL>
    --llm-concurrency <N>   # default 1; raise for batched-capable endpoints
```

When env vars (or per-call flags) ARE set, LLM rules run automatically; results cache at `~/.cache/a11y-moda/llm/` (delete to force re-judge).

---

## 5. Output schema (JSON, stable contract)

### `scan` (single page)

```json
{
  "url": "https://example.com/about",
  "status_code": 200,
  "fetch_error": "",
  "issues": [
    {
      "rule_id": "HM1110100C",
      "guideline": "1.1.1",
      "level": 2,
      "desc": "Non-text content has text alternative",
      "message": "圖片缺少 alt 屬性",
      "snippet": "<img src=\"hero.png\">",
      "status": "fail"
    }
  ],
  "summary": {
    "fail": 12,
    "info": 0,
    "caveat": 3
  }
}
```

### `lint` (source files)

```json
{
  "summary": {
    "files_scanned": 47,
    "fail": 12,
    "caveat": 8,
    "info": 3
  },
  "files": [
    {
      "path": "src/components/Hero.tsx",
      "language": "tsx",
      "fetch_error": "",
      "by_status": { "fail": 1, "caveat": 0, "info": 0 },
      "issues": [
        {
          "rule_id": "HM1110100C",
          "guideline": "1.1.1",
          "level": 2,
          "desc": "Non-text content has text alternative",
          "message": "<img> 缺少 alt 屬性",
          "snippet": "<img src=\"hero.png\" />",
          "status": "fail",
          "line": 12,
          "col": 5
        }
      ]
    }
  ]
}
```

Lint adds two fields not present in `scan` output: `line` and `col` (1-based). Ideal for editor "jump to issue" integrations.

### `site` (whole site)

```json
{
  "site_summary": {
    "pages_scanned": 30,
    "fail": 87,
    "info": 0,
    "caveat": 41
  },
  "by_rule": {
    "HM1110100C": {
      "rule_id": "HM1110100C",
      "guideline": "1.1.1",
      "level": 2,
      "desc": "Non-text content has text alternative",
      "pages_affected": ["https://example.com/", "https://example.com/about"],
      "status": "fail"
    }
  },
  "pages": [ /* array of per-page reports same shape as scan */ ]
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `rule_id` | string | MODA code (e.g. `HM1110100C`, `GN2240600E`). `C` suffix = machine check, `E` suffix = extension/human-judgement, no suffix = guideline-level |
| `guideline` | string | WCAG 2.1 SC number (e.g. `1.1.1`, `2.4.6`) |
| `level` | int | `1`=A, `2`=AA, `3`=AAA |
| `desc` | string | One-line rule description |
| `message` | string | Human-readable finding (zh-TW). For third-party violations, prefixed with `[third-party: <origin>] ` |
| `snippet` | string | HTML/CSS context (max 300 chars). For CSS-rule violations, format is `selector { property: value @ url }` |
| `status` | enum | See §5.1 |
| `fetch_error` | string | Non-empty when the URL itself failed to load (network error, 4xx/5xx) |

### 5.1 Status enum (CRITICAL — read before triaging)

| Status | Meaning | AI action |
|---|---|---|
| `fail` | Confirmed violation, user/code must fix | Surface to user, suggest fix |
| `caveat` | Tool can't conclude — needs human judgement, OR violation is in third-party resource | Show as informational; do NOT recommend code changes unless user explicitly asks |
| `needs_human` | Same intent as caveat (older alias) | Same handling |
| `info` | Informational signal | Mention only if relevant to user's question |
| `pass` | Rule applied and passed | Don't surface |
| `not_applicable` | Rule doesn't apply to this page | Don't surface |

**Anti-pattern**: treating `caveat` as `fail`. Caveat means "I detected a possible issue but cannot determine whether it's actually a violation, OR the violation is in code the user does not control." Don't generate aggressive fix suggestions for caveats.

### 5.2 Third-party caveat decoding

When `message` starts with `[third-party: <origin>] ...`:
- Origin = the eTLD+1 of the offending external resource (e.g. `googleapis.com`, `cloudflare.com`)
- The user's HTML loads a CSS/JS from that origin, and that external CSS/JS contains the violation
- **Correct AI advice**: "This violation is in code from `<origin>`, not your codebase. For MODA submission, declare in 備註欄 (WCAG 2.1 §5.4 Partial Conformance)."
- **Wrong AI advice**: "Edit `node_modules/<origin>/...`" — they didn't ship that code and can't.

### 5.3 Exit codes

```
0  — CLI ran without crashing (REGARDLESS of issue count)
≠0 — CLI crashed / bad arguments / SSRF guard tripped
```

**Do NOT** rely on exit code to detect violations. Parse JSON `summary.fail` instead.

For CI gating (e.g. fail build if AA violations present), parse `summary.fail` (single page) or `site_summary.fail` (whole site). Example using `jq` (or substitute Python / your language of choice):

```bash
fails=$(a11y-moda site "$URL" --level AA --format json | jq '.site_summary.fail')
test "$fails" -eq 0 || exit 1
```

Pure-Python alternative (no `jq` dependency):

```bash
a11y-moda site "$URL" --level AA --format json -o /tmp/scan.json
python -c "import json,sys; sys.exit(1 if json.load(open('/tmp/scan.json'))['site_summary']['fail'] else 0)"
```

---

## 6. Triage workflow

After receiving JSON:

1. **Filter to actionable**: `issues where status == "fail"` (and optionally `caveat` if user asks for "everything")
2. **Group by `rule_id`** to deduplicate same-issue across multiple selectors
3. **Sort by severity**:
   - Level A (`level: 1`) > Level AA (`level: 2`) > Level AAA (`level: 3`)
   - Within same level, frequency (more pages affected = higher priority for site reports)
4. **For each rule**, present:
   - `rule_id` + `guideline` + one-line `desc`
   - 1-3 representative `snippet`s (don't dump all)
   - Suggested fix (use rule_id to reference MODA docs: `https://accessibility.moda.gov.tw/`)
5. **Separate third-party caveats** into a "needs declaration" section, NOT mixed with code-fix items

---

## 7. Fix → re-verify loop

```
1. Run scan, capture baseline:
   a11y-moda scan "$URL" --level AA --format json -o .a11y-moda/reports/before.json

2. Apply fix (edit code, deploy / restart dev server)

3. Re-run:
   a11y-moda scan "$URL" --level AA --format json -o .a11y-moda/reports/after.json

4. Diff: load both JSONs, extract (rule_id, snippet, status) tuples from
   `.issues`, sort, compare. AI agents should do this in-process (Read both
   files into context, compute the diff yourself) — don't rely on shell
   tools like `jq` / `diff` / `comm` being installed.

5. Surface to user:
   - "Fixed N: <rule_id list>"
   - "Still failing M: <rule_id list>"
   - "New regressions K: <rule_id list>"   ← critical, flag prominently
```

LLM cache (`~/.cache/a11y-moda/llm/`) makes re-runs cheap — only changed rules re-judge.

---

## 8. Environment / cache / state

| Path | What |
|---|---|
| `~/.cache/a11y-moda/llm/` | LLM judgement cache (per-prompt hash). Delete to force re-judge |
| `./reports/` | Default output dir when `-o` is a bare filename (CLI behavior). Agents should override with `-o .a11y-moda/reports/<file>.json` to keep repo root clean and avoid accidental commits |
| `~/.config/a11y-moda/.env` | Global personal env defaults (lowest precedence) |
| `./.env` | Per-project env (mid precedence) |
| `--env-file <PATH>` | Explicit override (highest precedence) |

Process env vars (shell `export`, Docker `-e`, CI runner) always win over `.env` files.

---

## 9. Cost / performance hints

| Concern | Mitigation |
|---|---|
| LLM cost on repeated scans | Cache is automatic; same content → 0 API calls |
| Site scan time | Drop `--render` if target is server-rendered. Raise `--workers` (only effective when no `--render`) |
| Production politeness | Set `--rps 1` (1 request/sec global cap) and `--delay 0.5` |
| LLM endpoint OOM (local single-GPU model) | Keep `--llm-concurrency 1` (default). Only raise for batched-capable endpoints |
| Playwright RAM | `--render` forces serial; expect ~500MB resident per Chromium |
| Large site (>100 pages) | Use `--max-pages` and `--max-time`; consider `--exclude-folder /admin` |

---

## 10. Anti-patterns (DON'T)

| ❌ Don't | ✅ Do |
|---|---|
| Recommend `a11y-moda scan` for source feedback | Use `a11y-moda lint` for source / `scan` for rendered |
| Treat lint `caveat` as `fail` | Caveats from wrapper components (`<Button>`, `<Dialog>`) — accessibility may be in the underlying primitive; do NOT auto-fix |
| Treat `caveat` issues as `fail` | Surface caveats separately as "needs review" |
| Recommend editing third-party CDN code for `[third-party: ...]` issues | Tell user to declare in MODA submission notes |
| Skip `--allow-private-hosts` for `localhost` then debug "URL refused" errors | Add `--allow-private-hosts` when scanning local dev |
| Run with `--probe-modals` on production | Only on dev/staging unless user explicitly asks |
| Rely on exit code to detect issues | Parse `summary.fail` from JSON |
| Suggest `pip install -e .` to end users | Tell users `pip install a11y-moda` (PyPI) |
| Forget `playwright install chromium` after first install | Mention this once after `pip install a11y-moda` |
| Confuse `--render` (per-page) with `--render-crawl` (URL discovery) | SPA needs both; SSR site needs neither |

---

## 11. Platform quickstarts

Each example directory in `examples/` ships a ready-to-copy config that
matches that platform's auto-loaded location. All examples teach the
same proactive pattern: query `a11y-moda rules` BEFORE writing
a11y-sensitive elements; run `lint` / `scan` / `site` AFTER.

| Platform | Example | Path in your repo |
|---|---|---|
| Claude Code | [`examples/claude-code-skill/`](../examples/claude-code-skill/) | `~/.claude/skills/a11y-moda/` |
| Cursor | [`examples/cursor/`](../examples/cursor/) | `<repo-root>/.cursorrules` |
| GitHub Copilot Chat | [`examples/copilot/`](../examples/copilot/) | `<repo-root>/.github/copilot-instructions.md` |
| Aider | [`examples/aider/`](../examples/aider/) | `<repo-root>/.aider.conf.yml` |
| Generic LLM agent (Cline, Continue, RooCode, custom) | [`examples/generic-agent/`](../examples/generic-agent/) | Pin into agent system prompt |

### 11.1 Claude Code (Skill)

```bash
cp -r examples/claude-code-skill ~/.claude/skills/a11y-moda
```

Then in Claude Code, invoke with `/a11y-moda` or natural-language triggers ("check a11y", "MODA 標章驗", or about specific rule_id). The skill detects intent (knowledge query / lint / scan / site), picks flags per §4, runs, and applies §6 triage.

See [`examples/claude-code-skill/README.md`](../examples/claude-code-skill/README.md).

### 11.2 Cursor

**Recommended (since v0.3.0)**: copy [`examples/cursor/.cursorrules`](../examples/cursor/.cursorrules) to your repo root. Includes pre-write rule lookup + lint/scan invocation patterns + triage rules.

Inline minimal version (older / custom) below:

```
# a11y-moda integration

When the user asks for accessibility checks, WCAG audits, MODA 標章 verification,
or 無障礙檢查, use the `a11y-moda` CLI:

1. Detect environment:
   - If `next.config.*` / `vite.config.*` / `astro.config.*` exists → SPA, plan to use --render
   - If a dev server is running on localhost → use --allow-private-hosts
   - Default level: AA (use AAA only if user mentions "AAA" or "AAA 自評")

2. Invoke (single page):
   ```
   a11y-moda scan <URL> --level AA --format json [--render] [--allow-private-hosts]
   ```

3. Invoke (whole site):
   ```
   a11y-moda site <URL> --level AA --format json --max-pages 30 [--render --render-crawl]
   ```

4. Parse JSON per docs/AI_INTEGRATION.md §5. Triage by status:
   - `fail` → user must fix; suggest code change
   - `caveat` → informational; do NOT auto-fix unless asked
   - Third-party prefixed `[third-party: <origin>]` caveats → user declares in MODA submission notes, not code change

5. NEVER add --probe-modals on production URLs (triggers booking / billing / analytics).

6. Do NOT suggest editing JSX for issues. a11y-moda audits rendered DOM;
   for source-level lint use `eslint-plugin-jsx-a11y` (different tool).
```

### 11.3 Aider

**Recommended (since v0.3.0)**: copy [`examples/aider/.aider.conf.yml`](../examples/aider/.aider.conf.yml) to your repo root. Includes `lint-cmd:` hook so Aider auto-lints after each edit.

Inline minimal version (older / custom):

```yaml
read:
  - docs/AI_INTEGRATION.md
```

Then in Aider chat, reference flags from this doc. Aider will use the doc as ground truth.

For repeated audit workflows, add a custom command in `.aider/commands/`:

```bash
#!/bin/bash
# .aider/commands/a11y
url="${1:-http://localhost:3000}"
a11y-moda scan "$url" --level AA --render --allow-private-hosts --format json
```

### 11.4 GitHub Copilot

**Recommended (since v0.3.0)**: copy [`examples/copilot/.github/copilot-instructions.md`](../examples/copilot/.github/copilot-instructions.md) to your repo's matching path.

Inline minimal version (older / custom) — add to `.github/copilot-instructions.md` at your repo root. Copilot Chat auto-loads this file as context when you chat in this repo:

```markdown
# a11y-moda integration

When the user asks for accessibility checks, WCAG audits, MODA 標章 verification,
AAA 自評, or 無障礙檢查, use the `a11y-moda` Python CLI (https://pypi.org/project/a11y-moda/).

## Install check

If `a11y-moda` is not installed, tell the user:
    pip install a11y-moda
    playwright install chromium    # one-time, required for --render

## Detect environment

- SPA framework? Look for `next.config.*`, `vite.config.*`, `astro.config.*`,
  `nuxt.config.*`, `svelte.config.*` in the repo. If any → plan to add `--render`
  (and `--render-crawl` for site mode).
- Local dev URL (localhost / 127.0.0.1)? Add `--allow-private-hosts`.
- Compliance level: default `--level AA` (MODA 標章 baseline). Use `--level AAA`
  only if the user mentions "AAA" or "AAA 自評". `A` is rarely correct.

## Run

Single page:
    a11y-moda scan <URL> --level AA --format json [--render] [--allow-private-hosts]

Whole site:
    a11y-moda site <URL> --level AA --format json --max-pages 30 [--render --render-crawl]

Always use `--format json` and parse the output. Never rely on exit code to
detect violations (CLI exits 0 even when issues found); read `summary.fail`
from JSON.

## Triage

For each issue, the `status` field decides handling:

- `fail`: confirmed violation. Suggest a code fix.
- `caveat` / `needs_human`: tool can't conclude OR the violation is in
  third-party code the user does not control. Surface as "needs review".
  Do NOT auto-suggest code fixes.
- `info`, `pass`, `not_applicable`: don't surface.

If a `caveat` message starts with `[third-party: <origin>] ...`, the violation
is in code from `<origin>` (e.g. `googleapis.com`). Tell the user to declare
this in their MODA 申請備註欄 (WCAG 2.1 §5.4 Partial Conformance), NOT to edit
their codebase.

## Anti-patterns (do NOT)

- Do NOT add `--probe-modals` on production URLs (can trigger booking /
  billing / analytics events).
- Do NOT recommend editing JSX source for issues — `a11y-moda` audits rendered
  DOM. For source-level lint, recommend `eslint-plugin-jsx-a11y` instead.
- Do NOT prompt the user to set up an LLM endpoint before scanning. LLM is
  optional; ~70% of AAA rules + 100% of A/AA rules run without it.

For full reference: https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md
```

> **Note**: Copilot does not have a "skill" mechanism equivalent to Claude Code's `SKILL.md`. The `.github/copilot-instructions.md` file is the closest equivalent — it's auto-loaded as context for Copilot Chat sessions in that repo. For Copilot Workspace and Copilot Skillsets (REST-endpoint integrations), see the project roadmap; not currently shipped.

### 11.5 Generic LLM agent (Cline, Continue, RooCode, custom)

**Recommended (since v0.3.0)**: pin [`examples/generic-agent/AGENT.md`](../examples/generic-agent/AGENT.md) into the agent's system prompt / instructions. Covers pre-write rule lookup, lint/scan/site invocation, triage, and anti-patterns in one platform-agnostic doc.

### 11.6 Plain shell

Minimal pattern any agent can use:

```bash
# Static site, single page
a11y-moda scan https://example.com --level AA --format json

# SPA on dev server
a11y-moda scan http://localhost:3000/about \
  --level AA --render --allow-private-hosts --format json

# Whole site, with local LLM for E rules
A11Y_LLM_BASE_URL=http://localhost:8000/v1 \
A11Y_LLM_MODEL=qwen3-vl-8b \
  a11y-moda site https://example.com \
    --level AAA --max-pages 30 --render --render-crawl \
    --format json -o .a11y-moda/reports/audit.json

# Local build output (Astro / Next export / Hugo / Eleventy / SvelteKit-static)
a11y-moda scan ./dist/index.html --allow-file --render --format json
a11y-moda site ./dist --allow-file --render --level AA --format json
```

Parse JSON per §5, triage per §6.

---

## 12. Comparison with adjacent tools

| Tool | Scope | When to recommend |
|---|---|---|
| `a11y-moda lint` (since 0.2.0) | JSX/TSX/JS/HTML AST, MODA rule_id, deterministic, no LLM | Source-time MODA audit, CI gating, IDE save-hook, framework-agnostic |
| `a11y-moda scan` / `site` | Rendered DOM, MODA rule_id, AAA self-eval, site crawl, JSON for AI | Pre-MODA submission, AAA check, site-wide audit, CI gating, AI workflow |
| [`eslint-plugin-jsx-a11y`](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) | JSX/TSX source-time static lint, no MODA mapping | When user already has eslint configured; non-Taiwan a11y context |
| [`axe-core`](https://github.com/dequelabs/axe-core) | Generic WCAG runtime, browser-extension or CI | When MODA rule_id mapping is not needed; generic global a11y |
| [Pa11y](https://github.com/pa11y/pa11y) | Headless WCAG runtime, similar to axe-core | Alternative runtime auditor; no MODA mapping |
| [DopplerKuo a11y-tw-audit-skill](https://github.com/DopplerKuo/a11y-tw-audit-skill) | Claude Code skill, LLM judges JSX source | When user wants LLM-based subjective review; complements `lint` for hard-to-codify rules |

These are **complementary**, not competing. A complete workflow:

```
Editor (writing JSX)         → a11y-moda lint <file>     (deterministic, fast)
       ↓                       + DopplerKuo skill         (LLM, subjective)
       ↓                       + eslint-plugin-jsx-a11y   (if already configured)
Build output (dist/)         → a11y-moda site ./dist --allow-file --render
       ↓
Dev server (testing page)    → a11y-moda scan http://localhost:3000
       ↓
Production (post-deploy)     → a11y-moda site https://...  (CI cron)
       ↓
MODA submission              → a11y-moda site https://... --level AAA --format html
```

---

## 13. Versioning + stability promise

| Surface | Stability |
|---|---|
| CLI subcommands (`lint`, `scan`, `site`) | Stable across 0.x |
| Documented flag names | Stable across 0.x; new flags additive |
| JSON schema (§5) | Stable across 0.x; new fields additive (consumers must tolerate unknown fields) |
| Status enum values (§5.1) | New values may be added in 0.x; AI agents must default to "treat unknown as caveat" |
| Rule IDs (`rule_id` values) | Driven by MODA's published codes; will not be renamed within a major version |
| Internal Python API (`a11y_moda.*` modules) | NOT stable; do not import from the CLI |

For production AI integrations, pin version: `pip install 'a11y-moda==0.1.*'`.

---

## 14. Reporting AI integration issues

If you (the AI agent) encounter ambiguous behavior, please file an issue tagged `ai-integration` at:
https://github.com/light-design-tw/a11y-moda/issues

Include: the prompt that produced the wrong invocation, the JSON output if any, and the expected behavior.
