"""M5-L09 lab -- streaming: what breaks, and what you can no longer do.

Almost every section here is REAL: byte-boundary decoding, incremental JSON
parsing, and latency arithmetic. Streaming is one of the few LLM topics where
the hard parts are properties of your own transport code rather than of the
model, so a mock would be beside the point.

Deterministic. No API key, no network.
Run:  python labs/m5/l09_streaming.py
"""

from __future__ import annotations

import codecs
import json
import zlib

import numpy as np


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


# ============================================================ 1
rule("1. CHUNK BOUNDARIES SPLIT CHARACTERS")

TEXT = (
    "Your refund of £42.50 was processed. Grüße aus München — "
    "the café's naïve résumé, 東京より. Status: ✅ complete. "
    "Contact: jose@example.com (José). Fee: €3.20, ¥500, ₹120."
)
RAW = TEXT.encode("utf-8")

print("  A realistic response: currency symbols, accents, CJK, an emoji.\n")
print(f"    {len(TEXT)} characters, {len(RAW)} bytes "
      f"({len(RAW) - len(TEXT)} bytes of multi-byte characters)\n")
print("  Transports deliver BYTES. The chunk boundary falls wherever the")
print("  network puts it -- not on character boundaries.\n")

print(f"  {'chunk size':>11}{'chunks':>9}   {'naive decode':<22}"
      f"{'incremental decode':<20}")
for size in (1, 4, 8, 16, 64, 256):
    chunks = [RAW[i:i + size] for i in range(0, len(RAW), size)]

    naive_ok, naive_out = True, []
    for c in chunks:
        try:
            naive_out.append(c.decode("utf-8"))
        except UnicodeDecodeError:
            naive_ok = False
            break

    dec = codecs.getincrementaldecoder("utf-8")()
    inc_out = "".join(dec.decode(c) for c in chunks) + dec.decode(b"", True)

    naive_res = ("OK" if naive_ok and "".join(naive_out) == TEXT
                 else "UnicodeDecodeError" if not naive_ok else "CORRUPTED")
    inc_res = "OK" if inc_out == TEXT else "CORRUPTED"
    print(f"  {size:>11}{len(chunks):>9}   {naive_res:<22}{inc_res:<20}")

print("\n  The naive version is not merely fragile -- it fails on the FIRST")
print("  multi-byte character whenever the chunk size does not happen to")
print("  align with it. At 64 and 256 bytes it may pass, which is exactly")
print("  how this reaches production: ASCII test data, large chunks, green.")
print("\n  The fix is three lines and belongs in every streaming client:\n")
print('    dec = codecs.getincrementaldecoder("utf-8")()')
print("    for chunk in stream:  text = dec.decode(chunk)")
print('    text += dec.decode(b"", final=True)   # flush at the end')

# and the subtler one: a grapheme cluster split across chunks
FLAG = "Ready 🇬🇧 done"
fb = FLAG.encode("utf-8")
dec = codecs.getincrementaldecoder("utf-8")()
half = "".join(dec.decode(fb[i:i + 5]) for i in range(0, 10, 5))
print(f"\n  Even correct decoding does not give you whole GRAPHEMES. Decoding")
print(f"  the first 10 bytes of {FLAG!r} yields {half!r} --")
print("  a valid string, and half a flag. If you render each chunk as it")
print("  arrives, the user watches characters assemble themselves.")


# ============================================================ 2
rule("2. YOU CANNOT VALIDATE A PARTIAL RESPONSE")

FULL = json.dumps({
    "category": "billing",
    "refund_pence": 4250,
    "urgent": False,
    "reason": "duplicate_charge",
    "evidence": "Charged twice for order GB-4471 on 3 March.",
})

print("  Streaming a JSON response. At each prefix, ask two questions:")
print("  does it parse yet, and can I already tell it will be wrong?\n")
print(f"  response is {len(FULL)} characters\n")
print(f"  {'% received':>11}{'chars':>7}{'parses':>9}{'shown to user':>16}")
first_parse = None
for pct in (10, 25, 50, 75, 90, 99, 100):
    n = max(1, len(FULL) * pct // 100)
    prefix = FULL[:n]
    try:
        json.loads(prefix)
        ok = "yes"
        first_parse = first_parse or pct
    except Exception:
        ok = "no"
    print(f"  {pct:>11}{n:>7}{ok:>9}{n:>16}")

print(f"\n  It first parses at {first_parse}% -- which is to say, at the end.")
print("  A JSON object is not valid until its closing brace, so there is no")
print("  prefix at which you can validate and no prefix at which you can")
print("  safely act.")

print("\n  Now the consequence. Suppose the completed response fails")
print("  validation. How much had the user already seen?\n")

CASES = [
    ("refund over the cap", {"category": "billing", "refund_pence": 999999,
                             "urgent": False, "reason": "other",
                             "evidence": "Customer asked for a large refund."}),
    ("invented category", {"category": "escalation", "refund_pence": 100,
                           "urgent": False, "reason": "other",
                           "evidence": "Customer is unhappy with support."}),
    ("invented field", {"category": "billing", "refund_pence": 100,
                        "urgent": False, "reason": "other",
                        "evidence": "Refund approved.", "approved": True}),
]
print(f"  {'failure':<22}{'bad field appears at':>22}"
      f"{'detectable at':>16}{'shown meanwhile':>18}")
for label, obj in CASES:
    text = json.dumps(obj)
    key = ("refund_pence" if "refund" in label else
           "category" if "category" in label else "approved")
    pos = text.find(f'"{key}"')
    print(f"  {label:<22}{f'char {pos} ({pos * 100 // len(text)}%)':>22}"
          f"{f'char {len(text)} (100%)':>16}"
          f"{f'{len(text) - pos} chars':>18}")

print("\n  The field that makes it invalid arrives EARLY -- but you cannot act")
print("  on that, because a field is only invalid in the context of a schema")
print("  you can only apply to a complete object. So the whole thing streams,")
print("  and then you reject it.")
print("\n  This is the streaming trade, stated exactly:")
print("    you buy perceived latency with the ability to withhold output.")


# ============================================================ 3
rule("3. WHAT STREAMING ACTUALLY BUYS")

print("  Arithmetic, not simulation. TTFT = time to first token.\n")

TTFT = 0.45           # seconds  [ILLUSTRATIVE]
TOK_PER_S = 55.0
READ_TOK_PER_S = 5.0  # a person reads far slower than a model generates

print(f"  TTFT {TTFT}s, generation {TOK_PER_S:.0f} tok/s, "
      f"reading {READ_TOK_PER_S:.0f} tok/s  [ILLUSTRATIVE]\n")
print(f"  {'response':>10}{'total time':>12}{'non-stream wait':>17}"
      f"{'stream wait':>13}{'improvement':>13}{'reading time':>14}")
for tok in (20, 60, 150, 400, 1200):
    total = TTFT + tok / TOK_PER_S
    read = tok / READ_TOK_PER_S
    print(f"  {tok:>10}{total:>11.2f}s{total:>16.2f}s{TTFT:>12.2f}s"
          f"{total - TTFT:>12.2f}s{read:>13.1f}s")

print("\n  Two readings of that table.\n")
print("  1. Streaming does not make anything faster. Total time is identical.")
print("     It moves the wait from BEFORE the first word to BETWEEN words.")
print("  2. The value depends entirely on length. At 20 tokens the user waits")
print("     0.81s instead of 0.45s -- a difference nobody notices, for which")
print("     you accepted every complication in this lab. At 1,200 tokens the")
print("     wait falls from 22s to 0.45s, and that is transformative.")
print("\n  And note the last column: at 55 tok/s the model outruns the reader")
print("  by 11x. Past a few hundred tokens the user is reading, not waiting,")
print("  so further generation speed buys nothing at all.")


# ============================================================ 4
rule("4. THE RETRACTION PROBLEM")

print("  Three things you can do when a streamed response turns out bad.\n")

SCENARIOS = [
    ("validation failed at the end", 100),
    ("moderation flagged it at the end", 100),
    ("tool call was not permitted", 100),
    ("the model contradicted itself midway", 60),
]
print(f"  {'what went wrong':<38}{'% already shown':>17}{'options':>18}")
for label, shown in SCENARIOS:
    print(f"  {label:<38}{shown:>16}%{'retract/append':>18}")

print("\n  'Retract' means removing text the user has already read. It is")
print("  visible, it looks like a malfunction, and on a shared screen or a")
print("  screenshot it is not retractable at all.")
print("\n  The three honest designs:\n")
print(f"  {'design':<28}{'streams':<24}{'safe for':<26}")
print(f"  {'stream everything':<28}{'all output':<24}"
      f"{'low-stakes prose':<26}")
print(f"  {'stream prose, buffer JSON':<28}{'the explanation only':<24}"
      f"{'most applications':<26}")
print(f"  {'buffer everything':<28}{'nothing':<24}"
      f"{'decisions, money, actions':<26}")

print("\n  The middle row is the one to reach for: a two-part response where")
print("  the human-readable part streams and the machine-readable part does")
print("  not. The user sees progress; your code still validates before")
print("  anything is acted on.")
print("\n  What you must NOT do is stream a tool call. By the time you have")
print("  seen enough of it to know what it does, you have shown the user an")
print("  action you may be about to refuse (M5-L08).")


# ============================================================ 5
rule("5. ACCOUNTING AND FAILURE, MID-STREAM")

print("  A stream that dies at 60% has still consumed everything generated")
print("  so far, and most providers report usage only in the final event.\n")

REQ = 100_000
FAIL_RATE = 0.02
IN_TOK, OUT_TOK = 800, 400
IN_P, OUT_P = 0.50 / 1e6, 2.00 / 1e6      # ILLUSTRATIVE
full = IN_TOK * IN_P + OUT_TOK * OUT_P
partial = IN_TOK * IN_P + 0.6 * OUT_TOK * OUT_P

print(f"  {REQ:,} requests, {FAIL_RATE:.0%} of streams break at 60%  "
      f"[ILLUSTRATIVE]\n")
print(f"  {'':<34}{'requests':>12}{'$/month':>11}{'counted?':>12}")
ok_n = int(REQ * (1 - FAIL_RATE))
bad_n = REQ - ok_n
print(f"  {'completed streams':<34}{ok_n:>12,}"
      f"{f'${ok_n * full:,.0f}':>11}{'yes':>12}")
print(f"  {'broken streams (still billed)':<34}{bad_n:>12,}"
      f"{f'${bad_n * partial:,.0f}':>11}{'NO':>12}")
uncounted = bad_n * partial
total = ok_n * full + uncounted
print(f"\n  ${uncounted:,.0f}/month never reaches your usage metrics, because")
print(f"  the usage event never arrived -- {uncounted / total:.1%} of spend.")
print("  At this failure rate that is small, and the SIZE is not the point:")
print("  the error is one-directional. Your dashboard always under-reports,")
print("  never over-reports, so the gap is invisible until the invoice.\n")
print(f"  {'stream failure rate':>21}{'uncounted $/mo':>17}"
      f"{'share of spend':>17}")
for fr in (0.02, 0.10, 0.25, 0.50):
    n_bad = int(REQ * fr)
    n_ok = REQ - n_bad
    unc = n_bad * partial
    print(f"  {fr:>21.0%}{f'${unc:,.0f}':>17}"
          f"{unc / (n_ok * full + unc):>17.1%}")
print("\n  A 25% failure rate is not hypothetical for long streams over")
print("  mobile connections, and there the gap is material.")
print("\n  Fix: count what you RECEIVED, not what the provider told you at the")
print("  end. Increment a counter per chunk, and reconcile against the final")
print("  event when there is one (M5-L15).")

print("\n  Retrying a broken stream is a second full charge. A stream that")
print("  dies at 60% and is retried costs 1.6 responses for 1 result -- so")
print("  the retry budget from M5-L07 applies here too, and the deadline")
print("  bound matters more, because a stalled stream holds a connection.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: everything above except the illustrative prices and speeds.")
print("  The decoding results are properties of Python's codecs; the JSON")
print("  prefix results are properties of the format; the latency and cost")
print("  tables are arithmetic on stated inputs.")
print("\n  NOT SHOWN: server-sent-event framing, reconnection semantics and")
print("  the exact shape of each provider's final usage event. Those differ")
print("  by provider and change; check current documentation.")
print("\n  The single most useful line in this lab is the incremental decoder.")
print("  It is three lines, it is missing from a great deal of streaming")
print("  code, and its absence shows up as mojibake in exactly the languages")
print("  your English-language tests do not cover.")

print("\nDone.")
