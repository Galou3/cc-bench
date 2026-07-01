"""Generate held-out benchmark tasks from a repo's own git history."""

from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import Path


def _git(repo, *args) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, check=True).stdout


def _git_text(repo, *args) -> str:
    return _git(repo, *args).decode("utf-8", "replace")


def _is_test(path: str) -> bool:
    p = path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    return p.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py") or "/tests/" in f"/{p}")


def changed_files(repo, sha) -> tuple[list[str], list[str]]:
    """Return (source_files, test_files) changed by ``sha`` (Python, non-deleted)."""
    out = _git_text(repo, "diff", "--name-status", f"{sha}~1", sha)
    src, tests = [], []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or parts[0].startswith("D"):
            continue
        path = parts[-1]
        if not path.endswith(".py"):
            continue
        (tests if _is_test(path) else src).append(path)
    return src, tests


def make_task_from_commit(repo, sha, suite_dir, task_id, prompt=None) -> dict:
    """Build a held-out task from a commit that changed both source and tests.

    workspace = the whole repo at the parent commit (pre-change), reference = the
    post-change source files, hidden = the post-change test files. So an agent must
    reproduce the change and is graded on the commit's own tests, held out.
    """
    repo, suite_dir = Path(repo), Path(suite_dir)
    src, tests = changed_files(repo, sha)
    if not src or not tests:
        raise ValueError(
            f"commit {sha} must change both source and test .py files "
            f"(found source={len(src)}, tests={len(tests)})")

    base = suite_dir / "tasks" / task_id
    ws, ref, hid = base / "workspace", base / "reference", base / "hidden"
    for d in (ws, ref, hid):
        d.mkdir(parents=True, exist_ok=True)

    with tarfile.open(fileobj=io.BytesIO(_git(repo, "archive", "--format=tar", f"{sha}~1"))) as tf:
        try:
            tf.extractall(ws, filter="data")  # safe extraction (py3.12+/backports)
        except TypeError:
            tf.extractall(ws)
    for path in src:
        (ref / path).parent.mkdir(parents=True, exist_ok=True)
        (ref / path).write_bytes(_git(repo, "show", f"{sha}:{path}"))
    for path in tests:
        (hid / path).parent.mkdir(parents=True, exist_ok=True)
        (hid / path).write_bytes(_git(repo, "show", f"{sha}:{path}"))

    msg = _git_text(repo, "log", "-1", "--format=%s%n%n%b", sha).strip()
    return {
        "id": task_id,
        "prompt": prompt or (
            "Implement the change so the project's tests pass. The source has been "
            "reset to before the change; recreate the fix.\n\nCommit intent:\n" + msg),
        "template_dir": f"tasks/{task_id}/workspace",
        "reference_dir": f"tasks/{task_id}/reference",
        "hidden_tests_dir": f"tasks/{task_id}/hidden",
        "verify_cmd": ["python", "-m", "pytest", "-q", *tests],
        "timeout_s": 600,
        "tags": ["from-git"],
    }


__all__ = ["changed_files", "make_task_from_commit"]
