"""M3-L04: conditionals, Bayes, and why rare-event detectors mostly cry wolf.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l04_probability.py
"""

from __future__ import annotations

import numpy as np

LINE = "-" * 74

# rows: email, chat, phone   columns: billing, not billing
TABLE = np.array([[18, 22],
                  [9, 21],
                  [3, 27]])
CHANNELS = ["email", "chat", "phone"]
TOPICS = ["billing", "not billing"]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def contingency() -> None:
    section("1. EVERY CONDITIONAL COMES FROM A TABLE OF COUNTS")
    total = TABLE.sum()
    print(f"  {'':>8}{'billing':>10}{'not billing':>14}{'TOTAL':>8}")
    for name, row in zip(CHANNELS, TABLE):
        print(f"  {name:>8}{row[0]:>10}{row[1]:>14}{row.sum():>8}")
    print(f"  {'TOTAL':>8}{TABLE[:, 0].sum():>10}{TABLE[:, 1].sum():>14}{total:>8}")
    print()

    p_billing = TABLE[:, 0].sum() / total
    p_email = TABLE[0].sum() / total
    p_both = TABLE[0, 0] / total
    p_billing_given_email = TABLE[0, 0] / TABLE[0].sum()
    p_email_given_billing = TABLE[0, 0] / TABLE[:, 0].sum()

    print(f"  P(billing)            = {TABLE[:, 0].sum()}/{total} = {p_billing:.2f}")
    print(f"  P(email)              = {TABLE[0].sum()}/{total} = {p_email:.2f}")
    print(f"  P(billing and email)  = {TABLE[0, 0]}/{total} = {p_both:.2f}")
    print(f"  P(billing | email)    = {TABLE[0, 0]}/{TABLE[0].sum()} "
          f"= {p_billing_given_email:.2f}   <- restricted to EMAIL")
    print(f"  P(email | billing)    = {TABLE[0, 0]}/{TABLE[:, 0].sum()} "
          f"= {p_email_given_billing:.2f}   <- restricted to BILLING")
    print()
    print("  Same numerator (18). Different denominator. That is the whole")
    print("  difference between P(A|B) and P(B|A).")
    print()
    print("  Independence check:")
    print(f"    P(billing)         = {p_billing:.2f}")
    print(f"    P(billing | email) = {p_billing_given_email:.2f}")
    print("    They differ, so channel and topic are NOT independent -")
    print("    knowing the channel changes what you expect the topic to be.")
    print()
    print(f"  {'channel':>8}{'P(billing | channel)':>24}")
    for name, row in zip(CHANNELS, TABLE):
        print(f"  {name:>8}{row[0] / row.sum():>24.2f}")
    print("    Email is far more likely to be billing than phone is.")


def bayes_by_counting() -> None:
    section("2. THE BASE-RATE FALLACY, BY COUNTING")
    population = 100_000
    prevalence = 0.001
    sensitivity = 0.99          # P(flag | fraud)
    specificity = 0.99          # P(no flag | legitimate)

    fraud = int(population * prevalence)
    legit = population - fraud
    true_pos = int(fraud * sensitivity)
    false_neg = fraud - true_pos
    false_pos = int(legit * (1 - specificity))
    true_neg = legit - false_pos

    print(f"  {population:,} transactions, fraud rate {prevalence:.1%}")
    print(f"  Detector: catches {sensitivity:.0%} of fraud, "
          f"clears {specificity:.0%} of legitimate")
    print()
    print(f"  {'':>14}{'fraud':>10}{'legitimate':>14}{'TOTAL':>10}")
    print(f"  {'flagged':>14}{true_pos:>10}{false_pos:>14}{true_pos + false_pos:>10}")
    print(f"  {'not flagged':>14}{false_neg:>10}{true_neg:>14}{false_neg + true_neg:>10}")
    print(f"  {'TOTAL':>14}{fraud:>10}{legit:>14}{population:>10}")
    print()
    precision = true_pos / (true_pos + false_pos)
    print(f"  P(fraud | flagged) = {true_pos} / {true_pos + false_pos} = {precision:.3f}")
    print()
    print(f"  A '99% accurate' detector is right about {precision:.1%} of the time")
    print(f"  when it fires. There are {false_pos / true_pos:.0f}x more false alarms")
    print("  than real fraud.")
    print()
    print("  Via Bayes directly:")
    evidence = sensitivity * prevalence + (1 - specificity) * (1 - prevalence)
    posterior = sensitivity * prevalence / evidence
    print(f"    prior      P(fraud)          = {prevalence}")
    print(f"    likelihood P(flag | fraud)   = {sensitivity}")
    print(f"    evidence   P(flag)           = {sensitivity} x {prevalence} + "
          f"{1 - specificity:.2f} x {1 - prevalence:.3f} = {evidence:.5f}")
    print(f"    posterior  P(fraud | flag)   = {sensitivity} x {prevalence} / "
          f"{evidence:.5f} = {posterior:.4f}")
    print(f"    matches the counting result ({precision:.3f})")


def base_rate_sweep() -> None:
    section("3. PRECISION COLLAPSES AS THE EVENT GETS RARER")
    sensitivity, fp_rate = 0.95, 0.01
    print(f"  Holding sensitivity at {sensitivity:.0%} and the false-positive")
    print(f"  rate at {fp_rate:.0%}, varying only how common the event is:")
    print()
    print(f"  {'base rate':>12}{'precision':>12}{'':>4}{'false alarms per true positive':>32}")
    for prior in (0.5, 0.2, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001):
        evidence = sensitivity * prior + fp_rate * (1 - prior)
        precision = sensitivity * prior / evidence
        ratio = (1 - precision) / precision if precision > 0 else float("inf")
        bar = "#" * int(precision * 40)
        ratio_text = f"{ratio:.2f}x" if ratio < 10 else f"{ratio:.0f}x"
        print(f"  {prior:>12.4%}{precision:>12.3f}    {bar:<40}{ratio_text:>8}")
    print()
    print("  Nothing about the detector changed across those rows. Only the")
    print("  world did. This is why 'accuracy' is the wrong metric for rare")
    print("  events and precision is the right one (M3-L14).")

    # Solve for the base rate at which precision = 0.5
    target = 0.5
    prior_at_half = fp_rate * target / (sensitivity * (1 - target) + fp_rate * target)
    print()
    print(f"  Precision falls below 50% once the base rate drops below "
          f"{prior_at_half:.4%}.")


def alert_arithmetic() -> None:
    section("4. THE SECTION 6 ALERT DECISION")
    sessions = 50_000
    prior = 0.0002
    sensitivity = 0.95
    fp_rate = 0.02

    incidents = sessions * prior
    caught = incidents * sensitivity
    normal = sessions - incidents
    false_alarms = normal * fp_rate
    precision = caught / (caught + false_alarms)

    print(f"  {sessions:,} sessions/day, incident rate {prior:.2%}")
    print(f"    real incidents        : {incidents:>10.1f}")
    print(f"    caught ({sensitivity:.0%})         : {caught:>10.1f}")
    print(f"    false alarms ({fp_rate:.0%})     : {false_alarms:>10.1f}")
    print(f"    total pages           : {caught + false_alarms:>10.1f}")
    print(f"    P(incident | page)    : {precision:>10.4f}  ({precision:.2%})")
    print(f"    -> 1 real incident per {1 / precision:.0f} pages")
    print()
    print("  An engineer paged ~1,000 times a day will stop reading them.")
    print("  The system's real output is alert fatigue, and real incidents")
    print("  get missed BECAUSE of the alerts, not despite them.")
    print()
    print("  What would fix it:")
    print(f"  {'false-positive rate':>22}{'pages/day':>12}{'precision':>12}")
    for rate in (0.02, 0.005, 0.001, 0.0001):
        fa = normal * rate
        p = caught / (caught + fa)
        print(f"  {rate:>21.2%}{caught + fa:>12.0f}{p:>12.1%}")
    print()
    print("  Only at a 0.01% false-positive rate does paging become")
    print("  defensible - a 200x improvement on the current detector.")


def naive_bayes_calibration() -> None:
    section("5. NAIVE BAYES: GOOD RANKING, BAD PROBABILITIES")
    rng = np.random.default_rng(42)
    n = 4000

    # Two CORRELATED features - exactly what Naive Bayes assumes away.
    labels = rng.random(n) < 0.5
    base = rng.random(n)
    # Both features are noisy copies of the same underlying signal.
    f1 = np.where(labels, base * 0.6 + 0.4, base * 0.6)
    f2 = np.where(labels, base * 0.6 + 0.4, base * 0.6)
    f1 = np.clip(f1 + rng.normal(0, 0.05, n), 0.001, 0.999)
    f2 = np.clip(f2 + rng.normal(0, 0.05, n), 0.001, 0.999)

    # Naive Bayes multiplies as if f1 and f2 were independent.
    odds = (f1 / (1 - f1)) * (f2 / (1 - f2))
    naive_prob = odds / (1 + odds)
    # A single-feature model, which does NOT double-count.
    single_odds = f1 / (1 - f1)
    single_prob = single_odds / (1 + single_odds)

    naive_acc = ((naive_prob > 0.5) == labels).mean()
    single_acc = ((single_prob > 0.5) == labels).mean()
    print(f"  {n} samples, two HIGHLY CORRELATED features.")
    print(f"    accuracy using both (naive, double-counts) : {naive_acc:.3f}")
    print(f"    accuracy using one feature                 : {single_acc:.3f}")
    print("    Ranking quality is essentially unaffected.")
    print()
    print("  But look at the CALIBRATION of the naive probabilities:")
    print(f"  {'stated confidence':>20}{'n':>8}{'actual accuracy':>18}{'gap':>9}")
    ece = 0.0
    for lo, hi in ((0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9),
                   (0.9, 0.99), (0.99, 1.001)):
        confidence = np.maximum(naive_prob, 1 - naive_prob)
        correct = (naive_prob > 0.5) == labels
        mask = (confidence >= lo) & (confidence < hi)
        if mask.sum() < 20:
            continue
        stated = confidence[mask].mean()
        actual = correct[mask].mean()
        ece += abs(stated - actual) * mask.sum() / n
        print(f"  {f'{lo:.2f}-{hi:.2f}':>20}{mask.sum():>8}{actual:>18.3f}"
              f"{actual - stated:>+9.3f}")
    print()
    print(f"  Expected Calibration Error: {ece:.3f}")
    extreme = float(((naive_prob > 0.99) | (naive_prob < 0.01)).mean())
    print(f"  Predictions above 0.99 or below 0.01: {extreme:.1%}")
    print()
    print("  Multiplying two copies of the same evidence pushes the")
    print("  probability toward the extremes. The CLASS is usually right;")
    print("  the CONFIDENCE is not. Rank with Naive Bayes. Do not threshold")
    print("  on its probability without calibrating first (M1-L10).")


def main() -> None:
    print("=" * 74)
    print("PROBABILITY AND CONDITIONAL PROBABILITY")
    print("=" * 74)
    contingency()
    bayes_by_counting()
    base_rate_sweep()
    alert_arithmetic()
    naive_bayes_calibration()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
