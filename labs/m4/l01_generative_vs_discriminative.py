"""M4-L01 lab -- generative vs discriminative, on the same data.

Trains two models on ONE small synthetic corpus:

  * a discriminative classifier (logistic regression over character counts),
  * a generative character-level model (next-character probabilities),

then shows what each can and cannot do, and samples from the generative one at
several temperatures to make "sampling from a distribution" concrete.

No API key, no network, no downloads. Run:
    python labs/m4/l01_generative_vs_discriminative.py
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np

RNG = np.random.default_rng(4)


def rule(title: str) -> None:
    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


# ------------------------------------------------------------------ corpus
# Synthetic support messages. Two classes, deliberately small so the whole
# thing is inspectable.
BILLING = [
    "my card was charged twice for the same order",
    "i was billed again after cancelling my plan",
    "the invoice amount does not match my order",
    "please refund the duplicate payment on my card",
    "why was my card charged before the trial ended",
    "i need a receipt for the payment i made",
    "the subscription price changed without notice",
    "my refund has not arrived after two weeks",
    "i was charged in the wrong currency",
    "cancel my plan and refund the last invoice",
]
TECHNICAL = [
    "the app crashes when i open the reports page",
    "i cannot log in the page just reloads forever",
    "uploading a file fails with a server error",
    "the dashboard shows no data since this morning",
    "export to csv produces an empty file",
    "the search box returns nothing for any query",
    "notifications stopped arriving on my phone",
    "the page loads very slowly on every browser",
    "i get an error code when saving my settings",
    "the integration disconnects after a few minutes",
]
CORPUS = BILLING + TECHNICAL
LABELS = np.array([1] * len(BILLING) + [0] * len(TECHNICAL))   # 1 = billing


# ------------------------------------------- 1. the discriminative model
rule("1. A DISCRIMINATIVE MODEL  (logistic regression over word presence)")

vocab = sorted({w for msg in CORPUS for w in msg.split()})
vocab_index = {w: i for i, w in enumerate(vocab)}


def featurise(text: str) -> np.ndarray:
    vec = np.zeros(len(vocab))
    for w in text.split():
        if w in vocab_index:
            vec[vocab_index[w]] = 1.0
    return vec


X = np.array([featurise(m) for m in CORPUS])
y = LABELS.astype(float)

w = np.zeros(len(vocab))
b = 0.0
for _ in range(3000):
    p = sigmoid(X @ w + b)
    err = (p - y) / len(y)
    w -= 0.5 * (X.T @ err + 1e-3 * w)
    b -= 0.5 * err.sum()

train_acc = ((sigmoid(X @ w + b) >= 0.5).astype(int) == LABELS).mean()
print(f"  vocabulary   : {len(vocab)} words")
print(f"  parameters   : {len(w) + 1}")
print(f"  training acc : {train_acc:.4f}   (20 examples -- this is memorisation,")
print(f"                 not evidence of anything; see M3-L13)")

print("\n  strongest learned weights:")
order = np.argsort(-np.abs(w))[:8]
for j in order:
    side = "billing" if w[j] > 0 else "technical"
    print(f"    {vocab[j]:<16}{w[j]:>+8.3f}   -> {side}")

held_out = [
    ("i want a refund for the double charge", 1),
    ("the export button throws an error", 0),
]
print("\n  classifying two unseen messages:")
for text, truth in held_out:
    prob = float(sigmoid(featurise(text) @ w + b))
    label = "billing" if prob >= 0.5 else "technical"
    mark = "correct" if (prob >= 0.5) == bool(truth) else "WRONG"
    print(f"    {text!r}")
    print(f"      P(billing) = {prob:.4f} -> {label}   ({mark})")

print("\n  Now ask it to WRITE a support message:")
print("    ... there is no operation that does this.")
print("    The model maps text -> one number. It has no notion of what text")
print("    looks like, only of where the boundary between two classes lies.")
print("    No amount of scaling changes that: it never modelled P(text).")


# --------------------------------------------- 2. the generative model
rule("2. A GENERATIVE MODEL  (character-level, next-character distribution)")

START, END = "^", "$"
counts: dict[str, Counter] = defaultdict(Counter)
for msg in CORPUS:
    seq = START + msg + END
    for prev, nxt in zip(seq, seq[1:]):
        counts[prev][nxt] += 1

chars = sorted({c for msg in CORPUS for c in msg} | {START, END})
print(f"  distinct characters : {len(chars)}")
print(f"  contexts modelled   : {len(counts)}")
print(f"  transitions counted : {sum(sum(c.values()) for c in counts.values()):,}")

print("\n  What the model actually stores -- P(next | 'c'):")
row = counts["c"]
total = sum(row.values())
for ch, n in row.most_common(6):
    bar = "#" * int(40 * n / total)
    print(f"    {ch!r:>5} {n / total:>7.3f}  {bar}")

print("\n  and P(next | 'r'):")
row = counts["r"]
total = sum(row.values())
for ch, n in row.most_common(6):
    bar = "#" * int(40 * n / total)
    print(f"    {ch!r:>5} {n / total:>7.3f}  {bar}")

print("\n  THIS is the whole model: a probability distribution over what comes")
print("  next. Generation is: sample from it, append, repeat.")


def generate(temperature: float, max_len: int = 90, seed: int = 0) -> str:
    rng = np.random.default_rng(seed)
    out, cur = [], START
    for _ in range(max_len):
        row = counts.get(cur)
        if not row:
            break
        options = list(row)
        freqs = np.array([row[o] for o in options], dtype=float)
        if temperature <= 0:                       # greedy
            nxt = options[int(np.argmax(freqs))]
        else:
            logits = np.log(freqs) / temperature
            logits -= logits.max()                 # M3-L09 section 5.5
            probs = np.exp(logits)
            probs /= probs.sum()
            nxt = options[int(rng.choice(len(options), p=probs))]
        if nxt == END:
            break
        out.append(nxt)
        cur = nxt
    return "".join(out)


rule("3. SAMPLING AT DIFFERENT TEMPERATURES  (the same model, every time)")

for temp in (0.0, 0.3, 0.7, 1.0, 1.5, 2.5):
    label = "greedy" if temp == 0 else f"T={temp}"
    print(f"\n  {label}")
    for s in range(3):
        text = generate(temp, seed=s)
        print(f"    {text!r}")

print("\n  Greedy picks the single most likely character every time, so it is")
print("  deterministic -- and it loops, because the most likely continuation of")
print("  a common pattern is that same pattern again. Raising the temperature")
print("  flattens the distribution (M3-L09 section 5.6) and buys variety at the")
print("  cost of coherence. At T=2.5 it is close to uniform over characters.")


# ------------------------------------ 4. the generative model classifying
rule("4. THE GENERATIVE MODEL CAN CLASSIFY -- THE DISCRIMINATIVE ONE CANNOT GENERATE")


def class_model(messages):
    """A separate character model per class, for scoring."""
    c: dict[str, Counter] = defaultdict(Counter)
    for msg in messages:
        seq = START + msg + END
        for prev, nxt in zip(seq, seq[1:]):
            c[prev][nxt] += 1
    return c


models = {"billing": class_model(BILLING), "technical": class_model(TECHNICAL)}
alphabet = len(chars)


def log_prob(model, text: str) -> float:
    """Total log probability of `text` under `model`, with add-1 smoothing."""
    total = 0.0
    seq = START + text + END
    for prev, nxt in zip(seq, seq[1:]):
        row = model.get(prev, Counter())
        total += math.log((row[nxt] + 1) / (sum(row.values()) + alphabet))
    return total


print("  Scoring each unseen message under BOTH class models, then picking the")
print("  higher. This is generative classification -- it works because the model")
print("  knows what each class's text LOOKS like.\n")
print(f"  {'message':<40}{'log P(billing)':>16}{'log P(tech)':>14}{'verdict':>12}")
for text, truth in held_out:
    lb = log_prob(models["billing"], text)
    lt = log_prob(models["technical"], text)
    pick = "billing" if lb > lt else "technical"
    mark = "correct" if (pick == "billing") == bool(truth) else "WRONG"
    short = text if len(text) <= 38 else text[:35] + "..."
    print(f"  {short:<40}{lb:>16.1f}{lt:>14.1f}{pick:>12}  {mark}")

print("\n  The generative model did the discriminative model's job.")
print("  The reverse is impossible: P(class | text) contains no information")
print("  about what text looks like, so there is nothing to sample from.")
print("  That asymmetry IS the difference between the two kinds of model.")


rule("5. WHAT NEITHER MODEL HAS")

print("  Both models were built from 20 sentences and know nothing else.")
print("  Ask either about a fact and there is no mechanism to answer:\n")
print("    'What is our refund window?'   -> no stored records to consult")
print("    'What is 847 * 23?'            -> no arithmetic, only character")
print("                                      or word statistics")
print("    'What happened yesterday?'     -> the corpus is frozen\n")
print("  Scaling these to a trillion tokens changes the QUALITY of the")
print("  continuation enormously. It does not change the KIND of thing being")
print("  computed: still P(next | previous), still no records, still frozen.")
print("  That is why M4-L01 section 5.6 lists what a foundation model is not,")
print("  and why Modules 7 and 8 exist.")

print("\nDone.")
