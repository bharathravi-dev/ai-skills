"""M3-L12 lab -- learning rates, batches, optimizers and schedules.

Reproduces the lesson's worked example, sweeps the learning rate through every
failure mode, compares batch sizes, races SGD / momentum / Adam on a badly
scaled problem, measures bias correction, compares schedules, and shows
gradient clipping preventing divergence.

Run:  python labs/m3/l12_optimizers.py
"""

from __future__ import annotations

import math
import time

import numpy as np

RNG = np.random.default_rng(0)


def rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


# ------------------------------------------------------- 1. worked example
rule("1. ONE STEP, FOUR OPTIMIZERS  (g = [0.5, 0.02], lr = 0.1)")

g = np.array([0.5, 0.02])
LR = 0.1

sgd_step = -LR * g
print(f"  SGD           delta = {np.round(sgd_step, 6)}")
print(f"                ratio between the two = "
      f"{abs(sgd_step[0] / sgd_step[1]):.0f}x  (same as the gradient ratio)")

v_prev = np.array([0.4, 0.03])
v_new = 0.9 * v_prev + g
mom_step = -LR * v_new
print(f"\n  Momentum      v     = {np.round(v_new, 6)}")
print(f"                delta = {np.round(mom_step, 6)}")
print(f"                |delta[0]| vs plain SGD: "
      f"{abs(mom_step[0]) / abs(sgd_step[0]):.2f}x larger")

B1, B2, EPS = 0.9, 0.999, 1e-8
m = (1 - B1) * g
v = (1 - B2) * g**2
m_hat = m / (1 - B1**1)
v_hat = v / (1 - B2**1)
adam_step = -LR * m_hat / (np.sqrt(v_hat) + EPS)
print(f"\n  Adam (t=1)    m     = {np.round(m, 8)}")
print(f"                v     = {v}")
print(f"                m_hat = {np.round(m_hat, 8)}")
print(f"                v_hat = {v_hat}")
print(f"                delta = {np.round(adam_step, 6)}")
print(f"                BOTH parameters moved by exactly the learning rate "
      f"({LR}), despite")
print(f"                gradients differing {g[0] / g[1]:.0f}x.")

adam_nobc = -LR * m / (np.sqrt(v) + EPS)
print(f"\n  Adam, NO bias correction:")
print(f"                delta = {np.round(adam_nobc, 6)}")
print(f"                ratio to corrected = "
      f"{abs(adam_nobc[0] / adam_step[0]):.4f}x  -> TOO LARGE, not too small")
print(f"                (m is under-scaled 10x, sqrt(v) 31.6x; 31.6/10 = "
      f"{math.sqrt(1 / (1 - B2)) / (1 / (1 - B1)):.3f})")


# ------------------------------------------------------- 2. LR sweep
rule("2. LEARNING RATE SWEEP  (the M3-L11 network, 300 steps)")

Xs = RNG.normal(0, 1, size=(500, 2))
ys = ((Xs[:, 0] + Xs[:, 1] > 0) ^ (RNG.random(500) < 0.05)).astype(float).reshape(-1, 1)


def train_net(lr, steps=300, clip=None, init_scale=0.5, seed=7, schedule=None):
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, init_scale, size=(2, 8))
    b1 = np.zeros(8)
    W2 = rng.normal(0, init_scale, size=(8, 1))
    b2 = np.zeros(1)
    history = []
    for t in range(steps):
        z1 = Xs @ W1 + b1
        h1 = np.maximum(0.0, z1)
        p = sigmoid(h1 @ W2 + b2)
        pc = np.clip(p, 1e-12, 1 - 1e-12)
        loss = float(-(ys * np.log(pc) + (1 - ys) * np.log(1 - pc)).mean())
        history.append(loss)
        d2 = (p - ys) / len(Xs)
        gW2, gb2 = h1.T @ d2, d2.sum(axis=0)
        d1 = (d2 @ W2.T) * (z1 > 0)
        gW1, gb1 = Xs.T @ d1, d1.sum(axis=0)
        if clip is not None:
            norm = math.sqrt(sum(float((q**2).sum()) for q in (gW1, gb1, gW2, gb2)))
            if norm > clip:
                s = clip / norm
                gW1, gb1, gW2, gb2 = gW1 * s, gb1 * s, gW2 * s, gb2 * s
        step_lr = lr if schedule is None else schedule(t, steps, lr)
        W1 -= step_lr * gW1
        b1 -= step_lr * gb1
        W2 -= step_lr * gW2
        b2 -= step_lr * gb2
    return history


def classify(hist, best_known=0.31):
    """Diagnose a loss curve the way you would by eye."""
    final = hist[-1]
    if not math.isfinite(final):
        return "DIVERGED (nan/inf)"
    tail = hist[-50:]
    swing = max(tail) - min(tail)
    if swing > 0.02:
        return "OSCILLATING (lr too high)"
    still_falling = (hist[-100] - final) > 0.005
    if final <= best_known + 0.02:
        return "CONVERGED (good)"
    if still_falling:
        return "TOO SLOW (still falling at the end)"
    return "FLAT AND HIGH (lr too low / stuck)"


print(f"  {'lr':>8}{'start loss':>13}{'final loss':>13}{'min loss':>12}   diagnosis")
for lr in (1e-4, 1e-3, 1e-2, 0.1, 1.0, 10.0, 100.0):
    with np.errstate(over="ignore", invalid="ignore"):
        h = train_net(lr)
    finite = [x for x in h if math.isfinite(x)]
    fin = f"{h[-1]:.4f}" if math.isfinite(h[-1]) else "nan"
    mn = f"{min(finite):.4f}" if finite else "n/a"
    print(f"  {lr:>8}{h[0]:>13.4f}{fin:>13}{mn:>12}   {classify(h)}")


# ------------------------------------------------------- 3. batch size
rule("3. BATCH SIZE: GRADIENT NOISE AND WALL-CLOCK")

Xb = RNG.normal(0, 1, size=(4096, 20))
true_w = RNG.normal(0, 1, size=20)
yb = (Xb @ true_w + RNG.normal(0, 0.5, size=4096) > 0).astype(float)
w0 = np.zeros(20)


def grad_at(idx, w):
    Xi, yi = Xb[idx], yb[idx]
    return Xi.T @ (sigmoid(Xi @ w) - yi) / len(idx)


full_grad = grad_at(np.arange(4096), w0)
print(f"  {'batch':>8}{'grad norm sd':>16}{'cosine to full':>17}"
      f"{'steps/epoch':>14}{'ms/epoch':>12}")
for bs in (1, 8, 64, 512, 4096):
    samples = []
    for _ in range(200):
        idx = RNG.choice(4096, size=bs, replace=False)
        samples.append(grad_at(idx, w0))
    S = np.array(samples)
    sd = float(S.std(axis=0).mean())
    cos = float(np.mean([
        s @ full_grad / (np.linalg.norm(s) * np.linalg.norm(full_grad))
        for s in S]))
    steps = math.ceil(4096 / bs)
    t0 = time.perf_counter()
    for start in range(0, 4096, bs):
        grad_at(np.arange(start, min(start + bs, 4096)), w0)
    ms = (time.perf_counter() - t0) * 1000
    print(f"  {bs:>8}{sd:>16.5f}{cos:>17.4f}{steps:>14}{ms:>12.1f}")

print("\n  Noise falls as 1/sqrt(batch): quadrupling the batch should halve the sd.")
print("  Batch 4096 is the full dataset, so its sd is exactly 0 (it IS the answer).")


# ------------------------------------------------------- 4. optimizer race
rule("4. SGD vs MOMENTUM vs ADAM  (ill-conditioned bowl, curvature ratio 1000:1)")

# f(x, y) = 0.5 * (x^2 + 1000 y^2).  Minimum at (0, 0).
# The gradient is [x, 1000y]: one direction is 1000x steeper than the other.
CURV = np.array([1.0, 1000.0])
START = np.array([1.0, 1.0])
TARGET = 1e-6


def bowl_loss(p):
    return 0.5 * float((CURV * p**2).sum())


def bowl_run(kind, lr, steps=20000):
    p = START.copy()
    vel = np.zeros(2)
    m = np.zeros(2)
    vv = np.zeros(2)
    reached = None
    for t in range(1, steps + 1):
        grad = CURV * p
        if kind == "sgd":
            p = p - lr * grad
        elif kind == "momentum":
            vel = 0.9 * vel + grad
            p = p - lr * vel
        else:
            m = B1 * m + (1 - B1) * grad
            vv = B2 * vv + (1 - B2) * grad**2
            p = p - lr * (m / (1 - B1**t)) / (np.sqrt(vv / (1 - B2**t)) + EPS)
        loss = bowl_loss(p)
        if not math.isfinite(loss) or loss > 1e12:
            return None, t, p
        if reached is None and loss < TARGET:
            reached = t
    return reached, steps, p


# SGD on this bowl is stable only while lr < 2 / max_curvature = 0.002.
print(f"  {'optimizer':<12}{'lr':>8}{'steps to loss < 1e-6':>24}{'final loss':>14}")
results = {}
for kind, lr in (("sgd", 0.0019), ("sgd", 0.0021), ("momentum", 0.0005),
                 ("adam", 0.1)):
    reached, ran, p = bowl_run(kind, lr)
    results[(kind, lr)] = reached
    if reached is None:
        fl = bowl_loss(p)
        label = "DIVERGED" if not math.isfinite(fl) or fl > 1e12 else "not reached"
        shown = f"{fl:.3e}" if math.isfinite(fl) else "inf"
        print(f"  {kind:<12}{lr:>8}{label:>24}{shown:>14}")
    else:
        print(f"  {kind:<12}{lr:>8}{reached:>24,}{bowl_loss(p):>14.3e}")

sgd_steps = results[("sgd", 0.0019)]
adam_steps = results[("adam", 0.1)]
if sgd_steps and adam_steps:
    print(f"\n  Adam is {sgd_steps / adam_steps:.0f}x fewer steps than the fastest")
    print("  STABLE SGD rate. SGD cannot simply use a larger rate: at lr = 0.021 it")
    print("  exceeds the stability limit 2/1000 = 0.002 and diverges. One learning")
    print("  rate must serve both directions, so it is capped by the STEEPEST one")
    print("  while the shallowest one crawls. Adam rescales each direction separately.")

# ------------------------------------------------------- 5. schedules
rule("5. SCHEDULES  (300 steps, peak lr = 0.5)")


def cosine(t, total, peak):
    return peak * 0.5 * (1 + math.cos(math.pi * t / total))


def warmup_cosine(t, total, peak, warm=30):
    if t < warm:
        return peak * (t + 1) / warm
    return peak * 0.5 * (1 + math.cos(math.pi * (t - warm) / (total - warm)))


print(f"  {'schedule':<20}{'final loss':>14}{'min loss':>12}{'last-50 swing':>16}")
for name, sched in (("constant", None), ("cosine", cosine),
                    ("warmup + cosine", warmup_cosine)):
    h = train_net(0.5, schedule=sched)
    print(f"  {name:<20}{h[-1]:>14.4f}{min(h):>12.4f}"
          f"{max(h[-50:]) - min(h[-50:]):>16.5f}")

print("\n  LR profile for warmup + cosine (peak 0.5, 30 warmup steps of 300):")
pts = [0, 10, 29, 30, 75, 150, 225, 299]
print("    step: " + " ".join(f"{p:>7}" for p in pts))
print("      lr: " + " ".join(f"{warmup_cosine(p, 300, 0.5):>7.4f}" for p in pts))


# ------------------------------------------------------- 6. clipping
rule("6. GRADIENT CLIPPING  (one poisoned batch in an otherwise fine run)")

# Linear regression on well-behaved synthetic data, except that ONE row carries
# an extreme feature and target -- the kind of thing a bad ETL job produces.
# It lands in exactly one mini-batch, and that batch's gradient is enormous.
Xc = RNG.normal(0, 1, size=(512, 4))
wc_true = np.array([1.5, -2.0, 0.5, 3.0])
yc = Xc @ wc_true + RNG.normal(0, 0.1, size=512)
Xc[300] = np.array([1e4, -1e4, 1e4, -1e4])      # the poisoned row
yc[300] = 1e6


def train_clip(clip, lr=0.05, epochs=40, batch=32):
    w = np.zeros(4)
    peak_norm = 0.0
    poisoned_step = None
    for ep in range(epochs):
        for start_i in range(0, len(Xc), batch):
            Xi = Xc[start_i:start_i + batch]
            yi = yc[start_i:start_i + batch]
            grad = Xi.T @ (Xi @ w - yi) / len(Xi)
            norm = float(np.linalg.norm(grad))
            if math.isfinite(norm):
                peak_norm = max(peak_norm, norm)
            if start_i <= 300 < start_i + batch and poisoned_step is None:
                poisoned_step = norm
            if clip is not None and norm > clip:
                grad = grad * (clip / norm)
            w = w - lr * grad
    final = Xc[:300] @ w - yc[:300]
    clean_mse = float((final**2).mean())
    return w, peak_norm, poisoned_step, clean_mse


print(f"  {'setting':<26}{'peak grad norm':>18}{'MSE on clean rows':>20}  verdict")
for label, clip in (("no clipping", None), ("clip at global norm 1.0", 1.0)):
    with np.errstate(over="ignore", invalid="ignore"):
        w, peak, poisoned, mse = train_clip(clip)
    peak_s = f"{peak:.3e}" if math.isfinite(peak) else "inf"
    mse_s = (f"{mse:.4f}" if math.isfinite(mse) and mse < 1e6
             else (f"{mse:.3e}" if math.isfinite(mse) else "nan"))
    ok = "usable model" if math.isfinite(mse) and mse < 1.0 else "MODEL DESTROYED"
    print(f"  {label:<26}{peak_s:>18}{mse_s:>22}  {ok}")
    shown = np.round(w, 3) if math.isfinite(mse) and mse < 1e6 else w
    print(f"    learned weights: {shown}")
print(f"\n  true weights:      {wc_true}")
print("\n  One row out of 512 -- 0.2% of the data -- is enough to destroy the run")
print("  without clipping. Clipping caps the damage that any single batch can do,")
print("  which is why essentially all long training runs use it.")


# ------------------------------------------------------- 7. memory
rule("7. OPTIMIZER STATE MEMORY  (float32)")

print(f"  {'optimizer':<14}{'state copies':>15}{'100k params':>15}"
      f"{'7B params':>15}{'total w/ grads':>18}")
for name, copies in (("SGD", 0), ("Momentum", 1), ("Adam / AdamW", 2)):
    small = 100_000 * 4 * copies / 1024**2
    big = 7e9 * 4 * copies / 1024**3
    total = 7e9 * 4 * (2 + copies) / 1024**3      # params + grads + state
    print(f"  {name:<14}{copies:>15}{small:>12.1f} MB{big:>12.1f} GB"
          f"{total:>15.1f} GB")
print("\n  A 7B model needs ~26 GB to serve in float32 but ~104 GB to train with")
print("  Adam, before activations. That gap is why 'it fits for inference' does")
print("  not mean 'it fits for training'.")

print("\nDone.")
