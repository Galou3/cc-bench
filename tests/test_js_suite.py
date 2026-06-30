import shutil
from pathlib import Path

import pytest

from ccbench.agents import make_agent
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.suite import load_suite

SUITE = Path(__file__).resolve().parents[1] / "suites" / "js_sample"


def test_js_suite_loads():
    name, tasks = load_suite(SUITE)
    assert name == "js_sample" and tasks[0].id == "fizzbuzz_js"
    assert tasks[0].verify_cmd == ["node", "--test"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_suite_runs_with_mock():
    # Proves the harness is language-agnostic: a non-Python task graded by node.
    conds = [Condition(name="b", metadata={"mock_success_prob": 1.0})]
    run = run_suite(SUITE, conds, make_agent("mock"), reps=2, seed=0)
    # p=1 -> mock overlays the JS reference -> `node --test` passes for real
    assert run.results and all(r.passed for r in run.results)
