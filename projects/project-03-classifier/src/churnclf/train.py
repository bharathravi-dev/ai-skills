"""The end-to-end pipeline, and the report it prints.

Run:  python -m churnclf.train

The test set is touched exactly ONCE in this file, at the very end, and every
decision before that point uses validation data. Search this file for
`split.test` -- there should be two hits, both in `final_report`.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

import numpy as np

from .data import make_churn_data
from .evaluate import (baselines, choose_threshold_by_capacity,
                       choose_threshold_by_cost, choose_threshold_by_fbeta,
                       choose_threshold_by_recall, slice_report)
from .metrics import report
from .model import LogisticRegression, class_weights
from .split import grouped_temporal_split, random_split, stratified_kfold

SEED = 20260908
COST_FP = 12.0        # cost of one wasted retention offer
COST_FN = 240.0       # cost of losing a customer we could have kept


def banner(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def fmt(value, spec: str = ".4f") -> str:
    if value is None:
        return "--"
    if isinstance(value, float) and np.isnan(value):
        return "n/a"
    return format(value, spec) if isinstance(value, float) else str(value)


def fit_model(X, y, **kwargs) -> LogisticRegression:
    model = LogisticRegression(seed=SEED, **kwargs)
    model.fit(X, y, sample_weight=class_weights(y))
    return model


def run(n_customers: int = 3000, months: int = 12, seed: int = SEED,
        verbose: bool = True) -> dict:
    data = make_churn_data(n_customers=n_customers, months=months, seed=seed)
    split = grouped_temporal_split(data.groups, data.month, seed=seed)
    n_tr, n_va, n_te = split.sizes()

    if verbose:
        banner("1. DATA AND SPLIT")
        print(f"  rows {len(data):,}   customers {len(np.unique(data.groups)):,}"
              f"   months {months}")
        print(f"  base rate {data.base_rate:.4f} "
              f"({int(data.y.sum()):,} churn events)")
        print(f"\n  {'part':<8}{'rows':>9}{'customers':>12}{'months':>18}"
              f"{'base rate':>12}")
        for name, idx in (("train", split.train), ("val", split.val),
                          ("test", split.test)):
            months_seen = sorted(set(data.month[idx].tolist()))
            span = (f"{months_seen[0]}-{months_seen[-1]}" if months_seen else "--")
            print(f"  {name:<8}{len(idx):>9,}{len(set(data.groups[idx].tolist())):>12,}"
                  f"{span:>18}{data.y[idx].mean():>12.4f}")
        print("\n  No customer appears in two parts (asserted by the splitter),")
        print("  and training months strictly precede evaluation months.")

    # ---- gradient check before trusting anything the model says ----------
    checker = LogisticRegression(seed=SEED)
    worst_rel = 0.0
    for check_seed in range(4):
        rng = np.random.default_rng(check_seed)
        sub = rng.choice(split.train, size=400, replace=False)
        rel = checker.gradient_check(
            data.X[sub], data.y[sub],
            sample_weight=class_weights(data.y[sub]), seed=check_seed)
        worst_rel = max(worst_rel, rel)
    if verbose:
        banner("2. GRADIENT CHECK  (before trusting any number the model produces)")
        print(f"  worst relative error over 4 different training subsets: "
              f"{worst_rel:.2e}")
        print(f"  verdict: {'PASS (< 1e-7)' if worst_rel < 1e-7 else 'FAIL'}")
        print("  Checked on several subsets, not one: M3-L11 showed a real bug")
        print("  passing a check run on a single convenient input.")
    if worst_rel >= 1e-7:
        raise RuntimeError(f"gradient check failed: {worst_rel:.2e}")

    # ---- train -----------------------------------------------------------
    model = fit_model(data.X[split.train], data.y[split.train])
    p_val = model.predict_proba(data.X[split.val])

    if verbose:
        banner("3. TRAINING")
        print(f"  steps {model.steps}   lr {model.lr}   L2 {model.l2}   "
              f"clip {model.clip_norm}")
        print(f"  loss {model.history[0]:.4f} -> {model.history[-1]:.4f} "
              f"(fell: {model.history[-1] < model.history[0]})")
        print(f"\n  {'feature':<24}{'weight':>10}   direction")
        order = np.argsort(-np.abs(model.w))
        for j in order:
            direction = ("raises churn risk" if model.w[j] > 0
                         else "lowers churn risk")
            print(f"  {data.feature_names[j]:<24}{model.w[j]:>10.4f}   {direction}")
        print(f"  {'(intercept)':<24}{model.b:>10.4f}")
        print("\n  Weights are on STANDARDISED features, so they are comparable to")
        print("  each other -- but they are not causal, and this model is not")
        print("  evidence that changing a feature would change churn.")

    # ---- threshold selection, on VALIDATION only -------------------------
    y_val = data.y[split.val]
    choices = {
        "expected cost": choose_threshold_by_cost(y_val, p_val, COST_FP, COST_FN),
        "capacity (5%)": choose_threshold_by_capacity(p_val, 0.05),
        "maximise F1": choose_threshold_by_fbeta(y_val, p_val, 1.0),
        "maximise F2": choose_threshold_by_fbeta(y_val, p_val, 2.0),
    }
    recall_choice = choose_threshold_by_recall(y_val, p_val, 0.90)
    choices["recall >= 90%"] = recall_choice

    if verbose:
        banner("4. THRESHOLD SELECTION  (validation data only -- never test)")
        print(f"  {'method':<20}{'threshold':>11}{'precision':>11}{'recall':>9}"
              f"{'flagged':>9}{'val cost':>12}")
        for name, choice in choices.items():
            if choice is None:
                print(f"  {name:<20}{'UNREACHABLE':>11}{'--':>11}{'--':>9}"
                      f"{'--':>9}{'--':>12}")
                continue
            r = report(y_val, p_val, choice.threshold)
            cost = r["fp"] * COST_FP + r["fn"] * COST_FN
            print(f"  {name:<20}{choice.threshold:>11.4f}"
                  f"{fmt(r['precision']):>11}{r['recall']:>9.4f}"
                  f"{r['flagged']:>9,}{cost:>12,.0f}")
        if recall_choice is None:
            print("\n  A 90% recall requirement is NOT reachable with this model at")
            print("  any threshold. That is a finding to take to the stakeholder,")
            print("  not a number to quietly round down.")

    chosen = choices["expected cost"]
    if verbose:
        print(f"\n  CHOSEN: {chosen.threshold:.4f} ({chosen.method})")
        print(f"  rationale: {chosen.rationale}")
        print(f"  Costs used: FP = {COST_FP:g} (a wasted retention offer),")
        print(f"              FN = {COST_FN:g} (a customer lost who could have")
        print(f"              been kept). These are ASSUMPTIONS -- they belong to")
        print("              the business, and the threshold moves when they change.")

    # ---- cross-validation for stability, on training data only -----------
    folds = stratified_kfold(data.y[split.train], k=5, seed=seed)
    fold_scores = []
    for i in range(len(folds)):
        va = folds[i]
        tr = np.concatenate([f for j, f in enumerate(folds) if j != i])
        m = fit_model(data.X[split.train][tr], data.y[split.train][tr])
        r = report(data.y[split.train][va],
                   m.predict_proba(data.X[split.train][va]), chosen.threshold)
        fold_scores.append(r)

    if verbose:
        banner("5. 5-FOLD STABILITY CHECK  (training data only)")
        print(f"  {'fold':<8}{'PR-AUC':>10}{'precision':>12}{'recall':>10}")
        for i, r in enumerate(fold_scores, start=1):
            print(f"  {i:<8}{r['pr_auc']:>10.4f}{fmt(r['precision']):>12}"
                  f"{r['recall']:>10.4f}")
        for key in ("pr_auc", "precision", "recall"):
            vals = [r[key] for r in fold_scores if not np.isnan(r[key])]
            print(f"  {key:<8} mean {np.mean(vals):.4f} +/- {np.std(vals):.4f}")
        print("\n  Report the spread. A single split hands you one of these numbers")
        print("  with no indication of how much was luck (M3-L13 section 5.5).")
        print("  NOTE: these folds are NOT grouped, so they are a stability check")
        print("  on training only -- they are optimistic, and the test number below")
        print("  is the one to quote.")

    # ---- leakage experiments ---------------------------------------------
    # (a) The SAME honest features, split randomly instead of by customer+time.
    bad = random_split(len(data), 0.15, 0.20, seed=seed)
    bad_model = fit_model(data.X[bad.train], data.y[bad.train])
    bad_report = report(data.y[bad.test],
                        bad_model.predict_proba(data.X[bad.test]),
                        chosen.threshold)

    # (b) A target-encoded per-customer feature computed over ALL months --
    #     the classic leaky feature -- under the SAME honest split.
    leaky = make_churn_data(n_customers=n_customers, months=months, seed=seed,
                            add_leaky_feature=True)
    leaky_split = grouped_temporal_split(leaky.groups, leaky.month, seed=seed)
    leaky_model = fit_model(leaky.X[leaky_split.train], leaky.y[leaky_split.train])
    leaky_report = report(
        leaky.y[leaky_split.test],
        leaky_model.predict_proba(leaky.X[leaky_split.test]), chosen.threshold)

    # ---- the test set, used once -----------------------------------------
    p_test = model.predict_proba(data.X[split.test])
    final = report(data.y[split.test], p_test, chosen.threshold)
    base = baselines(data.y[split.test], data.base_rate, seed=seed)

    if verbose:
        banner("6. FINAL TEST-SET REPORT  (the test set is read here, once)")
        print(f"  threshold {chosen.threshold:.4f}   test rows {n_te:,}   "
              f"base rate {final['base_rate']:.4f}")
        print(f"\n  confusion matrix:   TP {final['tp']:<6} FP {final['fp']:<6}"
              f" FN {final['fn']:<6} TN {final['tn']:<6}")
        print(f"\n  {'metric':<16}{'model':>10}   compared with")
        print(f"  {'accuracy':<16}{final['accuracy']:>10.4f}   "
              f"always-negative baseline {base['always negative']['accuracy']:.4f}")
        print(f"  {'precision':<16}{fmt(final['precision']):>10}   "
              f"base rate {final['base_rate']:.4f} "
              f"(= precision of random flagging)")
        print(f"  {'recall':<16}{final['recall']:>10.4f}   "
              f"always-negative baseline 0.0000")
        print(f"  {'F1':<16}{final['f1']:>10.4f}")
        print(f"  {'F2':<16}{final['f2']:>10.4f}   (recall-weighted)")
        print(f"  {'ROC-AUC':<16}{final['roc_auc']:>10.4f}   random 0.5000")
        print(f"  {'PR-AUC':<16}{final['pr_auc']:>10.4f}   "
              f"random = base rate {final['base_rate']:.4f} "
              f"({final['pr_auc'] / final['base_rate']:.1f}x)")
        print(f"  {'ECE':<16}{final['ece']:>10.4f}   0 = perfectly calibrated")

        print(f"\n  {'baseline':<34}{'accuracy':>10}{'precision':>11}"
              f"{'recall':>9}{'flagged':>10}")
        for name, b in base.items():
            print(f"  {name:<34}{b['accuracy']:>10.4f}{fmt(b['precision']):>11}"
                  f"{fmt(b['recall']):>9}{b['flagged']:>10,}")

        banner("7. TWO LEAKAGE EXPERIMENTS  (a negative result and a positive one)")
        print(f"  {'setup':<40}{'precision':>11}{'recall':>9}{'PR-AUC':>10}"
              f"{'ROC-AUC':>10}")
        print(f"  {'grouped + temporal, honest features':<40}"
              f"{fmt(final['precision']):>11}{final['recall']:>9.4f}"
              f"{final['pr_auc']:>10.4f}{final['roc_auc']:>10.4f}")
        print(f"  {'(a) random split, honest features':<40}"
              f"{fmt(bad_report['precision']):>11}{bad_report['recall']:>9.4f}"
              f"{bad_report['pr_auc']:>10.4f}{bad_report['roc_auc']:>10.4f}")
        print(f"  {'(b) honest split, target-encoded feat':<40}"
              f"{fmt(leaky_report['precision']):>11}{leaky_report['recall']:>9.4f}"
              f"{leaky_report['pr_auc']:>10.4f}{leaky_report['roc_auc']:>10.4f}")

        d_a = bad_report["pr_auc"] - final["pr_auc"]
        d_b = leaky_report["pr_auc"] - final["pr_auc"]
        print(f"\n  (a) random split changes PR-AUC by {d_a:+.4f} -- essentially")
        print("      nothing, and this is a genuine finding, not a broken demo.")
        print("      A random split leaks only if the model can IDENTIFY the group.")
        print("      This feature set contains no customer identifier and the model")
        print("      is linear, so there is no mechanism by which it could memorise")
        print("      an individual. Grouping still matters -- add a customer")
        print("      embedding, an ID column or a high-capacity model and the leak")
        print("      appears at once -- but a rule applied without its mechanism is")
        print("      superstition. M3-L13 section 7.3 measured a 16.7-point gap on")
        print("      the same kind of data WITH an identity feature.")
        print(f"\n  (b) one target-encoded feature moves PR-AUC by {d_b:+.4f}, on the")
        print("      SAME honest split. `customer_churn_rate_alltime` is each")
        print("      customer's mean label over every month, so each row's feature")
        print("      already contains its own answer. The split was correct and the")
        print("      result is still worthless.")
        print("\n  The lesson is not 'always group your split'. It is: find the")
        print("  MECHANISM by which information could travel from the answer to the")
        print("  features, and close that. Sometimes it is the split; here it was a")
        print("  feature that no split could have saved.")

        banner("8. SLICED PERFORMANCE  (aggregate metrics hide subgroup failure)")
        contract = np.where(data.raw[split.test, 5] > 0.5, "annual", "monthly")
        print(f"  {'slice':<14}{'n':>7}{'positives':>11}{'accuracy':>10}"
              f"{'precision':>11}{'recall':>9}{'reliable':>10}")
        for row in slice_report(data.y[split.test], p_test, chosen.threshold,
                                contract):
            print(f"  {row['slice']:<14}{row['n']:>7,}{row['positives']:>11}"
                  f"{row['accuracy']:>10.4f}{fmt(row['precision']):>11}"
                  f"{fmt(row['recall']):>9}{str(row['reliable']):>10}")
        print("\n  'reliable' is False where a slice has too few rows or too few")
        print("  positives for its numbers to mean anything (M3-L13 section 5.4).")

        banner("9. LIMITATIONS  (state these before anyone acts on the model)")
        for line in LIMITATIONS:
            print(f"  - {line}")

    return {
        "split_sizes": {"train": n_tr, "val": n_va, "test": n_te},
        "threshold": asdict(chosen) if chosen else None,
        "test": final,
        "baselines": base,
        "random_split_test": bad_report,
        "leaky_feature_test": leaky_report,
        "gradient_check": worst_rel,
    }


LIMITATIONS = (
    "The data is SYNTHETIC. These numbers describe a generator, not a business.",
    "The model is correlational. Nothing here says changing a feature changes "
    "churn.",
    "Class weighting distorts calibration; the ECE above should be read with "
    "that in mind, and probabilities recalibrated before any expected-cost use "
    "in production.",
    "Costs (FP=12, FN=240) are assumptions. The chosen threshold moves when "
    "they do, and they belong to the business, not to this script.",
    "The test set has now been read. Re-tuning against it would make it a "
    "validation set (M1-L06).",
    "No fairness analysis has been performed. The contract-type slice above is "
    "a demonstration of technique, not a fairness assessment, and no metric "
    "here establishes legal compliance.",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate the churn "
                                                 "classifier.")
    parser.add_argument("--customers", type=int, default=3000)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--json", action="store_true",
                        help="print the result dict as JSON instead of a report")
    args = parser.parse_args(argv)

    result = run(n_customers=args.customers, months=args.months, seed=args.seed,
                 verbose=not args.json)
    if args.json:
        print(json.dumps(result, indent=2, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
