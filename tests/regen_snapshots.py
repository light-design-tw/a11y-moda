"""Regenerate `tests/fixtures/*.expected.json` from current lint output.

Run after a deliberate rule-logic change. Inspect the resulting diff
before committing — the diff IS the changelog entry for the rule change.

    python tests/regen_snapshots.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make conftest helpers importable when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import FIXTURES, lint_to_issues  # noqa: E402

from test_lint_golden import SNAPSHOT_FIXTURES  # noqa: E402


def main() -> int:
    for name in SNAPSHOT_FIXTURES:
        fixture = FIXTURES / name
        expected = FIXTURES / (fixture.stem + ".expected.json")
        issues = lint_to_issues(fixture)
        expected.write_text(
            json.dumps(issues, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"regenerated {expected.relative_to(FIXTURES.parent.parent)}: {len(issues)} issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
