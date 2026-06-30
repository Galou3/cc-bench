# Real measured run - Claude (haiku-4.5) on the HARD suite

A **real** `--agent claude` run (model `claude-haiku-4-5`) on `suites/hard`, whose
tests are **held out** from the agent. 16 runs (2 conditions x 4 tasks x 2 reps),
~**$2.01** of subscription usage, on 2026-06-30.

## What this run taught us (the honest version)

1. **The hard suite left the 100% ceiling** - `baseline` came in at **87.5%**, not
   100%. The held-out-tests mechanism works end-to-end against a real agent. That
   was the goal of building this suite.

2. **The single "failure" was a grader bug, not the agent.** On
   `baseline/merge_intervals` the agent's solution actually *passed* the held-out
   tests, but it had also written its **own** throwaway test file in the workspace,
   and that file errored at collection - so plain `pytest` (which collects
   everything in the workspace) failed the run. **Fix:** for held-out-test tasks,
   `verify_cmd` now targets only the hidden test file, so agent-authored tests
   can't pollute grading. With that fix, all 16 solutions pass.

3. **Honest conclusion:** at this model/difficulty there is **no measurable config
   effect** (`+12.5%`, p = 0.30 -> *not proven*), and once the grader artifact is
   removed both conditions are effectively at ceiling again. To surface a real
   "this setup helps/hurts" result you need **harder tasks** (or a weaker model)
   **and many more reps** - not folklore. cc-bench refusing to claim a win here is
   the feature working as intended.

> This report is kept as-is (pre-fix) for transparency - it's a real debugging
> story. The raw numbers follow.

---

# cc-bench report - suite `hard`

- Agent: `claude` | Conditions: 2 | Seed: 0 | Total runs: 16
- Generated: 2026-06-30T20:13:27+00:00

## Pass rate by condition (95% Wilson CI)

| Condition | Pass rate | 95% CI | pass/decided | timeouts | errors | mean tok in/out | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 87.5% | [52.9%, 97.8%] | 7/8 | 0 | 0 | 68/8644 | $0.1238 |
| `with-claude-md` | 100.0% | [67.6%, 100.0%] | 8/8 | 0 | 0 | 82/7918 | $0.1270 |

## Change vs baseline `baseline`

| Condition | delta pass rate | 95% CI (bootstrap) | p (raw) | p (holm) | verdict |
|---|---:|---:|---:|---:|:--|
| `with-claude-md` | +12.5% | [+0.0%, +37.5%] | 0.3017 | 0.3017 | [~] not proven |

_The +12.5% is one flipped run out of eight per condition; the CI touches 0 and p = 0.30, so the honest verdict is "not proven". And that single flip was the grader artifact described above._

## pass@k by condition

| Condition | pass@1 | pass@2 |
|---|---:|---:|
| `baseline` | 87.5% | 100.0% |
| `with-claude-md` | 100.0% | 100.0% |
