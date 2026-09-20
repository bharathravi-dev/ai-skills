"""M10-L06 lab -- personal data in an AI system: finding it, keeping less of it,
deleting it everywhere, and checking that 'anonymised' means anything. Measures:

  1. a regex PII detector's precision and recall per type on a labelled corpus,
  2. minimisation: fields collected vs fields the system actually reads,
  3. retention: records past their policy date, and where deletion does not reach,
  4. one erasure request traced across seven stores,
  5. k-anonymity of a 'pseudonymised' table: how many rows are unique.

All data is synthetic and generated in this file. No real personal data is used.
Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l06_personal_data.py
"""

from __future__ import annotations

import random
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1006)

# ============================================================ 1
rule("1. FINDING PERSONAL DATA: WHAT A REGEX DETECTOR CATCHES")

FIRST = ["Priya", "Sam", "Ana", "Raj", "Kim", "Li", "Tom", "Ivy"]
LAST = ["Nair", "Okafor", "Blum", "Mehta", "Adeyemi", "Chen", "Hart", "Silva"]
TEMPLATES = [
    ("email", lambda: f"Please update my address, my email is {rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}@example.com"),
    ("phone", lambda: f"Call me on 07{rng.randrange(100000000, 999999999)} about order {rng.randrange(1000, 9999)}"),
    ("card", lambda: f"I paid with card 4539 {rng.randrange(1000, 9999)} {rng.randrange(1000, 9999)} {rng.randrange(1000, 9999)}"),
    ("postcode", lambda: f"Delivery to {rng.choice(['SW1A 1AA', 'M1 4BT', 'EH8 9YL', 'BS1 5TR'])} was late"),
    ("dob", lambda: f"My date of birth is {rng.randrange(1, 28):02d}/{rng.randrange(1, 12):02d}/19{rng.randrange(50, 99)}"),
    ("name", lambda: f"This is {rng.choice(FIRST)} {rng.choice(LAST)} following up on the refund"),
    ("none", lambda: rng.choice(["The parcel never arrived and the tracking page is stuck",
                                 "Can you explain the refund policy for damaged goods?",
                                 "Order 5512 shipped twice, please advise",
                                 "The app crashes when I upload a photo"])),
]
CORPUS = []
for i in range(120):
    kind, make = TEMPLATES[i % len(TEMPLATES)]
    CORPUS.append((kind, make()))

DETECTORS = {
    "email": r"[\w.\-]+@[\w\-]+\.[a-z]{2,}",
    "phone": r"\b07\d{9}\b",
    "card": r"\b(?:\d{4}[ \-]?){3}\d{4}\b",
    "postcode": r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b",
    "dob": r"\b\d{2}/\d{2}/(19|20)\d{2}\b",
    "name": r"\b(?:Mr|Mrs|Ms|Dr)\.? [A-Z][a-z]+\b",          # only catches titled names
}


def detect(text: str) -> set[str]:
    return {kind for kind, pattern in DETECTORS.items() if re.search(pattern, text)}


stats = {kind: Counter() for kind, _ in TEMPLATES if kind != "none"}
false_positives = 0
for kind, text in CORPUS:
    found = detect(text)
    if kind == "none":
        false_positives += bool(found)
        continue
    stats[kind]["total"] += 1
    stats[kind]["found"] += kind in found
for kind, c in stats.items():
    recall = c["found"] / c["total"]
    print(f"  {kind:<9} detected in {c['found']:>2}/{c['total']:>2} texts containing it   recall {recall:.0%}")
print(f"  false positives on {sum(1 for k, _ in CORPUS if k == 'none')} texts with no personal data: {false_positives}")
VARIANTS = [
    ("email", "write to priya+refunds@example.co.uk please"),
    ("email", "my address is P.NAIR (at) example.com"),
    ("phone", "ring 07700 900123 after six"),
    ("phone", "my mobile is +44 7700 900123"),
    ("card", "card number 4539123412341234, expires soon"),
    ("card", "the card ending 1234 was charged twice"),
    ("postcode", "delivery to sw1a 1aa was late"),
    ("dob", "I was born on 3 Feb 1975"),
    ("dob", "d.o.b. 1975-02-03"),
    ("name", "this is Priya Nair following up"),
]
hits = sum(1 for kind, text in VARIANTS if kind in detect(text))
print(f"\n  the same detector on {len(VARIANTS)} everyday FORMAT VARIANTS: {hits}/{len(VARIANTS)} found")
for kind, text in VARIANTS:
    if kind not in detect(text):
        print(f"    missed {kind:<9} {text}")
print("\n  Names are the gap: without a title they look like any other words, and a")
print("  pattern that matches capitalised pairs would flag product names and places.")
print("  Detection finds structured identifiers; it does not make a system compliant.")


# ============================================================ 2
rule("2. MINIMISATION: COLLECTED VS ACTUALLY USED")

RECORD_FIELDS = ["order_id", "customer_name", "email", "phone", "billing_address", "delivery_address",
                 "date_of_birth", "card_last4", "order_total", "items", "delivery_status", "marketing_optin",
                 "support_history", "ip_address"]
PROMPT_TEMPLATE = "Order {order_id} for {customer_name}: status {delivery_status}, total {order_total}, items {items}."
DECISION_READS = {"order_total", "delivery_status", "order_id"}
used_in_prompt = set(re.findall(r"{(\w+)}", PROMPT_TEMPLATE))
used = used_in_prompt | DECISION_READS
unused = [f for f in RECORD_FIELDS if f not in used]
sensitive_unused = [f for f in unused if f in {"date_of_birth", "card_last4", "ip_address", "phone",
                                               "billing_address", "delivery_address", "support_history", "email"}]
print(f"  fields on the record            : {len(RECORD_FIELDS)}")
print(f"  fields the prompt renders       : {len(used_in_prompt)}  {sorted(used_in_prompt)}")
print(f"  fields the decision logic reads  : {len(DECISION_READS)}  {sorted(DECISION_READS)}")
print(f"  fields used by neither           : {len(unused)}  {unused}")
print(f"  of those, personal or sensitive  : {len(sensitive_unused)}  {sensitive_unused}")
print(f"\n  Sending the whole record to the model would expose {len(sensitive_unused)} unnecessary personal fields")
print("  to a third party, to logs, and to anyone who later reads the trace. Pass the")
print("  fields the task needs, and pseudonymise the ones it needs only as a key.")


# ============================================================ 3
rule("3. RETENTION AND WHERE DELETION DOES NOT REACH")

RETENTION_DAYS = 90
records = [{"id": f"T{i:04d}", "age_days": rng.randrange(1, 400)} for i in range(500)]
overdue = [r for r in records if r["age_days"] > RETENTION_DAYS]
print(f"  {len(records)} support conversations; policy says delete after {RETENTION_DAYS} days")
print(f"  past the policy date: {len(overdue)} ({len(overdue) / len(records):.0%})")

STORES = ["primary database", "search index", "vector index", "answer cache", "application logs",
          "evaluation dataset", "nightly backups"]
NAIVE_DELETE = {"primary database"}
PROPAGATED_DELETE = {"primary database", "search index", "vector index", "answer cache", "evaluation dataset"}
print(f"\n  a deletion job that only touches the primary store leaves data in:")
for store in STORES:
    if store not in NAIVE_DELETE:
        print(f"    - {store}")
print(f"\n  with propagation implemented, remaining: "
      f"{[s for s in STORES if s not in PROPAGATED_DELETE]}")
print("  Logs and backups need their own answer: shorten log retention and redact at")
print("  write time; for backups, record the maximum restore window as a documented")
print("  exception with an expiry, and re-apply deletions after any restore.")


# ============================================================ 4
rule("4. ONE ERASURE REQUEST, TRACED")

SUBJECT = "customer C-2291"
PRESENCE = {
    "primary database": ("row in customers, 14 orders", True),
    "search index": ("3 documents mentioning the name", True),
    "vector index": ("12 chunks embedded from their transcripts", True),
    "answer cache": ("2 cached answers containing their address", True),
    "application logs": ("47 lines containing email and IP", False),
    "evaluation dataset": ("1 example built from their complaint", True),
    "nightly backups": ("present in 35 daily snapshots", False),
}
for store, (what, deletable) in PRESENCE.items():
    print(f"  {store:<20} {what:<46} {'deletable now' if deletable else 'NOT reachable by the job'}")
unreachable = [s for s, (_, d) in PRESENCE.items() if not d]
print(f"\n  stores the deletion job cannot clear today: {len(unreachable)} ({', '.join(unreachable)})")
print("  The vector index matters even though it holds numbers, not text: embeddings")
print("  are derived from the person's words and can support retrieval about them, so")
print("  they are in scope. Delete the chunk AND its vector, and rebuild if the index")
print("  cannot delete in place (M6-L10).")


# ============================================================ 5
rule("5. 'PSEUDONYMISED' IS NOT 'ANONYMOUS': k-ANONYMITY")

table = []
for i in range(200):
    table.append({
        "pseudonym": f"U{i:04d}",                                  # name removed
        "postcode_district": rng.choice(["SW1A", "M1", "EH8", "BS1", "LS6", "CF10"]),
        "birth_year": rng.choice(range(1950, 2005)),
        "dept": rng.choice(["retail", "trade", "online"]),
    })
QUASI = ("postcode_district", "birth_year", "dept")
groups = Counter(tuple(r[q] for q in QUASI) for r in table)
unique = sum(1 for g, n in groups.items() if n == 1)
small = sum(n for g, n in groups.items() if n < 5)
print(f"  {len(table)} rows, names replaced by pseudonyms")
print(f"  distinct combinations of {QUASI}: {len(groups)}")
print(f"  rows that are the ONLY one with their combination (k=1): {unique} ({unique / len(table):.0%})")
print(f"  rows in a group smaller than k=5: {small} ({small / len(table):.0%})")
coarse = Counter((r["postcode_district"], (r["birth_year"] // 10) * 10) for r in table)
unique_coarse = sum(1 for g, n in coarse.items() if n == 1)
print(f"\n  after generalising: postcode district + birth DECADE, dropping dept")
print(f"    distinct combinations: {len(coarse)};  k=1 rows: {unique_coarse}")
print("\n  Removing the name does not make a row anonymous. Quasi-identifiers")
print("  re-identify people, so pseudonymised data is still personal data and still")
print("  needs access control, retention and deletion (this lesson).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every recall figure, field count, retention count and k-anonymity")
print("  statistic above is computed from the generated data in this file.")
print("\n  ILLUSTRATIVE: all data is synthetic; the detector is deliberately simple; and")
print("  k-anonymity is one crude measure of re-identification risk, not a guarantee.")
print("\n  NOT SHOWN: any jurisdiction's legal definitions or lawful bases -- this course")
print("  gives no legal advice (M10-L16). Differential privacy, secure enclaves and")
print("  formal de-identification standards are out of scope.")
print("\nDone.")
