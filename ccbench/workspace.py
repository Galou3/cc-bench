"""Build the isolated workspace an agent works in for a single run."""

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


def add_files(workspace: str | Path, src_dir: str | Path) -> None:
    """Copy the contents of ``src_dir`` into the workspace (overwriting).

    Used by the runner to drop held-out tests in *after* the agent has finished,
    so the agent never sees them.
    """
    shutil.copytree(Path(src_dir), Path(workspace), dirs_exist_ok=True)


TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "*.test.js", "*_test.go", "*Test.java")


def restore_protected_files(template_dir: str | Path, workspace: str | Path) -> list[str]:
    """Restore the template's test files over the workspace, post-agent.

    An agent that rewrites visible tests to always pass would otherwise grade as
    PASS (reward hacking). Grading must run the ORIGINAL tests, so any template
    file matching a test pattern is copied back before verification.
    """
    tpl, ws = Path(template_dir), Path(workspace)
    restored: list[str] = []
    for pattern in TEST_FILE_PATTERNS:
        for f in tpl.rglob(pattern):
            if not f.is_file():
                continue
            rel = f.relative_to(tpl)
            dest = ws / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, dest)
            restored.append(str(rel))
    return restored


def _is_within(root: str | Path, target: str | Path) -> bool:
    root_resolved = Path(root).resolve()
    try:
        Path(target).resolve().relative_to(root_resolved)
        return True
    except ValueError:
        return False


__all__ = ["prepare_workspace", "apply_condition", "add_files",
           "restore_protected_files", "TEST_FILE_PATTERNS"]
