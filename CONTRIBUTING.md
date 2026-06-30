# Contributing to cc-bench

Thanks for considering a contribution. cc-bench aims to be small, honest, and
easy to trust - contributions that keep it that way are very welcome.

## Setup

```bash
git clone https://github.com/Galou3/cc-bench
cd cc-bench
pip install -e ".[dev]"
pytest -q                  # 41 tests, ~16s, no network
ccbench run --suite suites/sample --conditions conditions --agent mock --reps 5
```

Python 3.10+ is required. The only runtime dependency is PyYAML; please keep it
that way unless there is a strong reason (open an issue first).

## Ways to contribute

- **A new task suite.** Add `suites/<name>/tasks.yaml` plus, per task, a
  `workspace/` (broken code + a failing test) and a held-out `reference/`. Run it
  with `--agent mock` to confirm tasks start broken and the reference fixes them.
- **A new condition.** A YAML file in `conditions/` with `inject_files`,
  `agent_args`, and - required by project policy - a `rationale` and a `citation`
  into [`EVIDENCE.md`](EVIDENCE.md). If you can't cite it, label it a hypothesis.
- **A new agent adapter.** Implement the `Agent` protocol in `ccbench/agents/`
  (mutate the workspace, return `Usage`), register it in `agents/__init__.py`, and
  isolate any output parsing in a pure function with unit tests (see
  `claude_code.parse_claude_json`). Don't require network access in CI.
- **Statistics / analysis.** Any change here must keep
  `tests/test_calibration.py` green and add a test demonstrating the new property.

## Project conventions

- **Honesty first.** No claim ships without a way to verify it. A result is only
  "significant" when the CI excludes 0 *and* the corrected p clears α.
- **Surgical changes.** Keep diffs minimal and focused; don't reformat unrelated
  code.
- **Tests are required** for behaviour changes; prefer fast, deterministic tests
  (seed everything).
- **Commits**: imperative subject + a body explaining the *why*. Conventional
  prefixes (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`) appreciated.

## Pull requests

1. Branch from `main`.
2. `pytest -q` green; add/adjust tests.
3. Describe what you changed and how you verified it.
4. Be ready for review focused on correctness and honesty of any statistical claim.

By contributing you agree your work is licensed under the project's [MIT](LICENSE)
license and that you follow the [Code of Conduct](CODE_OF_CONDUCT.md).
