from pathlib import Path

from ccbench.agents.base import AgentRunInfo
from ccbench.models import Condition, Usage
from ccbench.runner import run_suite
from ccbench.scaffold import scaffold
from ccbench.validate import validate_suite
from ccbench.workspace import restore_protected_files


class TamperAgent:
    """Reward hacker: rewrites the visible test to always pass, fixes nothing."""

    name = "tamper"

    def run(self, ctx) -> AgentRunInfo:
        for f in Path(ctx.workspace).rglob("test_*.py"):
            f.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        return AgentRunInfo(usage=Usage())


def test_test_tampering_does_not_grade_as_pass(tmp_path):
    scaffold(tmp_path)
    run = run_suite(tmp_path / "ccbench_suite", [Condition(name="c")],
                    TamperAgent(), reps=1, seed=0)
    assert run.results and all(not r.passed for r in run.results)


def test_restore_protected_files_returns_restored_paths(tmp_path):
    tpl = tmp_path / "tpl"
    ws = tmp_path / "ws"
    (tpl / "sub").mkdir(parents=True)
    ws.mkdir()
    (tpl / "test_a.py").write_text("original\n", encoding="utf-8")
    (tpl / "sub" / "b_test.py").write_text("original\n", encoding="utf-8")
    (tpl / "main.py").write_text("code\n", encoding="utf-8")
    (ws / "test_a.py").write_text("tampered\n", encoding="utf-8")
    restored = restore_protected_files(tpl, ws)
    assert sorted(restored) == sorted(["test_a.py", str(Path("sub") / "b_test.py")])
    assert (ws / "test_a.py").read_text() == "original\n"
    assert not (ws / "main.py").exists()  # non-test files are not touched


def test_validate_flags_good_and_broken_suites(tmp_path):
    scaffold(tmp_path)
    good = validate_suite(tmp_path / "ccbench_suite")
    assert all(v.ok for v in good)

    # break the suite: make the reference identical to the broken stub
    suite = tmp_path / "ccbench_suite"
    stub = (suite / "tasks" / "sum_list" / "workspace" / "sumlist.py").read_text(encoding="utf-8")
    (suite / "tasks" / "sum_list" / "reference" / "sumlist.py").write_text(stub, encoding="utf-8")
    bad = validate_suite(suite)
    assert any(not v.ok and v.reference_passes is False for v in bad)