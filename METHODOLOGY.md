# Methodology

cc-bench exists to answer one question honestly: **did a way of using a coding
agent change the task success rate, and by how much, with what uncertainty?**
This document explains how it measures that and, just as importantly, where it
can be wrong.

## What is measured

- **Unit of observation:** one *run* = one `(condition, task, repetition)`. Each
  run gets a fresh, isolated workspace (a copy of the task template), so no run
  can see another run's edits.
- **Success:** the task's own `verify_cmd` is executed in the workspace; exit
  code `0` is a PASS. There is no LLM judge and no fuzzy matching, so the signal
  is reproducible and a human can re-run the exact command. This mirrors the
  execution-based grading of SWE-bench (see `EVIDENCE.md` [2]).
- **Outcome accounting (4-way):** `PASS`, `FAIL`, `TIMEOUT`, `ERROR`.
  - The pass-rate **denominator** is `PASS + FAIL + TIMEOUT` ("decided" runs).
  - `ERROR` (the harness or agent could not run at all) is **excluded** from the
    denominator - a misconfiguration must not count against the agent - but is
    always reported.
  - `TIMEOUT` counts as not-solved: an agent too slow to finish did not solve the
    task.

## Statistics

### Per-condition rate - Wilson score interval
A condition's pass rate is a binomial proportion. cc-bench reports a **Wilson
score interval**, which stays well-calibrated at the small sample sizes typical
of agent benchmarks, unlike the normal (Wald) approximation (degenerate near 0/1
and at small n) or a naive bootstrap of a proportion.

### Difference vs baseline - two levels of claim

Runs cluster by task: an agent is often near-deterministic on a given task, so
10 reps of one task carry far less evidence than 10 independent tasks. Pooling
all reps into one binomial (what most eval tools do, and what cc-bench itself
did before its own adversarial review) can turn ONE deterministic task flip
into p < 0.001 - a number that reads as a general claim while the evidence is
"one task out of three". cc-bench therefore separates two claims:

**Level 1 - did it help on THIS suite?**
- Statistic: the unweighted **mean per-task difference** in pass rate.
- p-value: a **stratified permutation test** - condition labels are shuffled
  WITHIN each task, so task difficulty and run-to-run clustering cannot fake an
  effect. Exact under exchangeability, robust at small n.
- CI: a **within-task bootstrap** (tasks fixed, runs resampled per task), i.e.
  the uncertainty of the effect on these tasks.
- Verdict `improvement`/`regression` requires the CI to exclude 0 **and** the
  (Holm-adjusted) permutation p below `alpha = 1 - confidence`; else `not proven`.

**Level 2 - does it generalize beyond this suite?**
- Unit of evidence: the **task** (improved / regressed / tied).
- An exact **sign test** on task flips. With 3-4 tasks this is almost never
  significant - and that is the honest answer: few tasks cannot establish a
  general claim, no matter how many reps you run. The report says so and points
  to `ccbench from-git` to grow the task set.

The legacy pooled comparison (`compare`: binomial bootstrap + two-proportion
z-test) remains in the library for single-task data and cross-run comparisons.

### Multiple comparisons
Testing several variants against one baseline inflates the family-wise false-
positive rate. cc-bench corrects the variant p-values with **Holm-Bonferroni**
(default, controls FWER) or **Benjamini-Hochberg** (FDR). Both raw and adjusted
p-values are shown; significance uses the adjusted one. Testing more variants
therefore makes each one *harder* to call a win - the honest cost of asking more
questions of the same data.

### Reproducibility
Every run is parameterised by a `seed`. The mock agent is a pure function of
`(seed, task, condition, rep)` (SHA-256 -> uniform), so the same command yields
the same results, and parallelism (when added) cannot perturb them. Results are
saved as JSONL with the metadata needed to reproduce them.

### Controls
`conditions/placebo-claude-md.yaml` is a **negative control**: a CLAUDE.md of
similar length whose content is generic and task-irrelevant. Interpretation:
- treatment beats baseline AND placebo does not -> the effect comes from the
  content of the guidance, not the mere presence of a file;
- a placebo that "wins" is a red flag for a broken experiment (harness bias,
  contamination, too little data).
Run it alongside your real conditions; it costs one extra arm and buys a lot of
credibility.

## Self-validation: the calibration test

A measurement tool is only trustworthy if it is itself tested. `tests/
test_calibration.py` runs a seeded Monte Carlo over the analysis pipeline and
asserts:
1. **Power** - when a real effect exists (p = 0.45 vs 0.75), the pipeline calls
   it significant the large majority of the time at n ~ 80.
2. **Calibration** - under the null (equal p), the false-positive rate stays near
   the nominal level.
3. **Monotonicity** - power increases with sample size.

If a change silently breaks the statistics, these bounds fail in CI. This is the
guard behind every "improvement" cc-bench reports.

## Threats to validity (read this before trusting a number)

- **Statistical power / small n.** A 3-task suite at 5 reps has very wide
  intervals. cc-bench surfaces the interval and the n precisely so you do not
  over-read noise. Add tasks and reps to resolve smaller effects.
- **Pooling across tasks.** Found by our own adversarial review and fixed: the
  headline verdict is now task-stratified (permutation within task + per-task
  effects + a task-level sign test for generalization) instead of pooling
  `task x rep` runs as iid. The per-condition Wilson table still shows the
  pooled run-level rate; read it as descriptive, not inferential.
- **Agent nondeterminism.** Real agents are stochastic; that variance is exactly
  what the reps + CIs are meant to capture, but it also means small suites can
  swing run to run. Use enough reps.
- **Task contamination.** Public tasks may be in a model's training data,
  inflating pass rates (a known SWE-bench issue, `EVIDENCE.md` [3]). Prefer
  private or freshly authored tasks for absolute claims; for *relative*
  comparisons under identical tasks, contamination largely cancels.
- **White-box tests.** In the *sample* suite the agent can see the test file
  (a deliberate choice for a fast, cheap demo). For real measurement use
  **held-out tests** (`hidden_tests_dir`, as in `suites/hard/`): grading tests are
  copied in only after the agent finishes, so it cannot read or overfit them.
- **The mock proves the method, not the agent.** Mock numbers use injected
  ground-truth probabilities and are labelled `SIMULATED` in every report. They
  demonstrate the harness can *detect* an effect of a given size; they say
  nothing about a real agent. Use `--agent claude` (or another adapter) for real
  measurements.
- **Generality of findings.** A result on one suite/model/version may not
  transfer. Re-run on your own tasks; that is the entire point of the tool.
