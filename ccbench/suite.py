"""Load benchmark suites and conditions from declarative YAML."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import yaml

from .models import Condition, Task


class SuiteError(Exception):
    """Raised when a suite or condition definition is malformed."""


def load_suite(suite_dir: str | Path) -> tuple[str, list[Task]]:
    """Return ``(suite_name, tasks)`` with all task paths resolved to absolute.

    Raises ``SuiteError`` on a missing manifest, an empty suite, a duplicate task
    id, or a task whose ``template_dir`` does not exist on disk.
    """
    suite_dir = Path(suite_dir)
    manifest = suite_dir / "tasks.yaml"
    if not manifest.is_file():
        raise SuiteError(f"no tasks.yaml in suite directory: {suite_dir}")

    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    name = str(data.get("name", suite_dir.name))
    raw_tasks = data.get("tasks") or []
    if not raw_tasks:
        raise SuiteError(f"suite '{name}' declares no tasks")

    tasks: list[Task] = []
    seen: set[str] = set()
    for raw in raw_tasks:
        task = Task.from_dict(raw)
        if task.id in seen:
            raise SuiteError(f"duplicate task id in suite '{name}': {task.id}")
        seen.add(task.id)

        template = (suite_dir / task.template_dir).resolve()
        if not template.is_dir():
            raise SuiteError(
                f"task '{task.id}': template_dir does not exist: {template}"
            )
        reference = None
        if task.reference_dir:
            reference = (suite_dir / task.reference_dir).resolve()
            if not reference.is_dir():
                raise SuiteError(
                    f"task '{task.id}': reference_dir does not exist: {reference}"
                )
        hidden = None
        if task.hidden_tests_dir:
            hidden = (suite_dir / task.hidden_tests_dir).resolve()
            if not hidden.is_dir():
                raise SuiteError(
                    f"task '{task.id}': hidden_tests_dir does not exist: {hidden}"
                )

        tasks.append(
            replace(
                task,
                template_dir=str(template),
                reference_dir=(str(reference) if reference else None),
                hidden_tests_dir=(str(hidden) if hidden else None),
            )
        )

    return name, tasks


def load_conditions(path: str | Path) -> list[Condition]:
    """Load conditions from a single YAML file or a directory of YAML files.

    A file may hold one condition (a mapping), a top-level ``conditions:`` list,
    or a bare list. Directory loading is sorted for determinism so report column
    order is stable across machines. Raises ``SuiteError`` on duplicate names.
    """
    p = Path(path)
    if p.is_dir():
        files = sorted(p.glob("*.yaml")) + sorted(p.glob("*.yml"))
        if not files:
            raise SuiteError(f"no *.yaml conditions in directory: {p}")
    elif p.is_file():
        files = [p]
    else:
        raise SuiteError(f"conditions path not found: {p}")

    conditions: list[Condition] = []
    seen: set[str] = set()
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if isinstance(doc, list):
            items = doc
        elif isinstance(doc, dict) and "conditions" in doc:
            items = doc["conditions"]
        else:
            items = [doc]
        for raw in items:
            cond = Condition.from_dict(raw)
            if cond.name in seen:
                raise SuiteError(f"duplicate condition name: {cond.name}")
            seen.add(cond.name)
            conditions.append(cond)

    if not conditions:
        raise SuiteError(f"no conditions parsed from: {p}")
    return conditions


__all__ = ["SuiteError", "load_suite", "load_conditions"]
