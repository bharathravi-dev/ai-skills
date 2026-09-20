"""M12-L01 lab -- what you actually have to decide before calling a hosted model.
This lab computes:

  1. the access matrix: model x region x whether you have enabled it,
  2. how region parity narrows a design that started with a model in mind,
  3. on-demand vs provisioned throughput: the break-even point,
  4. what the service takes over and what stays yours (M11-L01 applied to Bedrock),
  5. the questions a model choice must answer before any code is written.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m12/l01_bedrock_concepts_model_access.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. THREE THINGS MUST ALL BE TRUE BEFORE A CALL SUCCEEDS")

# [ILLUSTRATIVE availability -- the real matrix changes constantly; check the console]
REGIONS = ["us-east-1", "eu-west-2", "eu-central-1", "ap-southeast-2"]
MODELS = {
    "frontier-large":   {"us-east-1": True, "eu-west-2": True,  "eu-central-1": True,  "ap-southeast-2": False},
    "frontier-small":   {"us-east-1": True, "eu-west-2": True,  "eu-central-1": True,  "ap-southeast-2": True},
    "embedding-v3":     {"us-east-1": True, "eu-west-2": True,  "eu-central-1": True,  "ap-southeast-2": True},
    "newest-preview":   {"us-east-1": True, "eu-west-2": False, "eu-central-1": False, "ap-southeast-2": False},
}
ENABLED = {"frontier-large", "embedding-v3"}      # access granted in this account
print(f"  {'model':<18}" + "".join(f"{r:>16}" for r in REGIONS) + "   enabled here?")
for model, avail in MODELS.items():
    row = "".join(f"{('available' if avail[r] else '-'):>16}" for r in REGIONS)
    print(f"  {model:<18}{row}   {'yes' if model in ENABLED else 'NOT REQUESTED'}")
print("\n  A call succeeds only when THREE things hold: the model exists in the region,")
print("  your account has been granted access to it, and your IAM policy allows the")
print("  invoke action for that model's ARN (M12-L08). Each fails with a different")
print("  error, and teams lose hours because 'access denied' can mean any of them.")


# ============================================================ 2
rule("2. REGION PARITY NARROWS THE DESIGN")

CONSTRAINTS = [
    ("no constraint",                             lambda m, r: True),
    ("data must stay in Europe",                  lambda m, r: r.startswith("eu-")),
    ("Europe + the model we designed around",     lambda m, r: r.startswith("eu-") and m == "frontier-large"),
    ("Europe + the newest preview model",         lambda m, r: r.startswith("eu-") and m == "newest-preview"),
]
for label, fn in CONSTRAINTS:
    ok = [(m, r) for m in MODELS for r in REGIONS if MODELS[m][r] and fn(m, r)]
    regions = sorted({r for _, r in ok})
    print(f"  {label:<40}{len(ok):>3} model/region pairs; regions: {', '.join(regions) or 'NONE'}")
print("\n  The last row is the one that ends a project: the model the prototype was")
print("  built on does not exist where the data is allowed to be. Check parity")
print("  BEFORE the prototype, record the date, and re-check before committing --")
print("  availability expands over time, which is why a six-month-old answer is not")
print("  an answer (M11-L02 section 5.4).")


# ============================================================ 3
rule("3. ON-DEMAND OR PROVISIONED THROUGHPUT?")

# [ILLUSTRATIVE rates]
IN_PER_M, OUT_PER_M = 3.00, 15.00          # USD per million tokens
PROVISIONED_PER_HOUR = 24.0                # one model unit
IN_TOK, OUT_TOK = 2400, 400
unit_cost = (IN_TOK * IN_PER_M + OUT_TOK * OUT_PER_M) / 1_000_000
print(f"  on-demand: ${IN_PER_M}/M input, ${OUT_PER_M}/M output; "
      f"a request is {IN_TOK} in + {OUT_TOK} out = ${unit_cost:.4f}")
print(f"  provisioned: ${PROVISIONED_PER_HOUR}/hour per model unit, "
      f"whether you use it or not\n")
print(f"  {'requests/day':>14}{'on-demand $/mo':>17}{'provisioned $/mo':>19}   cheaper")
monthly_prov = PROVISIONED_PER_HOUR * 730
for rpd in (1_000, 20_000, 100_000, 400_000, 2_000_000):
    od = unit_cost * rpd * 30
    print(f"  {rpd:>14,}{od:>17,.0f}{monthly_prov:>19,.0f}   "
          f"{'on-demand' if od < monthly_prov else 'provisioned'}")
breakeven = monthly_prov / (unit_cost * 30)
print(f"\n  break-even: about {breakeven:,.0f} requests/day at this token profile.")
print("  Two things the table hides. Provisioned throughput also buys PREDICTABLE")
print("  capacity -- no throttling from a shared pool (M12-L12) -- which can matter")
print("  more than the price. And it is a COMMITMENT: if you halve your context")
print("  length next month, the on-demand line falls and the provisioned one does")
print("  not (M11-L11 section 5.3).")


# ============================================================ 4
rule("4. WHAT THE SERVICE TAKES OVER, AND WHAT STAYS YOURS")

SPLIT = [
    ("running and scaling the model",        "service"),
    ("model weights and updates",            "service"),
    ("regional availability",                "service"),
    ("which model you choose",               "yours"),
    ("what data you send it",                "yours"),
    ("the prompt and its versioning",        "yours"),
    ("output validation and repair",         "yours"),
    ("guardrail configuration",              "yours (M12-L06)"),
    ("IAM permissions on invoke",            "yours (M12-L08)"),
    ("retry, timeout and backoff policy",    "yours (M12-L12)"),
    ("evaluation on your tasks",             "yours (M10-L12)"),
    ("cost per request",                     "yours (M12-L14)"),
]
svc = sum(1 for _, o in SPLIT if o == "service")
print(f"  {'concern':<40}{'owner':<20}")
for concern, owner in SPLIT:
    print(f"  {concern:<40}{owner:<20}")
print(f"\n  the service owns {svc}/{len(SPLIT)}; you own {len(SPLIT) - svc}/{len(SPLIT)}")
print("  This is M11-L01's table for one service. A managed model removes the")
print("  hardest operational problem in the stack and none of the engineering ones.")
print("  Everything in Modules 5, 7, 8 and 10 still applies, unchanged.")


# ============================================================ 5
rule("5. THE QUESTIONS A MODEL CHOICE HAS TO ANSWER")

QUESTIONS = [
    ("Does it exist in our region, today?",          "section 2; record the date"),
    ("Has access been requested and granted?",       "section 1; per account"),
    ("Is it good enough ON OUR TASKS?",              "your evaluation set, not a benchmark (M10-L11)"),
    ("What does a request cost at our token profile?", "section 3 (M11-L06, M12-L14)"),
    ("What is its p95 latency at our context size?", "measure it (M13-L11)"),
    ("What are the quotas, and what happens at them?", "throttling behaviour (M12-L12)"),
    ("Can we pin a version, and what notice of change?", "reproducibility (M10-L13)"),
    ("Is our data used for training? Retained?",     "supplier assessment (M10-L11)"),
    ("What is the fallback when it is unavailable?", "routing and degradation (M13-L08)"),
]
print(f"  {'question':<46}where it is answered")
for q, where in QUESTIONS:
    print(f"  {q:<46}{where}")
print(f"\n  {len(QUESTIONS)} questions; exactly ONE of them is about model quality.")
print("  That ratio is the lesson. Choosing a hosted model is mostly a procurement")
print("  and operations decision wearing an ML costume, and the questions that sink")
print("  projects are availability, quota, cost and version stability -- not whether")
print("  the model is clever enough.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count, filter result, cost projection and break-even figure")
print("  above is computed from the values in this script.")
print("\n  ILLUSTRATIVE: the model names, the availability matrix and every price are")
print("  INVENTED. Bedrock's model catalogue, regional availability and pricing")
print("  change frequently -- check the console and the pricing page, and record the")
print("  date you checked.")
print("\n  NOT SHOWN: the API surface itself (M12-L02), model customisation, and")
print("  cross-region inference routing.")
print("\nDone.")
