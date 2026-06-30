# cc-bench

**Does your Claude Code setup actually help?** A reproducible, evidence-based
benchmark harness for coding agents.

> Status: **alpha, under active construction.** The mock pipeline runs end-to-end
> today (zero API cost); the real `claude` adapter and the cited evidence base are
> landing milestone by milestone — see the commit history for the reasoning behind
> each step.

## The problem

There is a lot of *folklore* about how to use a coding agent well: "write a
`CLAUDE.md`", "use plan mode", "keep the context small", "add a linter hook". Most
of it is plausible. Almost none of it is **measured** on your own tasks. So you
can't tell whether a tweak helped, hurt, or did nothing but burn tokens.

cc-bench turns "I think this helps" into "this changed the pass rate from X% to Y%
(95% CI ...), n=Z".

## How it works

Three orthogonal pieces:

- **Tasks** — small, self-contained coding problems. Each task is *broken code +
  a test that fails*. Success = the test passes after the agent works. Pass/fail
  is deterministic; no LLM judge.
- **Conditions** — declarative descriptions of *how* the agent is invoked
  (baseline vs. "a `CLAUDE.md` is present", "plan first", a different context
  budget, ...). A condition is data, not code.
- **Runner** — for every `(task x condition x repetition)` it creates an isolated
  workspace, invokes the agent, runs the task's check, and records the outcome
  plus turns/tokens/cost/wall-time.

Then **analysis** estimates a per-condition pass rate with a **bootstrap
confidence interval** and does pairwise comparisons, and **report** renders
Markdown/CSV.

A deterministic **mock agent** lets the whole pipeline (and CI) run with zero API
cost, so the harness itself is testable. Real runs use the `claude` CLI in
headless mode and bring your own auth.

## Why "evidence-based"

Every actionable recommendation cc-bench ships with must trace to a citation in
[`EVIDENCE.md`](EVIDENCE.md) (benchmark methodology, long-context research, agent
scaffolding studies). Claims that can't be backed by a source don't ship.

## Honesty about limits

Small task suites mean wide confidence intervals. cc-bench reports the interval
and the sample size precisely *so you don't over-read a noisy difference*. See
[`METHODOLOGY.md`](METHODOLOGY.md) for the statistical choices and the threats to
validity (task contamination, agent nondeterminism, multiple-comparison risk).

## Quickstart (mock, no cost)

```bash
pip install -e .
ccbench run --suite suites/sample --conditions conditions/ --agent mock --reps 5
ccbench report runs/latest
```

## License

MIT - see [LICENSE](LICENSE).
