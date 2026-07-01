"""Deterministic, zero-cost mock agent.

Succeeds per a condition's ground-truth probability, hashing (seed, task,
condition, rep). On success it copies the held-out reference into the workspace so
the real grader passes for real (we never fake a PASS).
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from ..models import Usage
from .base import AgentRunInfo, RunContext


def _uniform01(seed: int | None, task_id: str, condition: str, rep: int) -> float:
    """A deterministic pseudo-uniform in [0, 1) from the experiment coordinates.

    SHA-256 of the coordinates -> first 64 bits / 2**64. Pure function of inputs,
    so parallel execution can't perturb it (unlike a call-order counter).
    """
    key = f"{seed}|{task_id}|{condition}|{rep}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:16], 16) / 2**64


class MockAgent:
    name = "mock"

    def __init__(self, base_prob: float = 0.5) -> None:
        # Fallback probability when a condition does not declare its own.
        self.base_prob = base_prob

    def run(self, ctx: RunContext) -> AgentRunInfo:
        prob = float(ctx.condition.metadata.get("mock_success_prob", self.base_prob))
        draw = _uniform01(ctx.seed, ctx.task.id, ctx.condition.name, ctx.rep)
        success = draw < prob

        if success and ctx.task.reference_dir:
            # Apply the real fix (preserving nested paths), never spoof a pass.
            shutil.copytree(ctx.task.reference_dir, ctx.workspace, dirs_exist_ok=True)

        # Plausible-but-fake usage so reports have something to aggregate; cost is
        # always 0 - the mock never touches a paid API.
        usage = Usage(
            input_tokens=1000 + (1 if success else 0) * 500,
            output_tokens=200 + (1 if success else 0) * 300,
            cost_usd=0.0,
            num_turns=2 if success else 1,
        )
        detail = f"mock draw={draw:.3f} < p={prob:.3f} -> {'solve' if success else 'no-op'}"
        return AgentRunInfo(usage=usage, detail=detail)


__all__ = ["MockAgent"]
