# Changelog

All notable changes to cc-bench are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
