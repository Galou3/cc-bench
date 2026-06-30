# cc-bench report - suite `sample`

- Agent: `mock` | Conditions: 3 | Seed: 0 | Total runs: 270
- Generated: 2026-06-30T18:35:06+00:00

> **SIMULATED RUN (agent = `mock`).** These numbers use injected ground-truth probabilities; they demonstrate that the harness *detects* an effect of this size at this sample size - they are NOT a measurement of any real agent. Re-run with `--agent claude` for real results.


## Pass rate by condition (95% Wilson CI)

| Condition | Pass rate | 95% CI | pass/decided | timeouts | errors | mean tok in/out | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 34.4% | [25.4%, 44.7%] | 31/90 | 0 | 0 | 1172/303 | $0.0000 |
| `bloated-context` | 21.1% | [14.0%, 30.6%] | 19/90 | 0 | 0 | 1106/263 | $0.0000 |
| `with-claude-md` | 64.4% | [54.2%, 73.6%] | 58/90 | 0 | 0 | 1322/393 | $0.0000 |

## Change vs baseline `baseline`

| Condition | delta pass rate | 95% CI (bootstrap) | p (raw) | p (holm) | verdict |
|---|---:|---:|---:|---:|:--|
| `bloated-context` | -13.3% | [-26.7%, +0.0%] | 0.0458 | 0.0458 | [~] not proven |
| `with-claude-md` | +30.0% | [+15.6%, +43.3%] | 0.0001 | 0.0001 | [+] improvement |

_Verdict is `improvement`/`regression` only when the difference CI excludes 0 **and** the holm-adjusted p < 0.05. Otherwise `not proven` - usually meaning the effect (if any) is smaller than this sample size can resolve: add reps. p-values are corrected for testing 2 variant(s) against one baseline._

## pass@k by condition

| Condition | pass@1 | pass@2 | pass@5 |
|---|---:|---:|---:|
| `baseline` | 34.4% | 57.7% | 89.8% |
| `bloated-context` | 21.1% | 37.1% | 66.5% |
| `with-claude-md` | 64.4% | 86.9% | 99.4% |

_pass@k = unbiased estimator (Chen et al. 2021): chance that at least one of k samples passes, averaged over tasks. '-' = fewer than k reps for some task._

## Conditions tested

- **`baseline`** - Default invocation, no CLAUDE.md injected. The control everything else is measured against.
  - Rationale: Control condition - all comparisons are relative to this.
- **`bloated-context`** - A long, mostly-irrelevant CLAUDE.md that pads the context window.
  - Rationale: Long-context research (lost-in-the-middle, context rot) predicts that padding the prompt with topically-plausible but task-irrelevant content degrades performance, and that the harm grows with input length. This condition tests whether bloating CLAUDE.md hurts the pass rate.

  - Evidence: EVIDENCE.md > Long-context behavior: context rot, Levy et al. 2024; Chroma Context Rot 2025
- **`with-claude-md`** - A short, focused CLAUDE.md is present in the agent's workspace.
  - Rationale: Anthropic's guidance is to keep CLAUDE.md short (<200 lines) because long files consume context and reduce instruction adherence; a concise, task-relevant CLAUDE.md is hypothesised to raise the pass rate.

  - Evidence: EVIDENCE.md > Claude Code usage: CLAUDE.md under 200 lines, Liu et al. 2023, Lost in the Middle
