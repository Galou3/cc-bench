import sys

import pytest

from ccbench.models import Condition, Outcome, Task
from ccbench.verify import run_check
from ccbench.workspace import apply_condition, prepare_workspace


def _task(tmp_path, verify_cmd, timeout_s=30):
    return Task(id="t", prompt="p", template_dir=str(tmp_path),
                verify_cmd=verify_cmd, timeout_s=timeout_s)


def test_prepare_workspace_copies_template(tmp_path):
    src = tmp_path / "tpl"
    src.mkdir()
    (src / "a.py").write_text("x = 1\n", encoding="utf-8")
    dest = tmp_path / "ws"
    task = Task(id="t", prompt="p", template_dir=str(src), verify_cmd=["x"])
    prepare_workspace(task, dest)
    assert (dest / "a.py").read_text() == "x = 1\n"


def test_apply_condition_writes_and_blocks_escape(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    written = apply_condition(ws, Condition(name="c", inject_files={"CLAUDE.md": "hi"}))
    assert written == ["CLAUDE.md"] and (ws / "CLAUDE.md").read_text() == "hi"
    with pytest.raises(ValueError):
        apply_condition(ws, Condition(name="evil", inject_files={"../escape.txt": "x"}))
    assert not (tmp_path / "escape.txt").exists()


def test_run_check_pass(tmp_path):
    oc, _ = run_check(_task(tmp_path, [sys.executable, "-c", "import sys; sys.exit(0)"]), tmp_path)
    assert oc is Outcome.PASS


def test_run_check_fail(tmp_path):
    oc, _ = run_check(_task(tmp_path, [sys.executable, "-c", "import sys; sys.exit(1)"]), tmp_path)
    assert oc is Outcome.FAIL


def test_run_check_error_on_missing_command(tmp_path):
    oc, detail = run_check(_task(tmp_path, ["this_command_does_not_exist_xyz"]), tmp_path)
    assert oc is Outcome.ERROR and "not runnable" in detail


def test_run_check_timeout(tmp_path):
    oc, _ = run_check(_task(tmp_path, [sys.executable, "-c", "import time; time.sleep(5)"], timeout_s=1), tmp_path)
    assert oc is Outcome.TIMEOUT
