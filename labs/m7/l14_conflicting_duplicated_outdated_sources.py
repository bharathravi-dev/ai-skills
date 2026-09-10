"""M7-L14 lab -- what happens when retrieval succeeds (M7-L13 correctly
decides to answer) but the retrieved evidence disagrees with itself: real,
measurable conflict detection between two sources on the same topic;
distinguishing GENUINE conflict (two current, legitimate sources that
actually disagree) from FALSE conflict (stale data that M7-L08's own
versioning metadata would have filtered out); three real resolution
strategies for genuine conflict; and a near-duplicate pair that looks like a
safe M7-L05-style dedup candidate but actually disagrees on the underlying
fact.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l14_conflicting_duplicated_outdated_sources.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def shingles(text: str, k: int = 2) -> set[str]:
    # k=2 (not M7-L05's k=3 default): a single differing word corrupts every
    # overlapping shingle that touches it (M7-L05's own k-sensitivity finding).
    # On these short sentences, k=3 over-penalizes a one-word numeric
    # difference; k=2 keeps enough shared shingles to still register these
    # as the same underlying topic.
    words = text.lower().replace(",", "").replace(".", "").split()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


# ============================================================ 1
rule("1. DETECTING CONFLICT: TWO SOURCES, SAME TOPIC, DIFFERENT NUMBERS")

CHUNK_A = {"id": "HR-GLOBAL#1", "source": "Global HR Policy (corporate-wide)",
           "text": "Full-time employees accrue 15 days of PTO per year.", "is_current": True}
CHUNK_B = {"id": "ENG-HANDBOOK#3", "source": "Engineering Team Handbook",
           "text": "Full-time employees accrue 20 days of PTO per year.", "is_current": True}

TOPIC_SHINGLE_THRESHOLD = 0.5


def same_topic(a: dict, b: dict) -> bool:
    return jaccard(shingles(a["text"]), shingles(b["text"])) >= TOPIC_SHINGLE_THRESHOLD


def detect_conflict(a: dict, b: dict) -> tuple[bool, set, set]:
    nums_a, nums_b = extract_numbers(a["text"]), extract_numbers(b["text"])
    disagreement = nums_a.symmetric_difference(nums_b)
    return bool(disagreement) and same_topic(a, b), nums_a, nums_b


print(f"  Chunk A ({CHUNK_A['source']}): {CHUNK_A['text']!r}")
print(f"  Chunk B ({CHUNK_B['source']}): {CHUNK_B['text']!r}\n")
topic_sim = jaccard(shingles(CHUNK_A["text"]), shingles(CHUNK_B["text"]))
conflict, nums_a, nums_b = detect_conflict(CHUNK_A, CHUNK_B)
print(f"  Topic similarity (M7-L05's shingling method): {topic_sim:.3f} "
      f"(>= {TOPIC_SHINGLE_THRESHOLD} -> same topic)")
print(f"  Numbers in A: {sorted(nums_a)}   Numbers in B: {sorted(nums_b)}")
print(f"  Conflict detected: {conflict}")

print("\n  Both chunks are clearly about the SAME fact (same topic, high shingle")
print("  overlap) but assert DIFFERENT numbers -- a real, computable signal")
print("  that something needs resolving before an answer is generated, not")
print("  after the fact.")


# ============================================================ 2
rule("2. FALSE CONFLICT: STALE DATA M7-L08's VERSIONING WOULD HAVE CAUGHT")

CHUNK_C = {"id": "PTO#v1", "source": "PTO Policy v1", "text": "Full-time employees accrue 15 days of PTO per year.",
           "is_current": False, "version": 1}
CHUNK_D = {"id": "PTO#v2", "source": "PTO Policy v2", "text": "Full-time employees accrue 20 days of PTO per year.",
           "is_current": True, "version": 2}

conflict_raw, _, _ = detect_conflict(CHUNK_C, CHUNK_D)
print(f"  Chunk C (v1, is_current={CHUNK_C['is_current']}): {CHUNK_C['text']!r}")
print(f"  Chunk D (v2, is_current={CHUNK_D['is_current']}): {CHUNK_D['text']!r}")
print(f"\n  Raw conflict detection (ignoring version metadata): {conflict_raw}")

current_only = [c for c in (CHUNK_C, CHUNK_D) if c["is_current"]]
print(f"  After filtering to is_current=True (M7-L08's own fix): "
      f"{[c['id'] for c in current_only]} remain -- {len(current_only)} source, no conflict possible.")

print("\n  This LOOKS like section 1's problem -- two sources, same topic,")
print("  different numbers -- but it isn't genuine conflict at all. It's a")
print("  single fact that CHANGED over time, retrievable as two versions")
print("  only because M7-L08's currency filtering wasn't applied. The fix here")
print("  is M7-L08's, not a new mechanism: filter to current sources FIRST,")
print("  and this specific 'conflict' disappears entirely.")


# ============================================================ 3
rule("3. GENUINE CONFLICT: BOTH SOURCES ARE CURRENT, AND THEY STILL DISAGREE")

print(f"  Back to section 1's Chunk A and Chunk B: both marked is_current=True.")
print(f"  Chunk A is_current: {CHUNK_A['is_current']}   Chunk B is_current: {CHUNK_B['is_current']}")
both_current = CHUNK_A["is_current"] and CHUNK_B["is_current"]
print(f"  Both current simultaneously: {both_current}")

print("\n  Filtering to 'current only' (section 2's fix) does NOTHING here --")
print("  both sources already pass that filter. This is not stale data hiding")
print("  behind missing version metadata; it is two legitimately different,")
print("  simultaneously valid documents that genuinely disagree -- a company-")
print("  wide policy and a team-specific handbook, neither one wrong by")
print("  virtue of being older. Versioning (M7-L08) cannot resolve this,")
print("  because there is no 'older' version here to discard.")


# ============================================================ 4
rule("4. THREE RESOLUTION STRATEGIES FOR GENUINE CONFLICT, COMPARED")


def resolve_transparent(a: dict, b: dict) -> str:
    return (f"Sources disagree: {a['source']} states {sorted(extract_numbers(a['text']))[0]} days, "
            f"while {b['source']} states {sorted(extract_numbers(b['text']))[0]} days. "
            f"Please confirm which applies to your situation.")


AUTHORITY_RANK = {"Global HR Policy (corporate-wide)": 1, "Engineering Team Handbook": 2}


def resolve_by_authority(a: dict, b: dict) -> str:
    winner = a if AUTHORITY_RANK[a["source"]] < AUTHORITY_RANK[b["source"]] else b
    return f"{winner['text']} (Source: {winner['source']} -- takes precedence per corporate policy hierarchy)"


def resolve_by_abstention(a: dict, b: dict) -> str:
    return ("I found conflicting information from two current sources "
            f"({a['source']} and {b['source']}) and can't confidently resolve which applies. "
            "Flagging for human review rather than guessing.")


print("  STRATEGY 1 -- transparent, surface both:")
print(f"    {resolve_transparent(CHUNK_A, CHUNK_B)!r}")
print("\n  STRATEGY 2 -- prefer by a real authority rule (corporate policy")
print("  outranks a team handbook, a genuine, if domain-specific, business rule):")
print(f"    {resolve_by_authority(CHUNK_A, CHUNK_B)!r}")
print("\n  STRATEGY 3 -- abstain and escalate (M7-L13's mechanism, triggered by")
print("  conflict rather than low retrieval score):")
print(f"    {resolve_by_abstention(CHUNK_A, CHUNK_B)!r}")

print("\n  None of these is universally correct. Strategy 1 is honest but pushes")
print("  the decision back to the user. Strategy 2 is decisive but REQUIRES a")
print("  real, trustworthy authority signal to exist -- guessing one would be")
print("  worse than not resolving at all. Strategy 3 is safest when no")
print("  authority signal exists and the disagreement matters enough that a")
print("  wrong guess would be costly -- the same asymmetry M7-L13 measured for")
print("  abstention generally, applied here to a conflict-triggered case.")


# ============================================================ 5
rule("5. NEAR-DUPLICATES THAT AREN'T ACTUALLY DUPLICATES")

CHUNK_E = {"id": "PTO-mirror#1", "source": "HR Mirror Site",
           "text": "Full time staff accrue 15 days of PTO each year.", "is_current": True}
CHUNK_F = {"id": "PTO-mirror#2", "source": "HR Archive Copy",
           "text": "Full time staff accrue 18 days of PTO each year.", "is_current": True}

sim_ef = jaccard(shingles(CHUNK_E["text"]), shingles(CHUNK_F["text"]))
print(f"  Chunk E ({CHUNK_E['source']}): {CHUNK_E['text']!r}")
print(f"  Chunk F ({CHUNK_F['source']}): {CHUNK_F['text']!r}")
print(f"\n  Text similarity (M7-L05/M7-L11's shingling method): {sim_ef:.3f}")

DEDUP_THRESHOLD = 0.5
would_dedup = sim_ef >= DEDUP_THRESHOLD
print(f"  Would a naive dedup step (threshold {DEDUP_THRESHOLD}) collapse these into one, "
      f"keeping only the first? {would_dedup}")

nums_e, nums_f = extract_numbers(CHUNK_E["text"]), extract_numbers(CHUNK_F["text"])
print(f"\n  But the actual NUMBERS differ: {sorted(nums_e)} vs {sorted(nums_f)} -- these are")
print("  not really duplicates, they are two DIFFERENT claims that happen to")
print("  be worded almost identically. A dedup step (M7-L05, M7-L11) that only")
print("  checks textual similarity would silently discard one of two genuinely")
print("  conflicting numbers, hiding a real disagreement behind what LOOKS")
print("  like harmless redundancy. Deduplication needs a fact-agreement check")
print("  (this section's number-extraction, or section 1's conflict detector)")
print("  BEFORE collapsing near-duplicates, not just a wording-similarity check.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: shingle-based topic similarity (M7-L05's mechanism -- word")
print("  shingles plus Jaccard similarity -- at k=2 rather than M7-L05's own")
print("  k=3 default, chosen per M7-L05's own k-sensitivity finding: these")
print("  short sentences differ in only one word, which k=3 over-penalizes);")
print("  number extraction (M7-L12's exact method); and every conflict/dedup")
print("  determination in this lab are genuinely computed from the stated")
print("  chunk text, not scripted to fit the narrative.")
print("\n  ILLUSTRATIVE: the specific chunks, sources, and authority ranking")
print("  (corporate policy over team handbook) are hand-authored for this")
print("  lesson -- a real system's authority hierarchy is domain-specific and")
print("  must be deliberately designed, not assumed.")
print("\n  NOT SHOWN: automatically inferring an authority hierarchy from")
print("  metadata alone (a hard, general problem); combining conflict")
print("  detection with M7-L13's abstention decision into one unified")
print("  pipeline stage; and detecting conflicts that don't involve numbers")
print("  (contradictory qualitative statements), which needs a more general")
print("  method than number extraction.")

print("\nDone.")
