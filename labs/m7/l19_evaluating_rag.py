"""M7-L19 lab -- evaluating a RAG system requires separating retrieval
quality (M6-L13's metrics) from answer quality, and answer quality itself
splits into three genuinely independent axes: groundedness (M7-L12 -- is the
claim supported by its cited source?), correctness (does the claim match
real-world ground truth, independent of what any source says?), and
completeness (does the answer cover everything a multi-part question asked?
M7-L09). Four real, hand-authored answers to the same compound question are
scored on all three axes, demonstrating that they diverge in both directions
-- including the genuinely dangerous case of an ungrounded but correct claim.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l19_evaluating_rag.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def extract_numbers(text: str) -> set[str]:
    """[REAL] Numbers from the CLAIM's own content only -- a citation marker
    like '[Source: P3, P4]' is provenance metadata, not an asserted fact, and
    must be stripped first so a document ID's digit (e.g. the '4' in 'P4')
    is never mistaken for a number the claim is actually stating."""
    content_only = re.sub(r"\[Source:[^\]]*\]", "", text)
    return set(re.findall(r"\d+", content_only))


# ============================================================ 1
rule("1. RETRIEVAL EVALUATION IS NOT ANSWER EVALUATION")

RETRIEVED_CONTEXT = {
    "P3": "Full time employees accrue 15 days of PTO per year, increasing to 20 days after 3 years of service.",
    "P4": "Referral bonuses are 2000 dollars, paid after 90 days of the new hire's employment.",
}

print("  Retrieval for this lesson's query found exactly the two right chunks")
print("  (P3 for PTO, P4 for referral bonus) -- by M6-L13's own metrics, this")
print("  retrieval could score a PERFECT Precision@2, Recall@2, and nDCG@2.")
print("  None of that guarantees the GENERATED ANSWER built from these chunks")
print("  is itself correct, complete, or even actually grounded in them --")
print("  retrieval quality and answer quality are measured by ENTIRELY")
print("  different checks, on entirely different objects (a ranked list of")
print("  chunk IDs, versus a generated string of text).")


# ============================================================ 2
rule("2. GROUNDEDNESS VS. CORRECTNESS: NOT THE SAME AXIS")

# Ground truth: the REAL, currently correct answer, verified independently of
# what any retrieved document says (e.g. confirmed directly with HR).
GROUND_TRUTH_NUMBERS = {"15", "25", "2000"}   # senior PTO was updated to 25 last month

ANSWER_STALE = "Senior employees (3+ years) get 20 days of PTO. [Source: P3]"


def groundedness_score(claim: str, source_text: str) -> float:
    """[REAL, M7-L12's exact mechanism] Does the cited source's text support
    the claim's numbers?"""
    claim_numbers = extract_numbers(claim)
    if not claim_numbers:
        return 1.0
    source_numbers = extract_numbers(source_text)
    return len(claim_numbers & source_numbers) / len(claim_numbers)


def correctness_score(claim: str, ground_truth: set[str]) -> float:
    """[REAL] Does the claim's numbers match REAL-WORLD ground truth --
    independent of what any retrieved document says."""
    claim_numbers = extract_numbers(claim)
    if not claim_numbers:
        return 1.0
    return len(claim_numbers & ground_truth) / len(claim_numbers)


grounded = groundedness_score(ANSWER_STALE, RETRIEVED_CONTEXT["P3"])
correct = correctness_score(ANSWER_STALE, GROUND_TRUTH_NUMBERS)

print(f"  Claim: {ANSWER_STALE!r}")
print(f"  Cited source (P3): {RETRIEVED_CONTEXT['P3']!r}")
print(f"  Real-world ground truth (verified independently): senior PTO is "
      f"actually 25 days now, updated last month.\n")
print(f"  Groundedness (does the CITED SOURCE support this claim?): {grounded:.2f}")
print(f"  Correctness (does the claim match REAL-WORLD truth?): {correct:.2f}")

print("\n  This claim is FULLY grounded -- P3 really does say '20 days,' so the")
print("  citation is completely honest about what the source contains. It is")
print("  simultaneously INCORRECT, because the source itself is stale (M7-L16's")
print("  propagation problem: the real policy changed, but this chunk was")
print("  never re-indexed). Groundedness measures faithfulness to the SOURCE;")
print("  correctness measures faithfulness to REALITY. A perfectly grounded")
print("  answer can still be wrong if the evidence it was grounded in is wrong.")


# ============================================================ 3
rule("3. THE DANGEROUS CASE: UNGROUNDED BUT CORRECT")

ANSWER_UNGROUNDED = "The referral bonus is 2000 dollars. [Source: P3]"

grounded_2 = groundedness_score(ANSWER_UNGROUNDED, RETRIEVED_CONTEXT["P3"])
correct_2 = correctness_score(ANSWER_UNGROUNDED, GROUND_TRUTH_NUMBERS)

print(f"  Claim: {ANSWER_UNGROUNDED!r}")
print(f"  Cited source (P3): {RETRIEVED_CONTEXT['P3']!r}  (says nothing about referral bonuses at all)")
print(f"\n  Groundedness: {grounded_2:.2f}")
print(f"  Correctness: {correct_2:.2f}")

print("\n  The number '2000' happens to be the REAL, correct referral bonus --")
print("  but the CITED source (P3) is about PTO and never mentions it. This")
print("  claim is CORRECT and UNGROUNDED simultaneously -- a genuinely")
print("  dangerous combination, because a fact-check that only asks 'is this")
print("  number right' would pass it, while the citation itself is fabricated")
print("  or misattributed. A user clicking through to 'verify' this citation")
print("  would find a document that says nothing about what was just claimed.")
print("  Checking correctness ALONE, without groundedness, misses this entirely.")


# ============================================================ 4
rule("4. COMPLETENESS: DID THE ANSWER COVER WHAT WAS ASKED?")

COMPOUND_QUESTION = "How many PTO days do junior and senior employees get, and what is the referral bonus?"
SUB_TOPICS = {
    "junior PTO": ["junior", "15"],
    "senior PTO": ["senior", "20", "25"],
    "referral bonus": ["referral", "bonus", "2000"],
}

ANSWER_PARTIAL = "Junior employees get 15 days of PTO. [Source: P3]"


def completeness_score(answer: str, sub_topics: dict[str, list[str]]) -> tuple[float, list[str]]:
    """[REAL] For each sub-topic of a decomposed compound question (M7-L09),
    check whether the answer addresses it at all (any of its keywords
    present). This checks COVERAGE, not correctness or groundedness.
    Keywords are matched on WORD boundaries -- a short numeric keyword like
    '20' must not spuriously match inside an unrelated longer number like
    '2000' in the answer text."""
    answer_lower = answer.lower()
    covered = [topic for topic, keywords in sub_topics.items()
               if any(re.search(rf"\b{re.escape(kw)}\b", answer_lower) for kw in keywords)]
    return len(covered) / len(sub_topics), covered


score, covered = completeness_score(ANSWER_PARTIAL, SUB_TOPICS)
missing = [t for t in SUB_TOPICS if t not in covered]

print(f"  Compound question: {COMPOUND_QUESTION!r}")
print(f"  Answer: {ANSWER_PARTIAL!r}\n")
print(f"  Sub-topics covered: {covered}")
print(f"  Sub-topics MISSING: {missing}")
print(f"  Completeness score: {score:.2f}")

print("\n  This answer is fully grounded (P3 really does say 15 days) and fully")
print("  correct (15 IS the real junior PTO figure) -- and still only")
print("  ONE-THIRD complete, because two of the three things the compound")
print("  question actually asked about (senior PTO, referral bonus) are")
print("  simply never addressed. A grounded, correct, INCOMPLETE answer can")
print("  still leave a user with a materially wrong impression of what they")
print("  asked -- exactly the compound-question risk M7-L09 introduced from")
print("  the retrieval side, now measured from the answer side.")


# ============================================================ 5
rule("5. ALL THREE AXES, ON FOUR REAL ANSWERS")

ANSWER_GOOD = ("Junior employees get 15 days of PTO, senior employees (3+ years) get "
               "20 days, and the referral bonus is 2000 dollars. [Source: P3, P4]")

ANSWERS = {
    "Grounded, complete, PARTLY stale": (ANSWER_GOOD, RETRIEVED_CONTEXT["P3"] + " " + RETRIEVED_CONTEXT["P4"]),
    "Grounded, INCORRECT (stale ground truth)": (ANSWER_STALE, RETRIEVED_CONTEXT["P3"]),
    "UNGROUNDED, correct": (ANSWER_UNGROUNDED, RETRIEVED_CONTEXT["P3"]),
    "Grounded, correct, INCOMPLETE": (ANSWER_PARTIAL, RETRIEVED_CONTEXT["P3"]),
}

print(f"  {'Label':<42}{'Grounded':>10}{'Correct':>10}{'Complete':>10}")
for label, (answer, source) in ANSWERS.items():
    g = groundedness_score(answer, source)
    c = correctness_score(answer, GROUND_TRUTH_NUMBERS)
    comp, _ = completeness_score(answer, SUB_TOPICS)
    print(f"  {label:<42}{g:>10.2f}{c:>10.2f}{comp:>10.2f}")

print("\n  Notice the first row is not a clean 1.00/1.00/1.00 baseline, and that")
print("  is itself a real, honest finding, not a loose end: this answer covers")
print("  all three sub-topics and is fully grounded in what was retrieved, but")
print("  its correctness is only 0.50, because it repeats the SAME stale")
print("  senior-PTO figure section 2 already found (20, not the real 25) --")
print("  it inherited that error simply by citing the same imperfect source.")
print("  Completeness and groundedness are real, worth measuring, and NEITHER")
print("  one protects against a correctness problem sitting upstream in the")
print("  index itself.")

print("\n  No two of these four answers share the same three scores. A single")
print("  blended 'quality score' would collapse genuinely different failure")
print("  types into one number -- an ungrounded-but-correct answer and a")
print("  grounded-but-incorrect answer are both 'wrong' in SOME sense, but")
print("  wrong for completely different reasons, needing completely different")
print("  fixes (M7-L16's propagation discipline for the stale case; citation")
print("  verification for the ungrounded case; decomposition, M7-L09, for the")
print("  incomplete case). Measuring all three separately is what makes each")
print("  fix identifiable at all.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every groundedness, correctness, and completeness score in")
print("  this lab is genuinely computed from the stated claims, sources, and")
print("  ground-truth values -- the divergence between axes (section 2's")
print("  grounded-but-wrong case, section 3's ungrounded-but-right case) is a")
print("  real, measured result of these independent checks, not asserted.")
print("\n  ILLUSTRATIVE: the four example answers are hand-authored, standing")
print("  in for real generated output -- no real model call was made,")
print("  consistent with this course's offline-first design. The correctness")
print("  and completeness checks are narrowed to number/keyword presence, the")
print("  same deliberate simplification M7-L12 used for groundedness.")
print("\n  NOT SHOWN: retrieval-side metrics themselves (M6-L13 already covers")
print("  Precision@k, Recall@k, MRR, and nDCG in depth); building a real")
print("  evaluation dataset with human-verified ground truth (M5-L18's")
print("  topic); and combining all of Module 7's evaluation signals into one")
print("  dashboard, a natural extension left to the exercises.")

print("\nDone.")
