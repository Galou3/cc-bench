import textwrap
from pathlib import Path

from ccbench.agents import make_agent
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.suite import load_suite


def _build_suite(tmp_path):
    t = tmp_path / "suite"
    (t / "tasks" / "x" / "workspace").mkdir(parents=True)
    (t / "tasks" / "x" / "reference").mkdir(parents=True)
    (t / "tasks" / "x" / "hidden").mkdir(parents=True)
    (t / "tasks" / "x" / "workspace" / "m.py").write_text("def f():\n    return 0\n", encoding="utf-8")
    (t / "tasks" / "x" / "reference" / "m.py").write_text("def f():\n    return 42\n", encoding="utf-8")
    (t / "tasks" / "x" / "hidden" / "test_hidden.py").write_text(
        "from m import f\n\n\ndef test_f():\n    assert f() == 42\n", encoding="utf-8")
    (t / "tasks.yaml").write_text(textwrap.dedent("""
        name: hid
        tasks:
          - id: x
            prompt: make f() return 42
            template_dir: tasks/x/workspace
            reference_dir: tasks/x/reference
            hidden_tests_dir: tasks/x/hidden
            verify_cmd: ["python", "-m", "pytest", "-q"]
    """), encoding="utf-8")
    return t


def test_hidden_tests_resolved(tmp_path):
    suite = _build_suite(tmp_path)
    _, tasks = load_suite(suite)
    assert tasks[0].hidden_tests_dir and Path(tasks[0].hidden_tests_dir).is_dir()


def test_reference_passes_hidden_tests(tmp_path):
    suite = _build_suite(tmp_path)
    run = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 1.0})],
                    make_agent("mock"), reps=1, seed=0)
    assert run.results and all(r.passed for r in run.results)


def test_stub_fails_hidden_tests(tmp_path):
    # The agent never sees the hidden test; the stub returns the wrong value,
    # so grading against the held-out test fails - exactly what keeps a hard
    # task off the 100% ceiling.
    suite = _build_suite(tmp_path)
    run = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 0.0})],
                    make_agent("mock"), reps=1, seed=0)
    assert run.results and all(not r.passed for r in run.results)
