# Changelog

All notable changes to cc-bench are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- **Scope-honest statistics.** Found by our own adversarial review: pooling reps
  across tasks as iid could turn one deterministic task flip into p < 0.001,
  overstating the scope of the claim. The headline verdict is now task-stratified
  (permutation within task + within-task bootstrap CI) and a separate task-level
  sign test answers "does it generalize?". Reports and CLI now say "on this
  suite" and report task flips explicitly.

### Fixed
- **Reward-hacking hole closed.** The runner restores the template's test files
  after the agent finishes and before grading, and bundled suites' verify_cmd
  targets exact test files, so an agent rewriting visible tests cannot grade as
  PASS (encoded as a TamperAgent regression test).

### Added
- `ccbench validate`: checks every task discriminates (workspace fails,
  reference passes); from-repo / from-git auto-validate the task they create.
- `conditions/placebo-claude-md.yaml`: a placebo arm (same-length, content-free
  CLAUDE.md) as a built-in negative control; see METHODOLOGY > Controls.
- `ccbench from-git`: held-out tasks from your repo's git history (SWE-bench-style
  construction on your own code).
- `--sandbox docker`: grading runs in an ephemeral, network-disabled container.
- `ccbench from-repo`: turn your own tested code into held-out tasks (no authoring).
- `ccbench compare`: head-to-head of two runs (e.g. claude vs codex).
- Held-out tests (`hidden_tests_dir`) and a `hard` suite (4 tasks) off the ceiling.
- Multi-seed robustness (`--seeds`), `pass@k`, and a 0-100 `doctor` health score.
- `doctor` covers `AGENTS.md` (Codex) and flags a CLAUDE.md with no test command.
- JavaScript sample suite; live GitHub Actions CI; PRIOR_ART competitor map; LAUNCH.md.

## [0.1.0] - 2026-06-30

First public release.

### Added
- Declarative **suites** (tasks = broken code + a failing test, with a held-out
  reference) and **conditions** (YAML, each with a rationale + citation).
- Isolated per-run **workspaces** and execution-based **grading** (4-way outcome:
  pass / fail / timeout / error).
- **Agents**: a deterministic zero-cost `mock`, a real `claude -p` adapter, and an
  experimental `codex` adapter.
- **Analysis**: Wilson rate intervals, bootstrap difference CI, two-proportion
  z-test, Holm-Bonferroni / BH-FDR multiple-comparison correction, `pass@k`
  (Chen et al. 2021), and multi-seed **robustness** (mean +/- SD).
- **Reports** (Markdown + CSV) with an honest two-gate verdict and a loud
  `SIMULATED` banner for mock runs.
- **CLI**: `run`, `report`, `compare` (head-to-head, e.g. claude vs codex),
  `agents`, `init` (scaffold a starter), and `doctor` (evidence-based audit of
  `CLAUDE.md` / `AGENTS.md` / settings, with `--fix`).
- **`EVIDENCE.md`**: 40 adversarially-verified, cited sources behind every
  recommendation; **`METHODOLOGY.md`** with the stats and threats to validity.
- 64 tests including a seeded **calibration** proof; sample suites in Python and
  JavaScript; MIT licensed.

[Unreleased]: https://github.com/Galou3/cc-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Galou3/cc-bench/releases/tag/v0.1.0
