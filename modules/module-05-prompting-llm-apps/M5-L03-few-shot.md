# M5-L03 — Zero-shot, Few-shot and Example Selection

| | |
|---|---|
| **Lesson ID** | M5-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M5-L01](M5-L01-prompt-anatomy.md), [M4-L16](../module-04-genai-llm-internals/M4-L16-knowledge-vs-context.md) |

---

## 1. Learning objectives

1. **Decide** when examples will help and when an instruction is enough.
2. **Choose** how many examples to include, from measured diminishing returns.
3. **Select** examples deliberately rather than by convenience.
4. **Recognise** the biases examples introduce — order, label distribution, format.
5. **Cost** a few-shot prompt and judge whether it earns its tokens.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Zero-shot** | No examples; instruction only. |
| **Few-shot** | A handful of input-output examples in the prompt. |
| **Shot** | One example. |
| **In-context learning** | Adapting from prompt examples without weight changes (M4-L16). |
| **Demonstration** | Another word for an example. |
| **Static examples** | The same set on every request. |
| **Dynamic selection** | Examples retrieved per request based on the input. |
| **Recency bias** | Later examples influencing the output more than earlier ones. |
| **Majority-label bias** | Predicting whichever label appears most in the examples. |
| **Format lock-in** | The model copying an example's format, including its mistakes. |

---

## 3. Plain-language explanation

### 3.1 What examples do that instructions cannot

An instruction says what to do. **An example shows what "done" looks like.**

Some things are far cheaper to demonstrate than to describe:

| Hard to instruct | Easy to demonstrate |
|---|---|
| The exact tone for an apology | Two apologies |
| How terse is terse enough | Three outputs of the right length |
| Which edge cases map to which label | Three borderline examples, labelled |
| An unusual output format | One correctly formatted output |

**The rule: if you find yourself writing a paragraph to describe a style, show two examples instead.**

### 3.2 When examples do *not* help

**Examples are the most expensive component per unit of benefit** (M5-L01 §9), and there are cases
where they buy nothing:

| Situation | Why examples do not help |
|---|---|
| The task is already unambiguous | The instruction has done the work |
| A schema constrains the output | The format is enforced, not suggested (M5-L06) |
| The examples are unrepresentative | You teach the wrong pattern |
| The model already does it correctly | You are paying for tokens that change nothing |

**Always measure zero-shot first.** It is free, and it is the baseline every few-shot prompt must beat
(M1-L11, M3-L14 §5.6). §7.3 measures a case where four examples buy nothing at all.

### 3.3 What examples teach that you did not intend

This is the part people are surprised by. Examples carry information beyond the mapping you meant:

- **The label distribution.** Four `billing` examples and one `technical` teaches the model that
  `billing` is likely.
- **The order.** Later examples weigh more than earlier ones.
- **The format, including errors.** A typo in an example is a demonstrated pattern.
- **The difficulty.** All-easy examples suggest the task is easy.

**§7.3 measures all four.** The label-distribution effect is the largest and the most commonly
overlooked.

---

## 4. Analogy

**Showing a new colleague three finished pieces of work rather than writing a style guide.** Faster,
clearer, and they will copy everything about them — including the parts you did not intend as
instruction.

### Where the analogy breaks

1. **A colleague asks which parts to copy.** The model copies everything, including a typo.
2. **A colleague notices when three examples are all of one kind.** The model treats that frequency as
   information about what is likely.
3. **Showing work costs you nothing per repetition.** Examples are billed on **every** request.
4. **A colleague generalises from principle.** The model generalises by similarity, so unrepresentative
   examples mislead in a specific and predictable way.

---

## 5. Detailed technical explanation

### 5.1 How many — and why the usual answer is the wrong shape

The advice you will read everywhere is *most of the benefit arrives in the first 2–4 examples, with
diminishing returns after*. The second half of that is right. **The first half is wrong in a way that
matters**, and §7.3 measures it.

Here is the curve people draw:

```
quality
  │        ╭────────────────────  ← flat
  │      ╭─╯
  │    ╭─╯
  │  ╭─╯
  │╭─╯
  └──┬──┬──┬──┬──┬──┬──▶ examples
     0  2  4  8  16 32
```

Here is the curve the lab actually produced, on a four-label classification task:

```
quality
  │              ╭──────────────  ← flat from ~8
  │           ╭──╯
  │        ╭──╯
  │ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ← zero-shot baseline (74.6%)
  │╲       │
  │ ╲──╮ ╭─╯
  │     ╰─╯   ← 1 and 2 examples are WORSE than none
  └──┬──┬──┬──┬──┬──┬──▶ examples
     0  1  2  4  8  16 32
```

**One and two examples scored below zero-shot** — 67.7% and 65.1% against 74.6%. Adding correct,
well-formed, correctly-labelled information made the system worse.

**The tempting conclusion is "few-shot needs a minimum count".** That conclusion is wrong, and the lab
tests it rather than asserting it. Holding the count fixed at four and varying only how many *labels*
appear:

| 4 examples drawn from | Accuracy |
|---|---|
| 1 label | 63.8% |
| 2 labels | 65.3% |
| 4 labels | **77.7%** |

Same count. Same tokens. **The dip was never about the count — it was that an example set missing a
label argues against that label.** One example of one class is not a weak version of few-shot; it is a
biased prior, and a confident one.

> **The rule this yields: show every label you want predicted, or show none at all.**
> A partial example set is worse than an empty one.

Past full coverage, the familiar shape returns: 4 → 8 gains 4.7 points, 8 → 32 gains 1.5 for four times
the tokens. **Cost is linear while benefit is not**, and §7.3 prices exactly where that stops paying.

`[UNVERIFIED as a general law — measured on a synthetic four-label task with a mock provider. The
coverage mechanism should generalise to any classification with a closed label set; the magnitudes
will not.]`

**Start at zero. Add examples in complete sets. Keep them only while they measurably help.**

### 5.2 Which ones

| Strategy | How | When |
|---|---|---|
| **Convenience** | The first ones to hand | Never, deliberately |
| **Representative** | Sampled to match the real distribution | A sensible default |
| **Edge cases** | The hard and ambiguous ones | When errors cluster there |
| **Diverse** | Deliberately spread across the input space | Broad tasks — *see the warning below* |
| **Dynamic** | Retrieved per request by similarity (M6) | Large, varied inputs |

**A warning about "diverse", found the hard way in §7.3.** Implemented as greedy maximum spread —
repeatedly take the point furthest from everything chosen so far — it scored **70.3%, below
zero-shot's 74.6%**, while a balanced representative set scored 83.6%. Greedy max-spread is an outlier
detector wearing a virtuous name: the points furthest from everything else are the least typical ones
you own. **Diversity is a property worth having only after representativeness.**

**Dynamic selection is usually the strongest and the most machinery.** It is retrieval applied to
examples rather than documents, and everything in Module 7 applies — including that a bad retriever
makes it worse than static examples.

### 5.3 The biases, precisely

**Majority-label bias.** If your examples are 4 `billing` and 1 `technical`, the model shifts toward
`billing` on ambiguous inputs. **Balance your example labels unless the true distribution is
deliberately being conveyed** — and if it is, say so in the instruction rather than leaving the model
to infer it.

**Recency bias.** The last example influences most. §7.3 measures this across all 24 orderings of one
four-example set: **whichever label sits last is over-predicted, by +5.5 to +14.7 points**, and
accuracy across those orderings spans 68.5% to 82.6%. **A 14-point spread from reordering four
examples you already decided to use** — same count, same tokens, same content.

**Put the most representative example last**, and do not put your one weird edge case there.

Note also *how* that was measured. A single forward-vs-reversed A/B — the comparison almost everyone
runs — reported a 10.1-point difference, and would have left you with a fact about one permutation
instead of a rule about position. **Two orderings cannot establish an effect of ordering.**

**Format lock-in.** The model reproduces surface features: quoting style, key order, whitespace,
capitalisation. **Every example must be exactly the output you want**, because it is a specification,
not an illustration.

**Difficulty signalling.** All-easy examples make the model over-confident on hard inputs. Include at
least one genuinely hard case *if* your traffic contains them.

### 5.4 Format

As alternating user/assistant turns (M5-L02 §5.4), or inline in one message:

```
<example>
  <input>My card was charged twice for GB-4471.</input>
  <output>{"category": "billing", "order_id": "GB-4471"}</output>
</example>
```

**Both work. Be consistent**, and use the same delimiters for examples as for the real input, so the
model sees one pattern rather than two.

### 5.5 Cost

```
cost_per_request = (instruction + n_examples × example_size + input) × price
```

**Examples are billed on every request forever.** Ten examples of 60 tokens is 600 tokens — at 100,000
requests a month, **60 million tokens** for a component that may have stopped helping after the third.

**Two mitigations:** put examples in the cacheable prefix (M5-L16), and **measure whether each one
still earns its place** (M5-L18).

### 5.6 Examples versus fine-tuning

| | Few-shot | Fine-tuning |
|---|---|---|
| Cost to set up | Minutes | Hours to days |
| Cost per request | **Tokens, forever** | Zero extra |
| Examples needed | 2–10 | Hundreds to thousands |
| Change it | Edit the prompt | Retrain |
| Break-even | — | High volume, stable task |

**At high, stable volume, fine-tuning is the cheaper way to buy the same behaviour** — because the
examples stop being billed. M13-L02 covers the crossover.

### 5.7 Assumptions and limitations

- The 2–4 example guidance is a common finding, not a law — and §7.3 found a task where the first two
  examples were actively harmful. Measure on your task.
- The coverage rule is derived from a closed-label classification task. For open-ended generation
  there is no label set to cover, and the failure mode is different.
- Bias magnitudes vary by model, version and task. The *directions* are stable; the numbers are not.
- The lab's provider is a mock (§7.3). It can demonstrate coverage, majority-label, recency and
  difficulty effects because they follow from its structure. **It cannot demonstrate format lock-in at
  all**, and the lab says so rather than staging it.
- §7.3's lab uses a mock provider that models these effects; it demonstrates the *shape*, not any real
  model's magnitudes.

---

## 6. Worked example — four examples that make things worse

**The task:** classify tickets as `billing`, `technical`, `account` or `other`.

**The examples, chosen by convenience — the four most recent tickets:**

```
"Charged twice for GB-4471"        → billing
"My invoice is wrong"              → billing
"Refund not received"              → billing
"I was double-billed in March"     → billing
```

**Every problem in §5.3 at once:**

| Problem | What it teaches |
|---|---|
| **All one label** | `billing` is the answer |
| **All easy** | The task is easy; be confident |
| **No edge cases** | Ambiguity does not arise |
| **Convenience-sampled** | Recent traffic ≠ the real distribution |

**The measured result** (§7.3, four examples chosen by convenience): **57.9% against zero-shot's
74.6% — 16.6 points worse than sending no examples at all.** The set pushes predicted `billing` to
56.5% when its true rate is 22.5%.

**Four examples made it substantially worse than none**, and they cost 240 extra tokens on every
request forever to do it.

**And here is the trap.** You will not notice, because you will test it on tickets like the examples —
and on those, it looks excellent.

### The fix

```
"Charged twice for GB-4471"           → billing
"The reports page crashes on load"    → technical
"I cannot reset my password"          → account
"Do you have a phone number?"         → other
"I can't log in to check my invoice"  → technical      ← the hard one, last
```

**Balanced across labels. One genuinely ambiguous case. The most representative example last.**

**Now the question §7.3 actually answers:** does this fixed set beat *zero-shot*?

| Prompt | Accuracy | 95% interval |
|---|---|---|
| Zero-shot | 74.6% | 72.5% – 76.5% |
| Convenience 4-shot | 57.9% | 55.6% – 60.2% |
| Fixed, balanced 4-shot | **79.9%** | 78.0% – 81.7% |

Here the answer is yes: **+5.3 points over zero-shot, intervals not overlapping.** The examples earn
their tokens.

**But look at which number you would have reported.** Convenience → fixed is **+21.9 points** — a
spectacular result, easy to write up, and it measures almost entirely the damage you did to yourself.
The number that decides whether to keep the examples at all is the +5.3, and it is a quarter the size.

**A prompt change that undoes damage you caused is not an improvement over never having caused it.**
Had the +5.3 come out inside the noise, the correct decision would have been to delete all four
examples and keep the tokens — while the +21.9 sat there looking like a triumph.

---

## 7. Practical activity

**File:** [`labs/m5/l03_few_shot.py`](../../labs/m5/l03_few_shot.py)

**No API key, no network, no cost.** Deterministic (`zlib.crc32`, never Python's `hash()`, which is
randomised per process). Runs in about 11 seconds.

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l03_few_shot.py
```

Six sections: the example-count curve and why the obvious version of that experiment is wrong; cost per
unit of quality; the four unintended lessons; five selection strategies at identical token cost; the
zero-shot comparison from §6; and a statement of what the mock cannot show.

**Two of the six exist to demonstrate that an experiment was badly designed** rather than to report a
result. That is deliberate. Most published few-shot comparisons have one of these two flaws.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.12.3, NumPy 2.5.3.

```text
============================================================================
1. HOW MANY EXAMPLES? -- AND WHY THE OBVIOUS EXPERIMENT IS WRONG
============================================================================
  600 test tickets x 3 runs = 1800 predictions per cell

  THE NAIVE EXPERIMENT: draw a fresh example set for each count.

    examples   accuracy   vs zero-shot
           0      74.6%          +0.0%
           1      68.7%          -5.8%
           2      61.7%         -12.9%
           4      78.3%          +3.8%
           8      78.3%          +3.7%
          16      80.6%          +6.1%
          32      85.0%         +10.4%

  That curve is not monotone -- 2 examples scored WORSE than 1 (61.7% vs 68.7%).
  Read as a dose-response curve it is nonsense, and it would be
  tempting to conclude 'few-shot is unpredictable'.

  The experiment is at fault. Each row drew a DIFFERENT example set,
  so every row differs in two ways at once: how many examples, and
  WHICH ones. The design cannot separate them.

  THE CORRECTED EXPERIMENT: nested sets (each larger set CONTAINS the
  smaller one), repeated over several independent draws.

    examples  labels shown   mean acc   sd across draws      min      max   vs zero-shot
           0             0      74.6%              0.0%    74.6%    74.6%          +0.0%
           1             1      67.7%              1.8%    64.5%    70.4%          -6.9%
           2             2      65.1%              4.1%    54.3%    67.4%          -9.5%
           4             4      80.5%              2.1%    76.2%    83.3%          +5.9%
           8             4      85.2%              1.0%    83.7%    86.7%         +10.6%
          16             4      85.8%              0.9%    84.2%    86.8%         +11.2%
          32             4      86.7%              0.6%    85.6%    87.5%         +12.2%

  mean sd BETWEEN draws at a fixed count : 1.8%
  effect of going from 1 to 32 examples  : +19.1%
  ratio                                  : 10.9x

  the count effect is larger than the between-draw noise, so a dose-response reading is defensible here.

  This is why few-shot experiments report contradictory results. Run
  one set at each count and you are measuring your draw, not the count.
  Report mean and spread over several draws, or report nothing.

  AND NOTE THE DIP: at 1, 2 example(s) the
  prompt is WORSE than no examples at all. Adding information made
  the system worse. The obvious reading is 'few-shot needs a minimum
  count'. Test that before believing it.

  Holding the COUNT at 4 and varying only how many LABELS appear:

  4 examples drawn from        accuracy       95% interval
  1 label(s)                      63.8%      61.6% - 66.0%
  2 label(s)                      65.3%      63.0% - 67.4%
  4 label(s)                      77.7%      75.7% - 79.6%

  Same count, same tokens. The dip is not about HOW MANY examples
  you show -- it is that an example set missing a label argues
  against that label. One example of one class is not a weak
  version of few-shot; it is a biased prior.

  Rule: show every label you want predicted, or show none.

============================================================================
2. COST PER UNIT OF QUALITY
============================================================================
  instruction 80 tokens, 60 tokens/example,
  100,000 requests/month at $0.50/M [ILLUSTRATIVE]

    examples   accuracy   tokens/req    $/month   $ per accuracy point
           0      74.6%           80         $4                  0.05
           1      67.7%          140         $7                  0.10
           2      65.1%          200        $10                  0.15
           4      80.5%          320        $16                  0.20
           8      85.2%          560        $28                  0.33
          16      85.8%        1,040        $52                  0.61
          32      86.7%        2,000       $100                  1.15

  Cost per accuracy point is lowest at 0 examples.
  Beyond that you pay linearly for a curve that has flattened -- the
  asymmetry the lesson's diagram shows, priced.

============================================================================
3. THE FOUR THINGS EXAMPLES TEACH THAT YOU DID NOT INTEND
============================================================================
  (a) MAJORITY-LABEL BIAS -- the largest and least noticed

  true proportion of 'billing' in the test set: 22.5%

  example split               predicted billing   over-prediction   accuracy
  4 billing, 0 others                     56.5%            +34.0%      59.9%
  3 billing, 1 other                      47.7%            +25.2%      65.7%
  2 billing, 2 others                     37.7%            +15.2%      70.5%
  balanced 1 each                         20.9%             -1.6%      83.6%

  Four all-billing examples push predicted 'billing' well above its
  true rate. This is section 6's convenience-sampled set, measured.

  (b) RECENCY BIAS -- what one A/B comparison cannot see

  THE ONE-COMPARISON VERSION: forward vs reversed.

  ordering                   accuracy       95% interval    last example
  as selected                   80.8%      78.9% - 82.5%           other
  reversed                      70.7%      68.6% - 72.8%         billing

  difference 10.1%, interval half-width 1.8%
  So order matters -- but this comparison does not say WHY, and it
  cannot tell you whether you got lucky. Reversal is one of 24
  orderings, and you have measured two of them.

  ALL 24 ORDERINGS of the same four examples:

  accuracy across orderings: min 68.5%, max 82.6%, spread 14.1%
  the single forward/reversed pair reported 10.1% of that 14.1%
  (same examples, same count, same tokens -- only the order changed)

  label placed LAST          its predicted rate   its true rate     lift
  billing                                 32.4%           22.5%    +9.9%
  technical                               37.7%           23.0%   +14.7%
  account                                 38.3%           28.8%    +9.5%
  other                                   31.2%           25.7%    +5.5%

  Every label is over-predicted when it sits last (lift +5.5% to +14.7%).
  THAT is the mechanism, and the two-ordering test could not have
  found it -- it would have told you 'reversing helped' and left you
  with a fact about one permutation instead of a rule about position.

  (c) DIFFICULTY SIGNALLING -- all-easy examples

  test set: 415 clear-cut, 185 ambiguous

  example difficulty          acc: clear-cut tests  acc: AMBIGUOUS tests     gap
  all clear-cut examples                     92.3%                 62.7%  +29.6%
  all ambiguous examples                     54.0%                 48.1%   +5.9%
  mixed (any)                                79.8%                 60.9%  +18.9%

  Every row is worse on the ambiguous half -- and a test set built the
  same way as the examples reports only the left-hand column.

  (d) FORMAT LOCK-IN is not modelled here.
      This mock predicts a LABEL, so it cannot demonstrate a typo being
      copied into an output string. That effect is real and widely
      reported; exercise 2.4 asks you to measure it on a real model.
      A lab should say what it does not show.

============================================================================
4. FIVE SELECTION STRATEGIES AT IDENTICAL COST
============================================================================
  all at 4 examples, so token cost is identical

  strategy                     accuracy      95% interval   vs zero-shot
  zero-shot (no examples)         74.6%     72.5% - 76.5%          +0.0%                     -
  convenience (first 4)           57.9%     55.6% - 60.2%         -16.6%                 WORSE
  balanced, clear-cut             83.6%     81.8% - 85.2%          +9.1%                better
  balanced, any difficulty        79.9%     78.0% - 81.7%          +5.3%                better
  balanced, ambiguous only        63.7%     61.4% - 65.9%         -10.9%                 WORSE
  diverse (max spread)            70.3%     68.2% - 72.4%          -4.2%                 WORSE

  Every row above costs the SAME 4 examples = 240 tokens. The spread
  between the best and worst four-example strategy is 25.7%.
  Selection is free; it is the largest lever on this page.

  Note the last row. 'Diverse' sounds like a virtue, but greedy
  max-spread selects the points FURTHEST from everything else -- it
  is an outlier detector wearing a nice word. Representative beats
  diverse when the examples are meant to show the typical case.

============================================================================
5. THE QUESTION SECTION 6 ACTUALLY ASKS
============================================================================
  prompt                       accuracy      95% interval
  zero-shot                       74.6%     72.5% - 76.5%
  convenience 4-shot              57.9%     55.6% - 60.2%
  fixed (balanced set)            79.9%     78.0% - 81.7%

  Does the FIXED set beat ZERO-SHOT?  YES -- it beats zero-shot, distinguishably
  (+5.3%; intervals do not overlap)

  And the repair everyone celebrates -- convenience -> fixed -- is
  +21.9%. It is easy to report that number, feel
  finished, and never check the row above it.

  That is the question worth asking, and it is not the same as
  'is the fixed set better than the broken one?'. Balancing removed
  harm. Whether it added BENEFIT over never having used examples is a
  separate measurement, and the two are constantly confused.

  If the answer is 'not distinguishable', the honest conclusion is to
  drop the examples and keep the tokens.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  The provider is a MOCK: similarity-weighted voting over the examples
  plus an instruction prior. It reproduces majority-label bias, recency
  bias and difficulty signalling because those follow from that
  structure -- not because a real model was measured.

  What transfers:
    * the SHAPE (diminishing returns; linear cost)
    * the METHOD (always measure zero-shot; report intervals)
    * the RANKING of selection strategies

  What does NOT transfer:
    * the magnitudes
    * format lock-in, which this mock cannot exhibit at all

  Measure on the model you deploy (M5-L18).

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Zero-shot baseline | 74.6% |
| 1 example | **67.7% — below baseline** |
| 2 examples | **65.1% — below baseline** |
| 4 examples (all labels covered) | 80.5% |
| 8 examples | 85.2% |
| 32 examples | 86.7% for 25× the example tokens |
| 4 examples, 1 label vs 4 labels | 63.8% vs 77.7% — **the dip is coverage, not count** |
| Between-draw sd at a fixed count | 1.8 points |
| Accuracy spread across 24 orderings | **14.1 points** |
| Over-prediction of whichever label is last | +5.5 to +14.7 points |
| Convenience 4-shot vs zero-shot | −16.6 points |
| Best vs worst 4-example strategy | **25.7 points, at identical cost** |
| Clear-cut vs ambiguous test accuracy | 92.3% vs 62.7% from all-easy examples |

**Four things worth taking away.**

**1. The naive experiment produced nonsense, and it was the design's fault.** Drawing a fresh example
set at each count gave 68.7% at one example and 61.7% at two — non-monotone, unusable. Every row
differed in two ways at once: how many examples, and which ones. The fix is nested sets — each larger
set *contains* the smaller — repeated over eight independent draws, so only the count varies. The
between-draw sd is 1.8 points, which is why one run per count tells you about your draw rather than
about the count.

**2. More information made the system worse, and the obvious explanation was wrong.** One and two
examples scored below zero-shot. "Few-shot needs a minimum count" is the natural reading; the
count-controlled test rejects it. **An example set missing a label argues against that label.**

**3. Selection is free and dominates.** Every strategy in section 4 costs the same 240 tokens. They
span 25.7 points. The word "diverse" scored *below zero-shot* — greedy max-spread selects the least
typical points you own.

**4. The lab reports what it cannot show.** The provider is a mock: similarity-weighted voting plus an
instruction prior. Coverage, majority-label, recency and difficulty effects follow from that structure,
so it reproduces them. **Format lock-in it cannot exhibit at all** — the mock returns a label, not a
string — and section 3(d) says so instead of staging a demonstration. Exercise 2 measures that one on a
real model.

**What transfers:** the shape, the method (always measure zero-shot; report intervals; control the
confound), and the ranking of strategies. **What does not:** every magnitude on this page.

---

## 8. Common mistakes and troubleshooting

1. **Not measuring zero-shot first.** It is the baseline the examples must beat.
2. **Convenience-sampling examples.** The commonest cause of harmful few-shot prompts.
3. **Unbalanced labels.** The largest and least-noticed bias.
   **3b. Incomplete labels — worse still.** An example set that never shows a label argues against it.
   §7.3 measured 63.8% vs 77.7% at identical count. **Show every label or show none.**
4. **A typo in an example.** It is now a specification.
5. **Putting the weird edge case last.** Recency bias amplifies it.
6. **Adding examples indefinitely.** Cost is linear; benefit is not.
7. **Testing on inputs like the examples.** Guarantees a flattering result.
8. **Using examples where a schema would do.** Constraint beats suggestion (M5-L06).
9. **Comparing counts with independently drawn sets.** Each count then differs in two ways at once.
   Use nested sets, repeated over several draws (§7.3).
10. **Concluding an ordering effect from two orderings.** Forward-vs-reversed is two of 24; it reported
    10.1 points of a 14.1-point spread and named no mechanism.
11. **Reaching for "diverse" as an obvious good.** Greedy max-spread picks outliers and scored *below*
    zero-shot. Representative first, diverse second.

| Symptom | Likely cause | Fix |
|---|---|---|
| One label over-predicted | Majority-label bias | Balance the examples |
| Output copies an example's quirk | Format lock-in | Make every example exactly right |
| Few-shot worse than zero-shot | Unrepresentative examples | Rebalance; re-measure against zero-shot |
| Few-shot worse than zero-shot at 1–2 examples | A label is missing from the set | Cover every label, or use none |
| Results change when you re-pick examples | Selection variance, not a real effect | Repeat over several draws; report the sd |
| Quality flat past a few examples | Diminishing returns | Cut back and re-measure |
| Costs high for a simple task | Too many examples | Measure cost per unit of quality |
| Good in testing, poor in production | Tested on example-like inputs | Build a real eval set (M5-L18) |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** **Examples frequently come from real data.** A support ticket used as an example is a
  customer's text sent on every request thereafter. Synthesise or redact examples; never paste
  production records into a prompt without checking you may.
- **Privacy.** Examples in a system prompt are stored in your repository. Treat them as data subject to
  retention and deletion, not as configuration.
- **Cost.** Examples are billed on every request, forever. Ten 60-token examples at 100,000 requests a
  month is **60M tokens**. Put them in the cacheable prefix (M5-L16).
- **Security.** If examples are selected dynamically from user-supplied content, that content enters
  your prompt — it is an injection vector (M5-L13).
- **Reliability.** Examples are part of the prompt and therefore part of what you version and test
  (M5-L12). Changing one is a behaviour change.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Give two things examples specify better than instructions.
2. Name the four biases examples introduce.
3. Why must zero-shot be measured first?
4. What is wrong with the four convenience-sampled examples in §6?
5. Ten 50-token examples at 200,000 requests a month — how many tokens?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab. Report where cost per unit of quality bottoms out.
2. Measure majority-label bias: run 4:0, 3:1 and 2:2 label splits and report the shift.
3. Demonstrate recency bias by swapping the first and last examples.
4. Introduce a typo into one example and measure how often it is reproduced.
5. Compare convenience, balanced, edge-case and diverse selection on the same inputs.

### Exercise 3 — Challenge (~45 min)

1. Build a dynamic selector that picks examples by similarity to the input, and compare it with the
   best static set at matched token cost.
2. Find the example count at which quality stops improving *on your own task*, with uncertainty.
3. Construct a case where few-shot is measurably worse than zero-shot, and explain why.
4. Compute the volume at which fine-tuning becomes cheaper than the token cost of your examples.
5. Write the review checklist for adding an example to a production prompt.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l03).)*

**Q1.** Examples are most useful when:

- A. The task instruction is already precise and unambiguous.
- B. Style or edge-case handling is hard to describe in words.
- C. A JSON schema already constrains the output format.
- D. You need to reduce the prompt's total token count.

**Q2.** Before adding examples you should always:

- A. Measure zero-shot performance as a baseline.
- B. Increase the sampling temperature to encourage variety.
- C. Collect at least thirty examples for coverage.
- D. Switch to a larger model to establish the ceiling.

**Q3.** Four examples all labelled `billing` will:

- A. Improve accuracy on billing tickets without other effects.
- B. Have no effect, since the model reads the instruction.
- C. Cause the model to refuse to use any other label.
- D. Shift predictions toward `billing` on ambiguous inputs.

**Q4.** Where should the most representative example go?

- A. First, to establish the pattern before the others.
- B. In the middle, balanced among the other examples.
- C. Last, because later examples influence output most.
- D. Position has no measurable effect on the outcome.

**Q5.** A typo in an example is:

- A. A demonstrated pattern the model may reproduce.
- B. Ignored, since the model corrects obvious errors.
- C. Only a problem if it appears in the final example.
- D. Automatically flagged by the provider's validation.

**Q6.** On the four-label task in §7.3, one and two examples scored *below* zero-shot. The
count-controlled follow-up showed the cause was:

- A. Too few examples for in-context learning to engage at all.
- B. An example set that omitted labels, biasing the model against them.
- C. Random variation between runs of the same prompt.
- D. The examples being longer than the instruction they followed.

**Q7.** Compared with instructions, examples are:

- A. Cheaper per request, since they replace instructions.
- B. Free, because they are part of the cached prefix.
- C. Billed once when the conversation is first created.
- D. The most expensive component per unit of benefit.

**Q8.** Fine-tuning becomes cheaper than few-shot when:

- A. The task changes frequently and needs rapid iteration.
- B. Fewer than ten examples are needed for the task.
- C. Volume is high and the task is stable.
- D. The examples contain personal data requiring protection.

**Q9.** In §6, the four convenience-sampled examples made the model:

- A. Worse than zero-shot on non-billing tickets.
- B. More accurate overall, because recent data is relevant.
- C. Identical to zero-shot, since the instruction dominated.
- D. Refuse to classify tickets outside the examples' labels.

**Q10.** Using a real customer ticket as a prompt example means:

- A. Nothing, as prompts are not stored by the provider.
- B. It is covered by the provider's data-processing terms.
- C. It is anonymised automatically by the tokenizer.
- D. That customer's text is sent on every request thereafter.

**Q11.** You compare 1, 2, 4 and 8 examples, drawing a fresh set for each count, and the accuracies
come out non-monotone. The correct conclusion is:

- A. Few-shot learning is inherently unstable and cannot be tuned.
- B. The design confounds count with selection; use nested sets over several draws.
- C. The test set is too small and should be enlarged.
- D. The lowest-scoring count should be discarded as an outlier.

**Q12.** Five selection strategies are compared at four examples each. Which statement about their
token cost is correct?

- A. They cost the same; selection changes quality at identical cost.
- B. Balanced selection costs least, since it needs fewer examples.
- C. Diverse selection costs most, since spread examples are longer.
- D. Cost cannot be compared without knowing the model's price.

**Q13.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why their new five-shot
prompt scores better in testing but performs worse in production than the zero-shot version it
replaced.

---

## 12. Revision notes

- **Examples specify what instructions cannot** — tone, terseness, edge-case mapping, unusual formats.
  **If you are writing a paragraph to describe a style, show two examples instead.**
- **Always measure zero-shot first.** It is free and it is the baseline (M3-L14 §5.6).
- **Examples teach four things you did not intend:** the **label distribution** (largest and least
  noticed), the **order** (later weighs more), the **format including typos**, and the **difficulty**.
- **Cover every label, or use no examples.** A partial set argues against the labels it omits — §7.3
  measured 1 and 2 examples scoring *below zero-shot*, and 63.8% vs 77.7% at a fixed count of four.
  **A partial example set is worse than an empty one.**
- **Past full coverage, benefit flattens fast** — 4→8 gained 4.7 points, 8→32 gained 1.5 for 4× the
  tokens. Cost is **linear**; benefit is not.
- **Selection is free and dominates.** Five strategies at 240 tokens each spanned **25.7 points**.
  "Diverse" implemented as max-spread scored *below zero-shot* — it selects outliers.
- **Ordering alone moved accuracy 14.1 points** across the 24 orderings of one four-example set.
- **Never convenience-sample.** Balance the labels, include a genuinely hard case, and put the most
  representative example **last**.
- **Every example is a specification, not an illustration.** A typo is a demonstrated pattern.
- **Examples are billed on every request, forever** — ten 60-token examples at 100k requests/month is
  **60M tokens**. Cache the prefix (M5-L16), and re-measure whether each still earns its place.
- **At high, stable volume, fine-tuning buys the same behaviour without the per-request tokens**
  (M13-L02).
- **Examples are often real customer data.** Synthesise or redact them.
- **Undoing harm you caused is not the same as adding benefit.** A rebalanced example set must still
  beat zero-shot to justify its tokens. In §6 the repair was +21.9 points; the number that actually
  decides the question was +5.3.
- **Two experimental designs in this lesson were wrong before they were right.** Independently drawn
  sets confound count with selection; two orderings cannot establish an ordering effect. **When a
  prompting result surprises you, suspect the experiment before the model.**

---

## 13. Completion checklist

- [ ] I measure zero-shot before adding any examples.
- [ ] I can name the four unintended things examples teach.
- [ ] I balance example labels and put the most representative one last.
- [ ] I treat every example as a specification, typos included.
- [ ] I can compute what my examples cost per month.
- [ ] I know when fine-tuning replaces few-shot on cost.
- [ ] I cover every label in an example set, or use none.
- [ ] I can design a count comparison that does not confound count with selection.
- [ ] I scored 9/13 on the quiz.

---

## 14. References

- Brown et al. (2020), *Language Models are Few-Shot Learners*.
  <https://arxiv.org/abs/2005.14165> `[UNVERIFIED]`
- Zhao et al. (2021), *Calibrate Before Use: Improving Few-Shot Performance*.
  <https://arxiv.org/abs/2102.09690> `[UNVERIFIED]`
- Lu et al. (2021), *Fantastically Ordered Prompts and Where to Find Them*.
  <https://arxiv.org/abs/2104.08786> `[UNVERIFIED]`
- Liu et al. (2021), *What Makes Good In-Context Examples for GPT-3?*
  <https://arxiv.org/abs/2101.06804> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L04 — Task Decomposition and Reasoning Prompts](M5-L04-decomposition.md)

You can show the model what good looks like. Next: breaking a task into steps the model can actually
do, and what "let's think step by step" does and does not buy.
