"""M7-L11 lab -- assembling M7-L10's reranked chunks into an actual context
block under a real token budget: real budget accounting (reusing M7-L02's
token estimate), a measured comparison of two truncation strategies when
reranked chunks exceed budget, why chunk order within the context window is
not an afterthought, and deduplicating near-identical retrieved chunks at
assembly time to avoid wasting budget on redundant content.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l11_context_assembly_token_budgets.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")

TOKENS_PER_WORD = 1.3   # [UNVERIFIED] M7-L02's own stated rough rule of thumb


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def estimate_tokens(text: str) -> float:
    return len(text.split()) * TOKENS_PER_WORD


# ============================================================ 1
rule("1. THE RETRIEVAL CONTEXT BUDGET IS WHAT'S LEFT OVER, NOT THE WHOLE WINDOW")

TOTAL_CONTEXT_WINDOW = 8_000     # [ILLUSTRATIVE] a round number for clean arithmetic
SYSTEM_PROMPT_TOKENS = 300
CONVERSATION_HISTORY_TOKENS = 500
RESERVED_OUTPUT_TOKENS = 1_000

retrieval_budget = (TOTAL_CONTEXT_WINDOW - SYSTEM_PROMPT_TOKENS
                    - CONVERSATION_HISTORY_TOKENS - RESERVED_OUTPUT_TOKENS)

print(f"  Total context window:         {TOTAL_CONTEXT_WINDOW:>6,} tokens")
print(f"  - System prompt:              {SYSTEM_PROMPT_TOKENS:>6,} tokens")
print(f"  - Conversation history:       {CONVERSATION_HISTORY_TOKENS:>6,} tokens")
print(f"  - Reserved for model output:  {RESERVED_OUTPUT_TOKENS:>6,} tokens")
print(f"  {'=' * 45}")
print(f"  = Budget actually available for retrieved context: {retrieval_budget:,} tokens")

print("\n  This is M5-L11's context-engineering discipline, applied specifically")
print("  to the retrieval slot: the context window is not one pool available")
print("  to retrieved chunks -- it is shared with the system prompt, whatever")
print("  conversation history is being carried (M7-L09's rewriting target),")
print("  and space reserved so the model can actually finish its answer.")


# ============================================================ 2
rule("2. WHEN RERANKED CHUNKS EXCEED BUDGET: TWO STRATEGIES, MEASURED")

# M7-L10-style reranked chunks, already in final rank order.
RERANKED_CHUNKS = [
    ("P3#1", "Full time employees accrue fifteen days of PTO per year, increasing to twenty days "
              "after three years of service, based on continuous employment without any unpaid leave "
              "gaps exceeding thirty consecutive days in a given calendar year."),
    ("P3#0", "Paid Time Off Policy applies to all full time employees hired before the policy's most "
              "recent revision date, with part time employees accruing PTO on a prorated basis "
              "according to their contracted weekly hours."),
    ("P5#1", "Employees are eligible for twelve weeks of paid parental leave following the birth or "
              "adoption of a child, available to any employee with at least six months of tenure at "
              "the time the leave begins."),
    ("P1#0", "Remote Work Policy allows employees to work remotely up to three days per week with "
              "direct manager approval, renewed quarterly, and documented in the employee's personnel "
              "file for audit purposes."),
    ("P4#0", "Referral Bonus Policy pays employees a two thousand dollar bonus for a successful hire "
              "referral, disbursed after the new hire completes ninety consecutive days of active "
              "employment without a formal performance improvement plan."),
]

BUDGET = 60   # tokens -- deliberately small so the exceed-budget case is unavoidable in this example
chunk_tokens = {cid: estimate_tokens(text) for cid, text in RERANKED_CHUNKS}
total_tokens = sum(chunk_tokens.values())

print(f"  {len(RERANKED_CHUNKS)} reranked chunks, most relevant first, "
      f"estimated token counts:")
for cid, text in RERANKED_CHUNKS:
    print(f"    {cid} ({chunk_tokens[cid]:.0f} tok): {text[:70]!r}...")
print(f"\n  Total: {total_tokens:.0f} tokens vs. a budget of {BUDGET} tokens for this example "
      f"(deliberately tight to force the trade-off).")


def drop_from_bottom(chunks: list[tuple[str, str]], budget: float) -> list[tuple[str, str]]:
    kept, used = [], 0.0
    for cid, text in chunks:
        t = estimate_tokens(text)
        if used + t > budget:
            break
        kept.append((cid, text))
        used += t
    return kept


def truncate_proportionally(chunks: list[tuple[str, str]], budget: float) -> list[tuple[str, str]]:
    share = budget / len(chunks)
    result = []
    for cid, text in chunks:
        words = text.split()
        keep_n = max(1, int(share / TOKENS_PER_WORD))
        truncated = " ".join(words[:keep_n])
        if keep_n < len(words):
            truncated += " [...]"
        result.append((cid, truncated))
    return result


dropped_strategy = drop_from_bottom(RERANKED_CHUNKS, BUDGET)
truncated_strategy = truncate_proportionally(RERANKED_CHUNKS, BUDGET)

print(f"\n  STRATEGY A -- drop from the bottom (keep highest-ranked chunks whole, "
      f"drop the rest):")
for cid, text in dropped_strategy:
    print(f"    {cid} (complete, {estimate_tokens(text):.0f} tok): {text!r}")
print(f"  Kept {len(dropped_strategy)} of {len(RERANKED_CHUNKS)} chunks, each FULLY intact.")

print(f"\n  STRATEGY B -- truncate every chunk proportionally (keep all "
      f"{len(RERANKED_CHUNKS)}, each shortened):")
for cid, text in truncated_strategy:
    print(f"    {cid} (partial, {estimate_tokens(text):.0f} tok): {text!r}")
print(f"  Kept all {len(truncated_strategy)} chunks, each CUT OFF mid-sentence.")

print("\n  Strategy A guarantees every included chunk is complete and internally")
print("  coherent, at the cost of dropping lower-ranked information entirely.")
print("  Strategy B guarantees every chunk contributes SOMETHING, at the cost")
print("  of each contribution being incomplete -- and, per M7-L06's own")
print("  measured finding, an arbitrary mid-sentence or mid-fact cut can sever")
print("  a label from its value just as easily inside a context-assembly")
print("  truncation as inside chunking itself. Neither strategy is free; the")
print("  right choice depends on whether partial information or missing")
print("  information is more useful for the task at hand.")


# ============================================================ 3
rule("3. ORDER WITHIN THE CONTEXT WINDOW IS NOT AN AFTERTHOUGHT")

print("  `[CONCEPTUAL -- not measured in this lab, which makes no real LLM call]`")
print("  Published research on long-context LLM behavior has reported a")
print("  'lost in the middle' effect: information placed in the MIDDLE of a")
print("  long context is sometimes used less reliably by a model than")
print("  information placed near the BEGINNING or END of the same context,")
print("  even when all of it is technically present. `[UNVERIFIED -- this is")
print("  model- and version-specific; verify against your own model and task")
print("  before relying on it.]`")
print("\n  If this effect applies to your model, the practical implication is")
print("  direct: place the highest-reranked (most likely to matter) chunk at")
print("  the START or END of the assembled context, not buried in an arbitrary")
print("  middle position -- simply preserving M7-L10's rank order when")
print("  concatenating chunks already does this correctly, provided the most")
print("  relevant chunk is placed first (or last), not in the middle of the list.")


# ============================================================ 4
rule("4. DEDUPLICATING NEAR-IDENTICAL RETRIEVED CHUNKS AT ASSEMBLY TIME")


def shingles(text: str, k: int = 4) -> set[str]:
    words = text.lower().split()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


NEAR_DUP_CHUNKS = [
    ("P3#1a", "Full time employees accrue fifteen days of PTO per year, increasing to twenty days "
               "after three years of service."),
    ("P3#1b", "Full time employees accrue fifteen days of PTO each year, increasing to twenty days "
               "after three years of tenure."),
    ("P5#1", "Employees are eligible for twelve weeks of paid parental leave following the birth or "
              "adoption of a child."),
]

sim_ab = jaccard(shingles(NEAR_DUP_CHUNKS[0][1]), shingles(NEAR_DUP_CHUNKS[1][1]))
sim_ac = jaccard(shingles(NEAR_DUP_CHUNKS[0][1]), shingles(NEAR_DUP_CHUNKS[2][1]))

print(f"  Retrieved chunks can overlap even after corpus-level dedup (M7-L05) --")
print(f"  e.g. two chunks from OVERLAPPING windows (M7-L06) covering the same fact:\n")
for cid, text in NEAR_DUP_CHUNKS:
    print(f"    {cid}: {text!r}")
print(f"\n  Jaccard(P3#1a, P3#1b) = {sim_ab:.3f}  (near-duplicate PTO chunks)")
print(f"  Jaccard(P3#1a, P5#1)  = {sim_ac:.3f}  (genuinely different topic)")

DEDUP_THRESHOLD = 0.5
deduped = [NEAR_DUP_CHUNKS[0]]
for cid, text in NEAR_DUP_CHUNKS[1:]:
    if all(jaccard(shingles(text), shingles(t)) < DEDUP_THRESHOLD for _, t in deduped):
        deduped.append((cid, text))
print(f"\n  After assembly-time dedup (threshold {DEDUP_THRESHOLD}, M7-L05's shingling method): "
      f"{[cid for cid, _ in deduped]} kept, "
      f"{[cid for cid, _ in NEAR_DUP_CHUNKS if cid not in [c for c, _ in deduped]]} dropped as redundant.")
tokens_saved = estimate_tokens(NEAR_DUP_CHUNKS[1][1])
print(f"  Roughly {tokens_saved:.0f} tokens of budget freed up -- enough, in section 2's tight")
print("  budget, to include an additional, genuinely different chunk instead of")
print("  a second near-copy of information already present.")


# ============================================================ 5
rule("5. THE FINAL ASSEMBLED CONTEXT BLOCK, WITH CITATIONS METADATA")

FINAL_CHUNKS = dropped_strategy   # from section 2's strategy A
SOURCE_URIS = {"P3#1": "hr-portal://policies/pto-policy#v2",
               "P3#0": "hr-portal://policies/pto-policy#v2",
               "P5#1": "hr-portal://policies/parental-leave#v1"}

context_block = "\n\n".join(
    f"[Source: {SOURCE_URIS.get(cid, 'unknown')}]\n{text}" for cid, text in FINAL_CHUNKS
)
print("  The actual context block assembled for the model (M7-L08's provenance")
print("  metadata attached per chunk, ready for M7-L12's citation step):\n")
print(context_block)
print(f"\n  Final assembled size: {estimate_tokens(context_block):.0f} tokens "
      f"(budget was {BUDGET}).")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: token estimates use M7-L02's own stated word-to-token ratio,")
print("  applied consistently; both truncation strategies and the assembly-")
print("  time deduplication are genuinely computed, not scripted; the near-")
print("  duplicate Jaccard scores use M7-L05's exact shingling method.")
print("\n  ILLUSTRATIVE / CONCEPTUAL: the total context window and reserved")
print("  token amounts in section 1 are round, chosen numbers, not a specific")
print("  real model's limits. Section 3's 'lost in the middle' effect is")
print("  reported as published, general research, not measured in this lab,")
print("  which makes no real LLM call at all.")
print("\n  NOT SHOWN: summarizing (rather than truncating or dropping) chunks")
print("  that don't fit budget, which is M5-L11's own topic applied here; and")
print("  how the assembled context block's citations get verified against the")
print("  model's actual generated answer, which is M7-L12's topic next.")

print("\nDone.")
