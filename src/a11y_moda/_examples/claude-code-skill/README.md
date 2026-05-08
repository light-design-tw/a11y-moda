# a11y-moda Claude Code Skill

Claude Code skill that wraps the [`a11y-moda`](https://github.com/light-design-tw/a11y-moda) CLI for accessibility audits triggered from natural-language prompts.

When you say "check a11y", "audit accessibility", "WCAG 檢查", "MODA 標章驗證", or similar, Claude will:

1. Detect your dev environment (SPA framework, dev server port, public vs local URL)
2. Pick the right `a11y-moda` flags automatically
3. Run the CLI and parse the JSON output
4. Present results in zh-TW Markdown, triaged by severity
5. Separate third-party CDN violations (which need MODA submission notes, not code fixes) from fixable failures
6. Offer a fix → re-verify loop with diff

---

## Install

### 1. Install the CLI

```bash
pip install a11y-moda
playwright install chromium    # one-time, required for --render
```

### 2. Install this skill

#### Recommended (since v0.3.1): one-line install

The skill files are bundled in the `a11y-moda` PyPI package. Use the
built-in `init` subcommand:

```bash
a11y-moda init claude-code
```

This copies `SKILL.md` + `REFERENCE.md` into `~/.claude/skills/a11y-moda/`.

Override destination if needed:

```bash
a11y-moda init claude-code --dest /custom/path
a11y-moda init claude-code --force      # overwrite existing
a11y-moda init claude-code --print      # preview content (don't write)
```

#### Manual install (if you can't use the CLI)

Browse the bundled skill source on GitHub at
[`src/a11y_moda/_examples/claude-code-skill/`](https://github.com/light-design-tw/a11y-moda/tree/main/src/a11y_moda/_examples/claude-code-skill)
and copy `SKILL.md` + `REFERENCE.md` into `~/.claude/skills/a11y-moda/`
yourself.

`README.md` (this file) is optional — it's for human reference only and the skill works without it.

After install, restart Claude Code or reload the skills list (`/skills` should show `a11y-moda`).

### 3. (Optional) Configure LLM endpoint

For E rules requiring human-judgement (form labels, heading semantics, alt text quality), set:

```bash
# In ~/.config/a11y-moda/.env or your shell rc
export A11Y_LLM_BASE_URL=http://localhost:8000/v1   # or https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...                           # or "sk-noauth" for keyless local servers
export A11Y_LLM_MODEL=qwen3-vl-8b                    # or gpt-4o-mini
```

Without an LLM endpoint, ~70% of AAA rules still run (DOM-only checks).

---

## Use

### Single page (dev server)

```
> /a11y-moda check http://localhost:3000/about
```

Or natural language:

```
> 幫我檢查 localhost:3000/about 的無障礙
```

### Whole site

```
> 對 https://example.com 跑 MODA 標章 AAA 自評
```

Claude will pick `site --level AAA --render --render-crawl --max-pages 30` and present results when done (~5-10 min for SPA).

### Fix → re-verify

After Claude reports issues and you fix them:

```
> 我修了 alt 缺失，重新掃一次
```

Claude re-runs the same command and diffs against the previous JSON, surfacing fixed / still-failing / new-regression items.

---

## What this skill does NOT do

| Task | Use instead |
|---|---|
| Source-time JSX/TSX a11y lint | [`eslint-plugin-jsx-a11y`](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) |
| AI-judged source code review | [DopplerKuo/a11y-tw-audit-skill](https://github.com/DopplerKuo/a11y-tw-audit-skill) |
| Generic axe-core scan (no MODA mapping) | [`@axe-core/cli`](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/cli) |
| Screen reader testing | Manual NVDA / VoiceOver / TalkBack |
| Official MODA certification submission | The [official MODA Freego tool](https://accessibility.moda.gov.tw/) |

These tools are **complementary**:

```
Editor (writing JSX)         → eslint-plugin-jsx-a11y + DopplerKuo skill
Dev server (testing page)    → a11y-moda scan ... (this skill)
Production (post-deploy)     → a11y-moda site https://...
MODA submission              → a11y-moda site ... --level AAA --format html
```

---

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Core skill prompt — Claude reads this when invoked. Kept lean for low context cost |
| `REFERENCE.md` | Companion — Claude Reads on-demand for edge cases (error mappings, LLM details, fix-loop full steps, MODA rule lookup, tool comparison) |
| `README.md` | This file (install + usage docs for humans) |

---

## Updating

When `a11y-moda` ships a new version:

```bash
pip install --upgrade a11y-moda
```

The skill itself rarely needs updating — it relies on the CLI's stable JSON contract documented in [`docs/AI_INTEGRATION.md`](../../docs/AI_INTEGRATION.md). New CLI flags are additive; the skill will simply not use them until updated.

If a new `a11y-moda` version changes the JSON schema (signaled by a major version bump), pull the latest skill from the upstream repo and re-copy.

---

## Trust model

The skill executes the `a11y-moda` CLI with arguments derived from your prompt and from project config files (`package.json`, framework configs). It runs with `Bash`, `Read`, `Glob`, and `Edit` tools pre-approved (no per-call permission prompt).

Practical implications:

- **Only scan URLs you trust.** Don't paste URLs from untrusted sources (e-mail, suspicious chat messages, unknown clipboard) — even though `SKILL.md` validates URL shape and the CLI itself blocks `file://` and private hosts by default, treating arbitrary URLs as code is bad hygiene.
- **The skill never `eval`s its commands.** All Bash invocations use direct argument arrays with quoted variables. Re-verify reads its previous run from `.a11y-moda/last-run.txt` as plain-text parameters (not as a shell command), then validates each value against an allow-list before re-invoking.
- **Output stays local.** Reports go to `.a11y-moda/reports/`; LLM cache (if you opt in) goes to `~/.cache/a11y-moda/llm/`. No telemetry, no remote upload.
- **The CLI's own SSRF guard** rejects loopback / RFC1918 / `file://` URLs unless you pass `--allow-private-hosts`. The skill adds that flag automatically for `localhost` scans, so be deliberate when telling it to scan internal addresses.

If you find a security issue (e.g. a way to bypass the validations in `SKILL.md` §5), please report privately to the maintainer rather than opening a public issue.

---

## Reporting issues

Issues with the skill (wrong invocation, missed environment detection, bad triage) → file at https://github.com/light-design-tw/a11y-moda/issues with the tag `ai-integration` and include the prompt that triggered the wrong behavior.

---

## License

MIT — same as `a11y-moda`. See [LICENSE](../../LICENSE).
