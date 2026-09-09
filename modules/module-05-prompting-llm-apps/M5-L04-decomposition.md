# M5-L04 — Task Decomposition and Reasoning Prompts

| | |
|---|---|
| **Lesson ID** | M5-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M5-L03](M5-L03-few-shot.md), [M4-L14](../module-04-genai-llm-internals/M4-L14-decoding.md) |

---

## 1. Learning objectives

1. **Explain** what "let's think step by step" does mechanically, and what it does not do.
2. **Decide** whether a task should be one call or several, using error accumulation rather than taste.
3. **Predict** how per-step accuracy compounds across a chain, and why an early error is fatal.
4. **Judge** self-consistency by the property it depends on — error independence — rather than by its
   reputation.
5. **Distinguish** a technique that improves a number from one that changes a shipping decision.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Decomposition** | Breaking a task into smaller stated steps, in one prompt or several calls. |
| **Chain of thought (CoT)** | Prompting the model to emit intermediate reasoning before its answer. |
| **Zero-shot CoT** | Adding a phrase such as *"think step by step"* with no worked examples. |
| **Intermediate value** | A partial result the model writes down on the way to its answer. |
| **Error propagation** | A wrong intermediate making every later step wrong. |
| **Self-consistency** | Sampling the same prompt k times and taking the majority answer. |
| **Agreement** | The fraction of samples that produced the winning answer. |
| **Independent errors** | Mistakes that differ from sample to sample. |
| **Systematic error** | The same mistake on every sample of the same input. |
| **Faithfulness** | Whether stated reasoning is an honest account of how the answer was produced. |
| **Verifier** | Deterministic code that checks the model's output or working. |

---

## 3. Plain-language explanation

### 3.1 Why a long task fails when its parts do not

A model that gets each small step right 95% of the time does **not** get a twelve-step task right 95% of
the time. It gets it right 0.95¹² ≈ **54%** of the time, because every step must be right for the
answer to be right.

This is the single most useful piece of arithmetic in this module, and it explains a family of
complaints that look unrelated:

- *"It's usually right but sometimes wildly wrong."*
- *"It works on my examples and fails on real ones."* (Real ones are longer.)
- *"It got the hard part right and the easy part wrong."*

**Nothing is wrong with the model's reasoning. The chain is just long.**

### 3.2 What "think step by step" actually changes

The popular explanation is that the phrase makes the model *reason*. That is not a mechanism.

Here is one. A model produces one token at a time, and each token is computed by a fixed amount of
work (M4-L10). An answer emitted immediately must be produced in that fixed budget. An answer emitted
after two hundred tokens of working has had two hundred forward passes to accumulate — and, crucially,
**each intermediate result is written into the context, where later steps can attend to it** rather
than having to reconstruct it.

**Writing a value down is cheaper and safer than carrying it.** That is all the lab models, and it is
enough to reproduce the effect.

### 3.3 The part that is usually left out

Decomposition has a second consequence that matters more than the first, and it is almost never the
reason people give for using it:

> **A decomposed answer contains intermediate values, and intermediate values can be checked by code.**

A model that answers `1847` gives you nothing to verify. A model that shows twelve steps gives you
twelve claims, each of which your own program can recompute in microseconds, for free, with no model
involved. §7.3 measures a plausibility check on the final answer catching **9.4%** of errors, and
recomputation of the written steps catching **100%**.

The technique that works is not "ask it to reason". It is **"ask it to show its working, then check
the working in ordinary code"**.

---

## 4. Analogy

A colleague doing long multiplication in their head versus on paper.

On paper they are more reliable — not because writing makes them cleverer, but because a written digit
cannot be forgotten while they work on the next one. And when the answer is wrong, **you can find where
it went wrong**, because the working is there.

### Where the analogy breaks

- **Your colleague's working is a record of what they did.** A model's chain of thought is *generated
  text*, produced by the same process as the answer. It can be a fluent, plausible, entirely post-hoc
  story. §7.3's mock cannot show this, and says so.
- **Your colleague notices when a number looks absurd.** The model has no separate faculty checking
  the result against the world.
- **Your colleague does not charge you per digit.** Working is output tokens, at output prices — §7.3
  prices twelve steps at **5× the direct prompt's bill**.

---

## 5. Detailed technical explanation

### 5.1 The compounding, precisely

For an *n*-step task where each step succeeds independently with probability *p*:

```
P(whole task correct) = p^n
```

| p | n=3 | n=8 | n=12 | n=20 |
|---|---|---|---|---|
| 0.99 | 97% | 92% | 89% | 82% |
| 0.97 | 91% | 78% | 69% | 54% |
| 0.95 | 86% | 66% | 54% | 36% |
| 0.90 | 73% | 43% | 28% | 12% |

**Read the 0.95 row.** A step accuracy you would call excellent produces a twenty-step task you cannot
ship. **The lever with the most force is *n*, not *p*** — halving the chain length beats a large
improvement in per-step accuracy, and it is usually the cheaper change to make.

### 5.2 What decomposition buys, measured

§7.3 compares a monolithic prompt with a decomposed one, holding everything else constant. The
decomposed prompt's per-step slip rate is lower (3.0% vs 4.5%), which is the *entire* difference.

| Steps | Direct | Decomposed | Gain |
|---|---|---|---|
| 1 | 96.8% | 96.8% | +0.0% |
| 3 | 85.5% | 91.9% | +6.4% |
| 8 | 66.1% | 78.3% | +12.2% |
| 20 | 40.3% | 55.7% | **+15.4%** |

The gain **grows with chain length**. A one-step task gains nothing, because there is no accumulation
to prevent.

**And now the finding that matters.** Set a usability bar and ask whether decomposition moves the task
*across* it:

| Bar | Direct already passes | Decomposition flips it | Both fail |
|---|---|---|---|
| 95% | 1 | 2 | 3, 5, 8, 12, 20 |
| 90% | 1, 2 | 3 | 5, 8, 12, 20 |
| **80%** | 1, 2, 3, 5 | **none** | 8, 12, 20 |
| 70% | 1, 2, 3, 5 | 8 | 12, 20 |
| 60% | 1, 2, 3, 5, 8 | 12 | 20 |

**At any given bar, at most one chain length changes verdict.** At an 80% bar, none does. The
+15.4-point gain at twenty steps takes a task from 40% to 56% — a large number, and it ships nothing.

> **Set the bar before you measure, or you will celebrate improvements that change no decision.**

This is not an argument against decomposition. It is an argument against reading gain columns.

### 5.3 Where errors enter and how far they survive

§7.3 instruments the decomposed run and finds the first wrong intermediate. The position is roughly
uniform — each step carries the same slip probability. **The consequence is not uniform at all:**

| First error at | Final answer correct |
|---|---|
| Steps 1–4 (early) | 0.8% |
| Steps 5–8 (middle) | 0.0% |
| Steps 9–12 (late) | 0.0% |

Of 1,000 trials, 320 had a corrupted intermediate; **one** of those recovered.

**There is no self-correction.** Every subsequent step is computed from a wrong number, competently.
The model does not notice, because nothing in the mechanism is checking. **Do not rely on a later step
catching an earlier one** — put the check in your code.

### 5.4 Self-consistency, and the property it silently assumes

Sample the same prompt k times, take the majority answer. §7.3 runs it under three regimes that differ
*only* in how the model's errors relate across samples:

| k | Independent acc / agree | 60% correlated acc / agree | Systematic acc / agree |
|---|---|---|---|
| 1 | 70.0% / 100% | 71.0% / 100% | 70.0% / 100% |
| 3 | 87.5% / 71.0% | 77.0% / 82.7% | 70.0% / 100% |
| 9 | 100.0% / 68.1% | 74.5% / 81.1% | 70.0% / 100% |
| 25 | **100.0%** / 68.7% | **72.5%** / 79.4% | **70.0%** / 100% |

Same task, same single-sample accuracy, same 25× bill. **+30.0 points, +1.5 points, and +0.0 points.**

Now read the agreement column:

```
benefit:     +30.0%        +1.5%         +0.0%
agreement:    68.7%        79.4%        100.0%
                ↑             ↑             ↑
          works well     capped        useless
```

**Agreement is highest exactly where voting helps least.** This is not a coincidence — it is the same
fact stated twice. Voting helps when samples disagree, because disagreement is what lets the correct
answer outvote scattered wrong ones. Perfect agreement means the model reproduced itself, and a
reproduced error is still an error.

> **Self-consistency does not measure correctness. It measures reproducibility.** They coincide only
> when errors are independent — an assumption about your model, not a property of the technique.

Two practical consequences:

- **Agreement is a bad confidence signal** and is widely used as one. It reads 100% on a single sample,
  where it is measuring nothing at all, and 100% under systematic error, where it is measuring the
  wrong thing confidently. (M5-L18 covers signals that do work.)
- **The 60%-correlated column is the realistic one.** Real models have shared quirks — a units
  convention, an ambiguous phrasing read the same way each time. A quirk firing on 60% of samples caps
  accuracy at 72.5% *no matter how many samples you buy*.

### 5.5 Verification: check the working, not the answer

| Check | Wrong answers caught |
|---|---|
| Plausibility of the final answer | 9.4% |
| Recomputation of the written steps | **100%** |

A corrupted digit usually lands inside any range you would have called sane. Recomputation catches
everything **because the working is available** — and the working is available only because the prompt
was decomposed.

```python
def check_working(start: int, steps: list[tuple[str, int]],
                  written: list[int]) -> int | None:
    """Return the index of the first step whose written value is wrong."""
    v = start
    for i, (op, k) in enumerate(steps):
        expect = v + k if op == "+" else v - k if op == "-" else v * k
        if written[i + 1] != expect:
            return i
        v = written[i + 1]
    return None
```

**That function contains no model, costs nothing, and is the most effective control in this lesson.**
Note what it requires: the model must emit its intermediates in a *parseable* form. This is where M5-L06
(structured output) and this lesson meet — "show your working" is only useful if the working is
machine-readable.

### 5.6 One call or several?

| | Single call, decomposed | Separate call per step |
|---|---|---|
| Latency | One round trip | n round trips |
| Cost | One prompt | n prompts, each re-sending context |
| Error isolation | You see where it broke | You can **retry just the broken step** |
| Validation | After the fact | **Between every step** |
| Complexity | A prompt | An orchestrator (Module 8) |

**Split when you need to act between steps** — validate, retry, call a tool, ask a human. **Keep it in
one call when the steps are pure reasoning and you only need to see them.**

Note what §7.3's table implies: beyond about five steps, no prompting technique rescued the task.
That is the boundary where this module ends and **Module 8 (agents)** begins — not because agents are
more advanced, but because the answer stops being a better prompt.

### 5.7 When decomposition does not help, or hurts

- **Single-step tasks.** Measured gain: +0.0%. Pure cost.
- **Classification with a small label set.** Reasoning about four labels invites elaborate arguments
  for the wrong one.
- **Latency-sensitive paths.** 176 output tokens instead of 8 (§7.3) is a real delay.
- **When the working is never read.** If nothing parses it, you paid output prices for text you threw
  away — the commonest waste in this lesson.
- **Reasoning models.** Models trained to reason internally may perform *worse* when instructed to
  reason in the output, and providers commonly advise against stacking CoT prompts on them.
  `[UNVERIFIED — check your provider's current guidance for the specific model.]`

### 5.8 Faithfulness: the limit of everything above

Everything in §5.1–5.7 is about *whether the answer is right*. None of it establishes that the stated
reasoning is *how the model got there*.

The chain of thought is generated text. It is produced by the same next-token process as the answer,
and it can be a fluent reconstruction attached to a conclusion reached otherwise. Published work has
found models giving reasoning that omits the cue that actually drove the answer.
`[UNVERIFIED — the general finding is well attested; magnitudes vary by model and setup.]`

**§7.3's mock cannot test this**, and says so: its written steps *are* its computation, by
construction. Treat this as the lab's boundary, not as reassurance.

Two consequences you can act on today:

- **Never present a chain of thought to a user as an explanation** of why the system decided something,
  particularly where a regulation requires a real one (M10-L07).
- **Verify the working against the world, not against the story.** Recomputation checks arithmetic;
  it does not check that the model's stated reason is its actual reason.

### 5.9 Assumptions and limitations

- The lab's task is arithmetic with a single error mechanism. Real errors are not one corrupted digit.
- `p^n` assumes independent steps. Real steps are correlated — often *worse* than independent, because
  a misread instruction affects all of them.
- All magnitudes here come from a mock. **The shapes and the method transfer; the numbers do not.**
- The self-consistency regimes (0%, 60%, 100% correlation) are chosen, not measured. What is *not*
  chosen is the resulting accuracy and agreement curves.

---

## 6. Worked example — the twelve-step extraction that fails once in three

**The task.** Extract twelve fields from a supplier invoice: number, date, supplier, twelve line items
totalled, tax rate applied, currency, terms.

**The prompt.** *"Extract all the invoice details and return JSON."*

**The complaint.** *"It's right most of the time, but every third invoice has something wrong, and it's
never the same thing."*

**The diagnosis, with no debugging.** Twelve extractions, each independently right ~97% of the time:

```
0.97^12 = 0.69
```

**31% of invoices have at least one wrong field**, and the field varies because the failure is random,
not structural. This matches the complaint exactly, and it required no investigation — only §5.1.

**What does not fix it:**

| Attempt | Why it fails |
|---|---|
| *"Be careful and double-check"* | Not a mechanism. The model has no separate checking faculty. |
| A better model | 0.99 per field still gives 89% — better, still one invoice in nine. |
| Asking it to reason | §7.3: at twelve steps, +10.8 points → 68.1%. Still unshippable. |
| Self-consistency, k=9 | 9× the cost, and **+1.5 points if the errors are correlated** — which for a fixed template they will be. |

**What does fix it,** in order of force:

1. **Shorten the chain.** Extract the four fields that drive the workflow in one call and the rest in
   another. Two chains of six beat one of twelve: 0.97⁶ = 83% each, and **you now know which half
   failed**.
2. **Make each field checkable, then check it.** Dates parse. Currencies are in a closed set. Line
   items sum to the total. Tax equals rate × subtotal. This is deterministic code, it costs nothing,
   and — as in §7.3 — it is the control that finds the errors.
3. **Fail loudly on the checks.** A field that fails its check is not a field; it is an escalation
   (M5-L14).

**The general form:** when a chain is too long, do not improve the model's odds on each link —
**remove links, and check the ones that remain.**

**And note the invoice total.** `sum(line_items) == total` is the whole game: a check that ties the
model's output to an *independent* fact, rather than asking the model whether it is confident. The
model's confidence is generated text; the sum is arithmetic.

---

## 7. Practical activity

**File:** [`labs/m5/l04_decomposition.py`](../../labs/m5/l04_decomposition.py)

**No API key, no network, no cost.** Deterministic (`zlib.crc32`). Runs in about one second.

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l04_decomposition.py
```

The mock has exactly one error mechanism: a single corrupted decimal digit, at 4.5% per carried step
and 3.0% per written step, with a controllable tendency to repeat itself across samples. **Everything
the lab reports is a consequence of that mechanism, not a further assumption.**

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.12.3, NumPy 2.5.3.

```text
============================================================================
1. DOES DECOMPOSITION HELP? IT DEPENDS ON THE LENGTH
============================================================================
  Task: chained arithmetic. 'start with 84, add 17, multiply by 3, ...'
  The mock slips one digit with probability 4.5% per carried step,
  3.0% per written step. That is the ONLY difference between the two
  prompts -- writing a value down makes it slightly harder to lose.

  200 problems x 5 runs = 1000 trials per cell

    steps    direct   decomposed   difference            both intervals
        1     96.8%        96.8%        +0.0%        96%-98% vs 96%-98%
        2     91.5%        95.4%        +3.9%        90%-93% vs 94%-97%
        3     85.5%        91.9%        +6.4%        83%-88% vs 90%-93%
        5     80.0%        87.8%        +7.8%        77%-82% vs 86%-90%
        8     66.1%        78.3%       +12.2%        63%-69% vs 76%-81%
       12     57.3%        68.1%       +10.8%        54%-60% vs 65%-71%
       20     40.3%        55.7%       +15.4%        37%-43% vs 53%-59%

  The gain from decomposing is not constant. It is smallest at 1 step(s) (+0.0%)
  and largest at 20 steps (+15.4%) -- it grows with chain length.

  Both curves fall, because both accumulate slips. Decomposition does
  not stop error accumulation -- it lowers the per-step rate. On a
  one-step task there is nothing to accumulate and nothing to gain.

  Now stop reading the gain column and ask the question that decides
  whether to ship: at each length, does decomposition move the task
  ACROSS a usability bar, or just move it within a band it fails in?

     bar        lengths where only       lengths where      lengths where
             DIRECT already passes     DECOMP flips it          BOTH fail
     95%                         1                   2        3,5,8,12,20
     90%                       1,2                   3          5,8,12,20
     80%                   1,2,3,5          -- none --            8,12,20
     70%                   1,2,3,5                   8              12,20
     60%                 1,2,3,5,8                  12                 20
     50%              1,2,3,5,8,12                  20         -- none --

  Decomposition changes the VERDICT only at lengths 2,3,8,12,20 --
  and at any one bar, at most one or two lengths. Everywhere else it
  moves a number without moving a decision: the task was already fine
  without it, or it fails with it.

  This is the question to ask of every prompting technique, and the
  gain column will not answer it. A +15.4% that takes you from 40% to
  56% has bought you nothing you can ship. Set the bar FIRST, then
  measure, or you will celebrate improvements that change no outcome.

  Past the band, you do not need a better prompt -- you need to stop
  asking one call to do the whole job. Section 4 shows what to do
  instead, and it is not a prompting technique.

============================================================================
2. WHERE THE ERROR ENTERS, AND HOW FAR IT SURVIVES
============================================================================
  12-step problems, 1000 trials.
  Trials where at least one intermediate was wrong: 320
  Of those, trials whose FINAL answer was nevertheless right: 1 (0.3%)

  Position of the FIRST wrong intermediate (1 = the first computed):
  step   1     37  ########################################
  step   2     27  #############################
  step   3     34  #####################################
  step   4     29  ###############################
  step   5     31  ##################################
  step   6     24  ##########################
  step   7     27  #############################
  step   8     30  ################################
  step   9     27  #############################
  step  10     14  ###############
  step  11     20  ######################
  step  12     20  ######################

  Roughly uniform, as the mechanism implies -- each step carries the
  same slip probability. But the CONSEQUENCE is not uniform:

  first error at step       final answer correct
  1-4  (early)                             0.0%  (n=127)
  5-8  (middle)                            0.0%  (n=112)
  9-12 (late)                              1.2%  (n=81)

  An early error is almost never survived: everything after it is
  computed from a wrong number. This is why a 95%-per-step model is
  not a 95% model -- and why the verification in section 4 has to
  check intermediates, not just the answer.

============================================================================
3. SELF-CONSISTENCY: WHAT MAJORITY VOTING ACTUALLY MEASURES
============================================================================
  Sample the same prompt k times, take the majority answer. Run it
  under three regimes that differ ONLY in how the model's errors
  relate to each other across samples:

    independent  -- fresh noise every sample (the textbook assumption)
    correlated   -- the same quirk on 60% of samples, noise on 40%
    systematic   -- the same quirk on EVERY sample

  Single-sample accuracy is the same in all three by construction.

     k             independent              correlated              systematic
          accuracy   agreement    accuracy   agreement    accuracy   agreement
     1       70.0%      100.0%       71.0%      100.0%       70.0%      100.0%
     3       87.5%       71.0%       77.0%       82.7%       70.0%      100.0%
     5       96.5%       69.3%       78.5%       82.6%       70.0%      100.0%
     9      100.0%       68.1%       74.5%       81.1%       70.0%      100.0%
    15      100.0%       68.3%       71.0%       80.3%       70.0%      100.0%
    25      100.0%       68.7%       72.5%       79.4%       70.0%      100.0%

  independent   accuracy  70.0% -> 100.0% (+30.0%)   agreement at k=25: 68.7%
  correlated    accuracy  71.0% ->  72.5% ( +1.5%)   agreement at k=25: 79.4%
  systematic    accuracy  70.0% ->  70.0% ( +0.0%)   agreement at k=25: 100.0%

  Same task, same single-sample accuracy, same 25x bill.
  Independent errors: +30.0%.  Systematic errors: +0.0%.

  And look at the agreement column in the systematic case: 100%.
  Every sample agreed. Perfect consensus, unchanged accuracy. If you
  had used agreement as a confidence signal -- and that is exactly
  what it is usually used for -- you would have been most confident
  precisely where voting had bought you nothing.

  The middle column is the realistic one. A 60% shared quirk is
  enough to cap accuracy at 72.5% no matter how many samples you buy:
  the quirk wins the vote whenever it fires.

  Self-consistency does not measure correctness. It measures
  REPRODUCIBILITY, and those coincide only when errors are
  independent -- which is an assumption about your model, not a
  property of the technique. Test it before you pay 9x for it.

  Note k=1: agreement is 100% by definition. A confidence score that
  reads 100% on a single sample is not measuring anything.

============================================================================
4. VERIFICATION: CHECKING THE ANSWER vs CHECKING THE WORKING
============================================================================
  Two cheap checks on the 12-step decomposed output:

    (a) plausibility  -- is the final answer in a sane range?
    (b) recomputation -- re-derive each step from the written value
        before it, and flag the first mismatch.

  1000 trials, 319 wrong answers (31.9%)

  check                               wrong answers caught
  (a) plausibility range                             9.4%
  (b) recompute the written steps                  100.0%

  The plausibility check is nearly useless here: a single corrupted
  digit usually lands inside any range you would have called sane.
  Recomputation finds the error because it checks the WORKING, and
  the working is only available because the prompt was decomposed.

  That is the real argument for decomposition, and it is not the one
  usually given: not that the model reasons better, but that it
  EMITS INTERMEDIATE VALUES YOUR CODE CAN CHECK.

============================================================================
5. WHAT EACH STRATEGY COSTS
============================================================================
  100,000 requests/month, $0.50/M in, $2.00/M out  [ILLUSTRATIVE]
  12-step problems.

  strategy                        accuracy   out tok    $/month   $ per point
  direct (answer only)               57.3%         8         $8          0.13
  decomposed (show steps)            68.1%       176        $41          0.60
  decomposed + recompute check       68.1%       176        $41          0.60
  self-consistency k=9 (indep.)      98.5%        72        $68          0.69
  self-consistency k=9 (system.)     59.0%        72        $68          1.16

  The recompute check is the same price as decomposing -- it runs in
  YOUR code, on tokens you were already paying for. It is the only
  row that adds reliability for nothing.

  The last two rows are the same technique at the same price. The
  only difference is a property of the MODEL -- whether its errors
  repeat. 98.5% against 59.0%, for an identical bill of
  9x. Nothing in the prompt tells you which row you are buying.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  SPECIFIED: one error mechanism -- a single corrupted decimal digit,
  at 4.5% per carried step and 3.0% per written step, and how strongly
  that slip repeats across samples (0%, 60%, 100%).

  NOT SPECIFIED, and therefore measured:
    * that the decomposition gain peaks in the middle of the range
    * that early errors are almost never survived
    * that majority voting reaches 100% under independent errors and
      moves accuracy not at all under systematic ones, at equal cost
    * that agreement is HIGHEST exactly where voting helps least
    * that a 60% shared quirk caps accuracy no matter how many
      samples are bought
    * that a plausibility check catches almost nothing

  WHAT IT CANNOT SHOW: whether a real model's stated reasoning is a
  faithful account of how it produced the answer. This mock's written
  steps ARE its computation, by construction. In a real model the
  chain-of-thought is generated text, and it can be a fluent
  after-the-fact story attached to an answer arrived at otherwise.
  Do not read this lab as evidence that reasoning traces are honest.
  Exercise 3 asks you to test that on a real model.

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Decomposition gain, 1 step | +0.0% |
| Decomposition gain, 20 steps | +15.4% |
| Chain lengths where decomposition flips an 80% usability bar | **none** |
| Trials with a corrupted intermediate (12 steps) | 320 / 1,000 |
| Those that recovered a correct final answer | **1** |
| Self-consistency k=25, independent errors | 70.0% → **100.0%** |
| Self-consistency k=25, 60% correlated | 71.0% → 72.5% |
| Self-consistency k=25, systematic | 70.0% → **70.0%**, agreement **100%** |
| Plausibility check, errors caught | 9.4% |
| Recomputation of working, errors caught | **100%** |
| Output tokens, direct vs decomposed | 8 vs 176 |

**Four things worth taking away.**

**1. The gain column is the wrong column.** Decomposition's benefit grows with chain length, reaching
+15.4 points at twenty steps — where it lifts a task from 40% to 56% and ships nothing. At an 80%
usability bar, *no* chain length changed verdict. **Set the bar first.**

**2. There is no self-correction.** 320 trials had a wrong intermediate; one recovered. Every later
step is computed competently from a wrong number. A check has to come from outside the chain.

**3. Self-consistency's benefit and its confidence signal move in opposite directions.** +30.0 points
at 68.7% agreement; +0.0 points at 100% agreement. The technique is sold on the first column and
monitored on the second. **Agreement measures reproducibility, and a reproduced error is still an
error.**

**4. The cheap control beat the expensive one.** Recomputing the written steps caught 100% of errors
for zero additional tokens, running in ordinary Python. Self-consistency at k=9 cost 9× and, under
correlated errors, bought 1.5 points. **The best thing decomposition buys is not better reasoning —
it is intermediate values your code can check.**

**What transfers:** the compounding arithmetic, the collapse of self-consistency under correlated
error, the uselessness of agreement as confidence, and the method of setting a bar before measuring.
**What does not:** every magnitude, and any implication that a model's stated reasoning is faithful —
which this lab explicitly cannot test.

---

## 8. Common mistakes and troubleshooting

1. **Expecting per-step accuracy to be task accuracy.** 0.95¹² = 54%.
2. **Adding "think step by step" and not reading the steps.** You paid output prices for text nothing
   parses.
3. **Trusting the model to catch its own earlier error.** Measured recovery rate: 0.3%.
4. **Reading a gain column without a usability bar.** +15.4 points, still unshippable.
5. **Treating agreement as confidence.** It reads 100% under systematic error, and 100% at k=1.
6. **Buying self-consistency without testing error independence.** 9× cost for +1.5 points if quirks
   are shared.
7. **Checking the answer instead of the working.** 9.4% vs 100%.
8. **Decomposing a one-step task.** Pure cost, measured gain of zero.
9. **Presenting chain of thought to users as an explanation.** It is generated text, not a record
   (§5.8).
10. **Prompting a reasoning model to reason.** Check your provider's guidance for that model.

| Symptom | Likely cause | Fix |
|---|---|---|
| "Usually right, occasionally very wrong" | A long chain; one slip is fatal | Shorten the chain; check intermediates |
| Different field wrong each time | Independent per-step errors | Per-field validation (§6) |
| The *same* field wrong every time | Systematic error | Self-consistency will not help; fix the prompt or the parse |
| Accuracy plateaus as k rises | Correlated errors | Stop paying for samples; find the shared quirk |
| High agreement, wrong answers | Reproducibility mistaken for correctness | Verify against an independent fact |
| Reasoning looks perfect, answer is wrong | Post-hoc rationalisation, or a slip mid-chain | Recompute the working in code |
| Cost tripled after adding CoT | Working is output tokens | Decide whether anything reads it |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** **Chain length is a reliability parameter.** Treat "how many steps must be right?"
  as a design number you own, alongside timeouts and retries (M2-L12).
- **Reliability.** Self-consistency's benefit is contingent on a property of your model that can change
  when the provider updates it. A technique whose value depends on an unmeasured assumption is a
  latent incident. Re-measure at every model change (M5-L17).
- **Cost.** Reasoning tokens are **output** tokens, at output prices — often 3–5× input. §7.3: 8
  tokens to 176. Self-consistency multiplies the whole bill by k.
- **Cost.** Bound k and chain length in code, not in the prompt. A retry loop around a k=9
  self-consistency call is a 9× multiplier on a multiplier (M2-L14).
- **Privacy.** Reasoning traces frequently restate the input in full, including personal data, and are
  often logged at a lower sensitivity than the request. **A trace log is a data store** (M2-L18).
- **Security.** Decomposition widens the injected-instruction surface: text asking the model to "revise
  step 3" is more likely to be honoured when the prompt has established that steps get revised
  (M5-L13).
- **Governance.** Do not present a chain of thought as the system's reason for a decision where a real
  explanation is required (M10-L07). It is not a record of the computation.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. A step is right 96% of the time. Give the task accuracy at 5, 10 and 25 steps.
2. Your task needs 90% end-to-end over 8 steps. What per-step accuracy does that require?
3. State two things decomposition gives you besides accuracy.
4. Why is agreement at k=1 always 100%, and what does that tell you about it as a confidence signal?
5. Give the one-line reason an early error is worse than a late one.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the chain length at which decomposed accuracy falls below 80%.
2. Change `SLIP_WRITTEN` to equal `SLIP_CARRIED` and re-run section 1. Explain the result.
3. Change the correlated regime from 0.60 to 0.35 and find the k at which accuracy stops improving.
4. Add a fourth check to section 4 — a parity or digit-sum check on the final answer — and report what
   fraction it catches.
5. Take the §6 invoice task, split it into two chains of six, and compute the expected fraction of
   invoices with at least one wrong field. Compare with twelve.

### Exercise 3 — Challenge (~50 min)

1. Build a step-level retry: when `check_working` flags step *i*, re-request **only** step *i* with the
   verified prefix. Measure accuracy and cost against full-output retry.
2. Construct a task where decomposition makes accuracy **worse**, and explain the mechanism.
3. On a real model with an API key you already have `[NOT EXECUTED — needs a key]`: give it a problem
   with an irrelevant hint that changes its answer, and check whether the stated reasoning mentions the
   hint. Report what that shows about faithfulness (§5.8).
4. Derive the k at which self-consistency's expected gain no longer covers its cost, given per-sample
   accuracy *p* and a correlation ρ.
5. Write the runbook entry for "accuracy fell after a model upgrade" that distinguishes a per-step
   accuracy change from a change in error correlation.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l04).)*

**Q1.** A model is right 95% of the time on each of 12 independent steps. Its end-to-end accuracy is
about:

- A. 95%, since each step is independent.
- B. 54%.
- C. 88%, because errors partially cancel.
- D. Not calculable without knowing the task.

**Q2.** In the lab, 320 of 1,000 trials had a corrupted intermediate value. How many produced a correct
final answer anyway?

- A. About a third, as later steps compensate.
- B. About half, since some errors cancel.
- C. One.
- D. None, which is guaranteed by the mechanism.

**Q3.** Self-consistency raises accuracy when:

- A. Sampling temperature is set to zero.
- B. The chain is longer than ten steps.
- C. k is an odd number, avoiding ties.
- D. Errors are independent across samples.

**Q4.** Under a systematic error, sampling 25 times and taking the majority produced:

- A. Accuracy unchanged and agreement of 100%.
- B. Accuracy improved by roughly 30 points.
- C. Accuracy unchanged and agreement near 70%.
- D. A tie that could not be resolved.

**Q5.** Which check caught the most wrong answers in the lab?

- A. Asking the model to double-check its answer.
- B. A plausibility range on the final answer.
- C. Sampling three times and comparing.
- D. Recomputing each written step in code.

**Q6.** Decomposition's measured gain was largest at 20 steps (+15.4 points). The correct reading is:

- A. Long chains are where decomposition should be applied.
- B. The gain is largest where both prompts still fail, so it changes no shipping decision.
- C. Decomposition scales linearly with chain length.
- D. Twenty steps is the optimal chain length for this task.

**Q7.** Chain-of-thought tokens are billed as:

- A. Input tokens, since they are part of the prompt.
- B. They are not billed; reasoning is free.
- C. Output tokens, typically the more expensive rate.
- D. A flat per-request reasoning surcharge.

**Q8.** A model gets the same field wrong on every invoice. Self-consistency at k=9 will:

- A. Fix it, because nine samples outvote one error.
- B. Fix it only if temperature is raised.
- C. Halve the error rate for 9× the cost.
- D. Not help, because the error is reproduced in every sample.

**Q9.** Agreement across samples is a poor confidence signal because:

- A. It reaches 100% both at k=1 and under systematic error, where it measures nothing useful.
- B. It is too expensive to compute at scale.
- C. Providers do not expose it through their APIs.
- D. It is only defined for multiple-choice tasks.

**Q10.** The most valuable thing a decomposed answer provides is:

- A. Intermediate values that deterministic code can verify.
- B. Evidence that the model reasoned rather than guessed.
- C. A faithful explanation to show to end users.
- D. A shorter, cheaper response.

**Q11.** A twelve-field extraction is wrong on 31% of documents, with a different field each time. The
highest-force fix is:

- A. Instruct the model to be careful and re-read the document.
- B. Upgrade to a larger model.
- C. Shorten the chain and validate each field in code.
- D. Sample five times and take the majority.

**Q12.** A model's chain of thought is best described as:

- A. A record of the computation that produced the answer.
- B. Generated text that may or may not reflect how the answer was produced.
- C. An audit log suitable for regulatory explanation.
- D. The model's internal activations rendered as words.

**Q13.** *(Written, rubric-graded.)* In under 150 words, a colleague reports that adding
self-consistency at k=5 raised their agreement metric from 71% to 94% and they are ready to ship.
State what you would ask for before agreeing, and why.

---

## 12. Revision notes

- **`p^n` is the whole lesson.** 0.95 per step over 12 steps is **54%**. The strongest lever is
  **shortening the chain**, not improving per-step accuracy.
- **Decomposition lowers the per-step error rate; it does not stop accumulation.** Measured gain grows
  with length: +0.0% at one step, +15.4% at twenty.
- **A gain is not an improvement unless it crosses a bar you set first.** At an 80% bar, *no* chain
  length changed verdict in the lab.
- **There is no self-correction.** 320 corrupted trials, **1** recovered. Every later step is computed
  competently from a wrong number.
- **Self-consistency depends on error independence** — an assumption about your model. Measured:
  **+30.0** points independent, **+1.5** at 60% correlation, **+0.0** systematic, all at the same 25×
  cost.
- **Agreement is highest where voting helps least** (68.7% / 79.4% / **100%** against +30.0 / +1.5 /
  +0.0). It is not a confidence signal. It reads 100% at k=1.
- **Check the working, not the answer**: 100% vs 9.4%. The check is ordinary code and costs nothing.
- **The real benefit of decomposition is machine-readable intermediates**, which is why it pairs with
  structured output (M5-L06) and validation (M5-L07).
- **Reasoning tokens are output tokens.** 8 → 176 in the lab; self-consistency multiplies by k.
- **A chain of thought is generated text, not a record.** Never present it as the reason for a decision
  (§5.8, M10-L07).
- **Past about five steps nothing here rescued the task.** That boundary is where Module 8 starts.

---

## 13. Completion checklist

- [ ] I can compute end-to-end accuracy from per-step accuracy and chain length.
- [ ] I set a usability bar before reading a gain column.
- [ ] I know that an early error is essentially never recovered.
- [ ] I test error independence before paying for self-consistency.
- [ ] I never use agreement as a confidence signal.
- [ ] I verify the working in code, not the answer by eye.
- [ ] I can say why a chain of thought is not an explanation.
- [ ] I scored 9/13 on the quiz.

---

## 14. References

- Wei et al. (2022), *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*.
  <https://arxiv.org/abs/2201.11903> `[UNVERIFIED]`
- Kojima et al. (2022), *Large Language Models are Zero-Shot Reasoners*.
  <https://arxiv.org/abs/2205.11916> `[UNVERIFIED]`
- Wang et al. (2022), *Self-Consistency Improves Chain of Thought Reasoning*.
  <https://arxiv.org/abs/2203.11171> `[UNVERIFIED]`
- Turpin et al. (2023), *Language Models Don't Always Say What They Think*.
  <https://arxiv.org/abs/2305.04388> `[UNVERIFIED]`
- Zhou et al. (2022), *Least-to-Most Prompting*. <https://arxiv.org/abs/2205.10625> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L05 — Delimiters and Handling Untrusted Content](M5-L05-delimiters.md)

You can make the model show its working. Next: what happens when the text you feed it contains
instructions of its own.
