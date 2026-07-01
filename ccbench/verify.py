"""Grade one run by executing the task's verify_cmd in its workspace."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import Outcome, Task
from .sandbox import wrap_command

VERIFY_TAIL_LINES = 15


def run_check(task: Task, workspace: str | Path, sandbox: str = "none",
              sandbox_image: str = "python:3.12-slim",
              sandbox_network: str = "none") -> tuple[Outcome, str]:
    """Run the task's verify command and return ``(outcome, detail)``.

    ``detail`` is the last few lines of combined stdout/stderr (or the error
    message), enough to see *why* a run failed without storing megabytes of logs.
    """
    cmd = wrap_command(task.verify_cmd, workspace, mode=sandbox,
                       image=sandbox_image, network=sandbox_network)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=task.timeout_s,
        )
    except subprocess.TimeoutExpired:
        return Outcome.TIMEOUT, f"verify_cmd timed out after {task.timeout_s}s"
    except (FileNotFoundError, OSError) as exc:
        return Outcome.ERROR, f"verify_cmd not runnable: {exc}"

    combined = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(combined.strip().splitlines()[-VERIFY_TAIL_LINES:])
    outcome = Outcome.PASS if proc.returncode == 0 else Outcome.FAIL
    return outcome, tail


__all__ = ["run_check", "VERIFY_TAIL_LINES"]
