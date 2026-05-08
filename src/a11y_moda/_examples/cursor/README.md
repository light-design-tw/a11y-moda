# Cursor integration

[Cursor](https://cursor.sh/) auto-loads `.cursorrules` from the repo
root as part of every chat / inline-edit context.

## Setup

1. Copy `.cursorrules` from this directory to your repo root.
2. Reload the Cursor window. The rules apply to the next chat / Composer
   / inline-edit session.

## Install a11y-moda

```bash
pip install a11y-moda                 # lint + rules subcommand only
pip install 'a11y-moda[scan]'         # add browser-based scan/site
playwright install chromium           # required for --render
```

If Cursor surfaces an "a11y-moda not installed" error, run the first
command. Cursor will not auto-install for you.

## How it works

`.cursorrules` tells Cursor:

1. **Pre-write rule lookup** — when about to write `<button>`, `<form>`,
   `<img>`, etc., Cursor calls `a11y-moda rules search <element> --format
   json` and uses the returned MODA rules to write compliant code.
2. **Reactive lint** — after edits, Cursor can be asked to run
   `a11y-moda lint <changed files>` and apply fixes.
3. **MODA rule_id mapping** — every issue surfaces with HM/GN/CS/AR/FA/SC
   code, suitable for MODA 標章 自評 documentation.

## Reference

Full CLI spec, JSON schema, triage rules:
<https://github.com/light-design-tw/a11y-moda/blob/main/docs/AI_INTEGRATION.md>
