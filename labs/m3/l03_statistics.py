"""M3-L03: describing data, and why the mean is usually the wrong summary.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l03_statistics.py
"""

from __future__ import annotations

import numpy as np

LINE = "-" * 74
DATA = np.array([2, 4, 4, 4, 5, 5, 7, 9], dtype=float)


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def by_hand() -> None:
    section("1. THE HAND CALCULATION, VERIFIED")
    mean = DATA.mean()
    print(f"  data = {DATA.astype(int).tolist()}")
    print(f"  mean = {DATA.sum():.0f} / {len(DATA)} = {mean}")
    print()
    print(f"  {'x':>4}{'x - mean':>12}{'(x - mean)^2':>16}")
    total = 0.0
    for x in DATA:
        deviation = x - mean
        squared = deviation ** 2
        total += squared
        print(f"  {x:>4.0f}{deviation:>12.1f}{squared:>16.1f}")
    print(f"  {'':>4}{'sum':>12}{total:>16.1f}")
    print()
    print(f"  population variance = {total} / {len(DATA)} = {total / len(DATA)}")
    print(f"  population std dev  = sqrt({total / len(DATA)}) = "
          f"{np.sqrt(total / len(DATA))}")
    print()
    print(f"  numpy np.var(data)          = {np.var(DATA)}")
    print(f"  numpy np.std(data)          = {np.std(DATA)}")
    print(f"  numpy np.var(data, ddof=1)  = {np.var(DATA, ddof=1):.4f}  <- sample form")
    print()
    diff = (np.var(DATA, ddof=1) - np.var(DATA)) / np.var(DATA) * 100
    print(f"  The two variances differ by {diff:.1f}% at n={len(DATA)}.")
    print("  NumPy defaults to ddof=0 (population); pandas defaults to ddof=1")
    print("  (sample). They will disagree on identical data.")


def outlier() -> None:
    section("2. MEAN IS FRAGILE, MEDIAN IS ROBUST")
    clean = np.array([1, 2, 3, 4, 5], dtype=float)
    dirty = np.array([1, 2, 3, 4, 500], dtype=float)
    print(f"  {'data':<26}{'mean':>10}{'median':>10}")
    print(f"  {str(clean.astype(int).tolist()):<26}{clean.mean():>10.1f}"
          f"{np.median(clean):>10.1f}")
    print(f"  {str(dirty.astype(int).tolist()):<26}{dirty.mean():>10.1f}"
          f"{np.median(dirty):>10.1f}")
    print()
    print(f"  One value changed. The mean moved {dirty.mean() / clean.mean():.0f}x.")
    print("  The median did not move at all.")


def latency() -> np.ndarray:
    section("3. A REALISTIC LATENCY DISTRIBUTION")
    rng = np.random.default_rng(42)
    # Lognormal produces the right-skewed shape real latency has.
    values = rng.lognormal(mean=6.4, sigma=0.75, size=5000)

    mean = values.mean()
    median = np.median(values)
    p50, p90, p95, p99 = np.percentile(values, [50, 90, 95, 99])

    print(f"  {len(values):,} simulated request latencies (ms)")
    print()
    print(f"    mean    {mean:>9.0f}")
    print(f"    median  {median:>9.0f}")
    print(f"    std dev {values.std():>9.0f}")
    print(f"    p50     {p50:>9.0f}")
    print(f"    p90     {p90:>9.0f}")
    print(f"    p95     {p95:>9.0f}")
    print(f"    p99     {p99:>9.0f}")
    print(f"    max     {values.max():>9.0f}")
    print()
    print(f"  mean / median = {mean / median:.2f}  -> RIGHT SKEWED")
    below = float((values < mean).mean())
    print(f"  requests FASTER than the mean: {below:.1%}")
    print("    For symmetric data this would be 50%. Here the mean sits above")
    print("    most of the data, so it describes almost nobody.")
    print()

    print("  Distribution (each # is ~2% of requests):")
    edges = [0, 250, 500, 750, 1000, 1500, 2000, 3000, 5000, 10000, 1e9]
    labels = ["<250", "250-500", "500-750", "750-1k", "1k-1.5k", "1.5k-2k",
              "2k-3k", "3k-5k", "5k-10k", ">10k"]
    for lo, hi, label in zip(edges[:-1], edges[1:], labels):
        count = int(((values >= lo) & (values < hi)).sum())
        share = count / len(values)
        marker = ""
        if lo <= mean < hi:
            marker += "  <- MEAN"
        if lo <= median < hi:
            marker += "  <- MEDIAN"
        if lo <= p95 < hi:
            marker += "  <- p95"
        print(f"    {label:>9} {'#' * int(share * 50):<50}{share:>6.1%}{marker}")
    print()
    print("  The mean sits to the RIGHT of the bulk of the data. A status")
    print(f"  report saying 'average latency {mean:.0f}ms' describes a user who")
    print(f"  does not exist: {below:.0%} of requests are faster than that, and")
    print(f"  the ones that are slower are MUCH slower (p99 = {p99:.0f}ms).")
    return values


def standard_error() -> None:
    section("4. IS A DIFFERENCE REAL? THE STANDARD ERROR")
    print("  SE of a proportion = sqrt(p(1-p)/n)")
    print()
    print(f"  {'n':>8}{'p=0.82 SE':>14}{'~95% interval':>22}"
          f"{'resolvable gap':>17}")
    for n in (50, 100, 200, 500, 1000, 2000, 5000):
        se = np.sqrt(0.82 * 0.18 / n)
        lo, hi = 0.82 - 2 * se, 0.82 + 2 * se
        print(f"  {n:>8}{se * 100:>13.2f}%{f'{lo:.1%} - {hi:.1%}':>22}"
              f"{2 * se * 100 * 1.41:>16.1f}%")
    print()
    print("  Last column: roughly the smallest difference between two prompts")
    print("  you could distinguish at that sample size.")
    print()
    print("  Note SE shrinks with sqrt(n): going from 500 to 2000 examples")
    print("  (4x the data) halves it. There is no cheap way around this.")


def simulate_noise() -> None:
    section("5. HOW OFTEN DOES NOISE ALONE PRODUCE A 'WIN'?")
    rng = np.random.default_rng(42)
    trials = 20_000
    true_rate = 0.80

    print(f"  Two prompts, BOTH genuinely {true_rate:.0%} accurate.")
    print(f"  Simulating {trials:,} head-to-head evaluations at each size.")
    print()
    print(f"  {'n per prompt':>14}{'|diff| > 3pp':>15}{'|diff| > 5pp':>15}"
          f"{'mean |diff|':>14}")
    for n in (50, 100, 200, 500, 1000, 2000):
        a = rng.binomial(n, true_rate, size=trials) / n
        b = rng.binomial(n, true_rate, size=trials) / n
        diff = np.abs(a - b)
        print(f"  {n:>14}{(diff > 0.03).mean():>14.1%}{(diff > 0.05).mean():>15.1%}"
              f"{diff.mean() * 100:>13.2f}pp")
    print()
    print("  Read the n=100 row. Two IDENTICAL prompts differ by more than")
    print("  3 percentage points most of the time, and by more than 5 points")
    print("  often. Every one of those would look like an improvement.")
    print()
    print("  Combine this with the M1-L05 optimistic-bias result - where")
    print("  picking the best of N candidates inflates the winner's score -")
    print("  and a small evaluation set is dangerous in two ways at once:")
    print("  it manufactures differences, and then you select on them.")


def main() -> None:
    print("=" * 74)
    print("MEAN, VARIANCE, STANDARD DEVIATION AND DISTRIBUTIONS")
    print("=" * 74)
    by_hand()
    outlier()
    latency()
    standard_error()
    simulate_noise()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
