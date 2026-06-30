"""A deterministic mock agent - the harness's test instrument.

The mock has no intelligence. Given a condition's *ground-truth* success
probability (``condition.metadata['mock_success_prob']``), it succeeds or fails
according to a hash of the experiment coordinates ``(seed, task, condition, rep)``.

Two reasons this matters more than it looks:

1. **Zero cost, fully reproducible.** CI can run the whole pipeline with no API
   calls, and the same seed always yields the same results.
2. **It makes "improvement" provable.** Because we *inject* a known effect (say
   baseline p=0.45 vs. a condition p=0.75), we can check that the analysis
   recovers a significant difference when one truly exists and, crucially, does
   NOT manufacture one when both conditions share the same p. That calibration is
   what licenses us to trust the same analysis on real ``claude`` runs.

On a simulated success the mock copies the held-out reference solution into the
workspace so the real grader (``verify.run_check``) passes for real - we never
fake the PASS, we make the code actually correct.
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
            # Make the code genuinely correct rather than spoofing a pass.
            for f in Path(ctx.task.reference_dir).iterdir():
                if f.is_file():
                    shutil.copy(f, Path(ctx.workspace) / f.name)

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
