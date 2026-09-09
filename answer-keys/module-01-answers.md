# Module 1 — Answer Key

**Do not read this until you have attempted the questions.** Every answer includes the reasoning,
and for multiple-choice, why each distractor is wrong. Open-ended items have rubrics rather than
single answers.

Contents: [L01](#m1-l01) · [L02](#m1-l02) · [L03](#m1-l03) · [L04](#m1-l04) · [L05](#m1-l05) ·
[L06](#m1-l06) · [L07](#m1-l07) · [L08](#m1-l08) · [L09](#m1-l09) · [L10](#m1-l10) · [L11](#m1-l11) ·
[Module assessment](#module-assessment)

---

<a id="m1-l01"></a>
## M1-L01 — What AI, ML, DL and Generative AI Mean

### Quiz answers

**Q1 — B.** AI ⊃ ML ⊃ DL, with "generative" describing an output property.
*Why not A:* they are not alternatives you choose between; a system can be all four.
*Why not C:* the nesting is inverted — generative AI does not contain deep learning.
*Why not D:* none of these pairs are synonyms; ML is a strategy, DL is a technique family.

**Q2 — B.** AI, ML, DL, not generative. It is trained (ML), many-layered (DL), and outputs one of
two fixed labels, so the output space is enumerated in advance — not generative.
*Why not A:* a fixed two-option output is a selection, not construction.
*Why not C:* it learned from labelled X-rays, so it is ML.
*Why not D:* perception tasks of this kind are universally called AI.

**Q3 — C.** Origin of the decision logic: human-authored versus fitted from data.
*Why not A:* rule-based systems can run anywhere; neural networks are one ML technique, not the
definition. *Why not B/D:* deployment location and output type are irrelevant to this distinction.

**Q4 — C.** Speech synthesis constructs an audio waveform that never existed.
*Why not A:* a 0–1 score is regression — a number, not content. *Why not B:* clustering assigns
groups. *Why not D:* detection outputs boxes and labels of fixed shape.

**Q5 — B.** The AI effect: techniques stop being called AI once they work reliably and are
understood (OCR, chess engines, spam filtering).
*Why not A:* that is a scaling observation. *Why not C:* social impact, not this term. *Why not D:*
that describes miscalibration (M1-L10).

**Q6 — C.** On tabular data of this size classical methods frequently match or beat deep learning at
lower cost with better explainability, so DL should have to beat a baseline.
*Why not A:* DL can handle tabular data, just often not better. *Why not B:* "always slower" is too
strong. *Why not D:* deep learning does not require generative output — the false premise this
lesson exists to remove.

**Q7 — A.** A handcrafted-evaluation chess engine is AI without learning; AlphaZero is AI with
learning. Exactly the pair that differs on ML.
*Why not B:* both are ML. *Why not C:* both are ML. *Why not D:* both are ML and both generative.

**Q8 — B.** The same model can be constrained to a fixed label or allowed open-ended output, and
generation predates neural networks (Markov chains).
*Why not A:* today's generative systems overwhelmingly do use neural networks. *Why not C:* modern
generation is not rule-based. *Why not D:* generative models are trained.

**Q9 — B.** Generative systems fail invisibly with fluent, wrong output, so a definition of correct
is needed *because* the model will not signal failure.
*Why not A:* models produce output regardless. *Why not C:* generative models are not trained on
task-specific labels. *Why not D:* it is a serious flaw.

**Q10 — Rubric (short written answer).**

| Criterion | Full marks |
|---|---|
| States that DL describes *how it is built*, not how well it works | Required |
| Names at least one thing to ask for instead | Required |
| Avoids jargon appropriate to a non-technical listener | Required |
| Under 60 words | Required |

Acceptable "ask for instead": measured accuracy on held-out data; comparison to a simple baseline;
error rate on the specific task; who checked it and on what data.

*Model answer:* "Deep learning describes the technique, not the result — like saying a building uses
steel. It tells you nothing about whether it stands up. What I'd want instead is how often it gets
the right answer on cases it has never seen, and how that compares to the simplest alternative we
could build in a week."

### Exercise solutions

**Exercise 1.** Sample acceptable definitions (yours may differ in wording):

| Term | Definition without the other three | Question answered |
|---|---|---|
| AI | The engineering field concerned with building systems that perform tasks we consider to require intelligence when people do them | *What field is this?* |
| ML | A set of methods where a program's decision logic is fitted from data rather than written by a person | *Where did the logic come from?* |
| DL | Methods using many stacked layers of adjustable numeric transformations, where intermediate layers construct their own representations | *What kind of model?* |
| Generative AI | Systems whose output is newly constructed content drawn from a space too large to enumerate | *What shape is the output?* |

**Exercise 2.**

1. **Fraud rule, block over £5,000 from a new device.** AI: arguably no (trivial rule). ML: no. DL:
   no. Generative: no. *Deciding property:* a human wrote the threshold.
2. **Google Translate today.** AI ✓ ML ✓ DL ✓ Generative ✓. *Deciding property:* it constructs a
   sentence token by token from an unbounded space.
3. **"Customers also bought" from co-purchase counts.** AI: weakly. ML: **ambiguous** — pure counting
   is arguably statistics rather than learning; if weights are fitted, it is ML. DL: no. Generative:
   no. **Flag as ambiguous.** *Needed:* is anything fitted, or is it a `GROUP BY`?
4. **Receipt photo → structured expense fields.** AI ✓ ML ✓ DL ✓ Generative: **ambiguous** — OCR
   plus extraction into fixed fields is not generative; if an LLM writes the JSON, it is generative
   machinery producing a constrained output. **Flag as ambiguous.** *Needed:* is the output a fixed
   schema filled by extraction, or free generation?
5. **IDE code completion.** AI ✓ ML ✓ DL ✓ Generative ✓.

Ambiguous items: **3 and 4.** Identifying them is worth as much as the confident answers.

**Exercise 3 — Rubric (max 10).**

| Criterion | Marks |
|---|---|
| Does not dismiss or embarrass the PM; treats the underlying concern as legitimate | 2 |
| Re-asks the real question (what problem are we solving / what would success look like?) | 3 |
| Names ≥ 2 categories with an appropriate use for each | 2 |
| Proposes a concrete next step costing < 1 day | 2 |
| Under 150 words | 1 |

*Zero marks for:* "that's not how AI works", listing only risks, or agreeing to build it as stated
without questions.

*Model answer (128 words):* "Competitors having AI is a real signal worth taking seriously — but
'add ChatGPT to checkout' is a solution, and I'd like to find the problem first. What's going wrong
at checkout today: abandonment, support volume, confusion about delivery? If it's abandonment
because people can't find sizing info, a search or rules-based helper may do it better and more
cheaply than a chatbot. If it's genuinely open-ended questions in free text, then a language model
is the right shape of tool. Here's a cheap next step: let me pull the last 200 checkout support
contacts and categorise them. Half a day. That'll tell us whether we need judgement over messy text,
or a better FAQ — and either way we'll be arguing from data rather than from what a competitor
announced."

---

<a id="m1-l02"></a>
## M1-L02 — Rule-Based vs Learned Systems

### Quiz answers

**Q1 — B.** Origin of the decision logic. *Why not A/C/D:* hardware, output type and deployment are
all orthogonal.

**Q2 — C.** Collapse rather than smooth decline outside anticipated cases.
*Why not A/B/D:* speed, deployment cadence and memory are unrelated to brittleness.

**Q3 — B.** The rule triggers on any single keyword; Naive Bayes weighs all words, and `meeting`
pushes toward HAM harder than `free` pushes toward SPAM.
*Why not A:* both saw the same test data. *Why not C:* it uses `free`, just not decisively.
*Why not D:* the rule was implemented as specified — the limitation is structural.

**Q4 — C.** Laplace smoothing prevents a zero probability from zeroing the whole product and
discarding all other evidence.
*Why not A:* readability is irrelevant. *Why not B:* class imbalance is handled by the prior.
*Why not D:* it does not affect speed.

**Q5 — C.** A published specification with a legally correct answer and an audit requirement.
*Why not A/B:* complexity does not justify learning a published rule, and a model will not
"generalise" to future statutory changes — it would need retraining on data that does not yet exist.
*Why not D:* using a model to pick the band adds a failure mode with no benefit.

**Q6 — A.** Superlinear rule growth (rules interact); learned systems have high fixed cost but scale
better with complexity. *Why not B/C/D:* each misstates one of the two curves.

**Q7 — B.** Correct by coincidence — the model learned "unfamiliar input is probably spam" from a
message-length artefact, and the verdict flips when spam samples lengthen.
*Why not A:* the diagnostic explicitly shows no attack detection occurred. *Why not C:* smoothing is
correct and necessary. *Why not D:* it handles spaces fine; the tokens were simply unknown.

**Q8 — B.** You must be able to *prove* the property and explain denials; a statistical system gives
evidence, not proof, and can be manipulated by crafted input.
*Why not A:* latency is not the issue. *Why not C:* it could be represented numerically. *Why not D:*
too broad and false.

**Q9 — C.** Log inputs, decisions and eventual outcomes now — that log becomes the labelled dataset.
*Why not A/B/D:* all are premature or irrelevant without data.

**Q10 — B.** Crossover moved left because someone else paid the training cost, but the fixed cost
relocates into evaluation, guardrails and verification.
*Why not A:* the cost is relocated, not eliminated. *Why not C:* rules remain correct for published
specs and security. *Why not D:* the curves are not identical.

### Exercise solutions

**Exercise 1.**

| Task | Answer | Reason |
|---|---|---|
| UK income tax | **Rule-based** | Published statutory specification; must be exactly correct and auditable |
| Cat in a photo | **Learned** | Perceptual judgement; nobody can write the rule |
| May user delete a document? | **Rule-based** | Security decision — requires proof, never a model |
| Taxi fare estimate | **Hybrid** | Learned duration/demand model inside a deterministic pricing formula |
| Password ≥ 12 chars | **Rule-based** | Trivial, exact, published policy |
| Ranking search results | **Hybrid/learned** | Learned relevance, usually with rule-based filters and business boosts on top |

**Exercise 2.**

1. Adding `cash`, `bonus`, `claim` raises rule-based accuracy (it now catches `claim your free prize
   now` style messages and the cash-bonus phishing). Naive Bayes is **unchanged** — `SPAM_WORDS` is
   only used by `classify_rule`; the learned model never reads it. If your Bayes number moved, you
   edited something else.
2. You cannot fix `we win the contract if the demo works` by editing `SPAM_WORDS` without removing
   `win` — and removing `win` loses `win big money today` and `free trial win rewards`. **There is no
   word list that gets all of them right**, because a flat keyword list cannot express context. That
   is the structural limit, and demonstrating it to yourself is the point of the exercise.
3. **Verified in the authoring environment.** Padding the first *n* SPAM messages with
   ` regards from the operations team here`:

   | padded | spam train words | ham train words | margin (SPAM − HAM) | verdict |
   |---|---|---|---|---|
   | 0 | 97 | 149 | +1.32 | SPAM |
   | 5 | 121 | 149 | +0.50 | SPAM |
   | 10 | 133 | 149 | +0.12 | SPAM |
   | 15 | 157 | 149 | −0.60 | **HAM** |
   | 25 | 205 | 149 | −1.88 | HAM |

   **The exact flip condition:** the verdict changes when spam's training word count **overtakes**
   ham's (157 > 149). Until then spam has the smaller smoothing denominator, so each unknown token
   scores slightly higher under SPAM; once spam messages are longer on average, the advantage
   reverses. Nothing about spam changed — only average message length.
4. *Acceptable answer:* A correct verdict is not evidence of correct reasoning. The model produced
   the right label from an artefact of the data, and a change with no relationship to spam at all
   (message length) reversed it — so the original result carried no reliable information about
   robustness to this attack.

**Exercise 3 — Rubric (max 15).**

| Criterion | Marks |
|---|---|
| Diagram places banned-term blocking as a **deterministic rule before** the model | 3 |
| Harassment detection is learned, and this is justified (cannot be word-listed) | 2 |
| Explicitly states which decisions are never delegated to the model (banned terms, and any account action) | 3 |
| Handles rule-allow / model-block: correct answer is that the model may **flag for review**, not silently block, since only rules produce citable reasons | 3 |
| User-facing reason cites the rule for rule-blocks; for model-flags says "under review" rather than asserting a violation | 2 |
| States one honest unmitigated failure mode | 2 |

*Common unmitigated failures worth full credit:* obfuscated banned terms (leetspeak, homoglyphs)
defeating the exact-match rule; the harassment model's false-positive rate silencing legitimate
speech; the review queue growing faster than moderators can clear it; adversaries probing the system
to learn the rule list.

*Zero marks for:* letting the model make the final block decision on banned terms, or a design with
no human review path.

---

<a id="m1-l03"></a>
## M1-L03 — The Four Task Shapes

### Quiz answers

**Q1 — B.** The structure of the output. *Why not A/C/D:* algorithm, dataset size and deployment do
not define the shape.

**Q2 — B.** The set of possible answers is not fixed in advance and changes at runtime.
*Why not A:* classification can have thousands of classes. *Why not C:* input type is irrelevant.
*Why not D:* the model family does not determine shape.

**Q3 — C.** Multi-label: Billing and Technical are both genuinely true.
*Why not A:* forcing one answer discards a true label and you will misdiagnose it as model error.
*Why not B:* importance is a different question. *Why not D:* the categories are predefined, so it
is not clustering.

**Q4 — B.** It assumes equal spacing between adjacent levels, which is usually false for business
severity (low→medium is not the same jump as high→critical).
*Why not A:* regression handles four values fine. *Why not C:* it is evaluable. *Why not D:* it uses
labels, so it is supervised.

**Q5 — C.** The issue set is large and changes over time, so no fixed label space exists, and the
useful output is an ordered shortlist.
*Why not A:* output type alone is not decisive. *Why not B:* accuracy is not the reason. *Why not D:*
classification can handle many classes; the problem is that the set is not fixed.

**Q6 — B.** Clustering always returns groups whether or not real structure exists, so output needs
independent validation.
*Why not A:* that is the error the demonstration disproves. *Why not C:* k-means behaved correctly.
*Why not D:* no value of k would change the point.

**Q7 — B.** A single score across three tasks cannot localise the failure.
*Why not A:* cost is a separate concern. *Why not C:* one model can do all three. *Why not D:* it is
the opposite of best practice.

**Q8 — B.** Constrain output to the four labels: cheaper, and accuracy becomes measurable.
*Why not A:* free text plus parsing adds failure modes and cost. *Why not C:* a larger model does not
address the shape mismatch. *Why not D:* clustering cannot produce your predefined categories.

**Q9 — C.** Ranking → accuracy is mismatched; ranking cares about the ordering of the top positions,
measured by MRR/nDCG/Precision@k. A, B and D are correct pairings.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Names two genuinely different shapes | Required |
| Gives one discriminating question | Required |
| Under 80 words | Required |

Acceptable shape pairs: retrieval/ranking ("find the relevant document") vs generation ("answer in
prose"); classification ("tag each document") vs generation ("summarise it"); extraction (fixed
schema) vs generation.

*Model answer:* "It could mean two quite different things. One is search: given a question, find the
right documents — the output is a ranked list. The other is answering: read the documents and write a
reply in prose. They need different components and different measures of success. The question I'd
ask: when this works perfectly, does your user see a list of documents, or a written answer?"

### Exercise solutions

**Exercise 1.**

| # | Task | Shape | Output type |
|---|---|---|---|
| 1 | Electricity demand in MW | Regression | Continuous number |
| 2 | Transaction fraudulent? | Binary classification | One of 2 labels |
| 3 | Endpoints with similar usage | Clustering | Group assignment, groups undefined |
| 4 | Release notes from PRs | Generation | Free text |
| 5 | Bug priority P0–P3 | Ordinal classification | Ordered category |
| 6 | 5 most relevant documents | Ranking | Ordered shortlist |

**Exercise 2 — Rubric (max 12).** Two marks per row for a defensible decision table; 2 for
sequencing; 2 for a justified "would not build".

*Sample decomposition for "reduce returns":*

| Decision | Shape | Output | Fixed label space? | Data needed |
|---|---|---|---|---|
| Will this order be returned? | Binary classification | 0/1 | Yes | Historical orders + return outcomes |
| Why was it returned? | Multi-label classification | tags | Yes (return reason codes) | Labelled return reasons |
| Is the size guidance wrong for this product? | Ranking/anomaly | ordered list of products | No | Return rate per product vs baseline |
| What size should we recommend? | Classification or regression | size label / numeric | Yes | Purchase + return + fit data |
| Draft a message asking why the item was returned | Generation | free text | No | None (prompt-based) |
| Estimated return-shipping cost | Regression | currency | n/a | Logistics data |

*Would-not-build with reason (full marks for any well-argued choice):* the generative "why did you
return it" message — low value, and the answer is better collected with a three-option form that
produces structured data you can actually aggregate.

**Exercise 3 — Rubric (max 15).** The three problems:

1. **Mixed dimensions (5 marks).** `Positive`/`Negative` are *sentiment*; `Complaint about
   shipping`/`product quality`/`Request for refund` are *topic/intent*; `Spam` is a *validity* check.
   These are three independent axes crushed into one list. A negative review about shipping is
   legitimately three of these at once.
2. **Not mutually exclusive (5 marks).** Modelled as multi-class, the model is forced to pick one
   and will look inconsistent. It is at minimum multi-label — and properly, several separate
   classifiers.
3. **Spam is a different pipeline stage (5 marks).** Spam filtering should happen *before*
   classification, not as a peer category. Mixing it in means the classifier trains on invalid input
   and the spam decision cannot be handled with different thresholds or escalation.

*Corrected specification:*
```
Stage 1 (gate):        is_spam            -> binary classification
Stage 2 (sentiment):   positive/neutral/negative -> ordinal or multi-class
Stage 3 (topic):       shipping / product_quality / other  -> multi-label
Stage 4 (intent flag): requests_refund    -> binary, independent of the above
```

*What to check in the existing labels (full marks for any 3):* how often two annotators agree; how
many reviews were forced into one category when several applied; whether `Spam` was applied
consistently; whether the class distribution is so skewed that some categories have too few examples
to learn or evaluate.

---

<a id="m1-l04"></a>
## M1-L04 — Data Vocabulary

### Quiz answers

**Q1 — B.** `X` is the 2-D feature matrix (capital by convention for 2-D), `y` the 1-D label vector.
*Why not A/C/D:* all misassign the roles; the capitalisation convention is dimensional, not
arbitrary.

**Q2 — B.** Algorithm = procedure existing before data; model = artefact produced by running it on a
specific dataset. Compiler vs binary.
*Why not A:* hardware is irrelevant. *Why not C:* they are distinct. *Why not D:* both are
implemented in code and both have mathematical descriptions.

**Q3 — C.** `number_of_replies_so_far` accumulates over the ticket's life and is 0 at creation, so it
is unavailable at prediction time.
*Why not A/B/D:* channel, tier and creation hour are all known at ticket creation.

**Q4 — B.** To demonstrate that misalignment produces no error, warning or type failure — the model
silently learns noise.
*Why not A:* it destroys accuracy. *Why not C:* they must be shuffled together. *Why not D:* no speed
effect.

**Q5 — B.** 50,000 sparse columns, and IDs carry no generalisable signal — a customer ID tells the
model nothing about a customer it has not seen.
*Why not A:* privacy is a real concern but not the modelling reason. *Why not C:* there is no such
limit. *Why not D:* nonsense.

**Q6 — C.** The label definition is ambiguous and ~78% is your realistic ceiling as defined.
*Why not A:* disagreement usually indicates definition ambiguity, not incompetence. *Why not B:* the
opposite. *Why not D:* no architecture beats noisy labels.

**Q7 — B.** Removes large-scale *training* labels but not the smaller labelled *test* set.
*Why not A:* you cannot know it works without labelled evaluation data. *Why not C:* it removes far
more than feature engineering. *Why not D:* it does substantially reduce the requirement.

**Q8 — B.** Features computed differently in training versus serving, so inference inputs do not
match what the model learned from.
*Why not A:* that is distribution shift/drift. *Why not C/D:* neither is the definition.

**Q9 — B.** Hour is cyclic: 23 and 0 are adjacent in reality but 23 apart numerically.
*Why not A:* it is a genuine limitation. *Why not C:* integers are usable. *Why not D:* creation hour
is known at prediction time, so it is not leakage.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Explicitly distinguishes reusing the algorithm from reusing the trained model | Required |
| States that the model answer depends on whether Brazilian data resembles training data | Required |
| Names at least one thing to check (language, currency, customer behaviour, label availability) | Required |
| Under 70 words | Required |

*Model answer:* "Two different questions. Reusing the *approach* — same algorithm, retrained on
Brazilian data — is straightforward. Reusing the *trained model* as-is depends on whether Brazilian
customers behave like the ones it learned from: different language, currency, payment methods and
seasonality would all break it. I'd want a few thousand labelled Brazilian examples to measure it
before deciding, rather than assuming either way."

### Exercise solutions

**Exercise 1.**
(a) One example = one customer-subscription-period (state the period explicitly — e.g. one customer
observed at their renewal date).
(b) Plausible features: tenure in months; plan tier; number of support tickets in the last 90 days;
logins in the last 30 days; payment failures to date; seats used vs purchased.
(c) Label: `renewed = 1` if a renewal payment succeeded within N days of the renewal date, else 0.
Must exclude customers whose renewal date has not yet passed.
(d) Tempting leakage: `cancellation_reason`, `downgrade_date`, or `days_since_last_login` computed
*after* the renewal date. Each is populated by or after the outcome.

**Exercise 2.**

1. **Usable:** `country`, `items`, `order_total`, and features derived from `placed_at`.
   **Leakage:** `delivered_at` (unknown at order time — and a late delivery is a cause of returns, so
   it is highly predictive and completely unavailable). `was_returned` is the label. `order_id` is an
   identifier, not a feature. `customer_id` is usable only as a source of derived features, not
   directly.
2. From `placed_at`: `hour_of_day` (cyclic — consider sine/cosine encoding), `day_of_week`,
   `is_weekend`, `days_until_next_public_holiday`, `is_late_night_order`.
3. Two ways to use `customer_id` without one-hot:
   - **Aggregate features** — prior order count, historical return *rate* for that customer.
     *Risk:* leakage if computed over the whole history including future orders; must be computed
     strictly as-of the order date.
   - **Target encoding** — replace the ID with the mean return rate for that customer.
     *Risk:* strong leakage if computed on the full dataset including the row itself; must be fitted
     on training data only, with smoothing for rare customers.
   (Also acceptable: an embedding, or bucketing into cohorts.)
4. With `country` (3 values one-hot), `items`, `order_total`, plus 4 derived time features and 2
   customer aggregates: `d = 3 + 1 + 1 + 4 + 2 = 11`. With 3 rows, `X` is `(3, 11)` and `y` is
   `(3,)`. Marks are for showing the arithmetic and stating both shapes, not for matching this exact
   count.

**Exercise 3 — Rubric (max 20).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 4 | Example = one employee observed at a fixed index date. Label = left within 12 months of that date. **Must address censoring**: exclude anyone whose 12-month window has not fully elapsed, or they will be silently labelled "stayed" |
| 2 | 4 | Five features with availability stated; at least one flagged as as-of-date dependent (e.g. tenure, recent performance rating) |
| 3 | 6 | Two problematic features (age, sex, ethnicity, disability, pregnancy/parental leave, salary as a proxy). **Must explain proxy risk**: excluding the protected attribute does not remove the effect, because postcode, commute distance, part-time status, or tenure gaps can encode it. Marks require this point |
| 4 | 3 | "Left" is not crisp: voluntary vs involuntary vs redundancy vs retirement vs internal transfer are different outcomes. Predicting all of them as one label produces a model that mostly predicts redundancies |
| 5 | 3 | Any well-argued recommendation. **A defensible "no" scores full marks** |

*Strong "no" arguments:* the label conflates outcomes with different causes; the useful features are
mostly protected characteristics or their proxies; the intervention the prediction enables is
unclear; and the system creates a risk of self-fulfilling treatment of flagged employees. A strong
"yes" must specify aggregate-only reporting, no individual-level exposure to managers, and a bias
audit.

---

<a id="m1-l05"></a>
## M1-L05 — Parameters vs Hyperparameters

### Quiz answers

**Q1 — B.** Did an algorithm compute it from data, or did a human set it before training?
*Why not A/C/D:* data type, storage location and impact on accuracy do not separate the two.

**Q2 — B.** `k` must be chosen before running; the centres are computed by the algorithm.
*Why not A/C/D:* centres and assignments are all outputs of the fitting procedure.

**Q3 — B.** Selecting the best of several noisy measurements is optimistically biased, so the test
set must play no part in the choice.
*Why not A/C:* size is a separate concern. *Why not D:* the consequence is measurable and large.

**Q4 — B.** Selection luck — the maximum of 50 noisy measurements exceeds the true value.
*Why not A:* every candidate was identical by construction. *Why not C:* the simulation is correct.
*Why not D:* no parameters were fitted.

**Q5 — C.** `k` is a setting you choose for your application.
*Why not A/B/D:* attention weights, embedding values and learned frequencies are all parameters
inside a model someone else trained.

**Q6 — B.** Set before running, materially changes behaviour, invalidates prior measurements.
*Why not A:* storage format is irrelevant. *Why not C:* the model does not learn your prompt.
*Why not D:* it is a configured value, not per-request user data.

**Q7 — C.** 5⁴ = 625. *Why not A (5×4):* that is not how combinations work. *Why not B (5²):* wrong
exponent. *Why not D:* 1024 = 4⁵, the operands reversed.

**Q8 — B.** Few hyperparameters matter; a grid retests the same few values of the important one,
random search tries a new value on every run.
*Why not A:* the values are random, not better. *Why not C:* grids handle floats. *Why not D:* both
need a validation set.

**Q9 — B.** Parameter count is size, not quality; ask for held-out evaluation results.
*Why not A:* the central error. *Why not C/D:* irrelevant responses.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Explains that the best-seen score was *selected* from many attempts | Required |
| States that selecting a maximum from noisy measurements is biased upward | Required |
| Says what to report instead (score on data not used for any decision) | Required |
| Under 80 words | Required |

*Model answer:* "That number is the best of everything we tried, and we tried a lot. Picking the
highest of many noisy measurements always overstates — even if every option were equally good, the
winner would look better than average by chance. So it's the top of the range, not the middle. The
figure to plan against is what it scores on a set of examples we never used to make any decision.
I'd expect that to be several points lower."

### Exercise solutions

**Exercise 1.** 1 hyper · 2 param · 3 hyper · 4 param · 5 hyper · 6 param · 7 hyper · 8 hyper.

**Exercise 2.**

1. 3 × 3 × 3 × 2 = **54** combinations.
2. 54 × 150 × £0.004 = **£32.40** for one full grid.
3. *Acceptable strategies (max 4 marks):* £50 affords roughly one and a half full grids, so a full
   grid is technically affordable but wasteful. Better: fix reranking **on** (it usually dominates)
   and `overlap` at 50 (least influential), then sweep chunk size × k = 9 runs ≈ £5.40. Use the
   result to pick a chunk size, then sweep the remaining parameters around the winner. Full marks
   require naming which parameters you expect to matter most and why.
4. **`chunk size` and `k` are not independent.** They jointly determine how many tokens of context
   reach the model. Halving chunk size while holding `k` fixed halves the context; the "best" `k`
   therefore shifts with chunk size, so tuning them separately can miss the true optimum. (Also
   acceptable: overlap interacts with chunk size, since overlap is meaningful only relative to chunk
   length.)

**Exercise 3.**

1. **Verified in the authoring environment.** With `true_rate=0.85` and `eval_size=30`, optimism at
   20 trials is substantially larger than the 100-item baseline. The direction is what is marked:
   *smaller evaluation set → larger optimistic bias.*
2. Each measurement's noise scales roughly with `1/√n`. Smaller `n` means noisier measurements, so
   the maximum of N of them lands further above the true value. **Optimism grows as the evaluation
   set shrinks and as the number of trials grows.**
3. *Model answer:* "Forty variants against forty questions is close to the worst case for this
   effect. Each question is worth 2.5 percentage points, so a couple of lucky items moves the score
   by five points, and you kept the luckiest of forty tries. In my simulation, forty trials on a
   thirty-item set inflated the apparent score substantially even when every variant was genuinely
   identical. I'd treat 92% as the top of a range, not an estimate. Before shipping I'd want a fresh
   set of at least 200 questions, scored once."
4. *Acceptable trade-offs:* early prototyping where you need direction rather than a number;
   comparing two options that differ by far more than the bias; when fresh evaluation data is
   genuinely unobtainable this quarter. **Bounding the risk:** state the number of configurations
   compared alongside the score; report a confidence interval; hold back a small final set even if
   it is smaller than ideal; monitor production quality closely after launch and treat the offline
   number as a hypothesis.

---

<a id="m1-l06"></a>
## M1-L06 — Training, Validation, Testing, Inference

### Quiz answers

**Q1 — A.** Training only. *Why not B/C/D:* validation and testing change *your* decisions, not the
model's parameters; inference changes nothing.

**Q2 — B.** Comparing hyperparameters uses up a dataset's ability to judge fairly.
*Why not A/D:* size and convention are not the reason. *Why not C:* labelling cost is unrelated.

**Q3 — C.** 98/1/1 — 1% of 10M is 100,000, ample for a precise estimate. Absolute held-out size
matters more than percentage.

**Q4 — B.** It lets the model train on later periods and test on earlier ones, which production never
allows. *Why not A:* it is a serious error. *Why not C:* random splits handle numeric targets.
*Why not D:* imbalance is a separate issue.

**Q5 — B.** Only ~8 positives, so one error moves recall by over 12 points.
*Why not A/C/D:* the test set is too small for the minority class, which is the specific problem.

**Q6 — B.** The scaling values encode the test data's distribution — preprocessing leakage.
*Why not A:* order matters greatly. *Why not C/D:* speed and imbalance are unaffected.

**Q7 — B.** Once. Each example sits in the held-out fold exactly one time.

**Q8 — B.** Prompt engineering is fitting, so a held-out eval set touched once is required and
few-shot examples must not appear in it.
*Why not A:* the central misconception. *Why not C:* public benchmarks risk contamination.
*Why not D:* many settings need tuning.

**Q9 — B.** Get a fresh test set; if impossible, report the figure explicitly as potentially
optimistic and state how many configurations were compared.
*Why not A:* dishonest. *Why not C:* fraud. *Why not D:* re-running the same 30 on more data does not
undo the selection.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| States that the bias is mechanical, not a matter of discipline | Required |
| References the M1-L05 measurement (selecting the max of noisy scores inflates it) | Required |
| Notes that every decision informed by the test set contaminates it, however careful | Required |
| Under 80 words | Required |

*Model answer:* "Care doesn't help, because the bias isn't caused by carelessness. In the simulation
we ran, twenty identical candidates produced a winner that looked eight points better than the truth
— purely from picking the highest of twenty noisy scores. That happens whether or not we're careful.
Any decision we make after looking at the test set leaks into the result. The only fix is a set we
don't look at until we're finished."

### Exercise solutions

**Exercise 1.**

1. **Random (stratified if categories are uneven).** Images are independent; no time dimension.
2. **Temporal.** Predicting the future; trends and seasonality present.
3. **Stratified**, and check the absolute positive count — 0.3% of a 20,000-row test set is only 60
   positives. Group by customer/card if entities repeat.
4. **Grouped by document.** Sentences within a document are highly related; without grouping you
   measure document memorisation.
5. **Grouped by patient**, plus temporal if predicting forward. Never split a patient's visits across
   train and test.

**Exercise 2.** (Answers from the executed lab.)

1. The extra 0.088 is the model's systematic **under-prediction of a rising trend**. Under a random
   split the test set contains December rows, so the training-set breach rate already reflects
   late-year behaviour and matches. Under a temporal split, training covers only months 1–9
   (rate 0.125) while the test period is months 10–12 (rate 0.215). The gap is real and would appear
   in production; the random split concealed it by letting the model see the future.
2. Random split: **60/60 = 100%** overlap. Grouped split: **0/12 = 0%**. The random split measures
   performance on customers already seen in training (partly memorisation); the grouped split
   measures performance on genuinely new customers.
3. The **grouped** number (−0.018 error). The other three are inflated by having seen every test
   customer during training.
4. Because it is the only one that reproduces the constraint production imposes: you can only train
   on the past. A number that could not be achieved in deployment is not a useful estimate, however
   flattering.
5. **Verified:** `cutoff_month = 7` gives train n=1425 predicting 0.094, test n=1575 actual 0.199,
   **error +0.105** — larger than +0.091. Training now covers only months 1–6, so it captures even
   less of the upward trend while the test window contains more of it. Shorter training windows on a
   trending series produce larger under-prediction.

**Exercise 3 — Rubric (max 20).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 6 | Concerns ranked: (a) no separate test set — 80/20 with tuning means the reported number is validation, potentially heavily optimistic; (b) "trained on all available data" suggests preprocessing/statistics computed before splitting; (c) random split may be wrong if data is temporal or has repeated entities; (d) no class-balance or baseline given, so 94% may be below the base rate; (e) no statement of what "accuracy" measures or on how many examples |
| 2 | 3 | Three questions, e.g.: How many configurations were compared, and against which data? What is the class balance and what does "always predict the majority" score? Do examples repeat by entity or over time? |
| 3 | 6 | Specific design: fresh held-out test set of stated size with minority-count check; grouped and/or temporal split justified by the data's structure; report accuracy **plus** precision/recall or a confusion matrix; state a baseline; run once |
| 4 | 5 | Honest, non-obstructive note. Must give a concrete risk, a concrete option, and let the decision-maker decide |

*Model answer for part 4 (119 words):* "The 94% figure is real but it's a validation number, not a
test number — it was measured on the data used to tune the model, so it's likely several points
optimistic. I can't say how many without checking. Two options. We launch Friday to a 10% cohort with
human review of every output, and I run the clean evaluation in parallel — we get the date and the
number by mid-week after. Or we delay two weeks and launch with a figure we can defend. My
recommendation is the first: it protects the date, bounds the exposure, and we learn the true number
either way. What I'd avoid is launching to everyone on a number we haven't verified."

---

<a id="m1-l07"></a>
## M1-L07 — Learning Paradigms

### Quiz answers

**Q1 — B.** Where the training signal comes from.

**Q2 — B.** The target is derived automatically from the data, such as predicting a hidden token.
*Why not A:* that is unsupervised. *Why not C:* supervised. *Why not D:* reinforcement.

**Q3 — B.** 7 pairs. The general rule is `n − 1` for `n` tokens; with 8 tokens you get 7.
*Why not C:* the first token has no preceding context to predict it from. *Why not A/D:* neither
matches the rule.

**Q4 — B.** The objective rewards likely continuations and contains no term for truth.
*Why not A:* more data does not add a truth objective. *Why not C:* not a sampling bug.
*Why not D:* LLMs are self-supervised, and the paradigm is not itself the cause.

**Q5 — B.** Self-supervised pretraining → supervised fine-tuning → preference optimisation.

**Q6 — B.** None — parameters are frozen; prompting, retrieval and tools change the input.
*Why not A:* the single most common misconception. *Why not C/D:* nothing is learned at inference.

**Q7 — B.** Reward hacking. *Why not A:* overfitting is about generalisation from training data.
*Why not C:* drift in input distribution. *Why not D:* credit assignment is the difficulty of
attributing reward to actions.

**Q8 — B.** No ground truth exists, so internal metrics measure cluster tightness rather than
usefulness; validation must come from outside.

**Q9 — B.** Bidirectional context suits understanding/encoding; causal left-to-right suits
generation. *Why not A/C:* speed and size are not the reason. *Why not D:* masking does not prevent
hallucination.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| States that parameters are frozen at inference and nothing is learned from conversations | Required |
| Explains apparent memory as re-sent context | Required |
| Identifies what they probably want (retrieval, stored conversation history, or a fine-tuning cycle) | Required |
| Under 80 words | Required |

*Model answer:* "A deployed model doesn't change from talking to users — its weights are frozen. What
looks like memory is just us re-sending the earlier messages with each request. If we want it to
improve from conversations, that's a deliberate cycle: store the exchanges, have someone label the
good and bad ones, and either fine-tune or feed the good ones back as retrieved examples. That's a
project, not a setting."

### Exercise solutions

**Exercise 1.** 1 supervised · 2 unsupervised · 3 self-supervised · 4 reinforcement ·
5 semi-supervised · 6 self-supervised (contrastive — the "label" comes from which photo the crops
came from, which the data already knows).

**Exercise 2.**

1. Marks for correct mechanics: each pair is (all tokens so far → next token), or (previous token →
   current token) for a bigram. The first token cannot be a target.
2. A 100-word paragraph gives **99** next-token pairs. General formula: **n − 1** for n tokens.
   (With full left-context rather than bigram, still n−1 training positions.)
3. Because sentiment is not present in the text — it is a human judgement *about* the text. Nothing
   in the raw data can be uncovered to reveal it. Self-supervision only works where the target is
   already in the data and can be hidden.
4. The bigram model produces locally plausible, globally meaningless text because **its context is
   exactly one token**. Every adjacent word pair genuinely occurred, so it reads like English at
   close range; nothing carries information across the sentence, so it collapses at longer range. A
   transformer's self-attention lets every position attend to every earlier position, extending
   context from 1 token to thousands. **The training objective is identical** — only the available
   context changed.

**Exercise 3 — Rubric (max 20).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 4 | Labels come from agent corrections (reassignments). Feedback delay = time until an agent re-routes, typically hours to days. Must note that "not reassigned" is a weak positive signal — it may mean the agent tolerated a bad route |
| 2 | 4 | State = ticket features. Action = choice of team. Reward = +1 if not reassigned within 24h, else −1. Any precise, consistent formulation earns full marks |
| 3 | **7** | Must identify a concrete hack. The canonical one: **route everything to the team least likely to reassign** — an overloaded or unengaged team that silently absorbs anything. Reward improves, business outcome worsens. Also accepted: route to a team with no reassignment permission; route to a catch-all queue; exploit tickets auto-closed after 24h |
| 4 | 3 | Mitigation with stated residual risk, e.g. add resolution time and CSAT to the reward (residual: those are also gameable and slower); cap per-team volume (residual: caps are arbitrary and may misroute at peak); require a human audit sample (residual: cost, and sampling may miss rare abuse) |
| 5 | 2 | Any justified recommendation. **"Neither — use a supervised classifier on historical routing, or an LLM with the team descriptions in a prompt"** is the strongest answer, on grounds of evaluation difficulty and reward risk |

*Part 3 is the heavily weighted item.* A submission that finds no hack in its own design scores zero
for that part regardless of how well the rest is written.

---

<a id="m1-l08"></a>
## M1-L08 — Generalization, Overfitting and Underfitting

### Quiz answers

**Q1 — B.** Overfitting: low training error, much higher validation error.

**Q2 — B.** Both errors high and close together.
*Why not A:* that is overfitting. *Why not C:* that is a bug signature. *Why not D:* perfect training
error suggests overfitting or leakage.

**Q3 — B.** It falls monotonically with capacity, so zero training error is achievable by
memorisation.

**Q4 — C.** More real training data — generally most effective and most expensive.

**Q5 — B.** The model is *underfitting* (both errors high and close), so further constraining it
makes things worse. This question tests whether you diagnose before treating.

**Q6 — B.** Fitting the prompt to the specific examples you iterated against.
*Why not A:* a length problem is different. *Why not C:* the model does not retain your prompt.
*Why not D:* temperature is unrelated.

**Q7 — B.** Investigate for a bug — dropout still active, preprocessing differences, or splits of
systematically different difficulty.
*Why not A:* a 14-point inversion is not a generalisation success. *Why not C/D:* treating a bug as a
capacity problem.

**Q8 — B.** Enough capacity to pass exactly through every training point — memorisation, confirmed by
validation error of 9.8.

**Q9 — B.** High bias → underfitting; high variance → overfitting.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Asks what data the 99% was measured on (train, validation or a clean test set) | Required |
| Asks about class balance / the baseline — 99% may be worse than "always predict not-fraud" | Required |
| Asks about leakage or feature availability at prediction time | Required |
| Under 80 words | Required |

*Model answer:* "Three questions. First, which data — training, validation, or a test set that
played no part in any decision? Second, what's the fraud rate? If it's 1%, then always saying 'not
fraud' also scores 99%, and the model may be adding nothing. Third, which features does it use, and
are they all available at the moment we'd need the prediction? A single very strong feature is
usually leakage rather than good luck."

### Exercise solutions

**Exercise 1.**

| # | Diagnosis | One remedy |
|---|---|---|
| 1 | Overfitting (98/62) | More data; regularisation; early stopping |
| 2 | Underfitting (64/63) | More capacity; better features; train longer |
| 3 | Good fit (88/86) | Ship it; compare against a baseline first |
| 4 | Bug (55/79 — validation above training) | Check dropout at eval, preprocessing consistency, split composition |
| 5 | Overfitting from epoch 20 | Early stopping at epoch 20 |

**Exercise 2.** (Answers from the executed lab.)

1. **Degree 5**, validation 2.063, training 0.181, **gap 1.882**.
2. Highest degree (11): **training 0.054**, **validation 15714.965**. The model with the lowest
   training error is the worst model by a factor of roughly 7,600. Once the polynomial has enough
   freedom to pass exactly through all 12 training points it does so, and swings violently between
   them. Training error rewards exactly that behaviour, which is why it must never be used to select
   a model.
3. **Verified:** with `N_TRAIN = 60`, best degree becomes **4** and the worst-case validation error
   falls from **15,715 to 1.71**. With 60 points, a degree-11 polynomial no longer has enough
   capacity to thread through them all, so the catastrophe is not merely reduced — it is eliminated.
   More data changes what the model is *able* to memorise.
4. **Verified:** with `RIDGE = 1.0`, best degree stays 5 (val 2.183) and worst-case validation error
   falls from **15,715 to 1,925**. The ridge term penalises large coefficients, so the fit cannot use
   the enormous alternating weights required to interpolate every point. It helps substantially — and
   is still an order of magnitude worse than simply having more data. That ordering is the practical
   lesson.

**Exercise 3 — Rubric (max 20).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 6 | Five hypotheses, ≥2 involving overfitting: prompt overfitting to the 40 questions; retrieval overfitting (thresholds tuned on those 40); eval questions written from the documents so they share rare wording; production questions cover topics absent from the eval set; users phrase things differently; "often wrong" may mean unhelpful rather than factually wrong |
| 2 | 6 | Per-hypothesis diagnostic with a confirming result, e.g. *run the 40 questions rephrased by someone who has not read the docs; a large accuracy drop confirms retrieval/prompt overfitting* |
| 3 | 5 | Questions sourced from real user language (support tickets, search logs, user interviews); a stated size (≥150–200); deliberately includes: out-of-scope questions that should be refused, ambiguous questions, multi-part questions, questions whose answer spans two documents, and topics with no answer in the corpus |
| 4 | 3 | Honest interim approach: sample and hand-label 30 real production queries; report as a preliminary estimate with a stated confidence range; say plainly that the 38/40 figure is not a production estimate |

---

<a id="m1-l09"></a>
## M1-L09 — Data Leakage and Evaluation Contamination

### Quiz answers

**Q1 — B.** Overfitting shows a train/validation gap; leakage makes all three splits look excellent,
removing every warning sign.

**Q2 — B.** Target leakage — collections assignment follows default.

**Q3 — B.** Split, fit the scaler on training only, then `transform` validation and test.
*Why not C:* fitting a separate scaler per split means the splits are scaled inconsistently, so the
model sees differently-scaled inputs at inference.

**Q4 — B.** Treat as a leakage alarm; check when the field is populated and whether its value is a
consequence of the label.

**Q5 — B.** tier2 assignment *is* how escalation is recorded — a business fact not discoverable from
the data alone.

**Q6 — B.** Questions inherit the documents' rare wording, so retrieval succeeds on lexical overlap
real users will not reproduce.

**Q7 — B.** Replace retrieved context with empty text and re-run; if accuracy stays high, the answer
is reaching the model from elsewhere.

**Q8 — B.** The diagnostic says "good fit", but it *assumes no leakage*; a perfect score with a zero
gap is the leakage signature. This question tests whether you can hold two lessons at once.

**Q9 — B.** Cross-split duplicates survive, so the same example can appear in both training and test.
Deduplicate before splitting.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Explains that good numbers are not yet *evidence* — they may measure leakage | Required |
| Gives a concrete, time-boxed check rather than an open-ended delay | Required |
| States the cost of being wrong (rebuild + credibility) versus the cost of the delay | Required |
| Does not moralise or catastrophise | Required |
| Under 90 words | Required |

*Model answer:* "The numbers are excellent, and that's exactly why I want a day on them. Scores this
high on a hard problem are usually one of two things: a real result, or a field in the data that
quietly contains the answer. I can tell which in a day — I rebuild the test rows as they'd actually
arrive and re-score. If it holds up, we launch with a number we can defend. If it doesn't, we've
saved a rebuild and a retraction. One day now against a quarter later."

### Exercise solutions

**Exercise 1.**

| # | Type | Fix |
|---|---|---|
| 1 | Target leakage | Remove `chargeback_filed`; it exists only after fraud is confirmed |
| 2 | Preprocessing leakage | Split first; fit the scaler on training only |
| 3 | Temporal leakage | Use a temporal split: train on earlier months, test on later |
| 4 | Group leakage | Split by document, so all sentences from one document stay together |
| 5 | Benchmark contamination | Build a private evaluation set; treat the public score as unreliable |

**Exercise 2.** (Answers from the executed lab.)

1. Test accuracy **100.0%**; on the same rows presented as they appear at prediction time,
   **75.0%** — exactly equal to the "always predict no" baseline. The model's entire skill was
   reading fields that record the answer.
2. **Step 2 (single-feature predictive power)** fired first, flagging `team_tier2` at 100.0%,
   `has_note` at 100.0%, and `prio_high` at 93.2%. Step 3 also found 2 duplicate rows across
   train/test.
3. `prio_high` is partly an *outcome*: in `make_data()`, escalated tickets have their priority set to
   `"high"` as part of escalating, overwriting the creation-time value. The current field therefore
   encodes the label. **Fix:** reconstruct priority *as of ticket creation* from the audit/change log
   rather than reading the current value — point-in-time feature reconstruction. Do not simply drop
   the field; creation priority is genuinely useful and genuinely available.
4. Marks for any feature that is subtle rather than obviously post-outcome. Good examples:
   `assigned_agent_seniority` (senior agents get escalated tickets); `thread_length`;
   `time_to_first_response` (escalated tickets get faster responses); `has_manager_cc`. Full marks
   require running the audit and reporting the single-feature accuracy it produced.
5. *Model answer:* "The 100% came from two fields that are only filled in *after* a ticket is
   escalated — the model was reading the answer, not predicting it. When I re-score those same test
   tickets as they actually look at creation time, it drops to 75%, which is the same as guessing
   'no' every time. The honest model gets 78.3% against that 75% baseline: a small real gain, and one
   that will still be there in production."

**Exercise 3 — Rubric (max 20).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 6 | All four channels named and ranked. Most likely: **retrieval contamination** (questions written from documents) and **prompt/threshold overfitting to 50 questions**. Less likely but possible: benchmark contamination; answer-in-the-prompt via metadata |
| 2 | 5 | Concrete: run the 50 questions with retrieved context replaced by an empty string, keeping everything else identical. If accuracy remains materially above what the model achieves with no domain knowledge, the answers are reaching it via the prompt, metadata, filenames, or pretraining memory |
| 3 | 4 | The engineer inherited the documents' vocabulary, structure and assumptions; the questions test whether the system can find text the question was copied from. Replacement: source questions from real user channels — support tickets, search logs, recorded onboarding calls — written by someone who has not read the corpus; include questions the corpus cannot answer |
| 4 | 5 | Testable criteria, e.g.: eval set ≥ 200 questions from real user language; ≥ 20% unanswerable questions with a measured abstention rate; zero overlap between few-shot examples and eval items, asserted in CI; empty-context test run and reported; retrieval and answer quality measured separately; the set is versioned and the final number produced by a single run |

---

<a id="m1-l10"></a>
## M1-L10 — Probability, Uncertainty and Hallucination

### Quiz answers

**Q1 — B.** Expected: generation samples from a probability distribution.

**Q2 — B.** Likely-continuation objective, no truth term, and generation must always produce
something.

**Q3 — B.** Essentially nothing measurable — that phrase is generated by the same next-token process
as the rest of the text.

**Q4 — C.** Overconfident: stated ~0.95, actual 0.81.

**Q5 — C.** About 21. Expected errors 150 × 0.05 = 7.5; actual 150 × 0.19 = 28.5; difference ≈ 21.

**Q6 — B.** Epistemic, by supplying the missing information via retrieval or tools.

**Q7 — B.** Sampling and infrastructure non-determinism make identical inputs produce different text
even at temperature 0.

**Q8 — B.** Fixes untraceable claims; leaves fabricated or mismatched citations open, so each must be
programmatically verified against the retrieved source.

**Q9 — B.** The *form* of a citation is highly learnable while its *content* is not, so output looks
maximally credible exactly where it is least reliable.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Explains that output is generated by predicting likely text, with no internal truth check | Required |
| States what *can* be promised: a measured rate, a defined failure behaviour, monitoring | Required |
| Avoids both over-reassurance and doom | Required |
| Under 90 words | Required |

*Model answer:* "The system writes the most plausible continuation of the text it's given. It has no
internal check for whether something is true, so a wrong answer looks exactly like a right one —
same confident tone, same formatting. I can't promise it will never be wrong. What I can promise:
a measured accuracy on a test set we control, that it cites the document behind every answer so you
can check, that it declines when it has no supporting source, and that we sample and review real
answers weekly so we'd notice if it got worse."

### Exercise solutions

**Exercise 1.**

1. **Expected.** Temperature 0.7 samples from the distribution.
2. **Expected behaviour of the model, and a defect of the system.** Citation form is highly
   learnable, content is not. The system must verify citations against retrieved sources.
3. **Expected.** Verbal confidence is generated text, not a measurement. It is a defect only if you
   built a threshold on it without measuring calibration.
4. **Defect of the prompt/system**, not surprising model behaviour. Instructions must constrain the
   model to the provided context and it must be measured for groundedness (M7-L19).
5. **Expected.** Infrastructure non-determinism — floating-point non-associativity, batching,
   hardware, and silent model updates.

**Exercise 2.** (Answers from the executed lab.)

1. **ECE = 0.069.** On average the model's stated confidence differs from its actual accuracy by
   about 6.9 percentage points. Crucially the *direction* varies: slightly under-confident below
   ~0.7, and increasingly over-confident above it (−0.034, −0.091, −0.139).
2. Threshold **0.99** gives the highest accuracy on auto-approved items (**0.837**) and automates
   only **2.5%** of traffic. Threshold 0.95 gives 0.827 at 10.4%.
3. **No.** The maximum achievable accuracy at any threshold is 0.837, short of 95% by more than 11
   points, and the curve has flattened — pushing from 0.95 to 0.99 buys 1 point of accuracy while
   losing three-quarters of the automated volume. *What to tell the business:* the 95% target is not
   reachable by thresholding this model; the options are a better model, a narrower task where
   accuracy is higher, a lower target, or human review of everything. Full marks require stating
   this as a finding rather than as a failure.
4. **Verified:** with `CAL_INTERCEPT = 0.0` and `CAL_SLOPE = 1.0`, ECE falls from 0.069 to **0.017**
   (residual sampling noise only) and threshold 0.95 now **MEETS TARGET** at 0.971. Those two values
   represent a **perfectly calibrated** model — one whose stated confidence equals its actual
   accuracy, so thresholding on confidence does exactly what you would expect.

**Exercise 3 — Rubric (max 24).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 4 | Mostly **epistemic** — the policy exists and is knowable, the model simply lacks it. Therefore retrieval is the primary fix. Aleatoric elements: questions about individual circumstances the policy does not determine, which should be routed to HR rather than answered |
| 2 | 6 | Ordered stack with residual failure per layer, e.g. retrieval (residual: model misreads retrieved text) → citation with programmatic verification (residual: correct citation, wrong interpretation) → abstention threshold (residual: confidently wrong *with* evidence) → structured output (residual: well-formed nonsense) → human escalation path (residual: over-trust, cost) |
| 3 | 4 | Precise trigger, e.g.: abstain if no chunk exceeds similarity threshold T; or if the top chunks come from documents flagged out-of-date; or if the question matches a defined sensitive category (termination, discrimination, pay disputes) — those route to a human regardless of confidence |
| 4 | 3 | Under 40 words, plain language, actionable. *Model:* "This assistant answers from our current HR policy documents and shows you the source for every answer. It can be wrong or out of date. For anything affecting your pay, leave balance or employment status, confirm with HR before acting." |
| 5 | 4 | Weekly measures: abstention rate; proportion of answers whose citations verify; sampled human review of ~30 answers; escalation rate to HR; user-reported corrections; retrieval hit rate on new questions |
| 6 | **3** | **Required.** Any honest residual, e.g.: the model can misread a correctly-retrieved clause and produce a confident wrong answer with a valid citation — no layer in this design catches that. Must also name who accepts it (HR system owner / named accountable person) |

Part 6 is mandatory. A submission claiming the design prevents all failures scores zero for that part.

---

<a id="m1-l11"></a>
## M1-L11 — Capability vs Reliability

### Quiz answers

**Q1 — B.** Capability = can do it sometimes under favourable conditions; reliability = how often the
whole system succeeds under real conditions.

**Q2 — C.** 0.95 × 0.90 × 0.95 × 0.98 × 0.90 = **0.7166** ≈ 71.7%.

**Q3 — C.** 0.90¹⁰ = 0.349 ≈ 35%.

**Q4 — B.** Replacing the step with deterministic code makes its rate ~1.0, removing it from the
product. *Why not A/C/D:* all leave a probabilistic factor in the chain.

**Q5 — C.** Authorization. Never delegated to a model — you need proof, not evidence.

**Q6 — B.** Have them write it down: faster, cheaper, testable, auditable, and it avoids an
evaluation problem you did not need.

**Q7 — B.** It changes the failure cost from a customer incident to an edit, so a reliability level
unacceptable for sending is genuinely useful for drafting.

**Q8 — B.** It assumes independent failures; real failures correlate, so measured reliability is
usually worse than `p^n`.

**Q9 — B.** "Who chose those five questions, and what happens on inputs nobody picked in advance?" —
the demo gap in one question.

**Q10 — Rubric.**

| Criterion | Full marks |
|---|---|
| Takes the demo seriously rather than dismissing it | Required |
| Distinguishes capability from reliability in plain language | Required |
| Includes at least one concrete number (compound reliability, failure count, or eval size) | Required |
| Names what the six weeks buys, specifically | Required |
| Under 100 words | Required |

*Model answer:* "The demo proves it can do this — that's real and it's the hard part. What it doesn't
tell us is how often it does it on inputs nobody picked in advance. Our pipeline has five model
steps; even at 95% each, that's 77% end-to-end, or about 115 bad tickets a day at our volume. The six
weeks is: build an evaluation set from real tickets so we can measure that number, move three steps
to plain code so they stop failing, and add a fallback for when the provider is down. I'd rather
show you 77% and a plan than a screenshot."

### Exercise solutions

**Exercise 1.**

| # | Task | Answer | Deciding question |
|---|---|---|---|
| 1 | VAT on an invoice | **Plain code** | Published specification; never compute money with a model |
| 2 | Is the email angry? | **AI** | Judgement over unstructured text |
| 3 | Password complexity | **Plain code** | Written-down policy, exact check |
| 4 | Summarise a thread | **AI** | Open-ended output over unstructured input |
| 5 | May X view Y? | **Plain code** | Authorization — never delegate |
| 6 | Extract `ORD-\d{6}` | **Plain code** | A regex does it exactly |
| 7 | Best of 5,000 help articles | **AI (retrieval/ranking)** | Semantic match over a large, changing set |

**Exercise 2.**

1. 0.97 × 0.93 × 0.99 × 0.88 × 0.95 × 0.99 = **0.7391** ≈ **73.9%**.
   (Working: 0.97 × 0.93 = 0.9021; × 0.99 = 0.8931; × 0.88 = 0.7859; × 0.95 = 0.7466; × 0.99 =
   0.7391.)
2. 2,000 × (1 − 0.7391) = **522** failures per day.
3. **Step 4 (0.88)** — the weakest. Raising it to 0.95: new total = 0.7391 × (0.95/0.88) =
   **0.7979** ≈ **79.8%**, saving ~118 failures/day. Improving the weakest step gives the largest
   gain because the relative improvement `Δ/p` is largest there.
4. **Step 4** again. Removing it entirely: 0.7391 / 0.88 = **0.8399** ≈ **84.0%**, saving ~202
   failures/day.
5. Deletion (+10.1 points) beats improvement (+5.9 points) by nearly double. **General principle:**
   deleting a step multiplies reliability by `1/p`, capturing the *entire* remaining failure rate of
   that step, whereas improving it captures only the portion you improved. So the first design
   question is "do we need this step at all, and can it be deterministic?" — not "how do we make this
   step better?"

**Exercise 3 — Rubric (max 25).**

| Part | Marks | Full-credit content |
|---|---|---|
| 1 | 4 | Decomposition, e.g.: detect anomaly (code/monitoring) → diagnose cause (AI) → choose remediation (AI) → validate the plan against policy (code) → execute (code) → verify result (code). Most steps should be code |
| 2 | 5 | Irreversible actions named: terminating instances, deleting resources, scaling down below capacity, modifying security groups or IAM. Each requires: explicit human approval, a dry-run/plan output, a blast-radius limit, and an idempotency key |
| 3 | 4 | Explicit per-step rates and an end-to-end product, with the assumption stated. Any internally consistent figure earns marks; hand-waving does not |
| 4 | **6** | Redesign where failure is cheap: the agent **diagnoses and proposes** a change as a reviewable plan (e.g. a pull request or a runbook entry) and **never executes** state-changing actions unattended. Read-only investigation is unrestricted; writes require approval. Explicit list of what it never does |
| 5 | **5** | Takes the idea seriously; names a concrete first build (e.g. read-only diagnosis assistant over CloudWatch and CloudTrail); states the reliability assumption openly; gives a measurable success criterion |
| 6 | 1 | Any honest "most likely wrong" with an early detection method, e.g. "I'm assuming diagnosis is 85% accurate; I'd validate that against 50 historical incidents before building anything else" |

*Zero marks for part 5* if the response only lists risks without proposing a build.

---

<a id="module-assessment"></a>
## Module 1 Assessment — Answer Key

Answers to [`assessments/module-01-assessment.md`](../assessments/module-01-assessment.md).
**Scoring:** Section A 1 mark each (10), Section B 3 marks each (15), Section C 15 marks.
**Total 40.** Pass = 28 (70%). Below 24, redo the lessons named in the remediation table.

### Section A — Recall and understanding (10 marks)

**A1 — C.** Where the decision logic came from. (M1-L02)

**A2 — B.** Ranking — the known-issue set is large and changes, so no fixed label space exists.
(M1-L03)

**A3 — C.** A hyperparameter: you set it before running and it changes behaviour. (M1-L05)

**A4 — B.** Once, on data that played no part in any decision. (M1-L06)

**A5 — B.** Self-supervised: the target is hidden text the data already contains. (M1-L07)

**A6 — C.** Overfitting. (M1-L08)

**A7 — B.** Target leakage — the field is populated as a consequence of the outcome. (M1-L09)

**A8 — D.** Nothing measurable — it is generated text, not a report of an internal probability.
(M1-L10)

**A9 — B.** 0.90⁵ = 0.590 ≈ 59%. (M1-L11)

**A10 — C.** Both training and validation error high and close together → underfitting → add
capacity. Adding regularisation (A) or more data (B) addresses overfitting, the opposite problem.
(M1-L08)

### Section B — Short answers (15 marks, 3 each)

**B1 — Why is leakage more dangerous than overfitting?** (3)
1 mark: overfitting shows a visible train/validation gap. 1 mark: leakage inflates *all* splits
equally, so every standard diagnostic passes. 1 mark: it is therefore discovered in production, after
commitments have been made.

**B2 — A model scores 100% on train, validation and test. What do you conclude and what do you do?**
(3)
1 mark: this is a leakage signature, not a success — the M1-L08 diagnostic assumes no leakage.
1 mark: name a check (single-feature predictive power; feature availability audit; rebuild test rows
as they appear at prediction time; check for cross-split duplicates). 1 mark: treat the result as a
bug report until explained.

**B3 — Explain why an LLM produces confident false statements, from the training objective.** (3)
1 mark: trained to predict likely continuations. 1 mark: no term in the objective for truth. 1 mark:
generation must always emit something, so gaps are filled with plausible text; fluency is produced
identically whether or not the content is correct.

**B4 — Your pipeline has 6 model steps at 0.95 each. Give the end-to-end figure and two ways to
improve it.** (3)
1 mark: 0.95⁶ = **0.735** ≈ 73.5%. 1 mark: remove a step (multiplies reliability by 1/p). 1 mark:
make a step deterministic so it leaves the product; or reshape the task so failure is cheap; or add
validation/repair per step; or checkpoint so a failure costs one step.

**B5 — When should a decision never be delegated to a model? Give two categories and the reason.**
(3)
1 mark each for two of: authorization/access control; arithmetic on money; exact lookup; format
validation; anything with a published specification. 1 mark for the reason: these require *proof* and
auditable explanation, and a statistical system provides evidence, not proof — and can be
manipulated by crafted input.

### Section C — Practical assignment (15 marks)

**The scenario.** A logistics company asks for "an AI system that predicts which deliveries will be
late, so we can warn customers proactively."

| Criterion | Marks | Full-credit content |
|---|---|---|
| **Task shape** | 2 | Binary classification (late / not late) at a stated decision point. Full marks require naming *when* the prediction is made — at dispatch, at booking, or in transit — because it changes everything downstream |
| **Label definition** | 2 | Precise and computable, e.g. `late = delivered_at > promised_at`. Must address censoring: exclude deliveries still in transit rather than labelling them "on time" |
| **Feature list with availability audit** | 3 | ≥6 features, each with the availability test applied. Must correctly reject at least two leaky candidates: `delivered_at`, `actual_transit_time`, `customer_complaint_filed`, `driver_reassigned`, `delivery_attempts` |
| **Split strategy** | 2 | **Temporal** (predicting forward; seasonality and carrier performance drift), plus grouped by route/carrier if entities repeat. Must justify, not just name |
| **Baseline** | 2 | A named trivial baseline: always predict "on time" (state the base rate), or a rule such as "late if the carrier's 30-day late rate exceeds X". Must state that the model has to beat it |
| **Reliability target and failure handling** | 2 | Acceptance criteria table: what rate is acceptable, what happens on a false positive (unnecessary warning, erodes trust) versus a false negative (no warning, worse), failure budget, fallback |
| **Honest limitation** | 2 | At least one stated residual, e.g.: warning a customer may change their behaviour and invalidate the label over time (feedback loop); the most predictive signals arrive after dispatch, so early predictions are weak; weather and carrier incidents are aleatoric and irreducible |

**Model outline of a full-marks answer:**

- **Shape:** binary classification, evaluated at the moment of dispatch (the latest point where a
  proactive warning is still useful).
- **Label:** `late = 1 if delivered_at > promised_at else 0`; exclude in-transit orders; exclude
  cancellations.
- **Features (available at dispatch):** carrier; origin and destination region; distance band;
  service level; package weight/size band; dispatch day-of-week and hour (cyclic); carrier's late
  rate over the trailing 30 days *as of dispatch*; public-holiday proximity; historical late rate for
  the destination postcode area *as of dispatch*.
- **Rejected as leakage:** `delivered_at` (is the label), `actual_transit_time`, `delivery_attempts`,
  `customer_complaint_filed`, `driver_reassigned` — all populated during or after the delivery.
- **Split:** temporal, train on months 1–9, validate 10–11, test 12; check that the minority class
  count in the test set is large enough to be meaningful.
- **Baseline:** always predict "on time" (scores 1 − base rate); plus a one-rule baseline on carrier
  late rate. The model must beat both.
- **Target:** ≥ 70% recall on late deliveries at ≤ 20% false-positive rate, measured on the held-out
  month. False positives cost customer trust; false negatives cost a missed warning. Fallback if the
  model is unavailable: warn on the carrier-late-rate rule alone.
- **Limitation:** proactive warnings may change customer and depot behaviour, so the label
  distribution shifts after launch and the offline estimate expires. Requires online monitoring and
  periodic retraining. Weather and carrier incidents are irreducibly random.

### Remediation guidance

| If you lost marks on | Re-read |
|---|---|
| A1, B5 | M1-L02 §5.4, M1-L11 §5.3 |
| A2 | M1-L03 §5.5 |
| A3 | M1-L05 §5.3 |
| A4, Section C split | M1-L06 §5.2–5.4 |
| A5, B3 | M1-L07 §5.2 |
| A6, A10 | M1-L08 §3, §5.4 |
| A7, B1, B2, Section C features | M1-L09 §5.1, §5.3 |
| A8, B3 | M1-L10 §5.2–5.3 |
| A9, B4 | M1-L11 §5.1 |
| Section C baseline/target | M1-L11 §5.5, M1-L03 §6 |
