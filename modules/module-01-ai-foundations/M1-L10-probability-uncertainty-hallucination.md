# M1-L10 — Probabilistic Behaviour, Uncertainty and Hallucination

| | |
|---|---|
| **Lesson ID** | M1-L10 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M1-L07](M1-L07-learning-paradigms.md) |

---

## 1. Learning objectives

1. **Explain** why the same input can produce different outputs, and **name** the two distinct
   sources of that variation.
2. **Define** hallucination precisely and **trace** it back to the training objective.
3. **Distinguish** a model's *confidence* from its *accuracy*, and **define** calibration.
4. **Interpret** a reliability diagram and **state** whether a system is over- or under-confident.
5. **List** the practical mitigations for unsupported output and **state** what each does and does
   not fix.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Deterministic** | Same input always produces the same output. |
| **Stochastic** | Involving randomness; repeated runs may differ. |
| **Probability distribution** | An assignment of probabilities to possible outcomes, summing to 1. |
| **Sampling** | Choosing an outcome at random according to a distribution. |
| **Temperature** | A setting that flattens or sharpens the distribution before sampling. Detail in M4-L14. |
| **Greedy decoding** | Always choosing the highest-probability option. Deterministic given the same input. |
| **Confidence** | The probability a model assigns to its own output. |
| **Calibration** | The property that among predictions made with confidence *p*, about *p* of them are correct. |
| **Overconfident** | Stated confidence exceeds actual accuracy. |
| **Reliability diagram** | A plot of stated confidence against observed accuracy. |
| **Hallucination** | Fluent, confident output that is unsupported by any source and often false. |
| **Groundedness** | The property that every claim is supported by provided evidence. |
| **Abstention** | The system declining to answer when evidence is insufficient. |
| **Epistemic uncertainty** | Uncertainty from lack of knowledge. Reducible with more data. |
| **Aleatoric uncertainty** | Uncertainty inherent in the process. Not reducible. |

---

## 3. Plain-language explanation

Two properties of these systems break the mental model most engineers arrive with.

**First: the same input can give different outputs.** You send the identical prompt twice and get two
different answers. Nothing is broken. Generation involves sampling from a probability distribution
over possible next tokens, and sampling is random by design. This is the opposite of every API you
have built.

**Second: the model has no notion of truth, and its fluency is unrelated to its accuracy.** A model
trained to predict likely text will produce likely-sounding text. "The capital of Australia is
Sydney" is an extremely likely-sounding sentence. It is also wrong. Nothing in the training objective
distinguishes those two properties (M1-L07 §5.2).

Put together, these produce the defining engineering challenge of this field:

> **The output is confident, fluent, well-formatted, plausible — and possibly entirely fabricated.
> There is no signal in the output itself that tells you which.**

Compare this with a database. If you `SELECT` a row that does not exist, you get zero rows. The
system tells you. An LLM asked about a policy that does not exist will frequently *write the policy*,
in your house style, with a plausible clause number. That is not a bug being triggered; it is the
system doing precisely what it was built to do.

Everything in Modules 5, 7 and 10 — validation, retrieval, citations, abstention, evaluation,
human oversight — exists to build the missing signal from the outside.

### Connecting to what you already know

| Web system | Behaviour on missing data | LLM |
|---|---|---|
| `SELECT` with no match | Returns 0 rows | May fabricate a plausible row |
| REST API, unknown ID | `404` | May invent the resource |
| Type checker, bad type | Compile error | May produce invalid output that parses fine |
| Failing test | Red | Silent |

**Every failure signal you rely on is absent.** You have to construct them: schema validation
(M5-L06), evidence checks (M7-L12), abstention thresholds (M7-L13), evaluation suites (M5-L18).

---

## 4. Analogy

**A very well-read colleague, speaking from memory, who never says "I don't know".**

They have read enormous amounts and recall much of it. Asked something they know, the answer is
excellent. Asked something they half-remember, they produce a fluent, confident answer with
plausible details — because they are reconstructing rather than recalling, and they cannot tell the
difference from the inside.

### Where the analogy breaks

1. **A person usually has *some* sense of shakiness.** Models have an internal probability, but it is
   frequently poorly calibrated, and — crucially — **the confidence you can see in the wording is not
   that number.** Fluent phrasing is generated the same way regardless.
2. **You can ask a colleague "how sure are you?" and get useful information.** Asking a model the
   same question gets you *text that resembles an expression of confidence*, generated by the same
   next-token process. A model saying "I am 95% certain" is not reporting a measurement. This is one
   of the most consequential misunderstandings in the field.
3. **A colleague's errors are usually random; model errors are systematic.** The same prompt shape
   will fail the same way across users, which is worse for reliability and better for testing.
4. **A colleague can go and check.** A model cannot, unless you give it tools and retrieval — which
   is exactly what Modules 7 and 8 are for.

---

## 5. Detailed technical explanation

### 5.1 Where the randomness comes from

Two separate sources. Engineers routinely conflate them.

**Source 1 — deliberate sampling.** At each step the model produces a probability distribution over
the whole vocabulary:

```
"The capital of France is"  ->   " Paris"     0.89
                                 " located"   0.04
                                 " the"       0.03
                                 " a"         0.02
                                 ...          (~100k more)
```

With **greedy decoding** you always take " Paris" and the output is reproducible. With **sampling**
you draw according to those probabilities, so roughly 4% of the time you get " located". Temperature
controls how flat that distribution is before drawing (M4-L14).

**This source is under your control.** Set temperature to 0 and it largely disappears.

**Source 2 — infrastructure non-determinism.** Even at temperature 0, hosted models may not be
byte-identical across calls. Floating-point addition is not associative, so results depend on batch
composition, GPU kernel selection and hardware. Providers also update models behind a version label.

**This source is not under your control.** Therefore:

> **Never write a test asserting exact model output.** Assert on structure, schema, and properties
> (M5-L12).

### 5.2 What hallucination is, mechanically

Hallucination is not a malfunction. It follows directly from three facts you already know:

1. The training objective is *predict the likely next token* (M1-L07).
2. There is no term in that objective for truth.
3. At generation time the model must produce *something* — there is no "no output" token that gets
   selected when knowledge is absent.

Given a prompt about a non-existent policy, the model computes the most likely continuation. Text
that looks like a policy is far more likely than text that looks like a refusal, especially in a
context that has been formatted as a policy document. **So it writes a policy.**

Contributing factors:

| Factor | Why it increases hallucination |
|---|---|
| Question outside training data | Nothing to recall; reconstruction fills the gap |
| Rare or long-tail entities | Weak statistical support; nearby patterns dominate |
| Specific details requested (dates, figures, citations) | Format is highly predictable, content is not — the shape of a citation is easy to generate |
| Long outputs | Each additional claim is another chance to fabricate |
| Leading prompts | "Summarise section 4.2" presupposes it exists |
| High temperature | Lower-probability tokens get selected more often |
| No grounding | Nothing anchors output to a source |

The row about citations deserves emphasis. **Fabricated references are among the most common and
most damaging failures**, precisely because the *form* of a citation — author, year, plausible title,
volume, page range — is extremely learnable while the *fact* of it is not. The output looks maximally
credible exactly where it is least reliable.

### 5.3 Confidence, accuracy and calibration

These are three different things.

- **Accuracy** — how often the system is right. A property of the system, measured over a dataset.
- **Confidence** — the probability the model assigns to its output. A number per prediction.
- **Calibration** — whether confidence *matches* accuracy.

A model is **calibrated** if, among all predictions made with confidence ≈ 0.8, about 80% are
correct. Calibration is what makes confidence *actionable*: it lets you set a threshold and route
low-confidence cases to a human.

```
Perfectly calibrated          Overconfident (typical)
accuracy                       accuracy
  1.0 |        /                 1.0 |        .
      |      /                       |      .
      |    /                         |    .      <- actual accuracy
      |  /                           |  .   /       falls below the
      |/                             |/   /         diagonal everywhere
  0.0 +---------- confidence     0.0 +----/------ confidence
      0.0      1.0                    0.0      1.0
```

**Three practical warnings:**

1. **A model's verbal confidence is not its probability.** "I'm confident that…" is generated text.
   Do not parse it as a measurement.
2. **Asking a model to rate its own confidence 1–10 gives you a number, not an estimate.** It is
   often weakly correlated with correctness — sometimes useful, never trustworthy without
   measurement. If you use it, *measure its calibration first* and re-measure after any prompt
   change.
3. **Token probabilities are available from some APIs and are better than verbal confidence**, but
   they measure confidence in the *token*, not in the *claim*. A model can be highly confident about
   every token of a fabricated sentence.

The honest engineering position: treat confidence as a signal to be validated, never as evidence.
Where you need reliability, get it from **grounding and verification**, not from asking the model how
sure it is.

### 5.4 Two kinds of uncertainty

| | Epistemic | Aleatoric |
|---|---|---|
| **Source** | The model lacks knowledge | The outcome is genuinely random |
| **Reducible?** | Yes — more data, retrieval, tools | No |
| **Example** | "What is our refund policy?" — fixable by giving it the policy | "Will this customer churn?" — genuinely uncertain |
| **Right response** | Retrieve the information (Module 7) | Report a probability, not a verdict |

Distinguishing these tells you what to build. **Most LLM application failures are epistemic**, which
is good news: they are fixable by giving the model the right context. That is the entire premise of
RAG.

### 5.5 Mitigations — and what each does *not* fix

| Mitigation | Fixes | Does **not** fix | Lesson |
|---|---|---|---|
| Retrieval (RAG) | Missing knowledge | Model ignoring or misreading retrieved text | Module 7 |
| Require citations | Untraceable claims | Fabricated or mismatched citations — **verify them programmatically** | M7-L12 |
| Abstention thresholds | Answering with no evidence | Confidently wrong answers *with* evidence | M7-L13 |
| Structured output + schema validation | Malformed output | Well-formed nonsense | M5-L06/07 |
| Lower temperature | Some variance | Systematic errors; a confident wrong answer stays wrong | M4-L14 |
| Multiple samples + agreement | Unstable answers | Consistently wrong answers | M13-L13 |
| Human review | Most of it | Scale, cost, and reviewer over-trust | M10-L09 |
| Tools / code execution | Arithmetic, lookups, current data | Anything the tool does not cover | Module 8 |

**Read the third column.** Every mitigation has a residual failure mode, and stacking them reduces
risk without eliminating it. There is no configuration that makes an LLM reliably truthful. Systems
that must not produce a wrong answer need a deterministic check outside the model, or a human, or
both. Stating this clearly to stakeholders is part of your job (M14-L10).

### 5.6 Assumptions and limitations

- Models and providers vary; calibration differs between them and between versions.
- Reasoning-focused models and self-consistency methods reduce some error classes but do not
  eliminate fabrication. `[UNVERIFIED]` — an actively moving area; verify claims against current
  provider documentation.
- "Hallucination" is an imprecise umbrella term covering fabricated facts, misread sources,
  outdated information and instruction-following failures. These have different fixes, and M7-L20
  separates them for debugging.

---

## 6. Worked example — confidence versus correctness

A classifier routes tickets and reports confidence. 1,000 predictions, bucketed by stated confidence:

| Confidence bucket | Predictions | Actually correct | Observed accuracy | Calibrated? |
|---|---|---|---|---|
| 0.5 – 0.6 | 120 | 71 | 0.59 | ✅ close |
| 0.6 – 0.7 | 180 | 116 | 0.64 | ✅ close |
| 0.7 – 0.8 | 250 | 175 | 0.70 | ⚠️ slightly over |
| 0.8 – 0.9 | 300 | 231 | 0.77 | ❌ overconfident |
| 0.9 – 1.0 | 150 | 122 | 0.81 | ❌ **badly overconfident** |

**Overall accuracy = (71+116+175+231+122)/1000 = 715/1000 = 71.5%.**

Now the practical question: you want to auto-approve high-confidence predictions and send the rest to
a human. You choose the ≥ 0.9 bucket, expecting ~95% accuracy.

**Reality: 81%.** Roughly **1 in 5** auto-approved decisions is wrong — nearly four times your
expected error rate.

**Step-by-step consequence.** With 150 auto-approved predictions per 1,000:

- Expected errors at 0.95 accuracy: 150 × 0.05 = **7.5**
- Actual errors at 0.81 accuracy: 150 × 0.19 = **28.5**

You planned for 7 or 8 problems and will get 28 or 29. If each mis-routed ticket costs an hour of
rework, your automation created 21 hours of unplanned work per 1,000 tickets — and it will be blamed
on "the AI being wrong" rather than on an uncalibrated threshold.

**What to do:** *measure* accuracy per confidence bucket, then choose the threshold from the measured
table rather than from the number the model reports. Here, no bucket reaches 95%, so **95% is not
achievable by thresholding at all** — a genuinely important finding. You would need a better model, a
narrower task, or a different automation target. Discovering that before launch rather than after is
the entire value of this analysis.

---

## 7. Practical activity

**File:** [`labs/m1/l10_calibration.py`](../../labs/m1/l10_calibration.py)

```bash
python3 labs/m1/l10_calibration.py
```

Three demonstrations, no API key or libraries required:

1. **Sampling non-determinism** — the same "prompt" run 10 times, showing different outputs, then the
   same prompt with greedy decoding showing identical outputs.
2. **A reliability diagram** — a simulated overconfident classifier, bucketed and plotted, with
   Expected Calibration Error computed.
3. **Threshold analysis** — what happens to your auto-approval rate and error count at each possible
   confidence threshold, reproducing the §6 arithmetic on simulated data.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `rng.choices(tokens, weights=probs)` | Sampling from a distribution — mechanically what an LLM does at each step. |
| `max(dist, key=dist.get)` | Greedy decoding — deterministic. |
| `CAL_INTERCEPT + CAL_SLOPE * stated` | Turns a stated confidence into the model's *true* accuracy. Slope 0.55 flattens the relationship, so bold claims are punished hardest. Slope 1.0 / intercept 0.0 would be perfect calibration. |
| `abs(acc - conf) * weight` | Expected Calibration Error: the average gap between stated and actual, weighted by bucket size. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Deterministic:

```
======================================================================
1. WHY THE SAME PROMPT GIVES DIFFERENT ANSWERS
======================================================================
Prompt: "The capital of France is"

The model produces a probability distribution over next tokens:
    ' Paris'     0.89  ############################################
    ' located'   0.04  ##
    ' the'       0.03  #
    ' a'         0.02  #
    ' home'      0.02  #

SAMPLING (temperature > 0) - 20 runs of the identical prompt:
    Paris |Paris |Paris |the |Paris |located |Paris |Paris |the |Paris |located |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |located
    -> 3 distinct outputs from the SAME input: [' Paris', ' located', ' the']

GREEDY (temperature = 0) - 20 runs of the identical prompt:
    Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris |Paris
    -> 1 distinct output. Reproducible.

But note: greedy removes SAMPLING variance only. Hosted models can
still differ run to run because floating-point addition is not
associative and batching/hardware change the summation order.
Never assert exact model output in a test.

======================================================================
2. CALIBRATION: does stated confidence match actual accuracy?
======================================================================
2000 predictions from a simulated overconfident model.

bucket             n    stated    actual      gap  reliability
----------------------------------------------------------------------
0.5-0.6         403     0.550     0.618   +0.067      |    *                                
0.6-0.7         382     0.650     0.660   +0.010              *                             
0.7-0.8         385     0.748     0.714   -0.034                   * |                      
0.8-0.9         432     0.850     0.759   -0.091                      *      |              
0.9-1.0         398     0.953     0.814   -0.139                           *          |     
----------------------------------------------------------------------
                                                  | = stated   * = actual

Expected Calibration Error (ECE) = 0.069
  In plain English: on average the model's stated confidence is
  wrong by about 6.9 percentage points.

  Look at the DIRECTION of the gaps, not just their size. At low
  confidence the model is slightly UNDER-confident (gap positive:
  it does better than it claims). From about 0.7 upward it flips to
  OVER-confident, and the gap widens as the claim gets bolder:
  -0.034, then -0.091, then -0.139.

  That pattern is the worst possible shape. The model is most wrong
  about itself exactly where you were planning to trust it - in the
  high-confidence bucket you wanted to automate. A single average
  ECE number would have hidden this. Always look per bucket.

======================================================================
3. CHOOSING AN AUTO-APPROVAL THRESHOLD
======================================================================
You want to auto-approve high-confidence predictions and send the
rest to a human. Which threshold actually delivers what you need?

 threshold  automated  % traffic  accuracy   errors   vs 95% target
----------------------------------------------------------------------
      0.60       1597      79.8%     0.738      418   short by 21.2pp
      0.70       1215      60.8%     0.763      288   short by 18.7pp
      0.80        830      41.5%     0.786      178   short by 16.4pp
      0.85        615      30.8%     0.802      122   short by 14.8pp
      0.90        398      19.9%     0.814       74   short by 13.6pp
      0.95        208      10.4%     0.827       36   short by 12.3pp
      0.99         49       2.5%     0.837        8   short by 11.3pp
----------------------------------------------------------------------

READ THIS CAREFULLY:
* No threshold reaches 95% accuracy - not even 0.99.
* That is a genuinely important finding. It means the 95% target is
  NOT achievable by thresholding this model at all. You would need a
  better model, a narrower task, or a different automation target.
* Discovering this BEFORE launch is the entire value of the exercise.
* Note the trade-off in the table: raising the threshold improves
  accuracy but automates less traffic. There is no free setting.
* And note what you must NOT do: take the model's stated 0.95 at
  face value. It claims 0.95 and delivers far less.
======================================================================
```

### 7.3 Reading the result

**Part 1** shows the mechanism directly: one distribution, 20 identical prompts, **three different
outputs**. Nothing failed. Then greedy decoding gives one output twenty times. If your mental model
was "same input, same output", this is the correction.

**Part 2 — read the direction of the gaps, not just the ECE.** The single ECE number is 0.069, which
sounds tolerable. The per-bucket breakdown says something much more specific:

| stated | actual | gap |
|---|---|---|
| 0.550 | 0.618 | **+0.067** (under-confident) |
| 0.650 | 0.660 | +0.010 (about right) |
| 0.748 | 0.714 | −0.034 (over) |
| 0.850 | 0.759 | −0.091 (over) |
| 0.953 | 0.814 | **−0.139** (badly over) |

The model is *under*-confident when it is unsure and *increasingly over*-confident as it becomes
assertive. **This is the worst possible shape**, because the high-confidence bucket is precisely the
one you were planning to automate. The average ECE hides it completely. Always look per bucket.

**Part 3 is the finding that changes a project plan.** You wanted 95% accuracy on auto-approved
items. The table says:

```
threshold 0.95 -> automates 10.4% of traffic, accuracy 0.827  (short by 12.3pp)
threshold 0.99 -> automates  2.5% of traffic, accuracy 0.837  (short by 11.3pp)
```

**No threshold achieves the target.** Not 0.99. Pushing the threshold higher buys almost nothing —
accuracy creeps from 0.827 to 0.837 while automated volume collapses from 10.4% to 2.5%. The curve
has flattened; there is no setting that rescues this.

That is not a failure of the analysis, it is the *point* of the analysis. The correct conclusion is
**"this approach cannot meet the stated requirement"**, and the options are a better model, a
narrower task, a lower target, or human review of everything. Learning that from a table in ten
minutes is enormously cheaper than learning it from production in three months.

Note also the trade-off structure: every threshold trades automation volume against accuracy, and
there is no free setting. This shape recurs constantly — you will meet it again as precision/recall
in M3-L14 and as retrieval `k` in M7-L11.

**Verification:** confirm `ECE = 0.069`, that the 0.9–1.0 bucket shows `0.953  0.814  -0.139`, and
that no row in part 3 says `MEETS TARGET`.

---

## 8. Common mistakes and troubleshooting

1. **Writing tests that assert exact model output.** They will fail for reasons unrelated to
   correctness. Assert schema, structure and properties.
2. **Treating temperature 0 as fully deterministic.** It removes sampling variance, not
   infrastructure variance.
3. **Trusting verbal confidence.** "I'm certain" is generated text.
4. **Using self-reported confidence as a routing threshold without measuring calibration.**
5. **Assuming citations are real.** Verify them against the source programmatically (M7-L12).
6. **Believing RAG eliminates hallucination.** It reduces epistemic error. The model can still
   misread, over-generalise, or ignore the context.
7. **Blaming the model for a specification failure.** "Summarise section 4.2" when there is no
   section 4.2 is a leading prompt.

| Symptom | Likely cause | Fix |
|---|---|---|
| Different answer each run | Sampling | Lower temperature; assert on structure not text |
| Different answer at temperature 0 | Infrastructure/model version | Pin model version; do not assert exact strings |
| Plausible but fake citations | Fabrication of a highly learnable format | Require IDs from retrieved chunks and verify each one exists |
| Auto-approval error rate above plan | Uncalibrated confidence | Build the bucket table; pick the threshold from measurement |
| Confident wrong answers *with* retrieved context | Misreading, or retrieval returned the wrong thing | Separate retrieval evaluation from answer evaluation (M7-L19) |

---

## 9. Security, privacy, reliability and cost

- **Security.** Non-determinism means a prompt-injection attack that fails once may succeed on
  retry. Security testing must be repeated, and defences must not rely on the model behaving
  consistently (M5-L13).
- **Reliability.** Design for *distributions*, not single outcomes. Your SLO is "≥ X% of responses
  meet criterion Y", never "the system is correct".
- **Cost.** Mitigations cost money: multiple samples multiply cost; retrieval adds calls; human
  review adds labour. Choose them against measured risk, not anxiety (M5-L15).
- **Governance.** Known failure modes and their mitigations belong in the system card (M10-L15).
  Users must be told the system can be wrong (M10-L09) — and told in a way they will actually act on,
  which is harder than adding a disclaimer.

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

For each, say whether it is expected behaviour or a defect, and why:

1. The same prompt returns different wording on two runs at temperature 0.7.
2. The model invents a plausible-looking academic citation.
3. The model says "I am 90% confident" and is wrong.
4. A model given a document still answers using outside knowledge.
5. Two identical API calls at temperature 0 return slightly different text.

### Exercise 2 — Intermediate (~20 min)

Run the lab, then:

1. What Expected Calibration Error does it report, and what does that number mean in plain English?
2. From the threshold table: which threshold gives the highest accuracy on auto-approved items, and
   what fraction of traffic does it automate?
3. Your target is 95% accuracy on auto-approved items. Is it achievable? What would you tell the
   business?
4. Set `CAL_INTERCEPT = 0.0` and `CAL_SLOPE = 1.0` and re-run. What happens to the ECE and to the
   threshold table? What do those two values represent about the model?

### Exercise 3 — Challenge (~25 min)

Design the reliability strategy for an assistant that answers HR policy questions for employees.
Wrong answers about leave entitlement create real harm.

1. Which failures are epistemic and which are aleatoric? What follows from that?
2. Specify your mitigation stack, in order, and for each state its residual failure mode.
3. Define the abstention rule precisely: what triggers "I cannot answer this"?
4. Write the exact user-facing wording that communicates the limitation, in under 40 words.
5. State what you would measure weekly in production to know the system is still working.
6. State one failure this design will not prevent, and who accepts that risk.

Part 6 is required. A design without a stated residual risk is not finished (M10-L16).

---

## 11. Quiz

**Q1.** Two identical prompts at temperature 0.8 give different answers. This is:

- A. A bug in the SDK  B. Expected: generation samples from a probability distribution
- C. A sign the model is overloaded  D. Caused by prompt injection

**Q2.** Which best describes the mechanical cause of hallucination?

- A. Corrupted training data.
- B. The training objective rewards likely continuations, contains no term for truth, and generation
  must always produce something — so gaps get filled with plausible text.
- C. Too high a learning rate during training.
- D. Insufficient model parameters.

**Q3.** A model outputs "I am 95% confident that…". What does this tell you?

- A. The model's internal probability is 0.95.
- B. Essentially nothing measurable: that phrase is generated by the same next-token process as the
  rest of the text and is not a report of an internal measurement.
- C. The answer is correct 95% of the time.
- D. Confidence should be recalibrated to 0.95.

**Q4.** In the §6 table, predictions in the 0.9–1.0 bucket were correct 81% of the time. The model is:

- A. Well calibrated  B. Underconfident  C. Overconfident  D. Perfectly accurate

**Q5.** You auto-approve the 150 predictions in the 0.9–1.0 bucket expecting 95% accuracy but getting
81%. How many more errors than planned, per 1,000 predictions?

- A. About 7  B. About 14  C. About 21  D. About 28

**Q6.** Which uncertainty type is reducible, and how?

- A. Aleatoric, by adding more training data.
- B. Epistemic, by supplying the missing information through retrieval or tools.
- C. Both, by lowering temperature.
- D. Neither.

**Q7.** Why must you never assert exact model output in a test?

- A. Tests run too slowly.
- B. Sampling and infrastructure non-determinism mean identical inputs can produce different text
  even at temperature 0, so the test fails for reasons unrelated to correctness.
- C. Model outputs are always too long.
- D. It is allowed and recommended.

**Q8.** Requiring citations fixes which problem, and leaves which one open?

- A. Fixes fabrication entirely; leaves nothing open.
- B. Fixes untraceable claims; leaves fabricated or mismatched citations open, so each citation must
  be programmatically verified against the retrieved source.
- C. Fixes calibration; leaves latency open.
- D. Fixes nothing.

**Q9.** Why are fabricated citations especially common and especially damaging?

- A. Citation formats are rare in training data.
- B. The *form* of a citation is highly learnable while its *content* is not, so the output looks
  maximally credible exactly where it is least reliable.
- C. Models are trained to invent sources.
- D. Citations are always at the end of a long output.

**Q10.** *(Written, rubric-graded.)* In under 90 words, explain to a non-technical stakeholder why you
cannot promise the assistant will never give a wrong answer, and what you can promise instead.

---

## 12. Revision notes

- Two randomness sources: **sampling** (yours to control via temperature) and **infrastructure**
  (not yours). Temperature 0 is not a determinism guarantee.
- **Hallucination is the objective working as designed:** predict likely text, no truth term, must
  output something.
- Worst for: unknown/long-tail topics, requested specifics, long outputs, leading prompts, high
  temperature, no grounding.
- **Fabricated citations** are the classic case — learnable form, unlearnable content.
- **Confidence ≠ accuracy.** Calibration is the match between them. Verbal confidence is generated
  text, not a measurement. Measure calibration before thresholding on it.
- **Epistemic** uncertainty (missing knowledge) is reducible — that is what RAG is for.
  **Aleatoric** is not; report a probability instead of a verdict.
- Every mitigation has a residual failure mode. **No configuration makes an LLM reliably truthful.**
  Hard requirements need deterministic checks or humans outside the model.
- Build SLOs as distributions: "≥ X% meet criterion Y", never "it is correct".

---

## 13. Completion checklist

- [ ] I can name both sources of non-determinism.
- [ ] I can explain hallucination from the training objective in three steps.
- [ ] I can define calibration and read a reliability diagram.
- [ ] I ran the lab and can interpret the ECE and threshold table.
- [ ] I can distinguish epistemic from aleatoric uncertainty with examples.
- [ ] For each mitigation I can state what it does not fix.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Ji et al., "Survey of Hallucination in Natural Language Generation" (2022). `[UNVERIFIED]`
- Guo et al., "On Calibration of Modern Neural Networks" (ICML 2017) — the overconfidence result.
  `[UNVERIFIED]`
- Kadavath et al., "Language Models (Mostly) Know What They Know" (2022) — evidence on self-reported
  confidence, and its limits. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L11 — AI Capability vs Application Reliability](M1-L11-capability-vs-reliability.md)

You now know why models are unreliable in a specific, characterisable way. The final lesson of
Module 1 turns that into a decision framework: when to use AI, when to use ordinary code, and how to
tell the difference before you have built the wrong thing.
