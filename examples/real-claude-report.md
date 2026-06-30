# Real measured run - Claude (haiku-4.5)

This is a **real** cc-bench run against the live `claude` CLI (model
`claude-haiku-4-5`), not the mock. It cost about **$0.86** in API usage across
**12 runs** (2 conditions x 3 tasks x 2 reps) on 2026-06-30.

**Result: both conditions reached 100% -> "not proven".** That is the honest,
correct outcome, and a useful lesson: the sample tasks (fizzbuzz, parse_version,
dedup) are trivial for a real model, so it solves them with or without a
`CLAUDE.md` - there is simply no room to show a difference (a *ceiling effect*).

It demonstrates two things that matter:
1. the `claude` adapter runs end-to-end and records **real** tokens/cost, and
2. cc-bench **refuses to claim "CLAUDE.md helps"** when the data does not support
   it - exactly the anti-hype behaviour the tool is built for.

To actually reveal a configuration effect you need *harder* tasks where the
baseline pass rate sits well below 100% (see the roadmap: SWE-bench-style suites).
The raw report follows.

---

# cc-bench report - suite `sample`

- Agent: `claude` | Conditions: 2 | Seed: 0 | Total runs: 12
- Generated: 2026-06-30T19:24:36+00:00

## Pass rate by condition (95% Wilson CI)

| Condition | Pass rate | 95% CI | pass/decided | timeouts | errors | mean tok in/out | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 100.0% | [61.0%, 100.0%] | 6/6 | 0 | 0 | 53/2107 | $0.0667 |
| `with-claude-md` | 100.0% | [61.0%, 100.0%] | 6/6 | 0 | 0 | 66/2715 | $0.0772 |

## Change vs baseline `baseline`

| Condition | delta pass rate | 95% CI (bootstrap) | p (raw) | p (holm) | verdict |
|---|---:|---:|---:|---:|:--|
| `with-claude-md` | +0.0% | [+0.0%, +0.0%] | 1.0000 | 1.0000 | [~] not proven |

_Verdict is `improvement`/`regression` only when the difference CI excludes 0 **and** the holm-adjusted p < 0.05. Otherwise `not proven` - usually meaning the effect (if any) is smaller than this sample size can resolve: add reps. p-values are corrected for testing 1 variant(s) against one baseline._

## pass@k by condition

| Condition | pass@1 | pass@2 |
|---|---:|---:|
| `baseline` | 100.0% | 100.0% |
| `with-claude-md` | 100.0% | 100.0% |

_pass@k = unbiased estimator (Chen et al. 2021): chance that at least one of k samples passes, averaged over tasks. '-' = fewer than k reps for some task._

## Conditions tested

- **`baseline`** - Default invocation, no CLAUDE.md injected. The control everything else is measured against.
  - Rationale: Control condition - all comparisons are relative to this.
- **`with-claude-md`** - A short, focused CLAUDE.md is present in the agent's workspace.
  - Rationale: Anthropic's guidance is to keep CLAUDE.md short (<200 lines) because long files consume context and reduce instruction adherence; a concise, task-relevant CLAUDE.md is hypothesised to raise the pass rate.
  - Evidence: EVIDENCE.md > Claude Code usage: CLAUDE.md under 200 lines, Liu et al. 2023, Lost in the Middle
