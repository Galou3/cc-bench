"""Turn raw runs into honest, defensible statistics.

This module is the whole point of cc-bench: it decides whether a condition
*provably* changed the pass rate, or whether an apparent difference is within
noise. Design principles:

- **Right tool per quantity.** A single condition's pass rate gets a Wilson score
  interval (well-calibrated for proportions at small n, unlike the normal
  approximation or a naive bootstrap). The *difference* between two conditions
  gets a percentile bootstrap CI plus a two-proportion z-test, because a
  closed-form CI for a difference of proportions is the part people most often
  get wrong.
- **No hidden libraries.** Everything is stdlib (``math.erf`` for the normal CDF,
  Acklam's rational approximation for its inverse), so the numbers are auditable
  and the install stays trivial.
- **Honesty by construction.** A result is only called "significant" when the
  bootstrap difference CI excludes zero AND the z-test clears alpha. Small n just
  produces a wide interval and a "not proven" verdict - which is the correct
  scientific answer, not a failure of the tool.
- **Outcomes are not all equal.** ERROR (harness/config fault) is excluded from
  the denominator; TIMEOUT counts as not-solved (a too-slow agent did not solve
  the task). Both counts are reported so nothing is swept under the rug.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence

from .models import Outcome, RunResult


# --------------------------------------------------------------------------- #
# Normal distribution helpers (stdlib only)
# --------------------------------------------------------------------------- #
def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF via Acklam's rational approximation.

    Accurate to ~1e-9 over the open interval, which is far better than we need
    for confidence levels. Used to turn a confidence (e.g. 0.95) into a z value
    without hardcoding a table.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _z_for_confidence(confidence: float) -> float:
    return _norm_ppf(1.0 - (1.0 - confidence) / 2.0)


# --------------------------------------------------------------------------- #
# Counting outcomes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Counts:
    passes: int
    fails: int
    timeouts: int
    errors: int

    @property
    def decided(self) -> int:
        """Denominator for the pass rate: PASS + FAIL + TIMEOUT (ERROR excluded)."""
        return self.passes + self.fails + self.timeouts


def count_outcomes(results: Iterable[RunResult]) -> Counts:
    p = f = t = e = 0
    for r in results:
        if r.outcome is Outcome.PASS:
            p += 1
        elif r.outcome is Outcome.FAIL:
            f += 1
        elif r.outcome is Outcome.TIMEOUT:
            t += 1
        else:
            e += 1
    return Counts(p, f, t, e)


# --------------------------------------------------------------------------- #
# Single-condition rate + Wilson interval
# --------------------------------------------------------------------------- #
def wilson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Returns (0, 0) for n == 0."""
    if n == 0:
        return (0.0, 0.0)
    z = _z_for_confidence(confidence)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


@dataclass(frozen=True, slots=True)
class RateSummary:
    condition: str
    counts: Counts
    rate: float
    ci_low: float
    ci_high: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "passes": self.counts.passes,
            "fails": self.counts.fails,
            "timeouts": self.counts.timeouts,
            "errors": self.counts.errors,
            "decided": self.counts.decided,
            "rate": self.rate,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "confidence": self.confidence,
        }


def summarize_condition(
    results: Sequence[RunResult], condition: str, confidence: float = 0.95
) -> RateSummary:
    counts = count_outcomes(results)
    n = counts.decided
    rate = counts.passes / n if n else 0.0
    lo, hi = wilson_interval(counts.passes, n, confidence)
    return RateSummary(condition, counts, rate, lo, hi, confidence)


# --------------------------------------------------------------------------- #
# Comparing two conditions
# --------------------------------------------------------------------------- #
def two_proportion_p(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided p-value for H0: rate1 == rate2 (pooled two-proportion z-test)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return 2.0 * (1.0 - _norm_cdf(abs(z)))


def bootstrap_diff_ci(
    k_a: int, n_a: int, k_b: int, n_b: int,
    confidence: float = 0.95, iters: int = 5000, seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap CI for (rate_b - rate_a).

    Resampling a 0/1 sample with replacement makes the resampled success count
    Binomial(n, phat), so we draw that directly instead of materialising and
    re-sampling lists - same distribution, far faster.
    """
    if n_a == 0 or n_b == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    pa, pb = k_a / n_a, k_b / n_b
    diffs = []
    for _ in range(iters):
        ra = sum(1 for _ in range(n_a) if rng.random() < pa) / n_a
        rb = sum(1 for _ in range(n_b) if rng.random() < pb) / n_b
        diffs.append(rb - ra)
    diffs.sort()
    alpha = 1.0 - confidence
    lo_idx = max(0, int((alpha / 2) * iters))
    hi_idx = min(iters - 1, int((1 - alpha / 2) * iters))
    return (diffs[lo_idx], diffs[hi_idx])


@dataclass(frozen=True, slots=True)
class Comparison:
    baseline: str
    variant: str
    rate_baseline: float
    rate_variant: float
    diff: float
    diff_ci_low: float
    diff_ci_high: float
    p_value: float
    confidence: float
    n_baseline: int
    n_variant: int

    @property
    def significant(self) -> bool:
        """Proven iff the bootstrap diff CI excludes 0 AND the z-test clears alpha."""
        alpha = 1.0 - self.confidence
        ci_excludes_zero = self.diff_ci_low > 0 or self.diff_ci_high < 0
        return ci_excludes_zero and self.p_value < alpha

    @property
    def verdict(self) -> str:
        if not self.significant:
            return "not proven"
        return "improvement" if self.diff > 0 else "regression"

    def to_dict(self) -> dict:
        return {
            "baseline": self.baseline,
            "variant": self.variant,
            "rate_baseline": self.rate_baseline,
            "rate_variant": self.rate_variant,
            "diff": self.diff,
            "diff_ci_low": self.diff_ci_low,
            "diff_ci_high": self.diff_ci_high,
            "p_value": self.p_value,
            "significant": self.significant,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "n_baseline": self.n_baseline,
            "n_variant": self.n_variant,
        }


def compare(
    baseline_results: Sequence[RunResult],
    variant_results: Sequence[RunResult],
    baseline_name: str,
    variant_name: str,
    confidence: float = 0.95,
    bootstrap_iters: int = 5000,
    seed: int = 0,
) -> Comparison:
    cb = count_outcomes(baseline_results)
    cv = count_outcomes(variant_results)
    nb, nv = cb.decided, cv.decided
    rb = cb.passes / nb if nb else 0.0
    rv = cv.passes / nv if nv else 0.0
    lo, hi = bootstrap_diff_ci(cb.passes, nb, cv.passes, nv, confidence, bootstrap_iters, seed)
    p = two_proportion_p(cb.passes, nb, cv.passes, nv)
    return Comparison(
        baseline=baseline_name, variant=variant_name,
        rate_baseline=rb, rate_variant=rv, diff=rv - rb,
        diff_ci_low=lo, diff_ci_high=hi, p_value=p,
        confidence=confidence, n_baseline=nb, n_variant=nv,
    )


__all__ = [
    "Counts", "count_outcomes", "wilson_interval", "RateSummary",
    "summarize_condition", "two_proportion_p", "bootstrap_diff_ci",
    "Comparison", "compare",
]
