import json

from ccbench.analysis import sample_size_two_proportions
from ccbench.cli import main
from ccbench.htmlreport import render_html
from ccbench.models import Outcome, RunResult, SuiteRun, Usage


def test_sample_size_matches_textbook_value():
    n = sample_size_two_proportions(0.5, 0.8, alpha=0.05, power=0.8)
    assert 38 <= n <= 41


def test_sample_size_rejects_equal_rates():
    import pytest
    with pytest.raises(ValueError):
        sample_size_two_proportions(0.5, 0.5)


def test_power_command_prints_floor(capsys):
    rc = main(["power", "--baseline", "0.4", "--effect", "0.2", "--tasks", "4"])
    out = capsys.readouterr().out
    assert rc == 0 and "decided runs per condition" in out and "FLOOR" in out


def _run(agent="mock"):
    res = []
    for cond, k in (("baseline", 4), ("variant", 10)):
        for t in ("t1", "t2"):
            for i in range(6):
                oc = Outcome.PASS if i < k // 2 else Outcome.FAIL
                res.append(RunResult(t, cond, i, oc, Usage(100, 50, 0.0, 1), 0.1))
    return SuiteRun("sample", agent, ("baseline", "variant"), tuple(res), 0,
                    "2026-01-01T00:00:00+00:00")


def test_html_report_is_self_contained(tmp_path):
    html_text = render_html(_run("mock"), iters=800)
    assert html_text.startswith("<!doctype html>") and html_text.endswith("</html>")
    assert "SIMULATED" in html_text
    assert "baseline" in html_text and "variant" in html_text
    assert "<style>" in html_text and "http" not in html_text.split("github.com")[0][:200]


def test_html_report_no_banner_for_real_agent():
    assert "SIMULATED" not in render_html(_run("claude"), iters=800)


def test_doctor_badge_written(tmp_path, capsys):
    (tmp_path / "CLAUDE.md").write_text("# P\nRun tests with `pytest -q`.\n", encoding="utf-8")
    badge_path = tmp_path / ".ccbench" / "badge.json"
    rc = main(["doctor", "--dir", str(tmp_path), "--badge", str(badge_path)])
    assert rc == 0
    badge = json.loads(badge_path.read_text(encoding="utf-8"))
    assert badge["schemaVersion"] == 1
    assert badge["label"] == "cc-bench setup"
    assert badge["message"].endswith("/100")
    assert "img.shields.io/endpoint" in capsys.readouterr().out
