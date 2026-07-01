"""Render a SuiteRun as a single self-contained shareable HTML file."""

from __future__ import annotations

import html
from typing import Sequence

from . import __version__
from .analysis import compare_all_stratified, summarize_condition
from .models import Condition, SuiteRun

_CSS = """
body{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 max-width:880px;margin:2rem auto;padding:0 1rem;color:#1f2328;background:#fff}
h1{font-size:1.5rem;margin-bottom:.2rem} h2{font-size:1.15rem;margin-top:1.6rem}
.meta{color:#57606a;font-size:.9rem}
.banner{background:#fff8c5;border:1px solid #d4a72c;border-radius:6px;
 padding:.7rem 1rem;margin:1rem 0;font-size:.92rem}
table{border-collapse:collapse;width:100%;margin:.6rem 0;font-size:.92rem}
th,td{border:1px solid #d0d7de;padding:.45rem .6rem;text-align:left}
th{background:#f6f8fa} td.num{text-align:right;font-variant-numeric:tabular-nums}
.bar{background:#eaeef2;border-radius:4px;height:12px;position:relative;min-width:120px}
.bar>span{display:block;height:12px;border-radius:4px;background:#0969da}
.chip{display:inline-block;padding:.1rem .55rem;border-radius:999px;
 font-size:.85rem;font-weight:600;color:#fff}
.win{background:#2da44e}.lose{background:#cf222e}.na{background:#57606a}
.foot{color:#57606a;font-size:.85rem;margin-top:2rem;border-top:1px solid #d0d7de;
 padding-top:.8rem}
code{background:#f6f8fa;padding:.1rem .3rem;border-radius:4px;font-size:.88em}
"""

_CHIP = {"improvement": ("win", "improvement"),
         "regression": ("lose", "regression"),
         "not proven": ("na", "not proven")}


def render_html(
    suite_run: SuiteRun,
    conditions: Sequence[Condition] | None = None,
    baseline: str | None = None,
    confidence: float = 0.95,
    iters: int = 5000,
    seed: int = 0,
    correction: str = "holm",
) -> str:
    pct = int(round(confidence * 100))
    esc = html.escape
    names = list(suite_run.conditions)
    base = baseline or ("baseline" if "baseline" in names else (names[0] if names else ""))

    out: list[str] = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append(f"<title>cc-bench report - {esc(suite_run.suite)}</title>")
    out.append(f"<style>{_CSS}</style></head><body>")
    out.append(f"<h1>cc-bench report - <code>{esc(suite_run.suite)}</code></h1>")
    out.append(f"<p class='meta'>agent <code>{esc(suite_run.agent)}</code> | "
               f"{len(names)} conditions | {len(suite_run.results)} runs | "
               f"seed {esc(str(suite_run.seed))} | {esc(suite_run.created_utc)}</p>")
    if suite_run.agent == "mock":
        out.append("<div class='banner'><b>SIMULATED RUN (agent = mock).</b> "
                   "Numbers use injected ground-truth probabilities: they demonstrate "
                   "the harness, they are not a measurement of any real agent.</div>")

    out.append(f"<h2>Pass rate by condition ({pct}% Wilson CI)</h2><table>")
    out.append("<tr><th>Condition</th><th>Pass rate</th><th>CI</th><th>Rate</th>"
               "<th>pass/decided</th></tr>")
    for name in names:
        rs = summarize_condition(suite_run.for_condition(name), name, confidence)
        out.append(
            f"<tr><td><code>{esc(name)}</code></td>"
            f"<td class='num'>{rs.rate:.1%}</td>"
            f"<td class='num'>[{rs.ci_low:.1%}, {rs.ci_high:.1%}]</td>"
            f"<td><div class='bar'><span style='width:{rs.rate * 100:.1f}%'></span></div></td>"
            f"<td class='num'>{rs.counts.passes}/{rs.counts.decided}</td></tr>")
    out.append("</table>")

    variants = [(n, suite_run.for_condition(n)) for n in names if n != base]
    if base and variants:
        comps = compare_all_stratified(base, suite_run.for_condition(base), variants,
                                       confidence=confidence, iters=iters, seed=seed,
                                       correction=correction)
        out.append(f"<h2>Change vs <code>{esc(base)}</code> (on this task suite)</h2><table>")
        out.append(f"<tr><th>Condition</th><th>mean delta/task</th><th>{pct}% CI</th>"
                   f"<th>p (perm, {esc(correction)})</th><th>tasks +/=/-</th>"
                   "<th>verdict</th></tr>")
        for c in comps:
            cls, label = _CHIP[c.verdict]
            out.append(
                f"<tr><td><code>{esc(c.variant)}</code></td>"
                f"<td class='num'>{c.mean_diff:+.1%}</td>"
                f"<td class='num'>[{c.ci_low:+.1%}, {c.ci_high:+.1%}]</td>"
                f"<td class='num'>{c.effective_p:.4f}</td>"
                f"<td class='num'>{c.tasks_improved}/{c.tasks_tied}/{c.tasks_regressed}</td>"
                f"<td><span class='chip {cls}'>{label}</span></td></tr>")
        out.append("</table>")
        out.append("<h2>Does it generalize beyond this suite?</h2><ul>")
        for c in comps:
            if c.sign_p < 1 - confidence:
                note = f"likely (sign p = {c.sign_p:.3f})"
            else:
                note = (f"not proven (sign p = {c.sign_p:.2f}) - add tasks with "
                        "<code>ccbench from-git</code>")
            out.append(f"<li><code>{esc(c.variant)}</code>: {c.tasks_improved} improved / "
                       f"{c.tasks_regressed} regressed / {c.tasks_tied} tied "
                       f"across {len(c.tasks)} task(s) - {note}</li>")
        out.append("</ul>")

    out.append(f"<p class='foot'>Generated by <a href='https://github.com/Galou3/cc-bench'>"
               f"cc-bench</a> v{__version__}. Verdicts require the CI to exclude 0 AND the "
               f"{esc(correction)}-adjusted within-task permutation p &lt; "
               f"{1 - confidence:.2f}. Reproduce with the same suite, conditions and seed.</p>")
    out.append("</body></html>")
    return "".join(out)


__all__ = ["render_html"]
