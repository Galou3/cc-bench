"""The calibration test - cc-bench's proof that it can prove things.

It runs a deterministic Monte Carlo over the analysis pipeline and checks the two
properties that make a "this setup helps" claim trustworthy:

1. POWER: when a real effect exists (p=0.45 vs 0.75), the pipeline calls it
   significant the large majority of the time at a realistic sample size.
2. CALIBRATION: when there is no effect (equal p), it almost never cries wolf -
   the false-positive rate stays near the nominal level.

Everything is seeded, so this is reproducible, not flaky. If a future change
quietly breaks the statistics (e.g. a CI that no longer covers), these bounds
fail loudly.
"""

import random

from ccbench.analysis import compare
from ccbench.models import Outcome, RunResult, Usage


def _res(cond, n, k):
    return [RunResult("t", cond, i, Outcome.PASS if i < k else Outcome.FAIL, Usage(), 0.0)
            for i in range(n)]


def _fraction_significant(pa, pb, n, trials, draw_seed, iters=600):
    rng = random.Random(draw_seed)
    hits = 0
    for t in range(trials):
        ka = sum(1 for _ in range(n) if rng.random() < pa)
        kb = sum(1 for _ in range(n) if rng.random() < pb)
        c = compare(_res("b", n, ka), _res("v", n, kb), "b", "v", bootstrap_iters=iters, seed=t)
        hits += c.significant
    return hits / trials


def test_power_detects_real_effect():
    power = _fraction_significant(0.45, 0.75, n=80, trials=80, draw_seed=7)
    assert power >= 0.85, f"power too low: {power}"


def test_false_positive_rate_under_null_is_controlled():
    fp = _fraction_significant(0.5, 0.5, n=30, trials=120, draw_seed=99)
    assert fp <= 0.15, f"false-positive rate too high: {fp}"


def test_power_increases_with_sample_size():
    low = _fraction_significant(0.45, 0.75, n=20, trials=60, draw_seed=3)
    high = _fraction_significant(0.45, 0.75, n=80, trials=60, draw_seed=3)
    assert high > low, f"power did not rise with n: {low} -> {high}"
