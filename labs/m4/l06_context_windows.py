"""M4-L06 lab -- context windows, budgets and truncation.

Measures attention's quadratic cost, implements the lesson's token budget with
an explicit drop order, compares truncation strategies, simulates a
needle-in-a-haystack test, and sizes the KV cache.

NumPy only, no API key, no network.
Run:  python labs/m4/l06_context_windows.py
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


# --------------------------------------------- 1. the quadratic cost
rule("1. WHY THE LIMIT EXISTS: ATTENTION IS QUADRATIC")

D = 64
print(f"  one attention head, d_head = {D}\n")
print(f"  {'tokens':>8}{'score matrix':>16}{'floats':>14}{'MB (fp32)':>12}"
      f"{'time':>11}{'vs 128':>10}")

base_t = None
measured = []
for T in (128, 256, 512, 1024, 2048, 4096):
    q = RNG.normal(0, 1, size=(T, D)).astype(np.float32)
    k = RNG.normal(0, 1, size=(T, D)).astype(np.float32)
    v = RNG.normal(0, 1, size=(T, D)).astype(np.float32)
    reps = max(1, 200_000_000 // (T * T * D))
    t0 = time.perf_counter()
    for _ in range(reps):
        scores = q @ k.T / math.sqrt(D)
        out = softmax(scores, axis=-1) @ v
    dt = (time.perf_counter() - t0) / reps
    if base_t is None:
        base_t = dt
    measured.append((T, dt))
    print(f"  {T:>8}{f'{T}x{T}':>16}{T * T:>14,}{T * T * 4 / 1024**2:>11.1f}M"
          f"{dt * 1000:>10.2f}ms{dt / base_t:>9.1f}x")

# Fit the exponent: time ~ T^a
ts = np.array([t for t, _ in measured], dtype=float)
dts = np.array([d for _, d in measured], dtype=float)
a, b = np.polyfit(np.log(ts), np.log(dts), 1)
print(f"\n  fitted exponent: time ~ T^{a:.2f}")
print(f"  (theory says 2.0 for the score matrix; measured {a:.2f})")
print("\n  Doubling the context roughly QUADRUPLES the attention work. That is")
print("  the whole reason a context window has a limit -- not an arbitrary")
print("  product decision.")

print(f"\n  extrapolating the score matrix alone (fp32, one head):")
print(f"  {'tokens':>10}{'score floats':>18}{'memory':>14}")
for T in (8_192, 32_768, 131_072, 1_000_000):
    n = T * T
    gb = n * 4 / 1024**3
    unit = f"{gb:,.1f} GB" if gb >= 1 else f"{gb * 1024:,.0f} MB"
    print(f"  {T:>10,}{n:>18,}{unit:>14}")
print("\n  A 1M-token context would need 3.6 TB for ONE head's score matrix if")
print("  materialised. It is not -- FlashAttention and similar never form the")
print("  full matrix. But the COMPUTE is still quadratic, and that is why long")
print("  context is expensive rather than free.")


# --------------------------------------------- 2. the token budget
rule("2. A TOKEN BUDGET WITH AN EXPLICIT DROP ORDER")


@dataclass
class Component:
    name: str
    tokens: int
    priority: int              # 0 = never drop
    divisible: bool = False    # can it be partially kept?


@dataclass
class BudgetResult:
    kept: dict = field(default_factory=dict)
    dropped: list = field(default_factory=list)
    total: int = 0
    output_reserved: int = 0
    ok: bool = True
    reason: str = ""


def fit(window: int, output_reserve: int, components, headroom=0.90):
    """Fit components into a window. Reserves OUTPUT FIRST, then spends.

    Returns a full report of what was kept and dropped -- a budget that
    silently drops things is a budget you cannot debug.
    """
    result = BudgetResult(output_reserved=output_reserve)
    fixed = [c for c in components if c.priority == 0]
    flexible = sorted((c for c in components if c.priority > 0),
                      key=lambda c: c.priority)

    fixed_total = sum(c.tokens for c in fixed)
    hard_limit = window - output_reserve
    usable = int(hard_limit * headroom)

    if fixed_total > usable:
        result.ok = False
        result.reason = (f"fixed components ({fixed_total:,}) exceed the usable "
                         f"budget ({usable:,}) -- this request cannot be built")
        return result

    for c in fixed:
        result.kept[c.name] = c.tokens
    spent = fixed_total

    for c in flexible:
        if spent + c.tokens <= usable:
            result.kept[c.name] = c.tokens
            spent += c.tokens
        elif c.divisible and usable - spent > 0:
            partial = usable - spent
            result.kept[c.name] = partial
            result.dropped.append(f"{c.name} (kept {partial:,} of {c.tokens:,})")
            spent = usable
        else:
            result.dropped.append(f"{c.name} (all {c.tokens:,})")

    result.total = spent
    return result


def show(label, res, window):
    print(f"\n  {label}")
    if not res.ok:
        print(f"    REFUSED: {res.reason}")
        return
    for name, n in res.kept.items():
        print(f"    keep   {name:<24}{n:>9,}")
    for d in res.dropped:
        print(f"    DROP   {d}")
    print(f"    {'input total':<31}{res.total:>9,}")
    print(f"    {'output reserved':<31}{res.output_reserved:>9,}")
    print(f"    {'window used':<31}"
          f"{(res.total + res.output_reserved) / window:>8.1%}")


WINDOW = 128_000
RESERVE = 1_500

print(f"  window {WINDOW:,} tokens, output reserve {RESERVE:,}, headroom 90%")
print("  drop order: retrieved documents (by rank) first, then history (by age)")

show("comfortable request:", fit(WINDOW, RESERVE, [
    Component("system prompt", 900, 0),
    Component("user message", 200, 0),
    Component("retrieved docs", 6_000, 1, divisible=True),
    Component("history", 4_000, 2, divisible=True),
]), WINDOW)

show("oversized documents -- docs are trimmed:", fit(WINDOW, RESERVE, [
    Component("system prompt", 900, 0),
    Component("user message", 200, 0),
    Component("retrieved docs", 200_000, 1, divisible=True),
    Component("history", 4_000, 2, divisible=True),
]), WINDOW)

show("huge history -- docs kept, history trimmed:", fit(WINDOW, RESERVE, [
    Component("system prompt", 900, 0),
    Component("user message", 200, 0),
    Component("retrieved docs", 60_000, 1, divisible=True),
    Component("history", 400_000, 2, divisible=True),
]), WINDOW)

show("impossible request -- the system prompt alone overflows:",
     fit(WINDOW, RESERVE, [
         Component("system prompt", 300_000, 0),
         Component("user message", 200, 0),
     ]), WINDOW)

print("\n  Note the last case REFUSES rather than truncating. Silently cutting")
print("  a system prompt can remove a safety instruction while leaving the")
print("  rest intact -- a failure that is invisible in the output.")


# --------------------------------------------- 3. truncation strategies
rule("3. TRUNCATION STRATEGIES: WHAT EACH ONE DISCARDS")

DOC_LEN = 1000
KEEP = 300
NEEDLE = "THE-REFUND-WINDOW-IS-45-DAYS"


def make_doc(needle_at_fraction):
    toks = [f"w{i}" for i in range(DOC_LEN)]
    toks[int(DOC_LEN * needle_at_fraction)] = NEEDLE
    return toks


def head(t, n):
    return t[:n]


def tail(t, n):
    return t[-n:]


def head_tail(t, n):
    h = n // 2
    return t[:h] + t[-(n - h):]


STRATEGIES = {"head": head, "tail": tail, "head+tail": head_tail}

print(f"  document {DOC_LEN} tokens, truncating to {KEEP} ({KEEP / DOC_LEN:.0%})\n")
print(f"  {'needle at':>11}" + "".join(f"{s:>14}" for s in STRATEGIES))
survived = {s: 0 for s in STRATEGIES}
depths = [0.05, 0.15, 0.25, 0.40, 0.50, 0.60, 0.75, 0.85, 0.95]
for frac in depths:
    doc = make_doc(frac)
    row = f"  {frac:>10.0%}"
    for name, fn in STRATEGIES.items():
        ok = NEEDLE in fn(doc, KEEP)
        survived[name] += ok
        row += f"{('kept' if ok else 'LOST'):>14}"
    print(row)

print(f"\n  {'strategy':>11}{'survived':>14}")
for name, n in survived.items():
    print(f"  {name:>11}{f'{n}/{len(depths)}':>14}")
best = max(survived.values())
tied = [n for n, v in survived.items() if v == best]
print(f"\n  ALL THREE SURVIVED {best}/{len(depths)} -- they TIE.")
print("  That is not a flaw in the experiment; it is arithmetic. Keeping 30% of")
print("  a document preserves 30% of it whichever 30% you choose. Truncation")
print("  strategies do not differ in HOW MUCH they keep, only in WHICH part:")
print(f"    head      kept depths {[f'{d:.0%}' for d in depths if NEEDLE in head(make_doc(d), KEEP)]}")
print(f"    tail      kept depths {[f'{d:.0%}' for d in depths if NEEDLE in tail(make_doc(d), KEEP)]}")
print(f"    head+tail kept depths {[f'{d:.0%}' for d in depths if NEEDLE in head_tail(make_doc(d), KEEP)]}")
print("\n  So the choice is a BET about where the information is:")
print("    head      -- bet it is near the top (abstracts, summaries, headers)")
print("    tail      -- bet it is near the bottom (chat history, logs, conclusions)")
print("    head+tail -- hedge, covering both ends and abandoning the middle")
print("\n  Every option loses the middle 40-60%, and none is safe for a fact you")
print("  have not located. That is what retrieval is for (M7): find the relevant")
print("  chunk instead of betting on which end of the document holds it.")


# --------------------------------------------- 4. lost in the middle
rule("4. NEEDLE IN A HAYSTACK  (a simulation, not a measurement of any model)")

print("  This SIMULATES the lost-in-the-middle effect with a position-dependent")
print("  attention prior, so you can see its shape and run the experiment.")
print("  It is NOT a measurement of any real model -- run this against the")
print("  model you deploy, with your own content (M4-L06 section 5.4).\n")


def recall_prior(depth, strength=0.75):
    """A U-shaped prior: strong at both ends, weak in the middle."""
    return 1.0 - strength * math.sin(math.pi * depth) ** 2


CTX_TOKENS = 100_000
TRIALS = 400
print(f"  {'depth':>8}{'simulated recall':>20}   profile")
for depth in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    p = recall_prior(depth)
    hits = int((RNG.random(TRIALS) < p).sum())
    bar = "#" * int(hits / TRIALS * 44)
    print(f"  {depth:>7.0%}{hits / TRIALS:>20.3f}   |{bar}")

print("\n  The shape is the point: a U. Facts at the very start and very end are")
print("  recovered reliably; facts at 40-60% depth are not. Consequences:")
print("    * put the question LAST, after the context")
print("    * put the most important document FIRST")
print("    * retrieve FEWER, better documents rather than more")
print("    * and measure this yourself -- the depth of the dip varies by model")


# --------------------------------------------- 5. KV cache
rule("5. THE KV CACHE: WHY LONG CONTEXT COSTS MEMORY, NOT JUST COMPUTE")

CONFIGS = [
    ("7B-ish", 32, 32, 128),
    ("13B-ish", 40, 40, 128),
    ("70B-ish", 80, 64, 128),
]
print(f"  KV bytes = 2 x layers x heads x head_dim x tokens x bytes_per_value\n")
print(f"  {'model':<10}{'layers':>8}{'heads':>7}{'per token':>12}"
      f"{'8k ctx':>11}{'32k ctx':>11}{'128k ctx':>12}")
for name, layers, heads, hd in CONFIGS:
    per_tok = 2 * layers * heads * hd * 2          # float16
    row = f"  {name:<10}{layers:>8}{heads:>7}{per_tok / 1024:>11.0f}K"
    for ctx in (8_192, 32_768, 131_072):
        gb = per_tok * ctx / 1024**3
        row += f"{gb:>10.1f}G"
    print(row)

per_tok_7b = 2 * 32 * 32 * 128 * 2
print(f"\n  A 7B-class model at 128k context needs "
      f"{per_tok_7b * 131_072 / 1024**3:.0f} GB of KV cache")
print(f"  for ONE request -- more than the model weights themselves "
      f"({7e9 * 2 / 1024**3:.0f} GB in fp16).")
print("\n  fitting concurrent requests on one 80 GB accelerator:")
weights = 7e9 * 2 / 1024**3
print(f"  {'context':>10}{'KV per request':>17}{'concurrent requests':>22}")
for ctx in (2_048, 8_192, 32_768, 131_072):
    kv = per_tok_7b * ctx / 1024**3
    n = int((80 - weights) / kv)
    print(f"  {ctx:>10,}{kv:>16.2f}G{n:>22,}")

kv_8k = per_tok_7b * 8_192 / 1024**3
kv_128k = per_tok_7b * 131_072 / 1024**3
print(f"\n  {int((80 - weights) / kv_8k)} concurrent users at 8k context; "
      f"{int((80 - weights) / kv_128k)} at 128k.")
print(f"  A {int((80 - weights) / kv_8k) // max(int((80 - weights) / kv_128k), 1)}x "
      f"reduction in how many people one accelerator can serve.")
print("  This -- not the attention arithmetic --")
print("  is usually what limits the context length a provider will offer you,")
print("  and why long-context requests are priced the way they are.")


# --------------------------------------------- 6. context stuffing
rule("6. THE COST OF FILLING THE WINDOW BECAUSE IT IS THERE")

TOK_PER_DOC = 750
IN_PRICE = 3.00 / 1_000_000          # illustrative only
REQUESTS = 100_000

print("  A synthetic quality curve: relevance falls off as you add lower-ranked")
print("  documents, and lost-in-the-middle erodes what the extra ones add.\n")
print(f"  {'docs':>6}{'tokens':>10}{'monthly cost':>15}{'quality':>10}"
      f"{'cost per quality point':>25}")
best = None
for n_docs in (1, 2, 4, 8, 16, 32, 64, 80):
    tokens = n_docs * TOK_PER_DOC + 1_100
    # diminishing relevance, then middle-loss erosion
    quality = 1 - math.exp(-n_docs / 4.0)
    quality *= recall_prior(min(0.5, n_docs / 160.0), strength=0.5)
    cost = tokens * REQUESTS * IN_PRICE
    ratio = cost / quality
    if best is None or ratio < best[1]:
        best = (n_docs, ratio)
    print(f"  {n_docs:>6}{tokens:>10,}{'$' + format(cost, ',.0f'):>15}"
          f"{quality:>10.3f}{ratio:>25,.0f}")

print(f"\n  Cost per unit of quality is lowest at {best[0]} documents.")
print("  Beyond that you are paying linearly for a quality curve that has")
print("  flattened -- and, past the middle of the context, is being eroded.")
print("\n  The numbers here are ILLUSTRATIVE (the quality curve is synthetic).")
print("  The METHOD is not: plot your own quality against document count on")
print("  your own evaluation set (M7-L16, M3-L14) and find your own knee.")
print("  'The window is large' is not a reason to fill it.")

print("\nDone.")
