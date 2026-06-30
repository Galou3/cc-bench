"""The Agent protocol: act on a workspace in place and report usage; grading is separate."""

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
