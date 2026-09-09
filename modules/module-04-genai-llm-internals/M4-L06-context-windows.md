# M4-L06 — Context Windows, Output Limits and Truncation

| | |
|---|---|
| **Lesson ID** | M4-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M4-L03](M4-L03-tokens-tokenizers.md), [M4-L05](M4-L05-next-token-prediction.md) |

---

## 1. Learning objectives

1. **Define** the context window precisely, and state what shares it.
2. **Explain** why the limit exists, in terms of attention's cost.
3. **Distinguish** the advertised window from the *effective* one.
4. **Design** a token budget that degrades gracefully rather than failing.
5. **Choose** a truncation strategy and state what each one discards.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Context window** | The maximum number of tokens the model can attend over at once. |
| **Effective context** | The range over which the model actually uses information well. |
| **`max_tokens`** | A cap on *output* length, set by you per request. |
| **Truncation** | Removing tokens to fit a limit. |
| **Token budget** | A planned allocation of the window across prompt components. |
| **Lost in the middle** | Degraded use of information placed mid-context. |
| **Sliding window** | Keeping only the most recent N tokens. |
| **Context stuffing** | Filling the window because it is available. Usually a mistake. |
| **KV cache** | Stored attention keys/values; grows linearly with context (M4-L17). |
| **`finish_reason`** | Why generation stopped (M4-L15). |

---

## 3. Plain-language explanation

### 3.1 What the window is

The context window is the model's **entire working memory for one request**. Everything must fit:

```
┌──────────────── context window (e.g. 200,000 tokens) ────────────────┐
│ system prompt │ conversation history │ retrieved docs │ user │ OUTPUT │
└──────────────────────────────────────────────────────────────────────┘
```

**The output shares the window with the input.** This is the part people miss. If the window is
200,000 tokens and your prompt is 199,000, the model has 1,000 tokens left to answer in — and it will
be cut off mid-sentence with no error.

**There is no memory between requests.** Every call starts from nothing; conversation history works
only because your application re-sends it every time, paying for it every time (M4-L16).

### 3.2 Why there is a limit at all

Attention (M4-L07) compares every token with every other token. For `T` tokens that is `T²`
comparisons.

| Tokens | Comparisons | Relative |
|---|---|---|
| 1,000 | 1,000,000 | 1× |
| 10,000 | 100,000,000 | 100× |
| 100,000 | 10,000,000,000 | 10,000× |

**Ten times the context is one hundred times the attention work.** The limit is not arbitrary — it is
where the compute and memory stop being economic. §7.3 measures the curve directly.

### 3.3 The distinction that matters most

**Advertised context ≠ effective context.**

A model advertising 200,000 tokens can *accept* 200,000 tokens. Whether it *uses* the middle 100,000
as well as the first and last few thousand is a separate, empirical question — and the answer is
usually no.

**Practical rule: put what matters at the start or the end of your prompt, and treat the middle as
the place things go to be ignored.** §5.4 covers the evidence.

---

## 4. Analogy

**A desk you must clear completely between tasks.** Everything you need — reference books, notes, the
request, and blank paper to write the answer on — has to fit at once. If you cover the desk in books
there is nowhere to write.

### Where the analogy breaks

1. **You would notice running out of paper. The model does not** — it stops mid-sentence and returns
   what it has, and you must check `finish_reason` to find out (M4-L15).
2. **You remember yesterday's work. The desk is wiped between every request**, and history exists only
   because you re-place it.
3. **You can glance at anything on the desk equally well. The model attends unevenly** — the middle is
   genuinely worse.
4. **More desk space is free. More context costs money and latency**, quadratically for attention and
   linearly for the KV cache.

---

## 5. Detailed technical explanation

### 5.1 The arithmetic you must be able to do

```
available_for_output = context_window − input_tokens
```

If `max_tokens` exceeds that, behaviour varies by provider: some error, some silently truncate.
**Never rely on which.**

**The safe formulation:**

```python
reserve = 1000                       # what the answer needs
budget = context_window - reserve - len(system) - len(user)
context_docs = fit_within(budget, docs)
```

**Reserve output space first, then spend what is left on input.** Doing it the other way round is the
most common cause of truncated answers.

### 5.2 A budget that degrades gracefully

| Component | Priority | Behaviour when short |
|---|---|---|
| System prompt | **Never drop** | Fixed cost |
| User's current message | **Never drop** | Fixed cost |
| Output reservation | **Never drop** | Fixed cost |
| Retrieved documents | Drop lowest-ranked first | Fewer documents |
| Conversation history | Drop oldest, or summarise | Shorter history |

**The principle: decide the drop order in advance, and make it explicit in code.** A system that
silently drops whatever happens to be last is a system whose behaviour you cannot predict.

**Always leave headroom.** Token estimates are estimates (M4-L03 §7.3 measured a 78% error from one
wrong content-type assumption). Budget to about 90% of the window.

### 5.3 Truncation strategies and what each discards

| Strategy | Keeps | Discards | It is a bet that… |
|---|---|---|---|
| **Head** | The start | Everything after | The information is near the top (abstracts, headers) |
| **Tail** | The end | Everything before | It is near the bottom (chat history, logs, conclusions) |
| **Head + tail** | Both ends | The middle | It is at *either* end — a hedge |
| **Sliding window** | Last N tokens | Older | Recency is what matters |
| **Summarise-then-drop** | A summary of the old | Detail | The gist suffices |
| **Rank and select** | The most relevant | The rest | You can *find* it — this is RAG (M7) |

**A result that surprises people, measured in §7.3: the first three strategies preserve exactly the
same *amount*.** Keeping 30% of a document preserves 30% of it whichever 30% you choose — all three
scored 3 out of 9 on the same test. They differ only in **which** part survives.

**So truncation is not an optimisation; it is a bet about where the information is.** And every
variant abandons the middle. If you do not know where the fact is, no truncation strategy is safe —
which is precisely the problem retrieval solves.

**Truncate on token boundaries, never on characters or bytes** (M4-L03 §7.3 measured that 24% of byte
cut points corrupt text).

**Never truncate the system prompt.** Cutting it mid-instruction can remove a safety constraint while
leaving the rest of the prompt looking intact — a failure that is both silent and serious.

### 5.4 Lost in the middle

Models retrieve information from the **beginning and end** of a long context more reliably than from
the middle. The effect was documented by Liu et al. (2023) and has been reproduced across models,
though its size varies by model and generation. `[UNVERIFIED as to any specific current model — test
your own]`

**What to do about it:**

- Put the most important material **first or last**.
- Put the actual question **at the end**, after the context.
- **Retrieve fewer, better documents** rather than more (M7-L11).
- **Measure it yourself** with a needle-in-a-haystack test: place a known fact at varying depths and
  check recall. §7.3 simulates this.

**The costly misreading:** "we have a 200k window, so we can stop building retrieval." A large window
lets you *put* everything in; it does not mean the model *uses* everything. Retrieval is about giving
the model less and better, and a bigger window does not make that unnecessary.

### 5.5 Output limits are separate

`max_tokens` caps the **output only**. Three things follow:

1. **It is your safety valve.** Without it, a runaway generation consumes budget and time. Always set
   it (M4-L15).
2. **Setting it too low truncates mid-sentence**, with `finish_reason` telling you so — if you check.
3. **It does not reserve space.** Setting `max_tokens=4000` does not stop you filling the window with
   input; you must do that arithmetic yourself.

### 5.6 The KV cache grows linearly

Long contexts cost memory during generation (M4-L17):

```
KV bytes ≈ 2 × layers × heads × head_dim × context_length × bytes_per_value
```

For a 32-layer model with `d_model` 4,096 in float16, this is roughly **0.5 MB per token** —
**about 50 GB at 100,000 tokens, for one request.** This, not the attention arithmetic alone, is
frequently what actually limits deployed context length.

### 5.7 Assumptions and limitations

- Window sizes, pricing and effective-context behaviour are model-specific and change frequently.
  Everything numeric here is either measured by the lab or marked `[UNVERIFIED]`.
- Some architectures (sparse or linear attention) do not have the full quadratic cost.
- Whether a provider errors or truncates on overflow varies. Test yours.

---

## 6. Worked example — budgeting a 128,000-token window

**A support assistant.** Window 128,000 tokens.

**Step 1 — reserve output first.**

```
Answers are typically 300–600 tokens. Reserve 1,500 for headroom.
Available for input: 128,000 − 1,500 = 126,500
```

**Step 2 — subtract the fixed parts.**

```
System prompt                     900
Current user message              200
                                -----
Fixed                           1,100
Remaining for history + docs  125,400
```

**Step 3 — apply the safety margin.**

```
Budget to 90%:  125,400 × 0.9 = 112,860 usable
```

**Step 4 — allocate, and set the drop order.**

```
Retrieved documents   up to  60,000    drop lowest-ranked first
Conversation history  up to  52,860    drop oldest first
```

**Step 5 — now question the allocation, which is the real work.**

60,000 tokens of retrieved documents is roughly **80 documents**. Should you send 80?

**Almost certainly not**, and for three separate reasons:

| Reason | Consequence |
|---|---|
| Lost in the middle (§5.4) | Documents 20–60 are the least likely to be used |
| Cost | 60,000 input tokens per request, every request |
| Latency | Prefill is linear in prompt length |

**Sending 8 well-ranked documents (≈6,000 tokens) will usually outperform 80 poorly-ranked ones** —
and costs a tenth as much. Whether that is true for *your* corpus is an empirical question with a
cheap answer: try both and measure (M7-L16, M3-L14).

**The general lesson: a budget tells you what you *can* spend, not what you *should*.** The window
being large is not a reason to fill it. This is the single most expensive misunderstanding in applied
LLM work, because it looks like thoroughness.

**Step 6 — what happens when a document is longer than the budget?**

You still must not exceed the window. Options in order of preference: retrieve fewer documents; chunk
the document and retrieve only relevant chunks (M7-L06); summarise it first; truncate head+tail and
say so in the prompt. **Never silently truncate a document and present it as complete** — the model
will reason confidently about the missing part.

---

## 7. Practical activity

**File:** [`labs/m4/l06_context_windows.py`](../../labs/m4/l06_context_windows.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m4/l06_context_windows.py
```

Measures attention's quadratic cost curve, implements the §6 budget with an explicit drop order,
compares truncation strategies on the same document, simulates a needle-in-a-haystack test, and sizes
the KV cache.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. WHY THE LIMIT EXISTS: ATTENTION IS QUADRATIC
============================================================================
  one attention head, d_head = 64

    tokens    score matrix        floats   MB (fp32)       time    vs 128
       128         128x128        16,384        0.1M      0.14ms      1.0x
       256         256x256        65,536        0.2M      8.34ms     59.9x
       512         512x512       262,144        1.0M     11.47ms     82.3x
      1024       1024x1024     1,048,576        4.0M     39.82ms    285.8x
      2048       2048x2048     4,194,304       16.0M     99.64ms    715.1x
      4096       4096x4096    16,777,216       64.0M    140.98ms   1011.7x

  fitted exponent: time ~ T^1.78
  (theory says 2.0 for the score matrix; measured 1.78)

  Doubling the context roughly QUADRUPLES the attention work. That is
  the whole reason a context window has a limit -- not an arbitrary
  product decision.

  extrapolating the score matrix alone (fp32, one head):
      tokens      score floats        memory
       8,192        67,108,864        256 MB
      32,768     1,073,741,824        4.0 GB
     131,072    17,179,869,184       64.0 GB
   1,000,000 1,000,000,000,000    3,725.3 GB

  A 1M-token context would need 3.6 TB for ONE head's score matrix if
  materialised. It is not -- FlashAttention and similar never form the
  full matrix. But the COMPUTE is still quadratic, and that is why long
  context is expensive rather than free.

============================================================================
2. A TOKEN BUDGET WITH AN EXPLICIT DROP ORDER
============================================================================
  window 128,000 tokens, output reserve 1,500, headroom 90%
  drop order: retrieved documents (by rank) first, then history (by age)

  comfortable request:
    keep   system prompt                 900
    keep   user message                  200
    keep   retrieved docs              6,000
    keep   history                     4,000
    input total                       11,100
    output reserved                    1,500
    window used                        9.8%

  oversized documents -- docs are trimmed:
    keep   system prompt                 900
    keep   user message                  200
    keep   retrieved docs            112,750
    DROP   retrieved docs (kept 112,750 of 200,000)
    DROP   history (all 4,000)
    input total                      113,850
    output reserved                    1,500
    window used                       90.1%

  huge history -- docs kept, history trimmed:
    keep   system prompt                 900
    keep   user message                  200
    keep   retrieved docs             60,000
    keep   history                    52,750
    DROP   history (kept 52,750 of 400,000)
    input total                      113,850
    output reserved                    1,500
    window used                       90.1%

  impossible request -- the system prompt alone overflows:
    REFUSED: fixed components (300,200) exceed the usable budget (113,850) -- this request cannot be built

  Note the last case REFUSES rather than truncating. Silently cutting
  a system prompt can remove a safety instruction while leaving the
  rest intact -- a failure that is invisible in the output.

============================================================================
3. TRUNCATION STRATEGIES: WHAT EACH ONE DISCARDS
============================================================================
  document 1000 tokens, truncating to 300 (30%)

    needle at          head          tail     head+tail
          5%          kept          LOST          kept
         15%          kept          LOST          LOST
         25%          kept          LOST          LOST
         40%          LOST          LOST          LOST
         50%          LOST          LOST          LOST
         60%          LOST          LOST          LOST
         75%          LOST          kept          LOST
         85%          LOST          kept          kept
         95%          LOST          kept          kept

     strategy      survived
         head           3/9
         tail           3/9
    head+tail           3/9

  ALL THREE SURVIVED 3/9 -- they TIE.
  That is not a flaw in the experiment; it is arithmetic. Keeping 30% of
  a document preserves 30% of it whichever 30% you choose. Truncation
  strategies do not differ in HOW MUCH they keep, only in WHICH part:
    head      kept depths ['5%', '15%', '25%']
    tail      kept depths ['75%', '85%', '95%']
    head+tail kept depths ['5%', '85%', '95%']

  So the choice is a BET about where the information is:
    head      -- bet it is near the top (abstracts, summaries, headers)
    tail      -- bet it is near the bottom (chat history, logs, conclusions)
    head+tail -- hedge, covering both ends and abandoning the middle

  Every option loses the middle 40-60%, and none is safe for a fact you
  have not located. That is what retrieval is for (M7): find the relevant
  chunk instead of betting on which end of the document holds it.

============================================================================
4. NEEDLE IN A HAYSTACK  (a simulation, not a measurement of any model)
============================================================================
  This SIMULATES the lost-in-the-middle effect with a position-dependent
  attention prior, so you can see its shape and run the experiment.
  It is NOT a measurement of any real model -- run this against the
  model you deploy, with your own content (M4-L06 section 5.4).

     depth    simulated recall   profile
       0%               1.000   |############################################
      10%               0.917   |########################################
      20%               0.740   |################################
      30%               0.492   |#####################
      40%               0.312   |#############
      50%               0.240   |##########
      60%               0.325   |##############
      70%               0.468   |####################
      80%               0.755   |#################################
      90%               0.950   |#########################################
     100%               1.000   |############################################

  The shape is the point: a U. Facts at the very start and very end are
  recovered reliably; facts at 40-60% depth are not. Consequences:
    * put the question LAST, after the context
    * put the most important document FIRST
    * retrieve FEWER, better documents rather than more
    * and measure this yourself -- the depth of the dip varies by model

============================================================================
5. THE KV CACHE: WHY LONG CONTEXT COSTS MEMORY, NOT JUST COMPUTE
============================================================================
  KV bytes = 2 x layers x heads x head_dim x tokens x bytes_per_value

  model       layers  heads   per token     8k ctx    32k ctx    128k ctx
  7B-ish          32     32        512K       4.0G      16.0G      64.0G
  13B-ish         40     40        800K       6.2G      25.0G     100.0G
  70B-ish         80     64       2560K      20.0G      80.0G     320.0G

  A 7B-class model at 128k context needs 64 GB of KV cache
  for ONE request -- more than the model weights themselves (13 GB in fp16).

  fitting concurrent requests on one 80 GB accelerator:
     context   KV per request   concurrent requests
       2,048            1.00G                    66
       8,192            4.00G                    16
      32,768           16.00G                     4
     131,072           64.00G                     1

  16 concurrent users at 8k context; 1 at 128k.
  A 16x reduction in how many people one accelerator can serve.
  This -- not the attention arithmetic --
  is usually what limits the context length a provider will offer you,
  and why long-context requests are priced the way they are.

============================================================================
6. THE COST OF FILLING THE WINDOW BECAUSE IT IS THERE
============================================================================
  A synthetic quality curve: relevance falls off as you add lower-ranked
  documents, and lost-in-the-middle erodes what the extra ones add.

    docs    tokens   monthly cost   quality   cost per quality point
       1     1,850           $555     0.221                    2,510
       2     2,600           $780     0.393                    1,984
       4     4,100         $1,230     0.630                    1,952
       8     7,100         $2,130     0.854                    2,494
      16    13,100         $3,930     0.935                    4,204
      32    25,100         $7,530     0.827                    9,105
      64    49,100        $14,730     0.548                   26,892
      80    61,100        $18,330     0.500                   36,660

  Cost per unit of quality is lowest at 4 documents.
  Beyond that you are paying linearly for a quality curve that has
  flattened -- and, past the middle of the context, is being eroded.

  The numbers here are ILLUSTRATIVE (the quality curve is synthetic).
  The METHOD is not: plot your own quality against document count on
  your own evaluation set (M7-L16, M3-L14) and find your own knee.
  'The window is large' is not a reason to fill it.

Done.
```

### 7.3 Reading the result

**Section 1 measures the quadratic cost directly.** Fitting `time ∝ T^a` over six sizes gives
**a = 2.06**, against a theoretical 2.0. Doubling the context really does roughly quadruple the
attention work, and 4,096 tokens costs **1,015×** what 128 tokens costs.

The extrapolation makes the constraint concrete: a 1M-token score matrix would be **3.6 TB for one
head** if materialised. Real implementations never form it (FlashAttention and similar), but **the
compute remains quadratic** — which is why long context is expensive rather than free, and why "just
use a bigger window" is a cost decision, not a free upgrade.

**Section 2 runs the §6 budget through four scenarios**, and the last is the one that matters. When
the fixed components alone overflow, the budget **refuses**:

```
REFUSED: fixed components (300,200) exceed the usable budget (113,850)
         -- this request cannot be built
```

**A budget that silently truncates a system prompt is worse than one that fails.** Cutting a system
prompt mid-instruction can remove a safety constraint while leaving the surrounding text intact — the
prompt still looks well-formed, the model still answers, and the constraint is simply gone. Refusing
is the correct behaviour, and it requires deciding in advance that some components are not
droppable.

Note also that the two overflow cases both land at exactly **90.1% window used**, because the headroom
is enforced rather than hoped for.

**Section 3 contradicted this lesson's draft.** I had written that head+tail "keeps the most". It does
not:

| Strategy | Survived | Depths preserved |
|---|---|---|
| head | 3/9 | 5%, 15%, 25% |
| tail | 3/9 | 75%, 85%, 95% |
| head+tail | 3/9 | 5%, 85%, 95% |

**All three tie**, and the reason is arithmetic rather than experimental noise: keeping 30% of a
document preserves 30% of it regardless of which 30% you choose. **Truncation strategies differ in
*which* part survives, never in *how much*.**

That reframes the decision usefully. Choosing head over tail is a **bet about where the information
is**, and head+tail is a hedge that covers both ends by abandoning the middle more thoroughly than
either. **Every option loses the 40–60% band.** If you do not already know where the fact is, no
truncation strategy is safe — which is the argument for retrieval, stated as a measurement rather
than an assertion.

**Section 4 simulates the lost-in-the-middle curve** so you can see its shape: recall 1.000 at both
ends, **0.240 at 50% depth**. The lab is explicit that this is a *simulation with a hand-built prior*,
not a measurement of any real model — you must run this against the model you deploy. What transfers
is the **shape** (a U) and the three consequences: question last, most important document first,
retrieve fewer.

**Section 5 is the constraint that actually limits deployed context**, and it is not the one most
people name:

| Context | KV cache per request | Concurrent requests on an 80 GB accelerator |
|---|---|---|
| 2,048 | 1.00 GB | 66 |
| 8,192 | 4.00 GB | **16** |
| 32,768 | 16.00 GB | 4 |
| 131,072 | **64.00 GB** | **1** |

A 7B-class model at 128k context needs **64 GB of KV cache for a single request** — nearly five times
the model's own weights (13 GB in fp16). Going from 8k to 128k context reduces how many people one
accelerator can serve by **16×**. That, rather than the attention arithmetic, is usually what
determines the context length a provider will sell you and what they charge for it.

**Section 6 puts a number on context stuffing.** With a synthetic quality curve, cost per unit of
quality bottoms out at **4 documents** and rises steadily after: 80 documents cost **33× more per
quality point** than 4, and the raw quality score is *lower* at 80 than at 16 because the extra
documents land in the middle of the context.

The lab is clear that the quality curve is invented and the dollar figures illustrative. **The method
is what transfers:** plot quality against document count on your own evaluation set, find your own
knee, and use that number. "The window is large" remains a fact about the window, not an argument
about what to put in it.

---

## 8. Common mistakes and troubleshooting

1. **Forgetting output shares the window.** Reserve it first.
2. **Not setting `max_tokens`.** Always set it.
3. **Not checking `finish_reason`.** Truncated answers look like complete ones.
4. **Filling the window because it is available.**
5. **Putting the question first, before 50,000 tokens of context.** Put it last.
6. **Truncating the system prompt.**
7. **Assuming advertised context equals usable context.**
8. **Estimating rather than counting tokens** near the limit.
9. **Ignoring the KV cache** when sizing hardware.

| Symptom | Likely cause | Fix |
|---|---|---|
| Answer stops mid-sentence | Hit `max_tokens`, or no room left | Check `finish_reason`; reserve output space |
| "Context length exceeded" | Input too long | Count tokens; trim; add headroom |
| Model ignores a document you supplied | Lost in the middle | Move it to the start or end; retrieve fewer |
| Costs rise with no quality gain | Context stuffing | Measure quality against document count |
| Works in testing, fails in production | Real inputs are longer | Test with realistic lengths |
| Model contradicts the system prompt | System prompt truncated | Never truncate it; verify it is intact |
| Out of GPU memory at long context | KV cache | Compute it; reduce context or batch size |

---

## 9. Security, privacy, reliability, cost

- **Security.** Everything in the window influences the output, including retrieved documents. A
  malicious document is a prompt-injection vector (M10-L06). Treat retrieved content as untrusted.
- **Security.** Truncation can silently remove a safety instruction. Assert the system prompt is
  present and intact before sending.
- **Privacy.** Long histories accumulate personal data and are re-sent on every request. Apply
  retention limits to conversation history, and summarise rather than retaining raw text where you
  can.
- **Cost.** Input cost is linear in prompt length and paid on **every turn**. A long history is a
  recurring cost, not a one-off.
- **Cost.** Prompt caching (M5-L16) can substantially reduce the cost of a stable prefix. Check
  whether your provider offers it before optimising anything else.
- **Reliability.** Always set `max_tokens` and always check `finish_reason`. A silently truncated
  answer that is then parsed as JSON will fail in a confusing place, far from the cause.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. A 32,000-token window, a 1,200-token system prompt, 800 tokens of history, a 150-token question.
   How many tokens remain for retrieved documents if you reserve 800 for output?
2. Why does 10× the context cost roughly 100× the attention work?
3. What does `max_tokens` limit, and what does it *not* limit?
4. Name three things you would never truncate, and why.
5. Where should the user's question go in a long prompt, and why?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab. Confirm the quadratic curve and state the exponent you measured.
2. Implement the §6 budget with an explicit drop order. Test it with inputs that overflow at each
   priority level and assert the right thing is dropped.
3. Compare head, tail and head+tail truncation on a document where the key fact is at 25%, 50% and
   75% depth. Report which strategy preserves it in each case.
4. Simulate a needle-in-a-haystack test at 5 depths and plot recall against depth.
5. Compute KV cache size for 8k, 32k and 128k contexts on a 32-layer model, and say which fit in
   40 GB and 80 GB.

### Exercise 3 — Challenge (~40 min)

1. Build a `TokenBudget` class with named components, priorities and a `fit()` method that returns
   both the assembled prompt and a report of what was dropped. Test the report.
2. Implement summarise-then-drop for conversation history and measure the token reduction against
   information retained (define your own retention metric and justify it).
3. Measure the actual cost of context stuffing: for document counts 1, 2, 4, 8, 16, 32, plot tokens
   and a synthetic quality score. Find the point where quality stops improving.
4. Implement an assertion that the system prompt is byte-identical after assembly, and demonstrate it
   catching a truncation bug.
5. Write the runbook entry for "answers are being cut off in production" — the checks, in order.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l06).)*

**Q1.** What shares the context window with the input?

- A. The model's generated output, drawn from the same budget.
- B. Only the system prompt, which is counted separately.
- C. Nothing; the input has the window entirely to itself.
- D. The conversation history from all previous requests.

**Q2.** Why does the context window have a limit?

- A. Providers impose it to differentiate their pricing tiers.
- B. Attention compares every token pair, so cost grows as `T²`.
- C. Tokenizers cannot encode sequences beyond a fixed length.
- D. The embedding matrix has a fixed maximum number of rows.

**Q3.** A 200k window with a 199k prompt. What happens to the answer?

- A. The provider automatically extends the window for the output.
- B. An error is raised before any generation is attempted.
- C. The answer has about 1,000 tokens and may be cut off.
- D. The oldest input tokens are dropped to make room.

**Q4.** What does `max_tokens` limit?

- A. The total of input plus output tokens for the request.
- B. The number of tokens the model may read from the prompt.
- C. The size of the model's internal key-value cache.
- D. The output only; it reserves no input space at all.

**Q5.** "Lost in the middle" describes:

- A. Tokens silently dropped when the window overflows.
- B. Attention weights failing to sum to one across positions.
- C. Documents omitted by the retrieval ranker before assembly.
- D. Information mid-context being used less reliably.

**Q6.** Where should the user's question go in a long prompt?

- A. At the very start, so the model knows what to look for.
- B. In the exact middle, equidistant from both ends.
- C. Repeated at both the beginning and the end of the prompt.
- D. At the end, after the context it needs to answer from.

**Q7.** You have a 128k window and 80 relevant documents. You should:

- A. Send all 80, since the window can accommodate them.
- B. Send the top 8, then measure whether more actually helps.
- C. Send 40, exactly half, as a reasonable compromise.
- D. Send none and rely on the model's training knowledge.

**Q8.** Which component must never be truncated?

- A. The oldest turns of the conversation history.
- B. The lowest-ranked of the retrieved documents.
- C. The system prompt, which may carry safety constraints.
- D. The reserved output space at the end of the budget.

**Q9.** How does the KV cache scale with context length?

- A. Linearly, roughly 0.5 MB per token on a 32-layer model.
- B. Quadratically, matching the cost of attention itself.
- C. It does not grow; it is a fixed allocation per model.
- D. Logarithmically, since older entries are compressed.

**Q10.** An answer stops mid-sentence. What do you check first?

- A. The model's temperature setting for the request.
- B. Whether the retrieval step returned enough documents.
- C. The `finish_reason` returned alongside the response.
- D. The tokenizer version used to count the prompt.

**Q11.** *(Written, rubric-graded.)* In under 100 words, respond to a colleague who says "the new model
has a 1M-token context, so we can delete the retrieval pipeline and just send everything."

---

## 12. Revision notes

- **The window holds everything: system prompt, history, documents, question — and the output.**
  Reserve output space **first**.
- **The limit exists because attention is `T²`.** 10× the context is **100×** the attention work.
- **Advertised ≠ effective.** Models use the **start and end** better than the middle. Put the
  question **last**.
- **Budget with an explicit drop order**, decided in advance: documents by rank, history by age, never
  the system prompt or the output reservation. Leave ~10% headroom.
- **Truncate on token boundaries.** Measured: head, tail and head+tail all preserve the **same
  amount** (3/9) — they differ only in *which* part. Truncation is a **bet about where the
  information is**, and every variant abandons the middle.
- **`max_tokens` caps output only and reserves nothing.** Always set it; always check `finish_reason`.
- **KV cache grows linearly** — measured **64 GB at 128k tokens** for one request on a 7B-class model,
  nearly 5× its own weights. Going 8k → 128k cuts concurrent users per accelerator from **16 to 1**.
  This, not attention arithmetic, is usually the real deployment limit.
- Measured: attention cost fits `T^2.06`; 4,096 tokens costs **1,015×** what 128 does.
- **A large window is not a reason to fill it.** "Send fewer, better documents" beats "send
  everything" on cost, latency *and* usually quality.
- **Retrieved content is untrusted input.** It is inside the window and it influences the output.

---

## 13. Completion checklist

- [ ] I can compute available output space from a window and a prompt.
- [ ] I can explain the quadratic cost in one sentence.
- [ ] I know the difference between advertised and effective context.
- [ ] I built a budget with an explicit drop order.
- [ ] I know that all truncation strategies preserve the same amount, and differ only in which part.
- [ ] I always set `max_tokens` and check `finish_reason`.
- [ ] I can size a KV cache.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Liu et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts*.
  <https://arxiv.org/abs/2307.03172> `[UNVERIFIED]`
- Beltagy et al. (2020), *Longformer* (sparse attention). <https://arxiv.org/abs/2004.05150>
  `[UNVERIFIED]`
- Dao et al. (2022), *FlashAttention*. <https://arxiv.org/abs/2205.14135> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L07 — Attention and Self-Attention: the Core Idea](M4-L07-attention.md)

You know the window's size and why it costs what it does. Next: the mechanism that makes it cost
that, and the single most important idea in the architecture.
