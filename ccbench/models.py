"""Typed, immutable value objects shared across cc-bench (no I/O, no clock)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Outcome(str, Enum):
    """Why a run ended; str base so it JSON-serialises as its value."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class Task:
    """A self-contained coding problem with a deterministic check.

    ``template_dir`` holds *broken* code (relative to the suite root). The runner
    copies it into an isolated workspace, lets the agent edit it, then runs
    ``verify_cmd`` inside that workspace: exit code 0 means the task passed. No
    LLM judge is involved, so the success signal is reproducible.
    """

    id: str
    prompt: str
    template_dir: str
    verify_cmd: list[str]
    # Held-out reference solution. NEVER copied into the agent's workspace; the
    # mock agent reads it to simulate a solved state, real adapters ignore it.
    reference_dir: str | None = None
    # Held-out tests. Copied into the workspace ONLY at grading time, after the
    # agent has finished, so the agent cannot read or overfit them. This is what
    # makes a "hard" task hard (cf. SWE-bench's FAIL_TO_PASS held-out tests) and
    # keeps the pass rate off the 100% ceiling.
    hidden_tests_dir: str | None = None
    timeout_s: int = 300
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        return cls(
            id=str(d["id"]),
            prompt=str(d["prompt"]),
            template_dir=str(d["template_dir"]),
            verify_cmd=list(d["verify_cmd"]),
            reference_dir=d.get("reference_dir"),
            hidden_tests_dir=d.get("hidden_tests_dir"),
            timeout_s=int(d.get("timeout_s", 300)),
            tags=tuple(d.get("tags", ())),
        )


@dataclass(frozen=True, slots=True)
class Condition:
    """A *way of using* the agent, expressed as data.

    A condition is the independent variable of an experiment. It can drop extra
    files into the workspace before the agent starts (``inject_files`` maps a
    workspace-relative path to literal content - e.g. a ``CLAUDE.md``) and pass
    extra knobs to the agent adapter (``agent_args``).

    ``rationale``/``citation`` are not decoration: cc-bench's contract is that
    every condition worth testing maps to something in EVIDENCE.md, so the
    citation travels with the condition and ends up in the report.
    """

    name: str
    description: str = ""
    inject_files: dict[str, str] = field(default_factory=dict)
    agent_args: tuple[str, ...] = ()
    rationale: str = ""
    citation: tuple[str, ...] = ()
    # Free-form annotations. Real adapters ignore it; the mock agent reads
    # ``mock_success_prob`` here to inject a known ground-truth effect, which is
    # what lets the calibration test prove the analysis detects real differences.
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Condition":
        return cls(
            name=str(d["name"]),
            description=str(d.get("description", "")),
            inject_files=dict(d.get("inject_files", {})),
            agent_args=tuple(d.get("agent_args", ())),
            rationale=str(d.get("rationale", "")),
            citation=tuple(d.get("citation", ())),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class Usage:
    """Resource cost of a run. Additive so a suite total is just a ``sum``."""

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    num_turns: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        if not isinstance(other, Usage):
            return NotImplemented
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cost_usd + other.cost_usd,
            self.num_turns + other.num_turns,
        )

    __radd__ = __add__  # so sum(usages, Usage()) works

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "num_turns": self.num_turns,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Usage":
        return cls(
            input_tokens=int(d.get("input_tokens", 0)),
            output_tokens=int(d.get("output_tokens", 0)),
            cost_usd=float(d.get("cost_usd", 0.0)),
            num_turns=int(d.get("num_turns", 0)),
        )


@dataclass(frozen=True, slots=True)
class RunResult:
    """The record of one ``(task, condition, rep)`` execution."""

    task_id: str
    condition: str
    rep: int
    outcome: Outcome
    usage: Usage
    wall_time_s: float
    agent: str = "mock"
    seed: int | None = None
    detail: str = ""  # tail of verify output, or the error message on ERROR

    @property
    def passed(self) -> bool:
        return self.outcome is Outcome.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "condition": self.condition,
            "rep": self.rep,
            "outcome": self.outcome.value,
            "usage": self.usage.to_dict(),
            "wall_time_s": self.wall_time_s,
            "agent": self.agent,
            "seed": self.seed,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RunResult":
        return cls(
            task_id=str(d["task_id"]),
            condition=str(d["condition"]),
            rep=int(d["rep"]),
            outcome=Outcome(d["outcome"]),
            usage=Usage.from_dict(d.get("usage", {})),
            wall_time_s=float(d["wall_time_s"]),
            agent=str(d.get("agent", "mock")),
            seed=d.get("seed"),
            detail=str(d.get("detail", "")),
        )


@dataclass(frozen=True, slots=True)
class SuiteRun:
    """All results of one experiment plus the metadata needed to reproduce it."""

    suite: str
    agent: str
    conditions: tuple[str, ...]
    results: tuple[RunResult, ...]
    seed: int | None = None
    created_utc: str = ""  # ISO-8601, stamped by the caller (models stay clock-free)

    def for_condition(self, name: str) -> list[RunResult]:
        return [r for r in self.results if r.condition == name]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "agent": self.agent,
            "conditions": list(self.conditions),
            "seed": self.seed,
            "created_utc": self.created_utc,
            "results": [r.to_dict() for r in self.results],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SuiteRun":
        return cls(
            suite=str(d["suite"]),
            agent=str(d["agent"]),
            conditions=tuple(d.get("conditions", ())),
            results=tuple(RunResult.from_dict(r) for r in d.get("results", ())),
            seed=d.get("seed"),
            created_utc=str(d.get("created_utc", "")),
        )


__all__ = ["Outcome", "Task", "Condition", "Usage", "RunResult", "SuiteRun"]
