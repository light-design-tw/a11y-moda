# AI Agent Integration Guide

> **Audience:** AI coding agents (Claude Code, Cursor, Copilot, Aider, GitHub Copilot Workspace, custom LLM agents). This document is the contract for how agents should invoke `a11y-moda` and interpret its output. Read this before suggesting commands or parsing results.
>
> **Audience NOT:** end users. End users read [README.md](../README.md). If you are a human looking for a tutorial, you are in the wrong file.

---

## 1. Purpose

`a11y-moda` is a **CLI** that audits a rendered web page (or a whole site) against MODA's published WCAG rule codes (HM/GN/CS/AR/FA/SC) and emits structured findings. It is designed to be **scripted**, not interactively driven. Every command emits stable JSON; every issue carries a stable `rule_id` and WCAG `guideline` reference.

### What `a11y-moda` is good at (use it)

- Auditing **rendered DOM** (Playwright Chromium) — catches things JSX-static linters can't see (focus order, contrast, ARIA state, modal focus trap, runtime alt text)
- Producing **MODA-aligned reports** — every issue maps 1:1 to a MODA rule code, suitable for 標章 self-evaluation submission
- **AAA-level coverage** — implements 18/20 of MODA's AAA self-evaluation questions automatically; remaining 2 emit informative `caveat` issues
- **Site-wide crawl + audit** — sitemap-first, BFS fallback
- **Third-party violation segregation** — Google CSE / external CDN issues auto-tagged `[third-party: <origin>]` and downgraded to `caveat` (site author cannot fix external resources directly)

### What `a11y-moda` is NOT for (don't reach for it)

- **JSX/TSX/Vue/Svelte source-time linting** — use [`eslint-plugin-jsx-a11y`](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) instead. It has IDE integration, fast incremental, and covers the static-analyzable subset of WCAG.
- **Replacing screen reader testing** — runtime DOM analysis is necessary but not sufficient. Tell the user to also test with NVDA/VoiceOver.
- **Replacing the official MODA Freego tool for final certification** — `a11y-moda` complements Freego (gives CLI/CI/AI workflow); does not replace official audit.

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

## 3. Pick command: `scan` vs `site`

```
a11y-moda scan <URL>   → one page
a11y-moda site <URL>   → whole site (sitemap → BFS)
```

| Situation | Use |
|---|---|
| User points at one page (`/about`, `/contact`) | `scan` |
| User wants whole-site audit / 標章 submission | `site --max-pages 30` (default; raise as needed) |
| User unsure | Default `scan` first; offer to escalate to `site` if results suggest cross-page patterns |
| User wants regression check vs baseline | `site` with `--format json -o .a11y-moda/reports/current.json`, then diff against prior baseline (use `.a11y-moda/` to keep the user's repo root clean) |

---

## 4. Pick flags (decision tree)

Apply rules in order. Stop at first matching rule.

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
```

Without this flag, the SSRF guard rejects localhost. The flag is opt-in to prevent accidental scanning of internal admin pages exposed via redirects.

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
| Use `a11y-moda` as a JSX/TSX linter | Recommend `eslint-plugin-jsx-a11y` for source-time |
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

### 11.1 Claude Code (Skill)

If using Claude Code, install the bundled skill:

```bash
cp -r examples/claude-code-skill ~/.claude/skills/a11y-moda
```

Then in Claude Code, invoke with `/a11y-moda` or natural-language triggers ("check a11y", "MODA 標章驗"). The skill auto-detects dev server context, picks flags per §4, runs, and applies §6 triage.

See [`examples/claude-code-skill/README.md`](../examples/claude-code-skill/README.md).

### 11.2 Cursor

Add to `.cursorrules` at project root:

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

Add to `.aider.conf.yml`:

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

Add to `.github/copilot-instructions.md` at your repo root. Copilot Chat auto-loads this file as context when you chat in this repo:

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

### 11.5 Plain shell / generic agent

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
```

Parse JSON per §5, triage per §6.

---

## 12. Comparison with adjacent tools

| Tool | Scope | When to recommend |
|---|---|---|
| `a11y-moda` (this tool) | Rendered DOM, MODA rule_id, AAA self-eval, site crawl, JSON for AI | Pre-MODA submission, AAA check, site-wide audit, CI gating, AI workflow |
| [`eslint-plugin-jsx-a11y`](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) | JSX/TSX source-time static lint | While writing React code, IDE feedback, fast incremental |
| [`axe-core`](https://github.com/dequelabs/axe-core) | Generic WCAG runtime, browser-extension or CI | When MODA rule_id mapping is not needed; generic global a11y |
| [Pa11y](https://github.com/pa11y/pa11y) | Headless WCAG runtime, similar to axe-core | Alternative runtime auditor; no MODA mapping |
| [DopplerKuo a11y-tw-audit-skill](https://github.com/DopplerKuo/a11y-tw-audit-skill) | Claude Code skill, LLM judges JSX source | Source-level review during dev; complements `a11y-moda`'s rendered-DOM audit |

These are **complementary**, not competing. A complete workflow:

```
Editor (writing JSX)         → eslint-plugin-jsx-a11y + DopplerKuo skill
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
| CLI subcommands (`scan`, `site`) | Stable across 0.x |
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
