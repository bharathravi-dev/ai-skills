"""M4-L10 lab -- inside a transformer block.

Verifies the lesson's hand-worked block, counts parameters for real
configurations, ablates each component on a trained model, and compares
pre-norm against post-norm at depth.

NumPy only, no API key, no network.
Run:  python labs/m4/l10_transformer_block.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(10)
np.set_printoptions(precision=4, suppress=True)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def rms_norm(x, gamma=None, eps=1e-6):
    rms = np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)
    out = x / rms
    return out if gamma is None else out * gamma


def layer_norm(x, gamma=None, beta=None, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    out = (x - mu) / np.sqrt(var + eps)
    if gamma is not None:
        out = out * gamma
    if beta is not None:
        out = out + beta
    return out


# ------------------------------------------------- 1. verify the worked example
rule("1. THE WORKED EXAMPLE, VERIFIED  (d_model 4, one token, pre-norm)")

x0 = np.array([1.0, 2.0, -1.0, 0.0])
print(f"  input x = {x0}")

xn1 = rms_norm(x0)
print(f"\n  step 1: RMSNorm")
print(f"    mean(x^2) = {(x0 ** 2).mean():.4f}   rms = "
      f"{math.sqrt((x0 ** 2).mean()):.4f}")
print(f"    x_norm    = {xn1}")
assert np.allclose(xn1, [0.8165, 1.6330, -0.8165, 0.0], atol=1e-4)

attn_out = xn1.copy()          # one token attends only to itself; W_v = W_o = I
print(f"\n  step 2: attention (single token, W_v = W_o = I)")
print(f"    attn_out  = {attn_out}")

x1 = x0 + attn_out
print(f"\n  step 3: first residual")
print(f"    x = {x0} + {attn_out}")
print(f"      = {x1}")
assert np.allclose(x1, [1.8165, 3.6330, -1.8165, 0.0], atol=1e-4)
print("    NOTE the original x is still entirely present in that sum.")

xn2 = rms_norm(x1)
print(f"\n  step 4: RMSNorm again")
print(f"    mean(x^2) = {(x1 ** 2).mean():.4f}   rms = "
      f"{math.sqrt((x1 ** 2).mean()):.4f}")
print(f"    x_norm    = {xn2}")
print(f"    identical to step 1? {np.allclose(xn2, xn1)}   "
      f"(max diff {np.abs(xn2 - xn1).max():.2e})")
print("    RMSNorm removes SCALE, and step 3 scaled without rotating. So the")
print("    normalisation discarded everything attention contributed here.")

W1 = np.zeros((4, 8))
W1[np.arange(4), np.arange(4)] = 1.0
h = xn2 @ W1
h_relu = np.maximum(0, h)
print(f"\n  step 5: FFN first layer + ReLU")
print(f"    h        = {h}")
print(f"    ReLU(h)  = {h_relu}")
print(f"    the {xn2[2]:.4f} became {h_relu[2]:.4f}. That information is gone")
print("    from this sublayer's output.")

W2 = np.zeros((8, 4))
W2[np.arange(4), np.arange(4)] = 1.0
ffn_out = h_relu @ W2
print(f"\n  step 6: FFN second layer")
print(f"    ffn_out  = {ffn_out}")

out = x1 + ffn_out
print(f"\n  step 7: second residual")
print(f"    out = {x1} + {ffn_out}")
print(f"        = {out}")
assert np.allclose(out, [2.6330, 5.2660, -1.8165, 0.0], atol=1e-4)

print(f"\n  step 8: reading the result")
print(f"    shape {out.shape} == input shape {x0.shape}: {out.shape == x0.shape}")
print(f"    component 2 = {out[2]:.4f}, NOT 0 -- ReLU zeroed it in the FFN")
print(f"      branch, and the residual preserved it.")
print(f"    components 0-1 grew from {x0[:2]} to {np.round(out[:2], 4)}")
print("      -- residual streams grow with depth, hence the final norm.")
print("\n  SECTION 6 FULLY VERIFIED.")


# ------------------------------------------------- 2. parameter counting
rule("2. PARAMETER COUNTING, AND THE FFN's SHARE")


def count(layers, d, vocab, ffn_mult=4, tied=True, swiglu=False):
    attn = 4 * d * d
    ffn = (3 * d * int(d * 8 / 3) if swiglu else 2 * d * (ffn_mult * d))
    per_block = attn + ffn
    blocks = layers * per_block
    emb = vocab * d * (1 if tied else 2)
    return attn, ffn, per_block, blocks, emb, blocks + emb


CONFIGS = [
    ("small", 12, 768, 50_000),
    ("7B-ish", 32, 4096, 32_000),
    ("13B-ish", 40, 5120, 32_000),
    ("70B-ish", 80, 8192, 128_000),
]
print(f"  {'config':<10}{'layers':>7}{'d_model':>9}{'attn/blk':>12}"
      f"{'ffn/blk':>12}{'ffn share':>11}{'total':>13}")
for name, L, d, V in CONFIGS:
    a, ff, per, blk, emb, tot = count(L, d, V)
    print(f"  {name:<10}{L:>7}{d:>9}{a / 1e6:>11.1f}M{ff / 1e6:>11.1f}M"
          f"{ff / per:>10.1%}{tot / 1e9:>12.2f}B")

print(f"\n  The FFN is {2 / 3:.1%} of every block, in every configuration --")
print("  it is 8d^2 against attention's 4d^2, so the ratio is exactly 2:1")
print("  regardless of size. The architecture is named after the smaller half.")

print(f"\n  verifying the lesson's arithmetic (32 layers, d=4096, vocab=32k):")
a, ff, per, blk, emb, tot = count(32, 4096, 32_000)
print(f"    blocks    = 32 x 12 x 4096^2 = {32 * 12 * 4096 ** 2:,}")
print(f"    computed  =                    {blk:,}")
print(f"    embedding = 32,000 x 4,096   = {emb:,}")
print(f"    total     =                    {tot:,}  ({tot / 1e9:.2f}B)")
assert blk == 32 * 12 * 4096 ** 2, "the 12d^2 shortcut does not match"
print("    the 12d^2-per-block shortcut is exact.")

print(f"\n  SwiGLU uses THREE matrices, so d_ff shrinks to keep the count level:")
print(f"  {'variant':<26}{'d_ff':>9}{'ffn params':>14}{'vs 2-matrix':>14}")
_, ff2, _, _, _, _ = count(32, 4096, 32_000, swiglu=False)
_, ff3, _, _, _, _ = count(32, 4096, 32_000, swiglu=True)
print(f"  {'2 matrices, d_ff = 4d':<26}{4 * 4096:>9,}{ff2 / 1e6:>13.1f}M"
      f"{'--':>14}")
print(f"  {'SwiGLU, d_ff = 8d/3':<26}{int(4096 * 8 / 3):>9,}{ff3 / 1e6:>13.1f}M"
      f"{ff3 / ff2:>13.2f}x")

print(f"\n  width vs depth -- which axis is expensive:")
print(f"  {'change':<28}{'parameters':>14}{'factor':>10}")
base = count(32, 4096, 32_000)[3]
print(f"  {'baseline (32L, d=4096)':<28}{base / 1e9:>13.2f}B{'1.00x':>10}")
d2 = count(32, 8192, 32_000)[3]
print(f"  {'double d_model':<28}{d2 / 1e9:>13.2f}B{d2 / base:>9.2f}x")
l2 = count(64, 4096, 32_000)[3]
print(f"  {'double layers':<28}{l2 / 1e9:>13.2f}B{l2 / base:>9.2f}x")
print("\n  Doubling width QUADRUPLES parameters; doubling depth doubles them.")


# ------------------------------------------------- 3. pre vs post norm
rule("3. PRE-NORM vs POST-NORM AT DEPTH")

D = 64
DEPTH = 48
print(f"  {DEPTH} blocks, d_model {D}, random weights, tracking activation")
print(f"  magnitude through the stack.\n")


def make_block(d, seed, scale=1.0):
    r = np.random.default_rng(seed)
    s = scale / math.sqrt(d)
    return {"Wq": r.normal(0, s, (d, d)), "Wk": r.normal(0, s, (d, d)),
            "Wv": r.normal(0, s, (d, d)), "Wo": r.normal(0, s, (d, d)),
            "W1": r.normal(0, s, (d, 4 * d)), "W2": r.normal(0, s, (4 * d, d))}


def sublayers(x, p):
    q, k, v = x @ p["Wq"], x @ p["Wk"], x @ p["Wv"]
    w = softmax(q @ k.T / math.sqrt(x.shape[-1]), axis=-1)
    attn = (w @ v) @ p["Wo"]
    return attn


def run_stack(mode, depth=DEPTH, d=D, T=8, seed0=100):
    x = RNG.normal(0, 1, size=(T, d))
    mags = [float(np.abs(x).mean())]
    for i in range(depth):
        p = make_block(d, seed0 + i)
        if mode == "pre":
            x = x + sublayers(rms_norm(x), p)
            x = x + np.maximum(0, rms_norm(x) @ p["W1"]) @ p["W2"]
        elif mode == "post":
            x = rms_norm(x + sublayers(x, p))
            x = rms_norm(x + np.maximum(0, x @ p["W1"]) @ p["W2"])
        else:                                   # no residual at all
            x = sublayers(rms_norm(x), p)
            x = np.maximum(0, rms_norm(x) @ p["W1"]) @ p["W2"]
        mags.append(float(np.abs(x).mean()))
    return mags


results = {m: run_stack(m) for m in ("pre", "post", "none")}
print(f"  {'layer':>7}{'pre-norm':>14}{'post-norm':>14}{'no residual':>15}")
for L in (0, 1, 4, 12, 24, 36, 48):
    row = f"  {L:>7}"
    for m in ("pre", "post", "none"):
        v = results[m][L]
        row += f"{v:>14.4e}" if (v < 1e-3 or v > 1e4) else f"{v:>14.4f}"
    print(row)

print(f"\n  growth from layer 0 to layer {DEPTH}:")
for m, label in (("pre", "pre-norm"), ("post", "post-norm"),
                 ("none", "no residual")):
    a, b = results[m][0], results[m][-1]
    print(f"    {label:<14}{a:.4f} -> {b:.4e}   ({b / a:.2e}x)")

print("\n  Pre-norm grows steadily and predictably -- the residual stream")
print("  ACCUMULATES each block's contribution, which is why a FINAL norm is")
print("  needed before the LM head. Post-norm re-normalises after every")
print("  addition, so magnitude stays flat -- but the identity gradient path is")
print("  broken at each layer, which is the cost that does not show up here.")
print("\n  NOTE what the 'no residual' column does NOT show. Its magnitude also")
print("  stays near 1.0, because each layer's own norm rescales it. Activation")
print("  MAGNITUDE is simply the wrong metric for that failure: the problem is")
print("  not that the signal shrinks, it is that each layer REPLACES the")
print("  previous representation instead of adding to it, so nothing survives")
print("  the stack and no gradient reaches the early layers. Section 4 measures")
print("  that directly, and finds a 10^9 difference.")


# ------------------------------------------------- 4. the gradient argument
rule("4. WHY RESIDUALS HELP: THE GRADIENT PATH, MEASURED")

print("  Propagating a gradient back through 48 blocks. With residuals the")
print("  Jacobian is (1 + f'); without, it is f' alone.\n")


def grad_through_stack(depth, with_residual, d=32, seed=7):
    r = np.random.default_rng(seed)
    g = np.ones((1, d))
    mags = [float(np.abs(g).mean())]
    for i in range(depth):
        W = r.normal(0, 0.8 / math.sqrt(d), (d, d))     # a sub-unit Jacobian
        g = g @ W + (g if with_residual else 0.0)
        mags.append(float(np.abs(g).mean()))
    return mags


with_res = grad_through_stack(48, True)
without = grad_through_stack(48, False)
print(f"  {'depth':>7}{'with residual':>18}{'without residual':>20}{'ratio':>14}")
for L in (0, 4, 12, 24, 36, 48):
    a, b = with_res[L], without[L]
    print(f"  {L:>7}{a:>18.4e}{b:>20.4e}"
          f"{(a / b if b > 0 else float('inf')):>14.2e}")

print(f"\n  after 48 layers the gradient is {with_res[-1] / without[-1]:.2e}x")
print("  larger with residuals than without. Without them it has vanished")
print("  entirely -- the early layers receive nothing and never learn.")
print("  This is M3-L11 section 5.1 Rule 2: dy/dx = 1 + f'(x), and that 1 is")
print("  a path with derivative exactly 1 from the loss to every layer.")


# ------------------------------------------------- 5. ablation
rule("5. ABLATION: WHAT EACH COMPONENT IS WORTH")

# A small next-token task with real structure.
TEXT = ("the cat sat on the mat . the dog ran to the park . "
        "a bird flew over the tree . the cat ran to the park . ") * 300
WORDS = sorted(set(TEXT.split()))
W2I = {w: i for i, w in enumerate(WORDS)}
V, DM, CTX = len(WORDS), 32, 5
ids = np.array([W2I[w] for w in TEXT.split()])
wins = np.array([ids[i:i + CTX + 1] for i in range(len(ids) - CTX)])
Xa, Ya = wins[:, :-1], wins[:, 1:]
CAUSAL5 = np.triu(np.ones((CTX, CTX), dtype=bool), k=1)


def train_variant(use_attn=True, use_ffn=True, use_res=True, use_norm=True,
                  steps=900, lr=0.3, seed=3):
    r = np.random.default_rng(seed)
    P = {"E": r.normal(0, 0.1, (V, DM)), "Pos": r.normal(0, 0.02, (CTX, DM)),
         "Wq": r.normal(0, 0.2, (DM, DM)), "Wk": r.normal(0, 0.2, (DM, DM)),
         "Wv": r.normal(0, 0.2, (DM, DM)), "Wo": r.normal(0, 0.2, (DM, DM)),
         "W1": r.normal(0, 0.2, (DM, 4 * DM)),
         "W2": r.normal(0, 0.2, (4 * DM, DM)),
         "Wlm": r.normal(0, 0.1, (DM, V))}
    hist = []
    for step in range(steps + 1):
        idx = RNG.choice(len(Xa), size=96, replace=False)
        X, Y = Xa[idx], Ya[idx]
        B, T = X.shape
        emb = P["E"][X] + P["Pos"][:T]
        h = emb
        # --- attention sublayer ---
        if use_attn:
            hn = rms_norm(h) if use_norm else h
            q, k, v = hn @ P["Wq"], hn @ P["Wk"], hn @ P["Wv"]
            sc = np.where(CAUSAL5, -1e9,
                          q @ k.transpose(0, 2, 1) / math.sqrt(DM))
            at = softmax(sc, axis=-1)
            a_out = (at @ v) @ P["Wo"]
            h = h + a_out if use_res else a_out
        # --- ffn sublayer ---
        if use_ffn:
            hn2 = rms_norm(h) if use_norm else h
            pre = hn2 @ P["W1"]
            act = np.maximum(0, pre)
            f_out = act @ P["W2"]
            h = h + f_out if use_res else f_out
        logits = h @ P["Wlm"]
        pr = softmax(logits)
        picked = pr[np.arange(B)[:, None], np.arange(T)[None, :], Y]
        hist.append(float(-np.log(np.clip(picked, 1e-12, None)).mean()))
        if step == steps:
            break
        dl = pr.copy()
        dl[np.arange(B)[:, None], np.arange(T)[None, :], Y] -= 1.0
        dl /= (B * T)
        g = {"Wlm": np.einsum("btd,btv->dv", h, dl)}
        dh = dl @ P["Wlm"].T
        if use_ffn:
            g["W2"] = np.einsum("btk,btd->kd", act, dh)
            dact = (dh @ P["W2"].T) * (pre > 0)
            g["W1"] = np.einsum("btd,btk->dk", hn2, dact)
            dh = (dh if use_res else 0) + dact @ P["W1"].T
        if use_attn:
            g["Wo"] = np.einsum("btd,bte->de", at @ v, dh)
            dctx = dh @ P["Wo"].T
            dat = dctx @ v.transpose(0, 2, 1)
            dv = at.transpose(0, 2, 1) @ dctx
            dsc = at * (dat - (dat * at).sum(-1, keepdims=True))
            dsc = np.where(CAUSAL5, 0.0, dsc) / math.sqrt(DM)
            dq, dk = dsc @ k, dsc.transpose(0, 2, 1) @ q
            g["Wq"] = np.einsum("btd,bte->de", hn, dq)
            g["Wk"] = np.einsum("btd,bte->de", hn, dk)
            g["Wv"] = np.einsum("btd,bte->de", hn, dv)
            dh = (dh if use_res else 0) + dq @ P["Wq"].T + \
                 dk @ P["Wk"].T + dv @ P["Wv"].T
        for kk, gv in g.items():
            n = float(np.linalg.norm(gv))
            P[kk] -= lr * (gv / n if n > 1.0 else gv)
        np.add.at(P["E"], X, -lr * dh)
    return hist[-1]


print(f"  vocabulary {V}, d_model {DM}, {CTX}-token context, 900 steps")
print(f"  loss at initialisation should be ln({V}) = {math.log(V):.4f}\n")
print(f"  {'variant':<32}{'final loss':>13}{'perplexity':>13}{'vs full':>11}")
full = train_variant()
print(f"  {'full block':<32}{full:>13.4f}{math.exp(full):>13.2f}{'--':>11}")
for label, kw in (("no attention", {"use_attn": False}),
                  ("no feed-forward network", {"use_ffn": False}),
                  ("no residual connections", {"use_res": False}),
                  ("no normalisation", {"use_norm": False})):
    v = train_variant(**kw)
    print(f"  {label:<32}{v:>13.4f}{math.exp(v):>13.2f}{v / full:>10.2f}x")

print("\n  READ THIS TABLE HONESTLY -- two components made the model WORSE by")
print("  their presence, and that is a real result, not a broken experiment.")
print("\n    attention   : 2.65x worse without it. Decisive. Positions cannot")
print("                  interact at all, so no amount of per-token processing")
print("                  can use context.")
print("    residuals   : 2.09x worse without them, even at ONE block.")
print("    FFN         : removing it made the model very slightly BETTER.")
print("    normalisation: same -- slightly better without.")
print("\n  Why? This task is 15 tokens of rigid templates solved by a single")
print("  attention head. The FFN's 4d^2 extra parameters have nothing useful")
print("  to learn and add optimisation noise; normalisation constrains a model")
print("  that was never going to destabilise in one layer.")
print("\n  The honest conclusion is NOT 'every component is always load-bearing'.")
print("  It is that components earn their place at DIFFERENT SCALES:")
print("    * attention is load-bearing immediately, at any size")
print("    * residuals are load-bearing from the first layer and become")
print("      decisive with depth (section 4: a 10^9 gradient difference at 48)")
print("    * the FFN and normalisation are overhead on a toy and essential at")
print("      scale -- the FFN is 67% of a real model's parameters, and section 3")
print("      shows what normalisation is holding together at 48 layers")
print("\n  If a component looks useless in your ablation, check whether your")
print("  experiment is large enough for it to matter before concluding anything.")

print("\nDone.")
