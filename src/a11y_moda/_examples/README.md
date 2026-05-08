# Examples

Bundled integration templates for `a11y-moda`. Auto-distributed via the
`a11y-moda init <ide>` subcommand (since v0.3.1).

```bash
a11y-moda init --list             # list all integrations
a11y-moda init claude-code        # → ~/.claude/skills/a11y-moda/
a11y-moda init cursor             # → ./.cursorrules
a11y-moda init copilot            # → ./.github/copilot-instructions.md
a11y-moda init aider              # → ./.aider.conf.yml
a11y-moda init agent              # → stdout (paste into agent system prompt)
```

Manual browse / copy if needed:

| Directory | For | Default install path |
|---|---|---|
| [`claude-code-skill/`](./claude-code-skill/) | [Claude Code](https://claude.com/claude-code) | `~/.claude/skills/a11y-moda/` |
| [`cursor/`](./cursor/) | [Cursor](https://cursor.sh/) | `<repo-root>/.cursorrules` |
| [`copilot/`](./copilot/) | [GitHub Copilot Chat](https://github.com/features/copilot) | `<repo-root>/.github/copilot-instructions.md` |
| [`aider/`](./aider/) | [Aider](https://aider.chat/) | `<repo-root>/.aider.conf.yml` |
| [`generic-agent/`](./generic-agent/) | Any LLM-based coding agent (Cline, Continue, RooCode, custom) | stdout (paste into agent system prompt) |

All examples share one architectural pattern (since v0.3.0):

> **Knowledge service mode** — when about to write a11y-sensitive
> JSX/HTML elements (`<button>` / `<form>` / `<img>` / etc.), the agent
> calls `a11y-moda rules search <element> --format json` to load
> relevant MODA rules **before** generating code. This is proactive,
> not reactive — the agent writes accessible code from the start, not
> after lint complains.

For platform-agnostic AI agent integration (any LLM that can call CLI
tools), read [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) — it
documents the JSON output schema, status enum semantics, third-party
caveat decoding, and triage workflow that any agent should follow.

---

## Pre-flight (every example assumes this)

```bash
# Lightweight: lint + rules subcommand only (~30MB)
pip install a11y-moda

# Add browser-based scan/site (~290MB total with chromium)
pip install 'a11y-moda[scan]'
playwright install chromium
```

The CLI emits clear install instructions when a missing-dependency code
path is hit. Examples are designed to work with the lightweight install
by default; `scan` / `site` paths gracefully degrade to "please install
[scan] extras" messages.

---

## Contributing examples for new platforms

If you've integrated `a11y-moda` with a tool not listed above (Codex, Continue, RooCode, Copilot Workspace, custom agent…), PRs welcome:

1. Create `examples/<tool-name>/`
2. Include a `README.md` with install steps + usage
3. Reference [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) as the authoritative spec — examples should not re-invent the JSON schema or triage rules
4. Add a row to the table above

Examples are **not** part of the published Python package (won't ship with `pip install a11y-moda`). They live in the repo for discoverability only.
