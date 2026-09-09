"""M5-L03 lab -- few-shot examples: what they buy, and what they cost.

Measures zero-shot against 1-32 examples, isolates majority-label bias,
recency bias and difficulty signalling, compares five selection strategies at
identical token cost, and computes cost per unit of quality.

Two of the six sections exist to show that the OBVIOUS experiment is wrong:
section 1 because it confounds how many examples with which ones, section 3b
because two orderings cannot establish an effect of ordering.

The mock provider models in-context learning as similarity-weighted voting
over the supplied examples, plus a prior from the instruction. That is a
simplification, but it reproduces the four biases the lesson names -- and the
lab reports where it is a simplification.

Deterministic (zlib.crc32). No API key, no network.
Run:  python labs/m5/l03_few_shot.py
"""

from __future__ import annotations

import itertools
import math
import zlib
from dataclasses import dataclass

import numpy as np

LABELS = ["billing", "technical", "account", "other"]


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


# ------------------------------------------------------------ the domain
# Each ticket is a point in a 3-D "topic space"; its true label is decided by
# which region it falls in. Ambiguous tickets sit near a boundary.
CENTRES = {
    "billing":   np.array([1.0, 0.0, 0.0]),
    "technical": np.array([0.0, 1.0, 0.0]),
    "account":   np.array([0.0, 0.0, 1.0]),
    "other":     np.array([0.4, 0.4, 0.4]),
}


@dataclass(frozen=True)
class Item:
    vec: np.ndarray
    label: str
    hard: bool
    text: str


def make_pool(n: int, seed: int, hard_fraction: float = 0.30) -> list[Item]:
    rng = seeded("pool", seed, n, hard_fraction)
    items = []
    for i in range(n):
        lab = LABELS[int(rng.integers(0, len(LABELS)))]
        hard = bool(rng.random() < hard_fraction)
        noise = 0.55 if hard else 0.16
        v = CENTRES[lab] + rng.normal(0, noise, size=3)
        items.append(Item(v, lab, hard, f"{lab}-{'hard' if hard else 'easy'}-{i}"))
    return items


TEST = make_pool(600, seed=1)
POOL = make_pool(400, seed=2)


def predict(item: Item, examples: list[Item], run: int,
            instruction_strength: float = 1.1) -> str:
    """Similarity-weighted vote over examples, plus an instruction prior.

    Recency is modelled by weighting later examples more -- which is where the
    order effect in section 3 comes from.
    """
    scores = {l: instruction_strength * float(item.vec @ CENTRES[l])
              for l in LABELS}
    n = len(examples)
    for i, ex in enumerate(examples):
        sim = float(item.vec @ ex.vec) / (
            np.linalg.norm(item.vec) * np.linalg.norm(ex.vec) + 1e-9)
        recency = 1.0 + 0.9 * (i / max(n - 1, 1))     # later weighs more
        scores[ex.label] += 2.2 * sim * recency / math.sqrt(n)
    rng = seeded(item.text, run, len(examples),
                 "".join(e.text for e in examples))
    noisy = {l: v + rng.normal(0, 0.22) for l, v in scores.items()}
    return max(noisy, key=noisy.get)


def accuracy(examples: list[Item], runs: int = 3) -> tuple[float, int]:
    hits = tot = 0
    for it in TEST:
        for r in range(runs):
            tot += 1
            hits += (predict(it, examples, r) == it.label)
    return hits / tot, tot


def balanced_set(k_per_label: int, seed: int = 7,
                 difficulty: str = "any") -> list[Item]:
    """k_per_label examples of every label. difficulty: any | easy | hard."""
    assert difficulty in ("any", "easy", "hard")
    rng = seeded("bal", k_per_label, seed, difficulty)
    out = []
    for lab in LABELS:
        cands = [x for x in POOL if x.label == lab
                 and (difficulty == "any" or x.hard == (difficulty == "hard"))]
        idx = rng.permutation(len(cands))[:k_per_label]
        out += [cands[i] for i in idx]
    return out


# ------------------------------------------------- 1. how many
rule("1. HOW MANY EXAMPLES? -- AND WHY THE OBVIOUS EXPERIMENT IS WRONG")

EX_TOKENS = 60
COUNTS = (0, 1, 2, 4, 8, 16, 32)
zero_acc, n_test = accuracy([])

print(f"  {len(TEST)} test tickets x 3 runs = {len(TEST) * 3} predictions per cell\n")
print("  THE NAIVE EXPERIMENT: draw a fresh example set for each count.\n")
print(f"  {'examples':>10}{'accuracy':>11}{'vs zero-shot':>15}")
naive = []
for k in COUNTS:
    ex = [] if k == 0 else balanced_set(max(1, k // 4), seed=7 + k,
                                        difficulty="any")[:k]
    acc, _ = accuracy(ex)
    naive.append(acc)
    print(f"  {k:>10}{acc:>11.1%}{acc - zero_acc:>+15.1%}")

drops = [(COUNTS[j], COUNTS[i]) for i in range(1, len(COUNTS))
         for j in range(i + 1, len(COUNTS)) if naive[j] < naive[i]]
if drops:
    a, b = drops[0]
    print(f"\n  That curve is not monotone -- {a} examples scored WORSE than "
          f"{b} ({naive[COUNTS.index(a)]:.1%} vs {naive[COUNTS.index(b)]:.1%}).")
    print("  Read as a dose-response curve it is nonsense, and it would be")
    print("  tempting to conclude 'few-shot is unpredictable'.")
else:
    print("\n  This particular draw happened to come out monotone. That is luck,")
    print("  not evidence -- as the next experiment shows.")
print("\n  The experiment is at fault. Each row drew a DIFFERENT example set,")
print("  so every row differs in two ways at once: how many examples, and")
print("  WHICH ones. The design cannot separate them.")

print("\n  THE CORRECTED EXPERIMENT: nested sets (each larger set CONTAINS the")
print("  smaller one), repeated over several independent draws.\n")


def nested_sets(seed: int, max_k: int = 32) -> dict[int, list[Item]]:
    """One draw, from which every count is a prefix. Only the COUNT varies."""
    rng = seeded("nested", seed)
    ordered = []
    per_label = {l: [x for x in POOL if x.label == l] for l in LABELS}
    for l in per_label:
        idx = rng.permutation(len(per_label[l]))
        per_label[l] = [per_label[l][i] for i in idx]
    cursors = {l: 0 for l in LABELS}
    while len(ordered) < max_k:
        for l in LABELS:
            if cursors[l] < len(per_label[l]) and len(ordered) < max_k:
                ordered.append(per_label[l][cursors[l]])
                cursors[l] += 1
    return {k: ordered[:k] for k in COUNTS}


DRAWS = 8
by_count = {k: [] for k in COUNTS}
for d in range(DRAWS):
    sets = nested_sets(seed=100 + d)
    for k in COUNTS:
        by_count[k].append(accuracy(sets[k])[0])

ref = nested_sets(seed=100)
print(f"  {'examples':>10}{'labels shown':>14}{'mean acc':>11}"
      f"{'sd across draws':>18}{'min':>9}{'max':>9}{'vs zero-shot':>15}")
means = {}
for k in COUNTS:
    vals = np.array(by_count[k])
    means[k] = float(vals.mean())
    cover = len({e.label for e in ref[k]})
    print(f"  {k:>10}{cover:>14}{vals.mean():>11.1%}{vals.std():>18.1%}"
          f"{vals.min():>9.1%}{vals.max():>9.1%}"
          f"{vals.mean() - zero_acc:>+15.1%}")

sd_across = float(np.mean([np.std(by_count[k]) for k in COUNTS if k > 0]))
effect = means[32] - means[1]
print(f"\n  mean sd BETWEEN draws at a fixed count : {sd_across:.1%}")
print(f"  effect of going from 1 to 32 examples  : {effect:+.1%}")
print(f"  ratio                                  : "
      f"{abs(effect) / max(sd_across, 1e-9):.1f}x")

if abs(effect) < 2 * sd_across:
    verdict = ("WHICH examples you pick matters as much as HOW MANY. A single "
               "run at each count cannot tell them apart.")
else:
    verdict = ("the count effect is larger than the between-draw noise, so a "
               "dose-response reading is defensible here.")
print(f"\n  {verdict}")
print("\n  This is why few-shot experiments report contradictory results. Run")
print("  one set at each count and you are measuring your draw, not the count.")
print("  Report mean and spread over several draws, or report nothing.")

# --- the dip: is it the COUNT, or is it label coverage? ---------------
below = [k for k in COUNTS if k > 0 and means[k] < zero_acc]
if below:
    print(f"\n  AND NOTE THE DIP: at {', '.join(map(str, below))} example(s) the")
    print(f"  prompt is WORSE than no examples at all. Adding information made")
    print(f"  the system worse. The obvious reading is 'few-shot needs a minimum")
    print(f"  count'. Test that before believing it.\n")

    print("  Holding the COUNT at 4 and varying only how many LABELS appear:\n")
    print(f"  {'4 examples drawn from':<26}{'accuracy':>11}{'95% interval':>19}")
    cov_rng = seeded("coverage")
    for n_lab in (1, 2, 4):
        per = 4 // n_lab
        picked = []
        for lab in LABELS[:n_lab]:
            cands = [x for x in POOL if x.label == lab]
            idx = cov_rng.permutation(len(cands))[:per]
            picked += [cands[i] for i in idx]
        a, n = accuracy(picked)
        lo, hi = wilson(a, n)
        print(f"  {f'{n_lab} label(s)':<26}{a:>11.1%}"
              f"{f'{lo:.1%} - {hi:.1%}':>19}")
    print("\n  Same count, same tokens. The dip is not about HOW MANY examples")
    print("  you show -- it is that an example set missing a label argues")
    print("  against that label. One example of one class is not a weak")
    print("  version of few-shot; it is a biased prior.")
    print("\n  Rule: show every label you want predicted, or show none.")

rows = [(k, means[k], k * EX_TOKENS) for k in COUNTS]

rule("2. COST PER UNIT OF QUALITY")

INSTR_TOKENS, REQ_PER_MONTH = 80, 100_000
IN_PRICE = 0.50 / 1_000_000        # ILLUSTRATIVE, dated 2026-09-09
print(f"  instruction {INSTR_TOKENS} tokens, {EX_TOKENS} tokens/example,")
print(f"  {REQ_PER_MONTH:,} requests/month at ${IN_PRICE * 1e6:.2f}/M "
      f"[ILLUSTRATIVE]\n")
print(f"  {'examples':>10}{'accuracy':>11}{'tokens/req':>13}"
      f"{'$/month':>11}{'$ per accuracy point':>23}")
best_ratio = None
for k, acc, ex_tok in rows:
    toks = INSTR_TOKENS + ex_tok
    cost = toks * REQ_PER_MONTH * IN_PRICE
    ratio = cost / (acc * 100)
    if best_ratio is None or ratio < best_ratio[1]:
        best_ratio = (k, ratio)
    print(f"  {k:>10}{acc:>11.1%}{toks:>13,}{f'${cost:,.0f}':>11}"
          f"{ratio:>22.2f}")

print(f"\n  Cost per accuracy point is lowest at {best_ratio[0]} examples.")
print("  Beyond that you pay linearly for a curve that has flattened -- the")
print("  asymmetry the lesson's diagram shows, priced.")


def acc_on(subset, examples, runs=3):
    hits = tot = 0
    for it in subset:
        for r in range(runs):
            tot += 1
            hits += (predict(it, examples, r) == it.label)
    return hits / tot


def acc_of(examples, runs=3):
    return acc_on(TEST, examples, runs)


def rate_of(examples, target, runs=3):
    hits = tot = 0
    for it in TEST:
        for r in range(runs):
            tot += 1
            hits += (predict(it, examples, r) == target)
    return hits / tot


rule("3. THE FOUR THINGS EXAMPLES TEACH THAT YOU DID NOT INTEND")

print("  (a) MAJORITY-LABEL BIAS -- the largest and least noticed\n")


def skewed_set(counts: dict[str, int], seed: int = 11) -> list[Item]:
    rng = seeded("skew", str(sorted(counts.items())), seed)
    out = []
    for lab, c in counts.items():
        cands = [x for x in POOL if x.label == lab]
        idx = rng.permutation(len(cands))[:c]
        out += [cands[i] for i in idx]
    return out


true_billing = sum(1 for t in TEST if t.label == "billing") / len(TEST)
print(f"  true proportion of 'billing' in the test set: {true_billing:.1%}\n")
print(f"  {'example split':<26}{'predicted billing':>19}{'over-prediction':>18}"
      f"{'accuracy':>11}")
for label, counts in (
        ("4 billing, 0 others", {"billing": 4}),
        ("3 billing, 1 other", {"billing": 3, "technical": 1}),
        ("2 billing, 2 others", {"billing": 2, "technical": 1, "account": 1}),
        ("balanced 1 each", {l: 1 for l in LABELS}),
):
    ex = skewed_set(counts)
    r = rate_of(ex, "billing")
    acc, _ = accuracy(ex)
    print(f"  {label:<26}{r:>19.1%}{r - true_billing:>+18.1%}{acc:>11.1%}")

print(f"\n  Four all-billing examples push predicted 'billing' well above its")
print(f"  true rate. This is section 6's convenience-sampled set, measured.")

print("\n  (b) RECENCY BIAS -- what one A/B comparison cannot see\n")
base = balanced_set(1, seed=21, difficulty="any")

a_fwd, n_ord = accuracy(base)
a_rev, _ = accuracy(list(reversed(base)))
lo_f, hi_f = wilson(a_fwd, n_ord)
lo_r, hi_r = wilson(a_rev, n_ord)
half = (hi_f - lo_f) / 2
print("  THE ONE-COMPARISON VERSION: forward vs reversed.\n")
print(f"  {'ordering':<24}{'accuracy':>11}{'95% interval':>19}{'last example':>16}")
print(f"  {'as selected':<24}{a_fwd:>11.1%}"
      f"{f'{lo_f:.1%} - {hi_f:.1%}':>19}{base[-1].label:>16}")
print(f"  {'reversed':<24}{a_rev:>11.1%}"
      f"{f'{lo_r:.1%} - {hi_r:.1%}':>19}{base[0].label:>16}")
print(f"\n  difference {abs(a_fwd - a_rev):.1%}, interval half-width {half:.1%}")
if abs(a_fwd - a_rev) > 2 * half:
    print("  So order matters -- but this comparison does not say WHY, and it")
    print("  cannot tell you whether you got lucky. Reversal is one of 24")
    print("  orderings, and you have measured two of them.")
else:
    print("  The difference is inside the noise. Two orderings cannot establish")
    print("  an order effect in either direction.")

print("\n  ALL 24 ORDERINGS of the same four examples:\n")
perms = list(itertools.permutations(range(len(base))))
by_last = {l: [] for l in LABELS}
accs = []
for p in perms:
    ordering = [base[i] for i in p]
    accs.append(acc_of(ordering))
    by_last[ordering[-1].label].append(rate_of(ordering, ordering[-1].label))

accs = np.array(accs)
spread_ord = float(accs.max() - accs.min())
print(f"  accuracy across orderings: min {accs.min():.1%}, "
      f"max {accs.max():.1%}, spread {spread_ord:.1%}")
print(f"  the single forward/reversed pair reported {abs(a_fwd - a_rev):.1%} of "
      f"that {spread_ord:.1%}")
print("  (same examples, same count, same tokens -- only the order changed)\n")
print(f"  {'label placed LAST':<24}{'its predicted rate':>21}"
      f"{'its true rate':>16}{'lift':>9}")
lifts = []
for l in LABELS:
    true_r = sum(1 for t in TEST if t.label == l) / len(TEST)
    pred_r = float(np.mean(by_last[l]))
    lifts.append(pred_r - true_r)
    print(f"  {l:<24}{pred_r:>21.1%}{true_r:>16.1%}{pred_r - true_r:>+9.1%}")
print(f"\n  Every label is over-predicted when it sits last "
      f"(lift {min(lifts):+.1%} to {max(lifts):+.1%}).")
print("  THAT is the mechanism, and the two-ordering test could not have")
print("  found it -- it would have told you 'reversing helped' and left you")
print("  with a fact about one permutation instead of a rule about position.")

print("\n  (c) DIFFICULTY SIGNALLING -- all-easy examples\n")
easy_tests = [t for t in TEST if not t.hard]
hard_tests = [t for t in TEST if t.hard]
print(f"  test set: {len(easy_tests)} clear-cut, {len(hard_tests)} ambiguous\n")
print(f"  {'example difficulty':<26}{'acc: clear-cut tests':>22}"
      f"{'acc: AMBIGUOUS tests':>22}{'gap':>8}")
for label, diff in (("all clear-cut examples", "easy"),
                    ("all ambiguous examples", "hard"),
                    ("mixed (any)", "any")):
    ex = balanced_set(1, seed=31, difficulty=diff)
    ae, ah = acc_on(easy_tests, ex), acc_on(hard_tests, ex)
    print(f"  {label:<26}{ae:>22.1%}{ah:>22.1%}{ae - ah:>+8.1%}")
print("\n  Every row is worse on the ambiguous half -- and a test set built the")
print("  same way as the examples reports only the left-hand column.")

print("\n  (d) FORMAT LOCK-IN is not modelled here.")
print("      This mock predicts a LABEL, so it cannot demonstrate a typo being")
print("      copied into an output string. That effect is real and widely")
print("      reported; exercise 2.4 asks you to measure it on a real model.")
print("      A lab should say what it does not show.")


rule("4. FIVE SELECTION STRATEGIES AT IDENTICAL COST")

print(f"  all at 4 examples, so token cost is identical\n")
print(f"  {'strategy':<26}{'accuracy':>11}{'95% interval':>18}{'vs zero-shot':>15}")


def convenience_set(k=4):
    """The first k from the pool -- whatever happened to be to hand."""
    return POOL[:k]


def diverse_set(k=4, seed=41):
    """Maximise pairwise distance -- a greedy spread over the input space."""
    rng = seeded("div", k, seed)
    chosen = [POOL[int(rng.integers(0, len(POOL)))]]
    while len(chosen) < k:
        best, best_d = None, -1.0
        for cand in POOL:
            d = min(float(np.linalg.norm(cand.vec - c.vec)) for c in chosen)
            if d > best_d:
                best, best_d = cand, d
        chosen.append(best)
    return chosen


STRATS = [
    ("zero-shot (no examples)", []),
    ("convenience (first 4)", convenience_set()),
    ("balanced, clear-cut", balanced_set(1, seed=51, difficulty="easy")),
    ("balanced, any difficulty", balanced_set(1, seed=51, difficulty="any")),
    ("balanced, ambiguous only", balanced_set(1, seed=51, difficulty="hard")),
    ("diverse (max spread)", diverse_set()),
]
lo_z, hi_z = wilson(zero_acc, n_test)
results = {}
for name, ex in STRATS:
    acc, n = accuracy(ex)
    lo, hi = wilson(acc, n)
    results[name] = acc
    if name.startswith("zero-shot"):
        verdict = "-"
    elif lo > hi_z:
        verdict = "better"
    elif hi < lo_z:
        verdict = "WORSE"
    else:
        verdict = "not distinguishable"
    print(f"  {name:<26}{acc:>11.1%}{f'{lo:.1%} - {hi:.1%}':>18}"
          f"{acc - zero_acc:>+15.1%}{verdict:>22}")

spread = max(results.values()) - min(v for k, v in results.items()
                                     if not k.startswith("zero-shot"))
print(f"\n  Every row above costs the SAME 4 examples = 240 tokens. The spread")
print(f"  between the best and worst four-example strategy is {spread:.1%}.")
print("  Selection is free; it is the largest lever on this page.")
print("\n  Note the last row. 'Diverse' sounds like a virtue, but greedy")
print("  max-spread selects the points FURTHEST from everything else -- it")
print("  is an outlier detector wearing a nice word. Representative beats")
print("  diverse when the examples are meant to show the typical case.")


rule("5. THE QUESTION SECTION 6 ACTUALLY ASKS")

fixed = balanced_set(1, seed=51, difficulty="any")
conv = convenience_set()
a_conv, n_c = accuracy(conv)
a_fixed, n_f = accuracy(fixed)
lo_c, hi_c = wilson(a_conv, n_c)
lo_f, hi_f = wilson(a_fixed, n_f)
print(f"  {'prompt':<26}{'accuracy':>11}{'95% interval':>18}")
print(f"  {'zero-shot':<26}{zero_acc:>11.1%}{f'{lo_z:.1%} - {hi_z:.1%}':>18}")
print(f"  {'convenience 4-shot':<26}{a_conv:>11.1%}{f'{lo_c:.1%} - {hi_c:.1%}':>18}")
print(f"  {'fixed (balanced set)':<26}{a_fixed:>11.1%}"
      f"{f'{lo_f:.1%} - {hi_f:.1%}':>18}")

if lo_f > hi_z:
    answer = "YES -- it beats zero-shot, distinguishably"
elif hi_f < lo_z:
    answer = "NO -- it is distinguishably WORSE than zero-shot"
else:
    answer = "NOT DISTINGUISHABLE from zero-shot"
print(f"\n  Does the FIXED set beat ZERO-SHOT?  {answer}")
print(f"  ({a_fixed - zero_acc:+.1%}; intervals "
      f"{'overlap' if not (lo_f > hi_z or hi_f < lo_z) else 'do not overlap'})")
print(f"\n  And the repair everyone celebrates -- convenience -> fixed -- is")
print(f"  {a_fixed - a_conv:+.1%}. It is easy to report that number, feel")
print("  finished, and never check the row above it.")
print("\n  That is the question worth asking, and it is not the same as")
print("  'is the fixed set better than the broken one?'. Balancing removed")
print("  harm. Whether it added BENEFIT over never having used examples is a")
print("  separate measurement, and the two are constantly confused.")
print("\n  If the answer is 'not distinguishable', the honest conclusion is to")
print("  drop the examples and keep the tokens.")


rule("6. WHAT THIS LAB IS AND IS NOT")

print("  The provider is a MOCK: similarity-weighted voting over the examples")
print("  plus an instruction prior. It reproduces majority-label bias, recency")
print("  bias and difficulty signalling because those follow from that")
print("  structure -- not because a real model was measured.")
print("\n  What transfers:")
print("    * the SHAPE (diminishing returns; linear cost)")
print("    * the METHOD (always measure zero-shot; report intervals)")
print("    * the RANKING of selection strategies")
print("\n  What does NOT transfer:")
print("    * the magnitudes")
print("    * format lock-in, which this mock cannot exhibit at all")
print("\n  Measure on the model you deploy (M5-L18).")

print("\nDone.")
