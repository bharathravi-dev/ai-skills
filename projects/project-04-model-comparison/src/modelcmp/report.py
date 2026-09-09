"""Comparison tables that state their own uncertainty.

Every rate is reported with its standard error, and the harness refuses to
call a difference significant when the samples cannot support it (M3-L14
section 5.4). A comparison harness that reports differences it cannot defend
is worse than no harness at all.
"""

from __future__ import annotations

from .metrics import distinguishable, proportion_stderr, token_cost
from .runner import GridResult

# ILLUSTRATIVE prices, dated 2026-09-09. Not quotes. Replace before budgeting.
IN_PRICE_PER_M = 0.50
OUT_PRICE_PER_M = 1.50


def config_table(result: GridResult) -> str:
    """One row per configuration, aggregated across prompts."""
    lines = [
        f"  {'config':<16}{'temp':>6}{'top_p':>7}{'determinism':>13}"
        f"{'distinct':>10}{'trunc':>8}{'out tok':>9}{'$/1k req':>10}",
        "  " + "-" * 79,
    ]
    for label, cells in result.by_config().items():
        n = sum(c.metrics.n_samples for c in cells)
        det = sum(c.metrics.determinism * c.metrics.n_samples
                  for c in cells) / n
        dis = sum(c.metrics.distinct_ratio * c.metrics.n_samples
                  for c in cells) / n
        tru = sum(c.metrics.truncation_rate * c.metrics.n_samples
                  for c in cells) / n
        out_t = sum(c.metrics.mean_output_tokens * c.metrics.n_samples
                    for c in cells) / n
        in_t = sum(c.metrics.mean_input_tokens * c.metrics.n_samples
                   for c in cells) / n
        cost = token_cost(in_t, out_t, IN_PRICE_PER_M, OUT_PRICE_PER_M) * 1000
        cfg = cells[0].config
        tp = "-" if cfg.top_p is None else f"{cfg.top_p:.2f}"
        se = proportion_stderr(det, n)
        lines.append(
            f"  {label:<16}{cfg.temperature:>6.1f}{tp:>7}"
            f"{det:>9.2f}+-{se:.2f}{dis:>10.2f}{tru:>8.2f}{out_t:>9.1f}"
            f"{cost:>10.3f}")
    return "\n".join(lines)


def determinism_claim(result: GridResult, label_a: str, label_b: str) -> str:
    """Compare two configs' determinism, refusing to overclaim."""
    by = result.by_config()
    for lbl in (label_a, label_b):
        if lbl not in by:
            raise KeyError(f"no config labelled {lbl!r} in this run")

    def agg(cells):
        n = sum(c.metrics.n_samples for c in cells)
        det = sum(c.metrics.determinism * c.metrics.n_samples
                  for c in cells) / n
        return det, n

    a, na = agg(by[label_a])
    b, nb = agg(by[label_b])
    diff = a - b
    if distinguishable(a, b, na, nb):
        verdict = f"DISTINGUISHABLE ({label_a} higher)" if diff > 0 else \
                  f"DISTINGUISHABLE ({label_b} higher)"
    else:
        verdict = "NOT distinguishable at this sample size"
    return (f"  {label_a}: {a:.3f} +- {proportion_stderr(a, na):.3f} (n={na})\n"
            f"  {label_b}: {b:.3f} +- {proportion_stderr(b, nb):.3f} (n={nb})\n"
            f"  difference {diff:+.3f}  ->  {verdict}")


def truncation_warnings(result: GridResult) -> list[str]:
    """Every cell where output was truncated. Never silently ignored."""
    warnings = []
    for cell in result.cells:
        rate = cell.metrics.truncation_rate
        if rate > 0:
            warnings.append(
                f"  {cell.prompt_id} / {cell.config.label}: "
                f"{rate:.0%} of samples TRUNCATED "
                f"(max_tokens={cell.config.max_tokens}) -- do not parse these")
    return warnings
