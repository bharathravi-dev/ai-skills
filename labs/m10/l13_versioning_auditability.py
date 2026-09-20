"""M10-L13 lab -- what you must pin to be able to answer "what produced this?".
This lab computes:

  1. the run fingerprint: which artefacts change it, and which changes are invisible,
  2. two prompts that look identical in a terminal and hash differently,
  3. silent drift under a floating model alias vs a pinned version,
  4. how many audit questions a log can answer at three levels of stamping,
  5. retention vs the complaint window: the fraction of questions that arrive too late.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l13_versioning_auditability.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def sha(obj) -> str:
    """Stable content hash of any JSON-serialisable artefact."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


rng = random.Random(1013)

# ============================================================ 1
rule("1. THE RUN FINGERPRINT: WHAT ACTUALLY DECIDES THE ANSWER")

BASE = {
    "model": "vendor-x-large@2026-06-11",
    "decoding": {"temperature": 0.2, "top_p": 1.0, "max_tokens": 800},
    "system_prompt": "You answer only from the provided context. Cite sources.",
    "retrieval": {"index": "kb-v7", "embedding_model": "embed-3@2026-02", "k": 8, "reranker": "none"},
    "chunking": {"size": 800, "overlap": 120, "splitter": "heading-aware-v2"},
    "tools": ["search_kb", "get_order"],
    "guardrail_config": "safety-policy-v4",
    "code": "app@9f2c1ab",
}

CHANGES = [
    ("model pinned -> floating alias", ("model", "vendor-x-large@latest")),
    ("temperature 0.2 -> 0.7", ("decoding.temperature", 0.7)),
    ("k 8 -> 12", ("retrieval.k", 12)),
    ("re-embedded with embed-4", ("retrieval.embedding_model", "embed-4@2026-08")),
    ("chunk overlap 120 -> 200", ("chunking.overlap", 200)),
    ("system prompt reworded", ("system_prompt", "Answer using only the context given. Always cite.")),
    ("guardrail policy v4 -> v5", ("guardrail_config", "safety-policy-v5")),
    ("app code deploy", ("code", "app@3ee70d4")),
]


def apply(cfg: dict, path: str, value) -> dict:
    out = json.loads(json.dumps(cfg))
    node = out
    parts = path.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value
    return out


base_fp = sha(BASE)
print(f"  baseline run fingerprint: {base_fp}\n")
print(f"  {'single change':<38}{'new fingerprint':<18}differs?")
for label, (path, value) in CHANGES:
    fp = sha(apply(BASE, path, value))
    print(f"  {label:<38}{fp:<18}{'yes' if fp != base_fp else 'NO'}")

partial = {k: BASE[k] for k in ("model", "system_prompt")}
print(f"\n  a log that records only model + prompt has fingerprint {sha(partial)} for ALL of")
print(f"  {sum(1 for label, (p, _) in CHANGES if p.split('.')[0] not in ('model', 'system_prompt'))}"
      " of the changes above: they are invisible to it.")
print("  Everything that can change the answer belongs in the stamp, including the")
print("  index, the embedding model, the chunker, the guardrail config and the code.")


# ============================================================ 2
rule("2. TWO PROMPTS THAT LOOK THE SAME")

P1 = "You answer only from the provided context. Cite sources."
P2 = "You answer only from the provided context.  Cite sources."      # two spaces
P3 = "You answer only from the provided context. Cite sources. "      # trailing space
P4 = "You answer only from the provided context. Cite sources​." # zero-width space
for name, p in (("as written", P1), ("double space", P2), ("trailing space", P3), ("zero-width space", P4)):
    print(f"  {name:<20} len={len(p):<5} sha={sha(p)}   rendered: {p!s}")
print(f"\n  distinct prompts above: {len({P1, P2, P3, P4})} -- all four render near-identically in a terminal,")
print("  a ticket, or a pull-request description. 'The prompt is the same' is a claim")
print("  about a hash, not about how the text looks (M5-L12).")


# ============================================================ 3
rule("3. SILENT DRIFT UNDER A FLOATING ALIAS")

WEEKS = 26
builds = ["build-2026-03-14"]
for _ in range(1, WEEKS):
    builds.append(builds[-1] if rng.random() > 0.18 else f"build-{2026}-{rng.randint(4, 9):02d}-{rng.randint(1, 28):02d}")
distinct = len(dict.fromkeys(builds))
switch_weeks = [i for i in range(1, WEEKS) if builds[i] != builds[i - 1]]
print(f"  a service calling 'vendor-x-large@latest' for {WEEKS} weeks")
print(f"  distinct underlying builds actually served : {distinct}")
print(f"  weeks on which the build changed           : {switch_weeks}")
print(f"  the pinned service calling '@2026-06-11'   : 1 build, 0 changes\n")
print("  Every change above is a release you did not test, did not gate (L12) and")
print("  cannot reproduce. Pin the version; upgrade deliberately, through the gates.")


# ============================================================ 4
rule("4. WHAT CAN THE LOG ANSWER?")

QUESTIONS = [
    ("Which model version answered this request?",            {"model"}),
    ("What exact prompt text was sent?",                      {"prompt_hash"}),
    ("Which documents were retrieved, and from which index?", {"retrieval"}),
    ("Who was the user and what were they permitted to see?", {"identity"}),
    ("Which tool calls ran, with what arguments?",            {"tools"}),
    ("What did the user actually see?",                       {"output"}),
    ("Which config and guardrail policy were in force?",      {"config"}),
    ("Was this request part of the canary or the baseline?",  {"release"}),
    ("Can we reproduce the answer exactly today?",            {"model", "prompt_hash", "retrieval", "config"}),
]
LEVELS = {
    "minimal (timestamp + text)":  {"output"},
    "typical (model + output)":    {"model", "output", "identity"},
    "audit-ready":                 {"model", "prompt_hash", "retrieval", "identity", "tools", "output",
                                    "config", "release"},
}
print(f"  {'question':<52}" + "".join(f"{k.split(' ')[0]:>14}" for k in LEVELS))
for q, needs in QUESTIONS:
    row = "".join(f"{('yes' if needs <= fields else 'no'):>14}" for fields in LEVELS.values())
    print(f"  {q:<52}{row}")
for name, fields in LEVELS.items():
    ok = sum(1 for _, needs in QUESTIONS if needs <= fields)
    print(f"\n  {name:<30} answers {ok}/{len(QUESTIONS)} questions", end="")
print("\n\n  The cost of the audit-ready level is storage and a retention policy (L06).")
print("  The cost of the others is discovering, during an incident, that the question")
print("  you most need to answer was never recorded (M10-L14).")


# ============================================================ 5
rule("5. RETENTION VS THE WINDOW IN WHICH QUESTIONS ARRIVE")

N = 4000
lags = [max(0, int(rng.gauss(38, 46))) for _ in range(N)]     # days between request and complaint/audit
for retention in (7, 30, 90, 180, 365):
    answerable = sum(1 for d in lags if d <= retention)
    print(f"  retention {retention:>4} days -> {answerable / N:>6.2%} of questions still answerable "
          f"({N - answerable:>4} of {N} arrive after the logs are gone)")
print(f"\n  median lag {sorted(lags)[N // 2]} days, 90th percentile {sorted(lags)[int(N * 0.9)]} days "
      f"[ILLUSTRATIVE distribution]")
print("  Retention is a governance decision with two opposing pressures: minimisation")
print("  (L06) says delete early, auditability says keep long enough to answer. Set it")
print("  from the actual lag distribution, per data class, and write it down.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every hash, fingerprint comparison, drift count, coverage count and")
print("  retention percentage above is computed by this script.")
print("\n  ILLUSTRATIVE: the configuration values, the drift probability and the")
print("  complaint-lag distribution are invented.")
print("\n  NOT SHOWN: the storage system itself, tamper-evidence and log integrity,")
print("  and legal retention requirements (M10-L16, M11-L16).")
print("\nDone.")
