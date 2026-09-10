"""M5-L16 lab -- response caching's hidden failure mode, and when routing to
a cheaper model costs MORE than never routing at all.

Section 1 is real arithmetic on a stated (mock) query-traffic mix, showing
semantic caching's higher hit rate against its own defect rate. Section 2 is
real arithmetic comparing three routing strategies at different classifier
accuracies, using M5-L15's own prices for continuity. Section 3 is a small,
exact demonstration of pipeline ordering. No LLM call anywhere in this lab.

Deterministic. No API key, no network.
Run:  python labs/m5/l16_caching_routing.py
"""

from __future__ import annotations


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. EXACT-MATCH VS SEMANTIC CACHING: HIT RATE VS SILENT WRONG ANSWERS")

DUPLICATE_SHARE = 0.15     # literal repeats of a prior query
PARAPHRASE_SHARE = 0.25    # same intent, different wording
NOVEL_SHARE = 1 - DUPLICATE_SHARE - PARAPHRASE_SHARE
WRONG_HIT_RATE_OF_PARAPHRASES = 0.20   # of paraphrase hits, fraction actually wrong

print(f"  1,000 queries: {DUPLICATE_SHARE:.0%} literal duplicates, "
      f"{PARAPHRASE_SHARE:.0%} paraphrases of a prior query, "
      f"{NOVEL_SHARE:.0%} genuinely novel.\n")

N = 1000
exact_hits = N * DUPLICATE_SHARE
semantic_hits = N * (DUPLICATE_SHARE + PARAPHRASE_SHARE)
semantic_wrong = N * PARAPHRASE_SHARE * WRONG_HIT_RATE_OF_PARAPHRASES

print(f"  {'cache type':<16}{'hit rate':>10}{'hits avoided (model calls)':>29}"
      f"{'silently WRONG answers':>25}")
print(f"  {'exact-match':<16}{DUPLICATE_SHARE:>10.0%}{exact_hits:>29.0f}{0:>25.0f}")
print(f"  {'semantic':<16}{DUPLICATE_SHARE + PARAPHRASE_SHARE:>10.0%}"
      f"{semantic_hits:>29.0f}{semantic_wrong:>25.0f}")

print(f"\n  Semantic caching serves {semantic_hits - exact_hits:.0f} more queries")
print(f"  from cache than exact-match -- real cost and latency saved. But")
print(f"  {semantic_wrong:.0f} of those served queries get an answer that is")
print(f"  actually wrong for what THIS query asked, silently, because")
print("  'similar enough to hit the cache' is not the same claim as")
print("  'identical enough to share an answer'. An exact-match cache cannot")
print("  produce this failure at all -- its hit rate is lower, but every hit")
print("  is provably the right answer to the exact same question.")
print("\n  This is the same shape as any recall/precision trade M3-L14")
print("  taught: a higher hit rate is not a free upgrade if some of the")
print("  extra hits are wrong, and a WRONG cache hit is worse than a MISS")
print("  -- a miss just costs a normal model call; a wrong hit costs an")
print("  incorrect answer delivered with the confidence of a cache.")


# ============================================================ 2
rule("2. ROUTING ECONOMICS: WHEN A BAD CLASSIFIER COSTS MORE THAN NO ROUTING")

CHEAP_IN, CHEAP_OUT = 0.125 / 1e6, 0.50 / 1e6     # $/token -- 4x cheaper, uniformly
EXPENSIVE_IN, EXPENSIVE_OUT = 0.50 / 1e6, 2.00 / 1e6   # matches M5-L15

EASY_IN, EASY_OUT = 300, 100
HARD_IN, HARD_OUT = 800, 600
EASY_SHARE = 0.50

TOTAL = 1000
n_easy = TOTAL * EASY_SHARE
n_hard = TOTAL - n_easy

easy_cheap = EASY_IN * CHEAP_IN + EASY_OUT * CHEAP_OUT
easy_expensive = EASY_IN * EXPENSIVE_IN + EASY_OUT * EXPENSIVE_OUT
hard_cheap = HARD_IN * CHEAP_IN + HARD_OUT * CHEAP_OUT
hard_expensive = HARD_IN * EXPENSIVE_IN + HARD_OUT * EXPENSIVE_OUT

print(f"  {TOTAL:,} requests: {EASY_SHARE:.0%} easy ({EASY_IN}in/{EASY_OUT}out tok), "
      f"{1 - EASY_SHARE:.0%} hard ({HARD_IN}in/{HARD_OUT}out tok).")
print(f"  Cheap model: ${CHEAP_IN * 1e6:.2f}/M in, ${CHEAP_OUT * 1e6:.2f}/M out. "
      f"Expensive: ${EXPENSIVE_IN * 1e6:.2f}/M in, ${EXPENSIVE_OUT * 1e6:.2f}/M out.\n")

always_expensive = n_easy * easy_expensive + n_hard * hard_expensive
always_cheap = n_easy * easy_cheap + n_hard * hard_cheap
print(f"  Always expensive: ${always_expensive:.4f} total "
      f"({n_hard:.0f} hard requests handled at full quality)")
print(f"  Always cheap:     ${always_cheap:.4f} total "
      f"({n_hard:.0f} hard requests get a cheap-model answer of unknown "
      f"quality -- not $-quantifiable, a real risk, not modelled here)\n")


def routed_cost(accuracy: float) -> float:
    easy_correct = n_easy * accuracy
    easy_misrouted = n_easy * (1 - accuracy)          # sent to expensive: wasted, not wrong
    hard_correct = n_hard * accuracy
    hard_misrouted = n_hard * (1 - accuracy)           # sent to cheap: fails, needs fallback

    cost = (easy_correct * easy_cheap
            + easy_misrouted * easy_expensive
            + hard_correct * hard_expensive
            + hard_misrouted * (hard_cheap + hard_expensive))   # pays BOTH
    return cost


print(f"  {'classifier accuracy':>20}{'routed total cost':>20}"
      f"{'vs always-expensive':>24}")
for acc in (0.95, 0.90, 0.80, 0.70, 0.65, 0.60, 0.50, 0.40):
    cost = routed_cost(acc)
    delta = cost / always_expensive - 1
    verdict = "cheaper" if delta < 0 else "MORE EXPENSIVE"
    print(f"  {acc:>20.0%}{f'${cost:.4f}':>20}"
          f"{f'{delta:+.1%} ({verdict})':>24}")

# Exact crossover: routed_cost is linear in accuracy, so solve directly.
cost0, cost1 = routed_cost(0.0), routed_cost(1.0)
crossover = (cost0 - always_expensive) / (cost0 - cost1)
print(f"\n  Exact crossover (solved, not read off the table): routing beats "
      f"always-expensive only above {crossover:.1%} classifier accuracy.")

print("\n  At 95%-90% accuracy, routing clearly saves money against always")
print("  using the expensive model. Read down the table: the saving shrinks")
print("  and then REVERSES. Below roughly the crossover point, misrouted")
print("  hard requests -- which pay for BOTH the cheap attempt that failed")
print("  AND the expensive fallback that fixed it -- cost enough that")
print("  routing is now WORSE than never routing at all. A router is only")
print("  worth building if its accuracy clears this bar, and the bar is")
print("  computable, not a guess.")


# ============================================================ 3
rule("3. PIPELINE ORDER: CHECK THE CACHE BEFORE YOU SPEND ON ROUTING")

CLASSIFY_COST = 0.00004    # $ per request to run the routing classifier
CACHE_HIT_RATE = DUPLICATE_SHARE + PARAPHRASE_SHARE   # semantic cache, from section 1
REQUESTS = 100_000

route_first_cost = REQUESTS * CLASSIFY_COST
cache_first_cost = REQUESTS * (1 - CACHE_HIT_RATE) * CLASSIFY_COST

print(f"  {REQUESTS:,} requests/month, classifier costs ${CLASSIFY_COST:.5f} each,")
print(f"  cache hit rate {CACHE_HIT_RATE:.0%} (section 1's semantic cache).\n")
print(f"    route-first (classify every request, then check cache): "
      f"${route_first_cost:.2f}/month spent on classification alone")
print(f"    cache-first (check cache, only classify on a MISS):      "
      f"${cache_first_cost:.2f}/month")
print(f"    wasted classification spend from the wrong order: "
      f"${route_first_cost - cache_first_cost:.2f}/month")

print("\n  This is on top of whatever the classifier saves or costs at the")
print("  MODEL layer (section 2) -- routing-first pays the classification")
print("  cost even on requests that were about to be served from cache for")
print("  free. The fix is one line of pipeline order, not a smarter")
print("  classifier: check the cache FIRST, route only on a miss.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every number is exact arithmetic given the stated inputs. No")
print("  model behaviour, embedding similarity, or classifier is actually")
print("  run -- all rates are stated parameters standing in for them.")
print("\n  ILLUSTRATIVE: the traffic mix, prices, and accuracy figures are")
print("  chosen to make the arithmetic legible, not measured from any real")
print("  system. Measure your own duplicate/paraphrase rates, your own")
print("  cheap/expensive prices, and your own classifier's real accuracy")
print("  before setting a routing policy from this lab's numbers.")
print("\n  NOT SHOWN: how to build the semantic-similarity cache or the")
print("  routing classifier itself (that's an embeddings/retrieval problem,")
print("  M6), and production-grade fallback chains across more than two")
print("  models, which is M13-L08's job, building on this lesson.")

print("\nDone.")
