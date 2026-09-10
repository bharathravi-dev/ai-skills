"""M7-L02 lab -- RAG versus its three real alternatives: stuffing everything
into a long context window, fine-tuning a model on your data, and skipping
the model's "knowledge" entirely with a plain deterministic tool call. Each
comparison is grounded in something actually measured or computed, not just
asserted -- token-cost scaling as a corpus grows, the specific task shapes
where each approach wins, and a worked decision framework.

Deterministic. No API key, no network.
Run:  python labs/m7/l02_rag_vs_alternatives.py
"""

from __future__ import annotations


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. FOUR APPROACHES TO THE SAME QUESTION")

# Reusing M7-L01's own small company-policy knowledge base for continuity.
KB_DOCUMENTS = {
    "P1": "Remote Work Policy. Employees may work remotely up to three days per "
          "week with manager approval. Fully remote arrangements require VP "
          "approval and a signed remote work agreement.",
    "P2": "Expense Reimbursement Policy. Employees must submit expense reports "
          "within thirty days of purchase. Reimbursements over five hundred "
          "dollars require director approval before submission.",
    "P3": "Paid Time Off Policy. Full time employees accrue fifteen days of PTO "
          "per year, increasing to twenty days after three years of service. "
          "PTO requests must be submitted at least two weeks in advance.",
    "P4": "Referral Bonus Policy. Employees who refer a successful hire receive "
          "a two thousand dollar bonus, paid out after the new hire completes "
          "ninety days of employment.",
    "P5": "Parental Leave Policy. Employees are eligible for twelve weeks of "
          "paid parental leave following the birth or adoption of a child, "
          "available to any employee with at least six months of tenure.",
    "P6": "Equipment Policy. New employees receive a company laptop and a one "
          "time three hundred dollar home office stipend within their first "
          "thirty days.",
}
QUERY = "How many weeks of paid parental leave do employees get?"

print(f"  Query: {QUERY!r}\n")

print("  APPROACH 1 -- RAG: retrieve only the relevant chunk(s), insert them")
print("  into the prompt alongside the query. (M7-L01's own pipeline.)")

print("\n  APPROACH 2 -- LONG CONTEXT: skip retrieval entirely; insert EVERY")
print("  document into the prompt on EVERY query, and let the model find the")
print("  relevant part itself.")

print("\n  APPROACH 3 -- FINE-TUNING: retrain the model's weights on this")
print("  company's policies in advance, so the answer comes from the model's")
print("  own parameters at inference time, with no retrieved context at all.")
print("  `[CONCEPTUAL -- this lab does not fine-tune a real model; no training")
print("  infrastructure or cost is available in this environment.]`")

print("\n  APPROACH 4 -- PLAIN TOOL: for a task with a deterministic, computable")
print("  answer (not this one -- see section 5), call a function directly and")
print("  skip the language model's 'knowledge' altogether.")


# ============================================================ 2
rule("2. TOKEN-COST SCALING: RAG VS LONG CONTEXT AS THE CORPUS GROWS")

TOKENS_PER_WORD = 1.3   # [UNVERIFIED] a commonly cited rough rule of thumb for English text


def estimate_tokens(text: str) -> float:
    return len(text.split()) * TOKENS_PER_WORD


doc_word_counts = {d: len(t.split()) for d, t in KB_DOCUMENTS.items()}
avg_words_per_doc = sum(doc_word_counts.values()) / len(doc_word_counts)
avg_tokens_per_doc = avg_words_per_doc * TOKENS_PER_WORD

print(f"  Measured on this lab's {len(KB_DOCUMENTS)} real documents: average "
      f"{avg_words_per_doc:.1f} words/doc, an estimated {avg_tokens_per_doc:.1f} "
      f"tokens/doc (at {TOKENS_PER_WORD} tokens/word).\n")

RAG_TOP_K = 3   # RAG's per-query cost is bounded by how many chunks it retrieves,
                # NOT by corpus size -- this is the entire argument in one constant.
IN_PRICE_PER_M = 0.50   # M5-L15's own stated input price, $/million tokens

print(f"  {'corpus size':>12}{'long-context tokens/query':>28}{'RAG tokens/query':>20}"
      f"{'long-context $/1K queries':>28}{'RAG $/1K queries':>20}")
for n_docs in (6, 50, 500, 5_000, 50_000):
    long_context_tokens = n_docs * avg_tokens_per_doc
    rag_tokens = RAG_TOP_K * avg_tokens_per_doc
    long_context_cost = long_context_tokens * IN_PRICE_PER_M / 1e6 * 1000
    rag_cost = rag_tokens * IN_PRICE_PER_M / 1e6 * 1000
    print(f"  {n_docs:>12,}{long_context_tokens:>28,.0f}{rag_tokens:>20,.0f}"
          f"{'$' + format(long_context_cost, ',.2f'):>28}{'$' + format(rag_cost, ',.2f'):>20}")

print(f"\n  RAG's per-query cost is FIXED at {RAG_TOP_K} chunks regardless of how")
print(f"  large the underlying corpus grows -- retrieval selects a constant-size")
print(f"  slice every time. Long context's per-query cost grows LINEARLY with")
print(f"  total corpus size, because it inserts everything, every query. At this")
print(f"  lab's actual 6-document corpus the two are close; by 50,000 documents")
print(f"  (a realistic size for a real knowledge base), long context costs")
print(f"  roughly {(50_000 * avg_tokens_per_doc) / (RAG_TOP_K * avg_tokens_per_doc):,.0f}x")
print(f"  more per query than RAG, for the same question.")


# ============================================================ 3
rule("3. WHERE LONG CONTEXT IS ACTUALLY THE RIGHT CHOICE")

print("  Section 2's table has a crossover, not a verdict. At this lab's OWN")
print(f"  {len(KB_DOCUMENTS)}-document corpus, long context costs only a few times")
print("  more than RAG -- and it comes with real advantages RAG does not have:")
print("  no retrieval step to get wrong (M7-L01 section 3's vocabulary-mismatch")
print("  miss cannot happen if nothing is ever excluded from the prompt), and")
print("  no separate indexing pipeline to build or maintain (M6-L05-M6-L08).")
print("\n  The honest read: for a SMALL, STABLE corpus -- one that comfortably")
print("  fits in a single prompt at a cost you're willing to pay every query --")
print("  long context is a legitimate, simpler choice, not an inferior one.")
print("  RAG earns its added complexity specifically at the scale where")
print("  section 2's cost gap becomes large, or where the corpus is too big to")
print("  fit in any single context window at all.")


# ============================================================ 4
rule("4. FINE-TUNING VS RAG: FACTS VS BEHAVIOUR, AND THE COST OF AN UPDATE")

print("  `[CONCEPTUAL -- typical, illustrative figures below; not measured in")
print("  this lab, which trains nothing]`\n")
print("  RAG:")
print("    Update mechanism:      re-index the new/changed documents")
print("    Typical time to reflect new data:  seconds to minutes (M6-L10)")
print("  Fine-tuning:")
print("    Update mechanism:      retrain (or re-run a tuning job)")
print("    Typical time to reflect new data:  hours to days, plus re-evaluation")

print("\n  The deeper distinction is not just speed -- it's WHAT each approach is")
print("  good at storing. Fine-tuning shifts a model's weights toward patterns")
print("  in its training data; this is well suited to teaching a STYLE, FORMAT,")
print("  or BEHAVIOUR (respond tersely, always structure answers as JSON, adopt")
print("  a specific tone). It is poorly suited to reliably storing individual,")
print("  precise FACTS for later exact recall -- weights are a lossy, compressed")
print("  summary of training data, not a lookup table. RAG retrieves the actual")
print("  source text VERBATIM at answer time, which is exactly why M7-L01's")
print("  grounded answer could state an exact figure (twelve weeks) with a")
print("  citation -- a fine-tuned model asked the same question has no verbatim")
print("  source to point to, only a weighted tendency learned from examples.")


# ============================================================ 5
rule("5. PLAIN TOOLS: WHEN NEITHER RAG NOR FINE-TUNING IS THE RIGHT ANSWER")

TOOL_QUERY = "What is 15% of $340, and how many minutes is 3.5 hours?"


def calculate_percentage(base: float, percent: float) -> float:
    return round(base * percent / 100, 2)


def hours_to_minutes(hours: float) -> float:
    return hours * 60


print(f"  Query: {TOOL_QUERY!r}\n")
pct_result = calculate_percentage(340, 15)
min_result = hours_to_minutes(3.5)
print(f"  [REAL, direct tool call] calculate_percentage(340, 15) = {pct_result}")
print(f"  [REAL, direct tool call] hours_to_minutes(3.5) = {min_result}")

print("\n  Neither RAG nor fine-tuning belongs anywhere near this query. RAG")
print("  would retrieve a document ABOUT how percentages work, which does not")
print("  compute this specific answer. Fine-tuning would try to make the model")
print("  BETTER AT ARITHMETIC IN GENERAL through weight updates -- expensive,")
print("  slow, and still probabilistic, for a problem with one exact, correct,")
print("  cheaply-computable answer. M5-L08 already covers calling a tool")
print("  directly for exactly this task shape: deterministic, well-defined,")
print("  and answerable without any of the three knowledge-access strategies")
print("  this lesson otherwise compares.")


# ============================================================ 6
rule("6. A DECISION FRAMEWORK")

DECISIONS = [
    ("Task has one deterministic, computable answer",       "Plain tool (M5-L08)"),
    ("Small, stable corpus; simplicity valued over cost",    "Long context"),
    ("Large or frequently-updated corpus; need citations",   "RAG"),
    ("Need to shift STYLE, FORMAT, or BEHAVIOUR broadly",    "Fine-tuning"),
    ("Need to recall specific FACTS precisely and verifiably", "RAG"),
    ("Corpus too large to fit any context window at all",    "RAG"),
]
for situation, approach in DECISIONS:
    print(f"  {situation}\n    -> {approach}")

print("\n  These four approaches are not mutually exclusive in a real system --")
print("  a production assistant might use a fine-tuned model (for tone), that")
print("  calls plain tools (for arithmetic and lookups), backed by RAG (for")
print("  facts and policies), with long context reserved for the rare case of a")
print("  small, one-off document a user pastes directly into a conversation.")


# ============================================================ 7
rule("7. WHAT THIS LAB IS AND IS NOT")

print("  REAL: word counts are computed directly from this lab's actual")
print("  document text; the token-cost and dollar-cost scaling in section 2 is")
print("  real arithmetic on those measured counts, extended by explicit,")
print("  labeled extrapolation to larger corpus sizes; section 5's tool calls")
print("  are genuinely executed, exact computations.")
print("\n  ILLUSTRATIVE / UNVERIFIED: the 1.3 tokens/word conversion is a commonly")
print("  cited rule of thumb, not a measurement from any specific tokenizer;")
print("  section 4's fine-tuning timescales are typical, illustrative figures,")
print("  not measurements -- this lab trains no model at all.")
print("\n  NOT SHOWN: an actual fine-tuning run, an actual long-context API call")
print("  at scale, and the accuracy trade-offs (not just cost) between these")
print("  approaches on real, ambiguous queries -- this lesson's job is the")
print("  decision framework, not a benchmark of any one approach's quality.")

print("\nDone.")
