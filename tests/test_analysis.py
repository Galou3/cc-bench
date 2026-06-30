import math

from ccbench.analysis import (
    _z_for_confidence, benjamini_hochberg, compare, count_outcomes,
    holm_bonferroni, pass_at_k, pass_at_k_mean, summarize_condition,
    two_proportion_p, wilson_interval,
)
from ccbench.models import Outcome, RunResult, Usage


def _results(cond, n, k, *, errors=0, timeouts=0):
    out = []
    for i in range(n):
        oc = Outcome.PASS if i < k else Outcome.FAIL
        out.append(RunResult("t", cond, i, oc, Usage(), 0.0))
    for i in range(errors):
        out.append(RunResult("t", cond, n + i, Outcome.ERROR, Usage(), 0.0))
    for i in range(timeouts):
        out.append(RunResult("t", cond, n + errors + i, Outcome.TIMEOUT, Usage(), 0.0))
    return out


def test_z_for_confidence():
    assert abs(_z_for_confidence(0.95) - 1.959964) < 1e-4


def test_wilson_known_value():
    lo, hi = wilson_interval(8, 10, 0.95)
    assert abs(lo - 0.490) < 0.01 and abs(hi - 0.943) < 0.01


def test_wilson_zero_n():
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_count_excludes_errors_from_denominator():
    counts = count_outcomes(_results("c", 10, 4, errors=3, timeouts=2))
    # decided = pass + fail + timeout = 4 + 6 + 2 = 12, errors excluded
    assert counts.passes == 4 and counts.errors == 3 and counts.decided == 12


def test_summarize_rate_uses_decided():
    rs = summarize_condition(_results("c", 10, 5, errors=4), "c")
    assert rs.rate == 0.5 and rs.counts.errors == 4


def test_two_proportion_symmetry():
    p1 = two_proportion_p(5, 20, 15, 20)
    p2 = two_proportion_p(15, 20, 5, 20)
    assert abs(p1 - p2) < 1e-12 and p1 < 0.05


def test_holm_and_bh_exact():
    assert all(abs(a - b) < 1e-9 for a, b in zip(holm_bonferroni([0.01, 0.02, 0.04]), [0.03, 0.04, 0.04]))
    assert all(abs(a - b) < 1e-9 for a, b in zip(benjamini_hochberg([0.01, 0.02, 0.04]), [0.03, 0.03, 0.04]))


def test_compare_detects_effect():
    c = compare(_results("b", 40, 16), _results("v", 40, 32), "b", "v", bootstrap_iters=2000, seed=1)
    assert c.verdict == "improvement" and c.diff > 0 and c.diff_ci_low > 0


def test_compare_null_not_proven():
    c = compare(_results("b", 40, 20), _results("v", 40, 20), "b", "v", bootstrap_iters=2000, seed=1)
    assert c.verdict == "not proven" and not c.significant


def test_pass_at_k_known_values():
    assert abs(pass_at_k(5, 2, 1) - 0.4) < 1e-9
    assert pass_at_k(5, 0, 1) == 0.0
    assert pass_at_k(5, 2, 5) == 1.0
    assert abs(pass_at_k(10, 5, 2) - (1 - 10 / 45)) < 1e-9


def test_pass_at_k_monotonic_in_k():
    vals = [pass_at_k(10, 3, k) for k in (1, 2, 3, 4)]
    assert all(a <= b + 1e-12 for a, b in zip(vals, vals[1:]))


def test_pass_at_k_mean_over_tasks():
    res = []
    for i in range(5):  # task A: 2/5 pass
        res.append(RunResult("A", "c", i, Outcome.PASS if i < 2 else Outcome.FAIL, Usage(), 0.0))
    for i in range(5):  # task B: 4/5 pass
        res.append(RunResult("B", "c", i, Outcome.PASS if i < 4 else Outcome.FAIL, Usage(), 0.0))
    assert abs(pass_at_k_mean(res, 1) - 0.6) < 1e-9          # (0.4 + 0.8) / 2
    assert pass_at_k_mean(res, 6) is None                     # k > reps for a task
