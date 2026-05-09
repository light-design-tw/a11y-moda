# a11y-moda

[![PyPI](https://img.shields.io/pypi/v/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![Python](https://img.shields.io/pypi/pyversions/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/light-design-tw/a11y-moda/blob/main/LICENSE)

> Python CLI for Taiwan MODA accessibility certification (無障礙標章) — lint + scan + rule lookup · WCAG A / AA / AAA · zh-TW reports · CI / AI friendly

[繁體中文](./README.md) · **English**

> ⚠️ **Unofficial / community tool.** Not affiliated with, endorsed by, or sponsored by Taiwan's Ministry of Digital Affairs (MODA / 數位發展部). Results are for developer convenience and do not replace official MODA review. The official tool is **[Freego](https://accessibility.moda.gov.tw/)**.

## Contents

- [Why](#why)
- [Install](#install)
- [30-second tour](#30-second-tour)
- [`lint` — source-level static analysis](#lint--source-level-static-analysis-tree-sitter-ast-no-playwright)
- [`rules` / `explain` — query MODA rule knowledge](#rules--explain--query-moda-rule-knowledge)
- [`scan` / `site` — pre-deploy / production scan](#scan--site--pre-deploy--production-scan-rendered-dom)
- [lint vs scan — which one?](#lint-vs-scan--which-one)
- [AI agent integration](#ai-agent-integration)
- [Coverage highlights](#coverage-highlights)
- [License](#license)

## Why

The official tool — [Freego](https://accessibility.moda.gov.tw/) — is a Java GUI without CLI, Docker, or API support. `a11y-moda` is a CLI complement designed for **CI/CD pipelines** and **AI-assisted development**. It implements MODA's published accessibility rule codes (HM / GN / CS / AR / FA / SC) and maps each finding to the corresponding MODA rule ID and WCAG 2.1 success criterion.

Three layers, mapped to development workflow stages:

| Command | Stage | Mechanism | Footprint |
|---|---|---|---|
| **`lint`** | Write / CI | Source tree-sitter AST | Pure Python, ~30MB |
| **`rules` / `explain`** | Pre-write / agent lookup | Rule metadata query | Pure Python, ~30MB |
| **`scan` / `site`** | Pre-deploy / production | Rendered DOM + contrast + focus probe | + Playwright, ~290MB |

Human-judgement rules (E codes) call an OpenAI-compatible endpoint. Works with OpenAI, Anthropic, OpenRouter, Ollama, vLLM, LM Studio, llama.cpp server — anything exposing `/v1/chat/completions`. The endpoint can point to a local model, so request data stays on your network.

> Reports are **Traditional Chinese (zh-TW)** by default — built for a Taiwanese audience submitting to MODA. The CLI itself is English; only rule output is zh-TW.

## Install

```bash
# Standard install — lint + rules + explain + init (~30MB)
pip install a11y-moda

# Add scan / site / --render — includes Playwright (~290MB)
pip install 'a11y-moda[scan]'
playwright install chromium
```

Python ≥ 3.10.

> ⚠️ **BREAKING since v0.3.0** — Playwright is no longer installed by default. The standard install covers most CI use cases (`lint` / `rules`). The `[scan]` extra is required for `scan` / `site` / `--render` / `--render-crawl` / `--probe-modals`.

> ⚠️ `pip install 'a11y-moda[scan]'` does **not** download Chromium. Run `playwright install chromium` before `--render`, otherwise you'll hit `Executable doesn't exist`.

From source for development:

```bash
git clone https://github.com/light-design-tw/a11y-moda
cd a11y-moda
pip install -e '.[scan,dev]'
playwright install chromium
```

## 30-second tour

```bash
# Write-time — lint React / Vue / HTML source
a11y-moda lint src/

# Lookup — agent queries MODA rules before writing code
a11y-moda rules search button
a11y-moda explain HM1110100C

# Pre-deploy — scan build output
a11y-moda scan ./dist/index.html --allow-file --render

# Production — full-site scan
a11y-moda site https://example.com --level AA --max-pages 30
```

---

## `lint` — source-level static analysis (tree-sitter AST, no Playwright)

Pure tree-sitter AST. **No LLM, no browser, no network.** Fast, repeatable, CI-friendly. 50 rules ported from the `scan` rule set, covering JSX / TSX / TS / JS / HTML.

```bash
a11y-moda lint src/                          # scan a directory
a11y-moda lint src/ --strict                 # any issue exits non-zero (CI gate)
a11y-moda lint src/ --fail-only              # ignore caveat / info
a11y-moda lint src/ --exclude '**/*.test.*'  # extra excludes (gitignore-style glob)
a11y-moda lint src/ --format json -o lint.json
```

Respects `.gitignore` by default; built-in excludes for `node_modules` / `.next` / `dist` / `build` / `.git` / `.cache`. Opt out with `--no-gitignore`.

**Three-tier status**:
- `fail` — AST-confirmed violation (e.g. `<img>` without `alt`)
- `caveat` — likely violation, needs human / runtime check (e.g. `<div onClick>` may be a modal backdrop)
- `info` — style / preference

**Wrapper-component heuristic**: capital-first JSX tags (`<Button>` / `<Dialog>`) downgrade keyboard / structure violations to `caveat`, since shadcn / Radix / HeadlessUI commonly delegate accessibility to the underlying primitive.

**`runtime_authoritative` downgrade (since v0.2.1)**: rules requiring cross-file or runtime evidence (e.g. `useHotkeys` in a parent, `outline:none` in external CSS) emit `caveat` from `lint` with a human-review note. `scan` still emits `fail` for the same rules — it has Playwright + computed style as evidence.

CI integration:

```yaml
# GitHub Actions
- run: pip install a11y-moda
- run: a11y-moda lint src/ --fail-only --strict
```

## `rules` / `explain` — query MODA rule knowledge

Knowledge service — exposes the rule registry as a CLI API for AI agents to **look up MODA rules before writing code**. All 129 rules are queryable.

```bash
a11y-moda rules list                         # list all 129
a11y-moda rules list --level AA              # filter by level
a11y-moda rules list --topic forms           # filter by topic
a11y-moda rules list --source extension      # freego (machine) / extension (E rules)
a11y-moda rules list --scope lint            # scan / lint applicability

a11y-moda rules search button                # English keyword (built-in alias map)
a11y-moda rules search dialog modal

a11y-moda rules show HM1110100C              # full metadata (JSON)
a11y-moda explain HM1110100C                 # short alias for rules show
```

Each rule returns 9 fields: `rule_id`, `guideline`, `level`, `level_name`, `desc`, `source`, `runtime_authoritative`, `wcag_url` (W3C WAI Quickref anchor), `topic`, `scope`.

**Design intent**: agents query relevant rules before writing `<button>` / `<dialog>` / `<form>` so they **write compliant code from the start** rather than fix it after lint complains. Reactive lookup (`explain` after seeing a `fail`) also works, but proactive query is the bigger UX win.

## `scan` / `site` — pre-deploy / production scan (rendered DOM)

Requires `pip install 'a11y-moda[scan]'`. Actually renders DOM, measures contrast, walks Tab focus, simulates form submission.

```bash
# Single page
a11y-moda scan https://example.com --level AA

# Full site, JS-rendered, local VLM, HTML report
a11y-moda site https://example.com \
  --level AAA --max-pages 30 --render \
  --llm-base-url http://localhost:8000/v1 --llm-model qwen3-vl-8b \
  --format html -o report.html

# Local build output (Astro / Next export / Hugo / Eleventy / SvelteKit-static)
a11y-moda scan ./dist/index.html --allow-file --render
a11y-moda site ./dist --allow-file --render --level AA --format html -o dist-audit.html
```

`--allow-file` is opt-in. Off by default so a redirect from a public site can't trick the scanner into reading local files. Accepts both POSIX (`/var/www/site/`) and Windows (`D:\dist\index.html`) paths.

LLM endpoint via env (used when `--llm-*` flags omitted):

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

LLM results are cached locally (`~/.cache/a11y-moda/llm/`) — re-runs only re-hit the model for changed rules.

## lint vs scan — which one?

| You want to… | Use | Why |
|---|---|---|
| Check while editing | `lint` | Pure AST, millisecond, IDE-friendly |
| CI gate (PR check) | `lint --strict` | No Chromium, fast install |
| Agent looks up rule before coding | `rules search` / `explain` | Knowledge service, proactive |
| Audit build output (Astro / Next export) | `scan --allow-file` | Known HTML, needs Playwright for contrast |
| Crawl + render full site | `site --render` | SPA / dynamic JS / contrast all need DOM |
| Strict contrast check (4.5:1 / 7:1) | `scan --render` | AST cannot see computed CSS |
| Tab order / focus traversal | `scan --render` | Needs real DOM + tab walk probe |

Rule of thumb: **`lint` while writing, `scan` while shipping.** Same rule_id namespace — issues cross-reference cleanly.

## AI agent integration

Stable JSON schema, three-tier `status` enum (`fail` / `caveat` / `pass`), `[third-party: <origin>]` prefix on caveats from external resources — all designed for AI workflows (write → scan → fix → re-verify), and now (since v0.3.0) for **lookup before write** via `rules` / `explain`.

**One-line install** (since v0.3.1):

```bash
a11y-moda init claude-code        # → ~/.claude/skills/a11y-moda/
a11y-moda init cursor             # → ./.cursorrules
a11y-moda init copilot            # → ./.github/copilot-instructions.md
a11y-moda init aider              # → ./.aider.conf.yml
a11y-moda init agent              # → stdout (paste into your agent system prompt)
a11y-moda init --list             # list all available IDE / agent integrations
a11y-moda init <ide> --print      # preview without writing
a11y-moda init <ide> --force      # overwrite existing file
```

- [`docs/AI_INTEGRATION.md`](./docs/AI_INTEGRATION.md) — platform-agnostic guide (any CLI-capable LLM agent). Includes JSON schema, flag decision tree, per-IDE templates.
- [`src/a11y_moda/_examples/`](./src/a11y_moda/_examples/) — 5 bundled integration templates (claude-code-skill / cursor / copilot / aider / generic-agent). Auto-distributed by `a11y-moda init`.

> The Claude Code skill `description` was rewritten in v0.3.2 — trigger accuracy measured 90% in a 90-prompt cold-start benchmark (vs 53% in v0.3.1). Existing installs upgrade with `a11y-moda init claude-code --force`.

## Coverage highlights

- **129** registered rules covering Freego's machine-checked C rules + extension E rules
- **20 / 20** of MODA's AAA self-evaluation questions implemented (official tool: 0)
- **70 %** of AAA self-eval rules run without any LLM/VLM call
- **50** `lint`-eligible source-checkable rules (subset of 129)
- LLM endpoint can point to local models — request data stays on your network

See the [中文 README](./README.md) for the full rule mechanism breakdown, command reference, and rule-authoring guide.

## License

[MIT](LICENSE)
