# Prior art & positioning

cc-bench is not the first tool near this space. This is an honest map of the
neighbours, where they are stronger, and the specific gap cc-bench fills. (Built
from an automated survey of 50+ tools; corrections welcome via PR.)

## Two arenas

The space splits in two, and cc-bench is deliberately weak in one and strong in
the other.

### Arena A: static setup audit / lint (this is `doctor`, and we are outgunned)

These read your `CLAUDE.md` / `AGENTS.md` / settings and flag issues. They never
run the agent.

- **agnix**: ~432 rules, an LSP with live diagnostics in several IDEs, tiered
  autofix, multi-assistant. The strongest linter by far.
- **claudelint** (pdugan20): ~114 rules across CLAUDE.md, skills, settings, hooks,
  MCP, plugins; auto-fix.
- **AgentLint**: 33 evidence-cited checks, a 0-100 score, HTML report. The closest
  philosophy to `doctor`, and it states plainly that it "measures harness health,
  not agent success rates". That sentence is cc-bench's opening.
- **cclint** (several variants), **AgentLinter**: schema validation, per-finding
  token-cost, GitHub Action / MCP packaging.

`ccbench doctor` has ~13 checks plus a 0-100 score. It is the on-ramp, not the
product, and it carries one thing the linters do not: every finding cites
EVIDENCE.md and points at a way to *prove* it.

### Arena B: measure whether a change actually helps (this is the wedge)

These run the agent and score outcomes. Almost none do it for a *config change* on
*your* tasks, free, with real statistics.

- **jchilcher/claude-benchmark**: purpose-built to benchmark a CLAUDE.md, but no
  reps, no confidence intervals, no significance test, Claude-only.
- **Anthropic skill-creator 2.0**: first-party blind A/B for Skills with held-out
  splits, but LLM-judge winner reports (no CIs / p / multiplicity), Claude-only,
  scoped to skills not the harness.
- **Braintrust**: real significance testing + CIs, but config-agnostic and paid
  hosted SaaS.
- **UK AISI Inspect**: serious, plugs in Claude Code AND Codex with epochs and
  clustered SE, but build-it-yourself, not a turnkey config A/B, no audit/fix.
- **promptfoo / Aider / SWE-bench / Terminal-Bench**: breadth and task realism we
  cannot match, but single pass rates, no config-A/B significance, not auditors.

### Arena C: optimizers (friends, not rivals)

DSPy, GEPA, MIPROv2, Arize Prompt Learning, CodexOpt: they *generate* a better
config. None ship a significance verdict. Natural pairing: optimize with them,
then certify the gain with cc-bench.

## The wedge

cc-bench is the only tool that closes the loop **audit -> fix -> prove** in one
free, local CLI:

- inferential statistics as the verdict on a config change (Wilson + bootstrap CIs,
  two-proportion z-test, Holm/BH, an honest "not proven" default);
- execution-only grading (success = the task's real tests pass), no LLM-judge noise;
- the unit is *your* config on *your* (possibly private) repo, for Claude AND Codex;
- calibration-tested stats plus an EVIDENCE.md base of 40 cited sources.

## Where the others are stronger (honestly)

- Linters: far more rules, LSP / IDE diagnostics, richer autofix.
- Benchmarks: thousands of realistic tasks, sandboxed execution, polished reports.
- Optimizers: they actually improve a config; cc-bench only measures one.

See [ROADMAP.md](ROADMAP.md) for the gaps we are closing (distribution, a flagship
real-agent result, more checks, broader suites).
