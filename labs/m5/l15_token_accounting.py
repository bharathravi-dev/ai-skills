"""M5-L15 lab -- token accounting: pricing asymmetry, caching, blended rates,
and why a short demo sample underestimates a real cost forecast.

Every section is REAL arithmetic on stated (illustrative, dated) prices and
parameters. No LLM call, no simulation of model behaviour -- this lab is
entirely about correctly accounting for costs you already know, not about
predicting what a model will do.

Prices are ILLUSTRATIVE and dated 2026-09-09. Verify your own provider's
current pricing before relying on any number here.

Deterministic. No API key, no network.
Run:  python labs/m5/l15_token_accounting.py
"""

from __future__ import annotations


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


IN_PRICE = 0.50 / 1e6     # $/token, input
OUT_PRICE = 2.00 / 1e6    # $/token, output
CACHE_DISCOUNT = 0.90     # fraction OFF the input price for a cache hit


# ============================================================ 1
rule("1. INPUT VS OUTPUT PRICING: THE ASYMMETRY")

print(f"  Stated prices [ILLUSTRATIVE, 2026-09-09]: input ${IN_PRICE * 1e6:.2f}/M, "
      f"output ${OUT_PRICE * 1e6:.2f}/M -- output costs "
      f"{OUT_PRICE / IN_PRICE:.0f}x input, per token.\n")

RATIOS = [("mostly input (20:1)", 2000, 100),
          ("balanced-ish (4:1)", 1600, 400),
          ("even split (1:1)", 1000, 1000),
          ("mostly output (1:4)", 400, 1600),
          ("mostly output (1:20)", 100, 2000)]

print(f"  {'shape':<24}{'in tok':>8}{'out tok':>9}{'in $':>10}{'out $':>10}"
      f"{'out share of $':>16}")
for name, in_tok, out_tok in RATIOS:
    in_cost = in_tok * IN_PRICE
    out_cost = out_tok * OUT_PRICE
    total = in_cost + out_cost
    print(f"  {name:<24}{in_tok:>8}{out_tok:>9}{f'${in_cost:.5f}':>10}"
          f"{f'${out_cost:.5f}':>10}{out_cost / total:>16.0%}")

breakeven_ratio = OUT_PRICE / IN_PRICE
print(f"\n  Break-even (in tokens : out tokens) where the two halves cost the")
print(f"  same: {breakeven_ratio:.0f}:1. Below that ratio -- i.e. relatively more")
print(f"  output -- OUTPUT dominates the bill even though it is usually the")
print(f"  smaller number of tokens on the page. A 2,000-token prompt that")
print(f"  produces a 400-token answer is already 44% output cost.")


# ============================================================ 2
rule("2. PROMPT CACHING: A REQUEST-STRUCTURE DECISION")

SYSTEM_TOOLS_TOK = 3000     # stable prefix: system prompt + tool definitions
PER_TURN_NEW = 300          # varies every request: current message, retrieved bits
OUTPUT_TOK = 400
SESSION_REQUESTS = 20

print(f"  A stable {SYSTEM_TOOLS_TOK:,}-token prefix (system + tools), "
      f"{PER_TURN_NEW} new input tokens/request, {OUTPUT_TOK} output tokens.")
print(f"  Cache discount on a hit: {CACHE_DISCOUNT:.0%} off the cached "
      f"portion's input price. [UNVERIFIED -- illustrative; check your "
      f"provider's current mechanics and minimum-prefix rules.]\n")


def cost_no_cache(n_requests: int) -> float:
    per_req = (SYSTEM_TOOLS_TOK + PER_TURN_NEW) * IN_PRICE + OUTPUT_TOK * OUT_PRICE
    return per_req * n_requests


def cost_with_cache(n_requests: int) -> float:
    first = SYSTEM_TOOLS_TOK * IN_PRICE + PER_TURN_NEW * IN_PRICE + OUTPUT_TOK * OUT_PRICE
    cached_prefix_price = SYSTEM_TOOLS_TOK * IN_PRICE * (1 - CACHE_DISCOUNT)
    later = cached_prefix_price + PER_TURN_NEW * IN_PRICE + OUTPUT_TOK * OUT_PRICE
    return first + later * (n_requests - 1)


no_cache_total = cost_no_cache(SESSION_REQUESTS)
with_cache_total = cost_with_cache(SESSION_REQUESTS)
print(f"  A {SESSION_REQUESTS}-request session:")
print(f"    without caching: ${no_cache_total:.4f}")
print(f"    with caching:    ${with_cache_total:.4f}")
print(f"    saved:           ${no_cache_total - with_cache_total:.4f} "
      f"({1 - with_cache_total / no_cache_total:.0%})")

print("\n  What breaks the cache: anything VARIABLE placed BEFORE the stable")
print("  prefix. A request built as [today's date][system prompt][tools]")
print("  never matches byte-for-byte request to request, so every single")
print("  request misses -- silently reverting to the 'without caching' total")
print(f"  above (${no_cache_total:.4f} instead of ${with_cache_total:.4f}) with")
print("  no error raised anywhere. Put anything that changes AFTER the")
print("  stable block, never before it.")


# ============================================================ 3
rule("3. ONE BLENDED RATE VS TWO REAL RATES")

ASSUMED_IN, ASSUMED_OUT = 1600, 400   # the shape a blended rate was built from
blended_rate = (ASSUMED_IN * IN_PRICE + ASSUMED_OUT * OUT_PRICE) / (ASSUMED_IN + ASSUMED_OUT)
print(f"  A blended $/token rate, built from one assumed shape "
      f"({ASSUMED_IN} in : {ASSUMED_OUT} out): ${blended_rate * 1e6:.3f}/M tokens.\n")

TASKS = [
    ("summarization (input-heavy)", 8000, 200),
    ("the shape the blend assumed", 1600, 400),
    ("open-ended generation (output-heavy)", 200, 2000),
]

print(f"  {'task':<38}{'exact cost':>12}{'blended est.':>14}{'error':>9}")
for name, in_tok, out_tok in TASKS:
    exact = in_tok * IN_PRICE + out_tok * OUT_PRICE
    blended_est = (in_tok + out_tok) * blended_rate
    error = (blended_est - exact) / exact
    print(f"  {name:<38}{f'${exact:.5f}':>12}{f'${blended_est:.5f}':>14}"
          f"{error:>+9.0%}")

print("\n  The blended rate is exact only for the shape it was built from --")
print("  by construction, the middle row's error is 0%. Move away from that")
print("  shape in either direction and the estimate is wrong, and wrong in")
print("  OPPOSITE directions: it overcharges input-heavy tasks (which pay a")
print("  cheaper real rate than the blend assumes) and undercharges")
print("  output-heavy ones. A single $/token number is a convenience for a")
print("  slide, not a substitute for tracking the two real rates.")


# ============================================================ 4
rule("4. FORECASTING FROM A SHORT DEMO SAMPLE UNDERESTIMATES BADLY")

MONTHLY_VOLUME = 100_000
DEMO_SAMPLE_MEAN_TOK = 1_200     # what a QA/demo sample of short chats looks like

demo_based_estimate = MONTHLY_VOLUME * DEMO_SAMPLE_MEAN_TOK * blended_rate
print(f"  A team estimates monthly cost from a {DEMO_SAMPLE_MEAN_TOK}-token")
print(f"  average, drawn from short QA/demo conversations, at "
      f"{MONTHLY_VOLUME:,} requests/month:")
print(f"    estimate: {MONTHLY_VOLUME:,} x {DEMO_SAMPLE_MEAN_TOK} tok x "
      f"${blended_rate * 1e6:.3f}/M = ${demo_based_estimate:,.2f}\n")

print("  Real production traffic, by percentile (illustrative; measure your")
print("  own), each bucket costed at its own midpoint token count:\n")
BUCKETS = [
    ("up to p50", 0.50, 1_200),
    ("p50-p90", 0.40, 5_000),
    ("p90-p99", 0.09, 25_000),
    ("above p99", 0.01, 90_000),
]
print(f"  {'bucket':<12}{'share':>7}{'requests':>10}{'tok/request':>13}{'bucket cost':>14}")
actual_total = 0.0
for name, share, tok in BUCKETS:
    n = MONTHLY_VOLUME * share
    cost = n * tok * blended_rate
    actual_total += cost
    print(f"  {name:<12}{share:>7.0%}{n:>10,.0f}{tok:>13,}{f'${cost:,.2f}':>14}")

print(f"\n  actual (bucketed) total: ${actual_total:,.2f}")
print(f"  demo-sample estimate:    ${demo_based_estimate:,.2f}")
print(f"  underestimate factor:    {actual_total / demo_based_estimate:.1f}x")

print("\n  Only 10% of requests (p90 and above) drive the majority of the")
print("  gap. A demo sample that happens to be all short conversations --")
print("  the natural shape of manual QA testing -- never sees that 10%, and")
print("  the resulting forecast is wrong by a large, one-directional factor")
print("  before a single real user has been added.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every number here is exact arithmetic given the stated inputs.")
print("  No model behaviour is simulated anywhere in this lab.")
print("\n  ILLUSTRATIVE / DATED: the prices, the cache discount and its")
print("  eligibility rules, and section 4's traffic percentiles are all")
print("  stated assumptions, current as of 2026-09-09 at best. Prices and")
print("  caching mechanics change; verify your own provider's current")
print("  documentation before budgeting from any number in this file.")
print("\n  NOT SHOWN: multi-model routing costs (M5-L16), the token cost of a")
print("  failed or refused request (M5-L14), and provider-specific minimums")
print("  or rounding rules for what counts as a cacheable prefix.")

print("\nDone.")
