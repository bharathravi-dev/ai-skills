"""M3-L14 lab -- classification and regression metrics, from scratch.

Every metric implemented directly from the confusion matrix, a threshold
sweep, ROC-AUC vs PR-AUC on imbalanced data, AUC's invariance to monotonic
transforms, a reliability diagram and ECE, baselines, macro vs micro
averaging, and regression metrics with and without an outlier.

All data is synthetic. Run:  python labs/m3/l14_metrics.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(0)


def rule(title: str) -> None:
    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


# ------------------------------------------------------------- metrics
def confusion(y_true, y_pred):
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    return tp, fp, fn, tn


def metrics(y_true, proba, threshold=0.5):
    tp, fp, fn, tn = confusion(y_true, (proba >= threshold).astype(int))
    acc = (tp + tn) / max(tp + fp + fn + tn, 1)
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    if math.isnan(prec) or math.isnan(rec) or prec + rec == 0:
        f1 = float("nan")
    else:
        f1 = 2 * prec * rec / (prec + rec)
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, acc=acc, prec=prec, rec=rec,
                spec=spec, f1=f1)


def fbeta(prec, rec, beta):
    if math.isnan(prec) or math.isnan(rec) or (beta**2 * prec + rec) == 0:
        return float("nan")
    return (1 + beta**2) * prec * rec / (beta**2 * prec + rec)


def roc_auc(y_true, score):
    """Probability a random positive outranks a random negative (ties = 0.5)."""
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), dtype=float)
    s = score[order]
    i = 0
    while i < len(s):                              # average ranks within ties
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return (ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def pr_auc(y_true, score):
    """Average precision: sum of precision at each threshold, weighted by the
    recall gained there."""
    order = np.argsort(-score, kind="mergesort")
    y = y_true[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / max(int(y_true.sum()), 1)
    prev_rec = 0.0
    ap = 0.0
    for p, r in zip(prec, rec):
        ap += p * (r - prev_rec)
        prev_rec = r
    return ap


# -------------------------------------------------- 1. confusion matrix
rule("1. EVERY METRIC FROM ONE CONFUSION MATRIX  (TP=40 FP=10 FN=60 TN=890)")

y_ex = np.concatenate([np.ones(100, dtype=int), np.zeros(900, dtype=int)])
p_ex = np.concatenate([np.ones(40), np.zeros(60), np.ones(10), np.zeros(890)])
m = metrics(y_ex, p_ex)

print(f"                  Predicted")
print(f"                  Neg      Pos")
print(f"  Actual  Neg  |{m['tn']:>7}{m['fp']:>9}  |")
print(f"          Pos  |{m['fn']:>7}{m['tp']:>9}  |")
print()
print(f"  accuracy    = ({m['tp']} + {m['tn']}) / 1000        = {m['acc']:.4f}")
print(f"  precision   = {m['tp']} / ({m['tp']} + {m['fp']})            "
      f"= {m['prec']:.4f}")
print(f"  recall      = {m['tp']} / ({m['tp']} + {m['fn']})            "
      f"= {m['rec']:.4f}")
print(f"  specificity = {m['tn']} / ({m['tn']} + {m['fp']})          "
      f"= {m['spec']:.4f}")
print(f"  F1          = 2PR/(P+R)               = {m['f1']:.4f}")
print(f"  F2 (recall-weighted)                  = "
      f"{fbeta(m['prec'], m['rec'], 2):.4f}")
print(f"  F0.5 (precision-weighted)             = "
      f"{fbeta(m['prec'], m['rec'], 0.5):.4f}")
maj = max((y_ex == 1).mean(), (y_ex == 0).mean())
print(f"\n  majority-class baseline accuracy      = {maj:.4f}")
print(f"  the model beats it by                 = {m['acc'] - maj:+.4f}")
print(f"  ... while missing {m['fn']} of {m['tp'] + m['fn']} positives.")

print("\n  F1 is the HARMONIC mean -- close to the smaller of P and R:")
print(f"  {'precision':>11}{'recall':>9}{'arithmetic':>13}{'F1':>9}")
for p_v, r_v in ((0.9, 0.9), (1.0, 0.5), (1.0, 0.1), (1.0, 0.01)):
    print(f"  {p_v:>11.2f}{r_v:>9.2f}{(p_v + r_v) / 2:>13.3f}"
          f"{2 * p_v * r_v / (p_v + r_v):>9.4f}")


# -------------------------------------------------- 2. threshold sweep
rule("2. ONE MODEL, MANY THRESHOLDS  (10,000 transactions, 1% fraud)")

n = 10000
Xm = RNG.normal(0, 1, size=(n, 5))
wm = np.array([1.4, -1.1, 0.9, 0.6, -0.4])
BASE = 0.01


def intercept_for(score, target):
    """Bisect for the intercept giving a mean predicted rate of `target`."""
    lo, hi = -50.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if sigmoid(score + mid).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# Ground truth: labels really are drawn from a logistic model, so a correctly
# specified model can be perfectly calibrated. This is the honest way to build
# a metrics lab -- the "right answer" is known.
s_true = Xm @ wm
b_true = intercept_for(s_true, BASE)
p_true = sigmoid(s_true + b_true)
ym = (RNG.random(n) < p_true).astype(int)

# The "model": estimated weights are slightly wrong (as they always are), and
# its intercept is fitted so its mean prediction matches the observed rate.
wm_hat = wm + RNG.normal(0, 0.22, size=5)
s_hat = Xm @ wm_hat
proba = sigmoid(s_hat + intercept_for(s_hat, ym.mean()))
base_rate = ym.mean()

print(f"  base rate = {base_rate:.4f}  ({int(ym.sum())} positives of {n})\n")
print(f"  {'thresh':>8}{'flagged':>9}{'TP':>6}{'FP':>7}{'FN':>6}"
      f"{'precision':>11}{'recall':>9}{'F1':>8}{'accuracy':>10}")
for t in (0.60, 0.40, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01):
    r = metrics(ym, proba, t)
    flagged = r["tp"] + r["fp"]
    pr = "nan" if math.isnan(r["prec"]) else f"{r['prec']:.4f}"
    f1s = "nan" if math.isnan(r["f1"]) else f"{r['f1']:.4f}"
    print(f"  {t:>8.2f}{flagged:>9}{r['tp']:>6}{r['fp']:>7}{r['fn']:>6}"
          f"{pr:>11}{r['rec']:>9.4f}{f1s:>8}{r['acc']:>10.4f}")

always_neg = metrics(ym, np.zeros(n))
print(f"\n  BASELINE (always negative): accuracy {always_neg['acc']:.4f}, "
      f"recall {always_neg['rec']:.4f}, fraud caught 0")
best_t = max(np.linspace(0.01, 0.99, 99),
             key=lambda t: (0 if math.isnan(metrics(ym, proba, t)["f1"])
                            else metrics(ym, proba, t)["f1"]))
print(f"  Highest-accuracy threshold in the sweep beats the baseline while")
print(f"  missing most of the fraud. Best-F1 threshold = {best_t:.2f}.")


rule("2b. FOUR ORGANISATIONS, FOUR THRESHOLDS, ONE MODEL")


def threshold_for_capacity(cap):
    for t in np.linspace(0.99, 0.001, 999):
        if (proba >= t).sum() >= cap:
            return float(t)
    return 0.001


def threshold_for_recall(target):
    """Lowest threshold meeting the recall target; None if unreachable."""
    for t in np.linspace(0.99, 0.0001, 2000):
        r = metrics(ym, proba, t)
        if not math.isnan(r["rec"]) and r["rec"] >= target:
            return float(t)
    return None


def threshold_for_cost(cost_fp, cost_fn):
    best, best_c = 0.5, float("inf")
    for t in np.linspace(0.01, 0.99, 99):
        r = metrics(ym, proba, t)
        c = r["fp"] * cost_fp + r["fn"] * cost_fn
        if c < best_c:
            best_c, best = c, float(t)
    return best, best_c


t_cap = threshold_for_capacity(20)
t_rec = threshold_for_recall(0.95)
t_rec_reachable = t_rec is not None
if t_rec is None:
    t_rec = 0.0001          # flag almost everything; still falls short
t_cost, c_cost = threshold_for_cost(5, 500)

print(f"  {'organisation':<34}{'method':<20}{'thresh':>8}{'flagged':>9}"
      f"{'prec':>8}{'recall':>8}{'FP':>7}")
for label, method, t in (
        ("A: 20-case/day review team", "capacity", t_cap),
        ("B: must catch 95% of fraud", "requirement*", t_rec),
        ("C: no cost data available", "maximise F1", best_t),
        ("D: FP costs 5, FN costs 500", "expected cost", t_cost)):
    r = metrics(ym, proba, t)
    pr = "nan" if math.isnan(r["prec"]) else f"{r['prec']:.4f}"
    print(f"  {label:<34}{method:<20}{t:>8.4f}{r['tp'] + r['fp']:>9}{pr:>8}"
          f"{r['rec']:>8.4f}{r['fp']:>7}")

r_b = metrics(ym, proba, t_rec)
if not t_rec_reachable:
    print(f"\n  Organisation B's 95% recall requirement is NOT ACHIEVABLE with this")
    print(f"  model at ANY threshold. Flagging {r_b['tp'] + r_b['fp']:,} of "
          f"{n:,} transactions -- "
          f"{(r_b['tp'] + r_b['fp']) / n:.0%} of all traffic -- still reaches only")
    print(f"  {r_b['rec']:.1%} recall, at {r_b['fp']:,} false alarms for "
          f"{r_b['tp']} real catches")
    print(f"  ({r_b['fp'] / max(r_b['tp'], 1):.0f} wasted investigations each). The "
          f"honest answer to this")
    print("  stakeholder is not a threshold -- it is 'this model cannot meet that")
    print("  requirement; here is what it CAN do, and here is what better data")
    print("  would cost'. Finding that out from a threshold sweep, before")
    print("  committing to the requirement, is the entire point of this exercise.")
elif r_b["tp"]:
    print(f"\n  Organisation B's 95% requirement costs {r_b['fp']} false alarms for")
    print(f"  {r_b['tp']} real catches -- {r_b['fp'] / r_b['tp']:.1f} wasted "
          f"investigations per catch.")
print("  Same trained model in all four rows. The threshold is a PRODUCT")
print("  decision, not a modelling one.")


# -------------------------------------------------- 3. ROC vs PR
rule("3. ROC-AUC vs PR-AUC ON IMBALANCED DATA")

print(f"  {'dataset':<24}{'base rate':>11}{'ROC-AUC':>10}{'PR-AUC':>9}"
      f"{'PR random baseline':>21}")
# The SAME underlying signal and the SAME model quality, at two base rates.
for label, target in (("balanced (50% pos)", 0.50), ("1% positive", BASE)):
    b_t = intercept_for(s_true, target)
    yb = (RNG.random(n) < sigmoid(s_true + b_t)).astype(int)
    pb = sigmoid(s_hat + intercept_for(s_hat, yb.mean()))
    print(f"  {label:<24}{yb.mean():>11.4f}{roc_auc(yb, pb):>10.4f}"
          f"{pr_auc(yb, pb):>9.4f}{yb.mean():>21.4f}")
print("\n  Same signal, same model, two base rates. ROC-AUC barely moves; PR-AUC")
print("  collapses. ROC-AUC does not tell you whether the model is USABLE.")

# Pick the threshold where the FALSE POSITIVE RATE is a reassuring 2%, then
# look at exactly the same errors through precision instead.
t_fpr = 0.5
for t in np.linspace(0.99, 0.0001, 4000):
    rr = metrics(ym, proba, t)
    if rr["fp"] / max(rr["fp"] + rr["tn"], 1) >= 0.02:
        t_fpr = float(t)
        break
r_at = metrics(ym, proba, t_fpr)
fpr = r_at["fp"] / (r_at["fp"] + r_at["tn"])
print(f"\n  On the 1% problem, at the threshold where FPR = 2% (t = {t_fpr:.4f}):")
print(f"    ROC-AUC   {roc_auc(ym, proba):.4f}   -- looks excellent")
print(f"    FPR       {fpr:.4f}   -- looks excellent: only {r_at['fp']} false "
      f"positives")
print(f"                          out of {r_at['tn'] + r_at['fp']:,} negatives")
print(f"    precision {r_at['prec']:.4f}   -- UNUSABLE: the SAME {r_at['fp']} false "
      f"positives,")
print(f"                          now measured against {r_at['tp'] + r_at['fp']} "
      f"total flags")
print(f"    -> {r_at['fp'] / max(r_at['tp'], 1):.1f} false alarms for every real "
      f"catch, at only {r_at['rec']:.0%} recall")
print("\n  Identical errors. FPR divides them by the huge negative count and they")
print("  vanish; precision divides them by the small flagged count and they")
print("  dominate. That is the whole reason to prefer PR-AUC when positives are")
print("  rare -- and why PR-AUC must be reported next to the base rate.")


# -------------------------------------------------- 4. AUC invariance
rule("4. AUC IS BLIND TO CALIBRATION  (monotonic transforms)")


def ece(y_true, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if mask.sum() == 0:
            continue
        total += mask.sum() / len(p) * abs(p[mask].mean() - y_true[mask].mean())
    return total


print(f"  {'transform':<28}{'ROC-AUC':>10}{'PR-AUC':>9}{'ECE':>9}"
      f"{'mean predicted':>17}{'actual rate':>14}")
for label, tp_fn in (("original", lambda q: q),
                     ("squared  (q^2)", lambda q: q**2),
                     ("cubed    (q^3)", lambda q: q**3),
                     ("sqrt     (q^0.5)", lambda q: np.sqrt(q)),
                     ("x0.5 then +0.25", lambda q: q * 0.5 + 0.25)):
    q = tp_fn(proba)
    print(f"  {label:<28}{roc_auc(ym, q):>10.6f}{pr_auc(ym, q):>9.6f}"
          f"{ece(ym, q):>9.4f}{q.mean():>17.4f}{ym.mean():>14.4f}")

print("\n  ROC-AUC and PR-AUC are IDENTICAL to six decimal places across all five")
print("  rows: every transform is monotonic, so the RANKING never changed. ECE")
print("  moves a lot. A model can rank perfectly and still tell you nothing")
print("  truthful about probability -- which matters the moment you make an")
print("  expected-cost decision or show a confidence number to a user.")


rule("5. RELIABILITY DIAGRAM  (10 bins, original model)")

edges = np.linspace(0, 1, 11)
print(f"  {'bin':<14}{'n':>7}{'mean predicted':>17}{'observed rate':>16}"
      f"{'gap':>9}")
for lo, hi in zip(edges[:-1], edges[1:]):
    mask = (proba >= lo) & (proba < hi if hi < 1 else proba <= hi)
    if mask.sum() == 0:
        print(f"  [{lo:.1f}, {hi:.1f})      {0:>7}{'--':>17}{'--':>16}{'--':>9}")
        continue
    mp, obs = proba[mask].mean(), ym[mask].mean()
    print(f"  [{lo:.1f}, {hi:.1f})      {int(mask.sum()):>7}{mp:>17.4f}"
          f"{obs:>16.4f}{obs - mp:>+9.4f}")
print(f"\n  ECE = {ece(ym, proba):.4f}   "
      f"(0 would be perfect; the diagonal is perfect calibration)")


# -------------------------------------------------- 6. macro vs micro
rule("6. MACRO vs MICRO AVERAGING  (5 classes, one dominant, one rare)")

counts = [8000, 1200, 500, 200, 100]
y_mc = np.concatenate([np.full(c, i) for i, c in enumerate(counts)])
pred_mc = y_mc.copy()
# The model handles class 0 almost perfectly and the rare classes badly.
acc_by_class = [0.99, 0.80, 0.45, 0.20, 0.05]
start = 0
for cls, (c, a) in enumerate(zip(counts, acc_by_class)):
    idx = np.arange(start, start + c)
    wrong = RNG.choice(idx, size=int(round((1 - a) * c)), replace=False)
    pred_mc[wrong] = 0 if cls != 0 else 1
    start += c

per_class = []
print(f"  {'class':<8}{'support':>9}{'precision':>11}{'recall':>9}{'F1':>9}")
for cls in range(5):
    tp = int(((pred_mc == cls) & (y_mc == cls)).sum())
    fp = int(((pred_mc == cls) & (y_mc != cls)).sum())
    fn = int(((pred_mc != cls) & (y_mc == cls)).sum())
    p_c = tp / (tp + fp) if tp + fp else 0.0
    r_c = tp / (tp + fn) if tp + fn else 0.0
    f_c = 2 * p_c * r_c / (p_c + r_c) if p_c + r_c else 0.0
    per_class.append((p_c, r_c, f_c, counts[cls]))
    print(f"  {cls:<8}{counts[cls]:>9}{p_c:>11.4f}{r_c:>9.4f}{f_c:>9.4f}")

micro = (pred_mc == y_mc).mean()          # micro-F1 == accuracy in single-label
macro_f1 = float(np.mean([f for _, _, f, _ in per_class]))
weighted_f1 = float(np.average([f for _, _, f, _ in per_class],
                               weights=[s for *_, s in per_class]))
print(f"\n  micro-F1 (= accuracy) : {micro:.4f}")
print(f"  weighted-F1           : {weighted_f1:.4f}")
print(f"  macro-F1              : {macro_f1:.4f}")
print(f"\n  micro - macro = {micro - macro_f1:.4f}. The dominant class (80% of the")
print("  data) carries micro and weighted; macro gives the rare classes equal")
print("  weight and exposes that class 4 is at F1 "
      f"{per_class[4][2]:.4f}. Report macro when")
print("  rare classes matter -- which includes every fairness question.")


# -------------------------------------------------- 7. regression metrics
rule("7. REGRESSION METRICS, WITH AND WITHOUT ONE OUTLIER")

yr = RNG.normal(50, 10, size=500)
pr_pred = yr + RNG.normal(0, 3, size=500)


def reg_metrics(y, p):
    err = y - p
    mae = float(np.abs(err).mean())
    mse = float((err**2).mean())
    rmse = math.sqrt(mse)
    r2 = 1 - mse / float(((y - y.mean()) ** 2).mean())
    mape = float((np.abs(err) / np.maximum(np.abs(y), 1e-9)).mean())
    return mae, rmse, r2, mape


print(f"  {'dataset':<34}{'MAE':>9}{'RMSE':>10}{'RMSE/MAE':>11}{'R2':>9}"
      f"{'MAPE':>9}")
mae, rmse, r2, mape = reg_metrics(yr, pr_pred)
print(f"  {'clean (500 rows)':<34}{mae:>9.4f}{rmse:>10.4f}{rmse / mae:>11.4f}"
      f"{r2:>9.4f}{mape:>9.4f}")

y_out, p_out = yr.copy(), pr_pred.copy()
y_out[0] = 500.0                                    # one outlier
mae, rmse, r2, mape = reg_metrics(y_out, p_out)
print(f"  {'+ one outlier (y=500)':<34}{mae:>9.4f}{rmse:>10.4f}"
      f"{rmse / mae:>11.4f}{r2:>9.4f}{mape:>9.4f}")

y_zero, p_zero = yr.copy(), pr_pred.copy()
y_zero[0] = 0.01                                    # a near-zero target
mae, rmse, r2, mape = reg_metrics(y_zero, p_zero)
print(f"  {'+ one near-zero target (y=0.01)':<34}{mae:>9.4f}{rmse:>10.4f}"
      f"{rmse / mae:>11.4f}{r2:>9.4f}{mape:>9.4f}")

print("\n  ONE row in 500 changes RMSE far more than MAE -- the RMSE/MAE ratio is")
print("  a direct read-out of how skewed your errors are. And MAPE explodes on a")
print("  near-zero target, because it divides by it. Choose the metric that")
print("  matches what the errors actually cost you.")

print("\nDone.")
