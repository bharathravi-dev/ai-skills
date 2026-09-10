"""M7-L05 lab -- cleaning, normalization, and deduplication: a real Unicode
normalization-form bug where two strings that render identically are not
equal as data, real whitespace collapsing, corpus-wide exact deduplication
via content hashing (M7-L03, applied at corpus scale), real near-duplicate
detection via k-shingling and Jaccard similarity, and a measured demonstration
of what duplicate content actually costs a retrieval result set.

Deterministic. No API key, no network, no third-party dependencies --
everything here is Python's standard library.
Run:  python labs/m7/l05_cleaning_dedup.py
"""

from __future__ import annotations

import hashlib
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. UNICODE NORMALIZATION: LOOKS IDENTICAL, ISN'T EQUAL AS DATA")

# The SAME visible word "café", built two genuinely different ways:
# composed (a single U+00E9 code point) vs decomposed (e + combining acute).
composed = "café"                 # 'é' as ONE code point
decomposed = "café"              # 'e' + U+0301 COMBINING ACUTE ACCENT

print(f"  composed:   {composed!r}  (length {len(composed)})")
print(f"  decomposed: {decomposed!r}  (length {len(decomposed)})")
print(f"  They print identically: {composed == decomposed and 'YES' or 'they DO look the same above'}")
print(f"  They are equal as Python strings: {composed == decomposed}")

nfc_composed, nfc_decomposed = unicodedata.normalize("NFC", composed), unicodedata.normalize("NFC", decomposed)
print(f"\n  After normalizing BOTH to NFC (composed form):")
print(f"    composed   -> {nfc_composed!r} (length {len(nfc_composed)})")
print(f"    decomposed -> {nfc_decomposed!r} (length {len(nfc_decomposed)})")
print(f"    Now equal: {nfc_composed == nfc_decomposed}")

print("\n  Two documents ingested from different sources (different export")
print("  tools, different operating systems) can contain the SAME visible")
print("  text encoded with different Unicode normalization forms. A content-")
print("  hash-based dedup check (M7-L03) run WITHOUT normalizing first would")
print("  compute two DIFFERENT hashes for genuinely identical-looking content")
print("  -- a silent deduplication failure with the same shape as M7-L03's")
print("  encoding bug: nothing crashes, the duplicate simply isn't caught.")


# ============================================================ 2
rule("2. WHITESPACE NORMALIZATION")

MESSY_TEXT = "Remote  work   requires\n\nmanager  approval.\t\tSubmit  the  form."


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


cleaned = normalize_whitespace(MESSY_TEXT)
print(f"  Raw (extraction artifact -- irregular spaces, tabs, blank lines):")
print(f"    {MESSY_TEXT!r}")
print(f"  Normalized:")
print(f"    {cleaned!r}")
print(f"\n  {len(MESSY_TEXT)} characters -> {len(cleaned)} characters. This kind of")
print("  irregular whitespace is a routine, unremarkable side effect of PDF and")
print("  HTML extraction (M7-L04) -- collapsing it is cheap and removes noise")
print("  that would otherwise inflate token counts and dilute embeddings with")
print("  meaningless variation.")


# ============================================================ 3
rule("3. EXACT DEDUPLICATION ACROSS A CORPUS, VIA CONTENT HASH")

CORPUS = {
    "src_a/policy.txt": "Employees may work remotely up to three days per week with manager approval.",
    "src_b/mirror_policy.txt": "Employees may work remotely up to three days per week with manager approval.",
    "src_a/expenses.txt": "Expense reports must be submitted within thirty days of purchase.",
    "src_c/policy_export.txt": "Employees may work remotely up to three days per week with manager approval.",
    "src_a/pto.txt": "Full time employees accrue fifteen days of PTO per year.",
}


def content_hash(text: str) -> str:
    normalized = unicodedata.normalize("NFC", " ".join(text.split()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


seen: dict[str, str] = {}
unique, exact_duplicates = [], []
for source, text in CORPUS.items():
    h = content_hash(text)
    if h in seen:
        exact_duplicates.append((source, seen[h]))
    else:
        seen[h] = source
        unique.append(source)

print(f"  {len(CORPUS)} documents ingested from {len(set(s.split('/')[0] for s in CORPUS))} different sources.\n")
print(f"  Unique (by content hash): {unique}")
print(f"  Exact duplicates found: {exact_duplicates}")
print(f"\n  Two of three copies of the SAME remote-work policy text (scraped or")
print("  exported from three different source locations) collapse to one")
print("  unique document once hashed -- exactly M7-L03's identity mechanism,")
print("  now applied across an entire corpus rather than one file's history.")


# ============================================================ 4
rule("4. NEAR-DUPLICATES: WHAT EXACT HASHING MISSES")

DOC_A = ("Employees may work remotely up to three days per week with manager "
         "approval. Fully remote arrangements require VP approval and a signed "
         "remote work agreement.")
DOC_B = ("Employees may work remotely up to three days each week with manager "
         "approval. Fully remote arrangements require VP sign-off and a signed "
         "remote work agreement.")   # same policy, lightly reworded
DOC_C = ("Expense reports must be submitted within thirty days of purchase. "
         "Reimbursements over five hundred dollars require director approval.")

print(f"  Doc A hash: {content_hash(DOC_A)}")
print(f"  Doc B hash: {content_hash(DOC_B)}  (a lightly reworded copy of A)")
print(f"  Exact hash match A vs B: {content_hash(DOC_A) == content_hash(DOC_B)}")
print("\n  A and B are the same policy, reworded in two small places -- exact")
print("  content hashing correctly reports them as DIFFERENT, because they are,")
print("  byte for byte. But they are near-duplicates in a way that still")
print("  matters for a retrieval corpus, and exact hashing has no way to see it.")


def shingles(text: str, k: int) -> set[str]:
    words = text.lower().split()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


word_diffs = sum(1 for x, y in zip(DOC_A.lower().split(), DOC_B.lower().split()) if x != y)
print(f"\n  A and B differ in exactly {word_diffs} words out of "
      f"{len(DOC_A.split())} -- a genuinely light edit.")

K = 3
shingles_a, shingles_b, shingles_c = shingles(DOC_A, K), shingles(DOC_B, K), shingles(DOC_C, K)
sim_ab = jaccard(shingles_a, shingles_b)
sim_ac = jaccard(shingles_a, shingles_c)

print(f"\n  {K}-word shingle sets: |A|={len(shingles_a)}, |B|={len(shingles_b)}, |C|={len(shingles_c)}")
print(f"  Jaccard(A, B) = {sim_ab:.3f}  (A vs its lightly reworded near-duplicate)")
print(f"  Jaccard(A, C) = {sim_ac:.3f}  (A vs a genuinely different policy)")

NEAR_DUP_THRESHOLD = 0.5
print(f"\n  At a threshold of {NEAR_DUP_THRESHOLD}: A/B "
      f"{'ARE' if sim_ab >= NEAR_DUP_THRESHOLD else 'are NOT'} flagged as near-duplicates; "
      f"A/C {'ARE' if sim_ac >= NEAR_DUP_THRESHOLD else 'are NOT'}.")
print("\n  Shingling breaks text into overlapping k-word windows and measures")
print("  set overlap -- two documents sharing most of their wording, even with")
print("  a few words changed, share most of their shingles too. This is what")
print("  catches near-duplicates exact hashing (section 3) cannot.")

print(f"\n  Shingle size k is a real, sensitive parameter, not an arbitrary")
print(f"  detail -- each single word edit corrupts every overlapping shingle")
print(f"  that touches it, so LARGER k amplifies the same small edit into a")
print(f"  bigger apparent difference:")
for k in (3, 4, 5):
    sa, sb = shingles(DOC_A, k), shingles(DOC_B, k)
    print(f"    k={k}: Jaccard(A, B) = {jaccard(sa, sb):.3f}")
print(f"\n  The SAME 2-word edit drives Jaccard(A, B) from "
      f"{jaccard(shingles(DOC_A, 3), shingles(DOC_B, 3)):.3f} at k=3 down to "
      f"{jaccard(shingles(DOC_A, 5), shingles(DOC_B, 5)):.3f} at k=5 -- crossing this")
print(f"  lab's {NEAR_DUP_THRESHOLD} threshold from 'flagged' to 'missed' depending")
print("  purely on k. `[UNVERIFIED -- calibrate both k and the threshold against")
print("  your own corpus and edit patterns before relying on either value.]`")


# ============================================================ 5
rule("5. WHAT DUPLICATE CONTENT ACTUALLY COSTS A RETRIEVAL RESULT SET")

RETRIEVAL_CORPUS = {
    "policy_v1": DOC_A, "policy_mirror": DOC_A, "policy_export": DOC_A,
    "policy_reworded": DOC_B, "expenses": DOC_C,
    "pto": "Full time employees accrue fifteen days of PTO per year, more after three years.",
}


def word_overlap_score(query_words: set, doc: str) -> float:
    doc_words = set(doc.lower().split())
    return len(query_words & doc_words) / len(query_words) if query_words else 0.0


query_words = set("remote work manager approval".split())
scored = {name: word_overlap_score(query_words, text) for name, text in RETRIEVAL_CORPUS.items()}
top_3 = sorted(scored, key=lambda n: -scored[n])[:3]

print(f"  Query concept: 'remote work manager approval'")
print(f"  Top-3 by simple overlap score, BEFORE deduplication: {top_3}")
for name in top_3:
    print(f"    {name}: score {scored[name]:.2f}")

deduped_names = ["policy_v1", "policy_reworded", "expenses", "pto"]  # one copy of the near-dup cluster kept
deduped_scored = {n: scored[n] for n in deduped_names}
top_3_deduped = sorted(deduped_scored, key=lambda n: -deduped_scored[n])[:3]
print(f"\n  Top-3 AFTER deduplication (near-duplicate cluster collapsed to one "
      f"representative): {top_3_deduped}")

print("\n  Before deduplication, the top 3 results are three near-identical")
print("  copies of the SAME policy -- a user gets no new information from")
print("  results 2 and 3, and a genuinely different, potentially more relevant")
print("  document (PTO policy) is crowded out of the top-3 entirely by")
print("  redundant copies of one document. Deduplication doesn't just save")
print("  storage -- it directly affects which distinct information a user")
print("  actually sees.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: the Unicode composed/decomposed inequality and its NFC fix are")
print("  exact, standard-library behavior; whitespace collapsing, content")
print("  hashing, shingling, and Jaccard similarity are all computed exactly")
print("  as coded, on real (if synthetic) text.")
print("\n  ILLUSTRATIVE: section 5's 'retrieval' is a simple word-overlap score,")
print("  not a real embedding or BM25 ranking (M6-L01/M6-L03) -- chosen to keep")
print("  the deduplication-crowding effect easy to verify by hand; the")
print("  underlying point (duplicates crowd out distinct results) holds")
print("  regardless of which real scoring method is used.")
print("\n  NOT SHOWN: locality-sensitive hashing (LSH) or MinHash for near-")
print("  duplicate detection at real corpus scale, where computing exact")
print("  pairwise Jaccard similarity (this lab's approach) becomes too slow --")
print("  a natural next step left to the exercises.")

print("\nDone.")
