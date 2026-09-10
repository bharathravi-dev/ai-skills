"""M7-L13 lab -- deciding, not just detecting, when a RAG system should say
"I don't know": a real threshold-based abstention decision built on BM25
retrieval scores, measured as a genuine confusion matrix (answerable vs
unanswerable queries, correctly answered/abstained vs incorrectly so), the
asymmetric real cost of the two error types, a measured threshold trade-off,
and what separates a genuinely useful abstention message from a merely terse
refusal.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l13_abstention.py
"""

from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
    "my", "it", "can", "i",
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


KB_DOCUMENTS = {
    "P1": "Remote Work Policy. Employees may work remotely up to three days per week with manager approval.",
    "P2": "Expense Reimbursement Policy. Employees must submit expense reports within thirty days of purchase.",
    "P3": "Paid Time Off Policy. Full time employees accrue fifteen days of PTO per year.",
    "P4": "Referral Bonus Policy. Employees who refer a successful hire receive a two thousand dollar bonus.",
    "P5": "Parental Leave Policy. Employees are eligible for twelve weeks of paid parental leave.",
    "P6": "Equipment Policy. New employees receive a company laptop and a home office stipend.",
}
CHUNK_TOKENS = {d: remove_stopwords(t.lower().replace(",", "").replace(".", "").split())
                for d, t in KB_DOCUMENTS.items()}


# ============================================================ 1
rule("1. WHY ABSTAIN AT ALL?")

print("  M7-L01 section 1 showed a closed-book mock answer inventing a")
print("  plausible-sounding, specific, WRONG number for a question the model")
print("  had no real access to. M7-L12 showed a citation-backed claim can")
print("  still be ungrounded. Both failures share one shape: the system")
print("  produced a confident-sounding answer when it should have said so")
print("  plainly instead -- 'I don't have enough information to answer that.'")
print("  This lesson is about deciding WHEN to say that, deliberately, not")
print("  leaving it to chance.")


# ============================================================ 2
rule("2. A REAL ABSTENTION DECISION FUNCTION")

QUERIES = [
    ("How many days of PTO do employees get?", True),
    ("What is the referral bonus amount?", True),
    ("How many weeks of parental leave are available?", True),
    ("What is the company stock option vesting schedule?", False),
    ("Can I bring my dog to the office?", False),
    ("What is the CEO name?", False),
]

THRESHOLD = 2.0


def top_score(query: str) -> tuple[str, float]:
    terms = remove_stopwords(query.lower().replace("?", "").split())
    scores = bm25_scores(CHUNK_TOKENS, terms)
    top = max(scores, key=scores.get)
    return top, scores[top]


def should_abstain(score: float, threshold: float) -> bool:
    return score < threshold


print(f"  Decision rule: abstain if the top BM25 retrieval score falls below "
      f"{THRESHOLD}.\n")
print(f"  {'Query':<52}{'Answerable?':<13}{'Top score':<11}{'Decision'}")
for query, is_answerable in QUERIES:
    top_doc, score = top_score(query)
    decision = "ABSTAIN" if should_abstain(score, THRESHOLD) else f"ANSWER (from {top_doc})"
    print(f"  {query:<52}{str(is_answerable):<13}{score:<11.3f}{decision}")


# ============================================================ 3
rule("3. MEASURING ABSTENTION ACCURACY -- A REAL CONFUSION MATRIX")

tp = tn = fp = fn = 0
for query, is_answerable in QUERIES:
    _, score = top_score(query)
    abstained = should_abstain(score, THRESHOLD)
    if is_answerable and not abstained:
        tp += 1
    elif not is_answerable and abstained:
        tn += 1
    elif not is_answerable and not abstained:
        fp += 1
    elif is_answerable and abstained:
        fn += 1

print(f"  At threshold={THRESHOLD}:")
print(f"    Correctly answered (true positive):   {tp}")
print(f"    Correctly abstained (true negative):  {tn}")
print(f"    WRONGLY answered (false positive):    {fp}  <- DANGEROUS: confident wrong/ungrounded answer")
print(f"    WRONGLY abstained (false negative):   {fn}  <- ANNOYING: refused an answerable question")

print("\n  These two error types are not equally bad. A false positive here")
print("  means the system would have generated an answer from a document")
print("  (M7-L12's groundedness problem) that doesn't actually address the")
print("  question -- exactly M7-L01 section 1's closed-book hallucination")
print("  risk, now happening WITH a citation attached that looks legitimate.")
print("  A false negative means a real, answerable question got an")
print("  unnecessary refusal -- frustrating, but not actively misleading.")
print("  This is the same asymmetry M3-L14 taught for classification generally,")
print("  applied here to a specific, consequential decision.")


# ============================================================ 4
rule("4. THE THRESHOLD TRADE-OFF, MEASURED")

print(f"  {'threshold':>10}{'TP':>5}{'TN':>5}{'FP (dangerous)':>17}{'FN (annoying)':>16}")
for threshold in (1.0, 2.0, 3.0):
    tp = tn = fp = fn = 0
    for query, is_answerable in QUERIES:
        _, score = top_score(query)
        abstained = should_abstain(score, threshold)
        if is_answerable and not abstained:
            tp += 1
        elif not is_answerable and abstained:
            tn += 1
        elif not is_answerable and not abstained:
            fp += 1
        elif is_answerable and abstained:
            fn += 1
    print(f"  {threshold:>10.1f}{tp:>5}{tn:>5}{fp:>17}{fn:>16}")

print("\n  At threshold=1.0 (too permissive), the two genuinely unanswerable")
print("  queries that happened to share a word with the Equipment Policy")
print("  ('office', 'company') score just high enough to pass -- the system")
print("  would confidently answer from a document that has nothing to do")
print("  with either question. At threshold=3.0 (too strict), a genuinely")
print("  answerable PTO question (scoring 2.21) gets refused unnecessarily.")
print("  Threshold=2.0 happens to separate this lab's specific 6 queries")
print("  perfectly -- a real, measured result, not a guarantee that any fixed")
print("  threshold generalizes to a different corpus or query set without")
print("  its own calibration.")
print("  `[UNVERIFIED -- calibrate this threshold against your own corpus and")
print("  representative queries, the same discipline M6-L11/M7-L05 applied")
print("  to their own threshold parameters.]`")


# ============================================================ 5
rule("5. WHAT A GOOD ABSTENTION MESSAGE LOOKS LIKE")

TERSE_ABSTENTION = "I don't know."
HELPFUL_ABSTENTION = ("I couldn't find information about stock option vesting in the "
                       "documents I have access to (company policies on remote work, "
                       "expenses, PTO, referrals, parental leave, and equipment). This may "
                       "be covered in a different system, or you may want to check with HR "
                       "directly.")

print(f"  `[MOCK -- hand-authored, illustrating the difference, not generated]`\n")
print(f"  Terse:   {TERSE_ABSTENTION!r}")
print(f"  Helpful: {HELPFUL_ABSTENTION!r}")

print("\n  Both are honest -- neither fabricates an answer. But the terse version")
print("  gives a user nowhere to go next: is this a permanently unanswerable")
print("  question, a wrong system to ask, or a temporary gap? The helpful")
print("  version states what WAS searched, which narrows down why it failed,")
print("  and suggests a concrete next step. Abstention done well is still a")
print("  genuinely useful response, not merely the absence of a wrong one.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every BM25 score is M6-L03's exact formula; the confusion")
print("  matrix and threshold sweep are computed directly from those scores")
print("  against the stated ground-truth labels, not scripted to fit.")
print("\n  ILLUSTRATIVE: the answerable/unanswerable ground-truth labels for")
print("  these 6 queries were assigned by hand, based on this lab's own small")
print("  corpus -- a real system needs this labeled 'should the system be")
print("  able to answer this' judgment at meaningfully larger scale (M5-L18's")
print("  evaluation-dataset discipline, applied here). The abstention messages")
print("  in section 5 are hand-authored, not generated by a real model.")
print("\n  NOT SHOWN: combining retrieval-score-based abstention with M7-L12's")
print("  groundedness-based abstention into one combined decision (a natural")
print("  extension, left to the exercises); and abstention decisions made")
print("  AFTER generation (checking groundedness) versus BEFORE it (checking")
print("  retrieval alone, this lab's approach) as two different points in the")
print("  pipeline where the same underlying decision can be made.")

print("\nDone.")
