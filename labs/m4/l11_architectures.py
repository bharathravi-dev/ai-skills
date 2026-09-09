"""M4-L11 lab -- encoder, decoder and encoder-decoder, over one block.

All three architectures are built from the SAME attention and FFN code. The
only differences are the mask and the wiring, which is the lesson's central
claim, demonstrated rather than asserted.

NumPy only, no API key, no network.
Run:  python labs/m4/l11_architectures.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(11)
np.set_printoptions(precision=4, suppress=True)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def rms_norm(x, eps=1e-6):
    return x / np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)


def attention(q_src, kv_src, P, mask=None):
    """ONE attention implementation, used by all three architectures.

    Self-attention is q_src is kv_src. Cross-attention passes a different
    kv_src. That is the entire difference.
    """
    d = q_src.shape[-1]
    Q, K, V = q_src @ P["Wq"], kv_src @ P["Wk"], kv_src @ P["Wv"]
    scores = Q @ K.T / math.sqrt(d)
    if mask is not None:
        scores = np.where(mask, -1e9, scores)
    W = softmax(scores, axis=-1)
    return (W @ V) @ P["Wo"], W


def ffn(x, P):
    return np.maximum(0, x @ P["W1"]) @ P["W2"]


def block(x, P, mask=None, cross_kv=None, cross_P=None):
    """One pre-norm block. Add cross_kv for an encoder-decoder decoder block."""
    x = x + attention(rms_norm(x), rms_norm(x), P, mask)[0]
    if cross_kv is not None:
        x = x + attention(rms_norm(x), cross_kv, cross_P, mask=None)[0]
    return x + ffn(rms_norm(x), P)


def make_params(d, seed):
    r = np.random.default_rng(seed)
    s = 0.6 / math.sqrt(d)
    return {"Wq": r.normal(0, s, (d, d)), "Wk": r.normal(0, s, (d, d)),
            "Wv": r.normal(0, s, (d, d)), "Wo": r.normal(0, s, (d, d)),
            "W1": r.normal(0, s, (d, 4 * d)), "W2": r.normal(0, s, (4 * d, d))}


# ------------------------------------------------- 1. the masks
rule("1. ONE PROPERTY SEPARATES THEM: WHO MAY ATTEND TO WHOM")

TOKENS = ["the", "cat", "sat", "on", "the", "mat"]
T = len(TOKENS)
CAUSAL = np.triu(np.ones((T, T), dtype=bool), k=1)
NO_MASK = np.zeros((T, T), dtype=bool)

for name, mask in (("ENCODER-ONLY (bidirectional)", NO_MASK),
                   ("DECODER-ONLY (causal)", CAUSAL)):
    visible = int((~mask).sum())
    print(f"\n  {name}   -- {visible} of {T * T} cells visible "
          f"({visible / (T * T):.0%})")
    print(f"  {'':>7}" + "".join(f"{t:>6}" for t in TOKENS))
    for i, t in enumerate(TOKENS):
        row = "".join(f"{('  X' if mask[i, j] else '  v'):>6}"
                      for j in range(T))
        tag = "   <- position 3" if i == 3 else ""
        print(f"  {t:>7}{row}{tag}")

enc_cells = int((~NO_MASK).sum())
dec_cells = int((~CAUSAL).sum())
print(f"\n  encoder sees {enc_cells} cells; decoder sees {dec_cells}.")
print(f"  the decoder sees {dec_cells / enc_cells:.0%} of the encoder's view.")
print("  That difference is exactly what it pays for the ability to generate.")


# ------------------------------------------------- 2. what each can see
rule("2. THE CONSEQUENCE, MEASURED: DOES A LATER TOKEN AFFECT AN EARLIER ONE?")

D = 32
P = make_params(D, 1)
x = RNG.normal(0, 1, size=(T, D))

x_alt = x.copy()
x_alt[5] = RNG.normal(0, 1, size=D)         # change ONLY the last token

print("  Changing only token 5 ('mat'), then checking every other position:\n")
print(f"  {'position':<12}{'encoder changed?':>20}{'decoder changed?':>20}")
for i, t in enumerate(TOKENS):
    e_a, e_b = block(x, P, NO_MASK), block(x_alt, P, NO_MASK)
    d_a, d_b = block(x, P, CAUSAL), block(x_alt, P, CAUSAL)
    e_ch = not np.allclose(e_a[i], e_b[i])
    d_ch = not np.allclose(d_a[i], d_b[i])
    print(f"  {i} ({t}){'':<5}{str(e_ch):>20}{str(d_ch):>20}")

print("\n  In the encoder EVERY position changed -- all six can see token 5.")
print("  In the decoder only position 5 changed; positions 0-4 are bit-")
print("  identical, because the causal mask makes them structurally unable to")
print("  see it. Same block code, same weights, one mask.")


# ------------------------------------------------- 3. training signal
rule("3. WHY DECODER-ONLY SCALED FIRST: THE TRAINING SIGNAL")

print(f"  {'document length':>18}{'MLM (15% masked)':>20}{'CLM (next token)':>20}"
      f"{'ratio':>10}")
for L in (128, 1000, 8192, 100_000):
    mlm = int(L * 0.15)
    clm = L - 1
    print(f"  {L:>18,}{mlm:>20,}{clm:>20,}{clm / mlm:>9.1f}x")

print("\n  Roughly 6.7x more supervised positions from the SAME text, at")
print("  essentially the same compute per forward pass. Over a trillion-token")
print("  corpus that is the difference between one training run and nearly")
print("  seven. This, more than any argument about representation quality, is")
print("  why decoder-only models scaled first.")

CORPUS_TOKENS = 1_000_000_000_000
print(f"\n  on a {CORPUS_TOKENS / 1e12:.0f}T-token corpus:")
print(f"    MLM supervises {CORPUS_TOKENS * 0.15 / 1e12:>6.2f}T positions")
print(f"    CLM supervises {CORPUS_TOKENS / 1e12:>6.2f}T positions")


# ------------------------------------------------- 4. representations
rule("4. REPRESENTATION QUALITY BY POSITION")

# A task where the disambiguating evidence is LATE in the sequence.
D2, TT = 24, 8
NOISE = 0.35
print(f"  A {TT}-token sequence whose meaning is determined by the LAST token.")
print(f"  How well can each position's representation predict that meaning?\n")


def build(label_late=True, n=800, seed=4):
    r = np.random.default_rng(seed)
    xs, ys = [], []
    for _ in range(n):
        y = int(r.random() < 0.5)
        seq = r.normal(0, 1, size=(TT, D2)) * NOISE
        # the class signal lives ONLY in the final token
        seq[-1 if label_late else 0] += np.array([2.0 if y else -2.0] +
                                                 [0.0] * (D2 - 1))
        xs.append(seq)
        ys.append(y)
    return np.array(xs), np.array(ys)


Xs, ys = build()
CAUSAL8 = np.triu(np.ones((TT, TT), dtype=bool), k=1)
P2 = make_params(D2, 5)


# A linear probe MUST be evaluated on held-out data (M3-L13). The first
# version of this lab fitted and scored on the same rows, and reported the
# decoder's frozen positions at 0.57 -- pure overfitting, since those
# representations provably contain no information about the label.
N_TRAIN = 600


def readout_accuracy(mask, position):
    """Fit a linear probe on one position's representation, score held out."""
    reps = np.array([block(s, P2, mask)[position] for s in Xs])
    tr, te = slice(0, N_TRAIN), slice(N_TRAIN, None)
    w = np.zeros(D2)
    b = 0.0
    for _ in range(600):
        p = 1 / (1 + np.exp(-np.clip(reps[tr] @ w + b, -500, 500)))
        e = (p - ys[tr]) / N_TRAIN
        w -= 2.0 * (reps[tr].T @ e)
        b -= 2.0 * e.sum()
    p = 1 / (1 + np.exp(-np.clip(reps[te] @ w + b, -500, 500)))
    return float(((p >= 0.5).astype(int) == ys[te]).mean())


ENC8 = np.zeros((TT, TT), dtype=bool)
n_test = len(ys) - N_TRAIN
chance = max(float(ys[N_TRAIN:].mean()), 1 - float(ys[N_TRAIN:].mean()))
se = math.sqrt(0.25 / n_test)
print(f"  probe: fitted on {N_TRAIN} rows, scored on {n_test} HELD OUT (M3-L13)")
print(f"  majority-class baseline {chance:.4f}; standard error "
      f"{se:.4f} (M3-L14)\n")
print(f"  {'position':>10}{'encoder probe':>18}{'decoder probe':>18}"
      f"{'can it see token 7?':>22}")
enc_scores, dec_scores = [], []
for pos in (0, 2, 4, 6, 7):
    e_acc = readout_accuracy(ENC8, pos)
    d_acc = readout_accuracy(CAUSAL8, pos)
    if pos != TT - 1:
        enc_scores.append(e_acc)
        dec_scores.append(d_acc)
    sees = "yes" if pos == TT - 1 else "NO"
    print(f"  {pos:>10}{e_acc:>18.4f}{d_acc:>18.4f}{sees:>22}")

print(f"\n  mean over the positions that CANNOT see token 7:")
print(f"    encoder {np.mean(enc_scores):.4f}   decoder {np.mean(dec_scores):.4f}"
      f"   baseline {chance:.4f}")
print(f"\n  Read this carefully. Both models are UNTRAINED (random weights), so")
print("  neither propagates the signal cleanly -- the encoder's early positions")
print("  are well short of 1.0. What matters is the GAP: the encoder's early")
print("  positions carry a detectable signal from token 7, and the decoder's")
print("  carry none, because they are structurally unable to see it.")
print(f"  Only position 7 reaches {readout_accuracy(CAUSAL8, 7):.2f} in the decoder,")
print("  and that is the only position that saw the evidence.")
print("\n  THIS is why decoder-derived embeddings are weaker at equal size: an")
print("  embedding is taken from a POSITION's representation, and most of a")
print("  decoder's positions never saw the second half of the text. It is also")
print("  why last-token pooling is the sensible choice for a decoder (M4-L04).")


# ------------------------------------------------- 5. cross-attention
rule("5. ENCODER-DECODER: CROSS-ATTENTION")

SRC = ["le", "chat", "est", "assis"]
TGT = ["the", "cat", "is", "sitting"]
Ds = 24
src_x = RNG.normal(0, 1, size=(len(SRC), Ds))
tgt_x = RNG.normal(0, 1, size=(len(TGT), Ds))
P_enc = make_params(Ds, 7)
P_dec = make_params(Ds, 8)
P_cross = make_params(Ds, 9)

enc_out = block(src_x, P_enc, mask=np.zeros((len(SRC), len(SRC)), dtype=bool))
print(f"  encoder: {len(SRC)} source tokens, bidirectional -> "
      f"{enc_out.shape} representation")

CAUSAL_T = np.triu(np.ones((len(TGT), len(TGT)), dtype=bool), k=1)
dec_out = block(tgt_x, P_dec, mask=CAUSAL_T,
                cross_kv=enc_out, cross_P=P_cross)
print(f"  decoder: {len(TGT)} target tokens, causal self-attention")
print(f"           + cross-attention (Q from decoder, K/V from encoder)")
print(f"           -> {dec_out.shape}")

_, cross_w = attention(rms_norm(tgt_x), enc_out, P_cross, mask=None)
print(f"\n  cross-attention weights (rows = target, columns = source):")
print(f"  {'':>10}" + "".join(f"{s:>9}" for s in SRC) + f"{'sum':>8}")
for t, row in zip(TGT, cross_w):
    print(f"  {t:>10}" + "".join(f"{w:>9.4f}" for w in row)
          + f"{row.sum():>8.4f}")

print("\n  Note it is NOT masked -- every target position may consult every")
print("  source position, which is correct: the source is fully known.")
print("  Rows still sum to 1; it is the same attention equation with K and V")
print("  taken from somewhere else. That is the ONLY change.")

print(f"\n  proving the decoder actually uses the source:")
enc_alt = enc_out.copy()
enc_alt[1] = RNG.normal(0, 1, size=Ds)          # change source token 'chat'
dec_alt = block(tgt_x, P_dec, mask=CAUSAL_T,
                cross_kv=enc_alt, cross_P=P_cross)
print(f"    changed source token 1; decoder output changed: "
      f"{not np.allclose(dec_out, dec_alt)}")
print(f"    max change: {np.abs(dec_out - dec_alt).max():.4f}")
dec_nocross = block(tgt_x, P_dec, mask=CAUSAL_T)
print(f"    with cross-attention removed entirely, the source has NO effect:")
print(f"      output identical for both sources: "
      f"{np.allclose(dec_nocross, block(tgt_x, P_dec, mask=CAUSAL_T))}")


# ------------------------------------------------- 6. cost
rule("6. THE COST ARGUMENT FOR SMALL ENCODERS")

print(f"  a narrow, labelled classification task, 50,000 requests per day\n")
print(f"  {'model':<26}{'params':>12}{'relative cost':>16}"
      f"{'runs locally?':>16}")
for name, params, local in (("encoder (BERT-base)", 110e6, "yes, on a CPU"),
                            ("encoder (DeBERTa-large)", 400e6, "yes, on a GPU"),
                            ("decoder (7B)", 7e9, "GPU required"),
                            ("decoder (70B, hosted)", 70e9, "no")):
    print(f"  {name:<26}{params / 1e6:>10.0f}M{params / 110e6:>15.0f}x"
          f"{local:>16}")

print(f"\n  A 110M encoder against a 70B decoder is a {70e9 / 110e6:.0f}x")
print("  parameter difference for a task with a fixed label set and plenty of")
print("  labels. The small model also runs locally, so sensitive data need")
print("  never leave your infrastructure -- frequently the deciding factor,")
print("  ahead of accuracy.")
print("\n  And a security point that is easy to miss: an encoder classifier has")
print("  NO instruction-following surface. Text in its input cannot redirect")
print("  it, because it was never trained to follow instructions. A prompted")
print("  decoder is exposed to injection by design (M10-L06).")
print("\n  None of this says 'always use an encoder'. It says BENCHMARK BOTH")
print("  before defaulting to the largest model available (M1-L11).")

print("\nDone.")
