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

from .analysis import (
    adjust_pvalues, compare, compare_all, distinct_seeds, pass_at_k_mean,
    robustness, summarize_condition,
)
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
    correction: str = "holm",
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

    # Comparisons vs baseline (with multiple-comparison correction)
    lines.append(f"## Change vs baseline `{base}`")
    lines.append("")
    lines.append(
        f"| Condition | delta pass rate | {pct}% CI (bootstrap) | p (raw) | p ({correction}) | verdict |"
    )
    lines.append("|---|---:|---:|---:|---:|:--|")
    base_results = suite_run.for_condition(base)
    variants = [(name, suite_run.for_condition(name)) for name in suite_run.conditions if name != base]
    comps = compare_all(
        base, base_results, variants,
        confidence=confidence, bootstrap_iters=bootstrap_iters, seed=seed, correction=correction,
    )
    for cmp in comps:
        mark = {"improvement": "[+] improvement", "regression": "[-] regression",
                "not proven": "[~] not proven"}[cmp.verdict]
        padj = cmp.p_adjusted if cmp.p_adjusted is not None else cmp.p_value
        lines.append(
            f"| `{cmp.variant}` | {cmp.diff:+.1%} | [{cmp.diff_ci_low:+.1%}, {cmp.diff_ci_high:+.1%}] | "
            f"{cmp.p_value:.4f} | {padj:.4f} | {mark} |"
        )
    lines.append("")
    lines.append(
        "_Verdict is `improvement`/`regression` only when the difference CI excludes 0 "
        f"**and** the {correction}-adjusted p < {1 - confidence:.2f}. Otherwise `not proven` - "
        "usually meaning the effect (if any) is smaller than this sample size can resolve: "
        f"add reps. p-values are corrected for testing {len(variants)} variant(s) against one "
        "baseline._"
    )
    lines.append("")

    # pass@k by condition (only the k that are estimable for every task)
    k_values = [1, 2, 5]
    cols = [k for k in k_values
            if any(pass_at_k_mean(suite_run.for_condition(n), k) is not None
                   for n in suite_run.conditions)]
    if cols:
        lines.append("## pass@k by condition")
        lines.append("")
        lines.append("| Condition | " + " | ".join(f"pass@{k}" for k in cols) + " |")
        lines.append("|---|" + "---:|" * len(cols))
        for name in suite_run.conditions:
            cells = []
            for k in cols:
                v = pass_at_k_mean(suite_run.for_condition(name), k)
                cells.append(f"{v:.1%}" if v is not None else "-")
            lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
        lines.append("")
        lines.append(
            "_pass@k = unbiased estimator (Chen et al. 2021): chance that at least one "
            "of k samples passes, averaged over tasks. '-' = fewer than k reps for some task._"
        )
        lines.append("")

    # Robustness across seeds (only when the run used more than one seed)
    if len(distinct_seeds(suite_run.results)) >= 2:
        lines.append("## Robustness across seeds")
        lines.append("")
        lines.append("| Condition | seeds | mean pass rate | SD | min..max |")
        lines.append("|---|---:|---:|---:|---:|")
        for name in suite_run.conditions:
            rb = robustness(suite_run.for_condition(name), name)
            if rb is None:
                continue
            lines.append(
                f"| `{name}` | {rb.n_seeds} | {rb.mean:.1%} | {rb.sd:.1%} | "
                f"{rb.rate_min:.1%}..{rb.rate_max:.1%} |"
            )
        lines.append("")
        lines.append(
            "_Lower SD = more reproducible. A high SD means a single run's headline rate is "
            "partly luck - add reps/seeds before trusting it._"
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


def render_run_comparison(
    run_a: SuiteRun,
    run_b: SuiteRun,
    label_a: str = "A",
    label_b: str = "B",
    confidence: float = 0.95,
    bootstrap_iters: int = 5000,
    seed: int = 0,
    correction: str = "holm",
) -> str:
    """Compare two saved runs (e.g. claude vs codex, or before vs after a change).

    Reports overall and per-shared-condition differences with the same honest
    two-gate verdict, p-values corrected across the rows. Loudly flags the cases
    that would make the comparison misleading (different suites; a mock run).
    """
    pct = int(round(confidence * 100))
    alpha = 1.0 - confidence
    rows: list[tuple[str, list[RunResult], list[RunResult]]] = [
        ("overall", list(run_a.results), list(run_b.results))
    ]
    shared = [c for c in run_a.conditions if c in set(run_b.conditions)]
    for c in shared:
        rows.append((c, run_a.for_condition(c), run_b.for_condition(c)))

    comps = [compare(a, b, label_a, label_b, confidence=confidence,
                     bootstrap_iters=bootstrap_iters, seed=seed) for _, a, b in rows]
    adj = adjust_pvalues([c.p_value for c in comps], correction)

    lines = [f"# cc-bench - {label_a} vs {label_b}", ""]
    lines.append(f"- {label_a}: suite=`{run_a.suite}` agent=`{run_a.agent}` n={len(run_a.results)}")
    lines.append(f"- {label_b}: suite=`{run_b.suite}` agent=`{run_b.agent}` n={len(run_b.results)}")
    lines.append("")
    if run_a.suite != run_b.suite:
        lines.append("> **Warning:** the two runs use different suites - this is not an "
                     "apples-to-apples comparison.\n")
    if run_a.agent == "mock" or run_b.agent == "mock":
        lines.append("> **Note:** a `mock` run uses injected probabilities; it demonstrates the "
                     "harness, it is not a real measurement.\n")

    lines.append(f"| Scope | {label_a} | {label_b} | delta ({label_b}-{label_a}) | "
                 f"{pct}% CI | p ({correction}) | verdict |")
    lines.append("|---|---:|---:|---:|---:|---:|:--|")
    for (scope, _, _), c, padj in zip(rows, comps, adj):
        ci_excludes_zero = c.diff_ci_low > 0 or c.diff_ci_high < 0
        sig = ci_excludes_zero and padj < alpha
        if sig and c.diff > 0:
            verdict = f"[+] {label_b} better"
        elif sig and c.diff < 0:
            verdict = f"[-] {label_a} better"
        else:
            verdict = "[~] not proven"
        lines.append(
            f"| {scope} | {c.rate_baseline:.1%} | {c.rate_variant:.1%} | {c.diff:+.1%} | "
            f"[{c.diff_ci_low:+.1%}, {c.diff_ci_high:+.1%}] | {padj:.4f} | {verdict} |"
        )
    lines.append("")
    lines.append(f"_delta is {label_b} minus {label_a}; a winner is declared only when the CI "
                 f"excludes 0 **and** the {correction}-adjusted p < {alpha:.2f}._")
    return "\n".join(lines)


__all__ = ["render_markdown", "render_csv", "render_run_comparison"]
