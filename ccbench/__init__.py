"""cc-bench: a reproducible, evidence-based benchmark harness for coding agents.

The question cc-bench answers is narrow on purpose: *does a given way of using a
coding agent (a CLAUDE.md, plan mode, a context strategy, ...) actually change the
task success rate, and by how much, with what uncertainty?*

It does that by running a small suite of self-contained tasks (each with a
deterministic pass/fail check) across one or more "conditions", repeating runs to
estimate a success rate with a bootstrap confidence interval, and comparing
conditions honestly instead of trusting folklore.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
