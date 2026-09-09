"""M4-L07 lab -- attention: the core idea, verified.

Reproduces the lesson's hand-worked example, trains the same head so the
weights sharpen, proves permutation invariance, measures softmax saturation
with and without the sqrt(d_k) scaling, demonstrates query/key asymmetry, and
trains a two-head model in which the heads must specialise.

NumPy only, no API key, no network.
Run:  python labs/m4/l07_attention.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(7)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def attention(X, Wq, Wk, Wv, scale=True, mask=None):
    """Scaled dot-product attention. Returns (output, weights)."""
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    d_k = Q.shape[-1]
    scores = Q @ K.T
    if scale:
        scores = scores / math.sqrt(d_k)
    if mask is not None:
        scores = np.where(mask, -1e9, scores)
    W = softmax(scores, axis=-1)
    return W @ V, W


# ------------------------------------------------- 1. the worked example
rule("1. THE WORKED EXAMPLE, VERIFIED  (4 tokens, d_k = 2)")

TOKENS = ["the", "cat", "sat", "it"]
X = np.array([
    [0.1, 0.0],     # the
    [0.9, 0.2],     # cat
    [0.2, 0.8],     # sat
    [0.3, 0.1],     # it
])
Wq = np.array([[1.0, 0.0], [0.0, 0.5]])
Wk = np.array([[1.0, 0.0], [0.0, 0.5]])
Wv = np.array([[1.0, 0.0], [0.0, 1.0]])

Q, K, V = X @ Wq, X @ Wk, X @ Wv
print(f"  {'token':<7}{'x':<16}{'q':<16}{'k':<16}{'v':<16}")
for t, x, q, k, v in zip(TOKENS, X, Q, K, V):
    print(f"  {t:<7}{str(np.round(x, 3)):<16}{str(np.round(q, 3)):<16}"
          f"{str(np.round(k, 3)):<16}{str(np.round(v, 3)):<16}")

out, W = attention(X, Wq, Wk, Wv)
i_it = TOKENS.index("it")
raw = Q[i_it] @ K.T
scaled = raw / math.sqrt(2)

print(f"\n  scores for the query at 'it'  (sqrt(d_k) = {math.sqrt(2):.4f}):")
print(f"  {'vs':<7}{'q.k':>10}{'/sqrt(d_k)':>14}{'exp':>10}{'weight':>10}")
for t, r, sc, w in zip(TOKENS, raw, scaled, W[i_it]):
    print(f"  {t:<7}{r:>10.4f}{sc:>14.4f}{math.exp(sc - scaled.max()):>10.4f}"
          f"{w:>10.4f}")
print(f"  {'sum':<7}{'':>10}{'':>14}{'':>10}{W[i_it].sum():>10.4f}")

print(f"\n  output for 'it' = {np.round(out[i_it], 4)}")
print(f"  highest weight  : {TOKENS[int(np.argmax(W[i_it]))]!r} "
      f"({W[i_it].max():.4f})  -- correct")
print(f"  weight spread   : {W[i_it].min():.4f} to {W[i_it].max():.4f} "
      f"= {W[i_it].max() - W[i_it].min():.4f}")
print(f"  score spread    : {scaled.min():.4f} to {scaled.max():.4f} "
      f"= {scaled.max() - scaled.min():.4f}")
print("\n  NEARLY UNIFORM. The right token wins, but only just. exp() of numbers")
print("  that close is nearly constant, so softmax cannot separate them.")
print("  This is what an UNTRAINED attention head looks like.")

print("\n  the full attention matrix (each ROW sums to 1):")
print(f"  {'':>7}" + "".join(f"{t:>9}" for t in TOKENS) + f"{'sum':>9}")
for t, row in zip(TOKENS, W):
    print(f"  {t:>7}" + "".join(f"{w:>9.4f}" for w in row) + f"{row.sum():>9.4f}")


# ------------------------------------------------- 2. training sharpens it
rule("2. TRAINING SHARPENS THE WEIGHTS  ('it' must attend to 'cat')")

TARGET = TOKENS.index("cat")


def train_head(steps=4000, lr=0.6, seed=0):
    r = np.random.default_rng(seed)
    wq = Wq + r.normal(0, 0.05, size=Wq.shape)
    wk = Wk + r.normal(0, 0.05, size=Wk.shape)
    trace = []
    for step in range(steps + 1):
        q, k = X @ wq, X @ wk
        scores = (q @ k.T) / math.sqrt(2)
        w = softmax(scores, axis=-1)
        trace.append(float(w[i_it, TARGET]))
        if step == steps:
            break
        # maximise log w[it, cat]  ->  d(loss)/d(scores[it]) = w - onehot
        d_scores = np.zeros_like(scores)
        d_scores[i_it] = w[i_it]
        d_scores[i_it, TARGET] -= 1.0
        d_scores /= math.sqrt(2)
        dq = d_scores @ k
        dk = d_scores.T @ q
        wq -= lr * (X.T @ dq)
        wk -= lr * (X.T @ dk)
    return wq, wk, trace


wq_t, wk_t, trace = train_head()
print(f"  {'step':>8}{'weight on cat':>16}{'profile':>10}")
for step in (0, 10, 50, 200, 1000, 4000):
    w = trace[min(step, len(trace) - 1)]
    print(f"  {step:>8}{w:>16.4f}   |{'#' * int(w * 40)}")

_, W_trained = attention(X, wq_t, wk_t, Wv)
print(f"\n  final attention row for 'it':")
print(f"  {'':>7}" + "".join(f"{t:>10}" for t in TOKENS))
print(f"  {'it':>7}" + "".join(f"{w:>10.4f}" for w in W_trained[i_it]))
q_t, k_t = X @ wq_t, X @ wk_t
sc_t = (q_t[i_it] @ k_t.T) / math.sqrt(2)
print(f"\n  score spread went {scaled.max() - scaled.min():.4f} -> "
      f"{sc_t.max() - sc_t.min():.4f}")
print(f"  weight on 'cat'  went {trace[0]:.4f} -> {trace[-1]:.4f}")
print("\n  Training did NOT teach the model to average. It learned projections")
print("  that SEPARATE the scores, and softmax turned that separation into a")
print("  sharp weight. Sharpness is a consequence, not an objective.")


# ------------------------------------------------- 3. permutation invariance
rule("3. ATTENTION IS PERMUTATION-INVARIANT  (why positional encoding exists)")

perm = np.array([2, 0, 3, 1])
out_orig, _ = attention(X, Wq, Wk, Wv)
out_perm, _ = attention(X[perm], Wq, Wk, Wv)

print(f"  original order : {TOKENS}")
print(f"  permuted order : {[TOKENS[i] for i in perm]}\n")
print(f"  {'token':<8}{'output (original)':<24}{'output (permuted input)':<26}")
for j, i in enumerate(perm):
    print(f"  {TOKENS[i]:<8}{str(np.round(out_orig[i], 6)):<24}"
          f"{str(np.round(out_perm[j], 6)):<26}")

print(f"\n  attention(shuffle(X)) == shuffle(attention(X)) ? "
      f"{np.allclose(out_perm, out_orig[perm])}")
print(f"  max difference: {np.abs(out_perm - out_orig[perm]).max():.2e}")
print("\n  Every output vector is IDENTICAL, merely reordered. 'dog bites man'")
print("  and 'man bites dog' are the same computation to this mechanism.")

print("\n  now add positional encodings and repeat:")
POS = np.array([[0.0, 0.0], [0.3, -0.3], [0.6, -0.6], [0.9, -0.9]])
Xp = X + POS
outp_orig, _ = attention(Xp, Wq, Wk, Wv)
outp_perm, _ = attention(X[perm] + POS, Wq, Wk, Wv)
print(f"    invariance still holds? {np.allclose(outp_perm, outp_orig[perm])}")
print(f"    max difference: {np.abs(outp_perm - outp_orig[perm]).max():.4f}")
print("\n  Broken, as required. Positional encoding is not an enhancement --")
print("  without it the model is a bag of words (M4-L09).")


# ------------------------------------------------- 4. the sqrt(d_k) scaling
rule("4. WHY DIVIDE BY sqrt(d_k)  (saturation and the gradient)")

T = 16
print(f"  {T} random tokens, unit-variance components\n")
print(f"  {'d_k':>6}{'score sd':>11}{'max weight':>13}{'entropy':>10}"
      f"{'mean softmax grad':>20}   scaled?")


def diagnose(d_k, scale):
    x = RNG.normal(0, 1, size=(T, d_k))
    wq = RNG.normal(0, 1 / math.sqrt(d_k), size=(d_k, d_k))
    wk = RNG.normal(0, 1 / math.sqrt(d_k), size=(d_k, d_k))
    q, k = x @ wq, x @ wk
    scores = q @ k.T
    if scale:
        scores = scores / math.sqrt(d_k)
    w = softmax(scores, axis=-1)
    # Gradient of each softmax output wrt its own input: w(1-w). Take the
    # MEAN, not the max -- a saturated row still contains a few mid-range
    # entries, so the max hides the collapse entirely. (The first version of
    # this lab used max and showed no effect at d_k=64 or 256.)
    grad = float((w * (1 - w)).mean())
    ent = float(-(w * np.log(np.clip(w, 1e-12, None))).sum(axis=-1).mean())
    return float(scores.std()), float(w.max()), ent, grad


rows = {}
for d_k in (8, 64, 256, 1024):
    for scale in (False, True):
        sd, mx, ent, grad = diagnose(d_k, scale)
        rows[(d_k, scale)] = (sd, mx, ent, grad)
        print(f"  {d_k:>6}{sd:>11.3f}{mx:>13.4f}{ent:>10.4f}{grad:>20.2e}"
              f"   {'yes' if scale else 'NO':>7}")

print(f"\n  uniform entropy for {T} positions = ln({T}) = {math.log(T):.4f}")
# Reuse the values printed above -- re-sampling here would print different
# numbers from the table immediately preceding, which is confusing and wrong.
g_uns_lo, g_uns_hi = rows[(8, False)][3], rows[(1024, False)][3]
g_sc_lo, g_sc_hi = rows[(8, True)][3], rows[(1024, True)][3]
print(f"\n  gradient collapse, unscaled: {g_uns_lo:.2e} at d_k=8 -> "
      f"{g_uns_hi:.2e} at d_k=1024")
print(f"    a {g_uns_lo / max(g_uns_hi, 1e-30):,.0f}x reduction")
print(f"  scaled                     : {g_sc_lo:.2e} -> {g_sc_hi:.2e}")
print(f"    a {g_sc_lo / max(g_sc_hi, 1e-30):.2f}x change -- "
      f"essentially constant")
print("\n  Unscaled, score standard deviation grows with sqrt(d_k), so at large")
print("  d_k one weight approaches 1.0, entropy collapses toward 0, and the")
print("  mean softmax gradient w(1-w) goes to zero -- training stalls (M3-L10).")
print("  Scaled, the statistics are roughly CONSTANT across four orders of")
print("  magnitude in d_k. That is what the divisor buys.")


# ------------------------------------------------- 5. query/key asymmetry
rule("5. WHY QUERY AND KEY MUST BE SEPARATE PROJECTIONS")

# Two tokens: a verb that seeks a subject, and a noun that is one.
x_verb = np.array([1.0, 0.0, 0.0, 0.0])
x_noun = np.array([0.0, 1.0, 0.0, 0.0])
Xa = np.stack([x_verb, x_noun])
NAMES = ["verb", "noun"]

print("  GOAL: 'verb' should attend strongly to 'noun', while 'noun' attends")
print("  only weakly to 'verb'. An asymmetric relationship -- the normal case")
print("  in language.\n")

# Separate Q and K: query maps verb -> "looking for noun-ness"
Wq_a = np.array([[0., 1., 0., 0.], [0., 0., 0., 0.],
                 [0., 0., 0., 0.], [0., 0., 0., 0.]])
Wk_a = np.eye(4)
Wv_a = np.eye(4)
_, W_sep = attention(Xa, Wq_a * 6, Wk_a, Wv_a)

# Shared projection: q and k are the same function of x
Wshared = np.eye(4)
_, W_shared = attention(Xa, Wshared * 6, Wshared, Wv_a)

print(f"  {'':>8}{'separate Q,K':>26}{'shared projection':>26}")
print(f"  {'':>8}{'-> verb':>13}{'-> noun':>13}{'-> verb':>13}{'-> noun':>13}")
for i, n in enumerate(NAMES):
    print(f"  {n:>8}{W_sep[i, 0]:>13.4f}{W_sep[i, 1]:>13.4f}"
          f"{W_shared[i, 0]:>13.4f}{W_shared[i, 1]:>13.4f}")

asym_sep = abs(W_sep[0, 1] - W_sep[1, 0])
asym_shared = abs(W_shared[0, 1] - W_shared[1, 0])
print(f"\n  asymmetry |w(verb->noun) - w(noun->verb)|:")
print(f"    separate Q,K      : {asym_sep:.4f}")
print(f"    shared projection : {asym_shared:.4f}")
print("\n  With a SHARED projection the score matrix is q_i . q_j, which is")
print("  symmetric by construction: score(i,j) == score(j,i) ALWAYS. It can")
print("  never express 'A looks at B but B does not look at A'. Separate Q and")
print("  K make the score matrix asymmetric, which is why there are two.")


# ------------------------------------------------- 6. multi-head
rule("6. MULTI-HEAD: SEVERAL RELATIONSHIPS FOR THE SAME PARAMETER BUDGET")

D_MODEL = 64
print(f"  d_model = {D_MODEL}\n")
print(f"  {'heads':>7}{'d_head':>9}{'params/head':>14}{'total Q,K,V params':>21}")
for h in (1, 2, 4, 8, 16):
    d_head = D_MODEL // h
    per = 3 * D_MODEL * d_head
    print(f"  {h:>7}{d_head:>9}{per:>14,}{per * h:>21,}")
print("\n  IDENTICAL total. 8 heads of 64 dims cost exactly what 1 head of 512")
print("  costs. You get several relationships for the same price -- at the cost")
print("  of each being lower-dimensional.")

# A task with two distinct relationships, so two heads must specialise.
SEQ = 6
D2 = 8
print(f"\n  training 2 heads on a task with TWO relationships:")
print(f"    head must learn: 'attend to the PREVIOUS token'")
print(f"    head must learn: 'attend to the FIRST token'")

x2 = RNG.normal(0, 1, size=(SEQ, D2))
pos_prev = np.array([[1.0 if j == max(i - 1, 0) else 0.0 for j in range(SEQ)]
                     for i in range(SEQ)])
pos_first = np.array([[1.0 if j == 0 else 0.0 for j in range(SEQ)]
                      for i in range(SEQ)])
TARGETS = [pos_prev, pos_first]

heads = []
for hi, target in enumerate(TARGETS):
    wq = RNG.normal(0, 0.3, size=(D2, D2))
    wk = RNG.normal(0, 0.3, size=(D2, D2))
    for _ in range(3000):
        q, k = x2 @ wq, x2 @ wk
        sc = (q @ k.T) / math.sqrt(D2)
        w = softmax(sc, axis=-1)
        d_sc = (w - target) / math.sqrt(D2) / SEQ
        wq -= 0.5 * (x2.T @ (d_sc @ k))
        wk -= 0.5 * (x2.T @ (d_sc.T @ q))
    _, wfin = attention(x2, wq, wk, np.eye(D2))
    heads.append(wfin)

for hi, (wfin, target, name) in enumerate(
        zip(heads, TARGETS, ["previous-token", "first-token"])):
    match = float((wfin * target).sum() / SEQ)
    print(f"\n    head {hi} ({name}): mean weight on its target = {match:.4f}")
    print(f"      attention matrix (rows = query position):")
    for i, row in enumerate(wfin):
        bars = "".join(f"{w:>7.3f}" for w in row)
        print(f"        pos {i} |{bars}")

overlap = float((heads[0] * heads[1]).sum() / SEQ)
print(f"\n  overlap between the two heads' attention: {overlap:.4f}")
print("  The heads learned genuinely DIFFERENT patterns -- one a diagonal band,")
print("  one a single column. A single head could express only one of them.")
print("  That is what multi-head buys.")

print("\n  A CAUTION on reading these matrices: they show which positions fed a")
print("  weighted average in ONE head at ONE layer. They are not importance,")
print("  not causation, and not the whole path -- residual connections carry")
print("  information around attention entirely (M4-L07 section 5.6).")

print("\nDone.")
