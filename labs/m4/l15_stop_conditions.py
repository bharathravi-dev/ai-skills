"""M4-L15 lab -- stop conditions, truncation and finish reasons.

A mock generator reproduces every finish reason so the whole lesson runs with
no API key. Reproduces the lesson's 2% failure rate from a realistic length
distribution, shows truncated JSON and truncated TOOL CALLS, demonstrates
stop-sequence boundary behaviour, and compares a naive handler with a correct
one.

Run:  python labs/m4/l15_stop_conditions.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

RNG = np.random.default_rng(15)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass
class Response:
    text: str
    finish_reason: str
    output_tokens: int


class MockModel:
    """A deterministic stand-in for a real API, with real finish semantics."""

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.calls = 0

    def generate(self, n_items: int, max_tokens: int, stop=None) -> Response:
        """Produce a JSON extraction whose length depends on the input."""
        self.calls += 1
        items = [{"sku": f"AB-{i:03d}", "qty": int(1 + i % 4),
                  "price": round(9.99 + i, 2)} for i in range(n_items)]
        full = json.dumps({"order_id": "GB-4471", "currency": "GBP",
                           "items": items})
        # ~4 characters per token (M4-L03); the model emits EOS when done.
        tokens = max(1, len(full) // 4)
        if stop:
            for s in stop:
                idx = full.find(s)
                if idx != -1:
                    return Response(full[:idx], "stop_sequence", idx // 4)
        if tokens > max_tokens:
            cut = max_tokens * 4
            return Response(full[:cut], "length", max_tokens)
        return Response(full, "stop", tokens)


# ------------------------------------------------- 1. the four reasons
rule("1. THE FOUR WAYS GENERATION ENDS")

m = MockModel()
print(f"  {'scenario':<34}{'finish_reason':>16}{'tokens':>9}"
      f"{'text ends with':>22}")
cases = [
    ("small doc, generous limit", 2, 600, None),
    ("large doc, tight limit", 40, 100, None),
    ("stop sequence matched", 10, 600, ['"items"']),
]
for label, n, limit, stop in cases:
    r = m.generate(n, limit, stop)
    tail = r.text[-18:].replace("\n", " ")
    print(f"  {label:<34}{r.finish_reason:>16}{r.output_tokens:>9}"
          f"{repr(tail):>22}")
print(f"  {'provider filter (simulated)':<34}{'content_filter':>16}"
      f"{0:>9}{repr(''):>22}")

print("\n  Look at the 'text ends with' column for the first two rows. Neither")
print("  gives any indication of which one was truncated. The text is the same")
print("  KIND of string in both cases -- only finish_reason distinguishes them.")


# ------------------------------------------------- 2. the 2% bug
rule("2. REPRODUCING THE LESSON'S BUG: WHY EXACTLY 2%?")

# Realistic: most documents are small, a few have many line items.
N_DOCS = 5000
item_counts = np.clip(RNG.gamma(shape=2.2, scale=2.6, size=N_DOCS)
                      .astype(int) + 1, 1, 60)

lengths = []
probe = MockModel()
for n in item_counts:
    lengths.append(probe.generate(int(n), 100_000).output_tokens)
lengths = np.array(lengths)

print(f"  {N_DOCS:,} documents, output-token distribution:\n")
print(f"  {'percentile':>12}{'output tokens':>16}")
for q in (50, 90, 95, 98, 99, 99.9, 100):
    print(f"  {f'p{q:g}':>12}{np.percentile(lengths, q):>16.0f}")

print(f"\n  {'max_tokens':>12}{'truncated':>12}{'failure rate':>15}"
      f"{'cost vs p50':>14}")
for limit in (100, 150, 200, 300, 600, 1000):
    fail = float((lengths > limit).mean())
    print(f"  {limit:>12}{int(fail * N_DOCS):>12,}{fail:>14.2%}"
          f"{limit / np.percentile(lengths, 50):>13.1f}x")

target = 200
rate = float((lengths > target).mean())
pct = float((lengths <= target).mean() * 100)
print(f"\n  At max_tokens={target} the failure rate is {rate:.2%}, because")
print(f"  {target} sits at the {pct:.1f}th percentile of output length.")
print("\n  The failures correlate with DOCUMENT COMPLEXITY -- exactly the")
print("  documents a small test set of simple examples would not contain")
print("  (M3-L13 section 5.4). That is why it 'works fine in testing'.")


# ------------------------------------------------- 3. the parse error
rule("3. WHAT THE ENGINEER ACTUALLY SEES")

big = MockModel().generate(30, 200)
print(f"  finish_reason : {big.finish_reason!r}")
print(f"  output tokens : {big.output_tokens}")
print(f"  text (last 60): ...{big.text[-60:]!r}\n")

print("  the naive pipeline:")
print("    data = json.loads(resp.text)")
try:
    json.loads(big.text)
except json.JSONDecodeError as e:
    print(f"    -> json.decoder.JSONDecodeError: {e.msg} "
          f"at line {e.lineno} column {e.colno}")

print("\n  NOTHING in that message mentions max_tokens. It names the PARSER and")
print("  a character offset. An engineer will reasonably check the prompt, the")
print("  schema, the temperature and the model before checking the token limit.")
print(f"\n  the one line that ends the investigation:")
print(f"    print(resp.finish_reason)  ->  {big.finish_reason!r}")


# ------------------------------------------------- 4. tool calls
rule("4. THE DANGEROUS CASE: A TRUNCATED TOOL CALL THAT PARSES")

FULL_CALL = ('{"action": "delete_records", "table": "orders", '
             '"filter": {"status": "archived", "before": "2020-01-01"}, '
             '"dry_run": false}')

print(f"  the intended call:")
print(f"    {FULL_CALL}\n")
print(f"  {'cut at':>8}{'parses?':>10}   raw truncated JSON")
for cut in (len(FULL_CALL), 118, 95, 60, 44, 30):
    partial = FULL_CALL[:cut]
    try:
        json.loads(partial)
        ok = True
    except json.JSONDecodeError:
        ok = False
    print(f"  {cut:>8}{str(ok):>10}   {partial[-34:]!r}")

print("\n  GOOD NEWS FIRST: raw truncated JSON almost never parses. You would")
print("  need to be cut at exactly a balanced closing brace. So a pipeline that")
print("  simply parses and fails is not the dangerous one.")

print("\n  THE DANGEROUS PATTERN is the 'repair' step people write when they")
print("  get tired of parse errors -- append closing braces until it parses:\n")


def naive_repair(text):
    """A pattern that appears in real codebases. Do not do this."""
    for suffix in ("", "}", '"}', "}}", '"}}', "]}", '"]}',  '"}]}',
                   '"}]}}',  "}]}"):
        try:
            return json.loads(text + suffix), suffix
        except json.JSONDecodeError:
            continue
    return None, None


print(f"  {'cut at':>8}{'repaired?':>11}{'action':>18}{'filter?':>10}"
      f"{'dry_run?':>10}   what executing it would do")
for cut in (len(FULL_CALL), 118, 108, 95, 60, 44):
    partial = FULL_CALL[:cut]
    obj, suffix = naive_repair(partial)
    if obj is None:
        print(f"  {cut:>8}{'no':>11}{'-':>18}{'-':>10}{'-':>10}"
              f"   (rejected, correctly)")
        continue
    act = obj.get("action", "-")
    has_f = "filter" in obj
    has_d = "dry_run" in obj
    if act == "delete_records" and not has_f:
        effect = "DELETES EVERY ROW"
    elif act == "delete_records" and not has_d:
        effect = "deletes for real (no dry_run)"
    elif act == "delete_records":
        effect = "deletes archived only"
    else:
        effect = "-"
    print(f"  {cut:>8}{'yes':>11}{act:>18}{str(has_f):>10}{str(has_d):>10}"
          f"   {effect}")

print("\n  There it is. The repair step turns an unparseable truncation into")
print("  VALID JSON that names a real destructive action with its safety")
print("  arguments missing. Every layer behaved reasonably: the model was cut")
print("  off, the repair 'fixed' the syntax, the parser succeeded, and the")
print("  executor did what it was told.")
print("\n  A schema validator that only asks 'is this valid JSON' passes it.")
print("  You must check that every REQUIRED argument is present -- and check")
print("  finish_reason before you get anywhere near execution (M8-L05).")

print(f"\n  what a correct guard looks like:")
REQUIRED = {"delete_records": {"table", "filter", "dry_run"}}


def safe_to_execute(resp_text, finish_reason):
    if finish_reason != "stop":
        return False, f"finish_reason={finish_reason!r} -- refusing to execute"
    try:
        obj = json.loads(resp_text)
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e.msg}"
    need = REQUIRED.get(obj.get("action"), set())
    missing = need - set(obj)
    if missing:
        return False, f"missing required arguments: {sorted(missing)}"
    return True, "ok"


print(f"  {'input':<38}{'safe?':>8}   reason")
for label, text, reason in (
        ("complete call, finish_reason=stop", FULL_CALL, "stop"),
        ("complete call, finish_reason=length", FULL_CALL, "length"),
        ("truncated but valid JSON", FULL_CALL[:44], "length"),
        ("truncated, invalid JSON", FULL_CALL[:60], "length")):
    ok, why = safe_to_execute(text, reason)
    print(f"  {label:<38}{str(ok):>8}   {why}")
print("\n  Note row 2: a COMPLETE call is still refused because finish_reason")
print("  was wrong. That is deliberate -- fail closed.")


# ------------------------------------------------- 5. stop sequences
rule("5. STOP SEQUENCES: THE BOUNDARY BEHAVIOUR")

CODE = '```python\nprint("hello")\n```\nThat prints a greeting.'
print(f"  the model would produce:\n    {CODE!r}\n")

stop_at = CODE.find("```", 3)
returned = CODE[:stop_at]
print(f"  with stop=['```'] the returned text is:")
print(f"    {returned!r}")
print(f"\n  the closing fence is NOT included. Count them:")
print(f"    fences in the returned text: {returned.count('```')}  "
      f"(should be 2 for valid markdown)")
print(f"    valid markdown code block?   {returned.count('```') % 2 == 0}")
print(f"\n  the fix -- append it back:")
repaired = returned + "```"
print(f"    {repaired!r}")
print(f"    fences: {repaired.count('```')}   valid: "
      f"{repaired.count('```') % 2 == 0}")

print("\n  And the reason field is ambiguous on many providers:")
print(f"  {'ended by':<22}{'finish_reason':>18}{'distinguishable?':>20}")
print(f"  {'model emitted EOS':<22}{'stop':>18}{'':>20}")
print(f"  {'stop sequence matched':<22}{'stop':>18}{'NOT from this field':>20}")
print("\n  If you need to know which happened, check whether YOUR stop string")
print("  was produced. Do not rely on the reason field alone.")


# ------------------------------------------------- 6. handlers
rule("6. A NAIVE HANDLER vs A CORRECT ONE")


def naive(resp):
    return json.loads(resp.text)


def correct(resp):
    if resp.finish_reason != "stop":
        raise ValueError(f"incomplete response: finish_reason="
                         f"{resp.finish_reason!r}, "
                         f"{resp.output_tokens} tokens -- raise max_tokens")
    return json.loads(resp.text)


mm = MockModel()
scenarios = [("small doc", 2, 600), ("medium doc", 12, 200),
             ("large doc", 40, 200)]
print(f"  {'scenario':<14}{'reason':>9}   {'naive handler':<44}"
      f"{'correct handler':<44}")
for label, n, limit in scenarios:
    r = mm.generate(n, limit)
    try:
        naive(r)
        n_res = "parsed (may be wrong)"
    except json.JSONDecodeError as e:
        n_res = f"JSONDecodeError: {e.msg[:26]}"
    try:
        correct(r)
        c_res = "parsed"
    except ValueError as e:
        c_res = str(e)[:42]
    except json.JSONDecodeError as e:
        c_res = f"JSONDecodeError: {e.msg[:16]}"
    print(f"  {label:<14}{r.finish_reason:>9}   {n_res:<44}{c_res:<44}")

print("\n  Both handlers FAIL on the large document -- the difference is the")
print("  error they produce. The naive one names the parser and a character")
print("  offset; the correct one names the actual cause and the fix.")
print("  That difference is the whole value of the check: it does not prevent")
print("  the failure, it makes the failure legible.")


# ------------------------------------------------- 7. retry
rule("7. A RETRY THAT ACTUALLY HELPS")

MODEL_LIMIT = 4096


def generate_complete(model, n_items, max_tokens=100, attempts=4):
    trace = []
    for attempt in range(1, attempts + 1):
        r = model.generate(n_items, max_tokens)
        trace.append((attempt, max_tokens, r.finish_reason))
        if r.finish_reason == "stop":
            return r, trace
        max_tokens = min(max_tokens * 2, MODEL_LIMIT)
    return None, trace


print(f"  {'document':<16}{'attempts':>10}   trace (attempt, max_tokens, reason)")
for label, n in (("small (2 items)", 2), ("medium (12)", 12),
                 ("large (40)", 40), ("huge (200)", 200)):
    r, trace = generate_complete(MockModel(), n)
    t = "  ".join(f"({a},{m},{fr})" for a, m, fr in trace)
    print(f"  {label:<16}{len(trace):>10}   {t}")

print("\n  Doubling the limit each time converges quickly. Retrying with the")
print("  SAME limit would truncate at exactly the same place every time --")
print("  temperature 0 or not, nothing about the request has changed.")
print("\n  But the better fix is usually upstream: ask for less output. A prompt")
print("  requesting a 200-word summary does not truncate at 1,000 tokens.")
print("  Truncation is often a prompt problem wearing a config problem's")
print("  clothes.")

print("\nDone.")
