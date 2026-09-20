"""M10-L09 lab -- 'a human reviews it' is a control only if the human can and does
catch what the system gets wrong. This lab simulates 2,000 reviewed decisions and
measures:

  1. three review designs: rubber-stamping, confidence-led, and forced review,
  2. what miscalibrated confidence does to a confidence-led reviewer,
  3. time budgets: how many cases a reviewer can actually examine,
  4. sampling QA: how long a 5% sample takes to notice a systematic fault,
  5. disclosure completeness across three user interfaces.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l09_transparency_oversight.py
"""

from __future__ import annotations

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1009)
N = 2000
MODEL_ACCURACY = 0.85
REVIEWER_ACCURACY = 0.80          # when the reviewer genuinely works the case

CASES = []
for _ in range(N):
    model_right = rng.random() < MODEL_ACCURACY
    # a well-calibrated confidence: higher when the model is right
    confidence = min(0.99, max(0.30, rng.gauss(0.88 if model_right else 0.62, 0.08)))
    CASES.append({"model_right": model_right, "confidence": confidence,
                  "reviewer_would_be_right": rng.random() < REVIEWER_ACCURACY})


# ============================================================ 1
rule("1. THREE REVIEW DESIGNS, SAME MODEL, SAME REVIEWERS")

def simulate(policy: str, confidence_of=lambda c: c["confidence"]) -> dict:
    wrong = reviewed = caught = 0
    for c in CASES:
        conf = confidence_of(c)
        if policy == "rubber_stamp":
            works_the_case = rng.random() < 0.02          # nearly always just accepts
        elif policy == "confidence_led":
            works_the_case = conf < 0.80                  # only looks when the model hedges
        else:                                             # forced review of a sample + all low confidence
            works_the_case = conf < 0.80 or rng.random() < 0.20
        reviewed += works_the_case
        if c["model_right"]:
            continue
        if works_the_case and c["reviewer_would_be_right"]:
            caught += 1
        else:
            wrong += 1
    model_errors = sum(1 for c in CASES if not c["model_right"])
    return {"reviewed": reviewed, "caught": caught, "escaped": wrong,
            "catch_rate": caught / model_errors, "final_error_rate": wrong / N}


results = {}
for policy, label in (("rubber_stamp", "rubber-stamping (accepts almost everything)"),
                      ("confidence_led", "reviews only when confidence < 0.80"),
                      ("forced", "low confidence + 20% forced sample")):
    r = simulate(policy)
    results[policy] = r
    print(f"  {label:<44} cases worked: {r['reviewed']:>4}/{N}  model errors caught: "
          f"{r['catch_rate']:>5.1%}  errors reaching the user: {r['final_error_rate']:.1%}")
print(f"\n  the model alone would send {1 - MODEL_ACCURACY:.0%} of decisions out wrong.")
print("  Rubber-stamping changes that number very little, at the cost of implying")
print("  to everyone -- users, auditors, the people affected -- that a human decided.")
print("\n  Note the third row: when confidence is WELL CALIBRATED, nearly every model")
print("  error already carries a low score, so the extra 20% sample costs "
      f"{results['forced']['reviewed'] - results['confidence_led']['reviewed']} more worked")
print("  cases and catches no more errors. Its value shows up in section 2.")


# ============================================================ 2
rule("2. WHEN CONFIDENCE IS MISCALIBRATED, CONFIDENCE-LED REVIEW MISFIRES")

def overconfident(c) -> float:
    return min(0.99, c["confidence"] + 0.18)              # the same score, uniformly inflated


calibrated = simulate("confidence_led")
miscal = simulate("confidence_led", confidence_of=overconfident)
print(f"  well-calibrated confidence : cases worked {calibrated['reviewed']:>4}, "
      f"caught {calibrated['catch_rate']:.1%}, errors out {calibrated['final_error_rate']:.1%}")
print(f"  overconfident by 0.18      : cases worked {miscal['reviewed']:>4}, "
      f"caught {miscal['catch_rate']:.1%}, errors out {miscal['final_error_rate']:.1%}")
forced_miscal = simulate("forced", confidence_of=overconfident)
print(f"  overconfident + 20% sample : cases worked {forced_miscal['reviewed']:>4}, "
      f"caught {forced_miscal['catch_rate']:.1%}, errors out {forced_miscal['final_error_rate']:.1%}")
high_conf_errors = sum(1 for c in CASES if not c["model_right"] and overconfident(c) >= 0.80)
all_errors = sum(1 for c in CASES if not c["model_right"])
print(f"\n  under the inflated score, {high_conf_errors}/{all_errors} model errors arrive labelled")
print("  'high confidence' and are never worked. A confidence display is a control")
print("  only if the number is calibrated and its meaning is explained (M1-L10).")


# ============================================================ 3
rule("3. THE TIME BUDGET DECIDES HOW MUCH REVIEW IS POSSIBLE")

SECONDS_TO_REVIEW_PROPERLY = 90
for cases_per_hour in (20, 40, 90):
    seconds_each = 3600 / cases_per_hour
    share = min(1.0, seconds_each / SECONDS_TO_REVIEW_PROPERLY)
    print(f"  target {cases_per_hour:>3} cases/hour -> {seconds_each:>5.0f}s per case -> "
          f"a proper review is possible for about {share:>4.0%} of them")
print(f"\n  A proper review here means {SECONDS_TO_REVIEW_PROPERLY}s: read the case, check the evidence,")
print("  form an independent view. If the throughput target implies less, the")
print("  organisation has chosen rubber-stamping without writing it down.")


# ============================================================ 4
rule("4. SAMPLING QA: HOW LONG UNTIL A SYSTEMATIC FAULT IS NOTICED?")

for sample_rate in (0.01, 0.05, 0.20):
    for fault_rate in (0.02, 0.10):
        p_detect_per_case = sample_rate * fault_rate
        for target in (0.50, 0.95):
            n = math.log(1 - target) / math.log(1 - p_detect_per_case)
            print(f"  sampling {sample_rate:>4.0%} of outputs, fault in {fault_rate:>4.0%} of cases: "
                  f"{target:.0%} chance of seeing one within {n:>7,.0f} cases")
print("\n  At 1,000 cases a day, a 1% sample of a 2% fault has an even chance of")
print("  surfacing it in about a month and a half. Sampling finds systematic faults")
print("  slowly; targeted review of high-risk cases and user reports find them faster.")


# ============================================================ 5
rule("5. WHAT USERS ARE TOLD")

DISCLOSURES = ["AI involvement stated", "what it is for / not for", "known limitations",
               "confidence or uncertainty shown", "source of the answer (citations)",
               "how to reach a human", "how to contest a decision", "what data is used and kept"]
INTERFACES = {
    "chat widget, first version": {"AI involvement stated"},
    "chat widget, after review": {"AI involvement stated", "what it is for / not for", "known limitations",
                                  "source of the answer (citations)", "how to reach a human",
                                  "what data is used and kept"},
    "internal agent console": {"AI involvement stated", "confidence or uncertainty shown",
                               "source of the answer (citations)", "known limitations"},
}
for name, present in INTERFACES.items():
    missing = [d for d in DISCLOSURES if d not in present]
    print(f"  {name:<28} {len(present)}/{len(DISCLOSURES)} present"
          + (f"   missing: {'; '.join(missing[:3])}{'...' if len(missing) > 3 else ''}" if missing else ""))
print("\n  The internal console is missing the two disclosures that matter to the person")
print("  affected -- how to reach a human and how to contest -- because the agent, not")
print("  the customer, is its user. Somebody has to own the end-to-end story (M10-L02).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every catch rate, error rate, time budget and detection figure above is")
print("  computed from the simulation or from binomial arithmetic.")
print("\n  ILLUSTRATIVE: reviewer behaviour is a scripted probability, not a study of")
print("  real reviewers. Published work on automation bias reports large effects, but")
print("  the numbers here are this lab's assumptions, not findings.")
print("\n  NOT SHOWN: what any jurisdiction requires to be disclosed, and accessibility")
print("  of disclosures, both of which matter and are out of scope (M10-L16).")
print("\nDone.")
