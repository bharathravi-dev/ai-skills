"""M6-L03 lab -- BM25, computed by hand on a tiny corpus, then its two key
design choices (IDF's rare-term weighting, term-frequency saturation, and
document-length normalisation) isolated and measured one at a time.

Every number in this lab is exact BM25 arithmetic on a small, real corpus
and stated parameters (k1=1.5, b=0.75, the common Okapi BM25 defaults).
No embeddings, no model, nothing mocked -- BM25 is a formula, not a
learned system, so "real" here means "correctly computed," full stop.

Deterministic. No API key, no network, no model download.
Run:  python labs/m6/l03_bm25.py
"""

from __future__ import annotations

import math


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


K1 = 1.5
B = 0.75

CORPUS = {
    "D1": "refund request for damaged item",
    "D2": "please process my refund quickly",
    "D3": "the item arrived damaged and broken",
    "D4": "how do I track my order",
    "D5": "refund refund refund please help me get my refund",
}
TOKENIZED = {doc_id: text.split() for doc_id, text in CORPUS.items()}
DOC_LENGTHS = {doc_id: len(toks) for doc_id, toks in TOKENIZED.items()}
N = len(CORPUS)
AVGDL = sum(DOC_LENGTHS.values()) / N


def doc_freq(term: str) -> int:
    return sum(1 for toks in TOKENIZED.values() if term in toks)


def idf(term: str) -> float:
    n = doc_freq(term)
    return math.log((N - n + 0.5) / (n + 0.5) + 1)


def term_freq(term: str, doc_id: str) -> int:
    return TOKENIZED[doc_id].count(term)


def length_norm(doc_id: str, b: float = B) -> float:
    return 1 - b + b * DOC_LENGTHS[doc_id] / AVGDL


def bm25_term_score(term: str, doc_id: str, k1: float = K1, b: float = B) -> float:
    f = term_freq(term, doc_id)
    if f == 0:
        return 0.0
    L = length_norm(doc_id, b)
    return idf(term) * (f * (k1 + 1)) / (f + k1 * L)


def bm25_score(query_terms: list[str], doc_id: str, k1: float = K1, b: float = B) -> float:
    return sum(bm25_term_score(t, doc_id, k1, b) for t in query_terms)


# ============================================================ 1
rule("1. BM25 BY HAND: A FULL WORKED EXAMPLE")

print(f"  {N}-document corpus, average length {AVGDL:.1f} words:\n")
for doc_id, text in CORPUS.items():
    print(f"    {doc_id} ({DOC_LENGTHS[doc_id]} words): {text!r}")

QUERY = ["refund", "damaged"]
print(f"\n  Query: {QUERY}\n")

for term in QUERY:
    n = doc_freq(term)
    print(f"  IDF({term!r}): doc freq n={n} of N={N} -> "
        f"ln(({N}-{n}+0.5)/({n}+0.5)+1) = {idf(term):.4f}")

print(f"\n  {'doc':<5}{'f(refund)':>11}{'f(damaged)':>12}{'|D|':>6}{'length norm':>13}"
      f"{'BM25 score':>12}")
scores = {}
for doc_id in CORPUS:
    scores[doc_id] = bm25_score(QUERY, doc_id)
    print(f"  {doc_id:<5}{term_freq('refund', doc_id):>11}"
          f"{term_freq('damaged', doc_id):>12}{DOC_LENGTHS[doc_id]:>6}"
          f"{length_norm(doc_id):>13.4f}{scores[doc_id]:>12.4f}")

ranking = sorted(scores, key=lambda d: -scores[d])
print(f"\n  Ranked: {ranking}")
print(f"\n  {ranking[0]} wins -- it is the only document containing BOTH query")
print(f"  terms. Read {ranking[1]} vs {ranking[2]}: {ranking[1]} has 'refund' FOUR times")
print(f"  and no 'damaged'; {ranking[2]} has 'damaged' ONCE and no 'refund'. They")
print("  score within a few hundredths of each other -- four repeats of a")
print("  common term very nearly, but not quite, matches one occurrence of")
print("  a rarer one. That trade-off is the entire subject of sections 2-3.")


# ============================================================ 2
rule("2. IDF: RARE TERMS OUTWEIGH COMMON ONES")

print(f"  IDF as a function of document frequency, at N={N}:\n")
print(f"  {'docs containing term (n)':>26}{'IDF':>10}")
for n in range(0, N + 1):
    val = math.log((N - n + 0.5) / (n + 0.5) + 1)
    note = "  (appears in every document)" if n == N else \
           "  (appears in no document -- query term never matches)" if n == 0 else ""
    print(f"  {n:>26}{val:>10.4f}{note}")

print("\n  A term in every single document contributes almost nothing to a")
print("  score -- it does not distinguish any document from any other, so")
print("  BM25's IDF correctly down-weights it almost to zero. A term found")
print("  in only one document out of five is weighted far higher: finding")
print("  it is genuinely informative about which document matches. This is")
print("  the entire rationale for the word 'inverse' in inverse document")
print("  frequency -- weight falls as document frequency rises.")
print("\n  [The +0.5 smoothing and the outer +1 are what keep this formula's")
print("  IDF positive even at n=N; a common textbook variant omits the")
print("  outer +1 and can go NEGATIVE for terms in more than half the")
print("  corpus -- effectively a penalty for over-common terms. Check which")
print("  variant your search engine actually implements. [UNVERIFIED --")
print("  varies by system; both are legitimately called 'BM25'.]")


# ============================================================ 3
rule("3. TERM-FREQUENCY SATURATION: WHY 10 REPEATS ISN'T 10x THE SCORE")

fixed_idf = 1.0
fixed_L = 1.0    # a document at exactly the average length
print(f"  Holding IDF={fixed_idf} and length-norm={fixed_L} fixed, vary only how many")
print(f"  times the term appears in the document (k1={K1}):\n")
print(f"  {'occurrences (f)':>17}{'score contribution':>21}{'marginal gain':>16}")
prev = 0.0
for f in (1, 2, 3, 4, 5, 10, 20, 50, 1000):
    val = fixed_idf * (f * (K1 + 1)) / (f + K1 * fixed_L)
    marginal = val - prev
    print(f"  {f:>17}{val:>21.4f}{marginal:>16.4f}")
    prev = val

limit = fixed_idf * (K1 + 1)
print(f"\n  As f grows without bound, the score approaches IDF*(k1+1) = "
      f"{limit:.4f} exactly, and NEVER exceeds it. Going from 1 to 2")
print("  occurrences gains real score. Going from 50 to 1000 gains almost")
print("  nothing. This is deliberate: without it, a document could win")
print("  purely by repeating a query word hundreds of times (an old,")
print("  well-known way to game naive keyword ranking), and BM25's")
print("  saturation makes that strategy worthless past a handful of repeats.")


# ============================================================ 4
rule("4. DOCUMENT LENGTH NORMALIZATION: THE b PARAMETER")

short_len, long_len = 5, 15    # long doc is 3x the short one, both avgdl=10
avgdl_demo = 10.0
f_demo = 1   # BOTH documents contain the query term exactly once

print(f"  Two documents, each containing the query term exactly ONCE.")
print(f"  Short document: {short_len} words. Long document: {long_len} words")
print(f"  ({long_len / short_len:.0f}x longer). Corpus average: {avgdl_demo:.0f} words.\n")
print(f"  {'b':>5}{'short-doc score':>18}{'long-doc score':>17}{'ratio (short/long)':>21}")
for b_val in (0.0, 0.25, 0.5, 0.75, 1.0):
    L_short = 1 - b_val + b_val * short_len / avgdl_demo
    L_long = 1 - b_val + b_val * long_len / avgdl_demo
    s_short = fixed_idf * (f_demo * (K1 + 1)) / (f_demo + K1 * L_short)
    s_long = fixed_idf * (f_demo * (K1 + 1)) / (f_demo + K1 * L_long)
    print(f"  {b_val:>5.2f}{s_short:>18.4f}{s_long:>17.4f}{s_short / s_long:>21.2f}")

print("\n  At b=0, length is IGNORED -- both documents score identically for")
print("  the same term frequency, however long either one is. At b=1, the")
print("  long document is penalised at full strength for its length, purely")
print("  because it is 3x longer, independent of whether that length is")
print("  relevant padding or genuinely more content. b=0.75 (this lab's")
print("  default, and a common real default) sits deliberately between the")
print("  two extremes -- some length penalty, not the maximum possible one.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every score in this lab is the exact BM25 formula, correctly")
print("  computed on real (if small) text and stated parameters. There is")
print("  no model and nothing to mock -- BM25 is deterministic arithmetic.")
print("\n  A NOTE ON PARAMETERS: k1=1.5 and b=0.75 are common real defaults")
print("  (e.g. in several widely used search engines), not universal")
print("  constants. `[UNVERIFIED -- check your own search engine's actual")
print("  configured values; many systems allow tuning them.]`")
print("\n  NOT SHOWN: how BM25 combines with semantic search (hybrid search,")
print("  M6-L11), how it scales to a real, large corpus with an inverted")
print("  index (a data-structure topic, not covered here), and stemming or")
print("  tokenisation choices that materially affect which terms 'match' at")
print("  all before BM25 ever runs.")

print("\nDone.")
