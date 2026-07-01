import shutil
import subprocess

import pytest

from ccbench.agents import make_agent
from ccbench.fromgit import changed_files, make_task_from_commit
from ccbench.fromrepo import add_task_to_suite
from ccbench.models import Condition
from ccbench.runner import run_suite
from ccbench.suite import load_suite


def _git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_from_git_generates_discriminating_task(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "m.py").write_text("def f(x):\n    return x\n", encoding="utf-8")
    (repo / "test_m.py").write_text("from m import f\n\n\ndef test_f():\n    assert f(2) == 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    # a commit that changes source AND tests together
    (repo / "m.py").write_text("def f(x):\n    return x\n\n\ndef g(x):\n    return x * 2\n", encoding="utf-8")
    (repo / "test_m.py").write_text(
        "from m import f, g\n\n\ndef test_f():\n    assert f(2) == 2\n\n\ndef test_g():\n    assert g(3) == 6\n",
        encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add g")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()

    src, tests = changed_files(repo, sha)
    assert "m.py" in src and "test_m.py" in tests

    suite = tmp_path / "suite"
    add_task_to_suite(suite, make_task_from_commit(repo, sha, suite, "addg"))
    _, tasks = load_suite(suite)
    assert tasks[0].hidden_tests_dir

    ref = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 1.0})],
                    make_agent("mock"), reps=1, seed=0)
    pre = run_suite(suite, [Condition(name="c", metadata={"mock_success_prob": 0.0})],
                    make_agent("mock"), reps=1, seed=0)
    assert all(r.passed for r in ref.results)       # fix applied -> held-out tests pass
    assert all(not r.passed for r in pre.results)   # pre-fix (no g) -> test_g fails
