# cc-bench report - suite `sample`

- Agent: `mock` | Conditions: 4 | Seed: 0 | Total runs: 360
- Generated: 2026-07-01T21:06:46+00:00

> **SIMULATED RUN (agent = `mock`).** These numbers use injected ground-truth probabilities; they demonstrate that the harness *detects* an effect of this size at this sample size - they are NOT a measurement of any real agent. Re-run with `--agent claude` for real results.


## Pass rate by condition (95% Wilson CI)

| Condition | Pass rate | 95% CI | pass/decided | timeouts | errors | mean tok in/out | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 34.4% | [25.4%, 44.7%] | 31/90 | 0 | 0 | 1172/303 | $0.0000 |
| `bloated-context` | 21.1% | [14.0%, 30.6%] | 19/90 | 0 | 0 | 1106/263 | $0.0000 |
| `placebo-claude-md` | 38.9% | [29.5%, 49.2%] | 35/90 | 0 | 0 | 1194/317 | $0.0000 |
| `with-claude-md` | 64.4% | [54.2%, 73.6%] | 58/90 | 0 | 0 | 1322/393 | $0.0000 |

## Change vs baseline `baseline` (on this task suite)

| Condition | mean per-task delta | 95% CI | p (perm, holm) | tasks +/=/- | verdict |
|---|---:|---:|---:|:---:|:--|
| `bloated-context` | -13.3% | [-25.6%, -0.0%] | 0.1352 | 1/0/2 | [~] not proven |
| `placebo-claude-md` | +4.4% | [-10.0%, +18.9%] | 0.6409 | 2/0/1 | [~] not proven |
| `with-claude-md` | +30.0% | [+15.6%, +44.4%] | 0.0012 | 3/0/0 | [+] improvement |

_Suite-level verdict: `improvement`/`regression` only when the CI excludes 0 **and** the holm-adjusted permutation p < 0.05. The permutation shuffles condition labels WITHIN each task, so task difficulty and run-to-run clustering cannot fake an effect. This verdict applies to THESE tasks._

**Does it generalize beyond this suite?** (task-level sign test)

- `bloated-context`: 1 improved / 2 regressed / 0 tied across 3 task(s) -> not proven (sign p = 1.00) - add tasks (`ccbench from-git`) to test generalization
- `placebo-claude-md`: 2 improved / 1 regressed / 0 tied across 3 task(s) -> not proven (sign p = 1.00) - add tasks (`ccbench from-git`) to test generalization
- `with-claude-md`: 3 improved / 0 regressed / 0 tied across 3 task(s) -> not proven (sign p = 0.25) - add tasks (`ccbench from-git`) to test generalization

## pass@k by condition

| Condition | pass@1 | pass@2 | pass@5 |
|---|---:|---:|---:|
| `baseline` | 34.4% | 57.7% | 89.8% |
| `bloated-context` | 21.1% | 37.1% | 66.5% |
| `placebo-claude-md` | 38.9% | 63.0% | 92.2% |
| `with-claude-md` | 64.4% | 86.9% | 99.4% |

_pass@k = unbiased estimator (Chen et al. 2021): chance that at least one of k samples passes, averaged over tasks. '-' = fewer than k reps for some task._

## Conditions tested

- **`baseline`** - Default invocation, no CLAUDE.md injected. The control everything else is measured against.
  - Rationale: Control condition - all comparisons are relative to this.
- **`bloated-context`** - A long, mostly-irrelevant CLAUDE.md that pads the context window.
  - Rationale: Long-context research (lost-in-the-middle, context rot) predicts that padding the prompt with topically-plausible but task-irrelevant content degrades performance, and that the harm grows with input length. This condition tests whether bloating CLAUDE.md hurts the pass rate.

  - Evidence: EVIDENCE.md > Long-context behavior: context rot, Levy et al. 2024; Chroma Context Rot 2025
- **`placebo-claude-md`** - Negative control - a CLAUDE.md of similar length whose content is generic and task-irrelevant.
  - Rationale: Placebo arm. If with-claude-md beats baseline but this placebo does not, the effect comes from the CONTENT of the guidance, not from the mere presence of a CLAUDE.md file. Standard control-arm logic applied to agent configs; also a built-in check against harness bias (a placebo that "wins" would reveal a broken experiment).

  - Evidence: METHODOLOGY.md > Controls
- **`with-claude-md`** - A short, focused CLAUDE.md is present in the agent's workspace.
  - Rationale: Anthropic's guidance is to keep CLAUDE.md short (<200 lines) because long files consume context and reduce instruction adherence; a concise, task-relevant CLAUDE.md is hypothesised to raise the pass rate.

  - Evidence: EVIDENCE.md > Claude Code usage: CLAUDE.md under 200 lines, Liu et al. 2023, Lost in the Middle
