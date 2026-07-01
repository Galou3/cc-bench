"""Orchestrate a benchmark sweep (condition x task x rep) and persist results."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from .agents.base import Agent, RunContext
from .models import Condition, RunResult, SuiteRun
from .suite import load_suite
from .verify import run_check
from .workspace import add_files, apply_condition, prepare_workspace, restore_protected_files

ProgressFn = Callable[[int, int, RunResult], None]


def run_suite(
    suite_dir: str | Path,
    conditions: Sequence[Condition],
    agent: Agent,
    *,
    reps: int = 5,
    seed: int = 0,
    keep_workspaces: str | Path | None = None,
    progress: ProgressFn | None = None,
    sandbox: str = "none",
    sandbox_image: str = "python:3.12-slim",
    sandbox_network: str = "none",
) -> SuiteRun:
    """Run every ``(condition, task, rep)`` and return a SuiteRun.

    ``keep_workspaces``: if a directory is given, each run's workspace is kept
    under it (useful for debugging a failure); otherwise workspaces are temporary
    and removed after grading.
    """
    name, tasks = load_suite(suite_dir)
    total = len(conditions) * len(tasks) * reps
    results: list[RunResult] = []
    done = 0
    keep_root = Path(keep_workspaces) if keep_workspaces else None

    for cond in conditions:
        for task in tasks:
            for rep in range(reps):
                if keep_root is not None:
                    ws = keep_root / cond.name / task.id / f"rep{rep}"
                    ws.mkdir(parents=True, exist_ok=True)
                    tmp_holder = None
                else:
                    tmp_holder = tempfile.mkdtemp(prefix="ccbench_")
                    ws = Path(tmp_holder)
                try:
                    prepare_workspace(task, ws)
                    apply_condition(ws, cond)
                    ctx = RunContext(task=task, condition=cond, workspace=ws, rep=rep, seed=seed)
                    t0 = time.perf_counter()
                    info = agent.run(ctx)
                    # Post-agent, pre-grading: restore the template's test files
                    # (an agent must not grade against tests it rewrote), then
                    # overlay held-out tests the agent never saw.
                    restore_protected_files(task.template_dir, ws)
                    if task.hidden_tests_dir:
                        add_files(ws, task.hidden_tests_dir)
                    outcome, verify_detail = run_check(
                        task, ws, sandbox=sandbox, sandbox_image=sandbox_image,
                        sandbox_network=sandbox_network)
                    wall = time.perf_counter() - t0
                finally:
                    if tmp_holder is not None:
                        shutil.rmtree(tmp_holder, ignore_errors=True)

                detail = verify_detail or info.detail
                rr = RunResult(
                    task_id=task.id, condition=cond.name, rep=rep, outcome=outcome,
                    usage=info.usage, wall_time_s=wall, agent=agent.name, seed=seed,
                    detail=detail,
                )
                results.append(rr)
                done += 1
                if progress is not None:
                    progress(done, total, rr)

    return SuiteRun(
        suite=name,
        agent=agent.name,
        conditions=tuple(c.name for c in conditions),
        results=tuple(results),
        seed=seed,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def run_suite_seeds(
    suite_dir: str | Path,
    conditions: Sequence[Condition],
    agent: Agent,
    *,
    reps: int = 5,
    seeds: Sequence[int] = (0,),
    keep_workspaces: str | Path | None = None,
    progress: ProgressFn | None = None,
    sandbox: str = "none",
    sandbox_image: str = "python:3.12-slim",
    sandbox_network: str = "none",
) -> SuiteRun:
    """Run the suite once per seed and merge the results into one SuiteRun.

    Each RunResult keeps its own seed, so downstream robustness analysis can
    measure how much the pass rate moves from seed to seed. SuiteRun.seed is left
    None to signal a multi-seed run.
    """
    all_results: list[RunResult] = []
    suite_name = ""
    for s in seeds:
        run = run_suite(suite_dir, conditions, agent, reps=reps, seed=s,
                        keep_workspaces=keep_workspaces, progress=progress,
                        sandbox=sandbox, sandbox_image=sandbox_image,
                        sandbox_network=sandbox_network)
        suite_name = run.suite
        all_results.extend(run.results)
    return SuiteRun(
        suite=suite_name,
        agent=agent.name,
        conditions=tuple(c.name for c in conditions),
        results=tuple(all_results),
        seed=None,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def save_run(suite_run: SuiteRun, runs_root: str | Path = "runs") -> Path:
    """Write the run to ``runs/<timestamp>/`` and mirror it to ``runs/latest/``.

    Mirroring (a plain copy, not a symlink) keeps ``ccbench report runs/latest``
    working on Windows where symlinks need elevated rights.
    """
    runs_root = Path(runs_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = runs_root / stamp
    _write_run(suite_run, out_dir)
    _write_run(suite_run, runs_root / "latest")
    return out_dir


def _write_run(suite_run: SuiteRun, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "suite": suite_run.suite,
        "agent": suite_run.agent,
        "conditions": list(suite_run.conditions),
        "seed": suite_run.seed,
        "created_utc": suite_run.created_utc,
        "n_results": len(suite_run.results),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as fh:
        for r in suite_run.results:
            fh.write(json.dumps(r.to_dict()) + "\n")


def load_run(run_dir: str | Path) -> SuiteRun:
    """Reconstruct a SuiteRun from a directory written by ``save_run``."""
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    results = []
    with (run_dir / "results.jsonl").open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                results.append(RunResult.from_dict(json.loads(line)))
    return SuiteRun(
        suite=meta["suite"],
        agent=meta["agent"],
        conditions=tuple(meta.get("conditions", ())),
        results=tuple(results),
        seed=meta.get("seed"),
        created_utc=meta.get("created_utc", ""),
    )


__all__ = ["run_suite", "run_suite_seeds", "save_run", "load_run", "ProgressFn"]
