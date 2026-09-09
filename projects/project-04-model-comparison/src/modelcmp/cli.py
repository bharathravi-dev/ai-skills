"""The harness's entry point: run a grid and print the comparison.

Run:  python -m modelcmp.cli
"""

from __future__ import annotations

import argparse
import sys

from .config import PRESETS, DecodeConfig
from .metrics import token_cost
from .provider import MockProvider
from .report import (IN_PRICE_PER_M, OUT_PRICE_PER_M, config_table,
                     determinism_claim, truncation_warnings)
from .runner import BudgetExceeded, estimate_tokens, run_grid

PROMPTS = {
    "extract": "Extract the refund status as JSON.",
    "explain": "Explain the refund status to the customer.",
    "steps": "List the steps to reset a password.",
}


def banner(t: str) -> None:
    print(f"\n{'=' * 76}\n{t}\n{'=' * 76}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Compare model behaviour across decoding configurations.")
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--budget", type=int, default=200_000,
                    help="token ceiling, enforced BEFORE the run")
    ap.add_argument("--save", type=str, default=None)
    args = ap.parse_args(argv)

    configs = [PRESETS[k] for k in
               ("extraction", "factual", "conversation", "creative",
                "reckless", "tight-budget")]
    provider = MockProvider()

    banner("1. WHAT THIS RUN WILL COST, BEFORE IT RUNS")
    est = estimate_tokens(PROMPTS, configs, args.samples)
    print(f"  prompts {len(PROMPTS)} x configs {len(configs)} x samples "
          f"{args.samples} = {len(PROMPTS) * len(configs) * args.samples} requests")
    print(f"  estimated tokens : {est:,}")
    print(f"  token budget     : {args.budget:,}")
    print(f"  ILLUSTRATIVE cost at ${IN_PRICE_PER_M}/M in, "
          f"${OUT_PRICE_PER_M}/M out: "
          f"${token_cost(est * 0.5, est * 0.5, IN_PRICE_PER_M, OUT_PRICE_PER_M):.4f}")
    print(f"\n  provider: {provider.name} -- NO network call, NO API key, $0.00")

    try:
        result = run_grid(provider, PROMPTS, configs, samples=args.samples,
                          max_tokens_budget=args.budget)
    except BudgetExceeded as e:
        print(f"\n  REFUSED: {e}")
        return 1

    banner("2. BEHAVIOUR BY CONFIGURATION")
    print(config_table(result))
    print(f"\n  determinism = fraction of samples identical to the first")
    print(f"  distinct    = distinct outputs / samples")
    print(f"  Every rate carries its standard error (M3-L14 section 5.4).")

    banner("3. CAN WE ACTUALLY CLAIM A DIFFERENCE?")
    for a, b in (("extraction", "reckless"), ("factual", "conversation"),
                 ("conversation", "creative")):
        print(f"\n  {a} vs {b}:")
        print(determinism_claim(result, a, b))

    banner("4. TRUNCATION")
    warns = truncation_warnings(result)
    if warns:
        print("\n".join(warns))
        print("\n  These cells hit max_tokens. Their output is INCOMPLETE and")
        print("  must not be parsed (M4-L15). The harness flags them rather")
        print("  than quietly averaging them into the results.")
    else:
        print("  no truncation in this run")

    banner("5. SAMPLE OUTPUTS")
    for label in ("extraction", "conversation", "reckless"):
        cells = [c for c in result.cells
                 if c.config.label == label and c.prompt_id == "extract"]
        if not cells:
            continue
        cell = cells[0]
        print(f"\n  {label} (temperature {cell.config.temperature}):")
        for t in list(dict.fromkeys(x.text for x in cell.completions))[:3]:
            print(f"    {t!r}")

    banner("6. REPRODUCIBILITY")
    print(f"  {'config':<16}{'fingerprint':>14}   settings")
    for cfg in configs:
        print(f"  {cfg.label:<16}{cfg.fingerprint:>14}   "
              f"T={cfg.temperature} top_p={cfg.top_p} "
              f"max_tokens={cfg.max_tokens} seed={cfg.seed}")
    print("\n  The fingerprint hashes every setting that affects behaviour and")
    print("  excludes the human-facing label. Record it with any result you")
    print("  report -- a comparison you cannot reproduce is an anecdote")
    print("  (M3-L14 section 5.9).")

    if args.save:
        path = result.save(args.save)
        print(f"\n  full results written to {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
