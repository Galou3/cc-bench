import json

from ccbench.doctor import apply_fixes, audit, health_score, render, summary


def _find(findings, rule):
    return next((f for f in findings if f.rule == rule), None)


def test_long_claude_md_fails(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("\n".join(f"line {i}" for i in range(600)), encoding="utf-8")
    f = _find(audit(tmp_path), "claude_md.length")
    assert f is not None and f.severity == "fail"


def test_oversize_but_not_huge_warns(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("\n".join(f"line {i}" for i in range(300)), encoding="utf-8")
    assert _find(audit(tmp_path), "claude_md.length").severity == "warn"


def test_concise_claude_md_passes(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project\n- run: x\n- test: y\n", encoding="utf-8")
    assert _find(audit(tmp_path), "claude_md.length").severity == "pass"


def test_missing_claude_md_is_info_and_fix_creates_it(tmp_path):
    findings = audit(tmp_path)
    assert _find(findings, "claude_md.present").severity == "info"
    actions = apply_fixes(tmp_path, findings)
    assert actions and (tmp_path / "CLAUDE.md").is_file()
    # re-audit: the file now exists and is concise
    assert _find(audit(tmp_path), "claude_md.length").severity == "pass"
    # fix never overwrites an existing file
    assert apply_fixes(tmp_path, audit(tmp_path)) == []


def test_invalid_settings_json_fails(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{ not valid json ", encoding="utf-8")
    assert _find(audit(tmp_path), "settings.valid").severity == "fail"


def test_permissions_allowlist_passes(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Edit", "Bash(git commit *)"]}}), encoding="utf-8")
    assert _find(audit(tmp_path), "settings.permissions").severity == "pass"


def test_flags_unfilled_starter_placeholders(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# <Project name>\n- Run: `<command>`\n", encoding="utf-8")
    assert _find(audit(tmp_path), "claude_md.placeholders").severity == "warn"


def test_agents_md_absent_is_info_present_long_fails(tmp_path):
    assert _find(audit(tmp_path), "agents_md.present").severity == "info"
    (tmp_path / "AGENTS.md").write_text("\n".join(f"l{i}" for i in range(600)), encoding="utf-8")
    assert _find(audit(tmp_path), "agents_md.length").severity == "fail"


def test_test_command_flagged_when_absent(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project\nSome prose about the project.\n", encoding="utf-8")
    assert _find(audit(tmp_path), "claude_md.test_command") is not None


def test_test_command_not_flagged_when_present(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project\nRun tests with `pytest -q`.\n", encoding="utf-8")
    assert _find(audit(tmp_path), "claude_md.test_command") is None


def test_health_score_drops_on_fail(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("\n".join(f"l{i}" for i in range(600)), encoding="utf-8")
    s = health_score(audit(tmp_path))
    assert 0 <= s < 100


def test_health_score_full_when_only_infos(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# P\nRun tests with `pytest -q`.\n", encoding="utf-8")
    assert health_score(audit(tmp_path)) == 100


def test_render_has_productivity_headline(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("\n".join(f"l{i}" for i in range(600)), encoding="utf-8")
    text = render(audit(tmp_path), tmp_path)
    assert "costing you quality" in text


def test_render_and_exit_signal(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("\n".join(f"l{i}" for i in range(600)), encoding="utf-8")
    findings = audit(tmp_path)
    text = render(findings, tmp_path)
    assert "doctor" in text and "FAIL" in text
    assert summary(findings)["fail"] >= 1
