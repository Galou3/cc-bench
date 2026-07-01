"""Scope-honest statistics: suite-level permutation + task-level generalization.

test_deterministic_flip_is_scope_limited encodes the adversarial finding that
motivated this module: pooling reps across tasks can turn ONE deterministic task
flip into p < 0.001, which reads as a general claim. The stratified analysis keeps
the suite-level claim (real, reproducible on these tasks) but the sign test says
generalization is unproven.
"""

import random

from ccbench.analysis import (
    compare, compare_all_stratified, compare_stratified,
    stratified_permutation_p, task_sign_test, within_task_bootstrap_ci,
)
from ccbench.models import Outcome, RunResult, Usage


def _runs(cond, spec):
    out = []
    for task, (n, k) in spec.items():
        for i in range(n):
            oc = Outcome.PASS if i < k else Outcome.FAIL
            out.append(RunResult(task, cond, i, oc, Usage(), 0.0))
    return out


def test_permutation_matches_exact_tiny_case():
    a = _runs("a", {"t": (2, 0)})
    b = _runs("b", {"t": (2, 2)})
    p, obs, tasks = stratified_permutation_p(a, b, iters=20000, seed=1)
    assert tasks == ["t"] and abs(obs - 1.0) < 1e-12
    assert abs(p - 1 / 3) < 0.02  # exact p = 2/C(4,2) = 1/3


def test_sign_test_exact_values():
    assert task_sign_test(0, 0) == 1.0
    assert task_sign_test(1, 0) == 1.0
    assert abs(task_sign_test(3, 0) - 0.25) < 1e-12
    assert abs(task_sign_test(5, 1) - 7 / 32) < 1e-12


def test_deterministic_flip_is_scope_limited():
    a = _runs("a", {"t1": (10, 10), "t2": (10, 10), "t3": (10, 0)})
    b = _runs("b", {"t1": (10, 10), "t2": (10, 10), "t3": (10, 10)})

    pooled = compare(a, b, "a", "b", bootstrap_iters=2000, seed=0)
    assert pooled.significant  # the old reading: p < 0.001 from one task flip

    s = compare_stratified(a, b, "a", "b", iters=4000, seed=0)
    assert s.significant  # real and reproducible on THIS suite
    assert s.tasks_improved == 1 and s.tasks_regressed == 0
    assert s.sign_p == 1.0  # but one task proves nothing about other tasks


def test_no_effect_when_arms_identical():
    a = _runs("a", {"t1": (6, 3), "t2": (6, 6)})
    b = _runs("b", {"t1": (6, 3), "t2": (6, 6)})
    s = compare_stratified(a, b, "a", "b", iters=2000, seed=0)
    assert not s.significant and s.verdict == "not proven"
    assert s.mean_diff == 0.0


def test_fpr_controlled_under_task_heterogeneity():
    difficulties = [0.2, 0.4, 0.6, 0.8]
    rng = random.Random(777)
    trials, hits = 60, 0
    for trial in range(trials):
        spec_a, spec_b = {}, {}
        for i, p in enumerate(difficulties):
            spec_a[f"t{i}"] = (8, sum(1 for _ in range(8) if rng.random() < p))
            spec_b[f"t{i}"] = (8, sum(1 for _ in range(8) if rng.random() < p))
        a, b = _runs("a", spec_a), _runs("b", spec_b)
        s = compare_stratified(a, b, "a", "b", iters=500, seed=trial)
        hits += s.significant
    assert hits / trials <= 0.12, f"stratified FPR too high: {hits / trials}"


def test_power_under_uniform_effect():
    rng = random.Random(31)
    trials, hits = 40, 0
    for trial in range(trials):
        spec_a, spec_b = {}, {}
        for i, p in enumerate([0.2, 0.3, 0.4, 0.3]):
            spec_a[f"t{i}"] = (10, sum(1 for _ in range(10) if rng.random() < p))
            spec_b[f"t{i}"] = (10, sum(1 for _ in range(10) if rng.random() < p + 0.4))
        a, b = _runs("a", spec_a), _runs("b", spec_b)
        s = compare_stratified(a, b, "a", "b", iters=500, seed=trial)
        hits += s.significant
    assert hits / trials >= 0.6, f"stratified power too low: {hits / trials}"


def test_compare_all_stratified_applies_correction():
    a = _runs("a", {"t1": (10, 4), "t2": (10, 5)})
    b1 = _runs("b1", {"t1": (10, 9), "t2": (10, 9)})
    b2 = _runs("b2", {"t1": (10, 5), "t2": (10, 4)})
    comps = compare_all_stratified("a", a, [("b1", b1), ("b2", b2)],
                                   iters=1500, seed=0, correction="holm")
    assert comps[0].p_adjusted is not None and comps[0].correction == "holm"
    assert comps[0].p_adjusted >= comps[0].perm_p


def test_bootstrap_ci_degenerate_no_variation():
    a = _runs("a", {"t": (5, 5)})
    b = _runs("b", {"t": (5, 5)})
    lo, hi = within_task_bootstrap_ci(a, b, iters=500, seed=0)
    assert lo == 0.0 and hi == 0.0
