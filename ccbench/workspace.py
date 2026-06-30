"""Build the isolated filesystem an agent works in for a single run.

Kept separate from grading (verify.py) and orchestration (runner.py) because the
filesystem layer is the part most likely to differ between a Windows dev box and
Linux CI, so it is small and independently testable.

Isolation matters for validity: if run N could see files left by run N-1, a pass
rate would measure contamination, not the agent. Every run gets a fresh copy of
the task template; the held-out reference is outside the template and never lands
here.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .models import Condition, Task


def prepare_workspace(task: Task, dest: str | Path) -> Path:
    """Copy a task's template into ``dest`` and return it as a Path.

    Uses ``dirs_exist_ok`` so callers may point at a freshly made run directory.
    Only the template is copied - never the reference solution.
    """
    dest = Path(dest)
    shutil.copytree(Path(task.template_dir), dest, dirs_exist_ok=True)
    return dest


def apply_condition(workspace: str | Path, condition: Condition) -> list[str]:
    """Write a condition's ``inject_files`` into the workspace before the agent runs.

    Paths are workspace-relative; missing parent directories are created. Returns
    the list of relative paths written, for the run record. Refuses any path that
    escapes the workspace (e.g. ``../../etc/x``), so a malicious or sloppy
    condition file can't scribble outside the sandbox.
    """
    workspace = Path(workspace)
    written: list[str] = []
    for rel, content in condition.inject_files.items():
        target = workspace / rel
        if not _is_within(workspace, target):
            raise ValueError(
                f"condition '{condition.name}': inject path escapes workspace: {rel}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel)
    return written


def _is_within(root: str | Path, target: str | Path) -> bool:
    root_resolved = Path(root).resolve()
    try:
        Path(target).resolve().relative_to(root_resolved)
        return True
    except ValueError:
        return False


__all__ = ["prepare_workspace", "apply_condition"]
