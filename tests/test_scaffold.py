from ccbench.agents import make_agent
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.scaffold import scaffold
from ccbench.suite import load_suite


def test_scaffold_creates_then_skips(tmp_path):
    created, skipped = scaffold(tmp_path)
    assert created and not skipped
    created2, skipped2 = scaffold(tmp_path)  # idempotent
    assert not created2 and set(skipped2) == set(created)


def test_scaffolded_suite_is_runnable(tmp_path):
    scaffold(tmp_path)
    name, tasks = load_suite(tmp_path / "ccbench_suite")
    assert name == "starter" and any(t.id == "sum_list" for t in tasks)

    # mock with p=1 overlays the reference -> the starter task actually passes
    conds = [Condition(name="b", metadata={"mock_success_prob": 1.0})]
    run = run_suite(tmp_path / "ccbench_suite", conds, make_agent("mock"), reps=2, seed=0)
    assert run.results and all(r.passed for r in run.results)
