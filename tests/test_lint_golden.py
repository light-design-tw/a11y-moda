"""Tier 2 golden-snapshot tests.

Lint is deterministic (pure tree-sitter AST, no LLM, no browser, no
network), so its output for a frozen fixture should be byte-stable
across refactors. If output drifts, either:

  (a) you intended the change — regenerate the snapshot:
      python tests/regen_snapshots.py
      then commit the .expected.json diff alongside the rule change.

  (b) you didn't intend the change — there's a regression. Investigate
      before updating the snapshot.

Snapshots intentionally store only (rule_id, status, line, col) per
file — message text and absolute paths are excluded as they're either
locale/i18n-sensitive or machine-dependent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import lint_to_issues


SNAPSHOT_FIXTURES = ["violations.tsx", "page.html"]


@pytest.mark.parametrize("fixture_name", SNAPSHOT_FIXTURES)
def test_lint_matches_snapshot(fixture_name: str, fixtures_dir: Path):
    fixture = fixtures_dir / fixture_name
    expected_path = fixtures_dir / (fixture.stem + ".expected.json")
    assert fixture.exists(), f"fixture missing: {fixture}"
    assert expected_path.exists(), (
        f"snapshot missing: {expected_path}. "
        f"Generate with: python tests/regen_snapshots.py"
    )

    actual = lint_to_issues(fixture)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    assert actual == expected, (
        f"lint output drifted for {fixture_name}.\n"
        f"--- expected ---\n{json.dumps(expected, ensure_ascii=False, indent=2)}\n"
        f"--- actual ---\n{json.dumps(actual, ensure_ascii=False, indent=2)}\n"
        f"If this change is intentional, regenerate snapshots: "
        f"python tests/regen_snapshots.py"
    )
