"""M5-L10 lab -- conversation state: what you resend, and what it costs.

The model is stateless (M4-L16). Every turn resends the whole conversation, so
a chat's cost is quadratic in its length while its value is not. This lab
measures that exactly -- it is arithmetic, not simulation -- and then measures
what four different state strategies actually preserve.

Sections 1-3 and 5 are REAL: token accounting on real text with a real
tokenizer where available, and exact arithmetic. Section 4 uses a mock to score
what information survives each strategy.

Deterministic (zlib.crc32). No API key, no network.
Run:  python labs/m5/l10_conversation_state.py
"""

from __future__ import annotations

import math
import zlib

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


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


# ============================================================ 1
rule("1. THE COST OF A CONVERSATION IS QUADRATIC")

print(f"  Tokenizer: {TOKENIZER}\n")
SYSTEM = 320          # tokens of system prompt + tool definitions
USER_TURN = 60
ASSISTANT_TURN = 140
IN_P, OUT_P = 0.50 / 1e6, 2.00 / 1e6      # ILLUSTRATIVE, dated 2026-09-09

print(f"  system + tools {SYSTEM} tok, user turn {USER_TURN} tok,")
print(f"  assistant turn {ASSISTANT_TURN} tok, ${IN_P * 1e6:.2f}/M in "
      f"${OUT_P * 1e6:.2f}/M out  [ILLUSTRATIVE]\n")
print(f"  {'turn':>6}{'input tokens':>14}{'output':>9}{'cost this turn':>16}"
      f"{'cumulative':>13}{'cost vs t1':>12}")
cum = 0.0
first = None
for turn in (1, 2, 5, 10, 20, 40, 80):
    hist = (turn - 1) * (USER_TURN + ASSISTANT_TURN)
    inp = SYSTEM + hist + USER_TURN
    cost = inp * IN_P + ASSISTANT_TURN * OUT_P
    if first is None:
        first = cost
    # cumulative over ALL turns up to here, not just the sampled ones
    total = 0.0
    for t in range(1, turn + 1):
        h = (t - 1) * (USER_TURN + ASSISTANT_TURN)
        total += (SYSTEM + h + USER_TURN) * IN_P + ASSISTANT_TURN * OUT_P
    print(f"  {turn:>6}{inp:>14,}{ASSISTANT_TURN:>9}"
          f"{f'${cost:.5f}':>16}{f'${total:.4f}':>13}{cost / first:>11.1f}x")

print("\n  Turn 80's INPUT is "
      f"{(SYSTEM + 79 * (USER_TURN + ASSISTANT_TURN) + USER_TURN) / (SYSTEM + USER_TURN):.1f}x "
      "the input of turn 1 -- for a message")
print("  the user would say is no more valuable than their first one.")
print("\n  The mechanism is simple and worth stating precisely: each turn adds")
print("  a fixed amount to the history, and every LATER turn pays for it")
print("  again. n turns cost O(n^2) tokens in total.")

n = 80
quad = sum(SYSTEM + (t - 1) * (USER_TURN + ASSISTANT_TURN) + USER_TURN
           for t in range(1, n + 1))
linear = n * (SYSTEM + USER_TURN)
print(f"\n  An {n}-turn conversation: {quad:,} input tokens sent in total.")
print(f"  If the model had memory and you sent only the new turn: "
      f"{linear:,}.")
print(f"  Ratio: {quad / linear:.1f}x. That factor is what statelessness costs.")


# ============================================================ 2
rule("2. WHERE THE TOKENS ACTUALLY GO")

TURNS = [
    ("user", "My order GB-4471 arrived damaged, the screen is cracked."),
    ("assistant", "I'm sorry to hear that. I can see order GB-4471, "
                  "delivered on 3 March. I can arrange a replacement or a "
                  "refund. Which would you prefer?"),
    ("user", "A refund please."),
    ("assistant", "Of course. I've noted a refund request for GB-4471. "
                  "Could you confirm the payment card ending in 4412 is "
                  "still the right one?"),
    ("user", "Yes that's right."),
    ("assistant", "Thank you. The refund of 42.50 GBP to the card ending "
                  "4412 has been requested and will be processed within "
                  "3-5 working days. Is there anything else?"),
    ("user", "No that's all, thanks."),
    ("assistant", "You're very welcome. I've emailed a confirmation to the "
                  "address on your account. Have a good day."),
]

print("  A real eight-turn support conversation, tokenized.\n")
print(f"  {'#':>3}  {'role':<11}{'tokens':>7}   {'text':<48}")
total = 0
for i, (role, text) in enumerate(TURNS, 1):
    t = ntok(text)
    total += t
    shown = text if len(text) <= 46 else text[:45] + "…"
    print(f"  {i:>3}  {role:<11}{t:>7}   {shown:<48}")
print(f"  {'':>3}  {'TOTAL':<11}{total:>7}")

FACTS = ["GB-4471", "damaged", "refund", "4412", "42.50"]
print(f"\n  The facts a later turn actually needs: {', '.join(FACTS)}")
fact_str = "order GB-4471 damaged; refund agreed; card 4412; amount 42.50 GBP"
print(f"  As a state record: {fact_str!r}")
print(f"  {ntok(fact_str)} tokens vs {total} -- "
      f"{total / max(ntok(fact_str), 1):.1f}x smaller.\n")
print("  That ratio is the whole opportunity, and also the whole risk: the")
print("  compressed version is a LOSSY summary you wrote, and everything it")
print("  omits is gone for good.")


# ============================================================ 3
rule("3. FOUR STRATEGIES, PRICED")

BUDGET = 4000
print(f"  A {BUDGET:,}-token context budget for history, "
      f"{USER_TURN + ASSISTANT_TURN} tokens per exchange.\n")
print(f"  {'strategy':<26}{'turns kept at turn 40':>23}"
      f"{'input tok, turn 40':>21}")
per_exchange = USER_TURN + ASSISTANT_TURN
strategies = {
    "send everything": min(39, 10_000),
    "last N (N=6)": 6,
    "summary + last 4": 4,
    "structured state + last 2": 2,
}
SUMMARY_TOK = 90
STATE_TOK = 35
for name, kept in strategies.items():
    hist = kept * per_exchange
    extra = (SUMMARY_TOK if "summary" in name else
             STATE_TOK if "state" in name else 0)
    inp = SYSTEM + hist + extra + USER_TURN
    over = "  OVER BUDGET" if hist > BUDGET else ""
    print(f"  {name:<26}{kept:>23}{inp:>21,}{over}")

print(f"\n  {'strategy':<26}{'cost/turn at 40':>18}{'vs everything':>16}")
base_inp = SYSTEM + 39 * per_exchange + USER_TURN
base_cost = base_inp * IN_P + ASSISTANT_TURN * OUT_P
for name, kept in strategies.items():
    extra = (SUMMARY_TOK if "summary" in name else
             STATE_TOK if "state" in name else 0)
    inp = SYSTEM + kept * per_exchange + extra + USER_TURN
    cost = inp * IN_P + ASSISTANT_TURN * OUT_P
    print(f"  {name:<26}{f'${cost:.5f}':>18}{cost / base_cost:>15.0%}")

print("\n  Cost is not the interesting column. Section 4 is.")


# ============================================================ 4
rule("4. WHAT EACH STRATEGY LOSES  [MOCK]")

print("  Twelve questions a user might ask at turn 40, each needing a fact")
print("  from a particular earlier turn. Can the strategy still answer?\n")

# Facts by the turn they were established. Recency is what most strategies keep.
QUESTIONS = [
    ("what is my order number?", 1, True),
    ("what was wrong with it?", 1, True),
    ("did I ask for a refund or a replacement?", 3, True),
    ("which card?", 5, True),
    ("how much?", 6, True),
    ("what did you say the delivery date was?", 2, False),
    ("did I mention I'd already contacted you once?", 8, False),
    ("what was the exact wording I used?", 1, False),
    ("what did I say about the packaging?", 12, False),
    ("what was the second option you offered?", 2, False),
    ("did I agree to the email confirmation?", 30, True),
    ("what did we just decide?", 39, True),
]

def survives(strategy: str, turn: int, in_summary: bool) -> bool:
    if strategy == "send everything":
        return True
    if strategy == "last N (N=6)":
        return turn >= 40 - 6
    if strategy == "summary + last 4":
        return turn >= 36 or in_summary
    if strategy == "structured state + last 2":
        return turn >= 38 or in_summary
    return False

print(f"  {'question':<42}{'all':>6}{'lastN':>7}{'summ':>7}{'state':>7}")
scores = {s: 0 for s in strategies}
for q, turn, in_summary in QUESTIONS:
    row = f"  {(q if len(q) <= 42 else q[:41] + chr(8230)):<42}"
    for s in strategies:
        ok = survives(s, turn, in_summary)
        scores[s] += ok
        row += f"{'yes' if ok else '--':>6}" if s == "send everything" \
            else f"{'yes' if ok else '--':>7}"
    print(row)

print(f"\n  {'':<42}{scores['send everything']:>6}"
      f"{scores['last N (N=6)']:>7}{scores['summary + last 4']:>7}"
      f"{scores['structured state + last 2']:>7}  of "
      f"{len(QUESTIONS)}")

print("\n  Read the rows that fail for 'summ' and 'state' but not for 'all'.")
print("  Every one of them is a detail nobody thought to put in the summary:")
print("  the exact wording, the second option offered, an offhand remark 28")
print("  turns ago. They are unanswerable now, and the model will not say so")
print("  -- it will answer from what it has, confidently.")
print("\n  THAT is the real cost of compression, and it is not a cost you")
print("  can see in a token count. You chose what to forget when you wrote")
print("  the summary prompt, weeks before the user asked.")

print("\n  Note that 'structured state' scores the same as 'summary' here but")
print("  fails DIFFERENTLY: its omissions are predictable, because the schema")
print("  says exactly which fields exist. A prose summary's omissions are")
print("  whatever the summarizer felt like leaving out this time.")


# ============================================================ 5
rule("5. WHAT YOU STORE IS NOT WHAT YOU SEND")

print("  Two different questions, constantly conflated:\n")
print("    STORE  -- what your database keeps, for audit, support, analytics")
print("    SEND   -- what goes in the next request's context\n")
print(f"  {'concern':<24}{'store':<28}{'send':<24}")
for concern, store, send in (
        ("full transcript", "yes, with retention policy", "no"),
        ("structured state", "yes, it is the record", "yes"),
        ("summaries", "yes, and version them", "yes"),
        ("tool call arguments", "names + outcomes only", "yes, current turn"),
        ("PII in messages", "only if lawful basis", "minimise"),
        ("deleted-account data", "must be erasable", "n/a"),
):
    print(f"  {concern:<24}{store:<28}{send:<24}")

print("\n  Three consequences people discover late:\n")
print("  1. A deletion request must reach the SUMMARY too. A summary derived")
print("     from a deleted message still contains it (M10-L06).")
print("  2. A summary is a derived artefact and must be versioned with the")
print("     prompt that produced it. Otherwise you cannot reproduce a")
print("     conversation, and you cannot explain one (M5-L12).")
print("  3. Context is not memory. Two users in the same session, a shared")
print("     inbox, a support agent taking over -- all of these put one")
print("     person's data in another's context if state is keyed loosely.")

print("\n  And the failure mode nobody tests for:\n")
leak_turns = 40
avg_sends = (leak_turns + 1) / 2
print(f"  In a {leak_turns}-turn conversation resent in full every turn, the")
print(f"  FIRST message is transmitted {leak_turns} times and the last once --")
print(f"  {avg_sends:.1f} times on average across the conversation.")
print("\n  If turn 3 contained a card number the user typed by mistake, it has")
print(f"  gone to the provider {leak_turns - 3 + 1} times. Redacting it from your")
print("  database does not unsend those, and a retention clock that starts")
print("  when you store it started 37 transmissions too late.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print(f"  REAL: sections 1, 2, 3 and 5. Token counts come from")
print(f"  {TOKENIZER}; the cost tables are arithmetic on stated inputs.")
print("\n  MOCK: section 4's survival rules are a simplification -- 'the last")
print("  N turns, plus whatever a summary happens to contain'. Real")
print("  summarizers keep and drop things less predictably than that, which")
print("  makes the real picture WORSE, not better.")
print("\n  NOT SHOWN: whether a model actually uses a fact that IS present in")
print("  its context. Presence is necessary, not sufficient -- retrieval")
print("  from a long context is its own failure mode (M4-L06, M7-L11).")

print("\nDone.")
