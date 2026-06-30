"""ccbench init: scaffold a runnable starter suite + conditions into any repo."""

from __future__ import annotations

from pathlib import Path

_FILES: dict[str, str] = {
    "ccbench_suite/tasks.yaml": """\
name: starter
description: >
  A one-task starter suite created by `ccbench init`. Replace it with tasks from
  your own project (any language: set verify_cmd to your test command).
tasks:
  - id: sum_list
    template_dir: tasks/sum_list/workspace
    reference_dir: tasks/sum_list/reference
    verify_cmd: ["python", "-m", "pytest", "-q"]
    timeout_s: 120
    tags: [starter]
    prompt: |
      sum_list(xs) in sumlist.py should return the sum of the numbers in xs,
      ignoring any None entries. The test currently fails. Fix sumlist.py so it
      passes. Do not modify the test.
""",
    "ccbench_suite/tasks/sum_list/workspace/sumlist.py": """\
def sum_list(xs):
    # BUG: crashes on None entries instead of skipping them.
    return sum(xs)
""",
    "ccbench_suite/tasks/sum_list/workspace/test_sumlist.py": """\
from sumlist import sum_list


def test_plain():
    assert sum_list([1, 2, 3]) == 6


def test_skips_none():
    assert sum_list([1, None, 2, None, 3]) == 6


def test_empty():
    assert sum_list([]) == 0
""",
    "ccbench_suite/tasks/sum_list/reference/sumlist.py": """\
def sum_list(xs):
    return sum(x for x in xs if x is not None)
""",
    "conditions/baseline.yaml": """\
name: baseline
description: Default invocation, no CLAUDE.md. The control.
rationale: Control condition.
metadata:
  # Used ONLY by the mock agent for an illustrative first run; real adapters ignore it.
  mock_success_prob: 0.40
""",
    "conditions/concise-claude-md.yaml": """\
name: concise-claude-md
description: A short, focused CLAUDE.md is present.
inject_files:
  CLAUDE.md: |
    # Working agreement
    - Make the failing test pass; do not edit tests.
    - Smallest correct change; read the test first.
rationale: >
  Concise CLAUDE.md is hypothesised to help (Anthropic <200-line guidance;
  long-context degradation). See EVIDENCE.md.
citation:
  - "EVIDENCE.md > Claude Code usage: CLAUDE.md under 200 lines"
metadata:
  mock_success_prob: 0.70
""",
}

_NEXT_STEPS = """\
Created a starter suite and conditions. Next:

  # zero-cost demo (mock agent):
  ccbench run --suite ccbench_suite --conditions conditions --agent mock --reps 20 --report

  # for real (needs the claude CLI authenticated; costs tokens):
  ccbench run --suite ccbench_suite --conditions conditions --agent claude --reps 10 --report

Then replace ccbench_suite/ with tasks from your own project.
"""


def scaffold(target_dir: str | Path) -> tuple[list[str], list[str]]:
    """Create starter files under ``target_dir``. Returns ``(created, skipped)``."""
    root = Path(target_dir)
    created: list[str] = []
    skipped: list[str] = []
    for rel, content in _FILES.items():
        path = root / rel
        if path.exists():
            skipped.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel)
    return created, skipped


def next_steps() -> str:
    return _NEXT_STEPS


__all__ = ["scaffold", "next_steps"]
