# Module 5 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 5 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M5-L01 Anatomy of a Prompt | [↓](#m5-l01) |
| M5-L02 Message Roles | [↓](#m5-l02) |
| M5-L03 Few-Shot | [↓](#m5-l03) |
| M5-L04 Decomposition | [↓](#m5-l04) |
| M5-L05 Delimiters | [↓](#m5-l05) |
| M5-L06 Structured Output | [↓](#m5-l06) |
| M5-L07 Validation and Repair | [↓](#m5-l07) |
| M5-L08 Tools | [↓](#m5-l08) |
| M5-L09 Streaming | [↓](#m5-l09) |
| M5-L10 Conversation State | [↓](#m5-l10) |
| M5-L11 Context Engineering | [↓](#m5-l11) |
| M5-L12 Prompt Versioning | [↓](#m5-l12) |
| M5-L13 Prompt Injection | [↓](#m5-l13) |
| M5-L14 Refusals and Fallback | [↓](#m5-l14) |
| M5-L15 Token Accounting | [↓](#m5-l15) |
| M5-L16 Caching and Routing | [↓](#m5-l16) |
| M5-L17 Provider Portability | [↓](#m5-l17) |
| M5-L18 Evaluation Dataset | [↓](#m5-l18) |

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

<a id="m5-l10"></a>
## M5-L10 — Conversation State: What You Store and What You Resend

**Answers: B · C · A · D · B · A · C · D · A · C · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Your application resends the prior turns on every request; the model itself retains nothing (M4-L16). **A** and **C** describe server-side persistence no provider gives you by default. **D** confuses fine-tuning, a slow offline process, with a live conversation. |
| 2 | **C** | About 43× (16,180 / 380 in the lab's table). **A** and **B** understate it by an order of magnitude. **D** would be true only if cost scaled with turn number directly, which it does not — turn 80's *own* message is the same size as turn 1's; only the history dragged behind it grows. |
| 3 | **A** | Each turn adds a fixed amount to history, and every later turn resends that addition again — so the total is a sum of a growing series, which is quadratic in the turn count. **B** is false in the lab's setup: each message is a fixed size. **C** and **D** invent mechanisms that are not what the table measures. |
| 4 | **D** | 7.5× smaller, and the smaller version is a summary someone wrote, not a lossless transform — the ratio is both the saving and the omission in one number. **A** ignores that a chosen sentence cannot contain everything the transcript did. **B** overclaims — §5.4 shows exactly the cases where a summary-sized record fails. **C** describes overhead in the wrong direction; the state record is smaller, not larger, than the transcript. |
| 5 | **B** | A schema bounds what structured state can omit; you know in advance which fields it does not track. A prose summary's omissions depend on what the summarizer happened to judge unimportant on a given run. **A** ignores that difference in predictability, which is the entire point of comparing them. **C** and **D** are not supported by the lab — both scored 7 of 12. |
| 6 | **A** | The lab's own table: 12 of 12 answered, and simultaneously flagged over the 4,000-token budget — informational completeness and affordability are independent axes. **B** is the belief the table exists to correct. **C** and **D** dodge the trade-off rather than naming it. |
| 7 | **C** | Store is what your database retains for audit, support and analytics; send is what goes into the next request's context — and §5.6's table shows rows (structured state, summaries) where the answer is "yes" to both and rows (full transcript, tool arguments) where it differs. **A** and **D** collapse a distinction the lesson exists to keep separate. **B** is simply wrong — the two answers frequently diverge for the same row. |
| 8 | **D** | A summary derived from the deleted message still contains what it summarised, until the summary itself is regenerated or edited. **A** and **C** assume deletion propagates automatically, which it does not without deliberate cascade logic. **B** overstates — deletion absolutely can be honoured; it just has to reach every derived copy, not only the source row. |
| 9 | **A** | Without a version tag you cannot later reproduce or explain why a stored summary says what it says — the same reproducibility argument M5-L12 makes for prompts generally. **B** invents a provider requirement. **C** confuses versioning with compression. **D** overstates what versioning does — it makes hallucination explicable after the fact, not impossible. |
| 10 | **C** | 38 times — every turn from turn 3 through turn 40 resends the full history, and turn 3's content is part of that history for all of them. **A** and **D** ignore that full resend means *every* prior turn travels with *every* later request. **B** quotes the conversation-wide average (20.5×), not the specific count for a message sent early. |
| 11 | **D** | The state was keyed by a ticket number the helpdesk platform reissued, fetched on key match with no check that it belonged to the current customer. **A** blames a hallucination that did not occur — the model reported the record accurately. **B** invents an attacker where the customer did nothing. **C** misattributes the bug to summarisation, which was not in use in this scenario. |
| 12 | **B** | Key by a stable, verified identity; check ownership on every read; make deletion cascade from one source of truth. **A** treats the symptom (the data format) rather than the cause (no ownership check), and a leaked summary is just as bad as a leaked structured record. **C** discards the feature rather than fixing the bug. **D** is a real control against a different threat (data at rest) and would not have stopped a correctly-authorised lookup at the wrong key. |

**Q13 rubric (5 marks).** One mark each for: **the cost argument** — full-history resend forever grows
the bill quadratically with conversation length and will eventually exceed the context window outright,
which "never losing anything" does not prevent, it only delays; **store vs send are separable** — keep
the full transcript in your database with a retention policy (that *is* "never losing anything," for the
record that matters) without resending all of it on every request; **naming a strategy** — a sliding
window, a rolling summary, or structured state, chosen against the actual questions users ask, not
against a vague fear of forgetting; **the honest trade-off** — any strategy short of full resend loses
*something*, and the choice should be made deliberately by checking what a workload actually needs (as
§5.4 does with twelve concrete questions), not avoided by pretending resending everything has no cost;
and **a boundary case** — sensitive data typed early in a full-resend conversation is retransmitted on
every later turn regardless of any later redaction, which "keep everything, forever" makes worse, not
safer. An answer that only says "it's too expensive" scores 2, without a concrete alternative and without
naming the store/send distinction.

---

<a id="m5-l11"></a>
## M5-L11 — Context Engineering: Summarization, Truncation, Budgets

**Answers: B · C · D · A · B · D · A · C · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Ten turns is not a fixed amount of text, so "every 10 turns" is a token-count trigger wearing a turn-count disguise — the lab measures an 8× spread between a chatty and a verbose profile under the identical rule. **A** invents a bug where there is a modelling error. **C** is not stated or needed to produce the gap. **D** is the opposite of what the section demonstrates. |
| 2 | **C** | A cascading pass summarises the previous summary, so a fact must survive every pass since the start to still be present — loss compounds multiplicatively. **A** describes a different resource limit. **B** contradicts the mechanism: passes are not independent, which is exactly why the effect compounds. **D** is not part of the model. |
| 3 | **D** | Checkpoint-3 read about 5× the tokens cascade did over the same 12 passes, because a checkpoint pass re-reads the growing transcript rather than a short summary. **A** ignores the lab's own cost table. **B** and **C** describe effects the mechanism does not have. |
| 4 | **A** | Across the three scenarios, document count fell from 10 to 3 before the conversation-state strategy downgraded to structured state — an explicit, decided-in-advance order. **B** and **D** are the components marked never-drop in the same budget. **C** is also never-drop; dropping it would remove the model's ability to answer at all. |
| 5 | **B** | Refuse, and state both numbers — the same principle M4-L06 established for a system prompt, generalised to the whole fixed set. **A** and **C** are the exact silent-truncation failure the lesson argues against — cutting a component marked never-drop is a worse failure than a declined request. **D** hides the problem instead of surfacing it. |
| 6 | **D** | A feature's enabled/removed status is a two-valued fact, changed at a specific point, and consequential if wrong — precisely what §5.4 says belongs in structured state. **A**, **B** and **C** are narrative, aggregate impressions with no single "still true or not" value to get wrong. |
| 7 | **A** | The summarizer, instructed to keep summaries brief, compressed "added, then removed" down to "added" in a single pass — a systematic bias toward the shorter, positive clause, not a multi-pass decay. **B** blames a hallucination that did not occur — the removal genuinely happened. **C** did not occur; the window was never the constraint here. **D** contradicts the scenario as stated. |
| 8 | **C** | Real failures tend to be systematic — the same clause shape dropped every time — which is worse in one sense (repeatable) and better in another: reading the summarization prompt can find and fix it, unlike a genuinely random loss. **A** overstates and gets the direction wrong. **B** and **D** are not claims the lesson makes. |
| 9 | **D** | p90 means at least 10% of conversations reach or exceed that length, and 22 turns exceeds the 15-turn trigger point — so at least that 10% fires it. **A** misreads what a percentile is. **B** confuses the maximum with the 90th percentile. **C** inverts the definition of p90. |
| 10 | **B** | Checkpointing periodically regenerates the summary from source rather than from the last summary, which bounds drift at a measured 3–5× token cost. **A** is false — a checkpoint pass is defined by re-reading source. **C** is not part of the mechanism. **D** is backwards: checkpointing is consistently more expensive than cascading. |
| 11 | **C** | Any fact whose value is "still true or not" belongs in structured state, because prose compression fails exactly where the negation is. **A** overstates — rolling summaries remain useful for narrative, aggregate content. **B** and **D** are cost-blind absolutes the lesson explicitly argues against; the interval is a dial, not a fixed rule. |
| 12 | **A** | An explicit priority order, decided in advance and applied consistently, is what makes a budget's behaviour predictable under pressure. **B**, **C** and **D** all describe an order nobody chose on purpose, which is precisely the failure mode M4-L06 and this lesson both warn against. |

**Q13 rubric (5 marks).** One mark each for: **diagnosing before changing anything** — pull the raw
transcript around the reversal and compare it to what the current summary claims, to confirm this is
compression drift and not a different bug (a lookup keyed wrong, or the summary simply never being sent);
**naming the systematic cause** — read the actual summarization prompt for the instruction (commonly
"keep it brief") that biases compression toward dropping a qualifying or negating clause, as in §6;
**the structural fix** — move status-type facts ("is this still true") into structured state so they
cannot be silently reworded, and/or add checkpoint resummarization at a deliberately chosen interval so
no single compression error survives unchallenged indefinitely; **the prompt fix** — since the failure is
systematic, rewrite the summarization instruction to preserve reversals and negations verbatim rather
than compressing them away; and **verifying without waiting six weeks** — replay the real (or a
reconstructed) historical transcript through the fixed pipeline offline and confirm the reversal now
survives to the present turn, i.e. a regression test built from the incident itself, not a wait for new
traffic to reach the same distance. An answer that only proposes "summarise less aggressively" without a
verification step scores 2.

---

<a id="m5-l12"></a>
## M5-L12 — Prompt Versioning and Regression Testing

**Answers: A · D · B · C · A · D · B · C · A · D · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Template, model, parameters and tool schema together — anything that can change what the model does belongs in the artefact. **B** and **C** each name one field and miss the others §5.1 shows also move behaviour. **D** ties the definition to a review artefact (a git diff) rather than to what actually affects output — precisely the assumption §6's incident shows failing. |
| 2 | **D** | Exact-match fails every correct answer that happens to be formatted differently from the one stored string, which is why a prompt that is truly right 95% of the time still scored 67%. **A** blames the model for a grading-method artefact. **B** dismisses a number the lab computed from 320 real simulated draws. **C** is not what the scenario describes — the golden set's expected categories were correct; the assertion type was wrong. |
| 3 | **B** | A property assertion checks a stated rule — "is the category right" — independent of exact wording, which is why it tracked true quality far more closely than exact-match in §7.2. **A** describes exact-match itself. **C** and **D** name concerns this lesson does not test for. |
| 4 | **C** | 19% false-alarm and 63% catch rate together mean the suite is unreliable in both directions at once — not evidence a gate should act on. **A** is the mistake the section exists to correct. **B** misreads a sampling-noise problem as a threshold-tuning problem. **D** misreads a gate's error rate as the prompt's own regression rate — two different quantities. |
| 5 | **A** | Measured exactly: false alarms fell to 5%, catch rate rose to 98%, at 10 samples/case. **B** and **C** contradict the lab's own table. **D** is wrong — both numbers moved together as samples increased. |
| 6 | **D** | The fingerprint payload includes model, temperature, max_tokens and tool schema alongside the template, so it changes even when the template does not. **A** invents nondeterminism in a pure hash function. **B** names a real difference between the two artefacts, but the version *string* is not part of the fingerprint's input — the model and max_tokens fields are what actually move it. **C** overclaims; two artefacts sharing every field would share a fingerprint. |
| 7 | **B** | A text-diff gate reports nothing when the template is unchanged, so the golden suite never runs — exactly what shipped v3 in §6 unexamined. **A** describes the correct behaviour, which the scenario is built to show failing. **C** and **D** describe actions a text-diff gate, by construction, cannot take, since it never even detects the change. |
| 8 | **C** | If a field can change the output, it is part of the version — model, parameters and tool schema included, with no "just config" exception. **A** overcorrects into never changing anything. **B** is the exact belief that produced §6's incident. **D** inverts the purpose of a gate, which exists to catch a regression *before* it ships. |
| 9 | **A** | Rollback means pointing at a previously kept version; output attribution means tagging a result with the version that produced it — both require that version to still exist, not merely be remembered. **B** gets the trade-off backwards; keeping versions costs storage precisely because it buys this. **C** invents a requirement no provider imposes. **D** confuses the fingerprint (a way to detect a change) with the retained artefact itself (what you roll back to). |
| 10 | **D** | Exact-match is appropriate exactly where byte-identical output is genuinely required, such as a fixed enum value — not where any legitimate variation in wording exists. **A** and **B** are the cases §7.2 shows exact-match handling badly. **C** names an unrelated setting. |
| 11 | **C** | The lab states its own numbers are illustrative of a method — simulate your own quality gap and threshold, then read off your own samples/case. **A** and **B** overclaim generality the lab explicitly disclaims. **D** is not a limitation the scenario or the method imposes. |
| 12 | **B** | A tool schema change alters what the model can do just as a wording change does, so it belongs in the same fingerprint and the same gate (M5-L08). **A** and **D** exempt exactly the kind of change §5.1's fingerprint is built to catch. **C** invents a dependency between two independent fields. |

**Q13 rubric (5 marks).** One mark each for: **naming the real risk** — "watch production closely" only
catches a regression after real users have already been served the worse version, and with no golden
suite there is no pre-deploy signal and often no fast way to confirm *what* changed once a problem is
noticed; **the minimum suite** — a small golden set (even 5–10 cases) covering the task's main categories
or outcomes, checked with property assertions rather than exact-match; **sizing it** — enough samples per
case that a real regression is more likely to be caught than missed, per §5.3, rather than a single
untested run; **tying it to the gate** — the suite must actually block or flag a deploy on an artefact
fingerprint change, not just exist as a script someone can choose to run; and **conceding the trade-off
honestly** — a minimal suite is cheap and worth insisting on before shipping, even though it will not
catch everything "watching production" eventually would. An answer that says only "we need tests" without
sizing them or connecting them to a gate scores 2.

---

<a id="m5-l13"></a>
## M5-L13 — Prompt Injection: Attack Catalogue and Real Defences

**Answers: A · B · C · D · A · B · C · D · A · B · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | A payload riding in a retrieved document is indirect injection — it never passed through the user's own message. **B** misapplies the term to content the user did not author. **C** denies the definition given in §2 for the sake of a technicality; injection is defined by mechanism (instruction-shaped content being followed), not by who typed it. **D** confuses an attack category with a detection tool. |
| 2 | **B** | Keep the filter as one layer, and pair it with controls that do not depend on recognising payload text at all — the lesson's stated conclusion, and the reason §5.6's stack has more than one row. **A** overreacts to a real limitation. **C** ignores that the cheapest bypass measured needed no encoding at all. **D** is false — §7.1's "plain" variant was direct, and the filter caught it fine; the failure was specifically against obfuscated forms. |
| 3 | **C** | A canary in the output proves the system prompt containing it was disclosed — that is the entire and exact claim it supports. **A** and **B** overreach into claims about future behaviour a single detection cannot support. **D** assumes a specific source the canary's presence does not establish. |
| 4 | **D** | A discount approval, however it was produced, is text that was never going to contain the canary string — so detection sits at zero regardless of the true compliance rate, which is exactly what the lab measured at 30%, 60% and 90%. **A** dismisses a result the simulation reproduces at every rate tested. **B** confuses "the canary can't see it" with "it is safe." **C** contradicts the table — the 90% row shows the same zero as the 30% row. |
| 5 | **A** | Keep the filter as one layer and add controls — like action gates — that do not depend on recognising the payload's text at all, since text-based recognition is exactly what obfuscation defeats. **B** discards a real, if partial, layer. **C** repeats Q4's mistake — a canary does not cover this class of harm. **D** is not established anywhere in the lesson; filters are weak against obfuscated forms of *any* category, not indirect specifically. |
| 6 | **B** | A brevity-tuned summarizer keeps short, confident, unqualified statements best — which is exactly the shape of a typical injected claim, and exactly why the hedge that would flag it as unverified is what gets compressed away first (M5-L11 §6). **A** invents a property injected claims do not have. **C** denies that the lab's chosen parameter is a modelling choice motivated by a real mechanism, not an error. **D** is not a claim the lesson makes or needs. |
| 7 | **C** | A pipeline that never re-screens its own summary lets a claim resurface as settled fact long after the untrusted content that produced it is gone from any re-screened window — precisely §6's incident. **A** and **B** both overclaim protection the described pipeline does not have. **D** contradicts the entire mechanism §5.4 describes. |
| 8 | **D** | The exact hostname carried the trusted domain as a genuine substring, which is why exact, parsed-host comparison — not substring containment — is required. **A** overgeneralises into banning a whole class of valid configuration. **B** is not achievable and not what the fix does. **C** is not a distinction the lesson draws; either content type can carry a URL. |
| 9 | **A** | `"ourcompany.com"` literally appears inside `"support.ourcompany.com.attacker.example"` as a substring, which is exactly why a substring check passes it. **B** is false — the operator works fine; it is simply the wrong check for this purpose. **C** is false; it is a syntactically valid hostname, which is the whole problem. **D** is an unrelated claim about performance, not correctness. |
| 10 | **B** | Each layer covers a different blind spot, so no single point of failure defeats the whole stack — a canary's blindness to Goal B is covered by an action gate, not by another canary. **A** would leave every layer sharing one blind spot. **C** is not a claim the lesson makes. **D** contradicts §5.6's entire premise, including the point that an outer filter is the one most easily bypassed (§5.2). |
| 11 | **C** | The tool result's untrusted status was not carried through summarisation, so an unverified claim became an asserted fact with no gate on the resulting action — all three defects in §6's table trace back to this. **A** invents a hallucination where the content genuinely existed in the notes. **B** misclassifies an indirect (tool-result) injection as direct. **D** is not part of the scenario as given. |
| 12 | **D** | Because instructions and data share one channel with no hard boundary, no single control eliminates injection — the lesson's stated central thesis, and the reason the whole lesson is about layered risk management rather than a fix. **A** contradicts M5-L05's own finding that a boundary helps with confusion but not compliance. **B** is false — §6 is built entirely around an indirect case, and direct injection is not "easily prevented" either. **C** repeats the mistake Q4/Q5 already ruled out. |

**Q13 rubric (5 marks).** One mark each for: **naming what the stack covers** — a keyword filter catches
unobfuscated direct attempts, and a canary catches system-prompt leakage specifically; **naming a class it
misses** — any indirect or stored injection whose payload is even lightly obfuscated or reworded, and any
harmful action (like a data change or an approval) that never touches the canary at all, per Goal B in
§7.2; **the concrete gap** — the colleague's stack has no defense against a tool-result-borne instruction
that gets folded into a summary and reactivated turns later, and no control at all on the action itself;
**the one layer to insist on first** — a gate on irreversible or high-value actions (M5-L08), independent
of how the model was persuaded to propose them, because it is the layer that still holds when every
upstream control has failed; and **framing it as risk management, not closure** — stating plainly that no
combination of these layers makes the system immune, only bounds the damage. An answer that only says
"add more filters" without naming the action-gate layer scores 2.

---

<a id="m5-l14"></a>
## M5-L14 — Refusals, Errors and Fallback Behaviour

**Answers: C · A · D · B · A · C · D · B · C · A · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | The two flagged samples were about billing and HR policy — genuinely legitimate content that happened to use "unable to," which is also a refusal marker. **A** invents a bug that is not present; the detector matched exactly as coded. **B** describes the opposite of what happened. **D** is not true of the samples as given. |
| 2 | **A** | An empty response and an infra error are their own failure classes, needing their own checks — neither is "the model refused." **B** collapses distinctions the lesson exists to keep separate. **C** misclassifies both as refusals, which they structurally are not. **D** confuses this with M5-L07's schema-validation failures, a different surface entirely. |
| 3 | **D** | A refusal is close to the model's stable, repeatable answer, so an identical re-ask mostly reproduces it; a timeout is closer to noise around an otherwise-reachable right answer, so retrying resolves it. **A** invents a fault in the wrong component. **B** is not established anywhere in the lesson. **C** dismisses a clean, exact table the lab computed. |
| 4 | **B** | Change something material — the prompt, the context, the offered alternative — or escalate; repeating the identical request mostly just re-spends budget for the same ~3%/attempt return. **A** and **D** apply M2-L14's transient-failure playbook to a failure §5.2 shows does not behave like one. **C** doubles down on a strategy the lab's own numbers argue against. |
| 5 | **A** | Short-circuiting locally after the trip is exactly what turned 18,000 wasted attempts into 8 in §7.3. **B** would make an outage's cost worse, not better. **C** describes a different technique (caching) not discussed here. **D** overstates the mechanism — users still get a fallback response, not a block. |
| 6 | **C** | Every one of the 6,000 users got a response in both scenarios in §7.3; the breaker changed where it came from and how fast, not whether it arrived. **A**, **B** and **D** all misread a lab result that explicitly states this. |
| 7 | **D** | The detector missed a real refusal with no marker phrase and flagged legitimate content sharing the same words — errors in both directions, the same shape M5-L13 found for injection filters. **A**, **B** and **C** name limitations the lab's actual detector does not have (it is pure string matching, language-agnostic within its own logic, and fast). |
| 8 | **B** | It is a parallel classification for a different surface — what came back from the model or the transport, prior to and separate from whether output validates a schema. **A** and **C** collapse two genuinely different questions into one. **D** is not correct; refusals and infra errors can occur with no repair loop involved at all, e.g. on the very first attempt. |
| 9 | **C** | "I don't have the ability to browse the internet" contains none of the detector's listed phrases, despite being a functional refusal — exactly the false-negative §7.1 reports. **A** contradicts the stated ground truth. **B** overclaims a limit specific to this detector as a limit of all methods. **D** is factually wrong about the sample. |
| 10 | **A** | A half-open breaker sends a limited probe to test recovery before committing to full traffic again — the state that makes recovery detection safe rather than all-or-nothing. **B** skips the caution half-open exists to provide. **C** describes a breaker that never recovers automatically, which is not the pattern described. **D** denies that recovery is possible at all. |
| 11 | **B** | Most of a refusal-retry budget buys almost no additional chance of success, because the outcome is close to a fixed decision rather than noise — exactly §7.2's 14%-after-5-attempts result. **A** invents a pricing difference the lesson does not claim. **C** is the opposite of what makes a timeout worth retrying. **D** invents an unrelated budget with no basis in the lesson. |
| 12 | **D** | Match the response to the failure class — the lesson's single organizing idea, restated. **A** is the exact mistake §6's incident made. **B** overgeneralises a case-by-case judgement (§5.4) into an absolute. **C** contradicts §7.3's entire result. |

**Q13 rubric (5 marks).** One mark each for: **naming the three classes** — infrastructure error, policy
refusal (or capability limit), and a sustained outage all currently collapse into one message; **the
concrete harm for each** — infra errors get a lucky-but-unexplained retry, refusals get repeated
identically for a near-zero return while the user concludes the bot is broken, and a real outage turns
into a retry storm that extends its visible impact past its actual duration; **prioritising one fix** — a
reasoned choice of which to fix first (commonly the circuit breaker, since an unbounded outage has the
largest blast radius, or refusal handling, since it directly damages user trust); **grounding the choice
in a number** — reference to a concrete measure such as §7.2's or §7.3's rates rather than a general
impression; and **not proposing one new generic message to replace the old one** — recognising that the
fix is classification into at least three paths, not a better single sentence. An answer that proposes
only "write better error messages" without classifying the failures first scores 2.

---

<a id="m5-l15"></a>
## M5-L15 — Token Accounting and Cost Calculation

**Answers: B · D · A · C · D · B · C · A · C · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Below the break-even ratio, output dominates cost regardless of which block looks longer — §7.1's own example is a 2,000-token prompt with a 400-token answer already at 44% output cost. **A** and **D** contradict the entire point of the section. **C** invents a rule with no basis. |
| 2 | **D** | The cached region must be byte-identical to a prior request; anything variable placed before it — a timestamp, a request id — means it never matches, so every request misses. **A**, **B** and **C** name conditions that do not affect prefix matching at all. |
| 3 | **A** | A blended rate is exact only for the input:output shape it was computed from — zero error there is definitional, not lucky. **B** contradicts §7.3's own table, which shows +49% and −57% errors on the other two rows. **C** and **D** invent conditions the lesson does not establish. |
| 4 | **C** | Averaging a cheap input price and an expensive output price into one number necessarily overprices input-heavy work and underprices output-heavy work — the mechanism, not a coincidence. **A** invents a tokenizer inconsistency that does not exist. **B** is not how any pricing described here works. **D** dismisses an exact, reproducible calculation as noise. |
| 5 | **D** | A small share of long, expensive requests that a short-conversation sample structurally cannot contain — measured at a 4.8× underestimate, with the top 10% of traffic driving most of the gap. **A**, **B** and **C** invent causes the scenario does not involve. |
| 6 | **B** | Later requests pay the discount rate on the cached portion instead of full input price — the entire mechanism. **A** confuses input caching with output token count, which caching does not touch. **C** overstates; the prefix is still sent, just priced differently. **D** is not how token pricing works in either direction. |
| 7 | **C** | At exactly the break-even ratio the two halves cost the same; below it (relatively more output), output costs more — the definition given in §5.1. **A** and **D** invent rules about limiting or zeroing costs that are not implied by a break-even ratio. **B** conflates two unrelated mechanisms. |
| 8 | **A** | It silently assumes one specific mix and is wrong, in opposite directions, for anything else — §7.3's exact result. **B** is false; the estimate undercharges output-heavy work in the same table. **C** is not true; it is pure arithmetic on token counts. **D** misdescribes what a blended rate covers. |
| 9 | **C** | A miss simply reverts to full price with no distinct signal — that silence is exactly why it is dangerous. **A**, **B** and **D** invent detection or compensation mechanisms the lesson does not describe. |
| 10 | **B** | Build the forecast from a sample that actually contains your long tail, not from short, hand-tested conversations. **A**, **C** and **D** are overreactions the lesson does not recommend — the fix is a better sample, not abandoning testing or rejecting long conversations outright. |
| 11 | **A** | The cache must be written before it can be read from — there is no discount to apply on the very first occurrence of a prefix. **B**, **C** and **D** invent rules about timing or thresholds that are not part of the mechanism as described. |
| 12 | **D** | Track input, output and cache-hit cost as three separate quantities — the synthesis of every section in the lesson. **A**, **B** and **C** each repeat a mistake the lesson spent a section correcting. |

**Q13 rubric (5 marks).** One mark each for: **naming the sample-size problem** — 20 manually-run
conversations are very unlikely to contain the long-tail requests that dominate real cost, per §5.4's
4.8× result; **naming the blended-rate problem** — a single $/token figure is only exact at the shape it
was built from, and the 20-conversation sample may not even represent that shape correctly; **what to ask
for instead** — a forecast built from logged production-shaped data (even a rough percentile bucketing,
§5.4), or, absent that, treating the manual estimate explicitly as a floor rather than a plan; **a
concrete next step** — instrumenting per-request cost logging now so that within a short window there is
real data to forecast from; and **not rejecting budgeting outright** — the critique should improve the
estimate, not argue that cost cannot be forecast at all. An answer that only says "that number seems too
low" without naming the long-tail mechanism or proposing an alternative scores 2.

---

<a id="m5-l16"></a>
## M5-L16 — Caching and Model Routing

**Answers: A · C · D · B · C · A · D · B · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | A higher hit rate is not a free upgrade — 50 of the extra 250 hits were wrong, and a wrong hit is worse than a miss because it delivers an incorrect answer with a cache's apparent confidence. **B** ignores the defect the same section measures. **C** overreaches; exact-match remains the safer choice wherever a wrong answer is costly. **D** is false — the wrong hits arose from correct, intended cache behaviour operating on genuinely similar-but-different queries. |
| 2 | **C** | Neither a wrong semantic hit nor a misrouted request raises an error — both revert to something that looks like normal operation unless specifically instrumented for. **A** and **D** invent conditions not established anywhere in the lesson. **B** is false; correctly-routed and correctly-cached requests are cheaper, not more expensive, than doing nothing. |
| 3 | **D** | Higher accuracy means fewer hard requests land on the cheap model and require a costly fallback, and fewer easy requests land on the expensive model and overpay — both effects reduce total cost as accuracy rises. **A** and **C** invent mechanisms unrelated to routing accuracy. **B** contradicts the lab's own prices, which never go to zero. |
| 4 | **B** | Below 60.4% accuracy in this lab's specific setup, the routed total exceeds the always-expensive baseline — exactly what the table and the closed-form calculation both show. **A** misreads a cost threshold as a routing rule. **C** confuses two independent lab sections. **D** overgeneralises a result computed for one specific price and traffic mix into a universal constant. |
| 5 | **C** | A misrouted hard request pays for the failed cheap attempt AND the expensive fallback that corrects it — double payment. A misrouted easy request just pays the (higher) expensive price once, for a correct answer. **A**, **B** and **D** invent billing rules not present in the model. |
| 6 | **A** | A cache hit means no model call and no need for a routing decision at all — classifying first spends money on a decision that turns out to be irrelevant. **B**, **C** and **D** invent effects or rules the lesson does not establish; §7.3 measures a pure cost effect, not a latency-only one. |
| 7 | **D** | A higher cache hit rate means more requests are, in the wrong order, classified before ever reaching a cache check that would have made classification unnecessary — so the waste scales up with hit rate, not down. **A** has the direction backwards. **B** and **C** describe changes unrelated to the mechanism being priced. |
| 8 | **B** | The easy request still gets a correct answer — it simply cost more than the cheap model would have charged for the same correct answer. No fallback is needed because nothing failed. **A** and **C** invent a failure that did not occur. **D** contradicts the whole premise of an "expensive" tier costing more per token. |
| 9 | **A** | The lesson explicitly flags this as a real, unmeasured quality risk on every hard request, not a cost figure — cheapness in dollars says nothing about correctness. **B** and **C** invent constraints not present. **D** confuses a strategy that ignores routing entirely with one that could violate a routing-specific calculation. |
| 10 | **D** | Routing is a decision made before any model call, using accuracy computed in advance; M5-L14's material addresses what to do once a request has already failed or been refused. **A** and **C** deny any relationship the lesson explicitly draws. **B** is false — the application, not the model, makes the routing decision. |
| 11 | **B** | The lesson's central, computed result: build a router only once its measured accuracy is confirmed to clear the specific break-even bar for your own prices and traffic. **A** is the mistake §6's incident makes explicitly. **C** and **D** are not claims the lesson supports — caching and routing are shown working together, and price is central to the whole analysis. |
| 12 | **C** | An unmeasured ~55%-accurate classifier shipped below the system's own 60.4% break-even point, so misrouted hard requests' double-payment outweighed the savings on correctly-routed easy ones. **A**, **B** and **D** invent causes the scenario does not describe — the incident is entirely explained by §5.2's arithmetic once the real accuracy is known. |

**Q13 rubric (5 marks).** One mark each for: **naming the skipped assumption** — "even a rough classifier
should save money" assumes routing is always net-positive, when §5.2 shows it has a specific break-even
accuracy below which it is net-negative; **what to measure** — the classifier's actual accuracy on a
held-out, representative set before shipping, not an assumption; **what to compute** — the break-even
accuracy for the system's own real prices and easy/hard traffic mix, using the closed-form approach in
§5.2; **the double-payment mechanism** — naming specifically that a misrouted hard request pays for both
a failed cheap attempt and a corrective expensive call, which is what can flip routing from a saving into
a loss; and **an ongoing check, not just a launch check** — accuracy and traffic mix can drift, so the
break-even comparison should be monitored continuously (§6's fix), not computed once. An answer that only
says "measure the accuracy" without connecting it to a specific break-even calculation scores 2.

---

<a id="m5-l17"></a>
## M5-L17 — Provider Differences and Portability

**Answers: C · B · A · D · B · C · A · D · C · B · D · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Bedrock nests the same Anthropic-shaped body inside its own envelope, so nothing at the top level matches by design; an OpenAI-style shape shares several top-level names but relocates the system prompt into the message list, a structural change. **A** is factually wrong. **B** contradicts the lab's own output. **D** invents randomness where the difference is a deliberate design choice each provider made. |
| 2 | **B** | The inner request body is identical; only the wrapper and authentication differ — an envelope change. **A** overstates the effort involved. **C** collapses a genuinely different-sized problem into the same category. **D** ignores that the request shape itself is affected, even if billing is too. |
| 3 | **A** | Common English and structured formats matched exactly; a rare word and non-Latin script diverged sharply — divergence tracks content, not a fixed ratio. **B** and **D** are not supported by anything in the lab and are not sound general claims. **C** directly contradicts the measured −32% gap. |
| 4 | **D** | Every downstream calculation built on a token count — budgets, cost, context checks — is only valid for the tokenizer that produced it. **A** and **B** invent constraints unrelated to the mechanism. **C** is false; input tokens are equally tokenizer-dependent. |
| 5 | **B** | Eight draws is too small a sample to reliably separate a 95%-quality process from an 80%-quality one — the same statistical result M5-L12 established generally, recurring here. **A** contradicts the stated, real 17-point gap. **C** invents an error that did not occur; the seeding is deterministic and correct. **D** overstates — golden suites can detect the gap, just not at this sample size. |
| 6 | **C** | The averaged column exists precisely because a single run is not reliable evidence when comparing providers — run the suite at a size that can actually resolve the gap you care about. **A** narrows a general principle to one use case arbitrarily. **B** is the exact belief the section refutes. **D** contradicts the lab's own 17-point measured gap. |
| 7 | **A** | The same words can land differently as instructions to different models, so a pass rate earned on one provider says nothing certain about another. **B** and **C** assert guarantees no provider makes. **D** narrows a general risk to one language with no basis. |
| 8 | **D** | Re-run the identical golden suite, sized adequately, against the actual target provider — the direct, stated recommendation. **A** and **B** are the failure modes §6's worked example walks through. **C** asks the wrong party to grade its own homework. |
| 9 | **C** | Centralising the provider-specific shape means a switch touches one layer, not every call site that builds a request. **A** and **B** overclaim what an adapter pattern does — it does not remove the need for testing or make providers behave identically. **D** describes a capability the pattern does not have; tokens still need separate re-counting (§5.2). |
| 10 | **B** | Streaming event formats and authentication mechanics are explicitly named as not covered. **A** and **C** are exactly what the lab does cover, in sections 2 and 1 respectively. **D** is covered via M5-L12's cross-reference, not excluded. |
| 11 | **D** | Verify format, tokens, and quality against the real target provider — the lesson's throughline across all three lab sections. **A** and **B** each skip verification the lesson insists on. **C** overreacts; the lesson's message is "verify," not "avoid." |
| 12 | **A** | The label flags that specific field names may be stale; the structural distinction (envelope vs structural change) is the part meant to transfer and does not depend on any single provider's current field names. **B** and **C** overreact to a caveat as if it invalidated the whole section. **D** confuses "the code ran" with "the shapes are confirmed accurate against live documentation," which are different claims. |

**Q13 rubric (5 marks).** One mark each for: **naming the specific risk** — a small manual spot-check has
a real, demonstrated chance of showing no difference even when a substantial quality gap exists, per
§7.3's identical 7/8 result for two providers that were 17 points apart; **connecting it to the lab** —
citing the single-draw-vs-averaged comparison specifically, not just a general "testing is good"
statement; **what to insist on instead** — running the existing golden suite (M5-L12) against the new
provider at a sample size sized to detect the quality gap that matters for this system, before switching
in production; **naming a second dimension** — token counts and cost estimates also need re-verification
against the new provider's tokenizer, not just quality (§5.2); and **not blocking the switch outright** —
the answer should support making the change once properly verified, not argue against switching providers
in general. An answer that only says "we should test more" without naming the sample-size mechanism
scores 2.

---

<a id="m5-l18"></a>
## M5-L18 — Building an Evaluation Dataset You Can Trust

**Answers: D · A · C · B · A · D · B · C · D · A · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | Every patch genuinely fixed the specific example in front of it — the gap opened from the process, not from any single dishonest or careless step. **A** and **B** invent a fault that did not occur. **C** contradicts the lab's own setup, where the generalisation rate was 20%, not zero, and still produced a large gap. |
| 2 | **A** | No gradient touched the data, yet the same-set-guides-and-reports pattern is the same family of failure M1-L09 named for training — a leakage variant specific to how prompts get iterated. **B** dismisses a documented, general mechanism as a coding error. **C** overstates the parallel; there is no gradient step here. **D** is false; the mechanism applies equally to hand-written or logged eval data. |
| 3 | **C** | §7.2 asks how precisely a single measurement reflects the truth, a distinct question from M5-L12's "how many samples to detect a known gap between two conditions." **A**, **B** and **D** name topics from other lessons, not the question this section poses. |
| 4 | **B** | The lab's own computed interval at N=10 spans roughly 63% to 100% — wide enough that the point estimate alone supports almost no decision. **A** denies that sampling has any uncertainty. **C** describes the interval at N≈1,000, not N=10. **D** does not match the formula or the lab's output. |
| 5 | **A** | `(1-0.02)^100 ≈ 13.3%`, computed exactly in the lab — a real, non-trivial chance of zero coverage. **B** and **C** are absolutes the binomial formula does not support. **D** confuses the case type's traffic share with the probability of it being entirely absent from a sample, which are different quantities. |
| 6 | **D** | Deliberately including a stated minimum count per case type guarantees coverage by design; the lab explicitly contrasts this with hoping a larger random sample happens to include it. **A** is the approach the section shows is still insufficient at realistic sizes. **B** and **C** are not proposed anywhere in the lesson and would remove exactly the coverage the section argues for. |
| 7 | **B** | A regression suite is deliberately, repeatedly iterated against (M5-L12) and is typically far too small to either report a precise quality figure or guarantee rare-case coverage — both problems this lesson names directly. **A**, **C** and **D** state constraints that are not true of regression suites. |
| 8 | **C** | Nothing about the process looked wrong at any step — that is precisely what makes it dangerous compared to an obvious bad-faith shortcut, which would be easier to catch. **A**, **B** and **D** invent conditions unrelated to the mechanism described. |
| 9 | **D** | One section addresses precision of a single average measurement; the other addresses whether the right cases were measured at all — genuinely separate concerns, both necessary. **A** collapses them into one. **B** and **C** narrow the sections' scope to topics they do not actually restrict themselves to. |
| 10 | **A** | The lesson explicitly frames LLM-as-judge as previewed here, with the full treatment of its agreement-with-humans problem deferred to M13-L13. **B**, **C** and **D** all overstate a claim the lesson deliberately avoids making. |
| 11 | **C** | Every section demonstrates that a number's trustworthiness depends on the process that produced it — how it was sampled, sized, and whether it was contaminated — not merely that a number exists. **A**, **B** and **D** are absolutes the lesson does not support; in particular, a golden suite (M5-L12) is explicitly shown to be an unreliable source of a quality claim. |
| 12 | **B** | Iterating against a set for regression purposes is the exact mechanism §7.1 shows inflates that same set's own reported pass rate — using it for both purposes at once compounds the two roles' conflicting demands. **A**, **C** and **D** state constraints not established anywhere in the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the mechanism** — a 12-example set iterated against
until every example passes is contaminated in the specific sense §7.1 demonstrates, not a lie, but a
number that no longer measures quality; **noting the missing precision** — even an honest 12-example
measurement carries a very wide confidence interval (§5.2), far too imprecise for a launch decision on its
own; **noting the missing coverage** — 12 hand-written examples are extremely unlikely to include rare,
high-stakes case types, which a stratified design would need to guarantee deliberately (§5.3); **what to
build instead** — a genuine, versioned holdout, sized for the decision's required precision, stratified
for known critical categories, never used to guide prompt changes; and **not dismissing the 12-example set
entirely** — it remains useful as a regression suite (M5-L12), just not as the source of a quality claim.
An answer that only says "12 examples is too few" without naming the contamination mechanism specifically
scores 2.

---

*All 18 Module 5 lessons (M5-L01 through M5-L18) are answered above.*