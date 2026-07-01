"""Validate that a suite's tasks are well-formed benchmarks (no agent needed).

A task earns trust only if it discriminates: the shipped workspace must FAIL its
check and the held-out reference must PASS it. Generated suites (from-repo,
from-git) get this gate automatically.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .models import Outcome, Task
from .suite import load_suite
from .verify import run_check
from .workspace import add_files, prepare_workspace


@dataclass(frozen=True, slots=True)
class TaskValidation:
    task_id: str
    stub_fails: bool
    reference_passes: bool | None  # None when the task has no reference_dir
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.stub_fails and self.reference_passes is not False


def _check(task: Task, apply_reference: bool) -> Outcome:
    tmp = tempfile.mkdtemp(prefix="ccbench_val_")
    try:
        ws = prepare_workspace(task, tmp)
        if apply_reference and task.reference_dir:
            add_files(ws, task.reference_dir)
        if task.hidden_tests_dir:
            add_files(ws, task.hidden_tests_dir)
        outcome, _ = run_check(task, ws)
        return outcome
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def validate_task(task: Task) -> TaskValidation:
    stub_outcome = _check(task, apply_reference=False)
    if task.reference_dir:
        ref_outcome = _check(task, apply_reference=True)
        ref_passes: bool | None = ref_outcome is Outcome.PASS
    else:
        ref_outcome, ref_passes = None, None
    detail = f"stub={stub_outcome.value}"
    if ref_outcome is not None:
        detail += f" reference={ref_outcome.value}"
    return TaskValidation(
        task_id=task.id,
        stub_fails=stub_outcome is not Outcome.PASS,
        reference_passes=ref_passes,
        detail=detail,
    )


def validate_suite(suite_dir: str | Path, only_task: str | None = None) -> list[TaskValidation]:
    _, tasks = load_suite(suite_dir)
    if only_task is not None:
        tasks = [t for t in tasks if t.id == only_task]
    return [validate_task(t) for t in tasks]


__all__ = ["TaskValidation", "validate_task", "validate_suite"]
