# a11y-moda tests

Two tiers, both purposefully narrow:

| File | Tier | Purpose |
|---|---|---|
| `test_smoke.py` | T1 | CLI surface, packaging, prior-version regressions. Does NOT verify rule logic correctness |
| `test_lint_golden.py` | T2 | Snapshot diff against frozen fixtures. Catches refactor regressions in rule helpers / `_lib/` |

Per-rule unit tests are intentionally out of scope — 143 brittle fixtures
with 0 external contributors today is negative ROI.

## Run

```bash
pip install -e .         # editable install
pip install pytest
pytest tests/
```

CI: `release.yml` runs `pytest tests/` against the freshly built wheel
before publishing to PyPI.

## When a snapshot test fails

Inspect the diff in the assertion output. Two cases:

**Case A — intentional rule-logic change.** You added a new rule, fixed
a false positive, tightened a `_lib/` helper, etc. The drift is correct.

```bash
python tests/regen_snapshots.py
git add tests/fixtures/*.expected.json
git commit              # alongside the rule change in the same commit
```

The snapshot diff IS the changelog entry for the behavior change.
Reviewers can see exactly which `(rule_id, status, line, col)` tuples
moved.

**Case B — unintended regression.** Output drifted but no rule logic
should have changed (you were just refactoring). Investigate before
regenerating. Common culprits: import depth typo silently dropping a
rule, `_lib/` helper changed semantics, tree-sitter grammar version
bump in `pyproject.toml`.

## Fixture design rules

- **Lint-only.** No Playwright (deterministic, no Chromium needed in CI).
- **No LLM rules.** E rules requiring LLM judgement are non-deterministic
  and excluded from snapshot fixtures.
- **Small.** Each fixture targets 2-4 specific `rule_id`s. Smaller fixtures
  fail more loudly when wrong.
- **Self-documenting.** Fixture comments explain why each violation exists.
  Future readers should see "this `<img>` deliberately has no `alt`" not
  "wat why no alt".

## Adding a new fixture

1. Create `tests/fixtures/<name>.{tsx,html,jsx,js}` with intentional violations
2. Add the filename to `SNAPSHOT_FIXTURES` in `test_lint_golden.py`
3. Run `python tests/regen_snapshots.py` to generate the snapshot
4. Inspect the generated `tests/fixtures/<name>.expected.json` for sanity
5. Commit fixture + snapshot together
