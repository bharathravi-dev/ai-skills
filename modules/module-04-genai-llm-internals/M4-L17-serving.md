# M4-L17 — Serving Internals: Quantization, KV Cache, Batching, Memory

| | |
|---|---|
| **Lesson ID** | M4-L17 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L10](M4-L10-transformer-block.md), [M4-L06](M4-L06-context-windows.md) |

---

## 1. Learning objectives

1. **Compute** the memory a model needs to serve, including the KV cache.
2. **Explain** quantization's trade-offs and why it speeds up decoding more than it reduces compute.
3. **Explain** why batching increases throughput without proportionally increasing latency.
4. **Distinguish** the metrics that matter — TTFT, TPOT, throughput — and say which your users feel.
5. **Diagnose** an out-of-memory failure from the arithmetic rather than by trial and error.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Quantization** | Storing weights and activations at lower numerical precision. |
| **KV cache** | Stored keys and values so prefill work is not repeated per token. |
| **Continuous batching** | Adding and removing requests from a batch as they arrive and finish. |
| **TTFT** | Time to first token — dominated by prefill. |
| **TPOT** | Time per output token — dominated by memory bandwidth. |
| **Throughput** | Tokens per second across all concurrent requests. |
| **Memory-bandwidth-bound** | Limited by reading data from memory, not by arithmetic. |
| **GQA / MQA** | Grouped- / multi-query attention: fewer K and V heads, smaller cache. |
| **PagedAttention** | Allocating KV cache in fixed blocks to reduce fragmentation. |
| **Speculative decoding** | A small model drafts tokens; the large one verifies them in parallel. |

---

## 3. Plain-language explanation

### 3.1 The three things that consume memory

```
┌──────────────────────────────────────────────┐
│ MODEL WEIGHTS      fixed, known in advance   │
├──────────────────────────────────────────────┤
│ KV CACHE           grows with tokens × users │  ← the one that surprises people
├──────────────────────────────────────────────┤
│ ACTIVATIONS        transient, per batch      │
└──────────────────────────────────────────────┘
```

**Weights are the number everyone quotes. The KV cache is the number that determines how many users you
can serve** — M4-L06 §7.3 measured a 7B model needing **64 GB of KV cache for one request at 128k
context**, five times its own weights.

### 3.2 Prefill and decode have different bottlenecks

M4-L05 §5.6 introduced this; here is what follows from it operationally.

| | Prefill | Decode |
|---|---|---|
| Processes | The whole prompt at once | One token |
| Parallel? | Yes | No |
| Bound by | **Compute** | **Memory bandwidth** |
| Determines | **TTFT** | **TPOT** |

**Decode reads every parameter from memory to produce one token, and does very little arithmetic with
them.** A 7B model in fp16 is 14 GB; at 2 TB/s of memory bandwidth that is a floor of **7 ms per
token**, no matter how fast the arithmetic units are.

**Three consequences follow, and all three are counter-intuitive:**

1. **Quantization speeds up decoding** — fewer bytes to read. It helps more than the arithmetic saving
   suggests.
2. **Batching is nearly free per request** — the same parameter read serves every request in the batch.
3. **A faster GPU with the same memory bandwidth barely helps decoding.**

### 3.3 Why batching works so well

Reading 14 GB of weights to generate **one** token for **one** user is enormously wasteful. Read them
once and generate a token for **64** users, and the per-user cost of that read falls 64-fold.

**This is why hosted inference is cheaper than running the model yourself** at low volume: the provider
batches your request with everyone else's. It is also why your own deployment at one request at a time
is the worst possible efficiency point.

---

## 4. Analogy

**A librarian fetching a heavy reference book from the basement.** The trip dominates; once the book is
on the desk, answering one question or twenty costs almost the same.

### Where the analogy breaks

1. **The librarian could keep the book out.** Weights must be re-read for every token, because they do
   not fit in the fast on-chip memory.
2. **Twenty questions might be unrelated.** Batched requests genuinely share the same read, exactly.
3. **A librarian gets tired. Throughput scales cleanly with batch size** until memory runs out — and
   then it stops abruptly rather than degrading.
4. **The book has a fixed size. The KV cache grows** with every token every user generates.

---

## 5. Detailed technical explanation

### 5.1 Weight memory

```
bytes = parameters × bytes_per_parameter
```

| Precision | Bytes | 7B model | 70B model |
|---|---|---|---|
| fp32 | 4 | 26.1 GB | 260.8 GB |
| fp16 / bf16 | 2 | 13.0 GB | 130.4 GB |
| int8 | 1 | 6.5 GB | 65.2 GB |
| int4 | 0.5 | 3.3 GB | 32.6 GB |

**Add roughly 10–20% for overhead** — activations, workspace, fragmentation. A 7B model in fp16 needs
about 16 GB in practice, not 13.

### 5.2 KV cache

```
bytes = 2 × layers × kv_heads × head_dim × tokens × bytes_per_value
```

The `2` is for K and V. **Note `kv_heads`, not `heads`** — that distinction is what GQA exploits.

| Model | Layers | Heads | KV per token (fp16) | At 8k | At 128k |
|---|---|---|---|---|---|
| 7B (MHA) | 32 | 32 | 512 KB | 4.0 GB | 64.0 GB |
| 7B (GQA, 8 kv heads) | 32 | 8 | **128 KB** | **1.0 GB** | **16.0 GB** |
| 70B (MHA) | 80 | 64 | 2,560 KB | 20.0 GB | 320.0 GB |

**GQA reduces the cache 4× here at almost no quality cost, which is why it is now standard.** §7.3
computes the concurrency this buys.

### 5.3 Quantization

| Method | What it does | Typical quality cost |
|---|---|---|
| **fp16 / bf16** | Half precision | Negligible; the default |
| **int8** | 8-bit weights | Small |
| **int4** (GPTQ, AWQ) | 4-bit weights, calibrated | Noticeable but often acceptable |
| **KV-cache quantization** | Lower precision for the cache | Small; directly buys concurrency |

`[UNVERIFIED — quality cost is model- and task-specific. Measure on your evaluation set.]`

**Why quantization speeds up decode disproportionately.** Decode is memory-bandwidth-bound, so halving
the bytes read roughly halves the time — even though int8 arithmetic is not twice as fast as fp16 on
all hardware. **You are buying bandwidth, not FLOPs.**

**Where it hurts:** long-tail accuracy, rare languages, arithmetic and precise formatting degrade
before headline benchmark scores do. **Evaluate on your own task, not on a benchmark table** (M3-L14).

### 5.4 Batching

**Static batching** waits for a full batch, then runs it. Every request waits for the slowest.

**Continuous batching** adds a new request as soon as any request finishes, keeping the accelerator
busy. This is what modern serving frameworks do, and it typically improves throughput several-fold over
static batching. `[UNVERIFIED — the exact factor depends heavily on the workload]`

**The trade:** larger batches raise throughput and raise per-request latency. §7.3 measures the curve so
you can choose a point rather than guess.

### 5.5 The metrics, and which one your user feels

| Metric | Definition | Driven by | User perceives |
|---|---|---|---|
| **TTFT** | Time to first token | Prefill; prompt length | **"Is it working?"** |
| **TPOT** | Time per output token | Memory bandwidth | **Reading speed** |
| **Total latency** | `TTFT + TPOT × tokens` | Both | Time to a complete answer |
| **Throughput** | Tokens/second, all requests | Batch size | **Nothing — it is your cost** |

**Optimising throughput can make individual users' experience worse.** Larger batches raise both TTFT
and TPOT while lowering cost per token. **Decide which you are optimising before you tune anything**,
because the two pull in opposite directions.

**Streaming changes what matters.** With streaming, TTFT dominates the perception of speed — a response
that starts in 200 ms and streams at 30 tokens/s feels faster than one that starts in 2 s and arrives
instantly at 1 s, even though the second finishes sooner.

### 5.6 Speculative decoding

A small draft model proposes several tokens; the large model verifies them **in parallel** in one
forward pass. Accepted tokens are kept; the first rejection restarts from there.

**Why it wins:** verifying `k` tokens costs about the same as generating one, because decode is
bandwidth-bound rather than compute-bound. **You get several tokens for one weight read.** Output is
mathematically identical to the large model's own sampling. `[UNVERIFIED — speedup depends on draft
acceptance rate]`

### 5.7 Diagnosing out-of-memory

**Do the arithmetic before touching a config file:**

```
weights + (kv_per_token × context × concurrency) + activations ≤ device_memory
```

| Lever | Effect |
|---|---|
| Quantize weights | Large one-off saving |
| Quantize the KV cache | Directly buys concurrency |
| Reduce max context | Linear reduction in cache |
| Reduce concurrency | Linear |
| Use a GQA model | 4–8× cache reduction |
| PagedAttention | Recovers fragmentation waste |

**Solve the inequality. Reaching for a bigger GPU before doing that is how budgets disappear.**

### 5.8 Assumptions and limitations

- Real frameworks add overheads this arithmetic omits. Treat results as a floor.
- Quantization quality is model- and task-specific.
- Serving-framework performance changes rapidly; benchmark rather than trusting a table.

---

## 6. Worked example — will this fit, and how many users?

**The question:** *"Can we serve a 13B model on one 80 GB accelerator, at 8k context, for 32 concurrent
users?"*

**Step 1 — weights.** 13B in fp16 (using GiB throughout, as the lab does):

```
13e9 × 2 bytes = 26e9 bytes = 24.2 GiB
```

**Step 2 — KV cache per token.** 40 layers, 40 heads, head_dim 128, fp16, no GQA:

```
2 × 40 × 40 × 128 × 2 bytes = 819,200 bytes ≈ 800 KB per token
```

**Step 3 — KV cache at 8k context, 32 users:**

```
800 KiB × 8,192 × 32 = 200.0 GiB
```

**Step 4 — the total.**

```
24.2 + 200.0 + ~4 (activations) = 228.2 GiB
```

**Against 80 GiB. It does not fit — it is 2.9× over.** And the KV cache is **88%** of the requirement,
not the weights everyone quotes.

**Step 5 — work the levers in order of cost to you:**

| Change | New total | Fits? | Saving |
|---|---|---|---|
| Baseline | 228.2 GiB | ✗ | — |
| int8 weights | 216.1 GiB | ✗ | **5%** |
| int4 weights | 210.1 GiB | ✗ | 8% |
| Halve context to 4k | 128.2 GiB | ✗ | 44% |
| Halve concurrency to 16 | 128.2 GiB | ✗ | 44% |
| **GQA-8 model** | **68.2 GiB** | ✅ | **70%** |
| **GQA-8 + int8 KV cache** | **48.2 GiB** | ✅ | **79%** |

**Only the GQA rows fit, and GQA is not the lever people reach for first.** Quantizing the weights —
the instinct, because that is the number in the model's name — saves **5%** of a 228 GiB problem. GQA
saves **70%**.

**Step 6 — the general lesson.** The instinct is to quantize the weights, because that is the number in
the model's name. **At long context and real concurrency, the KV cache dominates, and the levers that
matter are the ones that shrink it:** GQA, KV-cache quantization, shorter context, fewer concurrent
users.

**Step 7 — check the arithmetic against reality.** These are floors. Real frameworks add fragmentation,
workspace and framework overhead, and PagedAttention exists precisely because naive allocation wastes a
substantial fraction. **Budget 15–25% headroom above the calculation.**

---

## 7. Practical activity

**File:** [`labs/m4/l17_serving.py`](../../labs/m4/l17_serving.py)

**No API key, no network, no GPU.**

```bash
source .venv/bin/activate
python labs/m4/l17_serving.py
```

Computes §6's arithmetic and every lever, measures the batching throughput/latency curve on real matrix
operations, demonstrates the memory-bandwidth argument, and models speculative decoding's speedup
against draft acceptance rate.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-09. **No GPU, no cloud resources, £0.00.**

```text

============================================================================
1. WEIGHT MEMORY: THE NUMBER EVERYONE QUOTES
============================================================================
  model               fp32      fp16      int8      int4    +15% overhead (fp16)
  7B                 26.1G     13.0G      6.5G      3.3G                   15.0G
  13B                48.4G     24.2G     12.1G      6.1G                   27.8G
  70B               260.8G    130.4G     65.2G     32.6G                  149.9G

  Real deployments need 10-20% above this for workspace and
  fragmentation. A 7B model in fp16 needs about 15 GB, not 13.

============================================================================
2. KV CACHE: THE NUMBER THAT DECIDES HOW MANY USERS YOU SERVE
============================================================================
  kv_bytes = 2 x layers x KV_HEADS x head_dim x tokens x bytes

  model           layers  kv heads   per token    8k ctx   32k ctx   128k ctx
  7B (MHA)            32        32        512K      4.0G     16.0G      64.0G
  7B (GQA-8)          32         8        128K      1.0G      4.0G      16.0G
  13B (MHA)           40        40        800K      6.2G     25.0G     100.0G
  13B (GQA-8)         40         8        160K      1.2G      5.0G      20.0G
  70B (MHA)           80        64       2560K     20.0G     80.0G     320.0G
  70B (GQA-8)         80         8        320K      2.5G     10.0G      40.0G

  GQA reduces the cache 4x by using 8 KV heads instead of 32.
  Note it does NOT reduce the weights at all -- the query heads are
  unchanged. It is purely a cache optimisation, which is exactly why
  it is the right lever for a cache problem.

============================================================================
3. THE WORKED EXAMPLE: WILL A 13B MODEL FIT ON 80 GB?
============================================================================
  question: 13B model, 8,192 context, 32 concurrent users, 80 GB device

  component                           GB     share
  weights (fp16)                    24.2       11%
  KV cache                         200.0       88%
  activations (estimate)             4.0        2%
  TOTAL                            228.2

  device capacity 80 GB -> DOES NOT FIT (2.9x over)

  The KV cache is 88% of the requirement. The weights --
  the number in the model's name -- are 11%.

  working the levers:
  change                               weights        KV     total   fits?    saving
  baseline                                24.2     200.0     228.2      no       0%
  int8 weights                            12.1     200.0     216.1      no       5%
  int4 weights                             6.1     200.0     210.1      no       8%
  halve context (4k)                      24.2     100.0     128.2      no      44%
  halve concurrency (16)                  24.2     100.0     128.2      no      44%
  GQA-8 model                             24.2      40.0      68.2     YES      70%
  GQA-8 + int8 KV                         24.2      20.0      48.2     YES      79%

  Only the GQA rows fit. Quantizing the WEIGHTS -- the instinct, because
  that is the number in the model's name -- saves 5%
  of a 228 GB problem. GQA saves 70%.

  DO NOT QUANTIZE WEIGHTS TO FIX A KV-CACHE PROBLEM.

============================================================================
4. HOW MANY USERS FIT?  (solving the inequality)
============================================================================
  concurrent users, fp16 weights. The 7B and 13B models are sized on
  one 80 GiB device; a 70B model's weights alone are
  130 GiB, so it is sized on 160 GiB.

  model            device      2k      8k     32k     128k
  7B (MHA)            80G      62      15       3       0
  7B (GQA-8)          80G     251      62      15       3
  13B (MHA)           80G      33       8       2       0
  13B (GQA-8)         80G     165      41      10       2
  70B (MHA)          160G       5       1       0       0
  70B (GQA-8)        160G      40      10       2       0

  the same, with the KV CACHE quantized to int8:
  model            device      2k      8k     32k     128k
  7B (MHA)            80G     125      31       7       1
  7B (GQA-8)          80G     503     125      31       7
  13B (MHA)           80G      66      16       4       1
  13B (GQA-8)         80G     331      82      20       5
  70B (MHA)          160G      10       2       0       0
  70B (GQA-8)        160G      81      20       5       1

  Compare within a model size at 8k context:
    13B: MHA 8 users -> GQA-8 41 users  (5x)
    70B: MHA 1 users -> GQA-8 10 users  (10x)

  That is the difference between a demo and a product, from one
  architectural choice that costs almost nothing in quality.

  Note also the ZERO rows: a 70B model in fp16 needs 130 GiB for
  weights alone, so it does not fit on an 80 GiB device AT ALL, at any
  context or concurrency. Some deployments are ruled out by arithmetic
  before any tuning is possible.

============================================================================
5. WHY BATCHING WORKS: THE MEMORY-BANDWIDTH ARGUMENT, MEASURED
============================================================================
  Decode reads EVERY parameter to produce ONE token. If that read is
  the bottleneck, serving N users in a batch should cost barely more
  than serving one. Measuring on real matrix operations:

  weight matrix 2048x2048 float32 = 16.0 MB

    batch    time/call   time/request    throughput  vs batch 1
        1     2557.5us      2557.46us          391/s        1.0x
        2    15047.5us      7523.77us          133/s        0.3x
        4    16049.7us      4012.43us          249/s        0.6x
        8    12789.1us      1598.64us          626/s        1.6x
       16    20024.7us      1251.54us          799/s        2.0x
       32    24951.6us       779.74us         1282/s        3.3x
       64    22131.2us       345.80us         2892/s        7.4x
      128    42541.5us       332.36us         3009/s        7.7x

  Time per REQUEST falls sharply as the batch grows, because the same
  weight read serves every row. This is why hosted inference is cheaper
  than self-hosting at low volume -- the provider batches your request
  with everyone else's -- and why your own deployment at one request at
  a time is the worst efficiency point available.

============================================================================
6. THROUGHPUT vs LATENCY: THEY PULL IN OPPOSITE DIRECTIONS
============================================================================
  Modelling a queue: requests arrive, wait for a batch slot, then
  generate. Larger batches raise throughput AND raise latency.

    batch   ms/token   latency (s)   tokens/s total   cost/token
        1      20.00          6.00               50      20.000m
        4      20.72          6.22              193       5.180m
        8      21.68          6.50              369       2.710m
       16      23.60          7.08              678       1.475m
       32      27.44          8.23             1166       0.857m
       64      35.12         10.54             1822       0.549m
      128      50.48         15.14             2536       0.394m

  Throughput rises 51x from batch 1 to 128,
  and per-request latency rises 2.5x.

  There is no batch size that is best. You are choosing between COST
  (throughput, which you feel) and LATENCY (which your users feel).
  Decide which you are optimising BEFORE tuning anything.

============================================================================
7. SPECULATIVE DECODING
============================================================================
  A small draft model proposes k tokens; the large model verifies all k
  in ONE forward pass. Verification costs about as much as generating
  one token, because decode is bandwidth-bound, not compute-bound.

  draft model costs 8% of the large model per token

    accept rate       k=2       k=4       k=6       k=8
           20%      1.07x      0.95x      0.84x      0.76x
           40%      1.34x      1.25x      1.12x      1.02x
           60%      1.69x      1.75x      1.64x      1.51x
           70%      1.89x      2.10x      2.07x      1.95x
           80%      2.10x      2.55x      2.67x      2.64x
           90%      2.34x      3.10x      3.53x      3.74x
           95%      2.46x      3.43x      4.08x      4.51x

  break-even acceptance rate (speedup > 1.0):
    k=2: 14%
    k=4: 24%
    k=6: 33%
    k=8: 39%

  Below the break-even rate the drafting costs more than it saves.
  Above it, you get several tokens for one weight read -- and the output
  is MATHEMATICALLY IDENTICAL to the large model's own sampling, because
  rejected drafts are discarded. It is a pure latency win, not a quality
  trade.

============================================================================
8. THE CHECKLIST BEFORE YOU PROVISION ANYTHING
============================================================================
  weights + (kv_per_token x context x concurrency) + activations
                                          <= device_memory

  scenario                                  total GB   fits?    binding   headroom
  7B fp16, 4k, 8 users, 24 GB                   33.0      no   KV cache      -38%
  7B fp16, 8k, 32 users, 80 GB                 145.0      no   KV cache      -81%
  7B GQA, 8k, 32 users, 80 GB                   49.0     YES   KV cache       39%
  13B fp16, 8k, 32 users, 80 GB                228.2      no   KV cache     -185%
  70B GQA, 8k, 16 users, 160 GB                174.4      no    weights       -9%

  Solve the inequality BEFORE provisioning. Reaching for a bigger
  accelerator without doing this arithmetic is how budgets disappear --
  and note the 'binding' column: it is the KV cache in every row where
  concurrency is meaningful.

  Budget 15-25% headroom above the calculation for fragmentation and
  framework overhead. And if you provision cloud accelerators, SHUT
  THEM DOWN when idle -- an idle GPU bills at the same rate as a busy
  one, and a billing alert notifies you rather than capping the spend.

Done.
```

### 7.3 Reading the result

**Section 2 shows what GQA actually changes.** A 7B model at 128k context needs **64.0 GiB** of KV
cache with multi-head attention and **16.0 GiB** with 8 KV heads — a **4× reduction**. Note that it
does not reduce the weights at all; the query heads are unchanged. **It is purely a cache
optimisation, which is exactly why it is the right lever for a cache problem.**

**Section 3 reproduces §6 and works every lever.** The KV cache is **88%** of the requirement and the
weights are **11%**. Quantizing weights to int8 saves **5%**; to int4, **8%**. GQA saves **70%**.

**Do not quantize weights to fix a KV-cache problem** — a sentence worth carrying into your next
capacity meeting.

**Section 4 turns the arithmetic into a product answer:**

| Model | 2k | 8k | 32k | 128k |
|---|---|---|---|---|
| 13B (MHA), 80 GiB | 33 | **8** | 2 | 0 |
| 13B (GQA-8), 80 GiB | 165 | **41** | 10 | 2 |
| 70B (MHA), 160 GiB | 5 | **1** | 0 | 0 |
| 70B (GQA-8), 160 GiB | 40 | **10** | 2 | 0 |

**At 8k context, GQA takes a 13B model from 8 concurrent users to 41 — and a 70B model from 1 to 10.**
That is the difference between a demo and a product, from one architectural choice costing almost
nothing in quality.

And note the zero rows: **a 70B model in fp16 needs 130 GiB for weights alone**, so it does not fit on
an 80 GiB device at any context or concurrency. **Some deployments are ruled out by arithmetic before
any tuning is possible** — which is a good thing to discover on paper rather than after provisioning.

**Section 5 measures the batching argument on real matrix operations**, and the per-request time falls
sharply as the batch grows because the same weight read serves every row. This is why hosted inference
is cheaper than self-hosting at low volume — the provider batches your request with everyone else's —
and why **your own deployment at one request at a time is the worst efficiency point available**.

**Section 6 shows throughput and latency pulling in opposite directions.** Throughput rises steeply
from batch 1 to 128 while per-request latency rises with it. **There is no batch size that is best.**
You are choosing between cost (throughput, which *you* feel) and latency (which your *users* feel), and
you should decide which you are optimising before tuning anything.

**Section 7 models speculative decoding** and finds the break-even acceptance rates. Below them the
drafting costs more than it saves; above them you get several tokens for one weight read — and the
output is **mathematically identical** to the large model's own sampling, because rejected drafts are
discarded. **It is a pure latency win, not a quality trade**, which is unusual enough to be worth
remembering.

**Section 8 is the checklist.** Note the `binding` column: **it is the KV cache in every row where
concurrency is meaningful.** Solve the inequality before provisioning, and budget 15–25% headroom for
fragmentation.

---

## 8. Common mistakes and troubleshooting

1. **Sizing hardware from weights alone.** The KV cache usually dominates.
2. **Quantizing weights to fix a KV-cache problem.**
3. **Optimising throughput when users care about TTFT.**
4. **Benchmarking at batch size 1** and extrapolating.
5. **Assuming quantization is free.** Measure on your task.
6. **Ignoring GQA** when choosing a model for long context.
7. **Not leaving headroom** for fragmentation.

| Symptom | Likely cause | Fix |
|---|---|---|
| OOM at high concurrency, fine alone | KV cache scales with users | Quantize the cache; GQA; shorter context |
| Throughput fine, users complain | TTFT too high | Shorter prompts; prefix caching; smaller batches |
| Quantized model fails on edge cases | Long-tail degradation | Evaluate on your own set |
| Faster GPU did not speed up generation | Decode is bandwidth-bound | Buy bandwidth, or quantize |
| Latency rose after a throughput change | Larger batches | Choose a point on the curve deliberately |
| Memory usage exceeds the calculation | Fragmentation | PagedAttention; 15–25% headroom |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Do the memory arithmetic before provisioning. An instance sized from the weights alone will
  OOM under real concurrency, and discovering that in production is expensive in more than money.
- **Cost.** **Self-hosting is not automatically cheaper.** A provider batches your requests with
  everyone else's; a private deployment at low utilisation pays for an idle accelerator. Compute the
  break-even volume (M4-L18).
- **Privacy.** Batching processes multiple users' data in the same forward pass. Framework isolation
  bugs are a real class of vulnerability — a masking error can leak across a batch boundary (M4-L08
  §9). Verify isolation if you are multi-tenant.
- **Reliability.** KV cache exhaustion causes requests to be queued or evicted, appearing as latency
  spikes rather than errors. Monitor cache utilisation, not just GPU utilisation.
- **Cost.** If you provision cloud accelerators for this, **shut them down when not in use** — an idle
  GPU instance bills at the same rate as a busy one. Set a budget alert, and remember it notifies
  rather than caps.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Compute fp16 weight memory for 7B, 13B and 70B models.
2. Compute KV cache per token for a 32-layer, 32-head, head_dim 128 model in fp16.
3. At 8k context, how many concurrent users fit in 80 GB with a 7B fp16 model?
4. Why does quantization speed up decoding more than the arithmetic saving suggests?
5. Which metric does a user with streaming enabled feel most?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab and reproduce §6's 239.7 GB figure and every lever.
2. Write a function `fits(model, context, concurrency, device_gb)` returning a verdict and the binding
   constraint.
3. Measure throughput and per-request latency across batch sizes 1–64 and identify the knee.
4. Compute the concurrency GQA buys at 8k, 32k and 128k context.
5. Compute the break-even request volume where self-hosting beats per-token pricing, stating your
   assumptions.

### Exercise 3 — Challenge (~45 min)

1. Build a serving calculator taking a model config and a device, and returning maximum concurrency at
   several context lengths, with the binding constraint named.
2. Model speculative decoding: given a draft acceptance rate and relative model costs, compute the
   speedup and find the acceptance rate at which it stops paying.
3. Measure the memory-bandwidth argument empirically: time matrix operations at sizes that fit in cache
   versus those that do not, and report the ratio.
4. Model continuous versus static batching under a realistic arrival distribution and report the
   utilisation difference.
5. Write the capacity plan for 10,000 daily requests at a 4k prompt and 500-token output, stating the
   hardware, the concurrency, the expected TTFT and the assumptions you would need to verify.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l17).)*

**Q1.** A 7B model in fp16 needs how much memory for weights alone?

- A. 3.3 GB  B. 26.1 GB  C. 13.0 GB  D. 7.0 GB

**Q2.** The KV cache grows with:

- A. The model's parameter count and nothing else.
- B. The number of tokens multiplied by concurrent requests.
- C. The square of the sequence length, like attention.
- D. The batch size only; context length has no effect.

**Q3.** Decode is bound primarily by:

- A. Arithmetic throughput on the accelerator's tensor cores.
- B. Memory bandwidth, reading all weights per token.
- C. The size of the vocabulary in the output projection.
- D. Network round-trip time between client and server.

**Q4.** Why does batching improve throughput so much?

- A. Batched requests share the same weight read from memory.
- B. The accelerator switches to a faster numerical precision.
- C. Attention becomes linear rather than quadratic in a batch.
- D. The KV cache is shared between the batched requests.

**Q5.** In §6, the KV cache was what share of the memory requirement?

- A. About 25%  B. About 50%  C. About 87%  D. About 10%

**Q6.** Which change fixed §6's memory problem?

- A. Quantizing the model weights from fp16 to int8.
- B. Halving the maximum supported context length.
- C. Halving the number of concurrent users served.
- D. Switching to a model using grouped-query attention.

**Q7.** Quantization speeds up decoding disproportionately because:

- A. Integer arithmetic is inherently faster than floating point.
- B. Quantized models have fewer parameters to process.
- C. Decode is bandwidth-bound, and there are fewer bytes to read.
- D. Quantization allows a larger batch size to be used.

**Q8.** A user with streaming enabled perceives speed mainly through:

- A. Total throughput across all concurrent requests.
- B. Time to first token, then the streaming rate.
- C. The total time until the response is complete.
- D. The number of tokens the model generated overall.

**Q9.** Speculative decoding works because:

- A. The draft model is more accurate than the large one.
- B. Verifying several tokens costs about as much as generating one.
- C. It reduces the number of parameters that must be read.
- D. Draft tokens are cached and reused across requests.

**Q10.** Your model OOMs at 32 concurrent users but runs fine alone. The first thing to compute is:

- A. Whether a larger accelerator is available in your region.
- B. The KV cache requirement at that context and concurrency.
- C. The accuracy cost of quantizing the model's weights.
- D. The average prompt length across recent production traffic.

**Q11.** *(Written, rubric-graded.)* In under 120 words, respond to a colleague who says "we'll quantize
to int4 so we can serve 32 users on one GPU."

---

## 12. Revision notes

- **Three memory consumers: weights, KV cache, activations.** Weights are the quoted number; **the KV
  cache decides how many users you serve.**
- **`kv_bytes = 2 × layers × kv_heads × head_dim × tokens × bytes`.** Note **`kv_heads`** — that is what
  GQA shrinks, typically **4–8×** at almost no quality cost.
- **Prefill is compute-bound and sets TTFT. Decode is memory-bandwidth-bound and sets TPOT.**
- **Because decode is bandwidth-bound:** quantization helps more than the FLOP saving suggests;
  batching is nearly free per request; a faster GPU with the same bandwidth barely helps.
- **§6's result: the KV cache was 87% of the requirement.** Quantizing weights saved **5%**; GQA saved
  **70%**. **Do not quantize weights to fix a KV-cache problem.**
- **Throughput and latency pull in opposite directions.** Decide which you are optimising first.
- **With streaming, TTFT dominates perception**, not total time.
- **Speculative decoding gets several tokens per weight read**, with output identical to normal
  sampling.
- **Solve `weights + kv×context×concurrency + activations ≤ device` before provisioning**, and leave
  **15–25% headroom** for fragmentation.
- **Self-hosting is not automatically cheaper** — a provider batches you with everyone else.

---

## 13. Completion checklist

- [ ] I can compute weight and KV-cache memory from a model config.
- [ ] I reproduced §6's 239.7 GB and identified the binding constraint.
- [ ] I can explain why decode is bandwidth-bound and what follows.
- [ ] I know why quantizing weights does not fix a KV-cache problem.
- [ ] I can name the four serving metrics and who feels each.
- [ ] I can explain speculative decoding in one sentence.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Kwon et al. (2023), *Efficient Memory Management for LLM Serving with PagedAttention* (vLLM).
  <https://arxiv.org/abs/2309.06180> `[UNVERIFIED]`
- Ainslie et al. (2023), *GQA: Training Generalized Multi-Query Transformer Models*.
  <https://arxiv.org/abs/2305.13245> `[UNVERIFIED]`
- Leviathan et al. (2022), *Fast Inference from Transformers via Speculative Decoding*.
  <https://arxiv.org/abs/2211.17192> `[UNVERIFIED]`
- Dettmers et al. (2022), *LLM.int8()*. <https://arxiv.org/abs/2208.07339> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L18 — Hosted vs Local Models](M4-L18-hosted-vs-local.md)

You can size a deployment. Next: whether you should run one at all — the decision this arithmetic
actually feeds.
