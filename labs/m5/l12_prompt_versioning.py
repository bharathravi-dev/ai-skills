"""M5-L12 lab -- prompt artefacts, golden sets, and how many samples a
regression actually needs before you can trust it.

Section 1 is real, deterministic logic: hashing a prompt artefact's
behaviour-affecting fields (no LLM involved -- hashlib only). Sections 2-3
use a mock model -- a seeded stand-in for "an LLM of quality q on this
case" -- to make exact-match brittleness and sampling noise measurable.
Section 4 replays section 1 and 2's numbers as a single incident: a
parameter-only change that a text-diff gate misses and a fingerprint gate
catches.

Deterministic (zlib.crc32 seeding). No API key, no network.
Run:  python labs/m5/l12_prompt_versioning.py
"""

from __future__ import annotations

import hashlib
import json
import zlib
from dataclasses import dataclass

import numpy as np


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*parts) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


# ============================================================ 1
rule("1. A PROMPT ARTEFACT IS MORE THAN ITS TEXT")


@dataclass(frozen=True)
class PromptArtefact:
    id: str
    version: str
    template: str
    model: str
    temperature: float
    max_tokens: int
    tool_schema: tuple

    def fingerprint(self) -> str:
        payload = json.dumps(
            {
                "template": self.template,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "tool_schema": self.tool_schema,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:12]


TEMPLATE = (
    'Classify the support ticket into one of: billing, technical, '
    'account, other. Respond with JSON: {"category": ...}.'
)

v1 = PromptArtefact("ticket_categorizer", "1.4.0", TEMPLATE,
                     "claude-sonnet-5", 0.0, 300, (("category", "string"),))
v2 = PromptArtefact("ticket_categorizer", "1.5.0", TEMPLATE + " Be concise.",
                     "claude-sonnet-5", 0.0, 300, (("category", "string"),))
v3 = PromptArtefact("ticket_categorizer", "1.4.0-cost-cut", TEMPLATE,
                     "claude-haiku-4-5", 0.0, 120, (("category", "string"),))

print("  Same logical prompt, three artefact states:\n")
print(f"  {'version':<18}{'template changed?':<20}{'model':<18}"
      f"{'max_tok':>8}{'fingerprint':>14}")
for art, base in ((v1, None), (v2, v1), (v3, v1)):
    changed = "n/a" if base is None else str(art.template != base.template)
    print(f"  {art.version:<18}{changed:<20}{art.model:<18}"
          f"{art.max_tokens:>8}{art.fingerprint():>14}")

print(f"\n  v1 -> v2: template text changed ({v1.template != v2.template}), "
      f"fingerprint changed ({v1.fingerprint() != v2.fingerprint()}). Expected.")
print(f"  v1 -> v3: template text changed ({v1.template != v3.template}), "
      f"fingerprint changed ({v1.fingerprint() != v3.fingerprint()}).")
print("\n  v3's template is byte-identical to v1's. A tool that only diffs the")
print("  template file sees NOTHING. The fingerprint -- computed over the")
print("  model, temperature, max_tokens and tool schema as well -- changes")
print("  anyway, because all four can change what the model actually does.")


# ============================================================ 2
rule("2. EXACT-MATCH TESTS FORMATTING; PROPERTY TESTS TEST CORRECTNESS")

CATEGORIES = ["billing", "technical", "account", "other"]
CASES = [
    ("c1", "My invoice shows double the amount charged last month.", "billing"),
    ("c2", "The app crashes every time I open the settings page.", "technical"),
    ("c3", "I can't log into my account after resetting my password.", "account"),
    ("c4", "Can you explain what the enterprise plan includes?", "other"),
    ("c5", "I was charged a late fee but I paid on time.", "billing"),
    ("c6", "Getting a 500 error when I try to export my report.", "technical"),
    ("c7", "Please delete my account and all associated data.", "account"),
    ("c8", "Do you offer discounts for annual billing?", "other"),
]
SURFACE_VARIATION = 0.35   # correct answers that differ byte-for-byte anyway


def simulate_run(case_id: str, quality: float, expected: str, trial: int):
    correct = seeded("correctness", case_id, quality, trial).random() < quality
    if correct:
        category = expected
    else:
        idx = (CATEGORIES.index(expected) + 1) % len(CATEGORIES)
        category = CATEGORIES[idx]
    surface_differs = seeded("surface", case_id, quality, trial).random() < SURFACE_VARIATION
    exact_pass = correct and not surface_differs
    property_pass = correct
    return category, exact_pass, property_pass


VERSIONS = {"v1 current  (q=0.95)": 0.95, "v3 cost-cut (q=0.75)": 0.75}

print(f"  8 golden cases. Surface variation (harmless formatting drift on an")
print(f"  otherwise-correct answer): {SURFACE_VARIATION:.0%}.\n")
for vname, q in VERSIONS.items():
    exact_hits = property_hits = 0
    print(f"  {vname}")
    print(f"    {'case':<6}{'expected':<12}{'got':<12}{'exact':>7}{'property':>10}")
    for case_id, text, expected in CASES:
        got, ep, pp = simulate_run(case_id, q, expected, trial=0)
        exact_hits += ep
        property_hits += pp
        print(f"    {case_id:<6}{expected:<12}{got:<12}"
              f"{'PASS' if ep else 'fail':>7}{'PASS' if pp else 'fail':>10}")
    print(f"    single-run pass rate: exact-match {exact_hits}/8, "
          f"property {property_hits}/8\n")

TRIALS = 40
print(f"  Averaged over {TRIALS} simulated runs per case (a stable estimate,")
print(f"  not one draw):\n")
print(f"  {'version':<24}{'exact-match rate':>18}{'property rate':>16}")
for vname, q in VERSIONS.items():
    exact_sum = property_sum = 0
    n = 0
    for case_id, text, expected in CASES:
        for trial in range(TRIALS):
            _, ep, pp = simulate_run(case_id, q, expected, trial)
            exact_sum += ep
            property_sum += pp
            n += 1
    print(f"  {vname:<24}{exact_sum / n:>17.0%}{property_sum / n:>16.0%}")

print("\n  Read the current version's row: its TRUE correctness is 95% by")
print("  construction, but exact-match reports far less, because it fails")
print("  every correct answer that happens to be formatted differently from")
print("  the stored golden string. Exact-match is measuring formatting")
print("  stability, not the thing you actually care about. Property")
print("  assertions -- 'is the category right', ignoring surface form --")
print("  track true quality far more closely.")


# ============================================================ 3
rule("3. HOW MANY SAMPLES DOES A REGRESSION NEED?")

TRUE_GOOD_P = 0.90
TRUE_BAD_P = 0.75
N_CASES = 8
THRESHOLD = 0.85
SUITE_TRIALS = 500

print(f"  True property-pass rate: {TRUE_GOOD_P:.0%} (current) vs "
      f"{TRUE_BAD_P:.0%} (regressed). Alert threshold: observed suite rate "
      f"< {THRESHOLD:.0%}.")
print(f"  {N_CASES} golden cases, {SUITE_TRIALS} simulated suite runs per row.\n")
print(f"  {'samples/case':>13}{'total draws':>13}{'false-alarm rate':>19}"
      f"{'catch rate':>12}")
for samples_per_case in (1, 5, 10, 30):
    total_draws = N_CASES * samples_per_case
    false_alarms = 0
    caught = 0
    for trial in range(SUITE_TRIALS):
        rng_good = seeded("suite-good", samples_per_case, trial)
        rng_bad = seeded("suite-bad", samples_per_case, trial)
        good_rate = (rng_good.random(total_draws) < TRUE_GOOD_P).mean()
        bad_rate = (rng_bad.random(total_draws) < TRUE_BAD_P).mean()
        false_alarms += good_rate < THRESHOLD
        caught += bad_rate < THRESHOLD
    print(f"  {samples_per_case:>13}{total_draws:>13}"
          f"{false_alarms / SUITE_TRIALS:>19.0%}{caught / SUITE_TRIALS:>12.0%}")

print("\n  At 1 sample/case (8 draws total) the suite is a noisy coin flip on")
print("  BOTH questions: it cries wolf on a healthy prompt and misses a real")
print("  drop from 90% to 75% often enough to be useless as a gate. More")
print("  samples per case make both numbers do what you want: false alarms")
print("  fall toward zero and the catch rate rises toward one. A single run")
print("  of your golden set is not evidence. Decide your samples/case and")
print("  your threshold BEFORE you need them, the same way you would size")
print("  any other statistical test.")


# ============================================================ 4
rule("4. THE INCIDENT: A GATE THAT ONLY READS THE TEMPLATE FILE")


def gate_by_text_diff(old: PromptArtefact, new: PromptArtefact) -> bool:
    return old.template != new.template


def gate_by_fingerprint(old: PromptArtefact, new: PromptArtefact) -> bool:
    return old.fingerprint() != new.fingerprint()


print("  Same v1 -> v3 change as section 1: model swapped to cut cost,")
print("  max_tokens lowered, template untouched. Two CI gates, one change:\n")
print(f"  {'gate':<28}{'re-runs the golden suite?':>28}")
print(f"  {'gate_by_text_diff(v1, v3)':<28}{str(gate_by_text_diff(v1, v3)):>28}")
print(f"  {'gate_by_fingerprint(v1, v3)':<28}{str(gate_by_fingerprint(v1, v3)):>28}")

print("\n  The text-diff gate ships v3 without a single golden case re-run,")
print("  because its diff of the template file is empty. Section 2 showed")
print(f"  what v3's real property-pass rate is: {TRUE_BAD_P:.0%}, against v1's")
print(f"  {TRUE_GOOD_P:.0%}. Section 3 showed that gap is easily caught at 10")
print("  samples/case -- a suite that never ran cannot catch anything.")
print("\n  The fingerprint gate re-runs the suite because it hashes every")
print("  field that can change model behaviour, not only the one file a")
print("  human is likely to remember to check.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1's hashing and diffing, and the CI-gate logic in")
print("  section 4 -- both are exact, deterministic code with no LLM in the")
print("  loop. Sections 2 and 3's ARITHMETIC is real: exact counts and rates")
print("  from many simulated trials.")
print("\n  MOCK: sections 2 and 3's model. 'Quality q' standing in for a real")
print("  model's true accuracy, and the surface-variation rate, are chosen")
print("  parameters, not measurements of any real model or provider.")
print("\n  ILLUSTRATIVE: the 90%/75% quality gap and the 0.85 threshold. Pick")
print("  your own from your own golden set's history before relying on a gate.")
print("\n  NOT SHOWN: an LLM-graded assertion (semantic similarity, a judge")
print("  model) for outputs too open-ended for a property check. That is a")
print("  heavier tool with its own failure modes -- see M5-L18 and M13-L13.")

print("\nDone.")
