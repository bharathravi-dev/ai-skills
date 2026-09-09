"""M4-L09 lab -- positional information: sinusoidal, RoPE, ALiBi.

Verifies the lesson's sinusoidal table, implements RoPE and PROVES its
relative-distance property numerically, compares all four schemes on
extrapolation, and demonstrates position interpolation.

NumPy only, no API key, no network.
Run:  python labs/m4/l09_positional.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(9)
np.set_printoptions(precision=4, suppress=True)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def cos_sim(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else float("nan")


# ------------------------------------------------- 1. sinusoidal
rule("1. SINUSOIDAL ENCODINGS  (verifying the lesson's table)")


def sinusoidal(max_len, d, base=10000.0):
    pos = np.arange(max_len)[:, None]
    i = np.arange(0, d, 2)[None, :]
    freqs = 1.0 / (base ** (i / d))
    pe = np.zeros((max_len, d))
    pe[:, 0::2] = np.sin(pos * freqs)
    pe[:, 1::2] = np.cos(pos * freqs)
    return pe


D = 4
pe = sinusoidal(8, D)
freqs = [1.0 / (10000.0 ** (i / D)) for i in range(0, D, 2)]
print(f"  d_model = {D}, frequencies = {[f'{f:.4f}' for f in freqs]}\n")
print(f"  {'pos':>5}{'sin(p*1)':>12}{'cos(p*1)':>12}{'sin(p*0.01)':>14}"
      f"{'cos(p*0.01)':>14}")
for p in range(4):
    print(f"  {p:>5}{pe[p, 0]:>12.4f}{pe[p, 1]:>12.4f}{pe[p, 2]:>14.4f}"
          f"{pe[p, 3]:>14.4f}")

EXPECT = np.array([
    [0.0000, 1.0000, 0.0000, 1.0000],
    [0.8415, 0.5403, 0.0100, 1.0000],
    [0.9093, -0.4161, 0.0200, 0.9998],
    [0.1411, -0.9900, 0.0300, 0.9996],
])
assert np.allclose(pe[:4], EXPECT, atol=1e-4), pe[:4]
print("\n  section 6.1 verified to 4 dp.")
print("\n  The fast pair swings wildly between adjacent positions (it separates")
print("  NEIGHBOURS); the slow pair barely moves (it separates REGIONS). That")
print("  is why several frequencies are used rather than one.")

print("\n  similarity between position encodings, as distance grows:")
pe_big = sinusoidal(600, 64)
print(f"  {'distance':>10}{'cos(PE[0], PE[d])':>22}   profile")
for dist in (0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512):
    sim = cos_sim(pe_big[0], pe_big[dist])
    bar = "#" * max(0, int((sim + 1) / 2 * 40))
    print(f"  {dist:>10}{sim:>22.4f}   |{bar}")
print("\n  Similarity decays with distance -- nearby positions look alike, distant")
print("  ones do not. The model CAN exploit this. Nothing forces it to.")


# ------------------------------------------------- 2. RoPE
rule("2. RoPE, AND THE PROPERTY THAT MADE IT STANDARD")


def rope(x, pos, base=10000.0):
    """Rotate consecutive dimension pairs by an angle proportional to pos."""
    d = x.shape[-1]
    freqs = 1.0 / (base ** (np.arange(0, d, 2) / d))
    ang = pos * freqs
    c, s = np.cos(ang), np.sin(ang)
    out = np.empty_like(x, dtype=float)
    ev, od = x[..., 0::2], x[..., 1::2]
    out[..., 0::2] = ev * c - od * s
    out[..., 1::2] = ev * s + od * c
    return out


q = np.array([1.0, 0.0, 1.0, 0.0])
k = np.array([1.0, 0.0, 1.0, 0.0])

print("  q = k = [1, 0, 1, 0] -- the SAME vector at two positions, so any")
print("  difference in the dot product comes purely from position.\n")

for m, n in ((2, 5), (12, 15)):
    qr, kr = rope(q, m), rope(k, n)
    print(f"  m = {m:>3}, n = {n:>3}   (distance {m - n})")
    print(f"    q_rot = {qr}")
    print(f"    k_rot = {kr}")
    p0 = qr[0] * kr[0] + qr[1] * kr[1]
    p1 = qr[2] * kr[2] + qr[3] * kr[3]
    print(f"    pair 0 contribution: {p0:>9.4f}   = cos({(m - n) * 1.0:.2f}) "
          f"= {math.cos((m - n) * 1.0):.4f}")
    print(f"    pair 1 contribution: {p1:>9.4f}   = cos({(m - n) * 0.01:.2f}) "
          f"= {math.cos((m - n) * 0.01):.4f}")
    print(f"    total              : {qr @ kr:>9.4f}\n")

print("  Both distances are -3, and both totals are identical. The absolute")
print("  positions vanished; only m - n survived.")

print("\n  now verifying it exhaustively -- 40 position pairs at each distance:")
print(f"  {'distance':>10}{'mean dot':>13}{'max deviation':>16}{'verdict':>12}")
worst_overall = 0.0
for dist in (1, 3, 7, 50, 500, 5000):
    vals = []
    for start in RNG.integers(0, 100_000, size=40):
        m2, n2 = int(start), int(start) + dist
        vals.append(float(rope(q, m2) @ rope(k, n2)))
    vals = np.array(vals)
    dev = float(np.abs(vals - vals.mean()).max())
    worst_overall = max(worst_overall, dev)
    print(f"  {dist:>10}{vals.mean():>13.6f}{dev:>16.2e}"
          f"{'CONSTANT' if dev < 1e-9 else 'varies':>12}")

print(f"\n  worst deviation across all distances: {worst_overall:.2e}")
assert worst_overall < 1e-9, "RoPE's relative property failed"
print("  The dot product depends on m - n and NOTHING else, to within floating-")
print("  point noise. This is an algebraic identity, not an empirical finding.")

print("\n  and the same test with RoPE wrongly applied to V as well:")
v = np.array([0.5, 0.5, 1.0, 0.0])
print(f"  {'distance':>10}{'mean output[0]':>18}{'max deviation':>16}{'verdict':>12}")
for dist in (1, 3, 50):
    outs = []
    for start in RNG.integers(0, 10_000, size=20):
        m2, n2 = int(start), int(start) + dist
        w = float(rope(q, m2) @ rope(k, n2))
        outs.append(float((w * rope(v, n2))[0]))
    outs = np.array(outs)
    dev = float(np.abs(outs - outs.mean()).max())
    print(f"  {dist:>10}{outs.mean():>18.6f}{dev:>16.2e}"
          f"{'CONSTANT' if dev < 1e-9 else 'VARIES':>12}")
print("\n  Rotating V makes the OUTPUT depend on absolute position, destroying")
print("  the property RoPE exists to provide. Apply it to Q and K only.")


# ------------------------------------------------- 3. ALiBi
rule("3. ALiBi: A DISTANCE PENALTY ON THE SCORES")

T = 8


def alibi_bias(T, slope):
    idx = np.arange(T)
    dist = idx[None, :] - idx[:, None]        # negative for past positions
    return slope * dist


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


CAUSAL = np.triu(np.ones((T, T), dtype=bool), k=1)
print(f"  attention from the LAST position, flat scores, {T} tokens.")
print(f"  Different heads get different slopes:\n")
print(f"  {'slope':>8}  " + "".join(f"{f'pos{i}':>8}" for i in range(T))
      + f"{'effective range':>18}")
for slope in (0.0, 0.125, 0.25, 0.5, 1.0):
    scores = np.zeros((T, T)) + alibi_bias(T, slope)
    scores = np.where(CAUSAL, -1e9, scores)
    w = softmax(scores, axis=-1)[-1]
    # effective range: how many positions hold 90% of the mass
    order = np.argsort(-w)
    cum, rng_n = 0.0, 0
    for i in order:
        cum += w[i]
        rng_n += 1
        if cum >= 0.9:
            break
    print(f"  {slope:>8.3f}  " + "".join(f"{x:>8.3f}" for x in w)
          + f"{rng_n:>18}")
print("\n  slope 0 attends uniformly over the whole past; larger slopes")
print("  concentrate on recent tokens. A model with a spread of slopes across")
print("  heads gets local AND global views for free, with no parameters and no")
print("  positional vector at all.")


# ------------------------------------------------- 4. extrapolation
rule("4. BEYOND THE TRAINED LENGTH  (what this CAN and CANNOT be measured)")

TRAINED = 512
pe_train = sinusoidal(8192, 64)
qv64 = np.array([1.0, 0.0] * 32)

print(f"  a model trained to length {TRAINED}, then asked for longer.\n")
print("  FIRST, what IS measurable without a trained model: are the encodings")
print("  still well-defined and still distinguishable out there?\n")
print(f"  {'scheme':<22}{'at 256':>12}{'at 512':>12}{'at 1024':>12}"
      f"{'at 4096':>12}")

row = f"  {'learned absolute':<22}"
for L in (256, 512, 1024, 4096):
    row += f"{('defined' if L <= TRAINED else 'NO ROW'):>12}"
print(row)

for name, fn in (("sinusoidal", lambda L: (pe_train[L - 1], pe_train[L - 2])),
                 ("RoPE", lambda L: (rope(qv64, L - 1), rope(qv64, L - 2)))):
    row = f"  {name:<22}"
    for L in (256, 512, 1024, 4096):
        a, b = fn(L)
        row += f"{cos_sim(a, b):>12.4f}"
    print(row)
print("  " + " " * 22 + "  <- similarity between ADJACENT positions")

print("\n  Read that carefully. For a learned table, position 1024 has NO ROW --")
print("  the failure is total and immediate. For sinusoidal and RoPE the")
print("  adjacent-position similarity is IDENTICAL at every length, because")
print("  both schemes are translation-invariant by construction. Positions")
print("  100,000 apart are as distinguishable as positions 100 apart.")

print("\n  So the encodings do not degrade. NOW THE HONEST LIMIT OF THIS LAB:")
print("  that is not what extrapolation failure is. The encodings are fine; the")
print("  MODEL has simply never seen them. Weights trained only on rotations up")
print("  to angle 512*theta have no idea what to do with angle 4096*theta, and")
print("  measuring that requires a trained model, which this lab does not have.")
print("\n  What you can take from this section:")
print("    * learned tables fail HARD and immediately (no row exists)")
print("    * sinusoidal and RoPE fail SOFTLY and silently (defined, untrained)")
print("    * and the second failure mode is the more dangerous one, because")
print("      nothing errors -- see M4-L06 section 5.4 for the same point about")
print("      effective context. TEST AT YOUR REAL LENGTH.")


# ------------------------------------------------- 5. interpolation
rule("5. POSITION INTERPOLATION: THE TRADE IT MAKES")

print(f"  trained context {TRAINED}; extending to 4x by compressing positions")
print(f"  (position p is presented to the model as p / 4)\n")
SCALE = 4
print(f"  {'':<22}{'adjacent sim':>15}{'sim at dist 10':>17}"
      f"{'resolution':>14}")
qv = np.array([1.0, 0.0] * 32)
for label, scale in (("original (no scaling)", 1), (f"interpolated ({SCALE}x)", SCALE)):
    a = rope(qv, 100 / scale)
    b = rope(qv, 101 / scale)
    c = rope(qv, 110 / scale)
    adj, far = cos_sim(a, b), cos_sim(a, c)
    print(f"  {label:<22}{adj:>15.6f}{far:>17.6f}{1 - adj:>14.6f}")

a1, b1 = rope(qv, 100), rope(qv, 101)
a4, b4 = rope(qv, 25.0), rope(qv, 25.25)
loss = (1 - cos_sim(a4, b4)) / (1 - cos_sim(a1, b1))
print(f"\n  adjacent positions become {1 / loss:,.0f}x harder to tell apart.")
print("  That is the cost of interpolation, and it is why an interpolated model")
print("  can get WORSE at short sequences while getting better at long ones.")
print("  Evaluate BOTH ranges before shipping (M4-L09 section 9).")


# ------------------------------------------------- 6. parameter cost
rule("6. THE PARAMETER COST OF EACH SCHEME")

print(f"  {'scheme':<22}{'2k ctx':>14}{'32k ctx':>14}{'128k ctx':>14}")
D_MODEL = 4096
row = f"  {'learned absolute':<22}"
for L in (2048, 32768, 131072):
    row += f"{L * D_MODEL / 1e6:>12.1f}M"
print(row)
for name in ("sinusoidal", "RoPE", "ALiBi"):
    print(f"  {name:<22}{0:>13}{0:>14}{0:>14}")

print(f"\n  A learned table at 128k context and d_model {D_MODEL} costs")
print(f"  {131072 * D_MODEL / 1e6:.0f}M parameters -- about {131072 * D_MODEL / 7e9:.0%} of a 7B model,")
print("  spent entirely on saying where each token is. RoPE and ALiBi do the")
print("  same job for nothing, which is the other half of why the field moved.")

print("\nDone.")
