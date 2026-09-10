# M5-L15 — Token Accounting and Cost Calculation

| | |
|---|---|
| **Lesson ID** | M5-L15 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M4-L03](../module-04-genai-llm-internals/M4-L03-tokens-tokenizers.md) |

---

## 1. Learning objectives

1. **Compute** the exact cost of a request from separate input and output prices, and state why a
   blended rate misrepresents it.
2. **Explain** why output tokens are priced higher than input tokens, and find the break-even ratio
   between them.
3. **Structure** a request to benefit from prompt caching, and recognise what silently breaks it.
4. **Forecast** monthly cost from a traffic sample that represents your actual distribution, not a
   short-conversation demo sample.
5. **Identify** the token-accounting mistakes that are easy to make once and expensive to leave
   uncorrected.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Input price** | The $/token rate charged for tokens sent to the model. |
| **Output price** | The $/token rate charged for tokens the model generates — typically several times the input price. |
| **Break-even ratio** | The input:output token ratio at which the two halves of a request cost the same. |
| **Prompt caching** | A discount on input tokens that repeat, byte-for-byte, from a prior request's stable prefix. |
| **Cache hit / miss** | Whether a request's stable prefix matched a previously cached one. |
| **Blended rate** | A single $/token figure averaging input and output prices under an assumed mix. |
| **Long-tail cost** | The disproportionate share of total spend driven by a small fraction of unusually large requests. |
| **Demo-sample bias** | Underestimating cost by forecasting from short, manually-tested conversations that never include real long-tail traffic. |
| **Per-request cost report** | A cost breakdown attributing $ to input, cached input, and output separately for one request. |

---

## 3. Plain-language explanation

### 3.1 Tokenization tells you what you're billed for; this lesson tells you what it costs

M4-L03 taught you to count tokens. Two tokens are not interchangeable in price: **an output token
routinely costs several times an input token** (§7.1), and a repeated input token can cost a small
fraction of a fresh one, if your request is structured to let it (§7.2). Accounting means tracking these
as separate quantities, not folding them into one number that only happens to be right some of the time.

### 3.2 Why output is priced higher

Input tokens are processed largely in parallel during prefill; output tokens are generated one at a time,
sequentially, each depending on the last (M4-L05, M4-L17). **Generation is the more expensive operation
per token, and pricing reflects that.** The practical consequence: a request that looks input-heavy on
the page can still be output-dominated in cost, once the ratio crosses a specific, computable point.

### 3.3 Caching turns request structure into a cost decision

A stable prefix — system prompt, tool definitions, anything unchanged across many requests — can be
cached by many providers at a steep discount on repeat use. **This is not automatic regardless of how you
build the request**: the cached region has to be byte-identical to a prior one, which means anything
variable placed *before* it silently defeats the whole mechanism, with no error to tell you it happened.

### 3.4 A single "per 1K tokens" number is a convenience, not an account

A blended rate is exact for exactly one input:output ratio — the one it was computed from — and wrong,
in opposite directions, for everything else. §7.3 measures how wrong.

### 3.5 Your forecast is only as representative as your sample

A cost estimate built from short, hand-tested conversations will miss the long tail that dominates real
production spend, the same shape M5-L11 found for conversation-length triggers, now costed directly in
dollars (§7.4).

---

## 4. Analogy

**A courier service billed by weight for pickup and by distance for delivery**, at very different rates
per unit. A shipment described only by its "average charge per parcel" tells you nothing useful once
parcels vary — a heavy, short-haul parcel and a light, long-haul one can cost the same total for entirely
different reasons, and a single blended number hides which one you are actually paying for.

The courier also offers a discount for a **standing pickup route** — the same address, the same load,
repeated daily — but only if nothing about the pickup varies; add one irregular stop before the standard
route and the whole day reverts to full price, with the invoice giving no hint why.

### Where the analogy breaks

- **A courier's weight and distance are independent facts you can look up before shipping.** A model's
  exact output length is not knowable in advance — you can bound it (`max_tokens`, M4-L15) but not
  predict it precisely.
- **A missed pickup discount shows up as a distinctly higher line item.** A missed cache hit often looks
  identical to a normal request on your invoice — nothing marks it as a miss unless you specifically log
  cache status per request.
- **A courier's long-tail parcels are rare and visible.** An LLM system's long-tail *requests* can be a
  small, quiet fraction of traffic that never shows up in a demo, exactly because nobody manually tests a
  90,000-token conversation.

---

## 5. Detailed technical explanation

### 5.1 The asymmetry, and its break-even point

`[REAL, ILLUSTRATIVE prices]` §7.1 priced input at $0.50/M and output at $2.00/M — **output costs 4×
input, per token**:

| Shape (in:out) | Output's share of total cost |
|---|---|
| 20:1 | 17% |
| 4:1 | 50% |
| 1:1 | 80% |
| 1:20 | 99% |

**The break-even ratio is exactly `output_price / input_price` — 4:1 here.** Below that ratio (relatively
more output), output dominates the bill, even when it is visibly the smaller block of text. A prompt of
2,000 tokens producing a 400-token answer is **already 44% output cost** — a fact invisible if you only
look at which block is longer on the page.

**A tool-definition consequence worth stating plainly**: tool schemas (M5-L08) are sent as **input**
tokens on every request that includes them, whether or not the model calls a tool that turn. They are
never output-priced, and they are exactly the kind of stable, repeated content §5.3 says belongs in a
cached prefix.

### 5.2 Structuring a request for caching

`[REAL arithmetic, UNVERIFIED mechanics — check your provider]` §7.2 modelled a 20-request session with
a 3,000-token stable system+tools prefix and a 90% cache-hit discount:

| | Total for 20 requests |
|---|---|
| Without caching | $0.0490 |
| With caching | $0.0233 |
| **Saved** | **52%** |

**The first request in a session always pays full price** — it has to write the prefix to the cache
before anything can hit it. Every later request in the session benefits, provided the prefix stays
byte-identical.

**What silently breaks this**: placing anything that changes between requests — a timestamp, a
per-request id, a reordered field — *before* the stable block. The prefix then never matches, every
request misses, and cost reverts to the "without caching" total **with nothing in a normal response
telling you it happened.** Put variable content strictly after the stable block, never before it, and log
cache-hit status per request if your provider exposes it.

### 5.3 Why a blended rate is exact exactly once

`[REAL]` §7.3 built a blended rate from one assumed shape (1,600 input : 400 output tokens) and applied
it to three tasks:

| Task | Exact cost | Blended estimate | Error |
|---|---|---|---|
| Summarization (input-heavy) | $0.00440 | $0.00656 | **+49%** |
| The shape the blend assumed | $0.00160 | $0.00160 | 0% |
| Open-ended generation (output-heavy) | $0.00410 | $0.00176 | **−57%** |

**Zero error at the assumed shape is not a coincidence — it is the definition of a blended rate.** Move
away from that shape in either direction and the error moves in **opposite directions**: input-heavy work
is overcharged by the estimate (it should have paid the cheaper real input rate), output-heavy work is
undercharged (it should have paid the pricier real output rate). **A blended number is fine for a slide.
It is not an accounting system.**

### 5.4 The long tail dominates the forecast

`[REAL arithmetic on ILLUSTRATIVE percentiles]` §7.4 compared a demo-sample forecast against a bucketed
estimate of real traffic, at 100,000 requests/month:

| Source | Monthly estimate |
|---|---|
| Demo sample (1,200-token average, all short conversations) | $96.00 |
| Bucketed by actual percentile distribution | **$460.00** |
| **Underestimate factor** | **4.8×** |

**Only the top 10% of requests (p90 and above) drove the majority of the gap.** A demo sample built from
manual testing is almost never going to include a 90,000-token conversation — nobody tests that by hand —
so the forecast misses exactly the traffic that costs the most, before a single real user has been added
to the volume.

### 5.5 A per-request cost report

Track, per request, at minimum:

| Field | Why |
|---|---|
| Input tokens (cached) | Priced at the discount rate — cheap, but only if the prefix actually hit |
| Input tokens (uncached) | Full input price |
| Output tokens | Full output price, usually the largest single line for short exchanges |
| Cache hit? | A silent miss (§5.2) is invisible without this flag |
| Model / artefact version | Costs and prices differ by model (M5-L12) |

**Sum these across real traffic, not a sample chosen for convenience**, and the two numbers in §5.4's
table stop being a surprise.

### 5.6 Assumptions and limitations

- All prices, the cache discount and its eligibility rules are illustrative and dated 2026-09-09.
  `[UNVERIFIED — check your provider's current pricing and caching documentation before budgeting.]`
- §7.4's traffic percentiles are illustrative. Build the bucketed estimate from your own logged
  distribution, not these figures.
- This lesson does not cover multi-model routing cost trade-offs (M5-L16) or the token cost incurred by a
  request that fails or is refused before completing (M5-L14) — both add to a full accounting.
- Provider-specific minimums (a prefix must exceed some length to be cacheable at all) and rounding rules
  are not modelled here.

---

## 6. Worked example — the budget that was right for the demo and wrong by 5×

**The system.** A team builds a document-assistant prototype. Manual QA runs about 30 short
conversations, averaging 1,200 tokens each. Using a blended $0.80/M rate (§7.3's own example number),
they forecast: 100,000 requests/month × 1,200 tokens × $0.80/M = **$96/month**. Finance approves the
budget on that basis.

**What production actually looked like**, once real usage arrived: most requests were indeed short — but
a consistent 10% of sessions involved longer documents, multi-turn investigation, or power users who kept
conversations going far past what anyone tested by hand. Bucketed by the real distribution (§7.4), actual
monthly cost landed at **$460** — **4.8× the approved budget**, discovered on the first invoice, not
before.

**Why the demo sample missed it.** Nobody manually tests a 90,000-token conversation — it takes too long
to construct by hand, and QA time is naturally spent on short, repeatable cases. The sample wasn't wrong
about what it measured; it was **never capable of containing the traffic that mattered most for cost.**

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Forecast built from a sample with no long-tail requests | The most expensive 10% of real traffic was invisible to the estimate |
| 2 | A blended rate used without checking it against the sample's own true shape | Compounded the first error with a second, independent one |
| 3 | No per-request cost logging in the prototype | Nobody could reconcile the forecast against reality until the invoice arrived |

### The fix

**Forecast from logged production-shaped data**, not manual QA — even a rough bucketed estimate by
percentile (§5.4) catches an order-of-magnitude miss that a single average cannot.

**Track input, cached input, and output separately per request** (§5.5), so a forecast can be checked
against reality continuously, not discovered on an invoice.

**Treat a demo-only forecast as a lower bound, explicitly**, until real traffic data exists to replace it
— stating "this is a floor, not an estimate" is cheap; discovering the gap after committing a budget is
not.

**The general rule.** **A cost forecast is only as representative as the traffic it was built from — and
the traffic that costs the most is exactly the traffic nobody thinks to test by hand.**

---

## 7. Practical activity

**File:** [`labs/m5/l15_token_accounting.py`](../../labs/m5/l15_token_accounting.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l15_token_accounting.py
```

Pure Python, no dependencies. Every number is exact arithmetic on the stated prices and parameters — no
model behaviour is simulated anywhere in this lab.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11.

```text
============================================================================
1. INPUT VS OUTPUT PRICING: THE ASYMMETRY
============================================================================
  Stated prices [ILLUSTRATIVE, 2026-09-09]: input $0.50/M, output $2.00/M -- output costs 4x input, per token.

  shape                     in tok  out tok      in $     out $  out share of $
  mostly input (20:1)         2000      100  $0.00100  $0.00020             17%
  balanced-ish (4:1)          1600      400  $0.00080  $0.00080             50%
  even split (1:1)            1000     1000  $0.00050  $0.00200             80%
  mostly output (1:4)          400     1600  $0.00020  $0.00320             94%
  mostly output (1:20)         100     2000  $0.00005  $0.00400             99%

  Break-even (in tokens : out tokens) where the two halves cost the
  same: 4:1. Below that ratio -- i.e. relatively more
  output -- OUTPUT dominates the bill even though it is usually the
  smaller number of tokens on the page. A 2,000-token prompt that
  produces a 400-token answer is already 44% output cost.

============================================================================
2. PROMPT CACHING: A REQUEST-STRUCTURE DECISION
============================================================================
  A stable 3,000-token prefix (system + tools), 300 new input tokens/request, 400 output tokens.
  Cache discount on a hit: 90% off the cached portion's input price. [UNVERIFIED -- illustrative; check your provider's current mechanics and minimum-prefix rules.]

  A 20-request session:
    without caching: $0.0490
    with caching:    $0.0233
    saved:           $0.0257 (52%)

  What breaks the cache: anything VARIABLE placed BEFORE the stable
  prefix. A request built as [today's date][system prompt][tools]
  never matches byte-for-byte request to request, so every single
  request misses -- silently reverting to the 'without caching' total
  above ($0.0490 instead of $0.0233) with
  no error raised anywhere. Put anything that changes AFTER the
  stable block, never before it.

============================================================================
3. ONE BLENDED RATE VS TWO REAL RATES
============================================================================
  A blended $/token rate, built from one assumed shape (1600 in : 400 out): $0.800/M tokens.

  task                                    exact cost  blended est.    error
  summarization (input-heavy)               $0.00440      $0.00656     +49%
  the shape the blend assumed               $0.00160      $0.00160      +0%
  open-ended generation (output-heavy)      $0.00410      $0.00176     -57%

  The blended rate is exact only for the shape it was built from --
  by construction, the middle row's error is 0%. Move away from that
  shape in either direction and the estimate is wrong, and wrong in
  OPPOSITE directions: it overcharges input-heavy tasks (which pay a
  cheaper real rate than the blend assumes) and undercharges
  output-heavy ones. A single $/token number is a convenience for a
  slide, not a substitute for tracking the two real rates.

============================================================================
4. FORECASTING FROM A SHORT DEMO SAMPLE UNDERESTIMATES BADLY
============================================================================
  A team estimates monthly cost from a 1200-token
  average, drawn from short QA/demo conversations, at 100,000 requests/month:
    estimate: 100,000 x 1200 tok x $0.800/M = $96.00

  Real production traffic, by percentile (illustrative; measure your
  own), each bucket costed at its own midpoint token count:

  bucket        share  requests  tok/request   bucket cost
  up to p50       50%    50,000        1,200        $48.00
  p50-p90         40%    40,000        5,000       $160.00
  p90-p99          9%     9,000       25,000       $180.00
  above p99        1%     1,000       90,000        $72.00

  actual (bucketed) total: $460.00
  demo-sample estimate:    $96.00
  underestimate factor:    4.8x

  Only 10% of requests (p90 and above) drive the majority of the
  gap. A demo sample that happens to be all short conversations --
  the natural shape of manual QA testing -- never sees that 10%, and
  the resulting forecast is wrong by a large, one-directional factor
  before a single real user has been added.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every number here is exact arithmetic given the stated inputs.
  No model behaviour is simulated anywhere in this lab.

  ILLUSTRATIVE / DATED: the prices, the cache discount and its
  eligibility rules, and section 4's traffic percentiles are all
  stated assumptions, current as of 2026-09-09 at best. Prices and
  caching mechanics change; verify your own provider's current
  documentation before budgeting from any number in this file.

  NOT SHOWN: multi-model routing costs (M5-L16), the token cost of a
  failed or refused request (M5-L14), and provider-specific minimums
  or rounding rules for what counts as a cacheable prefix.

Done.
```

### 7.3 Reading the result

**Section 1's break-even point is a number worth memorising for your own provider's prices**: at exactly
`output_price / input_price` input:output tokens, the two halves cost the same. Every request cheaper
than that ratio in relative output is output-dominated, however input-heavy it looks.

**Section 2's 52% saving comes with a sharp edge.** The mechanism only works if the cached region is
byte-identical across requests — put one variable field ahead of it, and the saving disappears entirely,
silently. This is a request-*structure* decision, made once in code, not a setting you toggle.

**Section 3 makes a single blended rate's failure precise.** It is exact at one shape and wrong, in
opposite directions, everywhere else — a +49% error on one real task and a −57% error on another, from
the same one-number shortcut.

**Section 4 is the sharpest result in the lab.** A forecast that looked entirely reasonable — a real
1,200-token average, honestly measured from real testing — undershot actual cost by **4.8×**, because the
sample it came from structurally could not contain the 10% of traffic that dominates real spend.

---

## 8. Common mistakes and troubleshooting

1. **Using one blended $/token rate for planning.** Exact only at the shape it was built from (§5.3).
2. **Forecasting from manually-tested, short conversations.** Structurally excludes the long tail that
   dominates real cost (§5.4, §6).
3. **Putting variable content before a cacheable prefix.** Silently defeats caching entirely, with no
   error (§5.2).
4. **Not logging cache-hit status per request.** A miss looks identical to a normal request without it.
5. **Forgetting tool definitions are input tokens on every request**, used or not (§5.1, M5-L08).
6. **Assuming input dominates cost because the prompt looks longer on the page.** Check the ratio against
   your break-even point (§5.1).
7. **Budgeting once from a demo forecast and never reconciling against real invoices.**
8. **Treating a demo estimate as a target rather than a floor.**
9. **Not separating cost by model/artefact version** when comparing spend across a prompt change
   (M5-L12).
10. **Assuming caching mechanics and discounts are identical across providers or stable over time.**
    `[UNVERIFIED — check current documentation.]`

| Symptom | Likely cause | Fix |
|---|---|---|
| Invoice far exceeds forecast | Forecast built from a short demo sample | Rebuild from logged production percentiles (§5.4) |
| Caching "isn't saving anything" | Variable content placed before the stable prefix | Move all variable content after the cacheable block; log hit/miss |
| Cost estimates consistently off for one task type | Using a blended rate far from that task's true ratio | Track input/output cost separately (§5.3, §5.5) |
| Cost spikes with no clear cause after a config change | Model or parameter change altered price tier | Check the artefact fingerprint (M5-L12) against the cost report |
| Can't explain this month's bill | No per-request cost logging | Add the fields in §5.5 before the next billing cycle |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Track input, cached input, and output as three separate numbers per request. A blended
  figure is exact for one shape and wrong for every other (§5.3).
- **Cost.** Structure requests so the stable, cacheable prefix comes first and variable content comes
  after — reversed, caching silently stops working (§5.2).
- **Cost.** Forecast from your logged traffic distribution, not from manual QA. §7.4 measured a 4.8×
  underestimate from a plausible, honestly-measured demo sample.
- **Reliability.** A cost report that flags cache hit/miss per request turns a silent, invisible failure
  into a visible metric you can alert on.
- **Privacy.** Per-request cost logs often carry token counts derived from user content. Apply the same
  retention and access discipline to cost logs as to the content they were derived from (M2-L18, M10-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Given input $0.30/M and output $1.50/M, compute the break-even input:output ratio.
2. Why does the first request in a cached session always pay full price?
3. Name one thing that silently defeats prompt caching.
4. Why is a blended $/token rate exact for only one specific request shape?
5. Why does a forecast built from manual QA conversations tend to underestimate real cost?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the break-even ratio and the caching saving percentage from your own run (they
   will match the lesson's, since the lab is deterministic — confirm they do).
2. Recompute section 2 with a cache discount of 50% instead of 90%. How much does the session saving
   change?
3. Build your own three-task table like section 3's, using prices and task shapes from a provider of your
   choice, and report the errors.
4. Using section 4's bucket method, build a forecast from a traffic shape you define yourself (state your
   percentiles and bucket token counts) and compute the underestimate factor against a plausible demo
   sample.
5. Design the fields of a per-request cost log (§5.5) as a small schema (Pydantic, per M2-L08) and write
   one test that computes total cost from a list of logged requests.

### Exercise 3 — Challenge (~50 min)

1. Build a `CostReport` that ingests a list of per-request records (input tokens, cached tokens, output
   tokens, model) and produces a monthly summary broken down by model and by cache-hit rate.
2. Implement a check that flags a session where cache-hit rate is unexpectedly low (e.g. below 50% after
   the first request), and write a test that catches a "variable content before the prefix" bug.
3. Extend section 4's bucketed forecast into a small percentile-fitting exercise: given a larger set of
   sample token counts, estimate p50/p90/p99 yourself and compare your bucketed forecast to a naive mean-
   based one.
4. Research your own provider's current input/output prices and caching discount and rules
   `[you must verify this yourself]`, then rebuild section 1-3's tables with real numbers.
5. Write the finance-facing memo for §6's incident: what the original forecast assumed, what was wrong
   with the assumption, and the process change that prevents a recurrence.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l15).)*

**Q1.** Output tokens are priced 4× input tokens in §7.1. The consequence is:

- A. Output cost is always negligible compared to input cost.
- B. A request with more input tokens than output tokens can still have output dominate the total cost, once the ratio crosses the break-even point.
- C. The two prices must always be set equal by regulation.
- D. Input tokens should never be counted separately from output tokens.

**Q2.** What silently breaks a cached prefix, per §7.2?

- A. Using more than one tool definition in the same request.
- B. Sending fewer than 100 requests in a session.
- C. Setting `temperature` above zero.
- D. Placing anything that varies between requests, like a timestamp, before the stable system+tools block.

**Q3.** A blended $/token rate computed from an assumed input:output shape (§7.3) will be exact for:

- A. Only requests whose actual input:output ratio matches the shape it was built from.
- B. Every request, regardless of shape.
- C. Only requests that use caching.
- D. Only the first request in a session.

**Q4.** In §7.3, the blended rate overestimated cost for the input-heavy task and underestimated it for
the output-heavy one. This happened because:

- A. The tokenizer counted input and output tokens differently.
- B. Input-heavy tasks are always billed at a discount.
- C. The blended rate averages the cheap input price and expensive output price into one number, which is too high for input-heavy work and too low for output-heavy work.
- D. The lab introduced random noise into the calculation.

**Q5.** §7.4 found a demo-sample-based forecast underestimated actual monthly cost by 4.8×. The main
driver was:

- A. The demo sample used the wrong currency.
- B. Output prices increased after the forecast was made.
- C. The blended rate was computed incorrectly.
- D. A small share of long, expensive requests (the long tail) that a short-conversation demo sample never included.

**Q6.** Why does caching a stable system+tools prefix save money across a session, per §7.2?

- A. It reduces the number of output tokens generated.
- B. Later requests pay a steep discount on the cached portion's input tokens instead of full price.
- C. It removes the need to send a system prompt at all after the first request.
- D. It converts input tokens into output tokens, which are cheaper to cache.

**Q7.** The break-even ratio in §7.1 (4:1 input:output) means:

- A. Output should always be limited to a quarter of input length.
- B. Caching only activates above this ratio.
- C. At exactly that ratio, input and output cost the same; below it (relatively more output), output costs more.
- D. Input tokens become free once this ratio is exceeded.

**Q8.** Why is a "per 1K tokens" blended price a risky number to plan a budget around?

- A. It silently assumes a specific input:output mix, and diverges in opposite directions for tasks that don't match it.
- B. It is always higher than the true cost.
- C. It cannot be computed without a live model call.
- D. It only applies to output tokens.

**Q9.** What causes a cache miss to be invisible in normal operation, per §7.2?

- A. Providers refund missed cache hits automatically, so there is nothing to notice.
- B. Cache misses only occur once per year.
- C. No error is raised; the request simply reverts to full price, with nothing flagging that the cache was never hit.
- D. Cache misses are logged as a distinct HTTP status code by every provider.

**Q10.** The general lesson of §7.4 is:

- A. Manual QA testing should be eliminated entirely.
- B. Estimate costs from a traffic sample that includes your actual long tail, not from short QA/demo conversations alone.
- C. Monthly cost cannot be forecast in advance under any circumstances.
- D. Long conversations should always be rejected to control cost.

**Q11.** In §7.2, the first request of a cached session pays full price for the system+tools prefix
because:

- A. The first request must write the prefix to the cache before any request can benefit from a hit.
- B. The discount only applies to the tenth request onward.
- C. First requests are always billed at a premium rate.
- D. Caching is disabled for the first five minutes of any session.

**Q12.** The central practical rule this lesson establishes is:

- A. Always use a single blended rate for simplicity, even in production billing systems.
- B. Only output tokens need to be tracked; input is negligible.
- C. Caching should be disabled to keep cost calculations simple.
- D. Track input cost, output cost, and cache-hit cost as three separate quantities — a single blended number or a short-sample estimate both hide where the real spend comes from.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes budgeting next quarter's
LLM spend using "$0.80 per 1,000 tokens, times our expected request volume," based on a quick manual test
of 20 conversations. State what this estimate is likely to miss and what you would ask for instead.

---

## 12. Revision notes

- **Output tokens are priced several times higher than input tokens** — measured here at 4×. The
  break-even ratio (`output_price / input_price`) tells you when output, not input, dominates a request's
  cost.
- **Tool definitions are input tokens on every request**, used or not — and a strong candidate for a
  cached, stable prefix (M5-L08).
- **Prompt caching only works on a byte-identical stable prefix.** Measured: 52% session savings with
  correct structure; silently reverts to full cost if anything variable is placed before the cacheable
  block, with no error raised.
- **A blended $/token rate is exact at exactly one shape and wrong, in opposite directions, everywhere
  else.** Measured: +49% error on an input-heavy task, −57% on an output-heavy one, from the same rate.
- **A cost forecast is only as good as the traffic it was sampled from.** Measured: a demo-sample
  forecast underestimated real cost by 4.8×, because manual testing structurally never reaches the
  long-tail 10% of requests that dominate spend.
- **Log input, cached input, and output tokens separately per request.** Without that, you cannot
  reconcile a forecast against reality until the invoice arrives.
- **Treat any demo-based forecast as a floor, not an estimate**, until real traffic data replaces it.

---

## 13. Completion checklist

- [ ] I can compute the break-even input:output ratio for my own provider's prices.
- [ ] My requests place all variable content after the stable, cacheable prefix, never before it.
- [ ] I log cache-hit status per request, not just total cost.
- [ ] I track input, cached input, and output cost as separate figures, not one blended rate.
- [ ] My cost forecasts are built from logged production traffic, not manual QA samples alone.
- [ ] I treat any demo-based forecast as a floor and reconcile it against real invoices.
- [ ] I account for tool-definition tokens as input cost on every request that includes them.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic — pricing documentation. <https://www.anthropic.com/pricing> `[UNVERIFIED — verify current figures]`
- Anthropic — prompt caching documentation.
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching> `[UNVERIFIED]`
- OpenAI — pricing documentation. <https://openai.com/api/pricing/> `[UNVERIFIED — verify current figures]`

---

## 15. Next lesson

→ [M5-L16 — Caching and Model Routing](M5-L16-caching-routing.md)

You can now account for what a request costs. Next: deciding, per request, which model should even
handle it — and extending the caching mechanic from this lesson into a full routing strategy.
