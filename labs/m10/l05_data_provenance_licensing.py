"""M10-L05 lab -- where the material came from, and what you are permitted to do
with it, follow the data all the way into an answer. This lab tracks a 12-source
corpus and measures:

  1. permitted use: how much of the corpus may be used for a commercial product,
  2. propagation: licence restrictions surviving into chunks, retrieval and answers,
  3. attribution: required credits that the answer template drops,
  4. use classes: sources fine for retrieval that are not permitted for training,
  5. derived data: how 'unknown provenance' taints everything downstream.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l05_data_provenance_licensing.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass(frozen=True)
class Source:
    id: str
    origin: str
    licence: str
    internal_use: bool
    commercial_use: bool
    redistribute_verbatim: bool
    train_on: bool
    attribution: str | None


CORPUS = [
    Source("S01", "our own product docs", "company-owned", True, True, True, True, None),
    Source("S02", "supplier manual (contract)", "supplier contract, internal only", True, False, False, False, None),
    Source("S03", "public standard (paid)", "standards body licence, 3 named readers", True, False, False, False, "BS EN 1234"),
    Source("S04", "open-source project README", "Apache-2.0", True, True, True, True, "Apache-2.0 notice"),
    Source("S05", "open-source docs", "CC BY-SA 4.0", True, True, True, True, "author + share-alike"),
    Source("S06", "news article", "all rights reserved", True, False, False, False, None),
    Source("S07", "scraped forum posts", "unknown", False, False, False, False, None),
    Source("S08", "customer support transcripts", "customer contract: service delivery only", True, True, False, False, None),
    Source("S09", "partner API reference", "partner NDA", True, False, False, False, None),
    Source("S10", "government dataset", "Open Government Licence", True, True, True, True, "contains public sector information"),
    Source("S11", "ebook chapter", "purchased copy, no licence to reproduce", True, False, False, False, None),
    Source("S12", "internal HR policies", "company-owned, confidential", True, False, False, False, None),
]
BY_ID = {s.id: s for s in CORPUS}


# ============================================================ 1
rule("1. PERMITTED USE ACROSS THE CORPUS")

buckets = {
    "usable in a commercial product": [s for s in CORPUS if s.commercial_use],
    "internal use only": [s for s in CORPUS if s.internal_use and not s.commercial_use],
    "not usable at all (unknown or prohibited)": [s for s in CORPUS if not s.internal_use],
    "may be quoted verbatim to a customer": [s for s in CORPUS if s.redistribute_verbatim],
    "may be used to train or fine-tune a model": [s for s in CORPUS if s.train_on],
    "requires attribution when used": [s for s in CORPUS if s.attribution],
}
for label, group in buckets.items():
    print(f"  {label:<44} {len(group):>2}/{len(CORPUS)}  {', '.join(s.id for s in group)}")
print("\n  'We have the file' and 'we may use the file for this' are different questions,")
print("  and the second one has several answers depending on WHICH use.")


# ============================================================ 2
rule("2. PROPAGATION: SOURCE -> CHUNK -> RETRIEVAL -> ANSWER")

CHUNKS = [(f"{s.id}-c{i}", s.id) for s in CORPUS for i in range(1, 4)]     # 3 chunks per source
QUERIES = {
    "customer asks how to configure the widget": ["S01-c1", "S04-c2", "S02-c3", "S06-c1"],
    "customer asks what the standard requires": ["S03-c2", "S10-c1", "S01-c3"],
    "agent asks for an internal HR answer": ["S12-c1", "S08-c2"],
    "customer asks for a summary of recent coverage": ["S06-c2", "S07-c1", "S05-c3"],
}


def audience_of(query: str) -> str:
    return "internal" if query.startswith("agent") else "customer"


def allowed(chunk_id: str, audience: str) -> bool:
    s = BY_ID[chunk_id.split("-")[0]]
    if not s.internal_use:
        return False
    return s.commercial_use if audience == "customer" else True


leaks_unfiltered = leaks_filtered = used = 0
for query, hits in QUERIES.items():
    audience = audience_of(query)
    bad = [c for c in hits if not allowed(c, audience)]
    leaks_unfiltered += len(bad)
    kept = [c for c in hits if allowed(c, audience)]
    used += len(kept)
    print(f"  {query[:52]:<52} audience={audience}")
    print(f"    retrieved {len(hits)} chunk(s); not permitted for this audience: "
          f"{', '.join(bad) if bad else 'none'}")
print(f"\n  without a licence filter: {leaks_unfiltered} chunk(s) reached an audience they were not licensed for")
print(f"  with a licence filter at retrieval: 0 (and {used} chunk(s) still available to answer from)")
print("  The licence is an attribute of the CHUNK, not a note in a spreadsheet about")
print("  the source. If it is not in the index, the retriever cannot honour it.")


# ============================================================ 3
rule("3. ATTRIBUTION THAT THE ANSWER TEMPLATE DROPS")

ANSWER_TEMPLATE_INCLUDES_ATTRIBUTION = False
for query, hits in QUERIES.items():
    audience = audience_of(query)
    kept = [c for c in hits if allowed(c, audience)]
    need = [(c, BY_ID[c.split("-")[0]].attribution) for c in kept if BY_ID[c.split("-")[0]].attribution]
    if need:
        shown = "included" if ANSWER_TEMPLATE_INCLUDES_ATTRIBUTION else "MISSING"
        print(f"  {query[:52]:<52} attribution {shown}: "
              f"{'; '.join(f'{c} -> {a}' for c, a in need)}")
missing = sum(1 for q, hits in QUERIES.items()
              for c in hits if allowed(c, audience_of(q)) and BY_ID[c.split('-')[0]].attribution)
print(f"\n  {missing} attribution(s) required and {0 if ANSWER_TEMPLATE_INCLUDES_ATTRIBUTION else missing} omitted.")
print("  Attribution is a condition of the licence, not a courtesy: CC BY-SA and")
print("  Apache-2.0 both require notices to travel with the material.")


# ============================================================ 4
rule("4. THE SAME SOURCE, DIFFERENT USE CLASSES")

USES = {
    "retrieval for internal staff": ("internal", lambda s: s.internal_use),
    "retrieval for customers": ("customer", lambda s: s.commercial_use),
    "verbatim quotation to customers": ("verbatim", lambda s: s.redistribute_verbatim),
    "fine-tuning a model we deploy": ("fine-tune", lambda s: s.train_on),
    "sharing the index with a partner": ("share idx", lambda s: s.redistribute_verbatim and s.commercial_use),
}
SHORT = [short for short, _ in USES.values()]
USES = {label: fn for label, (_, fn) in USES.items()}
print(f"  {'source':<8}{'origin':<34}" + "".join(f"{u:>12}" for u in SHORT))
for s in CORPUS:
    row = "".join(f"{('yes' if fn(s) else 'NO'):>12}" for fn in USES.values())
    print(f"  {s.id:<8}{s.origin[:32]:<34}{row}")
print()
for label, fn in USES.items():
    print(f"  {label:<32}: {sum(1 for s in CORPUS if fn(s)):>2}/{len(CORPUS)} sources permitted")
print("\n  A corpus assembled for one use is not automatically available for the next.")
print(f"  Fine-tuning is the sharpest example: {sum(1 for s in CORPUS if s.train_on)} of {len(CORPUS)}"
      " sources permit it (M13-L02).")


# ============================================================ 5
rule("5. DERIVED DATA: UNKNOWN PROVENANCE IS INHERITED")

DERIVED = {
    "clean-docs-v3": ["S01", "S04", "S10"],
    "support-qa-pairs": ["S08", "S02"],
    "community-answers": ["S07", "S05"],
    "eval-set-v2": ["support-qa-pairs", "community-answers"],
    "finetune-mix-v1": ["clean-docs-v3", "eval-set-v2"],
}


def resolve(name: str, seen: set | None = None) -> set[str]:
    seen = seen or set()
    if name in BY_ID:
        return {name}
    out: set[str] = set()
    for parent in DERIVED.get(name, []):
        if parent not in seen:
            out |= resolve(parent, seen | {name})
    return out


for dataset in DERIVED:
    roots = resolve(dataset)
    unknown = sorted(r for r in roots if BY_ID[r].licence == "unknown")
    no_training = sorted(r for r in roots if not BY_ID[r].train_on)
    print(f"  {dataset:<18} roots: {', '.join(sorted(roots))}")
    print(f"  {'':<18} unknown licence: {', '.join(unknown) or 'none'};  "
          f"not permitted for training: {', '.join(no_training) or 'none'}")
print("\n  'finetune-mix-v1' inherits one unknown-licence source through two levels of")
print("  derivation. Provenance has to be recorded per record and carried forward, or")
print("  the answer to 'may we train on this?' becomes unknowable (M10-L13).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count, filter result and provenance resolution above is computed")
print("  from the encoded corpus and derivation graph.")
print("\n  ILLUSTRATIVE: the licences are simplified to five booleans. Real licence terms")
print("  are text, they differ by jurisdiction, and some questions have no settled")
print("  answer yet -- this course gives no legal advice (M10-L16).")
print("\n  NOT SHOWN: personal-data rules, which are a separate question from licensing")
print("  and apply even to data you own (M10-L06).")
print("\nDone.")
