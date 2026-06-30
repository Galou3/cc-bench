"""Turn your own tested code into held-out benchmark tasks (zero task authoring)."""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

import yaml


def stub_source(src: str) -> str:
    """Return the module with every function/method body replaced by a raise.

    Signatures, decorators, class attributes and module-level code are kept; only
    the bodies are removed, so an agent must reimplement them and the held-out
    tests decide success. Docstrings are preserved as a hint.
    """
    tree = ast.parse(src)
    _stub(tree)
    return ast.unparse(tree)


def _stub(node: ast.AST) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body: list[ast.stmt] = []
            doc = ast.get_docstring(child, clean=False)
            if doc is not None:
                body.append(ast.Expr(value=ast.Constant(value=doc)))
            body.append(ast.Raise(
                exc=ast.Call(func=ast.Name(id="NotImplementedError", ctx=ast.Load()),
                             args=[], keywords=[]),
                cause=None))
            child.body = body
        elif isinstance(child, ast.ClassDef):
            _stub(child)


def make_task(module_path, test_path, suite_dir, task_id, prompt=None):
    """Create one held-out task under ``suite_dir`` from a tested module.

    workspace/ gets the stubbed module, reference/ the original, hidden/ the test.
    Returns the tasks.yaml entry as a dict.
    """
    module_path, test_path, suite_dir = Path(module_path), Path(test_path), Path(suite_dir)
    base = suite_dir / "tasks" / task_id
    (base / "workspace").mkdir(parents=True, exist_ok=True)
    (base / "reference").mkdir(parents=True, exist_ok=True)
    (base / "hidden").mkdir(parents=True, exist_ok=True)

    original = module_path.read_text(encoding="utf-8")
    (base / "workspace" / module_path.name).write_text(stub_source(original), encoding="utf-8")
    (base / "reference" / module_path.name).write_text(original, encoding="utf-8")
    shutil.copy(test_path, base / "hidden" / test_path.name)

    return {
        "id": task_id,
        "prompt": prompt or (
            f"Implement the functions in {module_path.name} so the project's tests "
            "pass. The bodies have been removed (they raise NotImplementedError); "
            "restore correct behaviour. Do not change the public signatures."),
        "template_dir": f"tasks/{task_id}/workspace",
        "reference_dir": f"tasks/{task_id}/reference",
        "hidden_tests_dir": f"tasks/{task_id}/hidden",
        "verify_cmd": ["python", "-m", "pytest", "-q", test_path.name],
        "timeout_s": 300,
        "tags": ["from-repo"],
    }


def add_task_to_suite(suite_dir, entry, suite_name="from-repo"):
    """Create or update ``suite_dir/tasks.yaml`` with ``entry`` (dedup by id)."""
    suite_dir = Path(suite_dir)
    manifest = suite_dir / "tasks.yaml"
    if manifest.is_file():
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    else:
        data = {"name": suite_name, "tasks": []}
    data.setdefault("name", suite_name)
    tasks = [t for t in data.get("tasks", []) if t.get("id") != entry["id"]]
    tasks.append(entry)
    data["tasks"] = tasks
    manifest.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return manifest


__all__ = ["stub_source", "make_task", "add_task_to_suite"]
