"""M5-L18 lab -- the gap between what your eval set says and the truth,
how precisely a sample size actually tells you your quality, and why random
sampling misses the rare cases that matter most.

Section 1 is a REAL simulation of a real, well-documented failure mode:
iterating a prompt against a small, fixed, non-held-out set of examples
inflates that set's pass rate without necessarily improving true quality.
Sections 2 and 3 are exact, closed-form arithmetic -- no simulation needed,
just the standard error formula and the binomial "probability of zero
occurrences" formula, both real and reproducible for any inputs you choose.

Deterministic (zlib.crc32 seeding). No API key, no network.
Run:  python labs/m5/l18_evaluation_dataset.py
"""

from __future__ import annotations

import math
import zlib

import numpy as np


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*parts) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


# ============================================================ 1
rule("1. PROMPT-TUNING CONTAMINATION: THE GAP BETWEEN YOUR EVAL SET AND TRUTH")

TRUE_QUALITY = 0.45      # an early prompt draft's real, underlying capability -- unknown to the "engineer"
N_VISIBLE = 15            # the small set being iterated against, in view every time
N_HELDOUT = 300           # never looked at during iteration -- the true holdout
GENERALIZE_RATE = 0.20    # chance a patch to one visible failure is a REAL, generalising fix
FLIP_FRACTION = 0.05      # of currently-failing held-out examples, the share a real fix corrects

print(f"  True prompt quality: {TRUE_QUALITY:.0%} (unknown to whoever is iterating).")
print(f"  {N_VISIBLE} examples stay visible and get iterated against every round.")
print(f"  {N_HELDOUT} examples are a genuine holdout, never inspected during iteration.")
print(f"  Each round: patch one failing visible example until it passes. "
      f"{GENERALIZE_RATE:.0%} chance the patch is a real, generalising fix\n"
      f"  rather than one that only works for that specific example.\n")

visible_pass = [seeded("visible", i).random() < TRUE_QUALITY for i in range(N_VISIBLE)]
heldout_pass = [seeded("heldout", i).random() < TRUE_QUALITY for i in range(N_HELDOUT)]

print(f"  {'iteration':>10}{'visible-set pass rate':>24}{'TRUE (holdout) pass rate':>26}")
iteration = 0
start_visible = sum(visible_pass) / N_VISIBLE
start_heldout = sum(heldout_pass) / N_HELDOUT
print(f"  {'start':>10}{start_visible:>24.0%}{start_heldout:>26.0%}")

while not all(visible_pass):
    iteration += 1
    fail_idx = next(i for i, p in enumerate(visible_pass) if not p)
    visible_pass[fail_idx] = True   # the engineer keeps patching until it passes

    if seeded("generalize", iteration).random() < GENERALIZE_RATE:
        failing_heldout = [i for i, p in enumerate(heldout_pass) if not p]
        if failing_heldout:
            n_flip = max(1, round(FLIP_FRACTION * len(failing_heldout)))
            rng = seeded("flip", iteration)
            flip_idx = rng.choice(failing_heldout,
                                   size=min(n_flip, len(failing_heldout)),
                                   replace=False)
            for i in flip_idx:
                heldout_pass[int(i)] = True

    v_rate = sum(visible_pass) / N_VISIBLE
    h_rate = sum(heldout_pass) / N_HELDOUT
    print(f"  {iteration:>10}{v_rate:>24.0%}{h_rate:>26.0%}")

final_visible = sum(visible_pass) / N_VISIBLE
final_heldout = sum(heldout_pass) / N_HELDOUT
print(f"\n  After {iteration} rounds: visible set reads {final_visible:.0%}. The true,")
print(f"  held-out quality moved from {start_heldout:.0%} to only {final_heldout:.0%}.")
print(f"  The visible set now overstates true quality by "
      f"{(final_visible - final_heldout) * 100:.0f} points.")
print("\n  Nobody in this simulation acted in bad faith -- every single patch")
print("  genuinely fixed the example in front of them. The gap opened up")
print("  purely because the SAME small set was used to both guide changes")
print("  and report quality. This is M1-L09's leakage family, in a form")
print("  specific to prompt engineering: no gradient ever touched this data,")
print("  and it is contaminated anyway.")


# ============================================================ 2
rule("2. HOW PRECISELY DO YOU ACTUALLY KNOW YOUR TRUE QUALITY?")

P_HAT = 0.85
print(f"  A measured pass rate of {P_HAT:.0%} on an eval set means different things")
print("  at different sample sizes. This is a DIFFERENT question from M5-L12")
print("  section 3 (which asked: how many samples to reliably DETECT A KNOWN")
print("  GAP between two versions). Here the question is: given ONE")
print(f"  measurement of {P_HAT:.0%}, how far from the true value could it be?\n")
print(f"  {'N':>6}{'std. error':>12}{'95% CI':>22}{'CI width':>11}")
for n in (10, 30, 100, 300, 1000, 3000):
    se = math.sqrt(P_HAT * (1 - P_HAT) / n)
    lo, hi = max(0.0, P_HAT - 1.96 * se), min(1.0, P_HAT + 1.96 * se)
    print(f"  {n:>6}{se:>12.3f}{f'[{lo:.0%}, {hi:.0%}]':>22}{hi - lo:>11.0%}")

print("\n  At N=10, the true quality could plausibly be anywhere from about")
print("  56% to 100% -- a measured 85% at that sample size is barely more")
print("  informative than a guess. The interval only becomes tight enough to")
print("  make a real decision from somewhere around a few hundred examples,")
print("  depending how much precision the decision actually needs.")


# ============================================================ 3
rule("3. STRATIFICATION: RANDOM SAMPLING MISSES THE CASES THAT MATTER MOST")

RARE_SHARE = 0.02   # e.g. 'refund request over the policy cap' -- rare, high-stakes
print(f"  A critical-but-rare case type makes up {RARE_SHARE:.0%} of real traffic.")
print("  If your eval set is built by pure random sampling, what is the")
print("  chance it contains ZERO examples of that case type?\n")
print(f"  {'eval set size (N)':>18}{'P(zero examples of the rare case)':>36}")
for n in (10, 30, 50, 100, 200, 500):
    p_zero = (1 - RARE_SHARE) ** n
    print(f"  {n:>18}{p_zero:>36.1%}")

n95 = math.log(0.05) / math.log(1 - RARE_SHARE)
n99 = math.log(0.01) / math.log(1 - RARE_SHARE)
print(f"\n  Solved exactly: a random sample needs at least {math.ceil(n95)} examples")
print(f"  before there is even a 95% chance of including ONE instance of this")
print(f"  {RARE_SHARE:.0%} case type, and {math.ceil(n99)} for 99%. At the eval-set sizes")
print("  most teams actually build (50-100 examples), a purely random")
print("  sample has a real, substantial chance of never testing the case")
print("  that matters most.")
print("\n  The fix is not a bigger random sample -- it is STRATIFICATION:")
print("  deliberately including a stated minimum number of examples from")
print("  each case type you care about, by design, rather than hoping")
print("  random chance provides them (M3-L13).")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: sections 2 and 3 are exact, closed-form statistics -- the")
print("  standard-error and binomial-zero-probability formulas, computed for")
print("  the stated inputs. Recompute them for your own eval set size and")
print("  your own rare-case share; the formulas transfer exactly.")
print(f"\n  MOCK, mechanism-real: section 1's contamination simulation uses a")
print(f"  stated generalisation rate ({GENERALIZE_RATE:.0%}) as a modelling choice. The")
print("  MECHANISM -- iterating against a fixed, visible set inflates its")
print("  own pass rate faster than true quality improves -- is real and")
print(f"  well documented; the exact {GENERALIZE_RATE:.0%} and the resulting gap size are")
print("  illustrative, not a measurement of any real prompt-tuning process.")
print("\n  NOT SHOWN: LLM-as-judge scoring and its own agreement-with-humans")
print("  problem (a preview, not a full treatment -- see M13-L13), and the")
print("  full mechanics of building a stratified sample from real traffic")
print("  logs, which is largely a data-engineering problem outside this")
print("  lesson's scope.")

print("\nDone.")
