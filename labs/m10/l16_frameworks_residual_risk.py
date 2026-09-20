"""M10-L16 lab -- frameworks, obligations and the risk that is left over.
This lab computes:

  1. where this module's controls land against the four AI RMF functions,
  2. what is a legal obligation, what a framework expectation, what a team choice,
  3. residual risk arithmetic: controls are partial, and they stack multiplicatively,
  4. which rows exceed the risk appetite and therefore need a named accepter,
  5. a system that satisfies every checklist item and still carries an unacceptable risk.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l16_frameworks_residual_risk.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. THIS MODULE AGAINST THE FOUR AI RMF FUNCTIONS")

# AI RMF 1.0 (NIST, January 2023) organises practice into GOVERN, MAP, MEASURE, MANAGE.
LESSONS = {
    "L01 four disciplines":        ["GOVERN"],
    "L02 intended use, ownership": ["GOVERN", "MAP"],
    "L03 AI inventories":          ["GOVERN", "MAP"],
    "L04 risk registers":          ["MAP", "MANAGE"],
    "L05 provenance, licensing":   ["MAP"],
    "L06 personal data":           ["MAP", "MANAGE"],
    "L07 access control":          ["MANAGE"],
    "L08 bias, subgroups":         ["MEASURE"],
    "L09 transparency, oversight": ["GOVERN", "MANAGE"],
    "L10 security threat model":   ["MAP", "MANAGE"],
    "L11 supplier assessment":     ["GOVERN", "MAP"],
    "L12 release gates":           ["MEASURE", "MANAGE"],
    "L13 versioning, audit":       ["GOVERN", "MEASURE"],
    "L14 incident response":       ["MANAGE"],
    "L15 model and system cards":  ["GOVERN"],
    "L16 frameworks, residual":    ["GOVERN"],
}
FUNCTIONS = ["GOVERN", "MAP", "MEASURE", "MANAGE"]
print(f"  {'lesson':<32}" + "".join(f"{f:>9}" for f in FUNCTIONS))
for name, fns in LESSONS.items():
    print(f"  {name:<32}" + "".join(f"{('x' if f in fns else '.'):>9}" for f in FUNCTIONS))
print()
for f in FUNCTIONS:
    n = sum(1 for fns in LESSONS.values() if f in fns)
    print(f"  {f:<9} covered by {n:>2}/{len(LESSONS)} lessons")
print("\n  MEASURE is the thinnest column, and that is the usual shape: teams find it")
print("  easier to write policies than to measure whether they work (L08, L12).")
print("  A framework is a checklist of QUESTIONS, not a set of controls -- the")
print("  controls are the lessons.")


# ============================================================ 2
rule("2. OBLIGATION, EXPECTATION, OR CHOICE?")

STATEMENTS = [
    ("Personal data needs a lawful basis and a retention period",
     "obligation", "data-protection law where you operate; the ENGINEERING consequence is L06"),
    ("Keep an inventory of AI systems",
     "expectation", "ISO/IEC 42001 and AI RMF GOVERN; sometimes an obligation for specific sectors"),
    ("Gate releases on a per-slice quality threshold",
     "choice", "no framework prescribes your thresholds; you choose and justify them (L12)"),
    ("Tell users they are interacting with an AI system",
     "obligation", "required in several jurisdictions and contexts; verify yours"),
    ("Run a risk assessment before deploying a high-impact system",
     "expectation", "AI RMF MAP, ISO/IEC 42001; obligation in some sectors and jurisdictions"),
    ("Pin model versions in production",
     "choice", "pure engineering discipline; no framework mentions it (L13)"),
    ("Be able to delete a person's data on request",
     "obligation", "data-protection law; drives your deletion design (L06)"),
    ("Publish a model card",
     "choice", "widely expected, rarely required; you decide the audience (L15)"),
    ("Report a personal-data breach within a defined window",
     "obligation", "jurisdiction-specific timing; drives the L14 severity rule"),
    ("Evaluate subgroup performance",
     "expectation", "AI RMF MEASURE; an obligation where anti-discrimination law bites (L08)"),
    ("Keep a human in the loop for consequential decisions",
     "expectation", "obligation in specific regulated decisions; otherwise your design choice (L09)"),
    ("Use a canary rollout",
     "choice", "engineering practice; nothing requires it, the arithmetic argues for it (L14)"),
]
KIND = {"obligation": "LEGAL OBLIGATION", "expectation": "framework expectation", "choice": "your choice"}
print(f"  {'statement':<61}{'kind':<24}basis")
for text, kind, basis in STATEMENTS:
    print(f"  {text:<61}{KIND[kind]:<24}{basis[:42]}")
counts = {k: sum(1 for _, kk, _ in STATEMENTS if kk == k) for k in KIND}
print(f"\n  {counts['obligation']} obligations, {counts['expectation']} framework expectations, "
      f"{counts['choice']} engineering choices (out of {len(STATEMENTS)})")
print("  Two failure modes, equally common: treating a choice as an obligation ('we")
print("  must, the framework says so') and treating an obligation as a choice ('we")
print("  will do deletion later'). Only the first column is not negotiable -- and")
print("  which statements sit in it depends on YOUR jurisdiction and sector.")
print("  NOTHING HERE IS LEGAL ADVICE: the engineering job is to build the capability")
print("  and to ask the question early enough that the answer can change the design.")


# ============================================================ 3
rule("3. RESIDUAL RISK: CONTROLS ARE PARTIAL, AND THEY MULTIPLY")

RISK = 0.40   # inherent likelihood of the outcome in a year, before controls
CONTROLS = [
    ("input delimiting and provenance marking (M5-L13)", 0.35),
    ("authorization enforced outside the model (L07, M9-L13)", 0.70),
    ("egress allowlist (M9-L12)", 0.50),
    ("human approval for state-changing actions (M8-L10)", 0.60),
    ("monitoring and canary rollout (L14)", 0.30),
]
print(f"  inherent likelihood: {RISK:.0%} per year\n")
print(f"  {'control':<56}{'reduces by':>12}{'residual':>11}")
residual = RISK
for name, effect in CONTROLS:
    residual *= (1 - effect)
    print(f"  {name:<56}{effect:>11.0%}{residual:>11.2%}")
print(f"\n  five controls, none of them perfect  ->  residual {residual:.2%} per year")
print(f"  removing the single best control ({max(CONTROLS, key=lambda c: c[1])[0].split(' (')[0]}):")
without = RISK
for name, effect in CONTROLS:
    if effect != max(c[1] for c in CONTROLS):
        without *= (1 - effect)
print(f"    residual becomes {without:.2%}  -- {without / residual:.1f}x higher")
print("\n  No control is 100%, so residual risk is never zero. Stacking independent")
print("  partial controls works BECAUSE they multiply -- and the same arithmetic")
print("  says one strong control cannot carry the whole stack (L10).")


# ============================================================ 4
rule("4. WHAT IS LEFT, AND WHO ACCEPTS IT?")

APPETITE = {"low": 0.01, "medium": 0.05, "high": 0.15}
ROWS = [
    ("R01 cross-tenant data exposure",       0.30, 0.97, "low"),
    ("R02 unsafe advice reaches a user",     0.45, 0.88, "low"),
    ("R03 agent takes a wrong billing action", 0.35, 0.90, "medium"),
    ("R04 quality regression on a slice",    0.60, 0.75, "medium"),
    ("R05 provider outage, feature down",    0.80, 0.40, "high"),
    ("R06 cost overrun from a retry loop",   0.50, 0.85, "high"),
]
ACCEPTER = {"low": "executive owner + written acceptance", "medium": "system owner",
            "high": "team lead"}
print(f"  {'register row':<42}{'inherent':>10}{'controls':>10}{'residual':>10}{'appetite':>10}   verdict")
needs_acceptance = []
for name, inherent, reduction, tier in ROWS:
    residual = inherent * (1 - reduction)
    over = residual > APPETITE[tier]
    if over:
        needs_acceptance.append((name, tier))
    print(f"  {name:<42}{inherent:>10.0%}{reduction:>10.0%}{residual:>10.1%}"
          f"{APPETITE[tier]:>10.0%}   {'OVER -> accept or reduce' if over else 'within appetite'}")
print(f"\n  rows above appetite: {len(needs_acceptance)}/{len(ROWS)}")
for name, tier in needs_acceptance:
    print(f"    {name:<42} needs: {ACCEPTER[tier]}")
print("\n  Residual risk above appetite has exactly three honest endings: reduce it,")
print("  accept it in writing with a named person and a review date, or do not ship.")
print("  'We are aware of it' is not one of them (L04).")


# ============================================================ 5
rule("5. COMPLIANT AND STILL UNSAFE")

CHECKLIST = [
    ("inventory entry exists", True),
    ("intended use documented", True),
    ("DPIA-style assessment filed", True),
    ("system card published", True),
    ("supplier assessed", True),
    ("release gates defined", True),
    ("incident process documented", True),
    ("staff trained", True),
]
REALITY = [
    ("gates run on a 90-question set (MDE ~11 points)", False, "cannot detect the regressions it gates on"),
    ("no per-slice gate; French is 4% of the set", False, "L08/L12 gap the checklist does not see"),
    ("agent can email customers without approval", False, "one-way door, no approval gate (M8-L10)"),
    ("audit log keeps 7 days; complaints arrive at 36", False, "cannot investigate (L13)"),
]
done = sum(1 for _, ok in CHECKLIST if ok)
print(f"  checklist items complete: {done}/{len(CHECKLIST)}  -> the governance review passes\n")
print(f"  {'what is actually true':<50}{'effective?':>12}   why it matters")
for text, ok, why in REALITY:
    print(f"  {text:<50}{('yes' if ok else 'NO'):>12}   {why}")
print(f"\n  effective controls among the four checked: {sum(1 for _, ok, _ in REALITY if ok)}/4")
print("  A checklist asks whether an artefact EXISTS. Only a measurement asks whether")
print("  the control WORKS. Compliance is a floor and a vocabulary; it is not")
print("  evidence of safety, and passing it is not the goal (L01).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every coverage count, residual-risk figure, appetite comparison and")
print("  checklist count above is computed by this script from the encoded values.")
print("\n  ILLUSTRATIVE: the likelihoods, control effectiveness figures and appetite")
print("  thresholds are invented. Real ones come from your own incident history and")
print("  a decision by the people accountable for the system.")
print("\n  NOT LEGAL ADVICE: which statements in section 2 are obligations depends on")
print("  your jurisdiction, sector and the system itself. Ask early; the answer")
print("  changes the design, not just the paperwork.")
print("\nDone.")
