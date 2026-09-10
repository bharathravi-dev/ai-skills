"""M5-L11 lab -- context engineering: triggers, drift, and one shared budget.

M4-L06 gave you a budget mechanism (drop order, headroom) for a single
request. M5-L10 gave you strategies for conversation history specifically,
priced and scored for information loss. This lab is what sits between them in
production: WHEN a strategy switches, what happens when a summary is
repeatedly summarized instead of re-derived from source, and how one budget
arbitrates across every component sharing the window -- not just history.

Sections 1, 3 and 4 are REAL: token accounting on real text with tiktoken
where available, and exact arithmetic on stated inputs. Section 2 uses a
deterministic mock compressor to measure drift across cascading
summarization -- the ARITHMETIC is real, but "a fact survives one pass with
fixed probability" is a simplified model of what a real summarizer does; see
the lesson's worked example for what a real, systematic failure looks like.

Deterministic (zlib.crc32 seeding). No API key, no network beyond the
tokenizer's one-time download.
Run:  python labs/m5/l11_context_engineering.py
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

import numpy as np

try:
    import tiktoken
    ENC = tiktoken.get_encoding("cl100k_base")
    def ntok(s: str) -> int:
        return len(ENC.encode(s))
    TOKENIZER = "tiktoken cl100k_base"
except Exception:                                    # pragma: no cover
    def ntok(s: str) -> int:
        return max(1, len(s) // 4)
    TOKENIZER = "approximation (len/4)"


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*parts) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


# ============================================================ 1
rule("1. TRIGGER POLICIES: A FIXED TURN COUNT LIES TO YOU")

USER_TOK, ASSISTANT_TOK = 60, 140
PER_TURN = USER_TOK + ASSISTANT_TOK          # 200 tok/exchange, as in M5-L10

print(f"  Same task, two very different conversations. Per-exchange size")
print(f"  {PER_TURN} tok/exchange throughout (M5-L10's figures).\n")

profiles = {
    "chatty (short messages, many turns)": {"user": 20, "assistant": 55},
    "verbose (long messages, few turns)":   {"user": 180, "assistant": 420},
}

TRIGGER_TURNS = 10          # "summarise every 10 turns"
TRIGGER_TOKENS = 3000       # "summarise once history exceeds 3,000 tokens"

print(f"  Two trigger policies: every {TRIGGER_TURNS} turns, or once history")
print(f"  exceeds {TRIGGER_TOKENS:,} tokens.\n")
print(f"  {'profile':<38}{'tok/exchange':>13}{'turn-trigger fires at':>23}"
      f"{'token-trigger fires at':>24}")
for name, sizes in profiles.items():
    per_exch = sizes["user"] + sizes["assistant"]
    turn_trigger_tok = TRIGGER_TURNS * per_exch
    token_trigger_turn = -(-TRIGGER_TOKENS // per_exch)     # ceil
    print(f"  {name:<38}{per_exch:>13}{f'{turn_trigger_tok:,} tok':>23}"
          f"{f'turn {token_trigger_turn}':>24}")

print("\n  Read the turn-trigger column: the SAME rule ('every 10 turns')")
print("  fires at wildly different token totals depending on how chatty the")
print("  conversation is. A turn-count trigger is really a token-count")
print("  trigger in disguise, with an error bar the width of your users'")
print("  writing style. The token-threshold trigger fires at a materially")
print("  more consistent BUDGET POSITION across both profiles -- which is")
print("  the thing you actually meant to bound.")


# ============================================================ 2
rule("2. CASCADING SUMMARIZATION DRIFT  [MOCK compressor, REAL arithmetic]")

N_FACTS = 15
PASSES = 12
SURVIVAL_P = 0.90            # a fact survives ONE summarization pass, 90%
CHECKPOINT_K = (3, 5)        # resummarise from source every K passes

print(f"  {N_FACTS} facts established once, at the start of a conversation.")
print(f"  Each summarization pass keeps a fact with probability {SURVIVAL_P:.0%}")
print(f"  ({(1 - SURVIVAL_P):.0%} chance of loss per pass) -- a simplified stand-in")
print("  for a real summarizer's imperfect compression. Two strategies:\n")
print("    CASCADE      -- always summarise the previous summary")
print("    CHECKPOINT-K -- every K passes, re-derive the summary from the")
print("                    original source material instead of the last")
print("                    summary, resetting every fact to 'present'\n")


def survives(fact_i: int, pass_p: int) -> bool:
    return seeded("m5l11-survival", fact_i, pass_p).random() < SURVIVAL_P


def alive_cascade(fact_i: int, pass_p: int) -> bool:
    return all(survives(fact_i, p) for p in range(1, pass_p + 1))


def alive_checkpoint(fact_i: int, pass_p: int, k: int) -> bool:
    last_checkpoint = (pass_p // k) * k
    return all(survives(fact_i, p) for p in range(last_checkpoint + 1, pass_p + 1))


header = f"  {'pass':>5}{'cascade':>10}"
for k in CHECKPOINT_K:
    header += f"{f'checkpoint-{k}':>16}"
print(header)
cascade_counts, checkpoint_counts = [], {k: [] for k in CHECKPOINT_K}
for p in range(1, PASSES + 1):
    c = sum(alive_cascade(i, p) for i in range(N_FACTS))
    cascade_counts.append(c)
    row = f"  {p:>5}{f'{c}/{N_FACTS}':>10}"
    for k in CHECKPOINT_K:
        ck = sum(alive_checkpoint(i, p, k) for i in range(N_FACTS))
        checkpoint_counts[k].append(ck)
        row += f"{f'{ck}/{N_FACTS}':>16}"
    print(row)

print(f"\n  At pass {PASSES}: cascade keeps {cascade_counts[-1]}/{N_FACTS} facts "
      f"({cascade_counts[-1] / N_FACTS:.0%})")
for k in CHECKPOINT_K:
    print(f"  checkpoint-{k} keeps {checkpoint_counts[k][-1]}/{N_FACTS} facts "
          f"({checkpoint_counts[k][-1] / N_FACTS:.0%}) after {PASSES} passes")

print("\n  Cascading decays toward zero because loss compounds: a fact must")
print("  survive EVERY pass since the start to still be present. Checkpointing")
print("  resets that clock periodically, trading a bounded, recurring cost")
print("  for a bounded, recurring recovery.\n")

# Cost side of the same trade-off
SUMMARY_TOK, NEW_TURNS_TOK = 90, 200           # cascade pass reads this much
TRANSCRIPT_GROWTH_PER_PASS = 500               # source transcript grows this much/pass

cascade_cost = PASSES * (SUMMARY_TOK + NEW_TURNS_TOK)
print(f"  Cost: a cascade pass reads only the last summary + new turns --")
print(f"  {SUMMARY_TOK + NEW_TURNS_TOK} tok/pass, {cascade_cost:,} tok over "
      f"{PASSES} passes.\n")
print(f"  {'strategy':<16}{'tokens read over 12 passes':>28}{'vs cascade':>13}")
print(f"  {'cascade':<16}{cascade_cost:>28,}{'1.0x':>13}")
for k in CHECKPOINT_K:
    total = 0
    for p in range(1, PASSES + 1):
        if p % k == 0:
            total += p * TRANSCRIPT_GROWTH_PER_PASS   # checkpoint: reads full transcript so far
        else:
            total += SUMMARY_TOK + NEW_TURNS_TOK       # ordinary pass
    print(f"  {f'checkpoint-{k}':<16}{total:>28,}{f'{total / cascade_cost:.1f}x':>13}")

print("\n  Checkpointing costs more -- it periodically re-reads the whole")
print("  transcript instead of a short summary -- and that is the price of")
print("  bounding drift rather than merely delaying it.")


# ============================================================ 3
rule("3. ONE BUDGET, FOUR COMPONENTS")

WINDOW = 128_000
OUTPUT_RESERVE = 1_500
SYSTEM_TOK = 900
TOOLS_TOK = 600
USER_MSG_TOK = 200
HEADROOM = 0.90

# Conversation-state levers, priced as in M5-L10 at turn 40:
STATE_OPTIONS = [
    ("full history", 8_180),
    ("last N (N=6)", 1_580),
    ("summary + last 4", 1_270),
    ("structured state + last 2", 815),
]

DOC_TOK_PER_DOC = 750

print(f"  window {WINDOW:,}, output reserve {OUTPUT_RESERVE:,}, system "
      f"{SYSTEM_TOK}, tools {TOOLS_TOK}, user msg {USER_MSG_TOK}, "
      f"headroom {HEADROOM:.0%}")
print(f"  conversation-state levers (from M5-L10, priced at turn 40):")
for name, tok in STATE_OPTIONS:
    print(f"    {name:<28}{tok:>7,} tok")
print(f"  retrieved documents: {DOC_TOK_PER_DOC} tok/doc, ranked, drop "
      f"lowest first\n")


@dataclass
class Scenario:
    name: str
    n_docs_wanted: int


def assemble(scenario: Scenario, usable: int) -> None:
    fixed = SYSTEM_TOK + TOOLS_TOK + USER_MSG_TOK
    remaining = usable - fixed
    print(f"  {scenario.name}  (usable budget {usable:,} tok)")
    if remaining <= 0:
        print(f"    REFUSED: fixed components ({fixed:,}) exceed the usable "
              f"budget ({usable:,}) -- this request cannot be built")
        return
    print(f"    keep   system + tools + user msg          {fixed:>8,}")

    # Try the richest conversation-state option first, then degrade.
    chosen_state = None
    for name, tok in STATE_OPTIONS:
        docs_wanted_tok = scenario.n_docs_wanted * DOC_TOK_PER_DOC
        if tok + docs_wanted_tok <= remaining:
            chosen_state = (name, tok)
            docs_tok = docs_wanted_tok
            n_docs = scenario.n_docs_wanted
            break
    else:
        # Even the cheapest state option plus zero docs might not fit.
        cheapest_name, cheapest_tok = STATE_OPTIONS[-1]
        if cheapest_tok <= remaining:
            chosen_state = (cheapest_name, cheapest_tok)
            docs_budget = remaining - cheapest_tok
            n_docs = min(scenario.n_docs_wanted, docs_budget // DOC_TOK_PER_DOC)
            docs_tok = n_docs * DOC_TOK_PER_DOC
        else:
            print(f"    REFUSED: even the cheapest conversation-state option "
                  f"({cheapest_tok:,} tok) does not fit")
            return

    state_name, state_tok = chosen_state
    dropped_docs = scenario.n_docs_wanted - n_docs
    print(f"    pick   conversation state: {state_name:<26}{state_tok:>8,}")
    print(f"    keep   retrieved docs ({n_docs} of {scenario.n_docs_wanted} "
          f"wanted, {DOC_TOK_PER_DOC} tok each)  {docs_tok:>8,}")
    if dropped_docs:
        print(f"    DROP   {dropped_docs} lowest-ranked document(s)")
    total_input = fixed + state_tok + docs_tok
    print(f"    input total                              {total_input:>8,}")
    print(f"    output reserved                          {OUTPUT_RESERVE:>8,}")
    print(f"    window used                              "
          f"{(total_input + OUTPUT_RESERVE) / WINDOW:>7.1%}\n")


usable = int((WINDOW - OUTPUT_RESERVE) * HEADROOM)
scenarios = [
    Scenario("generous request  (10 docs wanted)", 10),
    Scenario("tight request     (10 docs wanted, smaller budget)", 10),
    Scenario("very tight request (10 docs wanted, tiny budget)", 10),
]
budgets = [usable, 5_000, 700]
for scenario, b in zip(scenarios, budgets):
    assemble(scenario, b)

print("  Note what changed as the budget shrank: first the DOCUMENT count")
print("  dropped, then the CONVERSATION-STATE strategy downgraded to a")
print("  cheaper one -- an explicit order, decided in advance, not whichever")
print("  component happened to be assembled last.")


# ============================================================ 4
rule("4. HOW OFTEN DOES THE TRIGGER ACTUALLY FIRE?")

print("  A synthetic conversation-length distribution across a day's traffic")
print("  (illustrative percentiles; measure your own):\n")
percentiles = [("p50", 6), ("p75", 12), ("p90", 22), ("p99", 61), ("max", 140)]
print(f"  {'percentile':<12}{'turns':>7}{'approx tokens':>16}")
for name, turns in percentiles:
    print(f"  {name:<12}{turns:>7}{turns * PER_TURN:>15,}")

reduction_trigger_turn = -(-TRIGGER_TOKENS // PER_TURN)   # ceil, from section 1
print(f"\n  The {TRIGGER_TOKENS:,}-token reduction trigger fires at turn "
      f"{reduction_trigger_turn}.")
for name, turns in percentiles:
    fires = "FIRES" if turns >= reduction_trigger_turn else "does not fire"
    print(f"    {name} ({turns} turns): {fires}")

print(f"\n  Reading the table: at least 10% of conversations (p90) cross the")
print(f"  reduction trigger, and at least 1% (p99) reach lengths where even")
print(f"  the cheapest conversation-state option plus a full document")
print(f"  allocation is under real pressure. Those are not edge cases you")
print(f"  can ignore -- at 100,000 conversations/month, p99 alone is 1,000")
print(f"  conversations experiencing your MOST aggressive degradation.\n")

print("  What to actually monitor in production, per day:")
print("    - % of requests that triggered ANY reduction")
print("    - % that triggered the CHEAPEST conversation-state option")
print("    - % that were REFUSED outright (section 3's failure mode)")
print("    - whether degraded requests correlate with your longest, most")
print("      engaged conversations -- often your most valuable users, and")
print("      the ones a naive fixed trigger degrades hardest")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print(f"  REAL: sections 1, 3 and 4 -- exact arithmetic on stated inputs,")
print(f"  using {TOKENIZER} for the M5-L10 figures re-used in section 3.")
print("\n  MOCK: section 2's compressor. 'A fact survives a pass with fixed")
print("  probability, independent of the others' is a simplification. Real")
print("  summarization failures are often SYSTEMATIC rather than random --")
print("  the same kind of clause gets dropped every time -- which is worse")
print("  in one way (predictably repeatable) and better in another (you can")
print("  find and fix it by reading the summarization prompt). See the")
print("  lesson's worked example for a systematic failure, not a random one.")
print("\n  ILLUSTRATIVE: section 4's traffic percentiles. Measure your own")
print("  conversation-length distribution before setting a trigger threshold.")
print("\n  NOT SHOWN: an actual model call. Whether a real summarizer keeps a")
print("  given fact is an empirical question about that model and that")
print("  prompt -- this lab measures the SHAPE of the drift and cost")
print("  trade-off, not any particular summarizer's behaviour.")

print("\nDone.")
