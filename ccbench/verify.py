"""Grade one run by executing the task's check command in its workspace.

The grader is deliberately the dumbest possible thing that is still honest: it
runs ``task.verify_cmd`` and maps the process outcome to an ``Outcome``. There is
no LLM judge and no fuzzy matching, so the pass/fail signal is reproducible and a
third party can re-run the exact command by hand.

The four-way mapping is what keeps a pass rate trustworthy:
- exit 0            -> PASS    (the task's own tests accept the work)
- exit non-zero     -> FAIL    (tests ran and rejected the work)
- TimeoutExpired    -> TIMEOUT (no verdict; counted apart from FAIL)
- command not found -> ERROR   (harness misconfig; never a silent FAIL)
"""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import Outcome, Task

VERIFY_TAIL_LINES = 15


def run_check(task: Task, workspace: str | Path) -> tuple[Outcome, str]:
    """Run the task's verify command and return ``(outcome, detail)``.

    ``detail`` is the last few lines of combined stdout/stderr (or the error
    message), enough to see *why* a run failed without storing megabytes of logs.
    """
    try:
        proc = subprocess.run(
            task.verify_cmd,
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
