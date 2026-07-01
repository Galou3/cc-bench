from ccbench.models import Outcome, RunResult, SuiteRun, Usage
from ccbench.report import render_csv, render_markdown, render_run_comparison


def _run(agent="mock"):
    res = []
    for cond, k in (("baseline", 4), ("variant", 9)):
        for i in range(12):
            oc = Outcome.PASS if i < k else Outcome.FAIL
            res.append(RunResult("t", cond, i, oc, Usage(100, 50, 0.0, 1), 0.1))
    return SuiteRun("sample", agent, ("baseline", "variant"), tuple(res), 0, "2026-01-01T00:00:00+00:00")


def test_markdown_has_mock_banner_and_two_level_verdicts():
    md = render_markdown(_run("mock"), bootstrap_iters=1000, correction="holm")
    assert "SIMULATED" in md
    assert "p (perm, holm)" in md
    assert "Does it generalize beyond this suite?" in md
    assert "`variant`" in md and "`baseline`" in md


def test_markdown_no_banner_for_real_agent():
    md = render_markdown(_run("claude"), bootstrap_iters=1000)
    assert "SIMULATED" not in md


def _run_named(agent, k, cond="baseline", n=12):
    res = [RunResult("t", cond, i, Outcome.PASS if i < k else Outcome.FAIL, Usage(), 0.1)
           for i in range(n)]
    return SuiteRun("sample", agent, (cond,), tuple(res), 0, "2026-01-01T00:00:00+00:00")


def test_render_run_comparison_picks_winner():
    a = _run_named("claude", 3)    # 25%
    b = _run_named("codex", 11)    # ~92%
    md = render_run_comparison(a, b, "claude", "codex", bootstrap_iters=1500)
    assert "claude vs codex" in md and "overall" in md
    assert "codex better" in md


def test_render_run_comparison_flags_mock():
    md = render_run_comparison(_run_named("mock", 5), _run_named("claude", 6),
                               "mock", "claude", bootstrap_iters=800)
    assert "mock" in md.lower() and "not a real measurement" in md


def test_csv_header_and_rows():
    csv_text = render_csv(_run("mock"))
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("condition,passes,fails")
    assert len(lines) == 3  # header + 2 conditions
    assert "baseline" in lines[1] or "baseline" in lines[2]
