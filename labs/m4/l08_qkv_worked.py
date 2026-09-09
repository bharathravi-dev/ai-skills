"""M4-L08 lab -- a complete masked multi-head attention pass, verified.

Recomputes every number in the lesson's worked example and ASSERTS it matches,
then introduces each of the four common implementation errors and shows
precisely which invariant each one breaks.

NumPy only, no API key, no network.
Run:  python labs/m4/l08_qkv_worked.py
"""

from __future__ import annotations

import math

import numpy as np

np.set_printoptions(precision=4, suppress=True)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


# ------------------------------------------------------------------ setup
T, D_MODEL, N_HEADS = 3, 4, 2
D_HEAD = D_MODEL // N_HEADS
TOKENS = ["the", "cat", "sat"]

X = np.array([
    [1.0, 0.0, 0.5, 0.0],
    [0.0, 1.0, 0.0, 0.5],
    [0.5, 0.5, 1.0, 0.0],
])
W_Q = np.eye(4)
W_K = np.array([[0., 1., 0., 0.],
                [1., 0., 0., 0.],
                [0., 0., 0., 1.],
                [0., 0., 1., 0.]])
W_V = np.array([[1., 0., 0., 0.],
                [0., 1., 0., 0.],
                [0., 0., 2., 0.],
                [0., 0., 0., 2.]])
W_O = np.eye(4)
CAUSAL = np.triu(np.ones((T, T), dtype=bool), k=1)


def split_heads(M):
    """(T, d_model) -> (n_heads, T, d_head). A reshape and a transpose."""
    return M.reshape(T, N_HEADS, D_HEAD).transpose(1, 0, 2)


def merge_heads(M):
    """(n_heads, T, d_head) -> (T, d_model)."""
    return M.transpose(1, 0, 2).reshape(T, D_MODEL)


def attention(X, w_q, w_k, w_v, w_o, mask=CAUSAL,
              softmax_axis=-1, mask_after_softmax=False, use_wo=True):
    Q, K, V = X @ w_q, X @ w_k, X @ w_v
    Qh, Kh, Vh = split_heads(Q), split_heads(K), split_heads(V)
    scores = Qh @ Kh.transpose(0, 2, 1) / math.sqrt(D_HEAD)
    if mask is not None and not mask_after_softmax:
        scores = np.where(mask, -1e9, scores)
    W = softmax(scores, axis=softmax_axis)
    if mask is not None and mask_after_softmax:
        W = np.where(mask, 0.0, W)
    out = merge_heads(W @ Vh)
    if use_wo:
        out = out @ w_o
    return out, W, scores, (Qh, Kh, Vh)


# ------------------------------------------------- 1. verify every number
rule("1. RECOMPUTING EVERY NUMBER IN THE WORKED EXAMPLE")

Q, K, V = X @ W_Q, X @ W_K, X @ W_V
print("  X (input, one row per token):")
for t, r in zip(TOKENS, X):
    print(f"    {t:<5}{r}")
print("\n  Q = X @ W_q   (W_q is the identity, so Q == X)")
for t, r in zip(TOKENS, Q):
    print(f"    {t:<5}{r}")
print("\n  K = X @ W_k   (columns swapped in pairs)")
for t, r in zip(TOKENS, K):
    print(f"    {t:<5}{r}")
print("\n  V = X @ W_v   (columns 2 and 3 doubled)")
for t, r in zip(TOKENS, V):
    print(f"    {t:<5}{r}")

EXPECT_Q = X.copy()
EXPECT_K = np.array([[0., 1., 0., .5], [1., 0., .5, 0.], [.5, .5, 0., 1.]])
EXPECT_V = np.array([[1., 0., 1., 0.], [0., 1., 0., 1.], [.5, .5, 2., 0.]])
assert np.allclose(Q, EXPECT_Q), "Q does not match the lesson"
assert np.allclose(K, EXPECT_K), "K does not match the lesson"
assert np.allclose(V, EXPECT_V), "V does not match the lesson"
print("\n  section 6.3 verified: Q, K, V all match.")

out, W, scores, (Qh, Kh, Vh) = attention(X, W_Q, W_K, W_V, W_O)

print(f"\n  head split: (T={T}, d_model={D_MODEL}) -> "
      f"(n_heads={N_HEADS}, T={T}, d_head={D_HEAD})")
for h in range(N_HEADS):
    cols = f"columns {h * D_HEAD}-{h * D_HEAD + D_HEAD - 1}"
    print(f"\n    head {h}  ({cols})")
    print(f"      Q{h} = {Qh[h].tolist()}")
    print(f"      K{h} = {Kh[h].tolist()}")
    print(f"      V{h} = {Vh[h].tolist()}")

EXPECT_Q0 = np.array([[1., 0.], [0., 1.], [.5, .5]])
EXPECT_Q1 = np.array([[.5, 0.], [0., .5], [1., 0.]])
assert np.allclose(Qh[0], EXPECT_Q0) and np.allclose(Qh[1], EXPECT_Q1)
print("\n  section 6.4 verified: both heads' Q, K, V match.")

for h in range(N_HEADS):
    raw = Qh[h] @ Kh[h].T
    print(f"\n  head {h}: raw Q.K^T")
    for t, r in zip(TOKENS, raw):
        print(f"    {t:<5}{r}")
    print(f"  head {h}: scaled by sqrt(d_head) = {math.sqrt(D_HEAD):.4f}, "
          f"then masked")
    masked = np.where(CAUSAL, -1e9, raw / math.sqrt(D_HEAD))
    for t, r in zip(TOKENS, masked):
        shown = ["  -inf " if v < -1e8 else f"{v:>7.4f}" for v in r]
        print(f"    {t:<5}[{' '.join(shown)}]")
    print(f"  head {h}: after softmax")
    for t, r in zip(TOKENS, W[h]):
        print(f"    {t:<5}{r}   sum {r.sum():.4f}")

EXPECT_W0 = np.array([[1., 0., 0.],
                      [0.6698, 0.3302, 0.],
                      [1 / 3, 1 / 3, 1 / 3]])
EXPECT_W1 = np.array([[1., 0., 0.],
                      [0.5441, 0.4559, 0.],
                      [0.2920, 0.4159, 0.2920]])
assert np.allclose(W[0], EXPECT_W0, atol=1e-4), f"head 0 weights: {W[0]}"
assert np.allclose(W[1], EXPECT_W1, atol=1e-4), f"head 1 weights: {W[1]}"
print("\n  sections 6.7 and 6.9 verified: all weights match to 4 dp.")

head_out = W @ Vh
print(f"\n  weighted values per head:")
for h in range(N_HEADS):
    for t, r in zip(TOKENS, head_out[h]):
        print(f"    head {h}  {t:<5}{r}")

EXPECT_OUT0 = np.array([[1., 0.], [0.6698, 0.3302], [0.5, 0.5]])
EXPECT_OUT1 = np.array([[1., 0.], [0.5441, 0.4559], [0.8761, 0.4159]])
assert np.allclose(head_out[0], EXPECT_OUT0, atol=1e-4)
assert np.allclose(head_out[1], EXPECT_OUT1, atol=1e-4)
print("\n  sections 6.8 and 6.9 verified: head outputs match.")

concat = merge_heads(head_out)
print(f"\n  concatenated -> {concat.shape}:")
for t, r in zip(TOKENS, concat):
    print(f"    {t:<5}{r}")
print(f"\n  after W_o (identity here) -> {out.shape}:")
for t, r in zip(TOKENS, out):
    print(f"    {t:<5}{r}")

assert out.shape == X.shape, "the block must be (T, d_model) -> (T, d_model)"
print(f"\n  SHAPE INVARIANT: input {X.shape} -> output {out.shape}  OK")
print("  EVERY NUMBER IN SECTION 6 VERIFIED.")


# ------------------------------------------------- 2. the three assertions
rule("2. THE THREE ASSERTIONS EVERY IMPLEMENTATION NEEDS")


def check(W, out, X, label):
    """Returns (rows_sum_to_1, mask_respected, shape_ok)."""
    rows = bool(np.allclose(W.sum(axis=-1), 1.0, atol=1e-6))
    masked_ok = bool(np.allclose(W[:, CAUSAL], 0.0, atol=1e-6))
    shape_ok = out.shape == X.shape
    print(f"  {label:<38}"
          f"{'PASS' if rows else 'FAIL':>8}"
          f"{'PASS' if masked_ok else 'FAIL':>16}"
          f"{'PASS' if shape_ok else 'FAIL':>12}")
    return rows, masked_ok, shape_ok


print(f"  {'implementation':<38}{'rows sum 1':>8}{'mask respected':>16}"
      f"{'shape':>12}")
check(W, out, X, "correct")

# Error 1: softmax over the wrong axis.
o1, w1, _, _ = attention(X, W_Q, W_K, W_V, W_O, softmax_axis=-2)
check(w1, o1, X, "ERROR: softmax over axis -2 (columns)")

# Error 2: mask applied after the softmax.
o2, w2, _, _ = attention(X, W_Q, W_K, W_V, W_O, mask_after_softmax=True)
check(w2, o2, X, "ERROR: mask applied AFTER softmax")

# Error 3: W_o omitted.
o3, w3, _, _ = attention(X, W_Q, W_K, W_V, W_O, use_wo=False)
check(w3, o3, X, "ERROR: W_o omitted")

# Error 4: divided by sqrt(d_model) instead of sqrt(d_head).
Qh4, Kh4, Vh4 = split_heads(X @ W_Q), split_heads(X @ W_K), split_heads(X @ W_V)
sc4 = np.where(CAUSAL, -1e9, Qh4 @ Kh4.transpose(0, 2, 1) / math.sqrt(D_MODEL))
w4 = softmax(sc4, axis=-1)
o4 = merge_heads(w4 @ Vh4) @ W_O
check(w4, o4, X, "ERROR: divided by sqrt(d_model)")

print("\n  Read the FAIL columns carefully:")
print("    * wrong softmax axis  -> 'rows sum 1' FAILS. Caught.")
print("    * mask after softmax  -> 'rows sum 1' FAILS (mass was removed after")
print("      normalisation, so the rows no longer sum to 1). Caught.")
print("    * W_o omitted         -> ALL THREE PASS. NOT CAUGHT.")
print("    * wrong divisor       -> ALL THREE PASS. NOT CAUGHT.")
print("\n  Two of the four errors are invisible to these assertions AND produce")
print("  no exception. They simply make the model worse. That is why 'it runs'")
print("  is not evidence that an attention implementation is correct.")


rule("3. HOW THE INVISIBLE ERRORS ACTUALLY SHOW UP")

print("  W_o omitted -- with the IDENTITY W_o used in the lesson there is no")
print("  difference at all, which is why the lesson's example cannot reveal it.")
print(f"    identity W_o, difference: "
      f"{np.abs(out - o3).max():.6f}")

rng = np.random.default_rng(8)
W_O_random = rng.normal(0, 0.5, size=(D_MODEL, D_MODEL))
out_with, _, _, _ = attention(X, W_Q, W_K, W_V, W_O_random, use_wo=True)
out_without, _, _, _ = attention(X, W_Q, W_K, W_V, W_O_random, use_wo=False)
print(f"    a LEARNED W_o, difference: "
      f"{np.abs(out_with - out_without).max():.6f}")
print("\n  The consequence is structural, not numerical: without W_o, head 0's")
print("  output can only ever occupy dimensions 0-1 of the block's output.")
print("  Information cannot move between heads. The model trains, produces no")
print("  error, and is permanently less expressive.")

print(f"\n  wrong divisor -- sqrt(d_model)={math.sqrt(D_MODEL):.4f} vs "
      f"sqrt(d_head)={math.sqrt(D_HEAD):.4f}")
print(f"    scores are {math.sqrt(D_MODEL) / math.sqrt(D_HEAD):.4f}x too small,")
print(f"    so the weights are too UNIFORM at initialisation:")
print(f"      correct head-1 row 2 weights: {W[1, 2]}")
print(f"      wrong   head-1 row 2 weights: {w4[1, 2]}")
ent_ok = float(-(W[1, 2] * np.log(np.clip(W[1, 2], 1e-12, None))).sum())
ent_bad = float(-(w4[1, 2] * np.log(np.clip(w4[1, 2], 1e-12, None))).sum())
print(f"      entropy {ent_ok:.4f} -> {ent_bad:.4f}  (uniform = "
      f"{math.log(3):.4f})")
print("    The divisor grows with d_head, so at realistic sizes (d_head 64 vs")
print("    d_model 4096) the error is an 8x scale mistake, not a 1.4x one.")


rule("4. THE MASK, PROVEN")

print("  Change ONLY the last token, then check whether earlier positions'")
print("  outputs moved. With correct causal masking they must not.\n")

X_alt = X.copy()
X_alt[2] = [0.9, 0.1, 0.2, 0.7]        # a completely different third token
out_a, _, _, _ = attention(X, W_Q, W_K, W_V, W_O)
out_b, _, _, _ = attention(X_alt, W_Q, W_K, W_V, W_O)

print(f"  {'position':<12}{'original output':<30}{'after change':<30}{'same?':>8}")
for i, t in enumerate(TOKENS):
    same = np.allclose(out_a[i], out_b[i])
    print(f"  {i} ({t}){'':<5}{str(np.round(out_a[i], 4)):<30}"
          f"{str(np.round(out_b[i], 4)):<30}{str(same):>8}")

assert np.allclose(out_a[:2], out_b[:2]), "the causal mask is not working"
print("\n  Positions 0 and 1 are bit-identical; position 2 changed, as it must.")
print("  The past cannot see the future.")

out_c, _, _, _ = attention(X, W_Q, W_K, W_V, W_O, mask=None)
out_d, _, _, _ = attention(X_alt, W_Q, W_K, W_V, W_O, mask=None)
print(f"\n  the same test WITHOUT the mask:")
print(f"    positions 0-1 identical? {np.allclose(out_c[:2], out_d[:2])}")
print(f"    max change at position 0: {np.abs(out_c[0] - out_d[0]).max():.4f}")
print("  Without the mask, changing the LAST token changes the FIRST token's")
print("  output. In training that means the answer is visible in the input")
print("  (M4-L05 measured the resulting loss collapse).")


rule("5. SHAPES AND MEMORY AT REALISTIC SIZES")

print(f"  {'T':>8}{'heads':>7}{'score tensor':>18}{'fp32':>12}{'fp16':>11}")
for t in (512, 2048, 8192, 32768):
    for h in (32,):
        n = h * t * t
        print(f"  {t:>8}{h:>7}{f'{h}x{t}x{t}':>18}"
              f"{n * 4 / 1024**3:>11.2f}G{n * 2 / 1024**3:>10.2f}G")

print("\n  The score tensor is n_heads x T x T -- quadratic in T and linear in")
print("  heads. At 32k context with 32 heads it is 128 GB in fp32 if")
print("  materialised, which is why fused kernels that never form it exist.")
print("  The COMPUTE is still quadratic (M4-L06 measured T^2.06).")

print("\nDone.")
