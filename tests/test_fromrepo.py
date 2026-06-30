from ccbench.agents import make_agent
from ccbench.fromrepo import add_task_to_suite, make_task, stub_source
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.suite import load_suite


def test_stub_source_removes_bodies_keeps_signatures():
    out = stub_source("import os\n\nK = 1\n\ndef f(a, b):\n    return a + b\n")
    assert "def f(a, b):" in out
    assert "NotImplementedError" in out
    assert "return a + b" not in out
    assert "K = 1" in out and "import os" in out


def test_from_repo_reference_passes_stub_fails(tmp_path):
    (tmp_path / "mymod.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "test_mymod.py").write_text(
        "from mymod import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    suite = tmp_path / "suite"
    entry = make_task(tmp_path / "mymod.py", tmp_path / "test_mymod.py", suite, "mymod")
    add_task_to_suite(suite, entry)

    _, tasks = load_suite(suite)
    assert tasks[0].id == "mymod" and tasks[0].hidden_tests_dir

    ref = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 1.0})],
                    make_agent("mock"), reps=1, seed=0)
    stub = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 0.0})],
                     make_agent("mock"), reps=1, seed=0)
    assert all(r.passed for r in ref.results)
    assert all(not r.passed for r in stub.results)
