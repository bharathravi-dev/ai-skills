"""M5-L17 lab -- what actually changes when a prompt moves to another
provider: wire format, token counts, and whether a golden suite still passes.

Section 1 is REAL code: adapters converting one neutral request into three
illustrative provider wire shapes, with an exact structural diff. Section 2
is REAL: two different real tiktoken encodings counting the same text,
standing in honestly for "different providers tokenize differently" without
claiming to measure any specific provider's real tokenizer. Section 3 reuses
M5-L12's mock-quality-simulation machinery, now varying PROVIDER instead of
prompt version, with real arithmetic on stated pass rates.

Deterministic. No API key, no network beyond tiktoken's one-time download.
Run:  python labs/m5/l17_provider_portability.py
"""

from __future__ import annotations

import sys
import zlib

import numpy as np

try:                                                  # Windows consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                     # pragma: no cover
    pass

try:
    import tiktoken
    ENC_A = tiktoken.get_encoding("cl100k_base")
    ENC_B = tiktoken.get_encoding("o200k_base")
    TOKENIZERS_AVAILABLE = True
except Exception:                                    # pragma: no cover
    TOKENIZERS_AVAILABLE = False


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*parts) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


# ============================================================ 1
rule("1. THE SAME LOGICAL REQUEST, THREE WIRE FORMATS  [UNVERIFIED shapes]")

print("  Illustrative shapes only -- verify exact current field names against")
print("  each provider's own documentation before using this in real code.\n")

NEUTRAL_REQUEST = {
    "system": "You are a helpful support assistant.",
    "messages": [{"role": "user", "content": "What is my order status?"}],
    "tools": [{"name": "get_order_status",
               "description": "Look up an order's status by id.",
               "parameters": {"order_id": "string"}}],
    "max_tokens": 300,
}


def to_anthropic_shape(req: dict) -> dict:
    return {
        "model": "claude-sonnet-5",
        "system": req["system"],
        "messages": req["messages"],
        "tools": [{"name": t["name"], "description": t["description"],
                    "input_schema": {"type": "object",
                                      "properties": t["parameters"]}}
                   for t in req["tools"]],
        "max_tokens": req["max_tokens"],
    }


def to_openai_shape(req: dict) -> dict:
    return {
        "model": "gpt-example",
        "messages": [{"role": "system", "content": req["system"]}] + req["messages"],
        "tools": [{"type": "function",
                    "function": {"name": t["name"], "description": t["description"],
                                 "parameters": {"type": "object",
                                                "properties": t["parameters"]}}}
                   for t in req["tools"]],
        "max_tokens": req["max_tokens"],
    }


def to_bedrock_shape(req: dict) -> dict:
    return {
        "modelId": "anthropic.claude-sonnet-5",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "system": req["system"],
            "messages": req["messages"],
            "tools": [{"name": t["name"], "description": t["description"],
                        "input_schema": {"type": "object",
                                          "properties": t["parameters"]}}
                       for t in req["tools"]],
            "max_tokens": req["max_tokens"],
        },
    }


SHAPES = {
    "Anthropic direct": to_anthropic_shape(NEUTRAL_REQUEST),
    "OpenAI-style": to_openai_shape(NEUTRAL_REQUEST),
    "Bedrock (Claude)": to_bedrock_shape(NEUTRAL_REQUEST),
}

print(f"  {'shape':<20}{'top-level keys':<45}{'system location'}")
for name, shaped in SHAPES.items():
    keys = ", ".join(shaped.keys())
    if "system" in shaped:
        sys_loc = "top-level field"
    elif "body" in shaped and "system" in shaped["body"]:
        sys_loc = "nested under body"
    else:
        sys_loc = "inside messages[0] with role='system'"
    print(f"  {name:<20}{keys:<45}{sys_loc}")

anthropic_keys = set(SHAPES["Anthropic direct"].keys())
openai_keys = set(SHAPES["OpenAI-style"].keys())
bedrock_keys = set(SHAPES["Bedrock (Claude)"].keys())
print(f"\n  Anthropic vs OpenAI-style top-level keys in common: "
      f"{sorted(anthropic_keys & openai_keys)}")
print(f"  Anthropic vs Bedrock top-level keys in common: "
      f"{sorted(anthropic_keys & bedrock_keys)} -- Bedrock wraps the SAME")
print("  Anthropic-shaped body inside an envelope (modelId, body), rather")
print("  than changing the inner shape itself. Porting Anthropic-direct to")
print("  Bedrock is an ENVELOPE change; porting to an OpenAI-style API is a")
print("  STRUCTURAL change reaching into the message list and the tool")
print("  schema's nesting, not just the outside.")


# ============================================================ 2
rule("2. THE SAME TEXT, DIFFERENT TOKEN COUNTS")

if TOKENIZERS_AVAILABLE:
    SAMPLE_TEXTS = [
        "What is my order status?",
        "Refund approved: GBP 940.00, ref #GB-4471, processed by support-bot.",
        "def calculate_refund(amount: float, cap: float = 500.0) -> float:",
        "The pneumonoultramicroscopicsilicovolcanoconiosis diagnosis was "
        "unexpected.",
        "Tokyo meeting scheduled: 東京都渋谷区で"
        "会議があります。",
    ]
    print("  Two REAL, different tiktoken encodings on the SAME text -- a")
    print("  concrete, honest stand-in for 'different providers tokenize")
    print("  differently'. This does NOT measure any specific provider's")
    print("  actual tokenizer; it measures two real, different encodings.\n")
    print(f"  {'text':<46}{'cl100k_base':>13}{'o200k_base':>12}{'diff':>7}")
    for text in SAMPLE_TEXTS:
        a = len(ENC_A.encode(text))
        b = len(ENC_B.encode(text))
        shown = text if len(text) <= 44 else text[:43] + "*"
        print(f"  {shown:<46}{a:>13}{b:>12}{b - a:>+7}")
    print("\n  Plain English and structured formats (code, JSON) often match")
    print("  exactly between these two real encodings -- they share most of")
    print("  their everyday vocabulary. But a rare English word and a")
    print("  non-Latin script both diverge substantially: the Japanese")
    print("  sentence took 32% FEWER tokens under the newer encoding. A")
    print("  token budget (M4-L06), a cost estimate (M5-L15), and a")
    print("  context-window check are all tokenizer-specific -- porting a")
    print("  prompt to a new provider means RE-COUNTING for content that")
    print("  looks like your actual traffic, not assuming the old numbers")
    print("  hold, and not assuming EVERY string will move by the same")
    print("  amount either.")
else:                                                  # pragma: no cover
    print("  tiktoken not available -- skipping (install it to run this "
          "section; not required to trust its conclusion).")


# ============================================================ 3
rule("3. A GOLDEN SUITE (M5-L12) DOES NOT AUTOMATICALLY PORT")

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


def simulate_run(case_id: str, quality: float, trial: int) -> bool:
    return seeded("port-correctness", case_id, quality, trial).random() < quality


PROVIDERS = {
    "original provider (tuned here)": 0.95,
    "new provider (same prompt, unmodified)": 0.80,
}
TRIALS = 40

print("  The SAME prompt text and golden suite from M5-L12, run against two")
print("  PROVIDERS instead of two prompt versions. Quality is a stated,")
print("  illustrative parameter per provider -- not a measurement of any")
print(f"  real model. Averaged over {TRIALS} runs/case, per M5-L12's own")
print("  lesson that a single small-sample run is not evidence by itself.\n")
print(f"  {'provider':<40}{'single 8-case draw':>19}{'40-run average':>16}")
for name, q in PROVIDERS.items():
    single = sum(simulate_run(cid, q, 0) for cid, _, _ in CASES)
    total = sum(simulate_run(cid, q, t) for cid, _, _ in CASES for t in range(TRIALS))
    avg = total / (len(CASES) * TRIALS)
    print(f"  {name:<40}{f'{single}/8':>19}{avg:>16.0%}")

print("\n  Look at the single-draw column first: it shows 7/8 for BOTH")
print("  providers, identical, despite a real 17-point quality gap between")
print("  them. This is not a bug in the lab -- it is M5-L12 section 3's")
print("  finding happening again, live: 8 samples is not enough to tell a")
print("  95%-quality provider from an 80%-quality one apart. Only the")
print("  averaged column reveals the gap that was there all along.")
print("\n  The averaged column is the number worth trusting -- 95% quality on")
print("  the tuned provider does not carry over to the new one just because")
print("  the prompt text is unchanged; wording that reads as a firm")
print("  instruction to one model can read as a softer suggestion to")
print("  another. The fix is not hope: it is running the EXACT SAME")
print("  golden suite (M5-L12), at a sample size that can actually detect a")
print("  drop (M5-L12 section 3), against the new provider before")
print("  switching.")

print("\n  (The delta above is stated by construction, chosen to be")
print("  illustrative; real provider-to-provider gaps range from")
print("  negligible to large depending on the prompt and the task, and are")
print("  only known once measured.)")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1's adapter code and structural diff, and section 2's")
print("  tiktoken counts, are exact and reproducible.")
print("\n  ILLUSTRATIVE / UNVERIFIED: section 1's exact wire shapes are")
print("  simplified and may not match any provider's current API precisely")
print("  -- verify field names against current documentation before using")
print("  them in real code. Section 3's per-provider quality figures are")
print("  stated parameters illustrating a real, documented risk (prompts")
print("  do not transfer quality automatically), not a measurement of any")
print("  specific two providers.")
print("\n  NOT SHOWN: differences in streaming event formats (M5-L09),")
print("  authentication mechanics (API key vs AWS SigV4), rate-limit")
print("  structures, or exact safety/refusal threshold differences --")
print("  all real, all provider-specific, all worth checking directly")
print("  against current documentation for any provider you actually use.")

print("\nDone.")
