"""Command-line interface for cc-bench (run / report / compare / doctor / init)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .agents import available_agents, make_agent
from .analysis import compare_all_stratified, distinct_seeds, robustness, summarize_condition
from .doctor import apply_fixes, audit, health_score, render as render_doctor, summary as doctor_summary
from .fromrepo import add_task_to_suite, make_task
from .fromgit import make_task_from_commit
from .report import render_csv, render_markdown, render_run_comparison
from .runner import load_run, run_suite, run_suite_seeds, save_run
from .scaffold import next_steps, scaffold
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


def _print_summary(run, confidence: float, correction: str = "holm") -> None:
    base = "baseline" if "baseline" in run.conditions else (run.conditions[0] if run.conditions else "")
    print(f"\nResults (suite={run.suite}, agent={run.agent}, n={len(run.results)}):")
    for name in run.conditions:
        rs = summarize_condition(run.for_condition(name), name, confidence)
        print(f"  {name:20} {rs.rate:6.1%}  CI[{rs.ci_low:.1%}, {rs.ci_high:.1%}]  "
              f"({rs.counts.passes}/{rs.counts.decided})")
    if base:
        variants = [(n, run.for_condition(n)) for n in run.conditions if n != base]
        comps = compare_all_stratified(base, run.for_condition(base), variants,
                                       confidence=confidence, correction=correction)
        print(f"\nvs baseline `{base}` (stratified by task; perm p, {correction}-adjusted):")
        for c in comps:
            gen = "generalizes: likely" if c.sign_p < 1 - confidence else "generalizes: not proven"
            print(f"  {c.variant:20} {c.mean_diff:+6.1%}/task  p={c.effective_p:.4f}  "
                  f"tasks +{c.tasks_improved}/={c.tasks_tied}/-{c.tasks_regressed}  "
                  f"-> {c.verdict} on this suite ({gen})")
    seeds = distinct_seeds(run.results)
    if len(seeds) >= 2:
        print(f"\nrobustness across {len(seeds)} seeds (mean +/- SD):")
        for name in run.conditions:
            rb = robustness(run.for_condition(name), name)
            if rb:
                print(f"  {name:20} {rb.mean:6.1%} +/- {rb.sd:.1%}  "
                      f"(min..max {rb.rate_min:.0%}..{rb.rate_max:.0%})")


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        conditions = load_conditions(args.conditions)
    except SuiteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    agent = _build_agent(args)
    print(f"Running suite '{args.suite}' x {len(conditions)} conditions x {args.reps} reps "
          f"with agent '{agent.name}'...")
    sbox = dict(sandbox=args.sandbox, sandbox_image=args.sandbox_image,
                sandbox_network=args.sandbox_network)
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip() != ""]
        run = run_suite_seeds(
            args.suite, conditions, agent,
            reps=args.reps, seeds=seeds,
            keep_workspaces=args.keep_workspaces, progress=_progress, **sbox,
        )
    else:
        run = run_suite(
            args.suite, conditions, agent,
            reps=args.reps, seed=args.seed,
            keep_workspaces=args.keep_workspaces, progress=_progress, **sbox,
        )
    out_dir = save_run(run, args.out)
    _print_summary(run, args.confidence, args.correction)
    print(f"\nSaved to {out_dir}  (mirror: {Path(args.out) / 'latest'})")
    if args.report:
        print("\n" + "=" * 70 + "\n")
        print(render_markdown(run, conditions, baseline=args.baseline,
                              confidence=args.confidence, correction=args.correction))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    conditions = None
    if args.conditions:
        conditions = load_conditions(args.conditions)
    md = render_markdown(run, conditions, baseline=args.baseline,
                         confidence=args.confidence, correction=args.correction)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(md)
    if args.csv:
        Path(args.csv).write_text(render_csv(run, args.confidence), encoding="utf-8")
        print(f"wrote {args.csv}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    run_a = load_run(args.run_a)
    run_b = load_run(args.run_b)
    md = render_run_comparison(run_a, run_b, args.label_a, args.label_b,
                               confidence=args.confidence, correction=args.correction)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(md)
    return 0


def _cmd_agents(_args: argparse.Namespace) -> int:
    print("available agents: " + ", ".join(available_agents()))
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    created, skipped = scaffold(args.dir)
    for c in created:
        print(f"  created {c}")
    for s in skipped:
        print(f"  skipped {s} (exists)")
    if not created:
        print("nothing to create - starter files already present.")
    else:
        print("\n" + next_steps())
    return 0


def _cmd_from_repo(args: argparse.Namespace) -> int:
    entry = make_task(args.module, args.test, args.out, args.id, prompt=args.prompt)
    add_task_to_suite(args.out, entry, args.suite_name)
    print(f"created held-out task '{args.id}' in suite {args.out}")
    print(f"  try: ccbench run --suite {args.out} --conditions conditions --agent mock --reps 5")
    return 0


def _cmd_from_git(args: argparse.Namespace) -> int:
    entry = make_task_from_commit(args.repo, args.commit, args.out, args.id, prompt=args.prompt)
    add_task_to_suite(args.out, entry, args.suite_name)
    print(f"created held-out task '{args.id}' from commit {args.commit[:8]} in {args.out}")
    print(f"  try: ccbench run --suite {args.out} --conditions conditions --agent mock --reps 5")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    findings = audit(args.dir)
    if args.fix:
        actions = apply_fixes(args.dir, findings)
        for a in actions:
            print(f"  fixed: {a}")
        if actions:
            findings = audit(args.dir)  # re-audit so the report reflects the fixes
    if args.json:
        print(json.dumps({"score": health_score(findings),
                          "summary": doctor_summary(findings),
                          "findings": [f.to_dict() for f in findings]}, indent=2))
    else:
        print(render_doctor(findings, args.dir))
    return 1 if doctor_summary(findings)["fail"] else 0


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
    r.add_argument("--seeds", default=None,
                   help="comma-separated seeds for a multi-seed robustness run (overrides --seed)")
    r.add_argument("--out", default="runs", help="runs root directory")
    r.add_argument("--confidence", type=float, default=0.95)
    r.add_argument("--correction", default="holm", choices=["none", "holm", "bh", "fdr"],
                   help="multiple-comparison correction for variant p-values")
    r.add_argument("--baseline", default=None, help="baseline condition name (default: 'baseline' or first)")
    r.add_argument("--report", action="store_true", help="print the full Markdown report after running")
    r.add_argument("--keep-workspaces", default=None, help="keep run workspaces under this dir (debug)")
    r.add_argument("--mock-base-prob", type=float, default=0.5, help="mock fallback success probability")
    r.add_argument("--sandbox", default="none", choices=["none", "docker"],
                   help="run grading inside a sandbox (docker: isolated, no network)")
    r.add_argument("--sandbox-image", default="python:3.12-slim")
    r.add_argument("--sandbox-network", default="none", help="docker --network value (default: none)")
    r.add_argument("--model", default=None, help="model for the claude agent")
    r.add_argument("--permission-mode", default="acceptEdits", help="claude --permission-mode")
    r.add_argument("--allowed-tools", default="Edit,Write,Read", help="claude --allowedTools")
    r.set_defaults(func=_cmd_run)

    rep = sub.add_parser("report", help="render a Markdown/CSV report from a saved run")
    rep.add_argument("run_dir", help="a runs/<timestamp> or runs/latest directory")
    rep.add_argument("--conditions", default=None, help="conditions YAML (adds rationale/citations)")
    rep.add_argument("--baseline", default=None)
    rep.add_argument("--confidence", type=float, default=0.95)
    rep.add_argument("--correction", default="holm", choices=["none", "holm", "bh", "fdr"],
                     help="multiple-comparison correction for variant p-values")
    rep.add_argument("--out", default=None, help="write Markdown here instead of stdout")
    rep.add_argument("--csv", default=None, help="also write a per-condition CSV here")
    rep.set_defaults(func=_cmd_report)

    cmp = sub.add_parser("compare", help="compare two saved runs (e.g. claude vs codex)")
    cmp.add_argument("run_a", help="first run dir (the reference)")
    cmp.add_argument("run_b", help="second run dir")
    cmp.add_argument("--label-a", default="A")
    cmp.add_argument("--label-b", default="B")
    cmp.add_argument("--confidence", type=float, default=0.95)
    cmp.add_argument("--correction", default="holm", choices=["none", "holm", "bh", "fdr"])
    cmp.add_argument("--out", default=None, help="write Markdown here instead of stdout")
    cmp.set_defaults(func=_cmd_compare)

    ag = sub.add_parser("agents", help="list available agents")
    ag.set_defaults(func=_cmd_agents)

    ini = sub.add_parser("init", help="scaffold a runnable starter suite + conditions")
    ini.add_argument("--dir", default=".", help="directory to scaffold into (default: cwd)")
    ini.set_defaults(func=_cmd_init)

    fr = sub.add_parser("from-repo", help="turn your own tested module into a held-out task")
    fr.add_argument("--module", required=True, help="path to the source module to benchmark")
    fr.add_argument("--test", required=True, help="path to its test file (held out at grading)")
    fr.add_argument("--id", required=True, help="task id")
    fr.add_argument("--out", default="ccbench_suite", help="suite directory to create/update")
    fr.add_argument("--suite-name", default="from-repo")
    fr.add_argument("--prompt", default=None)
    fr.set_defaults(func=_cmd_from_repo)

    fg = sub.add_parser("from-git", help="build a held-out task from a repo's git commit")
    fg.add_argument("--repo", default=".", help="path to the git repo")
    fg.add_argument("--commit", required=True, help="a commit that changed source AND tests")
    fg.add_argument("--id", required=True, help="task id")
    fg.add_argument("--out", default="ccbench_suite", help="suite directory to create/update")
    fg.add_argument("--suite-name", default="from-git")
    fg.add_argument("--prompt", default=None)
    fg.set_defaults(func=_cmd_from_git)

    doc = sub.add_parser("doctor", help="audit a Claude Code setup against the evidence")
    doc.add_argument("--dir", default=".", help="project root to audit (default: cwd)")
    doc.add_argument("--fix", action="store_true", help="apply safe auto-fixes (e.g. add a starter CLAUDE.md)")
    doc.add_argument("--json", action="store_true", help="emit findings as JSON")
    doc.set_defaults(func=_cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
