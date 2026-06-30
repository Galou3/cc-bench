"""Render a SuiteRun into a human-facing Markdown report (and a CSV).

The report is the artifact people actually read, so it carries the project's
honesty rules into the output:

- If the run used the ``mock`` agent, a loud banner states the numbers are a
  capability demo of the harness, not a claim about any real agent. This is the
  single most important line in the whole tool - it is what stops a reader from
  mistaking a simulated effect for a measured one.
- Every comparison shows the confidence interval and the n, and labels a result
  "not proven" unless it is genuinely significant, so a noisy difference can't be
  read as a win.
- Each condition's rationale/citation is printed, keeping the evidence trail
  visible from EVIDENCE.md all the way to the result.
"""

from __future__ import annotations

import csv
import io
from typing import Sequence

from .analysis import compare, summarize_condition
from .models import Condition, RunResult, SuiteRun

_MOCK_BANNER = (
    "> **SIMULATED RUN (agent = `mock`).** These numbers use injected "
    "ground-truth probabilities; they demonstrate that the harness *detects* an "
    "effect of this size at this sample size - they are NOT a measurement of any "
    "real agent. Re-run with `--agent claude` for real results.\n"
)


def _pick_baseline(suite_run: SuiteRun, baseline: str | None) -> str:
    names = list(suite_run.conditions)
    if baseline:
        if baseline not in names:
            raise ValueError(f"baseline '{baseline}' not among conditions: {names}")
        return baseline
    if "baseline" in names:
        return "baseline"
    return names[0] if names else ""


def _mean_usage(results: Sequence[RunResult]) -> tuple[float, float, float, float]:
    n = len(results)
    if not n:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        sum(r.usage.input_tokens for r in results) / n,
        sum(r.usage.output_tokens for r in results) / n,
        sum(r.usage.cost_usd for r in results) / n,
        sum(r.usage.num_turns for r in results) / n,
    )


def render_markdown(
    suite_run: SuiteRun,
    conditions: Sequence[Condition] | None = None,
    baseline: str | None = None,
    confidence: float = 0.95,
    bootstrap_iters: int = 5000,
    seed: int = 0,
) -> str:
    """Render a full Markdown report. ``conditions`` (optional) adds rationale/citations."""
    pct = int(round(confidence * 100))
    cond_by_name = {c.name: c for c in (conditions or [])}
    base = _pick_baseline(suite_run, baseline)
    lines: list[str] = []

    lines.append(f"# cc-bench report - suite `{suite_run.suite}`")
    lines.append("")
    lines.append(
        f"- Agent: `{suite_run.agent}` | Conditions: {len(suite_run.conditions)} | "
        f"Seed: {suite_run.seed} | Total runs: {len(suite_run.results)}"
    )
    lines.append(f"- Generated: {suite_run.created_utc}")
    lines.append("")
    if suite_run.agent == "mock":
        lines.append(_MOCK_BANNER)
        lines.append("")

    # Per-condition rates
    lines.append(f"## Pass rate by condition ({pct}% Wilson CI)")
    lines.append("")
    lines.append(
        "| Condition | Pass rate | "
        f"{pct}% CI | pass/decided | timeouts | errors | mean tok in/out | mean cost |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name in suite_run.conditions:
        rs = summarize_condition(suite_run.for_condition(name), name, confidence)
        it, ot, cost, _ = _mean_usage(suite_run.for_condition(name))
        lines.append(
            f"| `{name}` | {rs.rate:.1%} | [{rs.ci_low:.1%}, {rs.ci_high:.1%}] | "
            f"{rs.counts.passes}/{rs.counts.decided} | {rs.counts.timeouts} | "
            f"{rs.counts.errors} | {it:.0f}/{ot:.0f} | ${cost:.4f} |"
        )
    lines.append("")

    # Comparisons vs baseline
    lines.append(f"## Change vs baseline `{base}`")
    lines.append("")
    lines.append(f"| Condition | delta pass rate | {pct}% CI (bootstrap) | p-value | verdict |")
    lines.append("|---|---:|---:|---:|:--|")
    base_results = suite_run.for_condition(base)
    for name in suite_run.conditions:
        if name == base:
            continue
        cmp = compare(
            base_results, suite_run.for_condition(name), base, name,
            confidence=confidence, bootstrap_iters=bootstrap_iters, seed=seed,
        )
        mark = {"improvement": "[+] improvement", "regression": "[-] regression",
                "not proven": "[~] not proven"}[cmp.verdict]
        lines.append(
            f"| `{name}` | {cmp.diff:+.1%} | [{cmp.diff_ci_low:+.1%}, {cmp.diff_ci_high:+.1%}] | "
            f"{cmp.p_value:.4f} | {mark} |"
        )
    lines.append("")
    lines.append(
        "_Verdict is `improvement`/`regression` only when the difference CI excludes 0 "
        "**and** p < " + f"{1 - confidence:.2f}. Otherwise `not proven` - usually meaning "
        "the effect (if any) is smaller than this sample size can resolve: add reps._"
    )
    lines.append("")

    # Conditions tested (rationale + evidence)
    if cond_by_name:
        lines.append("## Conditions tested")
        lines.append("")
        for name in suite_run.conditions:
            c = cond_by_name.get(name)
            if not c:
                continue
            desc = c.description or "(no description)"
            lines.append(f"- **`{name}`** - {desc}")
            if c.rationale:
                lines.append(f"  - Rationale: {c.rationale}")
            if c.citation:
                lines.append(f"  - Evidence: {', '.join(c.citation)}")
        lines.append("")

    return "\n".join(lines)


def render_csv(suite_run: SuiteRun, confidence: float = 0.95) -> str:
    """One row per condition: counts, rate, CI, mean usage. For spreadsheets/plots."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "condition", "passes", "fails", "timeouts", "errors", "decided",
        "rate", "ci_low", "ci_high", "mean_in_tok", "mean_out_tok",
        "mean_cost_usd", "mean_turns",
    ])
    for name in suite_run.conditions:
        results = suite_run.for_condition(name)
        rs = summarize_condition(results, name, confidence)
        it, ot, cost, turns = _mean_usage(results)
        w.writerow([
            name, rs.counts.passes, rs.counts.fails, rs.counts.timeouts,
            rs.counts.errors, rs.counts.decided, f"{rs.rate:.6f}",
            f"{rs.ci_low:.6f}", f"{rs.ci_high:.6f}", f"{it:.2f}", f"{ot:.2f}",
            f"{cost:.6f}", f"{turns:.2f}",
        ])
    return buf.getvalue()


__all__ = ["render_markdown", "render_csv"]
