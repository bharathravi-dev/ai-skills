# Module 5 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 5 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M5-L01 Anatomy of a Prompt | [↓](#m5-l01) |
| M5-L02 Message Roles | [↓](#m5-l02) |

---

<a id="m5-l01"></a>
## M5-L01 — Anatomy of a Prompt

**Answers: A · B · C · B · D · B · C · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Instruction, context, examples, input, output primer. **B** lists *message roles* (M5-L02), which is a different axis — roles are the envelope, components are the contents. **C** and **D** are inventions. |
| 2 | **B** | First. Instructions are short, they set the frame, and the beginning is one of the two strong positions (M4-L06 §5.4 measured the U-shaped recall curve). **C** is the common ordering mistake — it buries the instruction behind bulk. **A** puts it exactly where recall is worst. **D** wastes tokens and can create ambiguity about which instruction applies. |
| 3 | **C** | Could two competent people follow it and produce materially different output? If so, so can the model. **A** — brevity is unrelated to specificity; "summarise this" is short and hopeless. **B** — technical vocabulary often *increases* precision. **D** — review helps, but the test is a property of the instruction itself. |
| 4 | **B** | A negative-case instruction: "use null; do not invent". §7.3 measured invented IDs at **24%** until the null rule was added, at which point they went to **0%**. **A** — an example may help but does not state the rule. **C** — more context does not tell the model what to do when the field is absent. **D** — temperature 0 invents just as confidently. |
| 5 | **D** | A partial start to the response, placed at the end of the prompt, so the model continues from it rather than deciding whether to write a preamble. Measured worth **+31 points of parse rate**. **A**, **B** and **C** describe other components. |
| 6 | **B** | So the model can distinguish instructions from data. This is both a clarity requirement and the basic prompt-injection mitigation — measured taking the injection rate from **100% to 24%** by delimiters alone (M5-L13). **A** — delimiters *add* tokens. **C** — no API requires them. **D** — caching operates on prefixes, not delimiters. |
| 7 | **C** | Billed on every request in the conversation. M4-L16 §7.3 measured it at **25%** of a 40-turn conversation's tokens while never changing — which is exactly why prompt caching targets it (M5-L16). **A**, **B** and **D** are all false and all lead to under-budgeting. |
| 8 | **D** | Identify which component is missing or vague. §7.3's table shows each failure column moving when *its own* component is added and staying flat otherwise, which is what makes diagnosis possible. **A** is the commonest waste of time — it fixes the symptom while telling you nothing. **B** and **C** address causes that are usually not the cause. |
| 9 | **B** | The question lands mid-context, where recall is weakest (M4-L06 §7.3 measured simulated recall of 1.000 at both ends against 0.240 at 50% depth). **A** may or may not be true and is a separate problem. **C** is not a convention, it is a measured effect. **D** — tokenizer efficiency is unaffected by ordering. |
| 10 | **C** | Code — versioned, tested and reviewed. It has inputs, outputs, edge cases and failure modes, and editing it changes behaviour. **The difference from ordinary code is that it fails silently and probabilistically**, which is an argument for *more* rigour, not less. **A** is how prompts get changed in production without anyone noticing. **B** and **D** misplace the ownership and the risk. |

**Q11 rubric (4 marks).** The rewrite must fix all four defects in *"Look at the customer email and tell
me what they need."* One mark each for: **naming the output** (a category from a stated set, or named
fields — not "what they need"); **stating the format** (JSON with named keys, or an explicit
structure); **covering the negative case** (what to emit when the need is unclear or absent — `null`,
`"unclear"`, or an escalation flag, explicitly *not* a guess); and **delimiting the email** so its
content cannot be read as an instruction. A rewrite that is merely longer and more polite scores 0.

---

<a id="m5-l02"></a>
## M5-L02 — Message Roles and Instruction Priority

**Answers: A · C · D · B · C · A · C · C · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Special tokens delimiting turns in one flat sequence (M4-L03 §5.5). **B** is the mental model people carry and it is the dangerous one — believing there is a privileged channel is why system prompts get treated as security boundaries. **C** — one set of weights. **D** — roles are *in* the token stream, which is exactly why they can be forged. |
| 2 | **C** | Post-training on data where system instructions were followed and contradicting user instructions were not (M4-L12). It is **learned behaviour**. **A** — no gateway enforces it. **B** — no attention weights are assigned by role; the model learned to weight a token *pattern*. **D** — position contributes, but §7.3 shows recency competing with it. |
| 3 | **D** | An internal price list. The system prompt is **not hidden** — it is in your request payload and models can be induced to reveal it. §7.3 measured the strongest defence as removing the secret entirely (100% vs 35.6%). **A**, **B** and **C** are exactly what a system prompt is for. |
| 4 | **B** | Untrusted input, delimited and validated. **A** is the common and costly assumption: your retriever fetched the document, but it did not *write* it (M7-L18). **C** would give attacker-controlled text the highest instruction weight. **D** — internal sources are compromised too. |
| 5 | **C** | It is structurally part of the assistant turn, not a hint at the end of the user turn — which is why it is stronger than an output primer. **A** is false; support is provider-specific. **B** — nothing precedes the system message. **D** is backwards: whatever you prefill is **not** returned, so you must prepend it. |
| 6 | **A** | Not encoding user content with special tokens enabled. §7.3 shows this taking the assembled prompt from **2 system turns to 1** — one flag, complete protection against *this* attack. **B** relies on the model's cooperation. **C** is an arms race against encodings and homoglyphs. **D** changes nothing about tokenisation. |
| 7 | **C** | Reduced by delimiting, not eliminated. §7.3 measured a **perfectly clean token sequence — 1 system turn** — with the model still complying **53.5%** of the time. **A** is the dangerous confusion: the flag fixes forgery, not persuasion. **B** — safety training covers harm categories, not your business rules. **D** misses that the persuasion works *because* they are ordinary words. |
| 8 | **C** | Recency competes with role; the outcome is not guaranteed. Measured: a direct forbidden request's refusal rate fell from **95.3% at turn 1 to 64.4% at turn 40**. **A** and **B** both state a rule where there is a contest. **D** — no conflict error exists. |
| 9 | **D** | Not putting the price in the context. Measured **100%** against 35.6% for the prompt alone. **A** bought **+0.5%** — within 0.6 standard errors of nothing. **B** helped (+18.6%) and is worked around. **C** is position tuning, not a control. |
| 10 | **B** | Disclosable, and never a place for anything sensitive. **A**, **C** and **D** each describe a protection that does not exist: it is not hidden from a determined user, transport encryption does not stop the model repeating it, and "visible only to the provider" is still a disclosure you may not be permitted to make. |

**Q11 rubric (4 marks).** One mark each for: identifying that the system prompt is **not hidden** and
that "tell it not to reveal it" is a prompt-level instruction, which §7.3 measured degrading to 35.6%
against a reframed request; noting that a discount matrix is **per-request-irrelevant bulk billed on
every turn** (M4-L16); proposing the alternative — supply *only the applicable discount* for the
current request, computed outside the model, or have the model emit a discount *code* the application
resolves; and stating the general rule that the model should not be given a capability or a secret you
would not want an injected instruction to reach. An answer that only says "that's insecure" without an
alternative scores 1.

---

<a id="m5-l03"></a>
## M5-L03 — Zero-shot, Few-shot and Example Selection

**Answers: B · A · D · C · A · B · D · C · A · D · B · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Style and edge-case handling are exactly what prose describes badly and a demonstration describes precisely. **A** — if the instruction is already precise, examples buy little and cost tokens forever. **C** is the commonest waste: a schema *constrains* format, examples only *suggest* it (M5-L06). **D** is backwards — examples only ever add tokens. |
| 2 | **A** | Zero-shot is the baseline the examples must beat, and §7.3 shows why: at 1 and 2 examples the prompt scored **below** it (67.7% and 65.1% vs 74.6%). Without the baseline you cannot see that. **B** changes what you are measuring. **C** presumes the answer. **D** answers a different question. |
| 3 | **D** | Majority-label bias — measured at **56.5% predicted `billing` against a true rate of 22.5%**, and accuracy 59.9% vs 83.6% for a balanced set. **A** ignores the effect on everything else. **B** treats the instruction as dominant; the examples compete with it. **C** overstates — other labels still appear, just far too rarely. |
| 4 | **C** | Last, because later examples weigh more. §7.3 measured the label in final position over-predicted by **+5.5 to +14.7 points** across all 24 orderings of one set. **A** and **B** are plausible-sounding placements with no support. **D** is refuted by a **14.1-point** accuracy spread from reordering alone. |
| 5 | **A** | Every example is a specification, not an illustration; a typo is a demonstrated pattern. **B** attributes an intention the model does not have. **C** confines a real effect to one position. **D** describes validation no provider performs on your prompt. |
| 6 | **B** | The count-controlled test settles it: at a fixed four examples, **63.8%** from one label vs **77.7%** from four. A set that never shows a label argues against it. **A** is the natural reading and the lab was built to reject it — the count was held constant. **C** is excluded by the 8 repeated draws (sd 1.8 points against a 14-point effect). **D** invents a mechanism nothing measured. |
| 7 | **D** | Per unit of benefit, examples are the most expensive component — billed on **every request forever** for a curve that flattens after a handful. **A** — they add to instructions, never replace them. **B** — caching reduces the price of the prefix; it does not make it free, and only if the prefix is stable (M5-L16). **C** describes no provider's billing. |
| 8 | **C** | High volume and a stable task: the examples stop being billed per request (M13-L02). **A** is the case *for* few-shot — editing a prompt is minutes, retraining is not. **B** is far below what fine-tuning needs. **D** is a reason to be *more* careful with training data, not a cost argument. |
| 9 | **A** | Measured: **57.9% against zero-shot's 74.6% — 16.6 points worse**, with the damage concentrated on the labels the examples never showed. **B** is the assumption that produced the bad set. **C** would require the instruction to dominate, which the same lab disproves. **D** overstates: other labels appear, at far below their true rate. |
| 10 | **D** | That customer's text is now in every request, indefinitely, to a third party. **A** is false for most default configurations. **B** may be true and does not answer whether *you* were permitted to send it. **C** describes something a tokenizer does not do — it encodes text, it does not remove identity. |
| 11 | **B** | Independently drawn sets differ in count **and** selection, so the design cannot attribute the difference to either. Nested sets over several draws separate them: it turned an unusable curve into a clean one, and the between-draw sd of **1.8 points** is what a single run per count would have silently reported as signal. **A** blames the phenomenon for a flaw in the design. **C** — more test data narrows intervals but does not remove a confound. **D** discards the evidence that the design is broken. |
| 12 | **A** | All five sets are four examples, so all cost 240 example tokens — yet they span **25.7 points**. Selection is the cheapest large lever available. **B** and **C** invent cost differences the design holds constant. **D** is true of the *absolute* cost and irrelevant to comparing strategies at equal token count. |

**Q13 rubric (4 marks).** One mark each for: **the test set resembles the examples** — a five-shot
prompt tested on inputs like its own examples flatters itself, and §7.3 measured 92.3% on clear-cut
cases against 62.7% on ambiguous ones from the same all-easy example set; **the examples may not cover
the production label distribution**, and an omitted label is argued against, not merely absent
(63.8% vs 77.7% at a fixed count); **the comparison was probably against the broken version rather
than against zero-shot** — the +21.9-point repair in §6 conceals that the number that matters is
+5.3; and **the concrete next step** — re-measure both prompts against a held-out set drawn from real
production traffic, reporting intervals, and delete the examples if they do not beat zero-shot on it.
An answer that says only "the test set was unrepresentative" scores 1. An answer that recommends
adding *more* examples without a baseline measurement scores 0 for that mark.

---

<a id="m5-l04"></a>
## M5-L04 — Task Decomposition and Reasoning Prompts

**Answers: B · C · D · A · D · B · C · D · A · A · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | 0.95¹² ≈ 0.54. **A** is the mistake the whole lesson exists to prevent — per-step accuracy is not task accuracy. **C** assumes errors cancel; they compound, and §7.3 measured a 0.3% recovery rate. **D** is a dodge: independence is stated in the question, which is all the calculation needs. |
| 2 | **C** | **One.** Of 320 trials with a corrupted intermediate, one produced a correct final answer. **A** and **B** describe a self-correction that does not exist — every later step is computed competently from a wrong number. **D** overstates in the other direction: recovery is possible (a later slip can cancel an earlier one), just vanishingly rare. Both errors matter: one leads you to trust the model to catch itself, the other to skip checking. |
| 3 | **D** | Independence is the assumption the technique rests on, and §7.3 varies only that: **+30.0** points independent, **+1.5** at 60% correlation, **+0.0** systematic, at identical cost. **A** would make every sample identical and voting pointless. **B** and **C** are real considerations of no consequence next to independence — an odd k avoids ties, it does not make voting work. |
| 4 | **A** | Accuracy 70.0% → 70.0%, agreement **100%**. Every sample reproduced the same error, so the vote elected it unanimously. **B** is the independent-error result, and the point of the comparison is that the two are indistinguishable from the prompt. **C** inverts the agreement. **D** — there is no tie; unanimity is the problem. |
| 5 | **D** | Recomputing the written steps caught **100%** against the plausibility check's **9.4%**, for zero extra tokens. **A** is not a mechanism (§8.1). **B** is the check most people write and it fails because a corrupted digit usually lands inside any sane range. **C** costs 3× and detects nothing when the error repeats. |
| 6 | **B** | At 20 steps decomposition moved the task from 40.3% to 55.7% — a large gain that ships nothing, and at an 80% bar **no** chain length changed verdict. **A** is the natural reading of a gain column and is exactly what the table refutes. **C** is false — the gain is not linear, and linearity would not matter. **D** confuses "largest gain" with "best operating point". |
| 7 | **C** | Output tokens, typically 3–5× the input rate. Measured: 8 → 176 output tokens. **A** is a common billing misunderstanding — reasoning is generated, not supplied. **B** is false for every provider. **D** describes no billing model in use. |
| 8 | **D** | The same field wrong every time is a systematic error, reproduced in all nine samples. §7.3 measured **+0.0%** in that regime. **A** states the folk theory the lab was built to test. **B** — raising temperature changes the sampling, not the shared cause, and degrades the good samples too. **C** invents a partial benefit; the measurement is zero. |
| 9 | **A** | It reads 100% at k=1, where it compares a sample with itself, and 100% under systematic error, where it is confidently measuring the wrong thing — highest exactly where voting helps least. **B** is false; it is a counter over k samples you already paid for. **C** is irrelevant — you compute it yourself. **D** is false: it applies to any answer you can compare for equality. |
| 10 | **A** | Machine-readable intermediates your code can verify — the control that caught 100%. **B** is unsupported: emitting reasoning text is not evidence of reasoning (§5.8). **C** is the dangerous answer, and §5.8 and M10-L07 both forbid it. **D** is backwards — decomposed output is longer and costs more. |
| 11 | **C** | Shorten the chain and validate each field: two chains of six give 0.97⁶ = 83% each **and tell you which half failed**, while field-level checks (dates parse, line items sum to the total) catch what remains for nothing. **A** is not a mechanism. **B** buys 0.99/field = 89% — still one invoice in nine, at higher cost forever. **D** is 5× the bill against errors that a fixed template makes correlated. |
| 12 | **B** | Generated text, produced by the same next-token process as the answer, which may or may not reflect how the answer was reached. **A** and **D** both assert a causal link the mechanism does not provide — the trace is not a dump of the computation. **C** is the one with legal consequences: presenting a trace as a regulatory explanation asserts a faithfulness nobody has established (M10-L07). |

**Q13 rubric (5 marks).** One mark each for: **naming the confusion** — agreement measures
reproducibility, not correctness, and the colleague has reported the confidence signal rather than the
outcome; **asking for accuracy against a labelled set** at k=1 and k=5, which is the only number that
answers the question; **raising error correlation** — a rise in agreement with little rise in accuracy
is the signature of a shared quirk, and §7.3 measured +0.0 points at 100% agreement; **the cost**, since
k=5 is a 5× bill that must be justified by the accuracy delta, not the agreement delta; and **the
regression risk**, that the benefit depends on a model property which a provider update can change
silently (M5-L17). An answer that merely says "get more data" scores 1. An answer that accepts the
agreement figure as evidence of improvement scores 0.

---

<a id="m5-l05"></a>
## M5-L05 — Delimiters and Handling Untrusted Content

**Answers: A · D · D · B · B · A · C · D · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Only the system prompt is text your application authored. **B** is the one people get wrong most often: your retriever *fetched* the chunk, it did not write it, and an attacker who can get a document into your index has written part of your prompt (M7-L18). **C** — your code made the call; the *content* came from wherever the tool went. **D** — authentication establishes who uploaded it, not who wrote it, and internal accounts are compromised. |
| 2 | **D** | A customer pasting a config file and a developer pasting Python — the commonest thing in a support ticket. This is the finding to carry: the delimiter broke on **ordinary traffic**, with no attacker present. **A** inverts the labels — they were in the benign set precisely because they are innocent. **B** and **C** are real concerns unrelated to boundary collision. |
| 3 | **D** | The content was composed before the nonce existed, so it cannot name the closing tag — the same property as a parameterised query or a CSRF token (M2-L16). **A** confuses length with unpredictability; a long *fixed* string is still in your repository. **B** invents an API behaviour that does not exist — no provider assigns priority by delimiter. **C** is false and irrelevant. |
| 4 | **B** | It held the boundary 17/17 and silently altered 4/17 documents. The corruption is permanent, invisible at the time, and surfaces months later in an export with no trace back to the prompt-assembly code. **A** and **C** are trivial next to data loss. **D** is false — you are rewriting a string, not using a provider feature. Note that escaping also starts an arms race the nonce simply does not enter. |
| 5 | **B** | 37.8%. The boundary took it from 100% to 70.1% and the stated rule to 37.8% — a large, real improvement that is not a solution. **A** is the belief this section exists to remove. **C** ignores the rule's measured effect. **D** ignores the boundary's. Both halves matter: the boundary helps, and the residual is why the controls that bound damage must live outside the model. |
| 6 | **A** | An assembler, a parser, a corpus — no model, no key, no judgement. That is what makes it a unit test you can run in CI on every document type you accept, and it catches the §6 CV attack before deployment. **B**, **C** and **D** all describe apparatus the test does not need, and requiring them is why teams never run it. |
| 7 | **C** | The round trip measures whether the sentinel collides, and `End of document.` is a rare string — so the worst option scores second while giving the model no structural signal at all. **A** takes the number at face value, which is the error being illustrated. **B** blames the corpus for a limitation of the metric. **D** mistakes rarity for a boundary. |
| 8 | **D** | Instruction first so the model has the task, content next, then a restatement of the rules — because recency competes with role (M5-L02) and the last region should be yours. **A** gives the model data with no task. **B** invites exactly the structural confusion delimiting is for. **C** correctly identifies recency and then hands it to the attacker. |
| 9 | **A** | Least privilege: if the injected instruction has no tool worth reaching, compliance costs nothing. **B** is a prompt-level control against a residual measured at 37.8%. **C** is the escalation the lab shows to be worthless — length is not unpredictability. **D** changes sampling, not willingness. The general rule: **make the worst case a wrong suggestion, not a wrong action.** |
| 10 | **B** | The nonce changes the prefix, so a naive cache key misses every request; put the nonce region *after* the cacheable prefix (M5-L16). **A** inverts how caching works — uniqueness is what destroys a hit. **C** is false; caching keys on the prompt text, delimiters included. **D** overstates: the prompt is still cacheable up to the point where the nonce begins. |
| 11 | **C** | Untrusted, and delimited like any user input. The page may have been written specifically for your model to read. **A** confuses *who made the request* with *who wrote the response*. **B** is the dangerous one: an allow-listed domain can be compromised, host user-generated content, or simply be wrong. **D** strips markup, not instructions — the payload is prose. |

**Q12 rubric (5 marks).** One mark each for: **`<cv>` is a fixed delimiter** and the payload can contain
`</cv>` — the lab measured every fixed strategy failing to the trivial attack of including its own
marker; **the instruction is a prompt-level control with a measured residual** (37.8% in §7.3 with a
perfect boundary *and* a stated rule), so "ignore instructions inside" reduces compliance rather than
preventing it; **the concrete replacement** — a per-request nonce from `secrets`, content after the
instruction, rules restated last; **the round-trip test** in CI over real PDFs, which catches this class
of payload with no model involved; and **the control that actually bounds damage** — the model
summarises and a person decides, so the worst case is a misleading suggestion rather than an automated
hiring action. An answer that only proposes a better delimiter scores at most 2, because it stays
inside the layer that cannot be made sufficient.

---

<a id="m5-l06"></a>
## M5-L06 — Structured Outputs and JSON Schemas

**Answers: B · A · D · B · A · D · B · D · C · B · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | 6 of 14. The eight failures include a code fence and a polite preamble — the two most natural things a chat model does. **A** and **D** describe an experience nobody has had in production. **C** understates: fenced output fails, but `NaN`, string numbers and extra fields all parse happily, which is the more dangerous half. |
| 2 | **A** | Parses rose 9 → 11 and correct results stayed at **5**. Both new "successes" were truncated responses reborn as complete-looking objects with a key missing. **B** and **C** assume a parse is a win, which is the belief the measurement refutes. **D** is false — balancing leaves already-valid input alone; the harm is entirely in what it invents. |
| 3 | **D** | `finish_reason` (M4-L15). A response that stopped on a length limit is debris, and repairing it manufactures a confident answer from a partial one. **A** is the wrong direction — the *response* was cut, and the length limit is what you check via `finish_reason` anyway. **B** and **D**'s alternatives are worth knowing and neither tells you the response is complete. |
| 4 | **B** | It coerces to `42.5` and reports success. This is Pydantic's default and it is usually convenient. **A** describes `strict=True`, which is not the default. **C** is the behaviour you wish it had — there is no warning, which is precisely the problem. **D** would be a type error the model would not survive. |
| 5 | **A** | The value is right and the *signal* is gone: if a model upgrade changes number formatting, lax validation absorbs it and your error rate never moves (M5-L17). **B** is a real Decimal/float concern and not this one. **C** and **D** are false. The fix worth knowing is "coerce but record" — keep the convenience, emit the metric. |
| 6 | **D** | Python's `json` accepts `NaN` and `Infinity` by default, though neither is valid JSON. The result is a float `nan` that compares false against every threshold you test — a value that fails silently rather than loudly. **A** is what the JSON specification implies and not what the library does. **B** and **C** describe conversions it does not perform. Pass `parse_constant` to reject them. |
| 7 | **B** | A bound on the field. **A** is the confusion the lesson exists to remove: parsing has no opinion about magnitude. **C** guarantees valid JSON, not permissible values. **D** is an instruction, and an instruction asks where a schema refuses — it also fails for exactly the injected-instruction case where you need it most. |
| 8 | **D** | An undeclared field arriving in your object where downstream code may read it — mass assignment (M2-L15), now arriving via the model instead of a request body. **A** is what `Field(...)` requirements handle. **B** is `strict=True`. **C** is unrelated to validation. |
| 9 | **C** | Valid JSON, not *your* JSON. **A** and **D** describe constrained decoding or a schema-enforcing structured-output feature, which is a different setting with a different guarantee. **B** is beyond what any grammar can promise: a schema-conforming object can still carry a refund of one million, which is why §5.4's validation is required regardless. |
| 10 | **B** | 95.9% → 51.0% `[MOCK]`. Even the best row is 4,139 failures per 100,000 — a retry budget and a support queue. **A** and **D** both assume shape is free. **C** understates by a factor that changes the architecture: at 51% you flatten and split the call rather than tune the prompt. |
| 11 | **A** | It rejects the impermissible action **regardless of what persuaded the model** — the one control on the injection page that does not depend on out-arguing the attacker (M5-L05 §5.5). **B** and **C** describe input-side controls that output validation does not perform and that cannot be made sufficient. **D** confuses transport security with authorisation. |
| 12 | **C** | Validation error messages generally include the offending value, so a `ValidationError` on an email field writes that address to your logs at whatever sensitivity your log store has (M2-L18). Log the field name and error type, never the value. **A** is false. **B** is false. **D** is false and irrelevant — the risk is the error text, not the schema's capability. |

**Q13 rubric (5 marks).** One mark each for: **the hypothesis** — truncation, since the correlation with
long documents points at an output-length limit rather than a model quality problem; **the mechanism**
— a repair step (brace-balancing, or a lenient parser) is turning the truncated response into valid
JSON with a field missing or half-formed, so it fails silently rather than raising; **the one-query
confirmation** — count responses grouped by `finish_reason`, which should show ~2% not equal to a
natural stop, and cross-tabulate against document length; **the fix** — refuse any response whose
`finish_reason` is not a natural stop, remove the repair that invents structure, and raise the output
token limit or split the extraction into two calls; and **the prevention** — a required-field schema
plus a metric on `finish_reason` so the next occurrence is visible on a dashboard rather than in a
customer complaint. An answer that proposes "add a retry" without identifying truncation scores 1,
because retrying the same over-long request reproduces the same failure.

---

<a id="m5-l07"></a>
## M5-L07 — Output Validation and Repair Loops

**Answers: A · D · B · D · A · D · A · C · B · B · C · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | 0%, at 4.00 calls per request. The loop is not failing to help — it *cannot*, because the same prompt and schema produce the same rejection every time. **B** assumes feedback describes a fixable problem; a better description of an impossible requirement is still impossible. **C** is the belief that produces `while True`. **D** is a real knob that changes nothing here: no temperature invents an enum value that does not exist. |
| 2 | **D** | All six. Excellent for repair, a liability in a log — the invalid value is frequently a customer's email, name or free text. **A** inverts the default. **B** and **C** would make the risk selective and therefore easy to reason about; it is not. |
| 3 | **B** | A `missing` error has no single offending value, so pydantic reports the **whole object** — every field the model produced. The one error you would expect to be harmless leaks the most. **A** is false. **C** is false and important: `include_input=False` handles it exactly. **D** confuses a privacy property with a retry property. |
| 4 | **D** | 62 tokens against 243, no documentation URLs the model cannot visit, no values from the output. **A** is false — it names every broken field. **B** and **C** both assume a trade-off; there is not one, which is why this is the default to adopt rather than a compromise to weigh. |
| 5 | **A** | Three: 90% → 99% → **99.9%**. A fourth attempt buys 0.09 points, spent almost entirely on requests that were never going to succeed. **C** stops at 99%, which is a 1-in-100 failure rate. **B** and **D** are paying for a tail that is already gone — and, worse, are the attempts where systematic failures accumulate. |
| 6 | **D** | The mean is 1.11 because 90% of requests take one call; the 1-in-1000 takes four calls and four times the latency. **That is what p99 shows and users feel**, and it is invisible in a monthly total. **A** and **B** are false — the arithmetic covers full calls. **C** is a fair general remark that names no mechanism; the specific answer is the tail. |
| 7 | **A** | 52% — $83 of a $158 bill, against $75 for the other 98%. **C** is the intuition that makes the bug survive review. **B** understates by 5×. **D** overstates. Note how it presents: not as a cost alert but as a latency incident, because the same 2% hold connections open and fill the worker pool. |
| 8 | **C** | Count flat across attempt number, for a given field. If attempt 4 fails as often as attempt 1, no further attempt will help. **A** describes load, not a schema mismatch. **B** would be strange and is not the signature. **D** happens with both kinds. This is why the metric must carry field, error type **and** attempt — two of the three is not enough. |
| 9 | **B** | Latency and cost. Four attempts at 30 s each is a two-minute request, and the user left after ten seconds (M2-L14). **A** is the assumption behind most repair loops in production. **C** confuses a resource bound with correctness. **D** names one consequence of many. |
| 10 | **B** | Near-identical output, so the retry is a second bill for the first answer. **A** confuses reproducibility with reliability. **C** invents a mechanism. **D** is false — determinism does not imply schema compliance. If you must retry a deterministic failure, change something: the prompt, the schema, or the feedback. |
| 11 | **C** | Return the four, clearly labelled partial, when the caller can act on them — degradation is the most under-used of the four responses. **A** is the dangerous version of the same idea: partial data presented as complete is worse than an error (M2-L10). **B** discards useful work. **D** is the reflex to refuse — the failing bound may be the one stopping a £1M refund (M5-L06). |
| 12 | **C** | An expected outcome the caller handles — you wrote the budget, so reaching it is the design working. **A** turns a planned path into an exception, which callers then catch broadly and swallow (M2-L10). **B** defeats the bound. **D** makes a systematic failure invisible, which is the §6 incident. |

**Q13 rubric (5 marks).** One mark each for: **the hypothesis** — a repair loop spinning on a systematic
validation failure for a minority of traffic, which is exactly the shape of "normal mean, terrible p99,
doubled cost"; **why the mean looks normal** — the majority still succeeds in one call, so the average
barely moves while a small share consumes many calls each; **the confirming query** — group validation
failures by field, error type and attempt number, and look for a count that does **not** fall with
attempt (the §6 signature); **the immediate fix** — bound the loop by attempts, deadline and cost, and
return an escalation on exhaustion; and **the structural fix** — correct the schema or prompt that
cannot be satisfied (widening a reference list loaded from data rather than a hard-coded enum), plus an
alert on flat-across-attempts failure rate so the next occurrence is caught in an hour. An answer that
proposes only "add a retry limit" scores 2: it stops the bleeding and leaves 2% of requests failing
with no diagnosis.

---

<a id="m5-l08"></a>
## M5-L08 — Tool Definitions and Tool-Call Arguments

**Answers: A · C · B · C · D · A · D · B · D · C · A · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | All ten — including a £1,000,000 refund to another user's account in an unhandled currency. The schema is not careless; `user_id: str, amount: float` has the correct type for every field. **B**, **C** and **D** all assume type annotations constrain *values*, which is the belief this table exists to remove: a `str` accepts `../../admin`, and a `float` accepts a million. |
| 2 | **C** | Not having the parameter. No prompt can set a field that does not exist — the same move as parameterised SQL (M2-L16) and nonce delimiters (M5-L05), and each removes a capability rather than policing it. **A** is correct and weaker: it depends on your remembering to check, on every call, for ever. **B** is a prompt-level control against a residual measured at 37.8% in M5-L05. **D** detects after the money has gone. |
| 3 | **B** | Two: `extra="forbid"` rejects the field, and the function never reads one. **Neither reason depends on the model behaving**, which is what makes the attack impossible rather than unlikely. **A** names only the first and would leave you exposed the day someone relaxes the config. **C** credits the model with a refusal it did not make. **D** describes a control that runs after the refund. |
| 4 | **C** | 29 per 1,000 — £725 overpaid. The model, the schema and the arguments were all correct; the HTTP layer retried a call that had already succeeded (M2-L11: `POST` is not idempotent). **A** is the assumption behind most tool code. **B** miscounts: the timeout rate is 3%, and every timeout produced a duplicate. **D** misplaces the retry — it is your client, not the model. |
| 5 | **D** | The logical request: a ticket id, message id, or client-supplied request id. **A** is the trap: a retry that re-runs the model produces a new key and you pay twice. **B** has the same flaw one layer down — a fresh key per execution defeats the mechanism entirely. **C** is not stable across a retry and collides under concurrency. |
| 6 | **A** | 87.3% against 76.8%. Two confusable tools scored *worse* than ten well-separated ones, so the fix is not fewer tools but descriptions that cannot both be right for the same request. **B** reads the wrong row. **C** and **D** both deny the measured effect of overlap, which is the larger of the two factors at these sizes. |
| 7 | **D** | `run_sql`. Its blast radius is the union of every other tool's, and it grows every time someone adds a table — so no review of it is ever complete. **A**, **B** and **C** all name tools that ship perfectly well *with a gate*: an allow-list, session scoping, and human approval respectively. The distinction is not "dangerous" but "boundable". |
| 8 | **B** | A person is not subject to the injected instruction. It is the only control in the table that sits outside the system entirely, and therefore the only row whose worst case is not a number you are agreeing to accept. **A** describes a race that is not the mechanism. **C** confuses transport security with authorisation. **D** is the reasoning that leaves the tool ungated until the day it is called. |
| 9 | **D** | Untrusted content, delimited like any user input. Your code made the call; it did not write the response. **A** is the confused-deputy assumption. **B** is worse than it looks — a read-only tool that fetches a URL returns whatever that page says, and the page may have been written for your model. **C** validates shape, not intent: well-formed JSON can carry an instruction in a string field. |
| 10 | **C** | Integer minor units or `Decimal`. The lab passed `0.1 + 0.2` = `0.30000000000000004` through a `float` field — not 30 pence, and never will be (M2-L02). **A** is the default everyone writes. **B** moves the parsing problem downstream and invites locale bugs. **D** delegates a correctness decision to a schema dialect. |
| 11 | **A** | Nothing. It still reads the request, finds the order and proposes the refund — the whole job. **This is the point worth remembering**: least privilege is usually argued as a trade-off against capability, and here there was no trade. **B** confuses identifying the *order* (which it does) with asserting the *owner* (which it never needed to). **C** and **D** describe costs that did not occur. |
| 12 | **B** | Independent; sequence them yourself if order matters. **A** is an assumption with side effects — `cancel_order` and `issue_refund` arriving together is not a stated plan. **C** discards work the model intended. **D** is false and dangerous: the provider validates the schema's *shape*, never whether the call is permitted. And whatever you assume, cap the number per turn in code. |

**Q13 rubric (5 marks).** One mark each for: **`SELECT`-only is not a bound on blast radius** — a read
can exfiltrate every customer record in the database, and the damage from a read is not smaller than a
write, only quieter; **the schema is unboundable** — a free SQL string has no pattern, enum or range you
can validate, so every control must be a filter on an infinite space, and its blast radius grows with
every table anyone adds; **denial of service and cost** — an unbounded query can lock tables, exhaust
connections or run for hours, which `SELECT` permissions do not prevent; **what to build instead** — a
small set of named, parameterised query tools (`search_orders(status, date_range)`), each scoped to the
session's user, each with bounded result sizes, so the model chooses *which* question and your code
owns *how* it is asked; and **the general rule** — a tool whose worst case is "anything the schema
allows" is not exposed to a model, however narrow the database grant. An answer that only says "SQL
injection" scores 1: the model is authoring the SQL by design, so injection is not the failure — the
absence of any bound is.

---

<a id="m5-l09"></a>
## M5-L09 — Streaming and User Experience

**Answers: B · C · B · C · D · A · A · D · B · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Total time is identical in every row of the lab's table; streaming moves the wait, it does not remove it. **A** is the claim that gets streaming proposed as a fix for a latency problem it does not solve. **C** is backwards — you are billed for what was generated whether or not it is displayed or read. **D** confuses delivery with context. |
| 2 | **C** | Large chunks and ASCII fixtures make the bug invisible in testing, so it ships and surfaces as mojibake for users writing in languages the tests do not contain. **A** treats a coincidence as a configuration — you do not control where the network splits chunks. **B** is false: 64 bytes happened to align here, and nothing guarantees it. **D** blames the library for the caller's use of it. |
| 3 | **B** | It flushes bytes the decoder is holding and raises on a truncated sequence. Without it a stream ending mid-character loses that character **silently**, which is the harder bug to find. **A** is the assumption that omits it. **C** and **D** describe operations it does not perform. |
| 4 | **C** | 100%. A JSON object is not valid until its closing brace, so there is no prefix at which you can validate and none at which you can act. **A** and **B** assume validity is gradual. **D** is the most tempting: field order changes *when the bad value appears*, not when the object becomes parseable. |
| 5 | **D** | Character 132. The bad field was the very first thing in the response, and a bound or an enum is only meaningful once the object is complete — a partial parser reporting a half-arrived value answers a different question. **A** is what a partial parser tempts you into. **B** invents a midpoint. **C** overstates: you can validate perfectly well, just not before the user has seen it. |
| 6 | **A** | 0.36 s against 21.82 s. **B** is false — TTFT is constant, which is exactly why the *benefit* grows with length. **C** quotes the reading-time column. **D** describes the total-time column, not the improvement. This ratio is the whole argument for when streaming is worth its complexity. |
| 7 | **A** | At 11× the reading speed the user is reading, not waiting, so further generation speed buys nothing. **B** and **C** are the wrong conclusions from the right observation — the experience is good; it is the *optimisation target* that has moved. **D** inverts it: the model has stopped being the bottleneck. |
| 8 | **D** | A tool call. By the time you have seen enough of it to know what it does, you have shown the user an action you may be about to refuse (M5-L08). **A**, **B** and **C** are all prose whose worst case is that the user reads something they must be told to disregard — bad, and not the same as displaying an action. |
| 9 | **B** | Billed for what was generated, and usually missing from your metrics because the usage event never arrived. **A** and **C** describe a refund policy no provider offers. **D** is the assumption that makes the gap invisible. Note the direction: your dashboard always under-reports, never over-reports, and the gap widens exactly when things are going badly. |
| 10 | **D** | Carry the error inside the stream. Your status was committed with the first chunk, so **A** is not available. **B** leaves the client unable to distinguish failure from a complete short response — the same "empty must not look like failed" rule as M2-L10. **C** is worse: continuing a stream after a silent retry can duplicate or contradict what was already shown. |
| 11 | **C** | The prose asserted an outcome the system had not authorised. The model was not wrong — £940 for a duplicate £940 charge is correct — and the policy lived in code the model could not see, applied after the user was told otherwise. **A** blames a hallucination that did not occur. **B** treats a policy as a bug. **D** blames the transport for a design decision. |
| 12 | **A** | Stream the explanation, buffer the decision — the user gets progress, your code still validates before anything is acted on. Best of all, generate the prose *from* the authorised outcome so it cannot contradict it. **B** discards the benefit where it is largest. **C** is the §6 incident. **D** confuses an authorisation control with a presentation one. |

**Q13 rubric (5 marks).** One mark each for: **the arithmetic** — at 30–60 tokens streaming moves the
wait by roughly 0.4–1.1 s, which is below the threshold at which users notice, so it will not resolve
the complaints; **naming the real question** — "slow" at that length is TTFT, not generation, so the
investigation is time-to-first-token and everything before the model call (retrieval, auth, cold
starts, queueing); **the cost side** — streaming brings incremental decoding, in-stream error handling,
idle timeouts, disconnect cancellation and uncounted usage, all for a benefit measured in fractions of
a second; **what you would measure instead** — the p50/p95 breakdown of end-to-end latency by stage, to
find where the seconds actually are; and **the case where they are right** — if some responses are long,
enable streaming for those, and stream the prose while buffering any decision (§6). An answer that
simply says "streaming doesn't help" scores 2 without the measurement plan; an answer that agrees to
stream everywhere scores 0.

---

*Further lessons are added to this key as Module 5 is written.*
