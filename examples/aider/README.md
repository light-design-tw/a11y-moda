# Aider integration

[Aider](https://aider.chat/) is a CLI AI coding assistant. It auto-loads
`.aider.conf.yml` from the repo root.

## Install

```bash
pip install a11y-moda                  # lint only (recommended for Aider)
pip install 'a11y-moda[scan]'          # if you also want browser-based scan/site
```

## Setup

1. Copy `.aider.conf.yml` from this directory to your repo root.
2. Adjust the `read:` paths if needed (point to wherever you keep
   accessibility reference material).
3. Aider will pick up the config automatically.

## Behavior

- **`read:`** — Aider injects the listed files as context. Reference
  `docs/AI_INTEGRATION.md` (copy from a11y-moda repo) so Aider knows the
  CLI invocation patterns and JSON schema.
- **`lint-cmd:`** — After Aider edits TSX/JSX/HTML, it runs
  `a11y-moda lint` on the changed files. Output is fed back to Aider so
  the next turn can react to issues.

## Querying rules within Aider chat

Within an Aider session, ask questions like:

```
> What MODA rules apply when I write a <button>?
> Run: a11y-moda rules search button --format json
```

Aider will execute the command and use the JSON output to inform its
next code suggestion.

## Custom command (optional)

Add a wrapper in `.aider/commands/a11y` for one-shot audits:

```bash
#!/bin/bash
# .aider/commands/a11y
url="${1:-http://localhost:3000}"
a11y-moda scan "$url" --level AA --render --allow-private-hosts --format json
```

Then in Aider chat:

```
> /a11y http://localhost:3000/about
```

## Reference

Full CLI spec, JSON schema, triage rules:
<https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md>
