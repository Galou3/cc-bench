# Prior art & positioning

cc-bench is not the first tool to evaluate coding agents. This page maps the
neighbours, says honestly where they are stronger, and explains the specific gap
cc-bench fills. (Landscape informed by an automated survey; corrections welcome
via PR — see a tool we mischaracterised? open an issue.)

## The landscape

**Agentic coding benchmarks & harnesses** — large, realistic task sets:
- [SWE-bench](https://github.com/SWE-bench/SWE-bench) / SWE-bench Verified — real
  GitHub issues; the field standard. Heavy per-task environments and Docker.
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) and
  [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) — agent scaffolds
  with their own evaluation paths.
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) evaluation,
  [moatless-tools](https://github.com/aorwall/moatless-tools) — agent platforms
  with eval harnesses.
- [Aider polyglot benchmark](https://aider.chat/docs/leaderboards/),
  [LiveCodeBench](https://livecodebench.github.io/),
  [BigCodeBench](https://github.com/bigcode-project/bigcodebench),
  [EvalPlus](https://github.com/evalplus/evalplus) (HumanEval+/MBPP+),
  [Terminal-Bench](https://www.tbench.ai/) — code/agent leaderboards.

**General eval frameworks** — flexible, mature, broad:
- [OpenAI Evals](https://github.com/openai/evals),
  [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness),
  [Inspect](https://inspect.aisi.org.uk/) (UK AISI),
  [promptfoo](https://github.com/promptfoo/promptfoo),
  [DeepEval](https://github.com/confident-ai/deepeval),
  [HELM](https://github.com/stanford-crfm/helm),
  [Langfuse](https://github.com/langfuse/langfuse),
  [Braintrust](https://www.braintrust.dev/).

**Prompt/program optimisers** — they *change* the prompt, not just measure it:
- [DSPy](https://github.com/stanfordnlp/dspy),
  [GEPA](https://github.com/gepa-ai/gepa), Arize prompt-learning.

**On statistical rigour in evals** — the motivation for cc-bench's stats:
- Anthropic, [*Adding Error Bars to Evals*](https://www.anthropic.com/research/statistical-approach-to-model-evals).
- [*The Leaderboard Illusion*](https://arxiv.org/abs/2504.20879) — how leaderboards mislead.
- Chatbot Arena / [LMArena](https://lmarena.ai/) — reports Bradley-Terry bootstrap CIs.

## Common mistakes cc-bench avoids

1. **Point estimates with no uncertainty.** Many leaderboards rank by a single
   number; small gaps are noise. cc-bench always reports a CI and only declares a
   winner when the difference CI excludes 0 *and* the corrected p clears α.
2. **Measuring the model, not your usage.** The above tools compare *models/
   agents*. None make it cheap to A/B *how you configure one agent* (a `CLAUDE.md`,
   plan mode) on *your* tasks. That is cc-bench's unit of analysis.
3. **No multiplicity control.** Comparing many variants inflates false positives;
   cc-bench corrects (Holm/BH) by default.
4. **Heavy setup / cost as a barrier.** Docker-per-task and large deps deter
   casual use. cc-bench is stdlib + PyYAML, and a deterministic mock runs the full
   pipeline offline for free (great for CI).
5. **LLM-as-judge noise.** cc-bench grades by executing the task's own tests —
   reproducible, auditable, no judge variance.
6. **Contamination treated as someone else's problem.** Public benchmarks leak
   into training data. cc-bench is built for *your* (possibly private) tasks; for
   relative comparisons under identical tasks, contamination largely cancels.

## Where the others are stronger (honestly)

- **Task realism & scale:** SWE-bench/Terminal-Bench offer thousands of real,
  hard tasks. cc-bench ships a tiny demo suite — you bring the realistic ones.
- **Maturity & features:** Inspect/promptfoo/DeepEval are full platforms (tracing,
  datasets, dashboards, many providers). cc-bench is intentionally small.
- **Optimisation:** DSPy/GEPA *improve* prompts automatically; cc-bench only
  *measures*. Use them together — optimise, then prove the gain with cc-bench.

## The gap cc-bench fills

> A cheap, rigorous, reproducible way to test whether **a way of using a coding
> agent** helps **on your own tasks**, with honest statistics and a zero-cost CI
> loop — and an evidence base ([`EVIDENCE.md`](EVIDENCE.md)) so every default is
> backed by a citation, not folklore.

## Drop-in adoption

- `ccbench init` scaffolds a `conditions/` + starter suite into any repo (see
  [ROADMAP.md](ROADMAP.md)).
- A reusable GitHub Action runs the zero-cost mock pipeline on every PR.
- `verify_cmd` is any shell command, so any language/test runner works.
- Pure-library API (`ccbench.runner`, `ccbench.analysis`) for use inside pytest.
