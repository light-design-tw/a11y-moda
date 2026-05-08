# a11y-moda

[![PyPI](https://img.shields.io/pypi/v/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![Python](https://img.shields.io/pypi/pyversions/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/light-design-tw/a11y-moda/blob/main/LICENSE)

> Python CLI for Taiwan MODA accessibility certification (無障礙標章) · WCAG A / AA / AAA · zh-TW reports

[繁體中文](./README.md) · **English**

> ⚠️ **Unofficial / community tool.** Not affiliated with, endorsed by, or sponsored by Taiwan's Ministry of Digital Affairs (MODA / 數位發展部). Results are for developer convenience and do not replace official MODA review. The official tool is **[Freego](https://accessibility.moda.gov.tw/)**.

## Why

The official tool — [Freego](https://accessibility.moda.gov.tw/) — is a Java GUI without CLI, Docker, or API support. `a11y-moda` is a CLI complement designed for **CI/CD pipelines** and **AI-assisted scanning workflows**. It implements MODA's published accessibility rule codes (HM / GN / CS / AR / FA / SC) and maps each finding to the corresponding MODA rule ID and WCAG 2.1 success criterion.

LLM-assisted (OpenAI-compatible endpoint) for human-judgement rules (E codes). Works with OpenAI, Anthropic, OpenRouter, Ollama, vLLM, LM Studio, llama.cpp server — anything exposing `/v1/chat/completions`.

> Reports are **Traditional Chinese (zh-TW)** by default — built for a Taiwanese audience submitting to MODA. The CLI itself is English; only rule output is zh-TW.

## Install

```bash
pip install a11y-moda           # PyPI
playwright install chromium     # required for --render
```

Python ≥ 3.10.

> ⚠️ `pip install` does **not** download Chromium. Run `playwright install chromium` before `--render`, otherwise you'll hit `Executable doesn't exist`.

## Quick start

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

`--allow-file` is opt-in. Off by default so a redirect from a public site
can't trick the scanner into reading local files. Accepts both POSIX
(`/var/www/site/`) and Windows (`D:\dist\index.html`) paths.

LLM endpoint via env (used when `--llm-*` flags omitted):

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

## AI agent integration

Stable JSON schema, three-tier `status` enum (`fail` / `caveat` / `pass`), `[third-party: <origin>]` prefix on caveats from external resources — all designed for AI workflows (write → scan → fix → re-verify).

**One-line install** (since v0.3.1):

```bash
a11y-moda init claude-code        # → ~/.claude/skills/a11y-moda/
a11y-moda init cursor             # → ./.cursorrules
a11y-moda init copilot            # → ./.github/copilot-instructions.md
a11y-moda init aider              # → ./.aider.conf.yml
a11y-moda init agent              # → stdout (paste into your agent system prompt)
a11y-moda init --list             # list all available IDE / agent integrations
```

- [`docs/AI_INTEGRATION.md`](./docs/AI_INTEGRATION.md) — platform-agnostic guide.
- [`src/a11y_moda/_examples/`](./src/a11y_moda/_examples/) — 5 bundled integration templates (claude-code-skill / cursor / copilot / aider / generic-agent). Auto-distributed by `a11y-moda init`.

## Coverage highlights

- **129** registered rules covering Freego's machine-checked C rules + extension E rules
- **20 / 20** of MODA's AAA self-evaluation questions implemented (official tool: 0)
- **70 %** of AAA self-eval rules run without any LLM/VLM call
- LLM endpoint can point to local models — request data stays on your network

See the [中文 README](./README.md) for the full rule mechanism breakdown, command reference, and rule-authoring guide.

## License

[MIT](LICENSE)
