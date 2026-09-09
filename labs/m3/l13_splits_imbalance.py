"""M3-L13 lab -- splits, stratification, grouping and class imbalance.

Measures how much a test score varies with the split, compares random and
stratified splits, shows a grouped split changing the answer, reproduces the
resample-before-split leak, compares four imbalance tools, and runs
stratified k-fold.

All data is synthetic. Run:  python labs/m3/l13_splits_imbalance.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(0)


def rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


# ------------------------------------------------------------ split helpers
def random_split(n, test_frac, rng):
    idx = rng.permutation(n)
    k = int(round(test_frac * n))
    return idx[k:], idx[:k]


def stratified_split(y, test_frac, rng):
    train, test = [], []
    for cls in np.unique(y):
        cls_idx = rng.permutation(np.where(y == cls)[0])
        k = int(round(test_frac * len(cls_idx)))
        test.extend(cls_idx[:k])
        train.extend(cls_idx[k:])
    return np.array(train), np.array(test)


def grouped_split(groups, test_frac, rng):
    uniq = rng.permutation(np.unique(groups))
    k = int(round(test_frac * len(uniq)))
    test_groups = set(uniq[:k].tolist())
    mask = np.array([g in test_groups for g in groups])
    return np.where(~mask)[0], np.where(mask)[0]


def fit_logistic(X, y, weights=None, steps=600, lr=0.5):
    """Plain gradient descent logistic regression (M3-L09)."""
    w = np.zeros(X.shape[1])
    b = 0.0
    sw = np.ones(len(y)) if weights is None else weights
    sw = sw / sw.mean()
    for _ in range(steps):
        p = sigmoid(X @ w + b)
        err = (p - y) * sw / len(y)
        w -= lr * (X.T @ err)
        b -= lr * err.sum()
    return w, b


def scores(y_true, proba, threshold=0.5):
    pred = (proba >= threshold).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    acc = (tp + tn) / len(y_true)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    return acc, prec, rec, (tp, fp, fn, tn)


# ------------------------------------------------- 1. test set variability
rule("1. HOW MUCH DOES A TEST SCORE DEPEND ON THE SPLIT?  (200 re-splits each)")

Xv = RNG.normal(0, 1, size=(20000, 5))
wv = np.array([1.2, -0.8, 0.5, 0.0, 0.3])
yv = (RNG.random(20000) < sigmoid(Xv @ wv)).astype(int)

# One model, trained once, scored on many different test sets of each size.
w_fixed, b_fixed = fit_logistic(Xv[:10000], yv[:10000])
pool_X, pool_y = Xv[10000:], yv[10000:]
pool_p = sigmoid(pool_X @ w_fixed + b_fixed)

print(f"  {'test size':>11}{'mean acc':>11}{'sd':>9}{'min':>9}{'max':>9}"
      f"{'predicted SE':>15}{'range':>9}")
for n_test in (50, 100, 250, 1000, 5000, 10000):
    accs = []
    for _ in range(200):
        idx = RNG.choice(len(pool_y), size=n_test, replace=False)
        accs.append((( pool_p[idx] >= 0.5).astype(int) == pool_y[idx]).mean())
    accs = np.array(accs)
    p_hat = accs.mean()
    se = math.sqrt(p_hat * (1 - p_hat) / n_test)
    print(f"  {n_test:>11}{p_hat:>11.4f}{accs.std():>9.4f}{accs.min():>9.4f}"
          f"{accs.max():>9.4f}{se:>15.4f}{accs.max() - accs.min():>9.4f}")

print("\n  (n=10000 shows sd exactly 0 because the pool IS 10000 rows: sampling all")
print("   of them without replacement gives the same test set every time. With no")
print("   sampling there is no sampling variability -- the formula's SE is the")
print("   uncertainty about the wider population, which does not vanish.)")
print("\n  The 'sd' column tracks the predicted SE closely -- the formula works.")
print("  At n=50 the SAME model scores anywhere in a range of ~0.2 accuracy")
print("  depending only on which rows you happened to test it on.")

# smallest test size at which a 2-point difference is distinguishable
for n_test in (50, 100, 250, 500, 1000, 2000, 5000, 10000):
    se = math.sqrt(0.75 * 0.25 / n_test)
    if 2 * se * math.sqrt(2) < 0.02:
        print(f"\n  A 2-point accuracy gap needs about n >= {n_test:,} test rows")
        print(f"  to be distinguishable (2 * SE * sqrt(2) = {2 * se * math.sqrt(2):.4f} < 0.02).")
        break


# ------------------------------------------------- 2. stratified vs random
rule("2. RANDOM vs STRATIFIED  (2% positive class, 200-row test set)")

n_imb = 10000
y_imb = np.zeros(n_imb, dtype=int)
y_imb[RNG.choice(n_imb, size=200, replace=False)] = 1     # exactly 2%

print(f"  {'method':<14}{'mean % pos':>13}{'sd':>9}{'min':>7}{'max':>7}"
      f"{'runs with 0 pos':>18}")
for name, fn in (("random", None), ("stratified", stratified_split)):
    rates, zeros = [], 0
    for _ in range(500):
        if fn is None:
            _, te = random_split(n_imb, 0.02, RNG)
        else:
            _, te = fn(y_imb, 0.02, RNG)
        k = int(y_imb[te].sum())
        rates.append(k)
        zeros += (k == 0)
    r = np.array(rates)
    print(f"  {name:<14}{r.mean():>13.2f}{r.std():>9.2f}{r.min():>7}{r.max():>7}"
          f"{zeros:>18}")

print("\n  Counts are positives in a 200-row test set; 2% means 4 are expected.")
print("  Random splitting sometimes yields ZERO positives -- recall is then")
print("  undefined and the run is wasted. Stratifying gives exactly 4, always.")


# ------------------------------------------------- 3. grouped split
rule("3. GROUPED SPLIT  (300 customers, 8 transactions each, customer-id feature)")

# A realistic set-up: the model gets a customer-identity feature (a one-hot, or
# in practice an embedding / target-encoded column). Each customer has a latent
# risk level that is NOT otherwise observable. On customers it has seen, the
# model can memorise that risk. On new customers it cannot.
n_cust, per_cust = 300, 8
groups = np.repeat(np.arange(n_cust), per_cust)
n_rows = n_cust * per_cust
cust_risk = RNG.normal(0, 2.5, size=n_cust)          # latent, not a feature
Xg_obs = RNG.normal(0, 1, size=(n_rows, 3))          # genuinely observable
onehot = np.zeros((n_rows, n_cust))
onehot[np.arange(n_rows), groups] = 1.0              # the customer-id feature
Xg = np.column_stack([Xg_obs, onehot])
yg = (RNG.random(n_rows)
      < sigmoid(0.5 * Xg_obs[:, 0] + cust_risk[groups])).astype(int)

print(f"  {'split':<26}{'test acc':>10}{'customers in both':>20}"
      f"{'test rows from seen custs':>28}")
gap = {}
for name, (tr, te) in (
        ("random (WRONG here)", random_split(n_rows, 0.25, RNG)),
        ("grouped by customer", grouped_split(groups, 0.25, RNG))):
    w, b = fit_logistic(Xg[tr], yg[tr], steps=800)
    acc = ((sigmoid(Xg[te] @ w + b) >= 0.5).astype(int) == yg[te]).mean()
    seen = set(groups[tr].tolist())
    overlap = len(seen & set(groups[te].tolist()))
    from_seen = int(np.isin(groups[te], list(seen)).sum())
    gap[name] = acc
    print(f"  {name:<26}{acc:>10.4f}{overlap:>20}"
          f"{f'{from_seen} / {len(te)}':>28}")

diff = gap["random (WRONG here)"] - gap["grouped by customer"]
print(f"\n  The random split overstates accuracy by {diff:.4f} "
      f"({diff * 100:.1f} percentage points).")
print("  Both numbers are computed on held-out ROWS, so both look legitimate.")
print("  But in the random split every test customer was also a TRAINING customer,")
print("  so the model had already learned their individual risk. The grouped")
print("  number is what you will actually see on customers you have never")
print("  observed -- which is the deployment case for fraud detection.")


# ------------------------------------------------- 4. the resampling leak
rule("4. THE RESAMPLE-BEFORE-SPLIT LEAK  (1% positive)")

n_f = 6000
Xf = RNG.normal(0, 1, size=(n_f, 4))
wf = np.array([1.0, -1.2, 0.7, 0.4])
score_f = Xf @ wf
thresh = np.quantile(score_f, 0.99)
yf = (score_f >= thresh).astype(int)          # exactly 1% positive
print(f"  dataset: {n_f} rows, {int(yf.sum())} positive ({yf.mean():.1%})")

# --- WRONG: oversample the whole dataset, then split
pos = np.where(yf == 1)[0]
reps = int(round((yf == 0).sum() / max(len(pos), 1)))
over_idx = np.concatenate([np.arange(n_f), np.repeat(pos, reps - 1)])
Xo, yo = Xf[over_idx], yf[over_idx]
tr_o, te_o = random_split(len(yo), 0.25, RNG)
w, b = fit_logistic(Xo[tr_o], yo[tr_o])
acc_leak, prec_leak, rec_leak, _ = scores(yo[te_o], sigmoid(Xo[te_o] @ w + b))

# how many test rows have an identical twin in train?
train_rows = {Xo[i].tobytes() for i in tr_o}
dupes = sum(1 for i in te_o if Xo[i].tobytes() in train_rows)

# --- RIGHT: split first, oversample the training side only
tr_r, te_r = stratified_split(yf, 0.25, RNG)
pos_tr = tr_r[yf[tr_r] == 1]
reps_tr = int(round((yf[tr_r] == 0).sum() / max(len(pos_tr), 1)))
tr_bal = np.concatenate([tr_r, np.repeat(pos_tr, reps_tr - 1)])
w2, b2 = fit_logistic(Xf[tr_bal], yf[tr_bal])
acc_ok, prec_ok, rec_ok, _ = scores(yf[te_r], sigmoid(Xf[te_r] @ w2 + b2))

print(f"\n  {'procedure':<34}{'test acc':>10}{'precision':>11}{'recall':>9}"
      f"{'test rows seen in train':>26}")
print(f"  {'oversample THEN split (WRONG)':<34}{acc_leak:>10.4f}{prec_leak:>11.4f}"
      f"{rec_leak:>9.4f}{f'{dupes} / {len(te_o)}  ({dupes / len(te_o):.0%})':>26}")
print(f"  {'split THEN oversample (right)':<34}{acc_ok:>10.4f}{prec_ok:>11.4f}"
      f"{rec_ok:>9.4f}{'0 / ' + str(len(te_r)) + '  (0%)':>26}")
print("\n  The wrong procedure reports a better-looking model. It is not a better")
print("  model; it is the same model scored on rows it was trained on.")


# ------------------------------------------------- 5. imbalance tools
rule("5. FOUR IMBALANCE TOOLS ON THE SAME DATA  (1% positive, honest split)")

tr, te = stratified_split(yf, 0.25, RNG)
Xtr, ytr, Xte, yte = Xf[tr], yf[tr], Xf[te], yf[te]
print(f"  train {len(ytr)} rows ({ytr.sum()} pos)   test {len(yte)} rows "
      f"({yte.sum()} pos)\n")

print(f"  {'approach':<30}{'acc':>8}{'precision':>11}{'recall':>9}"
      f"{'TP':>5}{'FP':>5}{'FN':>5}")

maj_acc, *_ , cm = scores(yte, np.zeros(len(yte)))
print(f"  {'majority baseline (all neg)':<30}{maj_acc:>8.4f}{'nan':>11}"
      f"{0.0:>9.4f}{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

w, b = fit_logistic(Xtr, ytr)
p_plain = sigmoid(Xte @ w + b)
a, pr, rc, cm = scores(yte, p_plain)
print(f"  {'no handling':<30}{a:>8.4f}{pr:>11.4f}{rc:>9.4f}"
      f"{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

cw = np.where(ytr == 1, len(ytr) / (2 * ytr.sum()),
              len(ytr) / (2 * (len(ytr) - ytr.sum())))
w, b = fit_logistic(Xtr, ytr, weights=cw)
a, pr, rc, cm = scores(yte, sigmoid(Xte @ w + b))
print(f"  {'class weights':<30}{a:>8.4f}{pr:>11.4f}{rc:>9.4f}"
      f"{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

pos_tr = np.where(ytr == 1)[0]
r = int(round((ytr == 0).sum() / len(pos_tr)))
bal = np.concatenate([np.arange(len(ytr)), np.repeat(pos_tr, r - 1)])
w, b = fit_logistic(Xtr[bal], ytr[bal])
a, pr, rc, cm = scores(yte, sigmoid(Xte @ w + b))
print(f"  {'oversample train only':<30}{a:>8.4f}{pr:>11.4f}{rc:>9.4f}"
      f"{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

neg_tr = RNG.choice(np.where(ytr == 0)[0], size=len(pos_tr), replace=False)
under = np.concatenate([pos_tr, neg_tr])
w, b = fit_logistic(Xtr[under], ytr[under])
a, pr, rc, cm = scores(yte, sigmoid(Xte @ w + b))
print(f"  {'undersample majority':<30}{a:>8.4f}{pr:>11.4f}{rc:>9.4f}"
      f"{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

# threshold tuning: choose on a validation slice carved from TRAIN, not test
tr2, val = stratified_split(ytr, 0.25, RNG)
wv2, bv2 = fit_logistic(Xtr[tr2], ytr[tr2])
p_val = sigmoid(Xtr[val] @ wv2 + bv2)
best_t, best_f1 = 0.5, -1.0
for t in np.linspace(0.01, 0.99, 99):
    _, pr_v, rc_v, _ = scores(ytr[val], p_val, t)
    if not (math.isnan(pr_v) or math.isnan(rc_v)) and pr_v + rc_v > 0:
        f1 = 2 * pr_v * rc_v / (pr_v + rc_v)
        if f1 > best_f1:
            best_f1, best_t = f1, t
a, pr, rc, cm = scores(yte, p_plain, best_t)
print(f"  {f'threshold tuned ({best_t:.2f})':<30}{a:>8.4f}{pr:>11.4f}{rc:>9.4f}"
      f"{cm[0]:>5}{cm[1]:>5}{cm[2]:>5}")

print("\n  The majority baseline scores {:.4f} accuracy while catching ZERO".format(maj_acc))
print("  positives. Every approach that actually finds positives has LOWER")
print("  accuracy. Reporting accuracy alone would rank the useless model first.")
print(f"  Threshold tuning used the SAME trained model as 'no handling' -- no")
print(f"  retraining, just a different cut point chosen on validation data.")


# ------------------------------------------------- 6. stratified k-fold
rule("6. STRATIFIED 5-FOLD CROSS-VALIDATION")


def stratified_kfold(y, k, rng):
    folds = [[] for _ in range(k)]
    for cls in np.unique(y):
        cls_idx = rng.permutation(np.where(y == cls)[0])
        for i, row in enumerate(cls_idx):
            folds[i % k].append(row)
    return [np.array(sorted(f)) for f in folds]


folds = stratified_kfold(yf, 5, RNG)
all_rows = np.concatenate(folds)
print(f"  every row validated exactly once: "
      f"{len(all_rows) == n_f and len(set(all_rows.tolist())) == n_f}")
print(f"  fold sizes: {[len(f) for f in folds]}")
print(f"  positives per fold: {[int(yf[f].sum()) for f in folds]}  "
      f"(whole dataset: {int(yf.sum())})\n")

print(f"  {'fold':<8}{'val n':>8}{'accuracy':>11}{'precision':>12}{'recall':>10}")
accs, precs, recs = [], [], []
for i, fold in enumerate(folds, start=1):
    tr_idx = np.concatenate([f for j, f in enumerate(folds) if j != i - 1])
    cwk = np.where(yf[tr_idx] == 1,
                   len(tr_idx) / (2 * yf[tr_idx].sum()),
                   len(tr_idx) / (2 * (len(tr_idx) - yf[tr_idx].sum())))
    w, b = fit_logistic(Xf[tr_idx], yf[tr_idx], weights=cwk)
    a, pr, rc, _ = scores(yf[fold], sigmoid(Xf[fold] @ w + b))
    accs.append(a)
    precs.append(0.0 if math.isnan(pr) else pr)
    recs.append(0.0 if math.isnan(rc) else rc)
    print(f"  {i:<8}{len(fold):>8}{a:>11.4f}{precs[-1]:>12.4f}{recs[-1]:>10.4f}")

print(f"\n  accuracy : {np.mean(accs):.4f} +/- {np.std(accs):.4f}")
print(f"  precision: {np.mean(precs):.4f} +/- {np.std(precs):.4f}")
print(f"  recall   : {np.mean(recs):.4f} +/- {np.std(recs):.4f}")
print("\n  Report the spread, not just the mean. A single split would have handed")
print(f"  you ONE of these folds -- precision anywhere from {min(precs):.4f} to "
      f"{max(precs):.4f},")
print(f"  a {max(precs) - min(precs):.4f} range -- with nothing to tell you how much of it was luck.")
print("  Recall is 1.0000 in every fold: class weighting has pushed the threshold")
print("  low enough to catch everything, at a precision cost. That is a choice,")
print("  not a result -- M3-L14 covers how to make it deliberately.")

print("\nDone.")
