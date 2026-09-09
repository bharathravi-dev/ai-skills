"""M3-L05: logs, underflow, entropy, cross-entropy and perplexity.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l05_entropy.py
"""

from __future__ import annotations

import math

import numpy as np

LINE = "-" * 74
CLASSES = ["billing", "technical", "account", "sales"]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def underflow() -> None:
    section("1. UNDERFLOW - why nobody multiplies probabilities")
    p = 0.1
    print(f"  Multiplying {p} by itself, n times:")
    print(f"  {'n':>6}{'product':>26}{'sum of logs':>16}")
    for n in (10, 50, 100, 200, 300, 323, 324, 400):
        product = p ** n
        log_sum = n * math.log(p)
        flag = "   <-- UNDERFLOWED TO ZERO" if product == 0.0 else ""
        print(f"  {n:>6}{product:>26.3e}{log_sum:>16.1f}{flag}")
    print()
    print(f"  Smallest positive float64: {np.nextafter(0, 1):.3e}")
    print()
    print("  Past ~324 multiplications the product is EXACTLY 0.0. Every")
    print("  distinction between 'unlikely' and 'impossible' is gone, and")
    print("  log(0) is -inf, so the damage propagates.")
    print()
    print("  The log column never leaves a comfortable numeric range. This")
    print("  is precisely why the M1-L02 Naive Bayes lab summed logs.")
    print()
    print("  The identity that makes it work:")
    a, b = 0.2, 0.3
    print(f"    log({a} x {b})    = log({a * b:.2f}) = {math.log(a * b):.6f}")
    print(f"    log({a}) + log({b}) = {math.log(a):.6f} + {math.log(b):.6f} "
          f"= {math.log(a) + math.log(b):.6f}")
    print(f"    identical? {math.isclose(math.log(a * b), math.log(a) + math.log(b))}")


def surprisal() -> None:
    section("2. SURPRISAL AND ENTROPY")
    print("  Surprisal of a single event, -ln(p):")
    print(f"  {'p':>8}{'-ln(p)':>12}{'-log2(p)':>12}   interpretation")
    for p, note in ((1.0, "certain, no surprise"), (0.5, "a coin flip"),
                    (0.25, "one of four"), (0.1, "fairly surprising"),
                    (0.01, "very surprising"), (0.001, "extremely surprising")):
        nat, bit = -math.log(p) + 0.0, -math.log2(p) + 0.0
        print(f"  {p:>8}{abs(nat):>12.3f}{abs(bit):>12.3f}   {note}")

    print()
    print("  Entropy = average surprisal of a whole distribution:")
    print(f"  {'shape':<20}{'distribution':<28}{'nats':>10}{'bits':>8}")
    for dist, label in (
        ([0.25, 0.25, 0.25, 0.25], "uniform over 4"),
        ([0.7, 0.1, 0.1, 0.1], "somewhat confident"),
        ([0.97, 0.01, 0.01, 0.01], "very confident"),
        ([1.0, 0.0, 0.0, 0.0], "certain"),
    ):
        arr = np.array(dist)
        nonzero = arr[arr > 0]                       # 0 * log(0) is defined as 0
        h = float(-np.sum(nonzero * np.log(nonzero)))
        h = abs(h) + 0.0
        print(f"  {label:<20}{str(dist):<28}{h:>10.4f}{h / math.log(2):>8.4f}")
    print()
    print(f"  Uniform over 4 gives exactly ln(4) = {math.log(4):.4f} nats = 2 bits.")
    print("  Entropy is maximised by uniformity and zero when certain.")


def cross_entropy_table() -> None:
    section("3. CROSS-ENTROPY - the loss is just -log(q_true)")
    true_class = 0                                   # billing
    print(f"  True class: {CLASSES[true_class]}")
    print()
    print(f"  {'model':<24}{'predicted distribution':<30}{'q(true)':>9}{'loss':>9}")
    for label, q in (
        ("confident and RIGHT", [0.90, 0.05, 0.03, 0.02]),
        ("uncertain", [0.40, 0.30, 0.20, 0.10]),
        ("uniform (no info)", [0.25, 0.25, 0.25, 0.25]),
        ("confident and WRONG", [0.02, 0.90, 0.05, 0.03]),
    ):
        arr = np.array(q)
        loss = float(-np.log(arr[true_class]))
        print(f"  {label:<24}{str(q):<30}{arr[true_class]:>9.2f}{loss:>9.3f}")
    print()
    uniform_loss = -math.log(0.25)
    right_loss = -math.log(0.90)
    wrong_loss = -math.log(0.02)
    print("  THE ASYMMETRY:")
    print(f"    uniform baseline           : {uniform_loss:.3f}")
    print(f"    confident and right SAVES  : {uniform_loss - right_loss:.3f}")
    print(f"    confident and wrong COSTS  : {wrong_loss - uniform_loss:.3f}")
    print(f"    ratio                      : "
          f"{(wrong_loss - uniform_loss) / (uniform_loss - right_loss):.1f}x")
    print()
    print("  Being confidently wrong is punished about 2x as hard as being")
    print("  confidently right is rewarded. That asymmetry is deliberate: it")
    print("  discourages asserting things the model cannot support.")
    print()
    print("  And the pathological case:")
    for q_true in (0.1, 0.01, 0.001, 1e-10, 0.0):
        clipped = np.clip(q_true, 1e-15, 1.0)
        raw = "inf" if q_true == 0 else f"{-math.log(q_true):.3f}"
        print(f"    q(true)={q_true:<8} loss={raw:<10} "
              f"clipped loss={-math.log(clipped):.3f}")
    print("    Implementations clip away from zero, for the same reason")
    print("    M1-L02 used Laplace smoothing.")


def evaluation() -> None:
    section("4. THE SECTION 6 EVALUATION, VERIFIED")
    tickets = [
        ("ticket 1", "billing", 0.85),
        ("ticket 2", "technical", 0.60),
        ("ticket 3", "billing", 0.95),
        ("ticket 4", "sales", 0.10),
        ("ticket 5", "account", 0.70),
    ]
    losses = np.array([-math.log(q) for _, _, q in tickets])
    mean_loss = float(losses.mean())
    perplexity = math.exp(mean_loss)

    print(f"  {'ticket':<12}{'true class':<14}{'q(true)':>9}{'loss':>9}"
          f"{'% of total':>12}")
    for (name, cls, q), loss in zip(tickets, losses):
        print(f"  {name:<12}{cls:<14}{q:>9.2f}{loss:>9.3f}"
              f"{loss / losses.sum() * 100:>11.1f}%")
    print(f"  {'':<12}{'':<14}{'total':>9}{losses.sum():>9.3f}")
    print()
    print(f"  mean cross-entropy = {losses.sum():.3f} / 5 = {mean_loss:.3f} nats")
    print(f"  perplexity         = exp({mean_loss:.3f}) = {perplexity:.2f}")
    print()
    print(f"  With 4 classes, a model that had learned NOTHING would score")
    print(f"  perplexity 4.00. This model is at {perplexity:.2f} - it has learned")
    print("  a lot, but it is far from confident.")
    print()
    worst = int(np.argmax(losses))
    print(f"  WHERE THE LOSS LIVES: {tickets[worst][0]} contributes "
          f"{losses[worst] / losses.sum() * 100:.0f}% of the total loss")
    print(f"  from {1 / len(tickets) * 100:.0f}% of the data.")
    print()
    print("  Accuracy cannot see this. If all five were correct by argmax,")
    print("  accuracy is 100% and tells you nothing. Cross-entropy points")
    print("  straight at ticket 4.")
    print()
    print("  Sensitivity check - fix ticket 4 from 0.10 to 0.50:")
    fixed = losses.copy()
    fixed[worst] = -math.log(0.50)
    print(f"    mean loss  {mean_loss:.3f} -> {fixed.mean():.3f}")
    print(f"    perplexity {perplexity:.2f} -> {math.exp(fixed.mean()):.2f}")
    print("    One example out of five moved the metric substantially.")


def perplexity_scale() -> None:
    section("5. PERPLEXITY - the effective number of choices")
    print(f"  {'cross-entropy (nats)':>22}{'perplexity':>14}   meaning")
    for h, note in ((0.0, "perfectly certain and correct"),
                    (math.log(2), "choosing between 2"),
                    (math.log(4), "choosing between 4"),
                    (math.log(10), "choosing between 10"),
                    (math.log(50), "choosing between 50"),
                    (math.log(100), "choosing between 100")):
        print(f"  {h:>22.3f}{math.exp(h):>14.2f}   {note}")
    print()
    print("  A uniform distribution over n outcomes has entropy ln(n), so its")
    print("  perplexity is exactly n. That is what makes the interpretation")
    print("  exact rather than a metaphor.")
    print()
    print("  Verifying it:")
    for n in (2, 4, 10, 50, 100):
        uniform = np.full(n, 1 / n)
        h = float(-np.sum(uniform * np.log(uniform)))
        print(f"    uniform over {n:>3}: entropy {h:.4f}, "
              f"perplexity {math.exp(h):.2f}")


def training_curve() -> None:
    section("6. WHAT 'TRAINED TO MINIMISE CROSS-ENTROPY' LOOKS LIKE")
    rng = np.random.default_rng(42)
    vocab = 50_000

    print(f"  Simulated language-model training. Vocabulary {vocab:,} tokens.")
    print()
    print(f"  {'step':>10}{'loss (nats)':>14}{'perplexity':>14}   what it means")

    # A plausible loss curve: starts at ln(vocab) (knows nothing), decays.
    start_loss = math.log(vocab)
    for step, loss in (
        (0, start_loss),
        (100, 7.2),
        (1_000, 5.4),
        (10_000, 4.1),
        (100_000, 3.2),
        (1_000_000, 2.6),
    ):
        ppl = math.exp(loss)
        if step == 0:
            note = "uniform guess - knows nothing"
        elif ppl > 1000:
            note = "learning token frequencies"
        elif ppl > 100:
            note = "learning common patterns"
        elif ppl > 20:
            note = "learning grammar and context"
        else:
            note = "strong next-token prediction"
        print(f"  {step:>10,}{loss:>14.3f}{ppl:>14,.0f}   {note}")
    print()
    print(f"  Step 0 loss = ln({vocab:,}) = {start_loss:.3f}, perplexity "
          f"{math.exp(start_loss):,.0f} - exactly the")
    print("  vocabulary size, because a uniform guess over the vocabulary is")
    print("  what 'knows nothing' means.")
    print()
    print("  IMPORTANT: this whole curve measures only NEXT-TOKEN PREDICTION.")
    print("  Not truth. Not helpfulness. A model at perplexity 13 predicts")
    print("  text well and may still be unhelpful, which is exactly why")
    print("  instruction tuning and preference optimisation exist (M4-L12,")
    print("  M4-L13). Perplexity is a training diagnostic, not a product")
    print("  metric.")


def main() -> None:
    print("=" * 74)
    print("LOGARITHMS, CROSS-ENTROPY AND PERPLEXITY")
    print("=" * 74)
    underflow()
    surprisal()
    cross_entropy_table()
    evaluation()
    perplexity_scale()
    training_curve()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
