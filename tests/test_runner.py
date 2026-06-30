from pathlib import Path

from ccbench.agents import make_agent
from ccbench.analysis import summarize_condition
from ccbench.models import Condition
from ccbench.runner import load_run, run_suite, save_run

SAMPLE = Path(__file__).resolve().parents[1] / "suites" / "sample"


def test_runner_recovers_planted_effect_and_persists(tmp_path):
    conds = [
        Condition(name="baseline", metadata={"mock_success_prob": 0.20}),
        Condition(name="variant", metadata={"mock_success_prob": 0.90}),
    ]
    run = run_suite(SAMPLE, conds, make_agent("mock"), reps=4, seed=0)
    assert len(run.results) == 2 * 3 * 4  # conditions x tasks x reps

    base = summarize_condition(run.for_condition("baseline"), "baseline").rate
    var = summarize_condition(run.for_condition("variant"), "variant").rate
    assert var > base  # deterministic given seed=0; the planted effect shows up

    out = save_run(run, tmp_path / "runs")
    assert load_run(out).to_dict() == run.to_dict()
    assert load_run(tmp_path / "runs" / "latest").to_dict() == run.to_dict()


def test_runner_no_errors_on_sample(tmp_path):
    conds = [Condition(name="baseline", metadata={"mock_success_prob": 0.5})]
    run = run_suite(SAMPLE, conds, make_agent("mock"), reps=3, seed=1)
    # every run is decided (pass/fail), no harness ERROR
    assert all(r.outcome.value in {"pass", "fail"} for r in run.results)
