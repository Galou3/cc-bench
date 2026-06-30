"""Command-line interface: ``ccbench run`` and ``ccbench report``.

Thin on purpose - it parses args, builds an agent, calls the library, and prints.
All the logic lives in importable modules so cc-bench is equally usable as a
library (or from a pytest, or a GitHub Action) and not only as a CLI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .agents import available_agents, make_agent
from .analysis import compare, summarize_condition
from .report import render_csv, render_markdown
from .runner import load_run, run_suite, save_run
from .suite import SuiteError, load_conditions


def _build_agent(args: argparse.Namespace):
    if args.agent == "mock":
        return make_agent("mock", base_prob=args.mock_base_prob)
    opts = {
        "permission_mode": args.permission_mode,
        "allowed_tools": args.allowed_tools,
    }
    if args.model:
        opts["model"] = args.model
    return make_agent("claude", **opts)


def _progress(done: int, total: int, rr) -> None:
    end = "\n" if done == total else "\r"
    print(f"  [{done:>4}/{total}] last: {rr.condition}/{rr.task_id} "
          f"rep{rr.rep} -> {rr.outcome.value}      ", end=end, flush=True)


def _print_summary(run, confidence: float) -> None:
    base = "baseline" if "baseline" in run.conditions else (run.conditions[0] if run.conditions else "")
    print(f"\nResults (suite={run.suite}, agent={run.agent}, n={len(run.results)}):")
    for name in run.conditions:
        rs = summarize_condition(run.for_condition(name), name, confidence)
        print(f"  {name:20} {rs.rate:6.1%}  CI[{rs.ci_low:.1%}, {rs.ci_high:.1%}]  "
              f"({rs.counts.passes}/{rs.counts.decided})")
    if base:
        print(f"\nvs baseline `{base}`:")
        for name in run.conditions:
            if name == base:
                continue
            c = compare(run.for_condition(base), run.for_condition(name), base, name,
                        confidence=confidence)
            print(f"  {name:20} {c.diff:+6.1%}  p={c.p_value:.4f}  -> {c.verdict}")


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        conditions = load_conditions(args.conditions)
    except SuiteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    agent = _build_agent(args)
    print(f"Running suite '{args.suite}' x {len(conditions)} conditions x {args.reps} reps "
          f"with agent '{agent.name}'...")
    run = run_suite(
        args.suite, conditions, agent,
        reps=args.reps, seed=args.seed,
        keep_workspaces=args.keep_workspaces, progress=_progress,
    )
    out_dir = save_run(run, args.out)
    _print_summary(run, args.confidence)
    print(f"\nSaved to {out_dir}  (mirror: {Path(args.out) / 'latest'})")
    if args.report:
        print("\n" + "=" * 70 + "\n")
        print(render_markdown(run, conditions, baseline=args.baseline,
                              confidence=args.confidence))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    conditions = None
    if args.conditions:
        conditions = load_conditions(args.conditions)
    md = render_markdown(run, conditions, baseline=args.baseline, confidence=args.confidence)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(md)
    if args.csv:
        Path(args.csv).write_text(render_csv(run, args.confidence), encoding="utf-8")
        print(f"wrote {args.csv}")
    return 0


def _cmd_agents(_args: argparse.Namespace) -> int:
    print("available agents: " + ", ".join(available_agents()))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ccbench", description="Measure whether your coding-agent setup actually helps.")
    p.add_argument("--version", action="version", version=f"cc-bench {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a suite across conditions")
    r.add_argument("--suite", required=True, help="path to a suite directory (with tasks.yaml)")
    r.add_argument("--conditions", required=True, help="conditions YAML file or directory")
    r.add_argument("--agent", default="mock", choices=available_agents())
    r.add_argument("--reps", type=int, default=5)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--out", default="runs", help="runs root directory")
    r.add_argument("--confidence", type=float, default=0.95)
    r.add_argument("--baseline", default=None, help="baseline condition name (default: 'baseline' or first)")
    r.add_argument("--report", action="store_true", help="print the full Markdown report after running")
    r.add_argument("--keep-workspaces", default=None, help="keep run workspaces under this dir (debug)")
    r.add_argument("--mock-base-prob", type=float, default=0.5, help="mock fallback success probability")
    r.add_argument("--model", default=None, help="model for the claude agent")
    r.add_argument("--permission-mode", default="acceptEdits", help="claude --permission-mode")
    r.add_argument("--allowed-tools", default="Edit,Write,Read", help="claude --allowedTools")
    r.set_defaults(func=_cmd_run)

    rep = sub.add_parser("report", help="render a Markdown/CSV report from a saved run")
    rep.add_argument("run_dir", help="a runs/<timestamp> or runs/latest directory")
    rep.add_argument("--conditions", default=None, help="conditions YAML (adds rationale/citations)")
    rep.add_argument("--baseline", default=None)
    rep.add_argument("--confidence", type=float, default=0.95)
    rep.add_argument("--out", default=None, help="write Markdown here instead of stdout")
    rep.add_argument("--csv", default=None, help="also write a per-condition CSV here")
    rep.set_defaults(func=_cmd_report)

    ag = sub.add_parser("agents", help="list available agents")
    ag.set_defaults(func=_cmd_agents)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
