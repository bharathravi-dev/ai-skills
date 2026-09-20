"""M12-L02 lab -- one request shape, and what streaming changes.
This lab computes:

  1. how many call sites change when you switch models, with and without a unified API,
  2. streaming: time to first token against total time, and what the user perceives,
  3. every timeout on the path against a streamed answer,
  4. the tool-use loop, counted in round trips and tokens,
  5. token accounting from the response, and the cost it implies.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m12/l02_invocation_streaming_converse.py
"""

from __future__ import annotations

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. ONE REQUEST SHAPE, OR ONE PER PROVIDER?")

CALL_SITES = {
    "build the request body":      {"unified": 0, "per_provider": 1},
    "set the system prompt":       {"unified": 0, "per_provider": 1},
    "set max tokens / temperature": {"unified": 0, "per_provider": 1},
    "parse the response text":     {"unified": 0, "per_provider": 1},
    "read the stop reason":        {"unified": 0, "per_provider": 1},
    "read token usage":            {"unified": 0, "per_provider": 1},
    "declare tools":               {"unified": 0, "per_provider": 1},
    "parse a tool call":           {"unified": 0, "per_provider": 1},
    "return a tool result":        {"unified": 0, "per_provider": 1},
    "handle the streaming events": {"unified": 0, "per_provider": 1},
    "the model id itself":         {"unified": 1, "per_provider": 1},
}
uni = sum(v["unified"] for v in CALL_SITES.values())
per = sum(v["per_provider"] for v in CALL_SITES.values())
print(f"  {'what the code does':<34}{'unified API':>14}{'per-provider API':>19}")
for name, v in CALL_SITES.items():
    print(f"  {name:<34}{v['unified']:>14}{v['per_provider']:>19}")
print(f"  {'TOTAL places to change':<34}{uni:>14}{per:>19}")
print(f"\n  switching models touches {uni} place with a unified API and {per} without it.")
print("  That is the entire argument for the Converse API: the request and response")
print("  shape is the same across providers, so a model swap is a configuration")
print("  change rather than a rewrite (M5-L17). The exception is the model-specific")
print("  extras, which the API passes through -- and every one you use puts a place")
print("  back on the list.")


# ============================================================ 2
rule("2. STREAMING: WHAT THE USER ACTUALLY WAITS FOR")

TTFT_MS = 640                 # time to first token
TOKENS = 400
MS_PER_TOKEN = 18
total_ms = TTFT_MS + TOKENS * MS_PER_TOKEN
READ_WPM = 240
words = TOKENS * 0.75
read_ms = words / READ_WPM * 60_000
print(f"  {TOKENS} output tokens, {MS_PER_TOKEN} ms/token, first token at {TTFT_MS} ms\n")
print(f"  {'mode':<26}{'user sees nothing for':>24}{'total':>11}")
print(f"  {'non-streaming':<26}{total_ms:>21,.0f} ms{total_ms:>8,.0f} ms")
print(f"  {'streaming':<26}{TTFT_MS:>21,.0f} ms{total_ms:>8,.0f} ms")
print(f"\n  the total is IDENTICAL: {total_ms:,.0f} ms. Streaming changes only when the first")
print(f"  word appears -- {TTFT_MS / total_ms:.0%} of the way through instead of 100%.")
print(f"  it also matters that reading {words:.0f} words takes about {read_ms / 1000:.0f} s, which is")
print(f"  {read_ms / total_ms:.1f}x the generation time: a streamed answer arrives faster than the")
print("  user can read it, so the perceived wait is the 640 ms, not the 7.8 s.")
print("  Streaming is not a performance optimisation. It is a perception change, and")
print("  it costs you every timeout on the path (section 3) and the ability to")
print("  validate the whole output before showing it (M5-L07, M12-L06).")


# ============================================================ 3
rule("3. EVERY TIMEOUT ON THE PATH")

LAYERS = [
    ("browser / client SDK default",       30,  "often the first to fire"),
    ("CDN or proxy",                       60,  "may also buffer, defeating streaming"),
    ("API Gateway integration (default)",  29,  "raiseable on REST APIs by quota"),
    ("load balancer idle timeout",         60,  "configurable into minutes"),
    ("application HTTP client",            10,  "the default in many libraries"),
    ("Bedrock SDK read timeout",           60,  "set it explicitly"),
]
ANSWER_S = total_ms / 1000
print(f"  a streamed answer takes {ANSWER_S:.1f} s end to end\n")
print(f"  {'layer':<38}{'timeout':>9}{'fits?':>8}   note")
for name, secs, note in LAYERS:
    print(f"  {name:<38}{secs:>7} s{('yes' if ANSWER_S <= secs else 'NO'):>8}   {note}")
smallest = min(LAYERS, key=lambda x: x[1])
print(f"\n  the effective timeout is the SMALLEST on the path: {smallest[0]} at {smallest[1]} s.")
LONG_S = 180
print(f"  now take a long answer of {LONG_S} s (a research-style response):")
fails = [n for n, s, _ in LAYERS if s < LONG_S]
print(f"    layers that would cut it: {len(fails)}/{len(LAYERS)} -- {', '.join(n.split(' (')[0] for n in fails)}")
print("  An idle timeout is usually reset by each streamed chunk, which is why")
print("  streaming SURVIVES some of these and a non-streamed call does not -- but")
print("  only if nothing on the path BUFFERS. A proxy that buffers the response")
print("  converts your stream back into one long silence (M11-L09, M11-L13).")


# ============================================================ 4
rule("4. THE TOOL-USE LOOP, COUNTED")

TURNS = [
    ("user question",                         620,    0, "you send messages + toolConfig"),
    ("model asks for a tool",                   0,   40, "stopReason = tool_use; a toolUse block"),
    ("you run the tool, send the result",     180,    0, "a toolResult block in a user message"),
    ("model asks for a second tool",            0,   35, "stopReason = tool_use again"),
    ("you run it, send the result",            240,    0, "another toolResult"),
    ("model answers",                            0,  380, "stopReason = end_turn"),
]
print(f"  {'step':<38}{'input tok':>11}{'output tok':>12}   what it is")
in_tot = out_tot = 0
for step, i, o, note in TURNS:
    in_tot += i
    out_tot += o
    print(f"  {step:<38}{i:>11}{o:>12}   {note}")
print(f"  {'TOTAL':<38}{in_tot:>11}{out_tot:>12}")
round_trips = sum(1 for _, i, _, _ in TURNS if i > 0)
print(f"\n  {round_trips} model round trips for one user question.")
print("  Two consequences. The CONVERSATION GROWS: every turn resends the whole")
print("  history, so input tokens accumulate faster than the answer suggests")
print("  (M5-L15). And the latency is the SUM of the round trips plus the tool")
print("  execution time, which is why an agent feels slow even when each step is")
print("  fast (M8-L03, M13-L10). Cap the loop (M8-L15).")


# ============================================================ 5
rule("5. TOKEN ACCOUNTING FROM THE RESPONSE")

RESPONSE = {
    "output": {"message": {"role": "assistant",
                           "content": [{"text": "The refund policy allows 30 days..."}]}},
    "stopReason": "end_turn",
    "usage": {"inputTokens": in_tot, "outputTokens": out_tot,
              "totalTokens": in_tot + out_tot},
    "metrics": {"latencyMs": 4180},
}
print("  a response carries what you need to account for it:\n")
print(json.dumps(RESPONSE, indent=2)[:520])
IN_PER_M, OUT_PER_M = 3.00, 15.00
cost = (in_tot * IN_PER_M + out_tot * OUT_PER_M) / 1_000_000
print(f"\n  cost of this ONE question: ${cost:.5f} "
      f"[ILLUSTRATIVE ${IN_PER_M}/M in, ${OUT_PER_M}/M out]")
print(f"  at 40,000 questions/day: ${cost * 40_000:,.0f}/day, ${cost * 40_000 * 30:,.0f}/month")
STOP_REASONS = [
    ("end_turn",      "the model finished normally"),
    ("max_tokens",    "TRUNCATED -- your output is incomplete, and may be invalid JSON"),
    ("stop_sequence", "a stop sequence you configured was produced"),
    ("tool_use",      "the model wants a tool result before continuing"),
    ("guardrail_intervened", "a guardrail blocked or modified the response (M12-L06)"),
]
print(f"\n  {'stopReason':<22}what it means for your code")
for reason, meaning in STOP_REASONS:
    print(f"  {reason:<22}{meaning}")
print("\n  Read the stop reason on EVERY response. 'max_tokens' is the one that")
print("  silently breaks structured output: you get valid-looking text that is a")
print("  truncated JSON object, and a parser that fails at the worst moment")
print("  (M5-L06, M5-L07). Record usage on every call -- it is your cost signal")
print("  and your runaway detector (M11-L06, M11-L16).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count, latency figure, timeout comparison, token total and cost")
print("  above is computed from the values in this script.")
print("\n  DOCUMENTED SHAPE: the response fields shown -- output.message, stopReason,")
print("  usage.inputTokens/outputTokens, metrics.latencyMs -- follow the Converse API's")
print("  documented structure, as do the stop reasons.")
print("\n  ILLUSTRATIVE: all timings, token counts, prices and the timeout values are")
print("  invented. Measure your own; the timeout defaults in particular vary by")
print("  client library and change over time.")
print("\n  NOT SHOWN: the actual SDK calls, multimodal content blocks, guardrail")
print("  configuration (M12-L06), and prompt caching.")
print("\nDone.")
