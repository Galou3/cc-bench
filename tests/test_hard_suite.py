from pathlib import Path

from ccbench.agents import make_agent
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.suite import load_suite

SUITE = Path(__file__).resolve().parents[1] / "suites" / "hard"


def test_hard_suite_loads():
    name, tasks = load_suite(SUITE)
    assert name == "hard"
    assert {t.id for t in tasks} == {"merge_intervals", "roman", "lru_cache", "json_path"}
    for t in tasks:
        assert t.hidden_tests_dir and Path(t.hidden_tests_dir).is_dir()


def test_hard_references_pass_held_out_tests():
    # mock p=1 overlays each reference; the held-out tests must pass for real.
    run = run_suite(SUITE, [Condition(name="c", metadata={"mock_success_prob": 1.0})],
                    make_agent("mock"), reps=1, seed=0)
    assert run.results and all(r.passed for r in run.results)
