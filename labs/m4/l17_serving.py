"""M4-L17 lab -- serving internals: memory, batching, bandwidth.

Computes the lesson's memory arithmetic and every lever, measures the batching
throughput/latency curve on real matrix operations, demonstrates the
memory-bandwidth argument empirically, and models speculative decoding.

NumPy only, no API key, no network, no GPU.
Run:  python labs/m4/l17_serving.py
"""

from __future__ import annotations

import time

import numpy as np

RNG = np.random.default_rng(17)
GB = 1024 ** 3


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ------------------------------------------------- model configs
MODELS = {
    "7B (MHA)":   dict(params=7e9, layers=32, heads=32, kv_heads=32, hd=128),
    "7B (GQA-8)": dict(params=7e9, layers=32, heads=32, kv_heads=8, hd=128),
    "13B (MHA)":  dict(params=13e9, layers=40, heads=40, kv_heads=40, hd=128),
    "13B (GQA-8)": dict(params=13e9, layers=40, heads=40, kv_heads=8, hd=128),
    "70B (MHA)":  dict(params=70e9, layers=80, heads=64, kv_heads=64, hd=128),
    "70B (GQA-8)": dict(params=70e9, layers=80, heads=64, kv_heads=8, hd=128),
}


def weight_gb(cfg, bytes_per=2):
    return cfg["params"] * bytes_per / GB


def kv_per_token(cfg, bytes_per=2):
    return 2 * cfg["layers"] * cfg["kv_heads"] * cfg["hd"] * bytes_per


def kv_gb(cfg, ctx, concurrency, bytes_per=2):
    return kv_per_token(cfg, bytes_per) * ctx * concurrency / GB


rule("1. WEIGHT MEMORY: THE NUMBER EVERYONE QUOTES")

print(f"  {'model':<14}{'fp32':>10}{'fp16':>10}{'int8':>10}{'int4':>10}"
      f"{'+15% overhead (fp16)':>24}")
for name in ("7B (MHA)", "13B (MHA)", "70B (MHA)"):
    c = MODELS[name]
    base = weight_gb(c, 2)
    print(f"  {name.split()[0]:<14}{weight_gb(c, 4):>9.1f}G"
          f"{base:>9.1f}G{weight_gb(c, 1):>9.1f}G{weight_gb(c, 0.5):>9.1f}G"
          f"{base * 1.15:>23.1f}G")
print("\n  Real deployments need 10-20% above this for workspace and")
print("  fragmentation. A 7B model in fp16 needs about 15 GB, not 13.")


rule("2. KV CACHE: THE NUMBER THAT DECIDES HOW MANY USERS YOU SERVE")

print(f"  kv_bytes = 2 x layers x KV_HEADS x head_dim x tokens x bytes\n")
print(f"  {'model':<14}{'layers':>8}{'kv heads':>10}{'per token':>12}"
      f"{'8k ctx':>10}{'32k ctx':>10}{'128k ctx':>11}")
for name, c in MODELS.items():
    per = kv_per_token(c)
    print(f"  {name:<14}{c['layers']:>8}{c['kv_heads']:>10}"
          f"{per / 1024:>11.0f}K{kv_gb(c, 8192, 1):>9.1f}G"
          f"{kv_gb(c, 32768, 1):>9.1f}G{kv_gb(c, 131072, 1):>10.1f}G")

mha, gqa = MODELS["7B (MHA)"], MODELS["7B (GQA-8)"]
print(f"\n  GQA reduces the cache {kv_per_token(mha) / kv_per_token(gqa):.0f}x "
      f"by using {gqa['kv_heads']} KV heads instead of {mha['kv_heads']}.")
print("  Note it does NOT reduce the weights at all -- the query heads are")
print("  unchanged. It is purely a cache optimisation, which is exactly why")
print("  it is the right lever for a cache problem.")


rule("3. THE WORKED EXAMPLE: WILL A 13B MODEL FIT ON 80 GB?")

DEVICE, CTX, USERS, ACT = 80.0, 8192, 32, 4.0
c13 = MODELS["13B (MHA)"]

w = weight_gb(c13, 2)
kv = kv_gb(c13, CTX, USERS)
total = w + kv + ACT
print(f"  question: 13B model, {CTX:,} context, {USERS} concurrent users,"
      f" {DEVICE:.0f} GB device\n")
print(f"  {'component':<28}{'GB':>10}{'share':>10}")
print(f"  {'weights (fp16)':<28}{w:>10.1f}{w / total:>10.0%}")
print(f"  {'KV cache':<28}{kv:>10.1f}{kv / total:>10.0%}")
print(f"  {'activations (estimate)':<28}{ACT:>10.1f}{ACT / total:>10.0%}")
print(f"  {'TOTAL':<28}{total:>10.1f}")
print(f"\n  device capacity {DEVICE:.0f} GB -> "
      f"{'FITS' if total <= DEVICE else 'DOES NOT FIT'} "
      f"({total / DEVICE:.1f}x over)")
print(f"\n  The KV cache is {kv / total:.0%} of the requirement. The weights --")
print(f"  the number in the model's name -- are {w / total:.0%}.")

print(f"\n  working the levers:")
print(f"  {'change':<34}{'weights':>10}{'KV':>10}{'total':>10}{'fits?':>8}"
      f"{'saving':>10}")
options = [
    ("baseline", c13, 2, CTX, USERS),
    ("int8 weights", c13, 1, CTX, USERS),
    ("int4 weights", c13, 0.5, CTX, USERS),
    ("halve context (4k)", c13, 2, CTX // 2, USERS),
    ("halve concurrency (16)", c13, 2, CTX, USERS // 2),
    ("GQA-8 model", MODELS["13B (GQA-8)"], 2, CTX, USERS),
    ("GQA-8 + int8 KV", MODELS["13B (GQA-8)"], 2, CTX, USERS),
]
for label, cfg, wbytes, ctx, users in options:
    ww = weight_gb(cfg, wbytes)
    kvb = 1 if "int8 KV" in label else 2
    kk = kv_gb(cfg, ctx, users, kvb)
    tt = ww + kk + ACT
    print(f"  {label:<34}{ww:>10.1f}{kk:>10.1f}{tt:>10.1f}"
          f"{('YES' if tt <= DEVICE else 'no'):>8}"
          f"{(total - tt) / total:>9.0%}")

print("\n  Only the GQA rows fit. Quantizing the WEIGHTS -- the instinct, because")
print(f"  that is the number in the model's name -- saves {(total - (weight_gb(c13, 1) + kv + ACT)) / total:.0%}")
print(f"  of a {total:.0f} GB problem. GQA saves "
      f"{(total - (weight_gb(MODELS['13B (GQA-8)'], 2) + kv_gb(MODELS['13B (GQA-8)'], CTX, USERS) + ACT)) / total:.0%}.")
print("\n  DO NOT QUANTIZE WEIGHTS TO FIX A KV-CACHE PROBLEM.")


rule("4. HOW MANY USERS FIT?  (solving the inequality)")


def max_users(cfg, ctx, device_gb=80.0, wbytes=2, kvbytes=2, act=4.0):
    avail = device_gb - weight_gb(cfg, wbytes) - act
    if avail <= 0:
        return 0
    return int(avail * GB / (kv_per_token(cfg, kvbytes) * ctx))


print(f"  concurrent users, fp16 weights. The 7B and 13B models are sized on")
print(f"  one {DEVICE:.0f} GiB device; a 70B model's weights alone are")
print(f"  {weight_gb(MODELS['70B (MHA)']):.0f} GiB, so it is sized on 160 GiB.\n")
print(f"  {'model':<14}{'device':>9}{'2k':>8}{'8k':>8}{'32k':>8}{'128k':>9}")
for name, c in MODELS.items():
    dev = 160.0 if name.startswith("70B") else DEVICE
    row = f"  {name:<14}{f'{dev:.0f}G':>9}"
    for ctx in (2048, 8192, 32768, 131072):
        row += f"{max_users(c, ctx, device_gb=dev):>8}"
    print(row)

print(f"\n  the same, with the KV CACHE quantized to int8:")
print(f"  {'model':<14}{'device':>9}{'2k':>8}{'8k':>8}{'32k':>8}{'128k':>9}")
for name, c in MODELS.items():
    dev = 160.0 if name.startswith("70B") else DEVICE
    row = f"  {name:<14}{f'{dev:.0f}G':>9}"
    for ctx in (2048, 8192, 32768, 131072):
        row += f"{max_users(c, ctx, device_gb=dev, kvbytes=1):>8}"
    print(row)

m8 = max_users(MODELS["13B (MHA)"], 8192)
g8 = max_users(MODELS["13B (GQA-8)"], 8192)
m70 = max_users(MODELS["70B (MHA)"], 8192, device_gb=160.0)
g70 = max_users(MODELS["70B (GQA-8)"], 8192, device_gb=160.0)
print(f"\n  Compare within a model size at 8k context:")
print(f"    13B: MHA {m8} users -> GQA-8 {g8} users  ({g8 / max(m8, 1):.0f}x)")
print(f"    70B: MHA {m70} users -> GQA-8 {g70} users  "
      f"({g70 / max(m70, 1):.0f}x)")
print("\n  That is the difference between a demo and a product, from one")
print("  architectural choice that costs almost nothing in quality.")
print("\n  Note also the ZERO rows: a 70B model in fp16 needs "
      f"{weight_gb(MODELS['70B (MHA)']):.0f} GiB for")
print("  weights alone, so it does not fit on an 80 GiB device AT ALL, at any")
print("  context or concurrency. Some deployments are ruled out by arithmetic")
print("  before any tuning is possible.")


rule("5. WHY BATCHING WORKS: THE MEMORY-BANDWIDTH ARGUMENT, MEASURED")

print("  Decode reads EVERY parameter to produce ONE token. If that read is")
print("  the bottleneck, serving N users in a batch should cost barely more")
print("  than serving one. Measuring on real matrix operations:\n")

D_W = 2048
W = RNG.normal(0, 0.02, size=(D_W, D_W)).astype(np.float32)
print(f"  weight matrix {D_W}x{D_W} float32 = "
      f"{W.nbytes / 1024**2:.1f} MB\n")
print(f"  {'batch':>7}{'time/call':>13}{'time/request':>15}"
      f"{'throughput':>14}{'vs batch 1':>12}")
base_per_req = None
for batch in (1, 2, 4, 8, 16, 32, 64, 128):
    x = RNG.normal(0, 1, size=(batch, D_W)).astype(np.float32)
    reps = max(3, 4000 // batch)
    for _ in range(3):
        _ = x @ W
    t0 = time.perf_counter()
    for _ in range(reps):
        _ = x @ W
    dt = (time.perf_counter() - t0) / reps
    per_req = dt / batch
    if base_per_req is None:
        base_per_req = per_req
    print(f"  {batch:>7}{dt * 1e6:>11.1f}us{per_req * 1e6:>13.2f}us"
          f"{batch / dt:>13.0f}/s{base_per_req / per_req:>11.1f}x")

print("\n  Time per REQUEST falls sharply as the batch grows, because the same")
print("  weight read serves every row. This is why hosted inference is cheaper")
print("  than self-hosting at low volume -- the provider batches your request")
print("  with everyone else's -- and why your own deployment at one request at")
print("  a time is the worst efficiency point available.")


rule("6. THROUGHPUT vs LATENCY: THEY PULL IN OPPOSITE DIRECTIONS")

print("  Modelling a queue: requests arrive, wait for a batch slot, then")
print("  generate. Larger batches raise throughput AND raise latency.\n")

TPOT_BASE_MS = 20.0        # per-token time at batch 1
OUT_TOKENS = 300


def serve(batch):
    # decode time per step grows sublinearly with batch (bandwidth-shared)
    step_ms = TPOT_BASE_MS * (1 + 0.012 * (batch - 1))
    latency_s = step_ms * OUT_TOKENS / 1000
    throughput = batch * OUT_TOKENS / latency_s
    return step_ms, latency_s, throughput


print(f"  {'batch':>7}{'ms/token':>11}{'latency (s)':>14}"
      f"{'tokens/s total':>17}{'cost/token':>13}")
best = None
for batch in (1, 4, 8, 16, 32, 64, 128):
    step, lat, thr = serve(batch)
    cost = 1 / thr
    if best is None or thr > best[1]:
        best = (batch, thr)
    print(f"  {batch:>7}{step:>11.2f}{lat:>14.2f}{thr:>17.0f}"
          f"{cost * 1000:>12.3f}m")

print(f"\n  Throughput rises {serve(128)[2] / serve(1)[2]:.0f}x from batch 1 to 128,")
print(f"  and per-request latency rises {serve(128)[1] / serve(1)[1]:.1f}x.")
print("\n  There is no batch size that is best. You are choosing between COST")
print("  (throughput, which you feel) and LATENCY (which your users feel).")
print("  Decide which you are optimising BEFORE tuning anything.")


rule("7. SPECULATIVE DECODING")

print("  A small draft model proposes k tokens; the large model verifies all k")
print("  in ONE forward pass. Verification costs about as much as generating")
print("  one token, because decode is bandwidth-bound, not compute-bound.\n")

DRAFT_COST = 0.08          # draft model cost relative to the large one


def spec_speedup(k, accept_rate, draft_cost=DRAFT_COST):
    """Expected tokens per verification round, over expected cost."""
    # expected accepted tokens before first rejection (plus one free token)
    exp_tokens = sum(accept_rate ** i for i in range(1, k + 1)) + 1
    cost = 1 + k * draft_cost          # one large pass + k draft passes
    return exp_tokens / cost


print(f"  draft model costs {DRAFT_COST:.0%} of the large model per token\n")
print(f"  {'accept rate':>13}" + "".join(f"{f'k={k}':>10}" for k in (2, 4, 6, 8)))
for rate in (0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95):
    row = f"  {rate:>12.0%}"
    for k in (2, 4, 6, 8):
        row += f"{spec_speedup(k, rate):>10.2f}x"
    print(row)

print("\n  break-even acceptance rate (speedup > 1.0):")
for k in (2, 4, 6, 8):
    be = None
    for r in np.linspace(0.01, 0.99, 500):
        if spec_speedup(k, float(r)) > 1.0:
            be = float(r)
            break
    print(f"    k={k}: {be:.0%}" if be else f"    k={k}: never")

print("\n  Below the break-even rate the drafting costs more than it saves.")
print("  Above it, you get several tokens for one weight read -- and the output")
print("  is MATHEMATICALLY IDENTICAL to the large model's own sampling, because")
print("  rejected drafts are discarded. It is a pure latency win, not a quality")
print("  trade.")


rule("8. THE CHECKLIST BEFORE YOU PROVISION ANYTHING")

print("  weights + (kv_per_token x context x concurrency) + activations")
print("                                          <= device_memory\n")


def verdict(name, cfg, ctx, users, device=80.0, wbytes=2, kvbytes=2):
    w = weight_gb(cfg, wbytes)
    k = kv_gb(cfg, ctx, users, kvbytes)
    t = w + k + ACT
    binding = "KV cache" if k > w else "weights"
    head = (device - t) / device
    return t, t <= device, binding, head


print(f"  {'scenario':<40}{'total GB':>10}{'fits?':>8}{'binding':>11}"
      f"{'headroom':>11}")
for label, cfg, ctx, users, dev in (
        ("7B fp16, 4k, 8 users, 24 GB", MODELS["7B (MHA)"], 4096, 8, 24.0),
        ("7B fp16, 8k, 32 users, 80 GB", MODELS["7B (MHA)"], 8192, 32, 80.0),
        ("7B GQA, 8k, 32 users, 80 GB", MODELS["7B (GQA-8)"], 8192, 32, 80.0),
        ("13B fp16, 8k, 32 users, 80 GB", MODELS["13B (MHA)"], 8192, 32, 80.0),
        ("70B GQA, 8k, 16 users, 160 GB", MODELS["70B (GQA-8)"], 8192, 16, 160.0)):
    t, ok, binding, head = verdict(label, cfg, ctx, users, dev)
    print(f"  {label:<40}{t:>10.1f}{('YES' if ok else 'no'):>8}{binding:>11}"
          f"{head:>10.0%}")

print("\n  Solve the inequality BEFORE provisioning. Reaching for a bigger")
print("  accelerator without doing this arithmetic is how budgets disappear --")
print("  and note the 'binding' column: it is the KV cache in every row where")
print("  concurrency is meaningful.")
print("\n  Budget 15-25% headroom above the calculation for fragmentation and")
print("  framework overhead. And if you provision cloud accelerators, SHUT")
print("  THEM DOWN when idle -- an idle GPU bills at the same rate as a busy")
print("  one, and a billing alert notifies you rather than capping the spend.")

print("\nDone.")
