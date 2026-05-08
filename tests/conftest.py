"""Shared pytest fixtures + helpers.

Tests invoke `a11y-moda` as a subprocess (not via direct module import) so
they exercise the same surface end users hit: console_script entry point,
argv parsing, JSON over stdout. This catches packaging / entry-point /
encoding regressions that an in-process call would miss.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_cli(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Invoke `a11y-moda` via subprocess. Force UTF-8 to dodge cp950 on Windows CI runners."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        ["a11y-moda", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"a11y-moda {' '.join(args)} exited {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


def lint_to_issues(path: Path) -> list[dict]:
    """Run lint on a single file/dir, return normalised issue tuples.

    Strips absolute file paths (machine-dependent) and keeps only the fields
    that describe what the rule found: (file_basename, rule_id, status, line, col).
    """
    result = run_cli("lint", str(path), "--format", "json")
    raw = result.stdout
    # CLI prints "linting N file(s)" before JSON — strip it.
    if raw.startswith("linting"):
        raw = raw.split("\n", 1)[1]
    data = json.loads(raw)
    issues = []
    for f in data["files"]:
        basename = Path(f["path"]).name
        for i in f["issues"]:
            issues.append({
                "file": basename,
                "rule_id": i["rule_id"],
                "status": i["status"],
                "line": i["line"],
                "col": i["col"],
            })
    issues.sort(key=lambda i: (i["file"], i["line"], i["col"], i["rule_id"]))
    return issues


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tmp_workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a tmp dir + cd into it. CLI's `-o name` writes to ./reports/name."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
