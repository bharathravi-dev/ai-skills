"""M10-L08 lab -- an aggregate score is an average over people, and averages hide
who the system fails. This lab builds a synthetic screening classifier and measures:

  1. overall accuracy vs per-subgroup error rates,
  2. Wilson confidence intervals: which gaps are distinguishable from noise,
  3. Simpson's paradox: a gap that reverses inside every stratum,
  4. three fairness definitions that cannot all hold at once,
  5. intersections: the cells where there is not enough data to measure at all.

All data is synthetic and generated here; subgroups are labelled neutrally
(Group A/B/C, channel) because the arithmetic, not the attribute, is the subject.
Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l08_bias_subgroup_evaluation.py
"""

from __future__ import annotations

import math
import random
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1008)

# ---------------------------------------------------------------- data
# A screening model scores applicants; the label is whether they were suitable.
# Group B is smaller and its suitable applicants score slightly lower, because the
# model was fitted on a population where Group B was under-represented.
POPULATION = []
for i in range(4000):
    group = "A" if rng.random() < 0.72 else ("B" if rng.random() < 0.75 else "C")
    channel = "online" if rng.random() < 0.6 else "referral"
    suitable = rng.random() < (0.45 if channel == "referral" else 0.30)
    base = rng.gauss(0.62 if suitable else 0.38, 0.13)
    if group == "B" and suitable:
        base -= 0.10                      # the model under-scores suitable Group B applicants
    if group == "C":
        base -= 0.02
    POPULATION.append({"group": group, "channel": channel, "suitable": suitable,
                       "score": min(max(base, 0.0), 1.0)})

THRESHOLD = 0.5


def predict(row, threshold=THRESHOLD) -> bool:
    return row["score"] >= threshold


def rates(rows, threshold=THRESHOLD) -> dict:
    tp = sum(1 for r in rows if r["suitable"] and predict(r, threshold))
    fn = sum(1 for r in rows if r["suitable"] and not predict(r, threshold))
    fp = sum(1 for r in rows if not r["suitable"] and predict(r, threshold))
    tn = sum(1 for r in rows if not r["suitable"] and not predict(r, threshold))
    n = len(rows)
    return {"n": n, "accuracy": (tp + tn) / n if n else 0,
            "tpr": tp / (tp + fn) if tp + fn else 0, "fnr": fn / (tp + fn) if tp + fn else 0,
            "fpr": fp / (fp + tn) if fp + tn else 0,
            "selection_rate": (tp + fp) / n if n else 0,
            "precision": tp / (tp + fp) if tp + fp else 0, "tp": tp, "fn": fn, "fp": fp, "tn": tn}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# ============================================================ 1
rule("1. ONE AGGREGATE SCORE, THREE DIFFERENT EXPERIENCES")

overall = rates(POPULATION)
print(f"  overall accuracy {overall['accuracy']:.1%} on {overall['n']} applicants "
      f"(the number that would appear in a release note)\n")
print(f"  {'group':<7}{'n':>6}{'accuracy':>10}{'miss rate (FNR)':>18}{'false alarm (FPR)':>19}{'selection rate':>16}")
for g in ("A", "B", "C"):
    r = rates([x for x in POPULATION if x["group"] == g])
    print(f"  {g:<7}{r['n']:>6}{r['accuracy']:>10.1%}{r['fnr']:>18.1%}{r['fpr']:>19.1%}{r['selection_rate']:>16.1%}")
fnr_a = rates([x for x in POPULATION if x["group"] == "A"])["fnr"]
fnr_b = rates([x for x in POPULATION if x["group"] == "B"])["fnr"]
print(f"\n  Group B's suitable applicants are missed {fnr_b / fnr_a:.1f}x as often as Group A's,")
print("  while overall accuracy looks healthy. Accuracy is an average over people.")


# ============================================================ 2
rule("2. IS THE GAP REAL? CONFIDENCE INTERVALS BY SUBGROUP SIZE")

print(f"  {'group':<7}{'suitable n':>12}{'missed':>9}{'FNR':>9}   95% interval")
for g in ("A", "B", "C"):
    rows = [x for x in POPULATION if x["group"] == g]
    r = rates(rows)
    lo, hi = wilson(r["fn"], r["fn"] + r["tp"])
    print(f"  {g:<7}{r['fn'] + r['tp']:>12}{r['fn']:>9}{r['fnr']:>9.1%}   [{lo:.1%}, {hi:.1%}]")
small = [x for x in POPULATION if x["group"] == "C"][:60]
rs = rates(small)
lo, hi = wilson(rs["fn"], max(rs["fn"] + rs["tp"], 1))
print(f"\n  the same measurement on a 60-applicant sample of Group C:")
print(f"    FNR {rs['fnr']:.1%} with interval [{lo:.1%}, {hi:.1%}] -- wide enough to contain")
print("    both 'no gap' and 'a very large gap'. Report intervals, and say when a")
print("    subgroup is too small to conclude anything (M3-L14).")


# ============================================================ 3
rule("3. SIMPSON'S PARADOX: AN AGGREGATE GAP THAT REVERSES IN EVERY STRATUM")

# Constructed deliberately: within each channel Group B is selected MORE often,
# but B applies mostly through the channel with the lower selection rate overall.
STRATA = {                     # channel -> group -> (applicants, selected)
    "referral (60-65% selected)": {"A": (800, 480), "B": (100, 65)},
    "online (20-25% selected)": {"A": (200, 40), "B": (900, 225)},
}
totals = {"A": [0, 0], "B": [0, 0]}
for channel, groups in STRATA.items():
    line = f"  {channel:<28}"
    for g in ("A", "B"):
        n, sel = groups[g]
        totals[g][0] += n
        totals[g][1] += sel
        line += f"  {g}: {sel}/{n} = {sel / n:.0%}"
    winner = "B" if groups["B"][1] / groups["B"][0] > groups["A"][1] / groups["A"][0] else "A"
    print(line + f"   higher: {winner}")
print(f"  {'ALL APPLICANTS':<28}" + "".join(
    f"  {g}: {totals[g][1]}/{totals[g][0]} = {totals[g][1] / totals[g][0]:.0%}" for g in ("A", "B"))
    + f"   higher: {'A' if totals['A'][1] / totals['A'][0] > totals['B'][1] / totals['B'][0] else 'B'}")
print("\n  Group B is selected more often in BOTH channels and less often overall,")
print("  because B applies mainly through the channel that selects fewer people.")
print("  Aggregates mix 'who applies where' with 'how they are treated', so report")
print("  stratified numbers and say which strata you controlled for.")


# ============================================================ 4
rule("4. THREE FAIRNESS DEFINITIONS, ONE THRESHOLD")

def definitions(threshold_a: float, threshold_b: float) -> dict:
    a = rates([x for x in POPULATION if x["group"] == "A"], threshold_a)
    b = rates([x for x in POPULATION if x["group"] == "B"], threshold_b)
    return {"selection gap (demographic parity)": abs(a["selection_rate"] - b["selection_rate"]),
            "TPR gap (equal opportunity)": abs(a["tpr"] - b["tpr"]),
            "precision gap (predictive parity)": abs(a["precision"] - b["precision"])}


scenarios = {"one threshold 0.50 for both": (0.50, 0.50),
             "Group B threshold lowered to 0.44": (0.50, 0.44),
             "Group B threshold lowered to 0.40": (0.50, 0.40)}
names = list(definitions(0.5, 0.5))
print(f"  {'scenario':<34}" + "".join(f"{n.split('(')[0].strip():>22}" for n in names))
for label, (ta, tb) in scenarios.items():
    d = definitions(ta, tb)
    print(f"  {label:<34}" + "".join(f"{d[n]:>22.1%}" for n in names))
print("\n  Closing one gap opens another: these definitions cannot all hold at once")
print("  when base rates differ (the standard impossibility result). Choosing WHICH")
print("  gap matters for this decision is a governance choice with a named owner --")
print("  and per-group thresholds carry legal constraints in many jurisdictions.")


# ============================================================ 5
rule("5. INTERSECTIONS: WHERE THERE IS NOT ENOUGH DATA TO MEASURE")

cells = Counter((x["group"], x["channel"]) for x in POPULATION)
suitable_cells = Counter((x["group"], x["channel"]) for x in POPULATION if x["suitable"])
MIN_N = 100
print(f"  {'cell':<22}{'n':>7}{'suitable n':>12}   status")
for cell, n in sorted(cells.items()):
    s = suitable_cells[cell]
    status = "measurable" if s >= MIN_N else f"too small to measure (need >= {MIN_N} suitable)"
    print(f"  {str(cell):<22}{n:>7}{s:>12}   {status}")
gaps = sum(1 for cell, n in cells.items() if suitable_cells[cell] < MIN_N)
print(f"\n  {gaps}/{len(cells)} cells cannot support a stable error-rate estimate.")
print("  Say so in the card (M10-L15) instead of publishing a number with no power,")
print("  and plan how to collect enough data -- or accept the limitation explicitly.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every rate, interval, paradox and gap above is computed from the")
print("  generated population; the Wilson intervals and the impossibility trade-off")
print("  are genuine arithmetic.")
print("\n  ILLUSTRATIVE: the population is synthetic, and the 'groups' are neutral")
print("  labels. Real subgroup analysis requires deciding which attributes you may")
print("  collect and hold at all (M10-L06), and the harms differ by context.")
print("\n  NOT SHOWN: causal analysis of WHY a gap exists, mitigation by reweighting or")
print("  data collection, and the legal treatment of protected characteristics, which")
print("  varies by jurisdiction (M10-L16).")
print("\nDone.")
