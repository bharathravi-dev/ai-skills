"""M4-L04 lab -- embeddings, static and contextual.

Reproduces the lesson's worked example exactly, trains a small embedding table
from random initialisation so structure can be watched emerging, sizes real
embedding matrices, compares pooling strategies including the padding bug, and
demonstrates anisotropy inflating cosine similarity.

NumPy only. Run:  python labs/m4/l04_embeddings.py
"""

from __future__ import annotations

import numpy as np

RNG = np.random.default_rng(11)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return float("nan")
    return float(a @ b / (na * nb))


# ------------------------------------------------- 1. the worked example
rule("1. THE WORKED EXAMPLE  (4 toy dimensions: water, money, structure, movement)")

VEC = {
    "river":   np.array([0.9, 0.0, 0.1, 0.4]),
    "money":   np.array([0.0, 0.9, 0.1, 0.1]),
    "shore":   np.array([0.8, 0.0, 0.3, 0.0]),
    "account": np.array([0.0, 0.8, 0.3, 0.0]),
    "bank":    np.array([0.45, 0.45, 0.5, 0.1]),      # the static average
}

print(f"  {'token':<10}{'water':>8}{'money':>8}{'struct':>8}{'move':>8}")
for name, v in VEC.items():
    tag = "   <- the static average of both senses" if name == "bank" else ""
    print(f"  {name:<10}{v[0]:>8.2f}{v[1]:>8.2f}{v[2]:>8.2f}{v[3]:>8.2f}{tag}")

s_shore = cos(VEC["bank"], VEC["shore"])
s_account = cos(VEC["bank"], VEC["account"])
print(f"\n  STATIC embedding:")
print(f"    cos(bank, shore)   = {s_shore:.4f}")
print(f"    cos(bank, account) = {s_account:.4f}")
print(f"    difference         = {abs(s_shore - s_account):.4f}  "
      f"<- {'IDENTICAL' if abs(s_shore - s_account) < 1e-9 else 'differ'}")
print("    One vector cannot say which sense is meant. The information was")
print("    averaged away before the question was asked.")


def contextualise(token, neighbours, weight=0.5):
    ctx = np.mean([VEC[n] for n in neighbours], axis=0)
    return (1 - weight) * VEC[token] + weight * ctx


print("\n  CONTEXTUAL, mixing 50% of the neighbour's vector:")
print(f"  {'phrase':<16}{'bank vector':<34}{'cos(shore)':>12}{'cos(account)':>14}")
for phrase, neigh in (("river bank", ["river"]), ("money bank", ["money"])):
    bctx = contextualise("bank", neigh)
    print(f"  {phrase:<16}{str(np.round(bctx, 3)):<34}"
          f"{cos(bctx, VEC['shore']):>12.4f}{cos(bctx, VEC['account']):>14.4f}")

print("\n  Same token, same starting row, opposite results. Nothing changed")
print("  except the neighbours.")

print("\n  How the mixing weight controls disambiguation:")
print(f"  {'weight':>8}{'river: cos(shore)':>20}{'money: cos(account)':>22}"
      f"{'separation':>13}")
for wgt in (0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0):
    r = cos(contextualise("bank", ["river"], wgt), VEC["shore"])
    m = cos(contextualise("bank", ["money"], wgt), VEC["account"])
    wrong = cos(contextualise("bank", ["river"], wgt), VEC["account"])
    print(f"  {wgt:>8.2f}{r:>20.4f}{m:>22.4f}{r - wrong:>13.4f}")
print("\n  'separation' is how much better the RIGHT sense scores than the")
print("  wrong one. At weight 0 there is none. It grows with the weight --")
print("  but at weight 1.0 the token's own identity is gone entirely, which")
print("  is why real attention LEARNS the weight instead of fixing it.")


# ------------------------------------------------- 2. structure emerging
rule("2. WATCHING STRUCTURE EMERGE FROM RANDOM INITIALISATION")

# A synthetic corpus where 'cat' and 'dog' are interchangeable, and 'invoice'
# and 'receipt' are interchangeable, but the two groups never co-occur.
TEMPLATES = [
    "the {pet} sat on the mat",
    "my {pet} needs food today",
    "a friendly {pet} came here",
    "please send the {doc} again",
    "the {doc} shows the amount",
    "i cannot find my {doc} anywhere",
]
PETS, DOCS = ["cat", "dog"], ["invoice", "receipt"]

sentences = []
for t in TEMPLATES:
    if "{pet}" in t:
        sentences += [t.format(pet=p) for p in PETS]
    else:
        sentences += [t.format(doc=d) for d in DOCS]
sentences *= 60

words = sorted({w for s in sentences for w in s.split()})
w2i = {w: i for i, w in enumerate(words)}
V, D = len(words), 12
print(f"  corpus     : {len(sentences)} sentences, {V} distinct words")
print(f"  d_model    : {D}")
print(f"  'cat'/'dog' appear in the same contexts and never together;")
print(f"  'invoice'/'receipt' likewise. Nothing tells the model they are alike.")

# Skip-gram style: predict a context word from a centre word.
pairs = []
for s in sentences:
    toks = [w2i[w] for w in s.split()]
    for i, c in enumerate(toks):
        for j in range(max(0, i - 2), min(len(toks), i + 3)):
            if i != j:
                pairs.append((c, toks[j]))
pairs = np.array(pairs)

E = RNG.normal(0, 0.1, size=(V, D))       # input embeddings
C = RNG.normal(0, 0.1, size=(V, D))       # context embeddings


def track():
    return (cos(E[w2i["cat"]], E[w2i["dog"]]),
            cos(E[w2i["invoice"]], E[w2i["receipt"]]),
            cos(E[w2i["cat"]], E[w2i["invoice"]]))


print(f"\n  {'step':>8}{'cos(cat,dog)':>15}{'cos(inv,rec)':>15}"
      f"{'cos(cat,inv)':>15}")
print(f"  {'random':>8}{track()[0]:>15.4f}{track()[1]:>15.4f}{track()[2]:>15.4f}")

LR, BATCH = 0.12, 512
for step in range(1, 3001):
    idx = RNG.choice(len(pairs), size=BATCH, replace=False)
    centre, ctx = pairs[idx, 0], pairs[idx, 1]
    h = E[centre]                                  # (B, D)
    logits = h @ C.T                               # (B, V)
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    p /= p.sum(axis=1, keepdims=True)
    p[np.arange(BATCH), ctx] -= 1.0                # softmax + CE gradient
    p /= BATCH
    gE = p @ C
    gC = p.T @ h
    np.add.at(E, centre, -LR * gE)
    C -= LR * gC
    if step in (200, 600, 1500, 3000):
        a, b, c = track()
        print(f"  {step:>8}{a:>15.4f}{b:>15.4f}{c:>15.4f}")

print("\n  Words used in the same contexts converged toward each other; words")
print("  from different contexts did not. Nothing supervised this -- the")
print("  structure fell out of predicting neighbours (M1-L07 self-supervision).")

print("\n  nearest neighbours in the learned space:")
for probe in ("cat", "invoice", "mat"):
    sims = sorted(((cos(E[w2i[probe]], E[i]), w) for w, i in w2i.items()
                   if w != probe), reverse=True)[:3]
    print(f"    {probe:<10} -> " + ", ".join(f"{w} ({s:.3f})" for s, w in sims))


# ------------------------------------------------- 3. matrix sizes
rule("3. HOW BIG IS THE EMBEDDING MATRIX?")

print(f"  {'vocab':>10}{'d_model':>10}{'params':>14}{'fp32':>11}{'fp16':>10}"
      f"{'% of a 7B model':>18}")
for vocab, d in ((32_000, 4096), (100_000, 4096), (128_000, 4096),
                 (128_000, 8192), (256_000, 8192)):
    n = vocab * d
    print(f"  {vocab:>10,}{d:>10,}{n:>14,}{n * 4 / 1024**3:>10.2f}G"
          f"{n * 2 / 1024**3:>9.2f}G{n / 7e9:>17.1%}")

print("\n  A 128k vocabulary at d_model 4,096 is 524M parameters -- 7.5% of a")
print("  7B model spent on a lookup table, before any layer does any work.")
print("  Tied embeddings (reusing E as the output projection) halve this.")

print("\n  and the lookup itself:")
one_hot = np.zeros(50_000)
one_hot[675] = 1.0
E_demo = RNG.normal(0, 0.02, size=(50_000, 512))
via_matmul = one_hot @ E_demo
via_index = E_demo[675]
print(f"    one_hot(675) @ E  == E[675] ? {np.allclose(via_matmul, via_index)}")
print(f"    multiplications in the matmul : {50_000 * 512:,}")
print(f"    multiplications in the index  : 0")
print("    Same answer. Nobody does it the first way.")


# ------------------------------------------------- 4. pooling
rule("4. POOLING, AND THE PADDING BUG  (which is subtler than it looks)")

D_P = 64
np_rng = np.random.default_rng(3)
topic_a = np_rng.normal(0, 1, size=D_P)
topic_b = np_rng.normal(0, 1, size=D_P)


def sentence(topic, length, noise=0.6):
    """A sentence: `length` token vectors scattered around a topic centre."""
    return topic + np_rng.normal(0, noise, size=(length, D_P))


def mean_pool(vectors, mask=None):
    if mask is None:
        return vectors.mean(axis=0)
    return vectors[mask.astype(bool)].mean(axis=0)


# A REAL padding embedding is a learned row of the embedding matrix, and after
# any transformer layer it is certainly not the zero vector. That distinction
# turns out to decide whether the bug bites at all.
PAD_ZERO = np.zeros(D_P)
PAD_LEARNED = np_rng.normal(0, 1, size=D_P)


def pad_to(vectors, length, pad_vec):
    extra = length - len(vectors)
    if extra <= 0:
        return vectors, np.ones(len(vectors))
    padded = np.vstack([vectors, np.tile(pad_vec, (extra, 1))])
    mask = np.array([1] * len(vectors) + [0] * extra)
    return padded, mask


print("  FIRST, the case people usually imagine: a ZERO padding vector,")
print("  both sentences the same real length.\n")
print(f"  {'real':>6}{'padded':>8}{'pad %':>8}{'cos WITH mask':>16}"
      f"{'cos WITHOUT':>14}{'error':>9}")
for real, padded in ((8, 8), (8, 32), (4, 64), (2, 64)):
    s1, m1 = pad_to(sentence(topic_a, real), padded, PAD_ZERO)
    s2, m2 = pad_to(sentence(topic_a, real), padded, PAD_ZERO)
    wm = cos(mean_pool(s1, m1), mean_pool(s2, m2))
    wo = cos(mean_pool(s1), mean_pool(s2))
    print(f"  {real:>6}{padded:>8}{(padded - real) / padded:>7.0%}"
          f"{wm:>16.4f}{wo:>14.4f}{abs(wm - wo):>9.4f}")

print("\n  ERROR IS EXACTLY ZERO -- and that is a real result, not a broken")
print("  demo. Averaging in zeros divides the vector by a larger number but")
print("  does not change its DIRECTION, and cosine similarity is scale-")
print("  invariant (M3-L02). With a zero pad vector and cosine, the bug is")
print("  genuinely harmless.")

print("\n  NOW the realistic case: a LEARNED (non-zero) padding embedding,")
print("  and sentences of DIFFERENT real lengths padded to the same width.\n")
print(f"  {'len A':>6}{'len B':>6}{'padded':>8}{'cos WITH mask':>16}"
      f"{'cos WITHOUT':>14}{'error':>9}")
for la, lb, padded in ((8, 8, 64), (8, 40, 64), (4, 56, 64),
                       (2, 60, 64), (30, 34, 64)):
    s1, m1 = pad_to(sentence(topic_a, la), padded, PAD_LEARNED)
    s2, m2 = pad_to(sentence(topic_a, lb), padded, PAD_LEARNED)
    wm = cos(mean_pool(s1, m1), mean_pool(s2, m2))
    wo = cos(mean_pool(s1), mean_pool(s2))
    print(f"  {la:>6}{lb:>6}{padded:>8}{wm:>16.4f}{wo:>14.4f}"
          f"{abs(wm - wo):>9.4f}")

print("\n  Same topic every row. Unmasked, the short sentence is dragged far")
print("  toward the pad embedding and the long one barely at all, so their")
print("  similarity is distorted. Note the LAST row: when both lengths are")
print("  similar, the error nearly vanishes -- both drift the same way.")

print("\n  And the case that actually costs you money -- UNRELATED sentences")
print("  of very different lengths, which SHOULD score near zero:\n")
print(f"  {'len A':>6}{'len B':>6}{'padded':>8}{'cos WITH mask':>16}"
      f"{'cos WITHOUT':>14}{'inflation':>11}")
for la, lb, padded in ((8, 8, 64), (4, 56, 64), (2, 60, 64), (2, 62, 64)):
    s1, m1 = pad_to(sentence(topic_a, la), padded, PAD_LEARNED)
    s2, m2 = pad_to(sentence(topic_b, lb), padded, PAD_LEARNED)
    wm = cos(mean_pool(s1, m1), mean_pool(s2, m2))
    wo = cos(mean_pool(s1), mean_pool(s2))
    print(f"  {la:>6}{lb:>6}{padded:>8}{wm:>16.4f}{wo:>14.4f}"
          f"{wo - wm:>+11.4f}")

print("\n  UNRELATED sentences are pushed UP toward each other, because both")
print("  now contain a large shared component: the padding embedding. That is")
print("  the failure -- false positives in retrieval, arriving silently.")
print("\n  THE RULE: mask padding. The bug is invisible with zero padding and")
print("  equal lengths, which is exactly the configuration people test with.")

print("\n  pooling strategies compared on the same sentence:")
s_demo = sentence(topic_a, 12)
strategies = {
    "mean": s_demo.mean(axis=0),
    "max": s_demo.max(axis=0),
    "last token": s_demo[-1],
    "first token": s_demo[0],
}
ref = sentence(topic_a, 12)
other_ref = sentence(topic_b, 12).mean(axis=0)
for name, vec in strategies.items():
    same = cos(vec, ref.mean(axis=0))
    other = cos(vec, other_ref)
    print(f"    {name:<14} same topic {same:>7.4f}   other topic {other:>7.4f}"
          f"   separation {same - other:>7.4f}")
print("\n  Mean pooling separates the topics best here because it averages away")
print("  per-token noise. Single-token strategies inherit that token's noise --")
print("  which is why they need a model TRAINED to put the meaning there.")


# ------------------------------------------------- 5. anisotropy
rule("5. ANISOTROPY: WHY A 0.8 THRESHOLD MEANS NOTHING")

D_A, N = 256, 4000
uniform = RNG.normal(0, 1, size=(N, D_A))

# An anisotropic set: every vector has a large shared component, as real
# language-model embeddings do. The shared component must dominate the noise
# to reproduce the effect -- with d=256 the noise has norm ~sqrt(256)=16, so a
# scale of 3 (a first attempt) is swamped by it and shows nothing.
common = RNG.normal(0, 1, size=D_A)
common /= np.linalg.norm(common)
SHARED = 30.0                      # norm of the shared part, vs ~16 for noise
aniso = SHARED * common + RNG.normal(0, 1, size=(N, D_A))


def sim_stats(M, label):
    Mn = M / np.linalg.norm(M, axis=1, keepdims=True)
    idx = RNG.choice(len(Mn), size=(4000, 2))
    idx = idx[idx[:, 0] != idx[:, 1]]
    sims = np.einsum("ij,ij->i", Mn[idx[:, 0]], Mn[idx[:, 1]])
    print(f"  {label:<28}{sims.mean():>9.4f}{sims.std():>9.4f}"
          f"{np.percentile(sims, 5):>10.4f}{np.percentile(sims, 95):>10.4f}"
          f"{(sims > 0.8).mean():>13.1%}")
    return sims


print(f"  cosine similarity of RANDOM UNRELATED pairs, {D_A} dimensions:\n")
print(f"  {'vector set':<28}{'mean':>9}{'sd':>9}{'p5':>10}{'p95':>10}"
      f"{'% above 0.8':>13}")
sim_stats(uniform, "isotropic (textbook)")
sims_a = sim_stats(aniso, "anisotropic (realistic)")

print(f"\n  In the anisotropic set, UNRELATED pairs average "
      f"{sims_a.mean():.2f} similarity and")
print(f"  {(sims_a > 0.8).mean():.0%} of them exceed 0.8. A threshold of 0.8 copied from a")
print("  tutorial would admit essentially the entire corpus as a 'match'.")
print(f"\n  shared-component norm {SHARED:.0f} vs noise norm ~{np.sqrt(D_A):.0f}:")
print("  the shared direction dominates, so every vector points roughly the")
print("  same way and cosine similarity measures almost nothing.")

print("\n  The fix -- centre the vectors (subtract the mean), then re-measure:")
centred = aniso - aniso.mean(axis=0)
print(f"  {'vector set':<28}{'mean':>9}{'sd':>9}{'p5':>10}{'p95':>10}"
      f"{'% above 0.8':>13}")
sim_stats(centred, "anisotropic, centred")
print("\n  Centring removes the shared component and restores a usable spread.")
print("  But note what it did NOT do: it changed the NUMBERS, not the ranking")
print("  of any pair. If you only need top-k, rank and ignore the absolute")
print("  scores. If you need a threshold, measure YOUR distribution first.")

print("\nDone.")
