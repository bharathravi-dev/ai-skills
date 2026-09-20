"""M10-L03 lab -- you cannot govern what you cannot list. This lab scans a synthetic
codebase for signs of AI usage, reconciles what it finds with a registered
inventory, and measures:

  1. discovery: which components use a model, and what the signal was,
  2. reconciliation: shadow systems, ghost entries, and recorded-but-wrong details,
  3. record quality: how many inventory fields are actually filled in,
  4. dependencies: the blast radius when one provider or shared prompt changes,
  5. tiering: high-risk systems missing the artefacts their tier requires.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l03_ai_inventory.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# A stand-in for a code search across repositories: path -> file content.
CODEBASE = {
    "support-assistant/app/llm.py": "from anthropic import Anthropic\nclient = Anthropic()\nMODEL='claude-sonnet-5'",
    "support-assistant/prompts/refund_draft.txt": "You are a support assistant. Draft a refund email...",
    "billing-classifier/train.py": "from sklearn.linear_model import LogisticRegression\nmodel.fit(X, y)",
    "billing-classifier/serve.py": "import joblib\nmodel = joblib.load('model.pkl')",
    "docs-search/index.py": "import requests\nrequests.post('https://api.example-embeddings.com/v1/embed', json=payload)",
    "docs-search/rerank.py": "from sentence_transformers import CrossEncoder",
    "hr-screening/score.py": "import boto3\nbedrock = boto3.client('bedrock-runtime')\nMODEL_ID='anthropic.claude-3-haiku'",
    "marketing-copy/generate.py": "import openai\nopenai.chat.completions.create(model='gpt-4o-mini', messages=msgs)",
    "ops-dashboard/anomaly.py": "import numpy as np\nthreshold = mean + 3 * std",
    "ops-dashboard/summarise.py": "from litellm import completion\ncompletion(model='claude-haiku-4-5', messages=m)",
    "intranet-bot/handler.js": "const res = await fetch('https://api.anthropic.com/v1/messages', {method:'POST'})",
    "payroll/report.py": "import pandas as pd\ndf.groupby('dept').sum()",
}

SIGNALS = [
    ("provider SDK", r"\b(anthropic|openai|litellm|bedrock-runtime|google\.generativeai)\b"),
    ("provider endpoint", r"https://api\.[a-z0-9.\-]*(anthropic|openai|example-embeddings)[a-z0-9.\-]*/"),
    ("model identifier", r"\b(claude|gpt|gemini|llama|mistral)[\w.\-]*\b"),
    ("local ML model", r"\b(sklearn|joblib|sentence_transformers|torch|xgboost)\b"),
    ("prompt asset", r"You are a .{0,40}(assistant|agent|classifier)"),
]

REGISTERED = {
    "support-assistant": {"owner": "Dir. Support Ops", "purpose_ref": "IU-014", "provider": "Anthropic",
                          "model": "claude-sonnet-5", "data_classes": ["customer email", "order"], "tier": "high",
                          "environments": ["prod"], "last_review": "2026-08-01",
                          "artefacts": {"risk_register", "evaluation", "card"}},
    "billing-classifier": {"owner": "Finance Eng", "purpose_ref": "IU-021", "provider": "in-house",
                           "model": "logistic regression", "data_classes": ["invoice"], "tier": "medium",
                           "environments": ["prod"], "last_review": "2026-05-12",
                           "artefacts": {"risk_register", "evaluation"}},
    "docs-search": {"owner": "Knowledge Team", "purpose_ref": None, "provider": "example-embeddings",
                    "model": None, "data_classes": ["internal docs"], "tier": "low",
                    "environments": ["prod"], "last_review": "2025-11-02", "artefacts": {"risk_register"}},
    "hr-screening": {"owner": "People Ops", "purpose_ref": "IU-033", "provider": "AWS Bedrock",
                     "model": "anthropic.claude-3-sonnet", "data_classes": ["CV", "personal data"], "tier": "high",
                     "environments": ["prod"], "last_review": "2026-02-17", "artefacts": {"risk_register"}},
    "legacy-chatbot": {"owner": "Digital", "purpose_ref": "IU-002", "provider": "OpenAI", "model": "gpt-3.5-turbo",
                       "data_classes": ["customer chat"], "tier": "medium", "environments": ["prod"],
                       "last_review": "2024-09-30", "artefacts": {"risk_register", "card"}},
}
REQUIRED_FIELDS = ["owner", "purpose_ref", "provider", "model", "data_classes", "tier", "environments", "last_review"]
TIER_ARTEFACTS = {"high": {"risk_register", "evaluation", "card", "subgroup_eval"},
                  "medium": {"risk_register", "evaluation"}, "low": {"risk_register"}}


# ============================================================ 1
rule("1. DISCOVERY: WHAT IN THE CODEBASE USES A MODEL?")

discovered: dict[str, set[str]] = {}
for path, content in CODEBASE.items():
    component = path.split("/")[0]
    for name, pattern in SIGNALS:
        if re.search(pattern, content, re.I):
            discovered.setdefault(component, set()).add(name)
for component in sorted(set(p.split("/")[0] for p in CODEBASE)):
    found = discovered.get(component)
    print(f"  {component:<20} {'AI: ' + ', '.join(sorted(found)) if found else 'no AI signal found'}")
print(f"\n  {len(discovered)} of {len(set(p.split('/')[0] for p in CODEBASE))} components show at least one signal.")
print("  Note what a scan cannot tell you: whether the use is important, what data it")
print("  touches, or whether anyone owns it. Discovery starts the conversation.")


# ============================================================ 2
rule("2. RECONCILIATION: SHADOW SYSTEMS AND GHOST ENTRIES")

shadow = sorted(set(discovered) - set(REGISTERED))
ghosts = sorted(set(REGISTERED) - set(discovered))
both = sorted(set(discovered) & set(REGISTERED))
print(f"  registered and found in code : {len(both)}  {both}")
print(f"  SHADOW (in code, not in the inventory): {len(shadow)}  {shadow}")
print(f"  GHOST (in the inventory, not in code) : {len(ghosts)}  {ghosts}")

mismatches, skipped = [], []
for component in both:
    record = REGISTERED[component]
    code = " ".join(c for p, c in CODEBASE.items() if p.startswith(component + "/"))
    if not record["model"] or not re.search(r"claude|gpt|gemini|llama|mistral", record["model"], re.I):
        skipped.append(component)          # nothing to compare: in-house or unrecorded model
        continue
    if record["model"].split(".")[-1].lower() not in code.lower():
        found = re.findall(r"(?:claude|gpt|gemini|llama)[\w.\-]*", code, re.I)
        mismatches.append((component, record["model"], found[0] if found else "none found"))
print(f"\n  recorded model does not match the code: {len(mismatches)}  (checked {len(both) - len(skipped)} of "
      f"{len(both)}; skipped {', '.join(skipped)} -- no hosted model id recorded)")
for component, recorded, actual in mismatches:
    print(f"    {component:<20} inventory says {recorded!r}, code says {actual!r}")
print("\n  Shadow systems are the reason inventories are built by SCANNING as well as")
print("  asking. Ghosts matter too: a decommissioned entry hides that nothing is")
print("  running, and an out-of-date model field invalidates every evaluation result")
print("  recorded against it.")


# ============================================================ 3
rule("3. RECORD QUALITY")

for name, record in REGISTERED.items():
    missing = [f for f in REQUIRED_FIELDS if not record.get(f)]
    stale = record["last_review"] < "2026-03-01"
    flags = []
    if missing:
        flags.append("missing: " + ", ".join(missing))
    if stale:
        flags.append(f"last reviewed {record['last_review']}")
    print(f"  {name:<20} {len(REQUIRED_FIELDS) - len(missing)}/{len(REQUIRED_FIELDS)} fields"
          + (f"   {'; '.join(flags)}" if flags else "   current"))
print("\n  An inventory nobody maintains becomes a list of things that were once true.")
print("  Tie each entry's review to the system's own change events (M10-L02).")


# ============================================================ 4
rule("4. DEPENDENCIES: BLAST RADIUS OF ONE CHANGE")

DEPENDS_ON = {
    "support-assistant": {"Anthropic API", "shared-prompt-lib", "vector-index"},
    "docs-search": {"example-embeddings API", "vector-index"},
    "hr-screening": {"AWS Bedrock", "shared-prompt-lib"},
    "marketing-copy": {"OpenAI API", "shared-prompt-lib"},
    "ops-dashboard": {"Anthropic API"},
    "intranet-bot": {"Anthropic API"},
    "billing-classifier": set(),
}
for dependency in ("Anthropic API", "shared-prompt-lib", "vector-index", "OpenAI API"):
    affected = sorted(c for c, deps in DEPENDS_ON.items() if dependency in deps)
    unowned = [c for c in affected if c not in REGISTERED]
    print(f"  {dependency:<24} affects {len(affected)} component(s): {', '.join(affected)}")
    if unowned:
        print(f"    {' ' * 22} of which not in the inventory: {', '.join(unowned)}")
print("\n  A provider deprecating a model, or a shared prompt library changing, is a")
print("  change to every component in that row -- including the ones nobody registered.")


# ============================================================ 5
rule("5. TIERING: DOES EACH SYSTEM HAVE THE ARTEFACTS ITS TIER REQUIRES?")

for name, record in REGISTERED.items():
    required = TIER_ARTEFACTS[record["tier"]]
    missing = sorted(required - record["artefacts"])
    print(f"  {name:<20} tier={record['tier']:<6} missing artefacts: {', '.join(missing) if missing else 'none'}")
print(f"\n  shadow systems have NO tier and NO artefacts at all: {', '.join(shadow)}")
print("  Tiering is how an inventory turns into work: the tier decides which artefacts")
print("  from the rest of this module are mandatory (M10-L04, L08, L12, L15).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count, match and blast-radius set above is computed from the")
print("  encoded codebase, inventory and dependency graph in this file.")
print("\n  ILLUSTRATIVE: the 'codebase' is twelve short snippets, and the signals are")
print("  regular expressions -- a real scan needs dependency manifests, network egress")
print("  logs, cloud billing data and procurement records to catch what code misses.")
print("\n  NOT SHOWN: SaaS features bought by other departments, models embedded in")
print("  vendor products, and staff use of public chatbots -- all of which belong in a")
print("  complete inventory and none of which appear in your repositories.")
print("\nDone.")
