"""M10-L15 lab -- documentation is a control, and controls can be checked.
This lab:

  1. checks four system cards against a required-field list,
  2. asks which reader's questions each card can answer,
  3. classifies claims as falsifiable or unfalsifiable,
  4. detects a card that has gone stale against the deployed configuration,
  5. counts how much of a card can be generated from artefacts you already have.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l15_model_cards.py
"""

from __future__ import annotations

import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:12]


# ============================================================ 1
rule("1. FOUR CARDS AGAINST A REQUIRED-FIELD LIST")

REQUIRED = [
    "owner", "intended_use", "out_of_scope", "users_affected", "data_sources",
    "personal_data", "model_and_version", "evaluation_sets", "evaluation_results",
    "subgroup_results", "known_limitations", "failure_modes", "human_oversight",
    "escalation_path", "retention", "review_date",
]
CARDS = {
    "A: marketing one-pager": ["owner", "intended_use", "model_and_version"],
    "B: engineering README": ["owner", "model_and_version", "data_sources", "evaluation_sets",
                              "evaluation_results", "retention"],
    "C: compliance template": ["owner", "intended_use", "out_of_scope", "users_affected",
                               "personal_data", "retention", "review_date", "human_oversight"],
    "D: system card (this course)": REQUIRED,
}
print(f"  {'card':<32}{'present':>9}{'missing':>9}   biggest gaps")
for name, present in CARDS.items():
    missing = [f for f in REQUIRED if f not in present]
    gaps = ", ".join(missing[:3]) + ("..." if len(missing) > 3 else "")
    print(f"  {name:<32}{len(present):>9}{len(missing):>9}   {gaps or 'none'}")
print(f"\n  required fields: {len(REQUIRED)}")
print("  Card A describes the product. Card B describes the implementation. Card C")
print("  describes the obligations. None of the three answers a question the other")
print("  two answer -- which is why the card is ONE document with all of them.")


# ============================================================ 2
rule("2. WHOSE QUESTIONS DOES THE CARD ANSWER?")

READERS = {
    "an end user":        ["intended_use", "out_of_scope", "known_limitations", "escalation_path"],
    "an integrator":      ["intended_use", "out_of_scope", "model_and_version", "failure_modes",
                           "evaluation_results", "escalation_path"],
    "a security reviewer": ["data_sources", "personal_data", "retention", "human_oversight", "owner"],
    "a new on-call engineer": ["owner", "model_and_version", "failure_modes", "escalation_path",
                               "human_oversight"],
    "someone deciding to reuse it elsewhere": ["intended_use", "out_of_scope", "users_affected",
                                               "subgroup_results", "known_limitations", "evaluation_sets"],
}
print(f"  {'reader':<42}" + "".join(f"{k.split(':')[0]:>6}" for k in CARDS))
for reader, needs in READERS.items():
    row = ""
    for name, present in CARDS.items():
        answered = sum(1 for f in needs if f in present)
        row += f"{f'{answered}/{len(needs)}':>6}"
    print(f"  {reader:<42}{row}")
print("\n  A card is not a form to complete; it is a set of answers for named readers.")
print("  Write the reader list first, then check the card against it (M10-L09).")


# ============================================================ 3
rule("3. CAN THE CLAIM BE CHECKED?")

CLAIMS = [
    ("The assistant is highly accurate.", False,
     "no metric, no set, no number"),
    ("Answer support was 91.2% (CI 89.4-92.8) on regression set v7, n=1200, 2026-09-02.", True,
     "metric, set, size, interval, date"),
    ("We take privacy seriously.", False,
     "no data class, no retention, no mechanism"),
    ("Prompts and outputs are deleted after 30 days; metadata after 180.", True,
     "a stated period, testable against the store"),
    ("The system is unbiased.", False,
     "unfalsifiable as written; which subgroups, which metric?"),
    ("Worst-slice answer support was 84.1% (French billing, n=260).", True,
     "names the slice, the number and the size"),
    ("Humans review all high-risk outputs.", False,
     "'high-risk' undefined, 'review' undefined, no rate"),
    ("Refunds above GBP 200 need approval; 412/412 such cases were approved by a named agent.", True,
     "a threshold, a count, an owner"),
    ("The model may occasionally make mistakes.", False,
     "true of every system; carries no information"),
    ("Abstention rate 6.4%; of abstentions sampled (n=100), 88 were correct abstentions.", True,
     "a rate and a sampled check of it"),
]
ok = sum(1 for _, t, _ in CLAIMS if t)
print(f"  {'claim':<92}{'checkable':>11}")
for text, testable, why in CLAIMS:
    print(f"  {text[:90]:<92}{('yes' if testable else 'NO'):>11}")
print(f"\n  checkable: {ok}/{len(CLAIMS)}")
for text, testable, why in CLAIMS:
    if not testable:
        print(f"    NOT checkable: {text[:58]:<60} -- {why}")
print("\n  The test: could someone disagree with this sentence and settle it with a")
print("  measurement? If not, it is reassurance, and reassurance is not documentation.")


# ============================================================ 4
rule("4. HAS THE CARD GONE STALE?")

DEPLOYED = {"model": "vendor-x-large@2026-09-01", "index": "kb-v8#build-2026-09-10",
            "prompt_sha": "a32fe82f110e", "guardrail": "safety-policy-v5", "k": 12}
CARD_SAYS = {"model": "vendor-x-large@2026-06-11", "index": "kb-v7#build-2026-08-30",
             "prompt_sha": "eb4171e7e428", "guardrail": "safety-policy-v5", "k": 8}
print(f"  {'field':<14}{'card says':<30}{'deployed':<30}status")
drift = 0
for field in DEPLOYED:
    same = CARD_SAYS[field] == DEPLOYED[field]
    drift += not same
    print(f"  {field:<14}{str(CARD_SAYS[field]):<30}{str(DEPLOYED[field]):<30}{'ok' if same else 'STALE'}")
print(f"\n  card fingerprint {sha(CARD_SAYS)} vs deployed {sha(DEPLOYED)} -> {drift}/{len(DEPLOYED)} fields stale")
print("  A card written once and never checked becomes confidently wrong. Compare it")
print("  to the deployed fingerprint in CI and fail the build on drift (M10-L13).")


# ============================================================ 5
rule("5. HOW MUCH OF THE CARD CAN BE GENERATED?")

SOURCES = {
    "owner":              ("inventory row (L03)", True),
    "intended_use":       ("written by the owner (L02)", False),
    "out_of_scope":       ("written by the owner (L02)", False),
    "users_affected":     ("inventory row (L03)", True),
    "data_sources":       ("ingestion manifest (M7-L08)", True),
    "personal_data":      ("data map (L06)", True),
    "model_and_version":  ("run fingerprint (L13)", True),
    "evaluation_sets":    ("evaluation harness", True),
    "evaluation_results": ("latest gated run (L12)", True),
    "subgroup_results":   ("latest gated run (L08)", True),
    "known_limitations":  ("written, informed by failures", False),
    "failure_modes":      ("incident history (L14) + written", False),
    "human_oversight":    ("written by the owner (L09)", False),
    "escalation_path":    ("written by the owner (L09)", False),
    "retention":          ("retention policy (L06)", True),
    "review_date":        ("inventory row (L03)", True),
}
auto = [f for f, (_, a) in SOURCES.items() if a]
manual = [f for f, (_, a) in SOURCES.items() if not a]
print(f"  {'field':<22}{'source':<34}generated?")
for field, (src, a) in SOURCES.items():
    print(f"  {field:<22}{src:<34}{'auto' if a else 'written'}")
print(f"\n  auto-generated: {len(auto)}/{len(SOURCES)}    written by a person: {len(manual)}/{len(SOURCES)}")
print("  The generated fields are the ones that go stale, so generate them. The written")
print("  fields are the ones that carry judgement, so do not template them -- they are")
print("  the reason a card is worth reading (M10-L02).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every coverage count, reader score, checkability verdict, staleness")
print("  comparison and generated/written split above is computed by this script.")
print("\n  ILLUSTRATIVE: the four cards, the claims and the deployed configuration are")
print("  invented; the required-field list is this course's, not a standard.")
print("\n  NOT SHOWN: published model cards from model providers, regulatory")
print("  documentation duties, and the review process itself (M10-L16).")
print("\nDone.")
