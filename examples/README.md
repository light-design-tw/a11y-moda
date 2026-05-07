# Examples

Optional, platform-specific integration examples for `a11y-moda`. Pick the one matching your AI agent / IDE.

| Directory | For | Status |
|---|---|---|
| [`claude-code-skill/`](./claude-code-skill/) | [Claude Code](https://claude.com/claude-code) | Bundled skill (copy into `~/.claude/skills/`) |
| `cursor/` | [Cursor](https://cursor.sh/) | (TODO — for now, see [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) §11.2 for inline `.cursorrules` snippet) |
| `aider/` | [Aider](https://aider.chat/) | (TODO — see [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) §11.3) |
| `github-copilot/` | [GitHub Copilot](https://github.com/features/copilot) | (TODO — see [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) §11.4 for `.github/copilot-instructions.md` snippet) |

For platform-agnostic AI agent integration (any LLM that can call CLI tools), read [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) — it documents the JSON output schema, status enum semantics, third-party caveat decoding, and triage workflow that any agent should follow.

---

## Contributing examples for new platforms

If you've integrated `a11y-moda` with a tool not listed above (Codex, Continue, RooCode, Copilot Workspace, custom agent…), PRs welcome:

1. Create `examples/<tool-name>/`
2. Include a `README.md` with install steps + usage
3. Reference [`docs/AI_INTEGRATION.md`](../docs/AI_INTEGRATION.md) as the authoritative spec — examples should not re-invent the JSON schema or triage rules
4. Add a row to the table above

Examples are **not** part of the published Python package (won't ship with `pip install a11y-moda`). They live in the repo for discoverability only.
