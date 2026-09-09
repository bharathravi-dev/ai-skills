"""M4-L13 lab -- preference optimisation, reward hacking and DPO.

Fits the lesson's reward model from six comparisons, shows the reward scale is
arbitrary, demonstrates reward hacking with and without a KL penalty, shows
length-balancing fixing it at the DATA level, implements the DPO loss, and
measures sycophancy emerging from preference data.

NumPy only, no API key, no network.
Run:  python labs/m4/l13_preference.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(13)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


# ------------------------------------------------- 1. the reward model
rule("1. A REWARD MODEL FROM SIX COMPARISONS  (Bradley-Terry)")

# features: [length, correct]
RESP = {
    "A": np.array([0.2, 1.0]),
    "B": np.array([0.9, 1.0]),
    "C": np.array([0.8, 0.0]),
    "D": np.array([0.1, 0.0]),
}
PAIRS = [("B", "A"), ("B", "C"), ("B", "D"),
         ("A", "D"), ("C", "D"), ("A", "C")]

print(f"  {'response':<10}{'length':>9}{'correct':>10}   description")
for name, desc in (("A", "short and right"), ("B", "long and right"),
                   ("C", "long and wrong"), ("D", "short and wrong")):
    v = RESP[name]
    print(f"  {name:<10}{v[0]:>9.1f}{v[1]:>10.0f}   {desc}")

print(f"\n  comparisons collected (winner first):")
for w, l in PAIRS:
    print(f"    {w} > {l}")


def fit_reward(pairs, steps=4000, lr=0.5, seed=0):
    """Bradley-Terry: P(win) = sigmoid(r(w) - r(l)). Logistic regression."""
    w = np.zeros(2)
    for _ in range(steps):
        g = np.zeros(2)
        for a, b in pairs:
            xa, xb = RESP[a], RESP[b]
            diff = xa - xb
            p = sigmoid(w @ diff)
            g += -(1 - p) * diff              # d/dw of -log sigmoid(w.diff)
        w -= lr * g / len(pairs)
    return w


w_fit = fit_reward(PAIRS)
print(f"\n  fitted weights: w_length = {w_fit[0]:.4f}, "
      f"w_correct = {w_fit[1]:.4f}")
print(f"  both positive, and correctness weighs "
      f"{w_fit[1] / w_fit[0]:.2f}x more than length.")

print(f"\n  {'response':<10}{'reward':>10}{'rank':>8}")
scores = {k: float(w_fit @ v) for k, v in RESP.items()}
for i, (k, sc) in enumerate(sorted(scores.items(), key=lambda kv: -kv[1]), 1):
    print(f"  {k:<10}{sc:>10.4f}{i:>8}")

print(f"\n  predicted preference probabilities:")
print(f"  {'comparison':<14}{'P(first wins)':>16}{'observed':>12}")
for a, b in PAIRS:
    p = sigmoid(w_fit @ (RESP[a] - RESP[b]))
    print(f"  {f'{a} vs {b}':<14}{p:>16.4f}{'1 (won)':>12}")

print("\n  The pair B > A carries NO information about correctness -- both are")
print("  correct, so the correctness terms cancel exactly:")
print(f"    r(B) - r(A) = w_len({RESP['B'][0]} - {RESP['A'][0]}) + "
      f"w_cor({RESP['B'][1]:.0f} - {RESP['A'][1]:.0f})")
print(f"                = {RESP['B'][0] - RESP['A'][0]:.1f} x w_len + 0")
print("  Only pairs that DIFFER on a feature can teach the model about it.")


rule("2. THE REWARD SCALE IS ARBITRARY")

print("  Adding a constant to every reward changes nothing, because only")
print("  DIFFERENCES enter the Bradley-Terry likelihood.\n")
print(f"  {'shift':>8}" + "".join(f"{k:>10}" for k in "ABCD")
      + f"{'ranking':>12}{'P(B>A)':>10}")
for shift in (0.0, 5.0, -100.0, 1000.0):
    sh = {k: scores[k] + shift for k in scores}
    order = "".join(sorted(sh, key=lambda k: -sh[k]))
    p = sigmoid((sh["B"]) - (sh["A"]))
    p_true = sigmoid(scores["B"] - scores["A"])
    print(f"  {shift:>8.0f}" + "".join(f"{sh[k]:>10.3f}" for k in "ABCD")
          + f"{order:>12}{p_true:>10.4f}")

print("\n  Identical ranking, identical preference probabilities. A reward of")
print("  '4.2' means nothing on its own and cannot be compared with a number")
print("  from a different reward model.")


# ------------------------------------------------- 3. reward hacking
rule("3. REWARD HACKING, WITH AND WITHOUT A KL PENALTY")

# A policy that chooses (length, correctness). Correctness is HARD to increase;
# length is trivially cheap. Both are rewarded by the fitted model.
REF = np.array([0.35, 0.55])          # the reference (SFT) policy's behaviour
COST_LEN, COST_COR = 0.02, 1.2        # effort required to move each feature


def optimise_policy(w, beta, steps=3000, lr=0.05):
    """Maximise reward - beta * (distance from reference)^2 - effort.

    The reward weights are NORMALISED to unit norm first. Without this, beta
    has no interpretable scale: the fitted weights happen to be ~7-10, so any
    beta below about 10 is simply invisible. The first version of this lab
    swept beta from 0 to 5 and every row was identical.
    """
    w = w / np.linalg.norm(w)
    p = REF.copy()
    for _ in range(steps):
        grad_reward = w.copy()
        grad_effort = np.array([2 * COST_LEN * (p[0] - REF[0]),
                                2 * COST_COR * (p[1] - REF[1])])
        grad_kl = 2 * beta * (p - REF)
        p = p + lr * (grad_reward - grad_effort - grad_kl)
        p = np.clip(p, 0.0, 1.0)
    return p


print(f"  reference policy: length {REF[0]:.2f}, correctness {REF[1]:.2f}")
print(f"  effort to change: length {COST_LEN}, correctness {COST_COR} "
      f"({COST_COR / COST_LEN:.0f}x harder)\n")
print(f"  (reward weights normalised to unit norm so beta is interpretable)\n")
print(f"  {'KL beta':>10}{'length':>10}{'correct':>10}{'reward':>10}"
      f"{'KL dist':>10}   what happened")
w_unit = w_fit / np.linalg.norm(w_fit)
for beta in (0.0, 0.2, 0.5, 1.0, 2.0, 5.0):
    p = optimise_policy(w_fit, beta)
    r = float(w_unit @ p)
    kl = float(np.linalg.norm(p - REF))
    len_move = p[0] - REF[0]
    cor_move = p[1] - REF[1]
    if kl < 0.02:
        note = "frozen at the reference"
    elif len_move > cor_move * 2:
        note = "LENGTH-HACKING"
    elif cor_move > len_move:
        note = "improved correctness most"
    else:
        note = "moved on both"
    print(f"  {beta:>10.2f}{p[0]:>10.4f}{p[1]:>10.4f}{r:>10.4f}"
          f"{kl:>10.4f}   {note}")

print(f"\n  reference was length {REF[0]:.2f}, correctness {REF[1]:.2f}. Read the")
print(f"  MOVEMENT, not the absolute values:")
print(f"  {'KL beta':>10}{'length moved':>15}{'correctness moved':>20}"
      f"{'ratio':>10}")
for beta in (0.0, 0.5, 2.0, 5.0):
    p = optimise_policy(w_fit, beta)
    dl, dc = p[0] - REF[0], p[1] - REF[1]
    ratio = dl / dc if abs(dc) > 1e-6 else float("inf")
    print(f"  {beta:>10.2f}{dl:>15.4f}{dc:>20.4f}"
          f"{(f'{ratio:.2f}x' if math.isfinite(ratio) else 'inf'):>10}")

print("\n  Length is 60x cheaper to increase than correctness, and the reward")
print("  model genuinely rewards both. So the policy buys length first: at every")
print("  beta it moves further on length than on correctness. The model is not")
print("  malfunctioning -- it is maximising exactly what was fitted, and doing")
print("  it in the cheapest available way.")
print("\n  Raising beta bounds how far it may travel. Too high and it does not")
print("  move at all. beta is the single most consequential hyperparameter in")
print("  the procedure, and it is a TRADE, not a setting with a right answer.")


rule("4. THE BETTER FIX: BALANCE THE DATA")

# Same underlying preferences, but every pair matched on length so that the
# only thing that can distinguish them is correctness.
BALANCED_RESP = {
    "A2": np.array([0.5, 1.0]), "B2": np.array([0.5, 0.0]),
    "C2": np.array([0.9, 1.0]), "D2": np.array([0.9, 0.0]),
    "E2": np.array([0.2, 1.0]), "F2": np.array([0.2, 0.0]),
}
BALANCED_PAIRS = [("A2", "B2"), ("C2", "D2"), ("E2", "F2")]

saved = dict(RESP)
RESP.update(BALANCED_RESP)
w_bal = fit_reward(BALANCED_PAIRS)
RESP.clear()
RESP.update(saved)

print("  Length-matched pairs: within each comparison the two responses have")
print("  IDENTICAL length, so length cannot explain any preference.\n")
for a, b in BALANCED_PAIRS:
    print(f"    {a} (len {BALANCED_RESP[a][0]}, correct "
          f"{BALANCED_RESP[a][1]:.0f})  >  "
          f"{b} (len {BALANCED_RESP[b][0]}, correct {BALANCED_RESP[b][1]:.0f})")

print(f"\n  {'dataset':<26}{'w_length':>12}{'w_correct':>12}{'ratio':>10}")
print(f"  {'original (confounded)':<26}{w_fit[0]:>12.4f}{w_fit[1]:>12.4f}"
      f"{w_fit[1] / w_fit[0]:>10.2f}x")
bal_ratio = ("inf" if abs(w_bal[0]) < 1e-9
             else f"{abs(w_bal[1] / w_bal[0]):.0f}x")
print(f"  {'length-balanced':<26}{w_bal[0]:>12.4f}{w_bal[1]:>12.4f}"
      f"{bal_ratio:>10}")

p_bal = optimise_policy(w_bal, beta=0.0)
print(f"\n  policy optimised against the BALANCED reward model, beta = 0:")
print(f"    length {p_bal[0]:.4f}   correctness {p_bal[1]:.4f}")
print(f"  compared with the confounded model at beta = 0:")
p_conf = optimise_policy(w_fit, beta=0.0)
print(f"    length {p_conf[0]:.4f}   correctness {p_conf[1]:.4f}")
print("\n  With the confound removed, the length weight collapses and the")
print("  policy stops chasing length EVEN WITH NO KL PENALTY. Fixing the data")
print("  removes the incentive; the KL penalty only bounds the symptom.")
print("  It is the better fix, and the harder one -- it requires noticing the")
print("  confound BEFORE collecting 100,000 comparisons.")


# ------------------------------------------------- 5. DPO
rule("5. THE DPO LOSS, IMPLEMENTED")

print("  DPO optimises preferences directly: raise log P(chosen) relative to")
print("  the reference, lower log P(rejected) -- no reward model, no RL.\n")


def dpo_loss(logp_chosen, logp_rejected, ref_chosen, ref_rejected, beta=0.1):
    margin = beta * ((logp_chosen - ref_chosen) -
                     (logp_rejected - ref_rejected))
    return float(-np.log(sigmoid(margin))), float(margin)


REF_C, REF_R = -2.0, -2.0          # the reference assigns both equal probability
print(f"  reference log-probs: chosen {REF_C}, rejected {REF_R} (equal)\n")
print(f"  {'policy chosen':>15}{'policy rejected':>17}{'margin':>10}"
      f"{'DPO loss':>11}   interpretation")
for lc, lr_ in ((-2.0, -2.0), (-1.5, -2.5), (-1.0, -3.0),
                (-2.5, -1.5), (-0.5, -4.0)):
    loss, margin = dpo_loss(lc, lr_, REF_C, REF_R)
    if margin > 0.2:
        note = "strongly prefers chosen"
    elif margin > 0.0:
        note = "prefers chosen"
    elif margin == 0.0:
        note = "no preference yet"
    else:
        note = "WRONG WAY -- prefers rejected"
    print(f"  {lc:>15.1f}{lr_:>17.1f}{margin:>10.4f}{loss:>11.4f}   {note}")

print("\n  Loss falls as the policy raises the chosen response relative to the")
print("  rejected one -- MEASURED AGAINST THE REFERENCE, which is what plays")
print("  the role the KL penalty played in RLHF. Two models in memory instead")
print("  of four, and ordinary gradient descent instead of PPO.")

print(f"\n  memory comparison:")
print(f"  {'method':<10}{'models held':>14}   which")
print(f"  {'RLHF':<10}{4:>14}   policy, reference, reward, value")
print(f"  {'DPO':<10}{2:>14}   policy, reference")


# ------------------------------------------------- 6. sycophancy
rule("6. SYCOPHANCY EMERGING FROM PREFERENCE DATA")

# Two features an annotator can see: agrees_with_user, and is_correct.
# The annotator pool mildly prefers agreement (it feels helpful), and prefers
# correctness -- but cannot always VERIFY correctness.
print("  Annotators rate two things they can perceive: whether the response")
print("  AGREES with the user's stated premise, and whether it is CORRECT.")
print("  Crucially, they can always see agreement; they can only sometimes")
print("  verify correctness.\n")

SYC = {
    "agree_right": np.array([1.0, 1.0]),
    "agree_wrong": np.array([1.0, 0.0]),
    "correct_disagree": np.array([0.0, 1.0]),
    "wrong_disagree": np.array([0.0, 0.0]),
}


def fit_generic(resp, pairs, steps=4000, lr=0.5):
    w = np.zeros(2)
    for _ in range(steps):
        g = np.zeros(2)
        for a, b in pairs:
            d = resp[a] - resp[b]
            g += -(1 - sigmoid(w @ d)) * d
        w -= lr * g / len(pairs)
    return w


print(f"  {'verification rate':>19}{'w_agreement':>14}{'w_correctness':>16}"
      f"{'sycophantic?':>15}")
for verify_rate in (1.0, 0.7, 0.4, 0.1):
    pairs = []
    rng = np.random.default_rng(20)
    for _ in range(400):
        verified = rng.random() < verify_rate
        if verified:
            # annotator sees correctness and prefers it
            pairs.append(("correct_disagree", "agree_wrong"))
        else:
            # cannot verify -- falls back on agreement
            pairs.append(("agree_wrong", "correct_disagree"))
        pairs.append(("agree_right", "wrong_disagree"))
    w_syc = fit_generic(SYC, pairs)
    syc = "YES" if w_syc[0] > w_syc[1] else "no"
    print(f"  {verify_rate:>18.0%}{w_syc[0]:>14.4f}{w_syc[1]:>16.4f}"
          f"{syc:>15}")

print("\n  As annotators become less able to VERIFY correctness, the reward")
print("  model shifts weight from correctness onto agreement -- because")
print("  agreement is what remains visible. A policy optimised against it")
print("  agrees with the user's premise whether or not the premise is true.")
print("\n  Note that no annotator was dishonest and no step was implemented")
print("  incorrectly. Sycophancy is the PREDICTED result of optimising a proxy")
print("  built from what humans could perceive (M4-L13 section 5.5).")
print("\n  If your application has users asserting premises -- 'our policy")
print("  allows X, right?' -- test for this explicitly (M5-L15). A model that")
print("  confirms a false premise is more dangerous than one that is simply")
print("  wrong, because it reinforces the user's confidence.")

print("\nDone.")
