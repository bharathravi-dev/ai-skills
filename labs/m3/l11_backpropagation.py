"""M3-L11 lab -- backpropagation, every gradient by hand and verified.

Reproduces the M3-L10 network's forward pass, computes every gradient
analytically, verifies each one numerically, demonstrates ReLU routing and
dead units, trains end to end, and measures per-layer gradient norms.

Run:  python labs/m3/l11_backpropagation.py
"""

from __future__ import annotations

import time

import numpy as np

RNG = np.random.default_rng(0)


def rule(title: str) -> None:
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


# ----------------------------------------------------------------- 1. network
# The exact network from M3-L10 section 6.
W1 = np.array([[0.5, -0.3], [0.8, 0.6]])
B1 = np.array([0.1, 0.2])
W2 = np.array([[1.2], [-0.7]])
B2 = np.array([-0.4])


def forward(x, W1, B1, W2, B2):
    """Forward pass, returning the probability and every cached intermediate."""
    z1 = x @ W1 + B1
    h1 = np.maximum(0.0, z1)
    z2 = h1 @ W2 + B2
    p = sigmoid(z2)
    return p, {"x": x, "z1": z1, "h1": h1, "z2": z2, "p": p}


def loss_bce(p, y):
    """Binary cross-entropy, clipped so log(0) cannot occur."""
    p = np.clip(np.asarray(p, dtype=float).reshape(-1)[0], 1e-12, 1 - 1e-12)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)))


def backward(cache, y, W2):
    """Backward pass. Returns the gradient of every parameter."""
    delta2 = cache["p"] - y                    # sigmoid + BCE, already cancelled
    dW2 = np.outer(cache["h1"], delta2)        # (2,) x (1,) -> (2,1)
    dB2 = delta2
    dh1 = delta2 @ W2.T                        # push back through the layer
    delta1 = dh1 * (cache["z1"] > 0)           # push back through ReLU
    dW1 = np.outer(cache["x"], delta1)         # (2,) x (2,) -> (2,2)
    dB1 = delta1
    return {"W1": dW1, "b1": dB1, "W2": dW2, "b2": dB2}


rule("1. FORWARD PASS  (x = [1.0, 2.0], y = 1)")

x = np.array([1.0, 2.0])
y = 1.0
p, cache = forward(x, W1, B1, W2, B2)
L = loss_bce(p, y)

print(f"  z1 = {np.round(cache['z1'], 4)}")
print(f"  h1 = {np.round(cache['h1'], 4)}   (ReLU passed both units)")
print(f"  z2 = {float(cache['z2'][0]):.4f}")
print(f"  p  = {float(p[0]):.4f}")
print(f"  L  = -log(p) = {L:.4f}")


rule("2. BACKWARD PASS  (compare with the lesson's hand calculation)")

grads = backward(cache, y, W2)
delta2 = float(cache["p"][0] - y)

print(f"  Step 1  dL/dz2 = p - y = {float(p[0]):.4f} - 1 = {delta2:+.4f}")
print("          (negative: raising z2 lowers the loss -- correct, we want p -> 1)")
print()
print(f"  Step 2  dL/dW2[0] = h1[0] * d2 = {cache['h1'][0]:.1f} * {delta2:+.4f} "
      f"= {grads['W2'][0, 0]:+.4f}")
print(f"          dL/dW2[1] = h1[1] * d2 = {cache['h1'][1]:.1f} * {delta2:+.4f} "
      f"= {grads['W2'][1, 0]:+.4f}")
ratio = grads["W2"][0, 0] / grads["W2"][1, 0]
print(f"          ratio = {ratio:.4f}  (= h1[0]/h1[1] = "
      f"{cache['h1'][0] / cache['h1'][1]:.4f})")
print(f"          dL/db2 = {float(grads['b2'][0]):+.4f}")
print()
dh1 = delta2 * W2.T[0]
print(f"  Step 3  dL/dh1 = {np.round(dh1, 4)}   (signs differ: W2[1] is negative)")
print(f"  Step 4  dL/dz1 = {np.round(grads['b1'], 4)}   (both z1 > 0, both pass)")
print()
print("  Step 5  dL/dW1 =")
print(f"            from x[0]=1.0:  {grads['W1'][0, 0]:+.4f}   {grads['W1'][0, 1]:+.4f}")
print(f"            from x[1]=2.0:  {grads['W1'][1, 0]:+.4f}   {grads['W1'][1, 1]:+.4f}")
print()
print("  Step 6  shape check (every gradient must match its parameter):")
for name, param in (("W1", W1), ("b1", B1), ("W2", W2), ("b2", B2)):
    ok = grads[name].shape == param.shape
    print(f"            {name}: grad {str(grads[name].shape):8s} param "
          f"{str(param.shape):8s} {'OK' if ok else 'MISMATCH'}")


rule("3. GRADIENT CHECKING  (central difference, h = 1e-5)")

PARAMS = {"W1": W1, "b1": B1, "W2": W2, "b2": B2}


def total_loss(params, x, y):
    p, _ = forward(x, params["W1"], params["b1"], params["W2"], params["b2"])
    return loss_bce(p, y)


def numerical_grad(params, name, index, x, y, h=1e-5):
    plus = {k: v.copy() for k, v in params.items()}
    minus = {k: v.copy() for k, v in params.items()}
    plus[name][index] += h
    minus[name][index] -= h
    return (total_loss(plus, x, y) - total_loss(minus, x, y)) / (2 * h)


def check_all(params, x, y, grads):
    rows = []
    for name in ("W1", "b1", "W2", "b2"):
        for index in np.ndindex(params[name].shape):
            g_a = float(grads[name][index])
            g_n = numerical_grad(params, name, index, x, y)
            rel = abs(g_a - g_n) / (max(abs(g_a), abs(g_n)) + 1e-12)
            rows.append((f"{name}{list(index)}", g_a, g_n, rel))
    return rows


rows = check_all(PARAMS, x, y, grads)
print(f"  {'parameter':<12}{'analytic':>12}{'numerical':>12}{'rel error':>14}")
worst = 0.0
for label, g_a, g_n, rel in rows:
    worst = max(worst, rel)
    print(f"  {label:<12}{g_a:>12.6f}{g_n:>12.6f}{rel:>14.2e}")
print(f"\n  worst relative error over all {len(rows)} parameters: {worst:.2e}")
print(f"  verdict: {'CORRECT (< 1e-7)' if worst < 1e-7 else 'SUSPECT'}")


rule("4. THE SAME CHECK WITH A DELIBERATE BUG  (ReLU mask removed)")


def backward_buggy(cache, y, W2):
    delta2 = cache["p"] - y
    dW2 = np.outer(cache["h1"], delta2)
    dh1 = delta2 @ W2.T
    delta1 = dh1                                # BUG: no ReLU mask
    return {"W1": np.outer(cache["x"], delta1), "b1": delta1,
            "W2": dW2, "b2": delta2}


for label, xv in (("both units active  x = [ 1.0, 2.0]", np.array([1.0, 2.0])),
                  ("unit 1 clipped     x = [-2.0, 0.5]", np.array([-2.0, 0.5]))):
    p_i, c_i = forward(xv, W1, B1, W2, B2)
    bad = backward_buggy(c_i, y, W2)
    rows_b = check_all(PARAMS, xv, y, bad)
    worst_b = max(r[3] for r in rows_b)
    broken = [r[0] for r in rows_b if r[3] > 1e-4]
    print(f"  {label}")
    print(f"    z1 = {np.round(c_i['z1'], 4)}   worst rel error = {worst_b:.2e}")
    print(f"    parameters broken by the bug: {broken if broken else 'none'}")
print("\n  The bug is INVISIBLE when every unit is active -- the mask is all ones.")
print("  It only shows up on inputs that clip a unit. A gradient check on one")
print("  lucky input would have passed.")


rule("5. ONE GRADIENT STEP  (alpha = 0.1)")

ALPHA = 0.1
W1n = W1 - ALPHA * grads["W1"]
B1n = B1 - ALPHA * grads["b1"]
W2n = W2 - ALPHA * grads["W2"]
B2n = B2 - ALPHA * grads["b2"]

p_new, _ = forward(x, W1n, B1n, W2n, B2n)
L_new = loss_bce(p_new, y)

print(f"  W1[0][0]: {W1[0, 0]:.4f} -> {W1n[0, 0]:.4f}")
print(f"  W2[0]   : {W2[0, 0]:.4f} -> {W2n[0, 0]:.4f}")
print(f"  b2      : {B2[0]:.4f} -> {B2n[0]:.4f}")
print(f"\n  p: {float(p[0]):.4f} -> {float(p_new[0]):.4f}")
print(f"  L: {L:.4f} -> {L_new:.4f}   ({'FELL' if L_new < L else 'ROSE'})")


rule("6. RELU BLOCKING  (x = [-2.0, 0.5], unit 1 clipped)")

x2 = np.array([-2.0, 0.5])
p2, cache2 = forward(x2, W1, B1, W2, B2)
grads2 = backward(cache2, y, W2)

print(f"  z1 = {np.round(cache2['z1'], 4)}   -> unit 1 is negative, ReLU clips it")
print(f"  h1 = {np.round(cache2['h1'], 4)}")
print(f"  dL/dh1 = {np.round(float(cache2['p'][0] - y) * W2.T[0], 4)}")
print(f"  dL/dz1 = {np.round(grads2['b1'], 4)}   <- unit 1's gradient is BLOCKED")
print()
print("  Gradients of the weights feeding hidden unit 1 (column 0 of W1):")
print(f"    dL/dW1[0][0] = {grads2['W1'][0, 0]:+.6f}")
print(f"    dL/dW1[1][0] = {grads2['W1'][1, 0]:+.6f}")
print("  Gradients of the weights feeding hidden unit 2 (column 1):")
print(f"    dL/dW1[0][1] = {grads2['W1'][0, 1]:+.6f}")
print(f"    dL/dW1[1][1] = {grads2['W1'][1, 1]:+.6f}")
col0_zero = np.all(grads2["W1"][:, 0] == 0.0)
print(f"\n  column 0 exactly zero: {col0_zero}  -- unit 1 learns NOTHING from this example")


rule("7. A DEAD RELU NEVER RECOVERS")

# Four hidden units; unit 3 is given a bias so negative it can never activate.
Wd = RNG.normal(0, 0.5, size=(3, 4))
Bd = np.array([0.1, 0.1, 0.1, -50.0])
Wo = RNG.normal(0, 0.5, size=(4, 1))
Bo = np.array([0.0])
Wd_start, Bd_start = Wd.copy(), Bd.copy()

Xd = RNG.normal(0, 1, size=(400, 3))
yd = (Xd[:, 0] + Xd[:, 1] > 0).astype(float).reshape(-1, 1)

for _ in range(2000):
    z1d = Xd @ Wd + Bd
    h1d = np.maximum(0.0, z1d)
    pd = sigmoid(h1d @ Wo + Bo)
    d2 = (pd - yd) / len(Xd)
    gWo, gBo = h1d.T @ d2, d2.sum(axis=0)
    d1 = (d2 @ Wo.T) * (z1d > 0)
    gWd, gBd = Xd.T @ d1, d1.sum(axis=0)
    Wd -= 0.5 * gWd
    Bd -= 0.5 * gBd
    Wo -= 0.5 * gWo
    Bo -= 0.5 * gBo

z1_final = Xd @ Wd + Bd
active = (z1_final > 0).mean(axis=0) * 100
print("  after 2000 training steps:")
print(f"    {'unit':<8}{'% inputs active':>18}{'weights changed?':>20}")
for u in range(4):
    changed = not np.array_equal(Wd[:, u], Wd_start[:, u])
    print(f"    {u:<8}{active[u]:>17.1f}%{str(changed):>20}")
print(f"\n  unit 3 bias: start {Bd_start[3]:.1f}  end {Bd[3]:.1f}  "
      f"(changed: {Bd[3] != Bd_start[3]})")
print("  Its weights are BIT-IDENTICAL to their starting values. Zero output ->")
print("  zero gradient -> unchanged weights -> zero output. Self-sustaining.")


rule("8. PER-LAYER GRADIENT NORMS  (12 layers, sigmoid vs ReLU)")


def layer_norms(activation: str, depth: int = 12, width: int = 32, seed: int = 1):
    rng = np.random.default_rng(seed)
    # Xavier-style init so the comparison is about the activation, not the scale.
    Ws = [rng.normal(0, np.sqrt(1.0 / width), size=(width, width))
          for _ in range(depth)]
    Bs = [np.zeros(width) for _ in range(depth)]
    Wout = rng.normal(0, np.sqrt(1.0 / width), size=(width, 1))

    X = rng.normal(0, 1, size=(64, width))
    yb = rng.integers(0, 2, size=(64, 1)).astype(float)

    zs, hs = [], [X]
    h = X
    for W, b in zip(Ws, Bs):
        z = h @ W + b
        zs.append(z)
        h = sigmoid(z) if activation == "sigmoid" else np.maximum(0.0, z)
        hs.append(h)
    p = sigmoid(h @ Wout)

    delta = (p - yb) / len(X)
    delta = delta @ Wout.T
    norms = []
    for i in range(depth - 1, -1, -1):
        delta = delta * (sigmoid(zs[i]) * (1 - sigmoid(zs[i]))
                         if activation == "sigmoid" else (zs[i] > 0))
        norms.append(np.linalg.norm(hs[i].T @ delta))
        delta = delta @ Ws[i].T
    return norms[::-1]          # layer 1 (nearest input) first


sig = layer_norms("sigmoid")
relu = layer_norms("relu")

print(f"  {'layer':<8}{'sigmoid |grad|':>18}{'ReLU |grad|':>16}{'ratio':>14}")
for i, (s, r) in enumerate(zip(sig, relu), start=1):
    tag = "  <- nearest input" if i == 1 else ("  <- nearest loss" if i == 12 else "")
    print(f"  {i:<8}{s:>18.3e}{r:>16.3e}{r / s if s > 0 else float('inf'):>14.1f}x{tag}")

print(f"\n  sigmoid: layer 12 / layer 1 = {sig[-1] / sig[0]:,.0f}x")
print(f"  ReLU   : layer 12 / layer 1 = {relu[-1] / relu[0]:,.1f}x")
print("\n  With sigmoid the early layers receive a vanishingly smaller gradient than")
print("  the late ones -- they barely learn. ReLU keeps the magnitudes comparable.")


rule("9. COST OF THE BACKWARD PASS  (~1M parameters)")

W_a = RNG.normal(0, 0.05, size=(512, 1024))
W_b = RNG.normal(0, 0.05, size=(1024, 512))
Xc = RNG.normal(0, 1, size=(128, 512))
n_params = W_a.size + W_b.size
REPS = 30


def fwd_only():
    hh = np.maximum(0.0, Xc @ W_a)
    return hh @ W_b, hh


def fwd_bwd():
    out, hh = fwd_only()
    d = out / len(Xc)
    _ = hh.T @ d
    dh = (d @ W_b.T) * (hh > 0)
    _ = Xc.T @ dh
    return None


for fn in (fwd_only, fwd_bwd):     # warm up
    fn()

t0 = time.perf_counter()
for _ in range(REPS):
    fwd_only()
t_fwd = (time.perf_counter() - t0) / REPS

t0 = time.perf_counter()
for _ in range(REPS):
    fwd_bwd()
t_both = (time.perf_counter() - t0) / REPS

print(f"  parameters            : {n_params:,}")
print(f"  forward only          : {t_fwd * 1000:.2f} ms")
print(f"  forward + backward    : {t_both * 1000:.2f} ms")
print(f"  ratio                 : {t_both / t_fwd:.2f}x")
print(f"\n  A naive forward-difference approach would need {n_params:,} forward")
print(f"  passes per step: {n_params * t_fwd:,.0f} s, about "
      f"{n_params * t_fwd / 3600:,.1f} hours -- for ONE step.")
print(f"  Backprop does it in {t_both * 1000:.2f} ms. That is the whole reason")
print("  deep learning is affordable.")

print("\nDone.")
