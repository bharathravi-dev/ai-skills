# M5-L07 — Output Validation and Repair Loops

| | |
|---|---|
| **Lesson ID** | M5-L07 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M5-L06](M5-L06-structured-output.md), [M2-L14](../module-02-python-foundations/M2-L14-retries.md) |

---

## 1. Learning objectives

1. **Classify** a validation failure as transient or systematic before deciding to retry.
2. **Build** a feedback message that repairs efficiently without leaking data into your logs.
3. **Bound** a repair loop by attempts, deadline **and** cost, and justify each bound with arithmetic.
4. **Choose** the right response to an unrepairable output — degrade, escalate, or fail.
5. **Predict** what a repair loop costs before it reaches production.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Repair loop** | Re-requesting after a validation failure, usually with feedback. |
| **Transient failure** | The model could have produced a valid answer; this sample did not. |
| **Systematic failure** | The prompt and schema disagree; no sample will be valid. |
| **Feedback message** | The text describing what was wrong, sent back to the model. |
| **Retry budget** | The bound on attempts, time and money for one logical request. |
| **Degradation** | Returning a reduced but honest result instead of failing. |
| **Escalation** | Handing the request to a person. |
| **`include_input`** | Pydantic switch controlling whether errors carry offending values. |
| **Attempt tail** | The p99 request that used every retry. |

---

## 3. Plain-language explanation

### 3.1 A rejected output is a question, not a task

Validation failed. Before writing the retry, answer one question:

> **Could this model, with this prompt and this schema, have produced a valid answer?**

If yes, the failure is **transient** and retrying is reasonable. If no, the failure is **systematic**
and retrying is a way of spending money to receive the same rejection repeatedly.

§7.3 measures exactly that. Against a systematic failure, every strategy solved **0%** — and the
four-attempt loop spent **four calls per request** to achieve it.

**Almost nobody makes this distinction in code.** The retry is written as though all failures are the
first kind, because the first kind is what you see in testing.

### 3.2 The three things a repair loop must be bounded by

| Bound | Stops |
|---|---|
| **Attempts** | The infinite loop |
| **Deadline** | A slow provider becoming a slow you |
| **Cost** | A retry storm becoming an invoice |

**Attempts alone is not enough.** Four attempts at 30 seconds each is a two-minute request, and the
user left after ten seconds. This is M2-L14's rule arriving in a new costume: bound by attempts,
deadline *and* budget.

### 3.3 What the loop is for

A repair loop buys you the difference between a **transient** failure rate and a much smaller one. At a
per-attempt success rate of 90%, three attempts reach 99.9%.

It cannot buy you a schema that matches your prompt, a model capable of the task, or an output that
exists. **When the answer is "this cannot be done as asked", the loop's job is to stop quickly and say
so.**

---

## 4. Analogy

A form rejected at a counter.

If the clerk says *"date of birth: use DD/MM/YYYY"*, you fix that field and resubmit. One specific
field, one specific rule. That is a good feedback message.

If the clerk says *"this is wrong"* and hands it back, you resubmit something equally likely to be
wrong. That is `"Invalid. Try again."` — it tells you exactly what you already knew.

And if the form has no box for your situation, resubmitting will never work no matter how the clerk
phrases the rejection. **You need a different form, or a person.**

### Where the analogy breaks

- **You learn from a rejection permanently.** A stateless model does not: the same prompt produces the
  same failure rate on the next request, next week, forever, unless *you* change something.
- **The clerk is not billed per attempt.** Every repair is a full request — the whole prompt again, at
  input prices, plus output.
- **You eventually give up.** A loop does not, unless you write the bound.

---

## 5. Detailed technical explanation

### 5.1 What a `ValidationError` actually contains

`[REAL — pydantic 2.13.5]` §7.3 runs six malformed outputs through a strict model:

| Bad output | Errors | Field named | **Value included** |
|---|---|---|---|
| Wrong enum | 1 | `category` | **YES** |
| Out of bounds | 1 | `refund` | **YES** |
| String number | 1 | `refund` | **YES** |
| Missing field | 1 | `urgent` | **YES** |
| Extra field | 1 | `approved` | **YES** |
| Several at once | 5 | all five | **YES** |

**6 of 6 carry the offending input value.** That is excellent for repair and a liability the moment it
reaches a log, because the invalid value is frequently a customer's email address, name or free text.

**And the missing-field case is worse than the others.** Its error type is `missing`, so there is no
single offending value — pydantic reports the **whole object**:

```
input = {'category': 'billing', 'refund': 10.0, 'contact': 'jo@example.com'}
```

**The one error you would expect to be harmless carries every field the model produced.**

The switch is real and it is per-call:

```python
except ValidationError as e:
    logger.warning("validation failed: %s",
                   e.errors(include_input=False, include_url=False))   # to logs
    feedback = terse(e.errors(include_url=False))                       # to model
```

> **`include_input=True` to the model. `include_input=False` to your logs.** Two audiences, two
> retention policies, two different strings. Most codebases send the same one to both.

### 5.2 The feedback message

`[REAL]` Three ways to describe the same five errors:

| Style | Chars | ~Tokens | Doc URLs | Leaks values |
|---|---|---|---|---|
| `str(e)` | 975 | 243 | yes | **YES** |
| `errors()` as JSON | 679 | 169 | no | **YES** |
| **Terse `loc: msg`** | **251** | **62** | no | **no** |

```python
def terse(errors) -> str:
    return "; ".join(
        f"{'.'.join(str(x) for x in er['loc'])}: {er['msg']}" for er in errors
    )
```

Which produces:

```
who: Extra inputs are not permitted
category: Input should be 'billing', 'technical', 'account' or 'other'
refund: Input should be greater than or equal to 0
contact: String should have at least 5 characters
urgent: Input should be a valid boolean
```

**A quarter of the tokens, no documentation URLs, no values from the output.** The URLs are the clearest
waste: they point at pydantic's error documentation, which the model cannot visit and you pay for on
every repair attempt.

**The obvious objection** — without the value, does the model know what it did wrong? Usually yes: its
own output is two messages up in the conversation. Include the value only when you have stripped the
prior turn to save context (M5-L11).

**A good feedback message names the field and states the rule.** `"Invalid, try again"` tells the model
precisely what it already knew.

### 5.3 Do repair loops converge?

`[MOCK — per-attempt rates specified]`

| Strategy | Kind | Solved | Mean calls | p99 calls | Wasted calls |
|---|---|---|---|---|---|
| No retry | transient | 71.9% | 1.00 | 1 | 5,625 |
| Naive retry | transient | 99.4% | 1.38 | 4 | 7,768 |
| Retry + feedback | transient | **100.0%** | **1.31** | **3** | 6,244 |
| No retry | **systematic** | **0.0%** | 1.00 | 1 | 20,000 |
| Naive retry | **systematic** | **0.0%** | **4.00** | 4 | **80,000** |
| Retry + feedback | **systematic** | **0.0%** | **4.00** | 4 | **80,000** |

**The top half is why repair loops exist.** Feedback converged in fewer calls than naive retry *and*
reached a higher rate — it both works better and costs less, because it succeeds earlier.

**The bottom half is why they must be bounded.** Every strategy solves 0%. The loop is not failing to
help; it *cannot* help, because the same prompt and the same schema produce the same rejection. And
feedback does not rescue it — a better description of an impossible requirement is still impossible.

**How to tell the difference in production:** a systematic failure has a signature. The same field
fails, in the same way, on a stable share of traffic, and the failure rate does not fall with attempt
number. Log the field and the error type (not the value) and this is a one-query answer:

```sql
SELECT field, error_type, attempt, count(*)
FROM validation_failures
GROUP BY 1, 2, 3 ORDER BY 4 DESC;
```

**If attempt 4 fails as often as attempt 1 for a given field, stop retrying that field and fix the
schema.**

### 5.4 The arithmetic of a retry budget

`[REAL — exact, not simulated]` With per-attempt success *p*:

| p | 1 attempt | 2 | 3 | 4 | Mean calls |
|---|---|---|---|---|---|
| 0.99 | 99.00% | 99.99% | 100.00% | 100.00% | 1.01 |
| 0.95 | 95.00% | 99.75% | 99.99% | 100.00% | 1.05 |
| **0.90** | 90.00% | 99.00% | **99.90%** | 99.99% | **1.11** |
| 0.80 | 80.00% | 96.00% | 99.20% | 99.84% | 1.25 |
| 0.72 | 72.00% | 92.16% | 97.80% | 99.39% | 1.38 |
| 0.50 | 50.00% | 75.00% | 87.50% | 93.75% | 1.88 |

**Two decisions come straight out of this table.**

**Where to stop.** At p=0.90, three attempts reach 99.9% and a fourth buys 0.09 points. Attempts beyond
the third are spent almost entirely on requests that were never going to succeed — which is to say, on
systematic failures.

**The tail.** Mean calls at p=0.90 is **1.11**: the average bill barely moves, which is why repair loops
look free in a monthly total. But the one-in-a-thousand request takes four calls and four times the
latency. **That is what your p99 shows and what your users feel**, and it is invisible in a mean.

### 5.5 What an unbounded loop costs

`[REAL arithmetic, illustrative prices]` 100,000 requests/month, 900 in + 120 out tokens per call:

| Scenario | Calls/req | $/month | vs baseline |
|---|---|---|---|
| No validation | 1.00 | $69 | 1.0× |
| Bounded retry, p=0.90, max 3 | 1.11 | $77 | 1.1× |
| Bounded retry, p=0.72, max 4 | 1.63 | $112 | 1.6× |
| Systematic failure, max 4 | 4.00 | $276 | 4.0× |
| **Unbounded loop, 2% systematic** | **2.29** | **$158** | **2.3×** |

Split that last row:

| Traffic | Share | Calls/req | $/month |
|---|---|---|---|
| Behaves (bounded retry) | 98% | 1.11 | $75 |
| **Systematic, spins to 60** | **2%** | **60** | **$83** |

**2% of requests account for 52% of the bill.** The loop reaches 60 calls only because a timeout
somewhere else in the stack eventually kills it — **nothing in the loop itself was ever going to stop**.

**And it will not arrive as a cost incident.** It arrives as a latency incident, because those same 2%
are holding connections open, filling your worker pool, and pushing p99 for everyone else. The invoice
is next month's problem.

### 5.6 What to do when repair fails

Retrying is one of four responses, and usually not the best one:

| Response | When | What the user gets |
|---|---|---|
| **Retry with feedback** | Transient, budget remains | Slightly slower, correct |
| **Degrade** | Part of the output is valid and useful | Less, honestly labelled |
| **Escalate** | The decision matters and cannot be automated | A human, and a queue entry |
| **Fail** | Nothing valid can be returned | An error, and a logged incident |

**Degradation is the most under-used.** If four of five fields validated, returning four fields marked
`partial` is usually better than a hard failure — provided the caller can tell. What is *not*
acceptable is returning four fields as though there were five (M2-L10: an empty result must not look
like a successful one).

```python
def extract(text: str, budget: Budget) -> Result:
    last_error = None
    while budget.allows():                       # attempts AND deadline AND cost
        raw = call_model(text, feedback=last_error)
        try:
            return Result.ok(Decision.model_validate_json(raw))
        except ValidationError as e:
            last_error = terse(e.errors(include_url=False))
            logger.warning("validation failed: fields=%s types=%s",
                           [er["loc"] for er in e.errors()],
                           [er["type"] for er in e.errors()])
            metrics.increment("validation_failure",
                              fields=[er["loc"][0] for er in e.errors()])
    return Result.escalate(reason="validation_budget_exhausted",
                           last_error=last_error)
```

Four things worth noting: **the budget is one object** checked in the loop condition rather than three
scattered conditions; **the log line carries fields and types, never values**; **the metric is per
field**, which is what makes §5.3's systematic-failure query possible; and the function **returns an
escalation rather than raising** — exhausting a budget is an expected outcome, not an exception.

### 5.7 Assumptions and limitations

- §7.3's sections 1, 2, 4 and 5 are real: pydantic behaviour and exact arithmetic.
- Section 3's per-attempt rates are specified. The convergence *shapes* and the systematic result are
  consequences; the rates are not measurements.
- Whether feeding a real model its validation errors helps as much as the mock assumes is **not
  established here**. Measure it on your model and your schema (Exercise 2.4).
- Failures are treated as independent across attempts. Real failures are correlated — the same reason
  self-consistency underperforms (M5-L04 §5.4) — so real retry curves are **worse** than this table.

---

## 6. Worked example — the loop that cost more than the service

**The system.** Invoice extraction, 100,000 documents a month, `strict=True` schema with
`supplier_country: CountryCode`.

**The code.**

```python
while True:
    raw = call_model(prompt)
    try:
        return Invoice.model_validate_json(raw)
    except ValidationError:
        continue
```

**Testing.** Flawless. Every test invoice is from a UK supplier and validates first time.

**Production, week one.** Costs are 2.3× forecast and p99 latency is 94 seconds. The dashboard shows a
normal mean.

**The investigation.** One query — the one §5.3 recommends — gives it away immediately:

```
field              error_type       attempt   count
supplier_country   enum             1         2,014
supplier_country   enum             2         2,014
supplier_country   enum             3         2,014
supplier_country   enum             4         2,014
```

**The count does not fall with attempt number.** That is the signature: 2% of invoices are from
suppliers in a country the enum does not contain, and no number of attempts will invent a code that is
not in the enum.

**Three defects, in order of cost:**

| # | Defect | Consequence |
|---|---|---|
| 1 | `while True` | 2% of traffic spins until an unrelated timeout kills it at ~60 calls |
| 2 | No feedback | Even the transient failures retry blind |
| 3 | No per-field metric | Nobody could see which field, so the investigation started with "the model got worse" |

**Note that the model was never wrong.** It extracted the correct country. The *schema* was wrong, and
the loop's job was to make that fact expensive rather than visible.

### The fix

```python
def extract_invoice(doc: str, budget: Budget) -> Result:
    last_error = None
    while budget.allows():
        raw = call_model(doc, feedback=last_error)
        try:
            return Result.ok(Invoice.model_validate_json(raw))
        except ValidationError as e:
            last_error = terse(e.errors(include_url=False))
            metrics.increment("extract_invalid",
                              field=e.errors()[0]["loc"][0],
                              error_type=e.errors()[0]["type"],
                              attempt=budget.used)
    return Result.escalate("validation_budget_exhausted", last_error)
```

Plus two changes that are not in the loop at all:

- **An alert on "failure rate flat across attempt number", per field.** That is the systematic-failure
  detector, and it would have fired in hour one.
- **A widened enum** — or, better, a `supplier_country` validated against a reference list loaded from
  data, so adding a country is a data change rather than a deploy.

**The general lesson.** The loop was written to handle failure. It was not written to notice that the
failure never changed. **A retry loop without a per-attempt metric is a way of converting a visible bug
into an invoice.**

---

## 7. Practical activity

**File:** [`labs/m5/l07_validation_repair.py`](../../labs/m5/l07_validation_repair.py)

**No API key, no network, no cost.**

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l07_validation_repair.py
```

Sections 1, 2, 4 and 5 involve **no model**: real pydantic error structures, real message sizes, and
exact probability and cost arithmetic. Section 3 uses a mock to compare retry strategies.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.12.3, pydantic 2.13.5, NumPy 2.5.3.

```text
============================================================================
1. WHAT A VALIDATION ERROR ACTUALLY CONTAINS
============================================================================
  Real pydantic. For each bad output: how many errors, do they name the
  field, and -- the part nobody checks -- do they contain the VALUE?

  bad output            errors                      fields named   value included
  wrong enum                 1                          category              YES
  out of bounds              1                            refund              YES
  string number              1                            refund              YES
  missing field              1                            urgent              YES
  extra field                1                          approved              YES
  several at once            5  who,category,refund,contact,urge              YES

  6/6 error sets carry the offending INPUT VALUE.

  And note the 'missing field' case. Its error type is 'missing', so there is
  no single offending value -- pydantic reports the WHOLE OBJECT as
  the input:
    input = {'category': 'billing', 'refund': 10.0, 'contact': 'jo@example.com'}
  The one error you would expect to be harmless carries every field
  the model produced, customer contact details included.
  That is excellent for feeding back to the model and a liability the
  moment you log it: the invalid value is frequently the customer's
  email address, name, or free text.

  The same error, two ways:

    e.errors()                       -> 971 chars, contains input values
    e.errors(include_input=False,
             include_url=False)      -> 600 chars, no values

    contact field, with input   : {'type': 'string_too_short', 'loc': ('contact',), 'msg': 'String should have at least 5 characters', 'input': 'x', 'ctx': {'min_length': 5}, 'url': 'https://errors.pydantic.dev/2.13/v/string_too_short'}
    contact field, without input: {'type': 'string_too_short', 'loc': ('contact',), 'msg': 'String should have at least 5 characters', 'ctx': {'min_length': 5}}

  Rule: errors(include_input=True) to the MODEL, errors(include_input=
  False) to your LOGS. They are different audiences with different
  retention. Most codebases send the same string to both.

============================================================================
2. BUILDING THE FEEDBACK MESSAGE
============================================================================
  Three ways to tell the model what was wrong, and what each costs.

  style                        chars   ~tokens  doc URLs  leaks values
  str(e)                         975       243       yes           YES
  errors() as JSON               679       169        no           YES
  terse loc: msg                 251        62        no            no

  The terse form, in full:

    who: Extra inputs are not permitted
    category: Input should be 'billing', 'technical', 'account' or 'other'
    refund: Input should be greater than or equal to 0
    contact: String should have at least 5 characters
    urgent: Input should be a valid boolean

  All three name every broken field and state every rule. They differ
  in what else they carry: documentation URLs the model cannot use and
  you pay for on every repair attempt, and input values you may not
  want in a prompt you are about to log.

  The terse form wins three ways at once: a quarter of the tokens,
  no documentation URLs, and no values from the model's output.

  The obvious objection: without the input value, does the model know
  what it did wrong? Usually yes -- its own output is already in the
  conversation, so repeating the value back spends tokens telling it
  something it can read two messages up. Include the value only when
  you have stripped the prior turn to save context (M5-L11).

  A good feedback message is the FIELD and the RULE it broke. Not
  'that was invalid, try again', which tells the model exactly what
  it already knew.

============================================================================
3. DO REPAIR LOOPS CONVERGE?  [MOCK]
============================================================================
  Three strategies against two kinds of failure.

    transient  -- the model can produce a valid answer; this one missed
    systematic -- the schema and the prompt disagree; no sample is valid

  Rates are specified. Convergence and cost are consequences.

  strategy              kind            solved  mean calls  p99 calls  wasted calls
  no retry              transient        71.9%        1.00          1         5,625
  no retry              systematic        0.0%        1.00          1        20,000
  naive retry           transient        99.4%        1.38          4         7,768
  naive retry           systematic        0.0%        4.00          4        80,000
  retry + feedback      transient       100.0%        1.31          3         6,244
  retry + feedback      systematic        0.0%        4.00          4        80,000

  Read the systematic rows. Every retry strategy solves 0%, and the
  4-attempt loop burns four calls per request to do it. The loop is
  not failing to help -- it cannot help, because the same prompt and
  the same schema produce the same rejection.

  A repair loop is a bet that the failure was transient. If you do not
  measure which kind you have, you are paying 4x on the ones where the
  answer is to change the schema or the prompt.

============================================================================
4. THE ARITHMETIC OF A RETRY BUDGET
============================================================================
  Exact, not simulated. p = per-attempt success probability.

       p   1 attempt         2         3         4   mean calls (max 4)
    0.99      99.00%    99.99%   100.00%   100.00%                 1.01
    0.95      95.00%    99.75%    99.99%   100.00%                 1.05
    0.90      90.00%    99.00%    99.90%    99.99%                 1.11
    0.80      80.00%    96.00%    99.20%    99.84%                 1.25
    0.72      72.00%    92.16%    97.80%    99.39%                 1.38
    0.50      50.00%    75.00%    87.50%    93.75%                 1.88

  Two things this table decides for you:

  1. WHERE TO STOP. At p=0.90, three attempts reach 99.9% and a fourth
     buys 0.09 points. Attempts 4+ are almost entirely spent on
     requests that were never going to succeed.
  2. THE TAIL. Mean calls at p=0.90 is 1.11 -- the average bill barely
     moves. But the 1-in-1000 request takes 4 calls and 4x the latency,
     and that is what your p99 shows and your users feel.

  A retry loop must be bounded by all three:

    bound                 why                                             
    attempts              stops the infinite loop                         
    deadline              stops a slow provider becoming a slow you       
    cost                  stops a retry storm becoming an invoice         

  Attempts alone is not enough: 4 attempts at 30 s each is a 2-minute
  request, and the user left after 10 s (M2-L14).

============================================================================
5. WHAT AN UNBOUNDED LOOP COSTS
============================================================================
  A real, common bug: retry until valid, no cap.

  100,000 requests/month, 900 in + 120 out tokens/call,
  $0.000690 per call  [ILLUSTRATIVE]

  scenario                                calls/req     $/month   vs baseline
  no validation (1 call)                       1.00         $69          1.0x
  bounded retry, p=0.90, max 3                 1.11         $77          1.1x
  bounded retry, p=0.72, max 4                 1.63        $112          1.6x
  SYSTEMATIC failure, max 4                    4.00        $276          4.0x
  unbounded loop, 2% systematic                2.29        $158          2.3x

  The last row is the one that reaches production. Split it:

    traffic                        share  calls/req    $/month
    behaves (bounded retry)          98%       1.11        $75
    systematic, spins to 60           2%         60        $83

  2% of requests account for 52% of the bill (1.1x what the
  other 98% costs). It reaches 60 calls only because a timeout
  elsewhere in the stack eventually kills it -- nothing in the loop
  itself was ever going to stop.

  And it will not look like a cost incident. It looks like a latency
  incident, because the same 2% are also holding connections open.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1 (pydantic 2.13.5 error structure, including the
  include_input switch), section 2 (message sizes), section 4 (exact
  probability arithmetic) and section 5 (cost arithmetic).

  MOCK: section 3's per-attempt success rates are specified. What is
  NOT specified, and is the point: that no strategy moves a systematic
  failure off 0%, and what the loop costs while failing to.

  NOT SHOWN: whether feeding a real model its validation errors helps
  as much as the mock assumes. Measure that on your model, on your
  schema -- exercise 2.4.

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Error sets carrying the offending input value | **6 / 6** |
| Missing-field error's `input` | **the entire object** |
| `str(e)` vs terse feedback | 243 vs **62** tokens |
| Terse form: doc URLs, leaked values | none, none |
| Retry + feedback, transient | 100.0% in **1.31** mean calls |
| Naive retry, transient | 99.4% in 1.38 mean calls |
| **Every strategy, systematic failure** | **0.0%**, 4.00 calls, 80,000 wasted |
| Attempts to 99.9% at p=0.90 | **3** |
| Mean calls at p=0.90 | 1.11 — but p99 is 4 |
| Unbounded loop: share of bill from 2% of traffic | **52%** |

**Four things worth taking away.**

**1. Your validation errors contain customer data, and the harmless-looking one contains the most.** A
`missing` error has no single offending value, so pydantic reports the whole object — every field the
model produced. `include_input=False` for logs, `True` for the model.

**2. The best feedback message is also the cheapest.** Terse `field: rule` is 62 tokens against 243,
carries no documentation URLs the model cannot use, and leaks no values. It is not a trade-off.

**3. Feedback converged faster than naive retry** — 1.31 calls against 1.38, at a higher success rate.
It costs less *because* it works better.

**4. No strategy moved a systematic failure off 0%, and the loop spent four calls per request finding
that out.** In the unbounded version, 2% of traffic produced 52% of the bill, and it presented as a
latency incident rather than a cost one.

**What transfers:** everything in sections 1, 2, 4 and 5 — library behaviour and arithmetic. **What
does not:** section 3's per-attempt rates, and — importantly — its assumption that attempts are
independent. Real failures are correlated, so real curves are worse than this table.

---

## 8. Common mistakes and troubleshooting

1. **`while True`.** The single most expensive line in this lesson.
2. **Bounding by attempts only.** Four attempts at 30 s is a two-minute request.
3. **Retrying a systematic failure.** 0% solved, 4× the calls.
4. **No per-field, per-attempt metric.** Without it you cannot tell the two kinds apart.
5. **`"Invalid, try again"` as feedback.** Tells the model what it already knew.
6. **Sending `str(e)` to the model.** 4× the tokens and every input value.
7. **Logging `str(e)`.** Customer data in your log store (M2-L18).
8. **Retrying a truncated response.** Fix the token limit; the output was cut, not wrong (M4-L15).
9. **Retrying at temperature 0.** The same input produces near-identical output; nothing changed.
10. **Failing hard when partial output was useful.** Degrade, and label it.
11. **Returning partial output as though complete.** Worse than failing (M2-L10).
12. **Raising on budget exhaustion.** It is an expected outcome; return it.

| Symptom | Likely cause | Fix |
|---|---|---|
| Costs up, mean latency normal, p99 terrible | A minority spinning in a loop | Bound by cost and deadline; per-field metric |
| Failure count identical at every attempt | Systematic failure | Fix schema or prompt; stop retrying |
| Retries never help at temperature 0 | Deterministic output | Vary the prompt, not just the attempt |
| Customer emails in the log store | `str(e)` or `include_input=True` in logs | `include_input=False` |
| Repair works locally, not in production | Real inputs hit schema edges | Build the corpus from real failures |
| p99 latency = max attempts × timeout | No deadline bound | Add one; it is not the same as attempts |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** **Validation errors carry the invalid value**, and a `missing` error carries the whole
  object. `include_input=False` for anything that reaches a log (M2-L18).
- **Privacy.** The feedback message goes back to the provider on the next request. If it contains input
  values, you have sent that data twice (M10-L05).
- **Cost.** Bound by attempts, deadline **and** cost. A 2% systematic failure produced 52% of the bill.
- **Cost.** A repair loop inside an HTTP retry (M2-L14) is a multiplier on a multiplier. Bound the
  outer one too.
- **Reliability.** Exhausting a budget is an expected outcome. Return an escalation; do not raise.
- **Reliability.** Emit a metric per field and per attempt. It is what makes a systematic failure a
  one-query diagnosis rather than a week.
- **Security.** Never widen a schema to make failures stop. The bound that keeps failing may be the one
  stopping a £1M refund (M5-L06 §5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. Give the one question to answer before writing a retry.
2. Name the three bounds a repair loop needs and what each prevents.
3. At p=0.95, how many attempts reach 99.9%?
4. Why must `include_input` differ between your logs and your feedback message?
5. Which four responses are available when repair fails, and when is each right?

### Exercise 2 — Intermediate (~45 min)

1. Run the lab. Report the token difference between `str(e)` and the terse form, and what else differs.
2. Write `terse()` and prove with a test that it contains no value from a deliberately invalid input.
3. Implement a `Budget` class enforcing attempts, deadline and cost, with tests for each bound.
4. `[NOT EXECUTED — needs a key]` On a real model, measure whether feedback actually lifts the repair
   rate on your schema, and by how much, with intervals.
5. Write the SQL and the alert condition that distinguish a systematic failure from a transient one.

### Exercise 3 — Challenge (~60 min)

1. Build the full loop from §5.6 with metrics, and demonstrate the §6 investigation on synthetic data.
2. Add correlated failures to the lab's section 3 — a shared cause that fires on 40% of attempts for
   the same input — and report how the convergence table changes.
3. Design a degradation path for a five-field extraction where two fields are optional. State exactly
   how the caller distinguishes partial from complete.
4. Measure the p99 latency impact of max-attempts 2, 3 and 4 given a provider latency distribution you
   state, and recommend a bound.
5. Write the runbook entry for "extraction cost doubled overnight" that reaches the right diagnosis in
   under ten minutes.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l07).)*

**Q1.** Against a systematic failure, retry with feedback solved:

- A. 0% — no strategy can help, and the loop spends four calls proving it.
- B. About 70%, since feedback guides the model.
- C. 100%, given enough attempts.
- D. It depends on the sampling temperature.

**Q2.** How many of six malformed outputs produced errors containing the input value?

- A. None — pydantic omits values by default.
- B. Two, only for string fields.
- C. Four of six.
- D. All six.

**Q3.** A `missing` field error is a larger privacy risk than the others because:

- A. It is logged at a higher severity.
- B. Its `input` is the whole object, not one value.
- C. It cannot be caught with `include_input=False`.
- D. It triggers more retries.

**Q4.** The terse `field: rule` feedback message compared with `str(e)`:

- A. Is cheaper but omits which field failed.
- B. Is more expensive but clearer to the model.
- C. Is equivalent; the difference is stylistic.
- D. Costs a quarter of the tokens, carries no URLs and leaks no values.

**Q5.** At p=0.90 per attempt, how many attempts reach 99.9%?

- A. Three.
- B. Five.
- C. Two.
- D. Ten.

**Q6.** Mean calls at p=0.90 with max 4 attempts is 1.11. The reason this understates the problem:

- A. It excludes the input tokens.
- B. It assumes retries are free.
- C. Mean is the wrong statistic for cost.
- D. The p99 request still takes four calls and four times the latency.

**Q7.** In the unbounded-loop scenario, 2% of traffic accounted for:

- A. 52% of the bill.
- B. About 10% of the bill.
- C. 2% of the bill, as expected.
- D. All of the bill.

**Q8.** The signature of a systematic failure in your metrics is:

- A. Failures clustering at particular times of day.
- B. A rising failure rate across attempts.
- C. Failure count for a field that does not fall with attempt number.
- D. Errors appearing in more than one field at once.

**Q9.** A repair loop is bounded by attempts only. What is still unprotected?

- A. Nothing; attempts is the binding constraint.
- B. Latency and cost — four attempts at 30 s each is a two-minute request.
- C. Only correctness.
- D. Only the provider's rate limit.

**Q10.** Retrying at temperature 0 after a validation failure:

- A. Is the recommended approach, since it is deterministic.
- B. Changes little — the same input produces near-identical output.
- C. Doubles the chance of success.
- D. Is required for schema compliance.

**Q11.** Four of five fields validated. The best response is usually to:

- A. Return the four silently, so the caller is not disrupted.
- B. Fail the whole request; partial data is never useful.
- C. Return the four, clearly labelled partial, if the caller can act on them.
- D. Widen the schema so the fifth field passes.

**Q12.** Exhausting a retry budget should be:

- A. Raised as an exception, since it is a failure.
- B. Retried once more outside the loop.
- C. Returned as an expected outcome the caller can handle.
- D. Logged and silently ignored.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your extraction service's cost doubled
overnight, the mean latency dashboard looks normal, and p99 is 90 seconds. Give your first hypothesis,
the one query that confirms it, and the two fixes — one immediate, one structural.

---

## 12. Revision notes

- **Ask first: could this model, with this prompt and this schema, have produced a valid answer?**
  Transient → retry. Systematic → **0% solved at 4× the cost**.
- **Systematic failures have a signature**: the same field, same error type, **count flat across
  attempt number**. One query, if you emit the metric.
- **Bound by attempts, deadline AND cost.** Attempts alone gives you a two-minute request.
- **Validation errors carry the input value — 6 of 6.** A `missing` error carries the **whole object**.
- **`include_input=False` to logs, `True` to the model.** Two audiences, two retentions.
- **Terse `field: rule` feedback: 62 tokens vs 243**, no URLs, no values. Cheapest *and* best.
- **Feedback converged faster than naive retry** (1.31 vs 1.38 calls) at a higher success rate.
- **At p=0.90, three attempts reach 99.9%.** A fourth buys 0.09 points and is spent on systematic
  failures.
- **The mean hides the tail.** 1.11 mean calls, p99 of 4 — that is what users feel.
- **`while True` is the most expensive line in this lesson.** 2% of traffic, 52% of the bill, presenting
  as a latency incident.
- **Four responses, not one:** retry, degrade, escalate, fail. **Degradation is under-used** — but
  partial output must never look complete (M2-L10).
- **Budget exhaustion is an outcome, not an exception.** Return it.
- **Never widen a schema to make failures stop.** That bound may be the one stopping a £1M refund.
- **Real failures are correlated**, so real retry curves are worse than the independent-attempt table.

---

## 13. Completion checklist

- [ ] I classify a failure as transient or systematic before retrying.
- [ ] My loops are bounded by attempts, deadline and cost.
- [ ] I emit a per-field, per-attempt failure metric.
- [ ] My feedback message names the field and the rule, and nothing else.
- [ ] My logs use `include_input=False`.
- [ ] I return budget exhaustion rather than raising it.
- [ ] I can state my p99 attempt count, not just the mean.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Pydantic docs — Error handling.
  <https://docs.pydantic.dev/latest/concepts/models/#error-handling> `[UNVERIFIED]`
- Pydantic docs — `ValidationError.errors()`.
  <https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError> `[UNVERIFIED]`
- Google SRE Book, *Handling Overload* — retry budgets and amplification.
  <https://sre.google/sre-book/handling-overload/> `[UNVERIFIED]`
- AWS Architecture Blog, *Exponential Backoff and Jitter*.
  <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L08 — Tool Definitions and Tool-Call Arguments](M5-L08-tools.md)

You can constrain what the model says and decide what to do when it says something unusable. Next: what
happens when the output is not text to read but an action to take.
