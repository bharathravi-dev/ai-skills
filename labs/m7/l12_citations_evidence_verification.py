"""M7-L12 lab -- verifying that a generated answer's citations are real
(pointing to something actually retrieved) AND grounded (the cited text
actually supports the specific claim made), as two distinct, both-necessary
checks: a citation can be real but the claim built on it still wrong, and a
real, computable numeric-groundedness check catches exactly this class of
error, including a partially-grounded claim that mixes a real fact with a
fabricated detail.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l12_citations_evidence_verification.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# The assembled, retrieved context (M7-L11's output) -- this is what was
# ACTUALLY handed to generation. Nothing outside this set was ever retrieved.
RETRIEVED_CONTEXT = {
    "P3": "Full time employees accrue 15 days of PTO per year, increasing to 20 days after 3 years of service.",
    "P5": "Employees are eligible for 12 weeks of paid parental leave, available after 6 months of tenure.",
}


# ============================================================ 1
rule("1. A CITATION CONNECTS A CLAIM TO A SPECIFIC RETRIEVED SOURCE")

EXAMPLE_ANSWER = "Full-time employees get 20 days of PTO after 3 years of service. [Source: P3]"
print(f"  Retrieved context available to generation: {list(RETRIEVED_CONTEXT.keys())}")
print(f"  Generated answer: {EXAMPLE_ANSWER!r}\n")
print("  A citation like '[Source: P3]' is a claim about PROVENANCE (M7-L08):")
print("  'this specific statement comes from this specific retrieved chunk.'")
print("  That claim can be checked two entirely different ways, covered next:")
print("  does P3 actually exist in what was retrieved (section 2), and does")
print("  P3's actual text actually support what was just said (section 3)?")


# ============================================================ 2
rule("2. CHECK 1 -- DOES THE CITED SOURCE EXIST IN THE RETRIEVED SET AT ALL?")


def extract_citations(answer: str) -> list[str]:
    return re.findall(r"\[Source:\s*([^\]]+)\]", answer)


def check_citation_exists(citation_id: str, retrieved: dict) -> bool:
    return citation_id in retrieved


REAL_CITATION_ANSWER = "Employees get 20 days of PTO after 3 years. [Source: P3]"
FAKE_CITATION_ANSWER = "Employees get free gym membership after 1 year. [Source: P9]"

for answer in (REAL_CITATION_ANSWER, FAKE_CITATION_ANSWER):
    cited = extract_citations(answer)
    print(f"  Answer: {answer!r}")
    for cid in cited:
        exists = check_citation_exists(cid, RETRIEVED_CONTEXT)
        print(f"    Cites {cid!r} -- exists in retrieved context: {exists}")
    print()

print("  P9 was never retrieved at all (it isn't in RETRIEVED_CONTEXT) -- a")
print("  citation to it is fabricated at the CITATION level, regardless of")
print("  whether the claim next to it happens to be true. This is the cheaper,")
print("  simpler of the two checks: does the cited ID correspond to anything")
print("  real that was actually handed to the model.")


# ============================================================ 3
rule("3. CHECK 2 -- DOES THE CITED TEXT ACTUALLY SUPPORT THE CLAIM?")


def extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def groundedness_score(claim: str, source_text: str) -> tuple[float, set[str], set[str]]:
    """[REAL mechanism, deliberately NARROW scope] Checks whether every
    number asserted in the claim actually appears in the cited source text.
    A real production groundedness check typically uses a trained NLI model
    over the full claim, not just its numbers -- this is a genuine, checkable
    instance of the same principle, intentionally narrowed to something
    exactly verifiable by hand."""
    claim_numbers = extract_numbers(claim)
    source_numbers = extract_numbers(source_text)
    if not claim_numbers:
        return 1.0, claim_numbers, source_numbers
    supported = claim_numbers & source_numbers
    return len(supported) / len(claim_numbers), claim_numbers, source_numbers


CLAIM_GROUNDED = "Full-time employees get 20 days of PTO after 3 years of service."
CLAIM_UNGROUNDED = "Full-time employees get 25 days of PTO after 3 years of service."

for claim in (CLAIM_GROUNDED, CLAIM_UNGROUNDED):
    score, claim_nums, source_nums = groundedness_score(claim, RETRIEVED_CONTEXT["P3"])
    print(f"  Claim: {claim!r}")
    print(f"    Numbers asserted in claim: {sorted(claim_nums)}")
    print(f"    Numbers present in cited source (P3): {sorted(source_nums)}")
    print(f"    Groundedness score: {score:.2f}")
    print(f"    Citation exists (P3 is real): True -- but is the CLAIM correct? "
          f"{'YES' if score == 1.0 else 'NO -- unsupported by the cited text'}\n")

print("  Both claims cite a REAL, retrieved source (P3 exists, section 2's")
print("  check would pass for both). Only the groundedness check catches the")
print("  second claim's fabricated '25' -- the source says 20, not 25. A")
print("  citation existing is necessary but NOT sufficient for a claim to be")
print("  trustworthy; this is the specific gap groundedness checking closes.")


# ============================================================ 4
rule("4. A PARTIALLY GROUNDED CLAIM: REAL FACT MIXED WITH A FABRICATED DETAIL")

CLAIM_PARTIAL = ("Full-time employees get 20 days of PTO after 3 years of service, "
                  "increasing further to 25 days after 5 years.")
score, claim_nums, source_nums = groundedness_score(CLAIM_PARTIAL, RETRIEVED_CONTEXT["P3"])
print(f"  Claim: {CLAIM_PARTIAL!r}")
print(f"    Numbers asserted in claim: {sorted(claim_nums)}")
print(f"    Numbers present in cited source (P3): {sorted(source_nums)}")
print(f"    Groundedness score: {score:.2f}  ({len(claim_nums & source_nums)} of "
      f"{len(claim_nums)} claimed numbers actually supported)")

print("\n  '20' and '3' are genuinely in the source; '25' and '5' are NOT -- P3")
print("  says nothing about a further increase at 5 years at all. A pure pass/")
print("  fail check would have to call this claim either entirely right or")
print("  entirely wrong, neither of which is accurate. A PARTIAL score (0.50")
print("  here) correctly flags this as a claim worth reviewing, not a clean")
print("  pass -- exactly the kind of subtly fabricated addition a fluent,")
print("  otherwise-accurate-sounding answer can smuggle in.")


# ============================================================ 5
rule("5. WHAT REAL PRODUCTION GROUNDEDNESS CHECKING ACTUALLY LOOKS LIKE")

print("  `[CONCEPTUAL]` This lab's groundedness check is deliberately narrow:")
print("  it verifies only NUMBERS, because a number either appears in the")
print("  source or it does not -- a fact simple enough to check by hand and")
print("  trust completely. Real production groundedness checking typically")
print("  uses a separate model call (often framed as natural language")
print("  inference: 'does this source text ENTAIL this claim?') to catch")
print("  fabricated or unsupported claims of ANY kind, not just wrong numbers")
print("  -- invented names, incorrect relationships between real facts, or")
print("  claims that are directionally wrong without changing any number at")
print("  all. `[UNVERIFIED -- specific NLI-based groundedness tools and their")
print("  accuracy change quickly; confirm current best practice before")
print("  relying on any specific one.]`")
print("\n  The MECHANISM this lab demonstrates -- checking a specific,")
print("  verifiable claim against the specific cited source text, rather than")
print("  trusting that a citation existing means the claim is correct -- is")
print("  real and load-bearing, even though the CHECK ITSELF here is")
print("  narrower than a full production system's.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: citation extraction, citation-existence checking, and the")
print("  numeric groundedness score are all genuinely computed on the stated")
print("  text, not scripted -- the ungrounded and partially-grounded examples")
print("  fail their checks because the numbers genuinely are or are not in")
print("  the source text, checkable by hand.")
print("\n  MOCK / ILLUSTRATIVE: the example answers and claims in this lab are")
print("  hand-authored, standing in for real LLM-generated output -- no real")
print("  model call was made, consistent with this course's offline-first")
print("  design. The groundedness check itself is intentionally narrowed to")
print("  numbers only, a real but partial instance of the broader NLI-style")
print("  checking a production system would use.")
print("\n  NOT SHOWN: checking non-numeric claims (names, relationships,")
print("  qualitative statements) for groundedness, which needs a more general")
print("  method than number-matching; and what a system should DO once an")
print("  ungrounded or partially-grounded claim is detected -- abstaining or")
print("  flagging the answer, which is M7-L13's dedicated topic next.")

print("\nDone.")
