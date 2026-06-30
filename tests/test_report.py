from ccbench.models import Outcome, RunResult, SuiteRun, Usage
from ccbench.report import render_csv, render_markdown


def _run(agent="mock"):
    res = []
    for cond, k in (("baseline", 4), ("variant", 9)):
        for i in range(12):
            oc = Outcome.PASS if i < k else Outcome.FAIL
            res.append(RunResult("t", cond, i, oc, Usage(100, 50, 0.0, 1), 0.1))
    return SuiteRun("sample", agent, ("baseline", "variant"), tuple(res), 0, "2026-01-01T00:00:00+00:00")


def test_markdown_has_mock_banner_and_adjusted_p_column():
    md = render_markdown(_run("mock"), bootstrap_iters=1000, correction="holm")
    assert "SIMULATED" in md
    assert "p (holm)" in md
    assert "`variant`" in md and "`baseline`" in md


def test_markdown_no_banner_for_real_agent():
    md = render_markdown(_run("claude"), bootstrap_iters=1000)
    assert "SIMULATED" not in md


def test_csv_header_and_rows():
    csv_text = render_csv(_run("mock"))
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("condition,passes,fails")
    assert len(lines) == 3  # header + 2 conditions
    assert "baseline" in lines[1] or "baseline" in lines[2]
