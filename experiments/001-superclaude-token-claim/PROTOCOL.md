# Experiment 001 (pre-registered): does SuperClaude's token claim hold?

Status: **pre-registered, not yet run.** This protocol is committed BEFORE any
data is collected; results will be published whatever direction they point,
including "SuperClaude wins" or "not proven". Deviations from this protocol will
be listed in a Deviations section of the results.

## Claim under test

SuperClaude_Framework (20k+ stars) advertises a large token reduction
("30-50%"). Public reviewers note the number is hard to verify. This experiment
measures it with cc-bench on real tasks.

- H1 (their claim): output tokens per solved task drop by 30-50% with
  SuperClaude installed, at no cost in success rate.
- H0: no meaningful token reduction, or a success-rate cost.

## Design

- Arms: `baseline` (vanilla Claude Code) vs `superclaude` (framework installed
  per its README, defaults untouched).
- Model held fixed: `--model haiku` for both arms; same seeds; same tasks.
- Tasks: the bundled `suites/hard` (4 held-out tasks) plus `from-git` tasks
  generated from 2 public repos (listed in the results doc when run).
- Grading: execution-only, held-out tests, `--sandbox docker` when available.
- Reps: 5 per task per arm per repo bloc (concrete n stated below).

## Endpoints

1. **Primary: output tokens per solved task** (continuous; mean ratio
   superclaude/baseline with a bootstrap CI over runs). This is the claim's own
   metric and is well powered at modest n for a 30-50% effect.
2. **Guard: config lift (success rate)**, task-stratified as everywhere in
   cc-bench. SuperClaude must not significantly REDUCE success.

## Power (declared before running)

Normal-approximation floors from `ccbench power` (per arm, decided runs):

- detect a 20pp success drop from 60%: 97 runs per arm
- detect a 15pp success drop from 60%: 173 runs per arm

Planned n is 60-80 runs per arm (budget bound), so the guard endpoint can only
detect success changes of roughly 20-25pp; smaller success effects will honestly
report as "not proven". The primary token endpoint does not have this problem: a
30-50% shift on a continuous metric is detectable at this n.

## Budget

At the observed ~$0.08-0.15 quota-equivalent per haiku run on `suites/hard`,
120-160 total runs cost roughly $10-25 of subscription quota. No API billing.

## Analysis commands (verbatim)

```bash
ccbench run --suite suites/hard --conditions experiments/001-superclaude-token-claim/conditions \
            --agent claude --model haiku --reps 5 --seeds 0,1,2 --out runs/exp001
ccbench report runs/exp001/latest --html exp001.html
```

Token analysis: mean output_tokens over PASS runs per arm from results.jsonl,
percentile-bootstrap CI (script committed with the results).

## Publication rule

The write-up leads with the measured ratio and its CI, states the guard verdict,
links this pre-registration, and includes the exact reproduce commands. Negative
or inconvenient results are published identically.
