"""The contract every agent adapter implements.

An agent's only job is to *act on a workspace in place* (edit files to try to make
the task's test pass) and report what it cost. Grading is not the agent's job -
the harness grades independently with ``verify.run_check`` - which keeps a clean
separation between "the agent did something" and "the something was correct".

``RunContext`` bundles everything an adapter might need. Real adapters use
``task``/``workspace``; the deterministic mock also uses ``rep``/``seed`` so its
outcome is a pure function of the experiment coordinates (reproducible, and order
-independent under parallelism).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models import Condition, Task, Usage


@dataclass(frozen=True, slots=True)
class RunContext:
    task: Task
    condition: Condition
    workspace: Path
    rep: int = 0
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class AgentRunInfo:
    """What the agent reports back. The harness records usage; ``detail`` is an
    optional short note (e.g. an error tail) surfaced in the run record."""

    usage: Usage
    detail: str = ""


@runtime_checkable
class Agent(Protocol):
    name: str

    def run(self, ctx: RunContext) -> AgentRunInfo:
        """Mutate ``ctx.workspace`` in place and return resource usage."""
        ...


__all__ = ["RunContext", "AgentRunInfo", "Agent"]
