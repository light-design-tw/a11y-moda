# GitHub Copilot integration

GitHub Copilot Chat auto-loads `.github/copilot-instructions.md` when
chatting in a repo. Place the included file at that exact path in your
own repo.

## Setup

1. Copy `.github/copilot-instructions.md` from this directory to the
   matching path in your repo:

   ```
   <your-repo>/.github/copilot-instructions.md
   ```

2. Open Copilot Chat in VS Code / Visual Studio / JetBrains plugin.
   Instructions auto-apply to the next message in this repo.

## Install a11y-moda

```bash
pip install a11y-moda                 # lint + rules subcommand only
pip install 'a11y-moda[scan]'         # add browser-based scan/site
playwright install chromium           # required for --render
```

## What's in the instructions file

- **Pre-write** — Copilot is told to call `a11y-moda rules search`
  before generating accessibility-sensitive elements
- **Reactive** — `a11y-moda lint` / `scan` invocation patterns + JSON
  parsing rules
- **Triage** — fail / caveat / info / third-party handling
- **Anti-patterns** — what NOT to do (auto-install, --probe-modals on
  prod, etc.)

## Note on Copilot Workspace / Skillsets

Copilot has no formal "skill" mechanism comparable to Claude Code. The
`.github/copilot-instructions.md` file is the closest equivalent:
auto-loaded as context for chat sessions in that repo.

For Copilot Workspace and Copilot Skillsets (REST-endpoint integrations),
see [`docs/AI_INTEGRATION.md`](https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md)
§11.4 in the a11y-moda repo. Currently the chat-instructions path is the
supported integration.

## Reference

Full CLI spec, JSON schema, triage rules:
<https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md>
