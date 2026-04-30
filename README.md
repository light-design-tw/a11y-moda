# a11y-moda

Python CLI for **Taiwan MODA accessibility certification** (無障礙標章 A / AA / AAA).

The official tool — [Freego](https://accessibility.moda.gov.tw/) — is a Java GUI without CLI, Docker, or API support. `a11y-moda` is a CLI complement designed for **CI/CD pipelines** and **AI-assisted scanning workflows**. It implements MODA's published accessibility rule codes (HM / GN / CS / AR / FA / SC) and maps each finding to the corresponding MODA rule ID and WCAG 2.1 success criterion.

LLM-assisted (OpenAI-compatible endpoint) for human-judgement rules (E codes). Works with OpenAI, Anthropic, OpenRouter, Ollama, vLLM, LM Studio, llama.cpp server — anything exposing `/v1/chat/completions`.

## Features

- Static scan (httpx + BeautifulSoup) or rendered scan (Playwright / headless Chromium) for SPAs.
- A / AA / AAA level filtering.
- Site crawl: sitemap.xml first, BFS fallback.
- Output: JSON / Markdown / HTML (HTML always renders by-rule, by-WCAG, by-URL views).
- LLM judge cache on disk — safe to re-run, only changed rules re-call the model.
- Vision-capable models can verify image / layout rules from screenshots.
- Optional `--freego-compat` mode aligns reporting with the official MODA tool for cross-checking.

## Install

```bash
pip install -e .
playwright install chromium    # required for --render and Playwright-based probes
```

Python ≥ 3.10.

## Quick start

Scan one URL:

```bash
a11y-moda scan https://example.com --level AA
```

Crawl + scan a whole site, render JS, use a local VLM, write HTML report:

```bash
a11y-moda site https://example.com \
  --level AAA --max-pages 30 --render \
  --llm-base-url http://localhost:8000/v1 --llm-model qwen3-vl-8b \
  --format html -o report.html
```

LLM endpoint via env (used when `--llm-*` flags omitted):

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

## Command reference

```
a11y-moda scan <URL>     scan a single page
a11y-moda site <URL>     discover and scan a whole site
```

Common options:

| Flag | Default | Note |
|---|---|---|
| `--level A\|AA\|AAA` | `AA` | scan level |
| `--render` | off | use headless Chromium for JS-rendered pages |
| `--max-pages N` | 30 | upper bound for `site` |
| `--source sitemap\|crawl\|auto` | `auto` | URL discovery strategy |
| `--workers N` | 4 | parallel workers (static scans only; render is serial) |
| `--rps N` | 0 | global rate cap (req/s); 0 = unlimited |
| `--ignore RULE_ID` | — | repeatable; skip specific rule IDs |
| `--freego-only` | off | only rules covered by the official tool's machine checks |
| `--freego-compat` | off | match the official tool's reporting for CS2140401C / CS3140801C / CS3140802C |
| `--format json\|md\|html` | `json` | output format (also auto-detected from `-o` extension) |
| `-o FILE` | stdout | bare filename → `./reports/FILE` |

## How rules work

Each MODA rule_id is one Python file under `src/a11y_moda/rules/codes/<theme>/<RULE_ID>.py`. The package auto-discovers every rule via `pkgutil.iter_modules` — registration is automatic via the `@register` decorator.

Skeleton:

```python
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

@register
class MyRule(Rule):
    meta = RuleMeta(rule_id="XX1234567E", guideline="1.1.1", level=Level.A,
                    desc="...", source="extension")
    def _check(self, soup, report, *, html, url, ctx) -> None:
        ...
        report.add(self._issue(message="...", snippet="...", status="fail"))
```

`source = "freego"` → rule covered by the official MODA tool's machine checks.
`source = "extension"` → an E (人工 / manual) rule we automated programmatically.

## Project status

Pre-1.0. Rule coverage tracked against MODA's published rule set; LLM-assisted rules require external LLM access. Output schema may change before 1.0.

## License

[MIT](LICENSE)
