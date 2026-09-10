"""M7-L01 lab -- a complete, minimal, real, end-to-end RAG pipeline: why
answering from a model's parametric knowledge alone fails on private,
company-specific information; ingestion through retrieval built entirely
from Module 6's own mechanisms (BM25, M6-L03); a deterministic, template-
based "generation" step standing in for a real LLM call; and a demonstration
that a RAG system's answer quality has a hard ceiling set by its retrieval
quality, not its generation step.

Deterministic. No API key, no network -- consistent with every lab in this
course to date, none of which calls a real LLM API (see section 5).
Run:  python labs/m7/l01_rag_pipeline_end_to_end.py
"""

from __future__ import annotations

import math

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants

# M6-L03's own corpus was small and hand-picked specifically to avoid this
# issue; this lesson's corpus is closer to real prose, where common function
# words otherwise create accidental matches -- on a small corpus, a stopword
# that happens to appear in only one chunk gets an artificially HIGH BM25
# IDF weight (rare = "important" to the formula) purely by chance, not
# relevance. Standard IR practice removes these before scoring; this is a
# realistic preprocessing addition, not a change to BM25's formula itself.
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
}


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS]


def bm25_scores(corpus_tokens: dict, query_terms: list[str]) -> dict:
    n = len(corpus_tokens)
    doc_lens = {d: len(t) for d, t in corpus_tokens.items()}
    avgdl = sum(doc_lens.values()) / n
    df = {term: sum(1 for t in corpus_tokens.values() if term in t) for term in query_terms}
    idf = {term: math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1) for term in query_terms}
    scores = {}
    for d, tokens in corpus_tokens.items():
        score = 0.0
        for term in query_terms:
            f = tokens.count(term)
            if f == 0:
                continue
            numer = f * (K1 + 1)
            denom = f + K1 * (1 - B + B * doc_lens[d] / avgdl)
            score += idf[term] * numer / denom
        scores[d] = score
    return scores


# ============================================================ 1
rule("1. WHY RAG EXISTS: A MODEL CANNOT KNOW WHAT IT WAS NEVER SHOWN")

QUERY = "How many weeks of paid parental leave do employees get?"


def mock_closed_book_answer(query: str) -> str:
    """[MOCK, ILLUSTRATIVE] A hand-scripted stand-in for an LLM answering with
    NO retrieved context -- not a real model call, and not a claim about what
    any specific real model would say. It illustrates a genuine, well-known
    failure mode: a plausible-sounding, specific-sounding number, invented
    because the model has no actual access to this company's real policy."""
    return ("Many companies offer around 6 to 8 weeks of paid parental leave, "
            "though this varies by employer.")


print(f"  Query: {QUERY!r}")
print(f"  No retrieval -- the model answers from parametric knowledge alone:\n")
closed_book = mock_closed_book_answer(QUERY)
print(f"  [MOCK closed-book answer] {closed_book!r}")

print("\n  This is a genuinely plausible-SOUNDING answer -- generically true of")
print("  'many companies' -- and genuinely, specifically WRONG for whichever")
print("  company this question was actually about, because no general-purpose")
print("  model was ever trained on this company's internal policy documents.")
print("  There is no amount of prompting skill (M5) that fixes this: the")
print("  correct number simply is not in the model's parameters. RAG exists")
print("  to solve exactly this -- not by making the model 'smarter', but by")
print("  giving it the actual, relevant document at answer time.")


# ============================================================ 2
rule("2. THE PIPELINE, STAGE BY STAGE, ON REAL DOCUMENTS")

# A small, synthetic internal knowledge base -- company policies, not reused
# from M6's ticket corpus, giving this module its own running example.
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


def naive_chunk(doc_id: str, text: str) -> list[tuple[str, str]]:
    """[REAL, deliberately naive] Split on sentence boundaries. M7-L06/M7-L07
    cover real chunking strategy (size, overlap, structure) in depth -- this
    lesson only needs SOME chunking to make the pipeline concrete."""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return [(f"{doc_id}#{i}", s) for i, s in enumerate(sentences)]


CHUNKS: dict[str, str] = {}
for doc_id, text in KB_DOCUMENTS.items():
    for chunk_id, sentence in naive_chunk(doc_id, text):
        CHUNKS[chunk_id] = sentence
CHUNK_TOKENS = {cid: remove_stopwords(s.lower().replace(",", "").split()) for cid, s in CHUNKS.items()}

print(f"  Step 1 -- INGESTION + CHUNKING: {len(KB_DOCUMENTS)} documents split into "
      f"{len(CHUNKS)} sentence-level chunks.")
print(f"  Step 2 -- INDEXING: BM25 (M6-L03's exact formula, stopwords removed) "
      f"over all {len(CHUNKS)} chunks.")

query_terms = remove_stopwords(QUERY.lower().replace("?", "").split())
scores = bm25_scores(CHUNK_TOKENS, query_terms)
top_chunk_ids = sorted(CHUNKS, key=lambda c: -scores[c])[:2]

print(f"  Step 3 -- RETRIEVAL: top 2 chunks for the query:")
for cid in top_chunk_ids:
    print(f"    {cid}  (score {scores[cid]:.3f}):  {CHUNKS[cid]!r}")

RETRIEVAL_THRESHOLD = 0.5
retrieved = [(cid, CHUNKS[cid]) for cid in top_chunk_ids if scores[cid] >= RETRIEVAL_THRESHOLD]
context_block = "\n".join(f"[{cid}] {text}" for cid, text in retrieved)
print(f"\n  Step 4 -- CONTEXT ASSEMBLY: {len(retrieved)} chunk(s) above threshold "
      f"assembled into a context block (token budgeting is M7-L11's topic):")
print(f"    {context_block!r}")


def mock_grounded_answer(query: str, retrieved_chunks: list[tuple[str, str]]) -> str:
    """[MOCK] A deterministic stand-in for an LLM's generation step: reads the
    TOP-RANKED retrieved chunk (retrieval already ordered these by relevance;
    re-deriving a second, independent relevance signal here would be both
    redundant and, as an early version of this lab found, noisier -- raw
    word overlap over-counts shared stopwords) and cites its source chunk.
    Real generation (M7-L12 covers citation quality in depth) would
    paraphrase and synthesize; this keeps the demonstration checkable and
    honest about being a template, not a language model."""
    if not retrieved_chunks:
        return "I don't have information about that in the provided documents."
    best_cid, best_text = retrieved_chunks[0]
    doc_id = best_cid.split("#")[0]
    return f"{best_text.strip()}. (Source: {doc_id})"


grounded = mock_grounded_answer(QUERY, retrieved)
print(f"\n  Step 5 -- GENERATION: [MOCK grounded answer] {grounded!r}")

print("\n  Compare directly to section 1's closed-book answer: the closed-book")
print("  mock invented a generic, wrong number. The retrieval-grounded pipeline")
print("  found the ACTUAL policy document (P5) and answered with the real")
print("  number (twelve weeks) plus a verifiable citation -- not because the")
print("  generation step got smarter, but because it was given the right")
print("  document to read from. This is RAG's entire value proposition in one")
print("  side-by-side comparison.")


# ============================================================ 3
rule("3. RAG's QUALITY CEILING IS SET BY RETRIEVAL, NOT GENERATION")

MISMATCH_QUERY = "Do you pay staff a reward for suggesting people who then join the team?"
mismatch_terms = remove_stopwords(MISMATCH_QUERY.lower().replace("?", "").split())
mismatch_scores = bm25_scores(CHUNK_TOKENS, mismatch_terms)
mismatch_top = sorted(CHUNKS, key=lambda c: -mismatch_scores[c])[:2]

print(f"  Query: {MISMATCH_QUERY!r}")
print("  This asks EXACTLY what P4 (Referral Bonus Policy) answers -- but using")
print("  different words throughout: 'pay/reward' instead of 'bonus',")
print("  'suggesting people' instead of 'refer', 'join the team' instead of")
print("  'hire' -- no shared content word with P4's actual text at all.\n")
for cid in mismatch_top:
    print(f"    {cid}  (score {mismatch_scores[cid]:.3f}):  {CHUNKS[cid]!r}")

mismatch_retrieved = [(cid, CHUNKS[cid]) for cid in mismatch_top if mismatch_scores[cid] >= RETRIEVAL_THRESHOLD]
mismatch_answer = mock_grounded_answer(MISMATCH_QUERY, mismatch_retrieved)
print(f"\n  Retrieved {len(mismatch_retrieved)} chunk(s) above threshold.")
print(f"  [MOCK generation output] {mismatch_answer!r}")

print("\n  BM25 (M6-L03) scores by literal term overlap, and this query shares")
print("  almost no literal terms with P4's actual wording -- exactly the")
print("  vocabulary gap M6-L01 introduced and M6-L04/M6-L11 addressed with")
print("  dense and hybrid retrieval. The generation step here did exactly what")
print("  it should with no relevant context: it abstained (M7-L13's topic)")
print("  rather than guessing. But notice what actually failed: not the")
print("  generation template, and not the model's 'reasoning' -- the RETRIEVAL")
print("  step never found the one document that had the real answer. Every")
print("  technique in Module 6 (BM25, dense, hybrid, reranking) exists to make")
print("  this specific failure less likely; no amount of generation-side")
print("  cleverness (M5's prompting techniques) can answer a question from a")
print("  document the pipeline never retrieved.")


# ============================================================ 4
rule("4. THE FULL ARCHITECTURE, AND WHERE EACH LESSON FITS")

STAGES = [
    ("Ingestion & parsing",        "M7-L03, M7-L04"),
    ("Cleaning & deduplication",   "M7-L05"),
    ("Chunking",                   "M7-L06, M7-L07"),
    ("Metadata & provenance",      "M7-L08"),
    ("Embedding & indexing",       "M6-L01, M6-L02, M6-L05-M6-L08"),
    ("Query rewriting",            "M7-L09"),
    ("Retrieval & reranking",      "M6-L03, M6-L04, M6-L11, M6-L12, M7-L10"),
    ("Context assembly",           "M7-L11"),
    ("Generation & citations",     "M7-L12"),
    ("Abstention",                 "M7-L13"),
    ("Evaluation",                 "M6-L13, M7-L19"),
]
print("  This lab's five steps (ingest, chunk, index, retrieve, generate) are a")
print("  minimal skeleton. The full pipeline this module builds toward:\n")
print(f"  {'Stage':<26}{'Covered in'}")
for stage, lessons in STAGES:
    print(f"  {stage:<26}{lessons}")

print("\n  Every stage after 'retrieval' in this lab was a placeholder (naive")
print("  chunking, a template generator, no reranking, no query rewriting).")
print("  That is deliberate: this lesson's job is the shape of the whole")
print("  pipeline and where retrieval quality caps answer quality, not the")
print("  depth of any one stage -- each gets its own lesson from here.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: chunking is genuinely executed (naive, sentence-based); scoring")
print("  is M6-L03's exact, unmodified BM25 formula, with standard stopword")
print("  removal added as realistic preprocessing (this lesson's prose corpus")
print("  is closer to real text than M6-L03's hand-picked one, where accidental")
print("  stopword matches would otherwise dominate a small corpus); the")
print("  vocabulary-mismatch retrieval failure in section 3 -- every score")
print("  landing at exactly 0.000 -- is a real, measured BM25 outcome on this")
print("  corpus, not scripted.")
print("\n  MOCK: 'generation' in both sections 1 and 2 is a hand-coded")
print("  template/extraction function, not a real LLM call. This matches")
print("  every lab in this course to date -- none calls a real model API,")
print("  consistent with this course's offline-first design (COURSE_PLAN.md A4).")
print("  Section 1's closed-book answer is a scripted ILLUSTRATION of a")
print("  plausible failure mode, not a transcript of any real model's output.")
print("\n  NOT SHOWN: real chunking strategy (M7-L06/M7-L07), query rewriting")
print("  (M7-L09), reranking integration (M7-L10, though M6-L12 built the")
print("  mechanism), token-budgeted context assembly (M7-L11), and real")
print("  citation-quality verification (M7-L12) -- each is this module's own")
print("  upcoming lesson.")

print("\nDone.")
