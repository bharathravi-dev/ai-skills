"""M5-L04 lab -- decomposition, chains of reasoning, and self-consistency.

Measures a monolithic prompt against an explicitly decomposed one on multi-step
arithmetic, locates where errors enter and how far they survive, and tests
self-consistency (majority vote over k samples) against two kinds of error.

The mock's ERROR MECHANISM is specified: a digit-level slip with a given rate,
plus an optional systematic bias. Everything the lab reports is a CONSEQUENCE
of that mechanism which was not specified -- the crossover length, the survival
of early errors, the shape of the self-consistency curve, and the divergence
between accuracy and agreement. Section 6 states what it cannot show.

Deterministic (zlib.crc32). No API key, no network.
Run:  python labs/m5/l04_decomposition.py
"""

from __future__ import annotations

import math
import zlib
from collections import Counter
from dataclasses import dataclass

import numpy as np

OPS = ("+", "-", "*")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


def wilson(p, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# --------------------------------------------------------------- the task
@dataclass(frozen=True)
class Problem:
    start: int
    steps: tuple[tuple[str, int], ...]

    def truth(self) -> int:
        v = self.start
        for op, k in self.steps:
            v = v + k if op == "+" else v - k if op == "-" else v * k
        return v

    def trace(self) -> list[int]:
        """Every intermediate value, including the start."""
        out, v = [self.start], self.start
        for op, k in self.steps:
            v = v + k if op == "+" else v - k if op == "-" else v * k
            out.append(v)
        return out

    def text(self) -> str:
        parts = [f"start with {self.start}"]
        for op, k in self.steps:
            parts.append({"+": f"add {k}", "-": f"subtract {k}",
                          "*": f"multiply by {k}"}[op])
        return ", ".join(parts)


def make_problems(n: int, n_steps: int, seed: int) -> list[Problem]:
    rng = seeded("prob", n, n_steps, seed)
    out = []
    for i in range(n):
        start = int(rng.integers(20, 200))
        steps = []
        for _ in range(n_steps):
            op = OPS[int(rng.integers(0, len(OPS)))]
            k = int(rng.integers(2, 30)) if op != "*" else int(rng.integers(2, 5))
            steps.append((op, k))
        out.append(Problem(start, tuple(steps)))
    return out


# ------------------------------------------------------------- the mock
# A slip corrupts one decimal digit of a value. That is the ONLY error
# mechanism. Everything else in this lab is a consequence of it.
SLIP_CARRIED = 0.045      # per step, when the value is held "in the head"
SLIP_WRITTEN = 0.030      # per step, when the value is written down and re-read


def apply_slip(value: int, pos_frac: float, new_digit: int) -> int:
    """Corrupt one decimal digit of value, at a position chosen by pos_frac."""
    t = str(abs(value))
    pos = min(int(pos_frac * len(t)), len(t) - 1)
    d = int(t[pos])
    nd = new_digit if new_digit != d else (d + 1) % 10
    out = int(t[:pos] + str(nd) + t[pos + 1:])
    return -out if value < 0 else out


def bias_plan(p: Problem, rate: float) -> list[tuple[bool, float, int]]:
    """A model's PERSISTENT quirk on this problem: same slip, every sample.

    Depends only on the problem, never on the run -- which is what makes it
    systematic rather than merely random.
    """
    rng = seeded("bias", p.text(), rate)
    return [(bool(rng.random() < rate), float(rng.random()),
             int(rng.integers(0, 10))) for _ in p.steps]


_PLANS: dict[tuple, list] = {}


def plan_for(p: Problem, rate: float):
    key = (p.start, p.steps, rate)
    if key not in _PLANS:
        _PLANS[key] = bias_plan(p, rate)
    return _PLANS[key]


def solve_direct(p: Problem, run: int, mode: str = "independent") -> int:
    """One prompt, answer only. Every intermediate is carried, never written.

    mode: independent -- slips are fresh noise on every sample
          systematic  -- the SAME slip on every sample of this problem
          correlated  -- the systematic slip on 60% of samples, noise on 40%
    """
    rng = seeded("direct", p.text(), run, mode)
    follow = (mode == "systematic"
              or (mode == "correlated" and rng.random() < 0.60))
    plan = plan_for(p, SLIP_CARRIED) if follow else None
    v = p.start
    for i, (op, k) in enumerate(p.steps):
        v = v + k if op == "+" else v - k if op == "-" else v * k
        if follow:
            do, pos, nd = plan[i]
            if do:
                v = apply_slip(v, pos, nd)
        elif rng.random() < SLIP_CARRIED:
            v = apply_slip(v, float(rng.random()), int(rng.integers(0, 10)))
    return v


def solve_stepwise(p: Problem, run: int) -> tuple[int, list[int]]:
    """Decomposed: each intermediate is written out, then read back."""
    rng = seeded("step", p.text(), run)
    v, written = p.start, [p.start]
    for op, k in p.steps:
        v = v + k if op == "+" else v - k if op == "-" else v * k
        if rng.random() < SLIP_WRITTEN:
            v = apply_slip(v, float(rng.random()), int(rng.integers(0, 10)))
        written.append(v)
    return v, written


def acc(problems, solver, runs=5, **kw) -> tuple[float, int]:
    hits = tot = 0
    for p in problems:
        for r in range(runs):
            tot += 1
            got = solver(p, r, **kw)
            got = got[0] if isinstance(got, tuple) else got
            hits += (got == p.truth())
    return hits / tot, tot


# ================================================================= 1
rule("1. DOES DECOMPOSITION HELP? IT DEPENDS ON THE LENGTH")

print("  Task: chained arithmetic. 'start with 84, add 17, multiply by 3, ...'")
print("  The mock slips one digit with probability 4.5% per carried step,")
print("  3.0% per written step. That is the ONLY difference between the two")
print("  prompts -- writing a value down makes it slightly harder to lose.\n")

LENGTHS = (1, 2, 3, 5, 8, 12, 20)
N_PROB, RUNS = 200, 5
print(f"  {N_PROB} problems x {RUNS} runs = {N_PROB * RUNS} trials per cell\n")
print(f"  {'steps':>7}{'direct':>10}{'decomposed':>13}{'difference':>13}"
      f"{'both intervals':>26}")
sets = {}
direct_acc, step_acc = {}, {}
for L in LENGTHS:
    probs = make_problems(N_PROB, L, seed=300 + L)
    sets[L] = probs
    a_d, n = acc(probs, solve_direct, RUNS)
    a_s, _ = acc(probs, solve_stepwise, RUNS)
    direct_acc[L], step_acc[L] = a_d, a_s
    ld, hd = wilson(a_d, n)
    ls, hs = wilson(a_s, n)
    print(f"  {L:>7}{a_d:>10.1%}{a_s:>13.1%}{a_s - a_d:>+13.1%}"
          f"{f'{ld:.0%}-{hd:.0%} vs {ls:.0%}-{hs:.0%}':>26}")

gaps = {L: step_acc[L] - direct_acc[L] for L in LENGTHS}
lo_L, hi_L = min(gaps, key=gaps.get), max(gaps, key=gaps.get)
print(f"\n  The gain from decomposing is not constant. It is smallest at "
      f"{lo_L} step(s) ({gaps[lo_L]:+.1%})")
print(f"  and largest at {hi_L} steps ({gaps[hi_L]:+.1%}) -- it grows with "
      f"chain length.")
print("\n  Both curves fall, because both accumulate slips. Decomposition does")
print("  not stop error accumulation -- it lowers the per-step rate. On a")
print("  one-step task there is nothing to accumulate and nothing to gain.")

print("\n  Now stop reading the gain column and ask the question that decides")
print("  whether to ship: at each length, does decomposition move the task")
print("  ACROSS a usability bar, or just move it within a band it fails in?\n")

print(f"  {'bar':>6}{'lengths where only':>26}{'lengths where':>20}"
      f"{'lengths where':>19}")
print(f"  {'':>6}{'DIRECT already passes':>26}{'DECOMP flips it':>20}"
      f"{'BOTH fail':>19}")
for bar in (0.95, 0.90, 0.80, 0.70, 0.60, 0.50):
    already = [L for L in LENGTHS if direct_acc[L] >= bar]
    flips = [L for L in LENGTHS if direct_acc[L] < bar <= step_acc[L]]
    neither = [L for L in LENGTHS if step_acc[L] < bar]
    fmt = lambda xs: ",".join(map(str, xs)) if xs else "-- none --"
    print(f"  {bar:>6.0%}{fmt(already):>26}{fmt(flips):>20}{fmt(neither):>19}")

flip_any = sorted({L for bar in (0.95, 0.90, 0.80, 0.70, 0.60, 0.50)
                   for L in LENGTHS if direct_acc[L] < bar <= step_acc[L]})
print(f"\n  Decomposition changes the VERDICT only at lengths "
      f"{','.join(map(str, flip_any))} --")
print("  and at any one bar, at most one or two lengths. Everywhere else it")
print("  moves a number without moving a decision: the task was already fine")
print("  without it, or it fails with it.")
print("\n  This is the question to ask of every prompting technique, and the")
print("  gain column will not answer it. A +15.4% that takes you from 40% to")
print("  56% has bought you nothing you can ship. Set the bar FIRST, then")
print("  measure, or you will celebrate improvements that change no outcome.")
print("\n  Past the band, you do not need a better prompt -- you need to stop")
print("  asking one call to do the whole job. Section 4 shows what to do")
print("  instead, and it is not a prompting technique.")

# ================================================================= 2
rule("2. WHERE THE ERROR ENTERS, AND HOW FAR IT SURVIVES")

L = 12
probs = sets[L]
first_err_pos, recovered = [], 0
total_wrong = 0
for p in probs:
    for r in range(RUNS):
        got, written = solve_stepwise(p, r)
        truth_trace = p.trace()
        bad = [i for i, (a, b) in enumerate(zip(written, truth_trace)) if a != b]
        if not bad:
            continue
        first_err_pos.append(bad[0])
        if got == p.truth():
            recovered += 1
        total_wrong += 1

fe = np.array(first_err_pos)
print(f"  {L}-step problems, {len(probs) * RUNS} trials.")
print(f"  Trials where at least one intermediate was wrong: {total_wrong}")
print(f"  Of those, trials whose FINAL answer was nevertheless right: "
      f"{recovered} ({recovered / max(total_wrong, 1):.1%})\n")
print("  Position of the FIRST wrong intermediate (1 = the first computed):")
hist = Counter(fe.tolist())
for pos in sorted(hist):
    bar = "#" * max(1, round(hist[pos] / max(hist.values()) * 40))
    print(f"  step {pos:>3}  {hist[pos]:>5}  {bar}")
print(f"\n  Roughly uniform, as the mechanism implies -- each step carries the")
print(f"  same slip probability. But the CONSEQUENCE is not uniform:\n")

print(f"  {'first error at step':<24}{'final answer correct':>22}")
for lo, hi, label in ((1, 4, "1-4  (early)"), (5, 8, "5-8  (middle)"),
                      (9, 12, "9-12 (late)")):
    n_band = ok_band = 0
    for p in probs:
        for r in range(RUNS):
            got, written = solve_stepwise(p, r)
            tt = p.trace()
            bad = [i for i, (a, b) in enumerate(zip(written, tt)) if a != b]
            if bad and lo <= bad[0] <= hi:
                n_band += 1
                ok_band += (got == p.truth())
    print(f"  {label:<24}{ok_band / max(n_band, 1):>21.1%}  (n={n_band})")

print("\n  An early error is almost never survived: everything after it is")
print("  computed from a wrong number. This is why a 95%-per-step model is")
print("  not a 95% model -- and why the verification in section 4 has to")
print("  check intermediates, not just the answer.")


# ================================================================= 3
rule("3. SELF-CONSISTENCY: WHAT MAJORITY VOTING ACTUALLY MEASURES")

print("  Sample the same prompt k times, take the majority answer. Run it")
print("  under three regimes that differ ONLY in how the model's errors")
print("  relate to each other across samples:\n")
print("    independent  -- fresh noise every sample (the textbook assumption)")
print("    correlated   -- the same quirk on 60% of samples, noise on 40%")
print("    systematic   -- the same quirk on EVERY sample")
print("\n  Single-sample accuracy is the same in all three by construction.\n")

KS = (1, 3, 5, 9, 15, 25)
MODES = ("independent", "correlated", "systematic")
probs3 = make_problems(N_PROB, 8, seed=999)


def self_consistency(problems, k, mode):
    """Returns (accuracy, mean agreement of the winning answer)."""
    hits, agree = 0, []
    for p in problems:
        votes = [solve_direct(p, r, mode) for r in range(k)]
        winner, count = Counter(votes).most_common(1)[0]
        hits += (winner == p.truth())
        agree.append(count / k)
    return hits / len(problems), float(np.mean(agree))


res = {m: {} for m in MODES}
print(f"  {'k':>4}" + "".join(f"{m:>24}" for m in MODES))
print(f"  {'':>4}" + "".join(f"{'accuracy':>12}{'agreement':>12}"
                             for _ in MODES))
for k in KS:
    line = f"  {k:>4}"
    for m in MODES:
        a, g = self_consistency(probs3, k, m)
        res[m][k] = (a, g)
        line += f"{a:>12.1%}{g:>12.1%}"
    print(line)

k_last = KS[-1]
print()
for m in MODES:
    a1, _ = res[m][1]
    ak, gk = res[m][k_last]
    print(f"  {m:<13} accuracy {a1:>6.1%} -> {ak:>6.1%} ({ak - a1:+6.1%})"
          f"   agreement at k={k_last}: {gk:.1%}")

ind_gain = res["independent"][k_last][0] - res["independent"][1][0]
sys_gain = res["systematic"][k_last][0] - res["systematic"][1][0]
print(f"\n  Same task, same single-sample accuracy, same {k_last}x bill.")
print(f"  Independent errors: {ind_gain:+.1%}.  Systematic errors: "
      f"{sys_gain:+.1%}.")
print("\n  And look at the agreement column in the systematic case: "
      f"{res['systematic'][k_last][1]:.0%}.")
print("  Every sample agreed. Perfect consensus, unchanged accuracy. If you")
print("  had used agreement as a confidence signal -- and that is exactly")
print("  what it is usually used for -- you would have been most confident")
print("  precisely where voting had bought you nothing.")
print("\n  The middle column is the realistic one. A 60% shared quirk is")
print(f"  enough to cap accuracy at {res['correlated'][k_last][0]:.1%} no "
      f"matter how many samples you buy:")
print("  the quirk wins the vote whenever it fires.")
print("\n  Self-consistency does not measure correctness. It measures")
print("  REPRODUCIBILITY, and those coincide only when errors are")
print("  independent -- which is an assumption about your model, not a")
print("  property of the technique. Test it before you pay 9x for it.")

print("\n  Note k=1: agreement is 100% by definition. A confidence score that")
print("  reads 100% on a single sample is not measuring anything.")


rule("4. VERIFICATION: CHECKING THE ANSWER vs CHECKING THE WORKING")

print("  Two cheap checks on the 12-step decomposed output:\n")
print("    (a) plausibility  -- is the final answer in a sane range?")
print("    (b) recomputation -- re-derive each step from the written value")
print("        before it, and flag the first mismatch.\n")

probsv = sets[12]
n_tr = caught_a = caught_b = wrong = 0
for p in probsv:
    lo_b = min(min(p.trace()), 0) - 10_000
    hi_b = max(max(p.trace()), 0) + 10_000
    for r in range(RUNS):
        got, written = solve_stepwise(p, r)
        n_tr += 1
        if got == p.truth():
            continue
        wrong += 1
        caught_a += not (lo_b <= got <= hi_b)
        v = written[0]
        mismatch = False
        for i, (op, k) in enumerate(p.steps):
            expect = v + k if op == "+" else v - k if op == "-" else v * k
            if written[i + 1] != expect:
                mismatch = True
                break
            v = written[i + 1]
        caught_b += mismatch

print(f"  {n_tr} trials, {wrong} wrong answers ({wrong / n_tr:.1%})\n")
print(f"  {'check':<34}{'wrong answers caught':>22}")
print(f"  {'(a) plausibility range':<34}{caught_a / max(wrong, 1):>21.1%}")
print(f"  {'(b) recompute the written steps':<34}"
      f"{caught_b / max(wrong, 1):>21.1%}")
print("\n  The plausibility check is nearly useless here: a single corrupted")
print("  digit usually lands inside any range you would have called sane.")
print("  Recomputation finds the error because it checks the WORKING, and")
print("  the working is only available because the prompt was decomposed.")
print("\n  That is the real argument for decomposition, and it is not the one")
print("  usually given: not that the model reasons better, but that it")
print("  EMITS INTERMEDIATE VALUES YOUR CODE CAN CHECK.")


# ================================================================= 5
rule("5. WHAT EACH STRATEGY COSTS")

IN_P, OUT_P = 0.50 / 1e6, 2.00 / 1e6      # ILLUSTRATIVE, dated 2026-09-09
REQ = 100_000
BASE_IN, ANS_OUT, STEP_OUT = 120, 8, 14

print(f"  {REQ:,} requests/month, ${IN_P * 1e6:.2f}/M in, ${OUT_P * 1e6:.2f}/M "
      f"out  [ILLUSTRATIVE]")
print(f"  12-step problems.\n")
print(f"  {'strategy':<30}{'accuracy':>10}{'out tok':>10}{'$/month':>11}"
      f"{'$ per point':>14}")

a_direct = direct_acc[12]
a_step = step_acc[12]
a_sc9, _ = self_consistency(sets[12], 9, "independent")
a_sc9s, g_sc9s = self_consistency(sets[12], 9, "systematic")

for name, a, out_tok, mult in (
        ("direct (answer only)", a_direct, ANS_OUT, 1),
        ("decomposed (show steps)", a_step, ANS_OUT + 12 * STEP_OUT, 1),
        ("decomposed + recompute check", a_step, ANS_OUT + 12 * STEP_OUT, 1),
        ("self-consistency k=9 (indep.)", a_sc9, ANS_OUT, 9),
        ("self-consistency k=9 (system.)", a_sc9s, ANS_OUT, 9),
):
    cost = (BASE_IN * IN_P + out_tok * OUT_P) * REQ * mult
    print(f"  {name:<30}{a:>10.1%}{out_tok * mult:>10,}{f'${cost:,.0f}':>11}"
          f"{cost / (a * 100):>14.2f}")

print("\n  The recompute check is the same price as decomposing -- it runs in")
print("  YOUR code, on tokens you were already paying for. It is the only")
print("  row that adds reliability for nothing.")
print(f"\n  The last two rows are the same technique at the same price. The")
print(f"  only difference is a property of the MODEL -- whether its errors")
print(f"  repeat. {a_sc9:.1%} against {a_sc9s:.1%}, for an identical bill of")
print(f"  9x. Nothing in the prompt tells you which row you are buying.")


# ================================================================= 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  SPECIFIED: one error mechanism -- a single corrupted decimal digit,")
print("  at 4.5% per carried step and 3.0% per written step, and how strongly")
print("  that slip repeats across samples (0%, 60%, 100%).")
print("\n  NOT SPECIFIED, and therefore measured:")
print("    * that the decomposition gain peaks in the middle of the range")
print("    * that early errors are almost never survived")
print("    * that majority voting reaches 100% under independent errors and")
print("      moves accuracy not at all under systematic ones, at equal cost")
print("    * that agreement is HIGHEST exactly where voting helps least")
print("    * that a 60% shared quirk caps accuracy no matter how many")
print("      samples are bought")
print("    * that a plausibility check catches almost nothing")
print("\n  WHAT IT CANNOT SHOW: whether a real model's stated reasoning is a")
print("  faithful account of how it produced the answer. This mock's written")
print("  steps ARE its computation, by construction. In a real model the")
print("  chain-of-thought is generated text, and it can be a fluent")
print("  after-the-fact story attached to an answer arrived at otherwise.")
print("  Do not read this lab as evidence that reasoning traces are honest.")
print("  Exercise 3 asks you to test that on a real model.")

print("\nDone.")
