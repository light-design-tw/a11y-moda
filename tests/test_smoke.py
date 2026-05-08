"""Smoke tests — packaging, entry points, CLI surface, regression invariants.

These tests do NOT verify rule logic correctness (that's lint_golden's job).
They verify the CLI runs at all, subcommands are wired up, bundled
package-data is reachable, and prior-version regressions stay fixed.

Most invariants here mirror real packaging bugs that have shipped:
- v0.3.1: .aider.conf.yml dotfile silently omitted from wheel
- v0.2.1: GN1210100E lint emitting `fail` instead of `caveat`
- v0.3.0: rules subcommand absent, no JSON contract for knowledge queries
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from .conftest import run_cli


# ---------- Tier 1: CLI surface ----------

def test_version_runs():
    r = run_cli("--version")
    assert "a11y-moda" in r.stdout
    # Don't assert specific version — pyproject is source of truth, test
    # would churn every release.


def test_top_help_lists_all_subcommands():
    r = run_cli("--help")
    out = r.stdout
    for cmd in ("lint", "scan", "site", "rules", "init", "explain"):
        assert cmd in out, f"--help missing subcommand: {cmd}"


def test_lint_help_runs():
    run_cli("lint", "--help")


def test_scan_help_runs():
    run_cli("scan", "--help")


def test_rules_help_runs():
    run_cli("rules", "--help")


# ---------- Tier 1: init subcommand + bundled package-data ----------

def test_init_list_shows_all_ides():
    r = run_cli("init", "--list")
    out = r.stdout
    for ide in ("claude-code", "cursor", "copilot", "aider", "agent"):
        assert ide in out, f"init --list missing: {ide}"


def test_init_claude_code_writes_skill_files(tmp_path: Path):
    dest = tmp_path / "skill-dir"
    run_cli("init", "claude-code", "--dest", str(dest))
    assert (dest / "SKILL.md").exists(), "init claude-code didn't write SKILL.md"
    assert (dest / "REFERENCE.md").exists(), "init claude-code didn't write REFERENCE.md"
    # Frontmatter must survive packaging — Claude reads it for skill triggering.
    skill_text = (dest / "SKILL.md").read_text(encoding="utf-8")
    assert skill_text.startswith("---\n"), "SKILL.md missing YAML frontmatter"
    assert "name: a11y-moda" in skill_text


def test_init_aider_dotfile_bundled(tmp_path: Path):
    """Regression for v0.3.1: setuptools default glob skipped .aider.conf.yml.

    If this test fails, check pyproject.toml [tool.setuptools.package-data] —
    the explicit `_examples/aider/.aider.conf.yml` line must be present.
    """
    dest = tmp_path / ".aider.conf.yml"
    run_cli("init", "aider", "--dest", str(dest))
    assert dest.exists(), "init aider didn't write .aider.conf.yml — dotfile bundling broken"
    content = dest.read_text(encoding="utf-8")
    assert len(content) > 100, "aider config suspiciously empty — bundled file may be truncated"


def test_init_cursor_dotfile_bundled(tmp_path: Path):
    """Regression — same root cause as aider test, different dotfile."""
    dest = tmp_path / ".cursorrules"
    run_cli("init", "cursor", "--dest", str(dest))
    assert dest.exists(), "init cursor didn't write .cursorrules — dotfile bundling broken"
    assert len(dest.read_text(encoding="utf-8")) > 100


def test_init_agent_prints_to_stdout():
    r = run_cli("init", "agent", "--print")
    # AGENT.md content should land on stdout, not require a file write.
    assert len(r.stdout) > 200, "init agent --print emitted suspiciously little"


# ---------- Tier 1: lint emits valid JSON ----------

def test_lint_emits_parseable_json(tmp_workdir: Path):
    sample = tmp_workdir / "sample.tsx"
    sample.write_text("export const X = () => <img src='x' />;\n", encoding="utf-8")
    r = run_cli("lint", str(sample), "--format", "json")
    raw = r.stdout
    if raw.startswith("linting"):
        raw = raw.split("\n", 1)[1]
    data = json.loads(raw)  # raises if invalid JSON
    assert "files" in data
    assert "summary" in data
    assert data["summary"]["files_scanned"] == 1
    rule_ids = {i["rule_id"] for f in data["files"] for i in f["issues"]}
    assert "HM1110100C" in rule_ids


def test_lint_runtime_authoritative_downgrade(tmp_workdir: Path):
    """Regression for v0.2.1: GN1210100E (mouse handler missing keyboard
    equivalent) must emit `caveat` not `fail` in lint context — AST cannot
    see cross-file useHotkeys / event delegation.
    """
    sample = tmp_workdir / "click_div.tsx"
    sample.write_text(
        "export const X = () => <div onClick={() => alert('hi')}>click</div>;\n",
        encoding="utf-8",
    )
    r = run_cli("lint", str(sample), "--format", "json")
    raw = r.stdout
    if raw.startswith("linting"):
        raw = raw.split("\n", 1)[1]
    data = json.loads(raw)
    gn = [i for f in data["files"] for i in f["issues"] if i["rule_id"] == "GN1210100E"]
    assert gn, "GN1210100E did not fire on <div onClick> — rule missing or AST broken"
    assert gn[0]["status"] == "caveat", (
        f"GN1210100E emitted {gn[0]['status']!r}; expected 'caveat' "
        f"(runtime_authoritative downgrade)"
    )


# ---------- Tier 1: rules / knowledge subcommand ----------

def test_rules_show_known_rule_returns_json():
    r = run_cli("rules", "show", "HM1110100C", "--format", "json")
    data = json.loads(r.stdout)
    assert data["rule_id"] == "HM1110100C"
    assert data["guideline"] == "1.1.1"
    assert data["level_name"] == "A"
    # 9-field schema contract — agents depend on these keys existing.
    for key in ("desc", "source", "runtime_authoritative", "wcag_url", "topic", "scope"):
        assert key in data, f"rules show missing field: {key}"


def test_rules_search_returns_results():
    r = run_cli("rules", "search", "button", "--format", "json")
    data = json.loads(r.stdout)
    assert data["query"] == "button"
    assert data["count"] > 0, "rules search 'button' returned 0 — alias map broken?"
    assert isinstance(data["rules"], list)


def test_explain_alias_equals_rules_show():
    """`explain` is a top-level alias for `rules show` — must return identical JSON."""
    r1 = run_cli("rules", "show", "HM1110100C", "--format", "json")
    r2 = run_cli("explain", "HM1110100C", "--format", "json")
    assert json.loads(r1.stdout) == json.loads(r2.stdout)
