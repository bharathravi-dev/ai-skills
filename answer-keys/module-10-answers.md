# Module 10 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple choice, a reason
each distractor fails.

> Module 10 quiz options are written to similar lengths with a balanced, unpatterned answer distribution, and carry no
> inline explanation of the correct choice. All rationale lives here.
>
> **Scope note.** This module teaches governance as engineering artefacts. Nothing in these answers is legal advice; where
> a question touches law, the answer is about the *engineering* consequence (see M10-L16).

| Lesson | Jump to |
|---|---|
| M10-L01 Governance, Safety, Security and Compliance are Four Different Things | [↓](#m10-l01) |
| M10-L02 Intended Use, Limitations and System Ownership | [↓](#m10-l02) |
| M10-L03 AI Inventories | [↓](#m10-l03) |
| M10-L04 Risk Registers and Risk Assessment | [↓](#m10-l04) |
| M10-L05 Data Provenance, Licensing and Permitted Use | [↓](#m10-l05) |
| M10-L06 Personal and Sensitive Data; Minimization, Retention, Deletion | [↓](#m10-l06) |
| M10-L07 Access Control and Tenant Isolation as Governance Controls | [↓](#m10-l07) |
| M10-L08 Bias and Subgroup Evaluation | [↓](#m10-l08) |
| M10-L09 Transparency, User Communication and Human Oversight | [↓](#m10-l09) |
| M10-L10 Security: Prompt Injection, Exfiltration and Tool Misuse | [↓](#m10-l10) |
| M10-L11 Model and Supplier Assessment | [↓](#m10-l11) |
| M10-L12 Release Evaluation Gates | [↓](#m10-l12) |
| M10-L13 Versioning, Configuration and Auditability | [↓](#m10-l13) |
| M10-L14 Incident Response, Rollback and Change Management | [↓](#m10-l14) |
| M10-L15 Model Cards and System Documentation | [↓](#m10-l15) |
| M10-L16 NIST AI RMF, Legal Requirements vs Voluntary Frameworks, Residual Risk | [↓](#m10-l16) |

---

<a id="m10-l01"></a>
## M10-L01 — Governance, Safety, Security and Compliance are Four Different Things

**Answers: C · A · D · B · A · C · B · D · A · B · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Governance is about ownership, purpose, scope and evidence. **A** is security; **B** is compliance; **D** is an evaluation question that informs safety. |
| 2 | **A** | No adversary, harm in ordinary use — a safety failure. **B** needs an attacker; **C** applies only where an obligation is engaged; **D** would be the missing decision about accuracy, not the fabrication itself. |
| 3 | **D** | The union covered every failure. **A** and **B** are single-lens counts; **C** matches no measurement. |
| 4 | **B** | Those two have an adversary and no other flag. **A** are safety-only; **C** are governance-only; **D** are compliance failures also caught elsewhere. |
| 5 | **A** | Every compliance failure in the set also triggered another lens, so nothing went unseen. **B**, **C** and **D** contradict the measurement. |
| 6 | **C** | It makes certain findings non-negotiable and defines the evidence and sign-off. **A** — every lens has an owner; **B** is security's job; **D** — the register is a governance artefact. |
| 7 | **B** | Security ∩ safety = 5: attacks that also harm users. **A**, **C** and **D** had different measured overlaps (7, 1 and 7 respectively). |
| 8 | **D** | It resists attackers yet harms users in normal use — 9 such failures had no attacker at all. **A** is a security-internal trade-off; **B** is compliant-but-ungoverned; **C** is an evidence gap. |
| 9 | **A** | A named person answerable for behaviour. **B**, **C** and **D** are teams, rotas and sponsors — none is accountable for behaviour. |
| 10 | **B** | The security review found the limit was only in the prompt, not enforced in the tool. **A** is safety; **C** is compliance; **D** is governance. |
| 11 | **C** | Without a test, log or record, a control is an intention. **A** is risk left after controls; **B** is an alternative control; **D** is an external obligation. |
| 12 | **D** | Governance artefacts must change as the system changes. **A**, **B** and **C** are what governance *is*. |

**Q13 rubric (5 marks).** One mark each for: **naming the three missing reviews** — safety, compliance and governance
(§5.1); **a concrete safety question** for the feature, e.g. what happens when it is wrong, confidently wrong, or wrong for
one subgroup, with an agreed threshold (§5.4, L08, L12); **a concrete compliance question** — data, disclosure, retention
or supplier terms, and who signs off (§5.4, L05, L06, L09, L11); **a concrete governance question** — named owner,
intended use and out-of-scope list, records kept (§5.1, L02, L03, L13); and **a reason grounded in the measurement or an
example** — e.g. 9 of 24 failures involve no attacker, so a security review cannot cover them, or an example of
secure-but-unsafe. Listing the words without a question for each caps the score at 2.

---

<a id="m10-l02"></a>
## M10-L02 — Intended Use, Limitations and System Ownership

**Answers: B · D · A · C · D · B · A · C · B · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | The build team's statement covered purpose, users, inputs, outputs, limitations and owner, but not decisions affected (nor out-of-scope, oversight or review date). **A**, **C** and **D** were all present. |
| 2 | **D** | It records uses the owner has decided the system must not serve, before launch. **A** is a disclaimer's purpose; **B** is a roadmap; **C** is monitoring output. |
| 3 | **A** | 13 of the 20 were out of scope. **B**, **C** and **D** do not match the measurement. |
| 4 | **C** | On six requests written afterwards the rules missed 4 and wrongly refused 1. **A**, **B** and **D** contradict the output. |
| 5 | **D** | A limit in the tool cannot be argued with by a model or a caller. **A**, **B** and **C** are advisory layers, useful but weaker (M9-L13). |
| 6 | **B** | Falsifiable claims can be tested; bounded scope can be enforced. **A**, **C** and **D** may all be true of an unreviewable statement. |
| 7 | **A** | Paging and detection are what ownership means in practice. **B**, **C** and **D** identify authorship or funding, not accountability. |
| 8 | **C** | Four of five limitations existed only in internal documents. **A**, **B** and **D** are the places users actually look, where most were absent. |
| 9 | **B** | Visibility at the moment of use is what changes behaviour. **A** overstates a legal claim this course does not make; **C** is false; **D** is not the reason. |
| 10 | **D** | Six of ten fields were stale. **A**, **B** and **C** do not match the measurement. |
| 11 | **C** | A new data source changes inputs, users and possibly scope. **A** is a backstop, not the mechanism; **B** and **D** do not change what the system does or affects. |
| 12 | **A** | Three jobs were added by accretion, with no scope list and no owner approval for the new tool. **B**, **C** and **D** were not part of the incident. |

**Q13 rubric (5 marks).** One mark each for: **a falsifiable purpose** naming the narrow task, not a benefit (§5.1); **users
and the setting** in which they use it; **inputs and outputs** stated concretely, including versions or sources where
relevant; **decisions affected plus either out-of-scope or human oversight**, showing the bound on what it may do; and **a
named owner or review date, plus one limitation with the specific place it is surfaced** (UI, refusal message, footer) per
§5.4. A statement of benefits with no bound or owner scores at most 2.

---

<a id="m10-l03"></a>
## M10-L03 — AI Inventories

**Answers: D · B · C · A · B · D · C · A · D · C · B · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | Shadow AI is production use missing from the inventory. **A** is a staging system (still worth registering, but not the definition); **B** is a ghost entry; **C** describes closed weights. |
| 2 | **B** | `intranet-bot`, `marketing-copy` and `ops-dashboard`. **A** is the ghost count; **C** is the matched count; **D** is the number of components with any AI signal. |
| 3 | **C** | Controls and evidence attached to a retired system protect nothing while appearing to. **A**, **B** and **D** are not consequences the lesson describes. |
| 4 | **A** | Evidence recorded against the old model no longer describes what runs. **B**, **C** and **D** are unaffected by the record's accuracy. |
| 5 | **B** | Another department's SaaS toggle leaves no trace in your repositories. **A**, **C** and **D** are exactly the signals a scan finds. |
| 6 | **D** | Three components, two of them unregistered. **A**, **B** and **C** do not match the measurement. |
| 7 | **C** | It is the "what breaks when this changes" question. **A** and **B** are capacity questions; **D** is lateral movement in a security context. |
| 8 | **A** | Tier by consequence and data, not by technology. **B** is the common mistake; **C** and **D** measure effort and spend. |
| 9 | **D** | Card, evaluation and subgroup evaluation were all missing. **A** is `support-assistant`'s gap; **B** and **C** contradict the output. |
| 10 | **C** | Reporting skips keeps the check honest — two entries were never compared. **A** inverts it; **B** and **D** are not why entries were skipped. |
| 11 | **B** | Differences surfaced and a tier-driven backlog make it operational. **A**, **C** and **D** can all be true of a decorative register. |
| 12 | **A** | With no data-class field, the question required interviews. **B**, **C** and **D** were not the cause. |

**Q13 rubric (5 marks).** One mark each for: **discovery from multiple sources** — code scanning plus procurement/expense,
egress logs, vendor questionnaires and staff survey (§5.2); **reconciliation against the existing list**, classifying
shadow, ghost and wrong-detail findings (§5.3); **a minimum schema** — owner, purpose reference, provider/model, data
classes, environments, tier, review date, dependencies (§5.1); **tiering by consequence and using it to require
artefacts** (§5.5); and **an expectation stated honestly** — typically far more than five, concentrated in shadow use such
as SaaS features and individual scripts, plus stale details on the known ones (§7.2, §6). An answer that only circulates a
questionnaire scores at most 2.

---

<a id="m10-l04"></a>
## M10-L04 — Risk Registers and Risk Assessment

**Answers: C · A · D · B · A · C · B · D · C · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | It names an event, a cause and a consequence, so it can be scored and controlled. **A**, **B** and **D** are topics; nothing about them can be estimated or treated as written. |
| 2 | **A** | Nine of ten positions differed. **B**, **C** and **D** do not match the measurement. |
| 3 | **D** | Likelihood band 1 multiplied by impact band 5 gives 5 — the lowest score on the register, despite a £900,000 consequence. **A** is false; **B** and **C** do not affect the matrix score. |
| 4 | **B** | Only the interpretation of the impact bands changed, and 9/10 positions moved. **A**, **C** and **D** were held constant. |
| 5 | **A** | Two risks 30× apart in expected loss shared a cell: the matrix discarded what separated them. **B** is not implied; **C** is a different problem; **D** does not follow from a tie. |
| 6 | **C** | Residual is what remains after effective controls. **A** is transfer; **B** is unrelated; **D** is a comparison artefact. |
| 7 | **B** | Residual rose for R1, R3, R4, R7 and R10, and one moved over appetite. **A** overstates; **C** contradicts the lab's two counts; **D** did not happen. |
| 8 | **D** | No test, log or record backs it. **A**, **B** and **C** each name a concrete piece of evidence. |
| 9 | **C** | Acceptance with a named owner, a date and a review interval. **A** is rationalising the score; **B** hides it; **D** is not a general rule and this course gives no legal advice. |
| 10 | **B** | Reputational and regulatory consequences rarely transfer, whatever the contract says. **A**, **C** and **D** all remain available. |
| 11 | **A** | Change events — new model, data source, automated action or user population — change likelihood and impact. **B** is a backstop; **C** and **D** do not change the system's behaviour. |
| 12 | **D** | Its matrix score of 10 sat below operational rows scored 12 and 16, although its expected loss was the largest. **A**, **B** and **C** contradict the example. |

**Q13 rubric (5 marks).** One mark each for: **the event with cause and consequence** (e.g. incorrect amount sent because
the limit is enforced only in the prompt, leading to money lost and complaints); **likelihood and impact with the
assumption or units stated**, not a bare band; **at least two controls, each with the evidence that it works** — a CI test
id, a monitoring alert, an approval record — and honest marking of any control with no evidence; **inherent and residual
stated separately**, with residual counting only evidenced controls; and **a treatment decision with an owner and a date**
(reduce / transfer / avoid / accept), plus a review trigger. An entry with controls but no evidence or owner scores at
most 3.

---

<a id="m10-l05"></a>
## M10-L05 — Data Provenance, Licensing and Permitted Use

**Answers: B · D · C · A · D · B · A · C · B · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Five sources permit commercial, customer-facing use. **A** is the internal-retrieval count; **C** and **D** contradict the measurement. |
| 2 | **D** | The same source answers differently for internal use, customer answers, quotation, training and sharing. **A** is irrelevant; **B** is not the reason; **C** is a separate field. |
| 3 | **C** | Five chunks reached audiences they were not licensed for. **A** — seven chunks remained usable; **B** and **D** did not occur. |
| 4 | **A** | Enforcement happens at retrieval, so the attribute must be on the chunk. **B**, **C** and **D** leave the retriever unable to act. |
| 5 | **D** | Three permitted answers required notices and the template rendered none. **A** inverts it; **B** is too narrow; **C** confuses the corpus-wide count with the answers measured. |
| 6 | **B** | Training absorbs content into weights: it cannot be cited and cannot be removed without retraining. **A** and **D** are false; **C** inverts the copying. |
| 7 | **A** | Default deny; quarantine until resolved. **B**, **C** and **D** all grant a permission nobody verified. |
| 8 | **C** | It resolves to seven roots including the unknown-licence scraped posts, two levels down. **A** ignores transitivity; **B** is arbitrary; **D** is the mistake the section exists to refute. |
| 9 | **B** | `derived_from` makes resolution to roots automatic. **A**, **C** and **D** are useful fields that do not link datasets. |
| 10 | **D** | Every source had been checked only for internal indexing. **A**, **B** and **C** were not the cause. |
| 11 | **C** | A new audience for the same corpus changes which permissions apply. **A**, **B** and **D** do not change permitted use. |
| 12 | **A** | They are independent: ownership does not settle privacy, and a licence does not exempt personal data. **B**, **C** and **D** each collapse the two questions. |

**Q13 rubric (5 marks).** One mark each for: **re-asking permission for the new use class and audience**, source by source
(§5.2, §6); **checking each source's terms for customer-facing use, verbatim quotation and attribution**, treating unknown
as deny (§5.1–§5.2); **moving licence attributes onto chunks and filtering at retrieval by audience** (§5.3); **rendering
required attributions and deciding policy on share-alike sources** (§5.4); and **recording the decision** — updated
inventory and intended-use statement, per-source permitted-use fields, manifest version, and a re-review trigger for the
next audience change (§5.5, L02, L03). Answering "check the licences" with no propagation or recording scores at most 2.

---

<a id="m10-l06"></a>
## M10-L06 — Personal and Sensitive Data: Minimization, Retention, Deletion

**Answers: A · C · B · D · B · A · D · C · A · B · D · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The name pattern only matched titled names, so it found 0 of 17. **B** and **C** contradict the output; **D** — no cross-type confusion occurred. |
| 2 | **C** | Two of ten variants were detected. **A** inverts it; **B** — false positives were not measured on variants and were 0 in-sample; **D** understates the misses. |
| 3 | **B** | It reduces exposure and catches obvious leaks. **A**, **C** and **D** treat a lossy heuristic as a guarantee. |
| 4 | **D** | Eight of the nine unused fields were personal or sensitive. **A** is the decision-logic count; **B** is the prompt count; **C** is the whole record. |
| 5 | **B** | Construct it from the fields the template and logic actually read. **A** leaks by default and relies on redaction; **C** and **D** are not tied to the task. |
| 6 | **A** | 404 of 500, i.e. 81%. **B**, **C** and **D** do not match. |
| 7 | **D** | Logs and backups were the two the job could not reach. **A**, **B** and **C** were all clearable once propagation existed. |
| 8 | **C** | The embeddings are derived from that person's words and enable retrieval about them. **A** is sometimes true but not the reason; **B** overstates; **D** is false. |
| 9 | **A** | 162 of 200 rows were unique on three quasi-identifiers. **B**, **C** and **D** are exactly the claims the measurement refutes. |
| 10 | **B** | Coarser geography and decade-banded ages, with department dropped. **A**, **C** and **D** leave the quasi-identifiers intact. |
| 11 | **D** | Weights cannot be deleted from; removal requires retraining. **A**, **B** and **C** all support deletion. |
| 12 | **C** | Deletion stopped at the database, leaving vectors, cached answers and an evaluation example. **A** is false; **B** and **D** were not the cause. |

**Q13 rubric (5 marks).** One mark each for: **enumerating the stores** — primary records, search index, vector index and
its chunks, caches, evaluation datasets, traces/logs, backups (§5.4); **the deletion mechanism per store**, including
rebuilding an index that cannot delete in place and subject-scoped cache keys; **explicit handling of logs and backups** —
write-time redaction, short retention, documented restore window, re-application after restore; **verification** — a test
subject inserted and erased end to end, with assertions of zero remaining references plus evidence retained; and **the
consequences** — re-running evaluation baselines after removing examples, and noting that model weights require retraining
rather than deletion (§5.3–§5.4, M13-L01). Answering "delete from the database and the index" scores at most 2.

---

<a id="m10-l07"></a>
## M10-L07 — Access Control and Tenant Isolation as Governance Controls

**Answers: D · B · A · C · A · D · B · C · D · A · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The cache key was the question text alone, so the first tenant's answer was reused. **A**, **B** and **C** were not involved — retrieval was correct. |
| 2 | **B** | 80 of 300. **A** is the keyed-by-tenant result; **C** is the number of cache hits; **D** overstates. |
| 3 | **A** | Twenty of sixty queries returned nothing, because the tenant's own documents never reached the global top K. **B** describes no filter; **C** and **D** were not measured. |
| 4 | **C** | Pre-filtering returned 300 results, 0 from other tenants and no empty sets. **A** leaks; **B** and **D** still post-filter. |
| 5 | **A** | It was added after the design, and per-handler checks only protect handlers that remember them. **B**, **C** and **D** were not the cause. |
| 6 | **D** | The accessor applies the predicate, so a new caller cannot omit it. **A** is not the argument; **B** is false; **C** is unrelated. |
| 7 | **B** | It is neither scoped nor logged. **A** is half the answer; **C** and **D** are different controls entirely. |
| 8 | **C** | Frequent break-glass means ordinary access does not meet operational needs. **A**, **B** and **D** do not follow from frequency. |
| 9 | **D** | Three had CI tests, one was manual, two had none. **A**, **B** and **C** contradict the output. |
| 10 | **A** | Only a recall check for a small tenant exposes post-filtering; the leak-oriented tests pass. **B**, **C** and **D** all pass under post-filtering. |
| 11 | **C** | Quality complaints from small customers came months before the panel leak. **A** came second; **B** never happened; **D** did not occur in the example. |
| 12 | **B** | `cacheScope: "private"` exists so caller-specific results are not shared across authorization contexts. **A**, **C** and **D** describe other mechanisms. |

**Q13 rubric (5 marks).** One mark each for: **enforcement at the data layer** — one accessor requiring the authorization
context, row-level security, or per-tenant credentials (§5.3); **pre-filtering in retrieval**, with namespaces or index
metadata filters rather than post-filtering (§5.2); **the authorization context in every cache key, quota, log and
background job** (§5.1); **break-glass governance** — scoped, reasoned, logged, time-boxed and independently reviewed
(§5.4); and **evidence** — named automated tests parametrised over all routes, a small-tenant recall check, cache-key
tests, and when each last ran (§5.5). "We filter by tenant" with no evidence scores 1.

---

<a id="m10-l08"></a>
## M10-L08 — Bias and Subgroup Evaluation

**Answers: B · D · A · C · C · B · D · A · B · C · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Miss rates were 17.1% and 39.8%. **A** understates by reporting only accuracy; **C** — false alarm rates were closer and favoured B; **D** — the intervals did not overlap. |
| 2 | **D** | Group A was 72% of the population, so the aggregate is essentially their experience. **A** did not happen; **B** is false — accuracy includes false negatives, but they are diluted; **C** is unrelated. |
| 3 | **A** | The interval spans "no gap" to "a very large gap". **B** misreads a confidence interval; **C** inverts the conclusion; **D** is the mistake the section exists to correct. |
| 4 | **C** | Wrongful exclusion is a false negative. **A** and **B** obscure it; **D** measures the opposite harm. |
| 5 | **C** | 65% vs 60% in referral and 25% vs 20% online. **A**, **B** and **D** contradict the constructed table. |
| 6 | **B** | Group B applied mostly through the online channel, which selects far fewer people. **A** — one threshold applied; **C** — the counts were large; **D** — the arithmetic is shown. |
| 7 | **D** | TPR gap fell to 3.3% while selection and precision gaps rose to 13.7% and 19.6%. **A**, **B** and **C** contradict the table. |
| 8 | **A** | Since the definitions conflict, the choice must be made explicitly and recorded with an owner. **B** overstates; **C** ignores legal constraints and alternatives; **D** is arbitrary. |
| 9 | **B** | Say the cell cannot support an estimate. **A** invites misreading; **C** and **D** substitute a different population's result. |
| 10 | **C** | Only a per-language gate with a minimum cell size would have failed the release. **A** without stratification still buries 8% of volume; **B** and **D** do not surface the subgroup. |
| 11 | **A** | Billing policies existed only in English, so retrieval had nothing to cite. **B** is the assumption the analysis overturned; **C** and **D** were not found. |
| 12 | **D** | Routing low-confidence cases to a human changes the process, not the model. **A**, **B** and **C** all modify the model or its outputs. |

**Q13 rubric (5 marks).** One mark each for: **choosing subgroups and the metric matched to the harm** — FNR/TPR for
exclusion, FPR for unwanted attention, plus selection rate (§5.1); **disaggregated reporting with confidence intervals and a
declared minimum cell size**, marking small cells unmeasurable (§5.2, §5.5); **stratification** to separate composition
effects from treatment, reporting both aggregate and stratified (§5.3); **a response plan if a gap is found** — investigate
data coverage, retrieval and process before the model, and re-measure after each change (§5.6, §6); and **governance** —
stating which fairness definition governs, who owns that choice, and gating the gap so it cannot regress (§5.4, L12).
"Check for bias across groups" with no metric, interval or action scores 1.

---

<a id="m10-l09"></a>
## M10-L09 — Transparency, User Communication and Human Oversight

**Answers: C · A · D · B · B · D · A · C · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | 1.2%, against 12.7% of all decisions leaving wrong. **A** is confidence-led review; **B** and **D** are the miscalibrated scenarios. |
| 2 | **A** | It transfers responsibility without changing outcomes. **B**, **C** and **D** are not produced by nominal review. |
| 3 | **D** | With calibrated confidence, model errors already scored low, so the sample caught nothing extra. **A**, **B** and **C** are not what the measurement isolated. |
| 4 | **B** | Catch rate fell to 36.3% and errors out rose to 8.2%. **A** inverts it — fewer cases were worked; **C** contradicts the table; **D** is a different row. |
| 5 | **B** | 136 of 256 errors carried a high score and were never examined. **A**, **C** and **D** were not observed. |
| 6 | **D** | 40 seconds per case against a 90-second review: about 44%. **A** applies at 20–40 cases/hour; **B** and **C** do not match. |
| 7 | **A** | The design has chosen rubber-stamping without recording the decision. **B** is wishful; **C** does not follow; **D** is the opposite — sampling matters more. |
| 8 | **C** | 3,465 cases for a 50% chance. **A** and **B** correspond to higher sample or fault rates; **D** is the 95% figure. |
| 9 | **D** | Automated checks — schema, citation, policy — run on everything and catch definable faults immediately. **A** scales cost; **B** changes behaviour, not detection; **C** discloses without detecting. |
| 10 | **B** | The console served agents, so the customer-facing routes were absent. **A**, **C** and **D** were present in that interface. |
| 11 | **C** | At the decision or refusal, where it can change what someone does. **A**, **B** and **D** are rarely read at the moment of use. |
| 12 | **A** | Overrides required a written justification and agreements did not. **B** may be true but was not the incentive; **C** and **D** were not found. |

**Q13 rubric (5 marks).** One mark each for: **measuring the override or disagreement rate** and comparing it with the
model's known error rate (§5.2, §6); **checking the time budget** — seconds per case against the time a real review needs,
given staffing and volume (§5.4); **checking the interface** — does the reviewer see the evidence and a calibrated,
explained confidence signal (§5.1, §5.3); **checking authority and friction** — is there an override path, is it equally
easy as agreeing, is it recorded (§5.1, §6); and **the change if the claim is false** — either fund and redesign review
(risk-based, evidence inline, equal friction) or restate the claim honestly as automation with targeted review and
sampling QA, with the detection latency stated (§5.5, §6). Answering "audit a sample of reviews" alone scores 2.

---

<a id="m10-l10"></a>
## M10-L10 — Security: Prompt Injection, Exfiltration and Tool Misuse

**Answers: B · C · D · A · B · C · D · D · A · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | All three must hold for data to be stolen through the assistant. **A** describes scale, not exposure; **C** lacks private data; **D** omits the way out. |
| 2 | **C** | The support agent, the email assistant and the browser agent. **A**, **B** and **D** do not match the table. |
| 3 | **D** | The client fetches the URL while rendering; no tool is involved. **A** and **B** are tool calls; **C** is an error path, not a fetch. |
| 4 | **A** | It blocked 15 and leaked 10. **D** is the allowlist result; **B** is auto-load; **C** inverts the counts. |
| 5 | **B** | It never resolves an attacker-chosen host, so the encoding is irrelevant. **A** is the opposite — it inspects nothing; **C** — egress control is still needed for tools; **D** — nothing prevents influence. |
| 6 | **C** | The injection acts with the agent's tools and permissions. **A**, **B** and **D** understate or misplace the inheritance. |
| 7 | **D** | A generic fetch plus raw SQL gives read/write over everything and an unrestricted way out. **A**, **B** and **C** are bounded by design. |
| 8 | **D** | Model-layer defences reduce frequency but cannot bound behaviour. **A**, **B** and **C** each have listed controls. |
| 9 | **A** | They lower how often an injection succeeds; they do not limit consequences. **B**, **C** and **D** overstate them. |
| 10 | **A** | The console auto-loaded remote images, so rendering the summary made the request. **B** was allowlisted; **C** and **D** were not involved. |
| 11 | **B** | Outbound fetches were not logged or alerted on, so nothing surfaced the leak. **A** does not detect; **C** and **D** address quality, not detection. |
| 12 | **C** | New tools, data sources or clients change the legs and the channels. **A** is too late; **B** is a backstop; **D** matters but is narrower than the rule. |

**Q13 rubric (5 marks).** One mark each for: **naming the exposure** — customer emails are untrusted content, account data is
private, and the reply tool is a way out, i.e. all three legs (§5.1); **egress and channel controls** — recipient allowlist
or restriction to replying to the original sender, no remote content rendering, egress proxy (§5.2–§5.3); **tool and
permission limits** — no generic fetch or SQL, least-privilege credentials, narrow account lookups (§5.4, M9-L12);
**authorisation and approval** — per-call checks against the authenticated user and human approval for anything
consequential, since the model will sometimes be fooled (§5.5, M9-L13); and **detection and recovery** — logging tool calls
and outbound requests, alerting on non-allowlisted destinations, and an incident path (§5.5, L14). Answers relying on
better prompts or an injection classifier as the main control score at most 2.

---

<a id="m10-l11"></a>
## M10-L11 — Model and Supplier Assessment

**Answers: C · B · A · D · B · A · C · D · A · C · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | A gate is a fact that disqualifies, answered before scoring. **A** and **B** are scored criteria; **D** describes something still open, not a requirement. |
| 2 | **B** | It failed the EU region and deletion SLA gates. **A** contradicts the table; **C** — it carried a support-tier cost; **D** — lock-in was not scored there. |
| 3 | **A** | Providers B and D. **B**, **C** and **D** overstate the eligible set. |
| 4 | **D** | The same supplier led under all four weightings; positions 2 and 3 swapped once. **A** and **B** contradict the output; **C** is not a finding. |
| 5 | **B** | It tells you whether the weights or the evidence are driving the decision. **A** — scores are unchanged; **C** is not a general requirement; **D** does not follow. |
| 6 | **A** | Self-hosted open weights had no per-token price. **B**, **C** and **D** all charge per token. |
| 7 | **C** | Engineering and operating effort dominated its total. **A** — the per-token price stayed zero; **B** — it had no support tier; **D** — egress was small beside engineering. |
| 8 | **D** | Lock-in is counted as the provider-specific features a design depends on. **A**, **B** and **C** measure commercial terms or volume. |
| 9 | **A** | The all-in design used eight features, six provider-specific. **B** had three; **C** had none; **D** contradicts the output. |
| 10 | **C** | Acquisition changes ownership, terms and roadmap. **A**, **B** and **D** do not change the supplier. |
| 11 | **D** | Evidence is the contractual text plus the mechanism you can verify. **A**, **B** and **C** are assertions or proxies. |
| 12 | **B** | Passing every gate says nothing about quality on your tasks. **A**, **C** and **D** are complementary activities, not things assessment replaces. |

**Q13 rubric (5 marks).** One mark each for: **gates answered first with evidence** — training use, retention and deletion,
region, sub-processors, notice periods (§5.1–§5.2); **evaluation on your own tasks**, with your metrics and subgroups, not
benchmark scores (§5.6); **total cost at your volume**, including support, engineering, migration and re-evaluation
(§5.4); **lock-in and exit** — provider-specific features used, abstraction at the call site, a tested migration path
(§5.4); and **a stated refusal condition** — e.g. our data would be used for training, no deletion commitment, no
deprecation notice period, or an unacceptable evaluation result — regardless of price (§5.2). An answer that compares
price and benchmarks only scores 1.

---
<a id="m10-l12"></a>
## M10-L12 — Release Evaluation Gates

**Answers: B · C · A · D · C · A · D · B · D · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | A gate is pre-registered; a threshold chosen after the number describes the number. **A** — the baseline informs the value, not the commitment; **C** — class does not decide whether it is a gate; **D** — approval does not make it prior. |
| 2 | **C** | 37% at n=100 for a system genuinely two points below the gate. **A** is the bound's pass rate for the *good* system; **B** is the point estimate at n=400; **D** is the good system at n=100. |
| 3 | **A** | The lower bound passes only if the evidence supports the threshold. **B** describes a slice gate; **C** is a hygiene rule; **D** describes averaging runs, a different technique. |
| 4 | **D** | Aggregate rose 1.9 points while three slices regressed. **A** and **B** contradict the output; **C** is false — weights were the slice sizes. |
| 5 | **C** | A weighted average is dominated by the largest slices, so small slices cannot move it. **A** is backwards; **B** is unrelated; **D** is true of small slices, not of aggregates. |
| 6 | **A** | ~10.6 points at n=100. **B** is n=300, **C** is n=1000, **D** is n=3000. |
| 7 | **D** | Its unsafe-output rate was 1.9% against a 0.5% hard gate. **A**, **B** and **C** all passed for that candidate. |
| 8 | **B** | Budget failures are trade-offs a named owner may accept and record. **A** is false — same run; **C** is backwards; **D** is an implementation detail, not the distinction. |
| 9 | **D** | About +4.9 points of pure selection effect. **A** is true only at k=1; **B** is backwards — smaller sets inflate more; **C** contradicts the output. |
| 10 | **A** | Re-measure the chosen candidate on a set it never influenced. **B** increases inflation; **C** and **D** discard the selection you actually made. |
| 11 | **B** | The evidence does not distinguish pass from fail; the answer is more data. **A** does not follow; **C** is the §6 failure; **D** ignores the gate. |
| 12 | **C** | Its minimum detectable effect is far larger than any tolerance worth setting. **A** may be true but is not the measurement problem; **B** is unrelated; **D** invents a convention. |

**Q13 rubric (5 marks).** One mark each for: **checking per-slice results**, not just the aggregate, with a stated
tolerance and floor (§5.4); **the interval**, i.e. whether 1.5 points is above the MDE at n=400 — it is not, ~3.4 points is
(§5.5); **hard-gate results** — safety, unsafe-output rate, slice regressions — which block regardless (§5.2);
**selection effects**, i.e. whether this candidate was the best of several on the same set, and re-measuring on a
confirmation set (§5.6); and **a stated block condition**, e.g. any slice below its floor or any safety-gate failure,
independent of the aggregate. An answer that only checks the aggregate scores 1.

---

<a id="m10-l13"></a>
## M10-L13 — Versioning, Configuration and Auditability

**Answers: D · B · C · B · A · D · B · C · A · C · D · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The rule is: if changing it can change the output, it is in the stamp. **A** and **B** are partial; **C** describes how logs end up missing the fields that matter. |
| 2 | **B** | Six of the eight changes touched neither model nor prompt. **A**, **C** and **D** contradict the computed result. |
| 3 | **C** | §7.2's four prompts render identically and hash differently; a label cannot distinguish them. **A** is incidental; **B** is false; **D** — hashing detects edits, it does not prevent them. |
| 4 | **B** | Six distinct builds over 26 weeks, changing in weeks 8, 12, 17, 21, 22 and 25. **A** contradicts the output; **C** is not shown; **D** is the whole problem — the alias never changes. |
| 5 | **A** | Each silent build change is a production release that skipped gates, evaluation and the change record. **B** invents a prohibition; **C** is not what was measured; **D** confuses ownership with version drift. |
| 6 | **D** | Design from the questions an incident or audit will ask. **A** and **C** produce the 1/9 and 3/9 levels; **B** ignores what each system actually needs. |
| 7 | **B** | Three of nine — model, identity and output. **A** is the minimal level; **C** is not a level in the lab; **D** is audit-ready. |
| 8 | **C** | Without a revision, a re-run retrieves different text from the "same" document. **A** is false; **B** is a separate concern; **D** is not the reason. |
| 9 | **A** | Evidential reproducibility promises you can show what happened, not that it re-runs identically. **B** is exact; **C** is statistical; **D** is not in your gift. |
| 10 | **C** | 45.38% at 30 days. **A** is 7 days, **B** is 90 days, **D** is 180 days. |
| 11 | **D** | Minimisation says delete early; auditability says keep. **A**, **B** and **C** are operational costs, not the governance tension. |
| 12 | **A** | One store means one retention rule, one deletion path, one access boundary. **B** is false at this scale; **C** is why you keep the store at all; **D** is not the reason. |

**Q13 rubric (5 marks).** One mark each for: **the run fingerprint** — model version, decoding, prompt hash, retrieval
index build, embedding and chunker versions, guardrail config, code commit (§5.1); **document ids with revisions** and the
retrieval record (§5.4); **identity and permissions** in force at the time (§5.4); **retention long enough** to cover the
three-month lag, per record class (§5.6); and **what you would change** — pin versions, add fingerprints, extend
retention, build an "explain this request" tool — stated as specific controls, not intentions. An answer that only says
"better logging" scores 1.

---

<a id="m10-l14"></a>
## M10-L14 — Incident Response, Rollback and Change Management

**Answers: C · B · D · B · D · A · B · C · A · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Mitigate, then diagnose — stop the harm first. **A** and **D** are diagnosis; **B** follows once the facts are known. |
| 2 | **B** | 17.5 hours mean, including triage. **A** is the canary; **C** is the hourly alert; **D** is the p90 for reports, not the mean. |
| 3 | **D** | It fired on 62% of quiet fortnights — an alert that will be muted. **A** and **B** contradict the output (**B** is the canary's rate); **C** is false by an order of magnitude. |
| 4 | **B** | Exposure is a multiplier; detection time is an addend. **A** and **C** are not how the lab is constructed; **D** is false — the base rate is the same. |
| 5 | **D** | Sent emails cannot be unsent. **A**, **B** and **C** all revert by configuration change. |
| 6 | **A** | The reverse migration ships with the forward one or it does not exist when needed. **B**, **C** and **D** are all after the fact. |
| 7 | **B** | Severity is set by the kind of harm; volume adjusts urgency. **A** is false; **C** is a legal question, not the classification rule; **D** overstates — the exposure may be contained, and it is still SEV1. |
| 8 | **C** | Eleven of the twelve are innocent. **A** is the 4-change case; **B** counts the guilty one too; **D** describes the outcome after bisecting, which costs 3.7 deploys. |
| 9 | **A** | The commander decides and coordinates and is deliberately not debugging. **B** and **D** are other people's jobs; **C** inverts the authority — on-call may roll back alone. |
| 10 | **D** | Control changes with owners and dates. **A** is the opposite of blameless; **B** and **C** are outputs, not the purpose. |
| 11 | **C** | Mitigate at the boundary: flag off, read-only, route to humans. **A** risks a second incident; **B** leaves harm running; **D** changes the label, not the harm. |
| 12 | **A** | The alias switch is what makes an index rebuild revertible. **B** is not the reason; **C** is false; **D** confuses retention with rollback. |

**Q13 rubric (5 marks).** One mark each for: **stop the harm first** — disable the email tool or the agent path, before
diagnosis (§5.3); **assess and contain the blast radius** — which 40 customers, what was sent, what correction is needed
(§5.2); **severity and roles** — SEV1 given money and customer impact, named commander, comms owner (§5.5);
**communication and correction**, since the emails cannot be unsent (§5.4, L09); and **three controls** — e.g. human
approval for outbound customer email, per-run caps and idempotency, an outbound-volume monitor with a measured false-alarm
rate (§5.1, M8-L10, M8-L12). An answer that only says "roll back" scores 1 — the emails are a one-way door.

---

<a id="m10-l15"></a>
## M10-L15 — Model Cards and System Documentation

**Answers: A · D · B · C · D · A · C · B · C · A · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The system card describes the deployment: retrieval, tools, oversight, data handling, owner. **B**, **C** and **D** are all model-card content. |
| 2 | **D** | Six of sixteen. **A** is the marketing one-pager, **C** is the compliance template, **B** is the full system card. |
| 3 | **B** | Against the questions its named readers bring. **A** is a process step, not validation; **C** is formatting; **D** tells you nothing about your own readers. |
| 4 | **C** | Reuse in a new context is a new system — the L02 rule. **A**, **B** and **D** are readers of an existing deployment. |
| 5 | **D** | Falsifiability: could someone disagree and settle it by measurement? **A** and **B** are process; **C** is the opposite of checkability. |
| 6 | **A** | "High-risk" and "review" are undefined and no rate is given. **B**, **C** and **D** each name a number, a period or a slice with its size. |
| 7 | **C** | Four of five — model, index, prompt hash and `k`; only the guardrail version matched. **A**, **B** and **D** contradict the output. |
| 8 | **B** | A CI comparison against the deployed fingerprint fails the build. **A** is too slow; **C** does not scale and drifts; **D** stores the card without checking it. |
| 9 | **C** | Versions, evaluation results, retention and owner all derive from artefacts you already keep. **A**, **B** and **D** are the judgement fields. |
| 10 | **A** | Templated judgement produces generic text nobody reads — and it is the reason the card exists. **B** is false; **C** invents a requirement; **D** is an implementation detail, avoided by separating the blocks. |
| 11 | **B** | The same facts in the register of user-facing communication, minus internal identifiers and security detail. **A** leaks the threat surface; **C** is incomplete; **D** is not your system. |
| 12 | **D** | The published results were measured on a set the system is no longer evaluated against. **A** ignores that readers act on the number today; **B** is irrelevant; **C** contradicts §5.4. |

**Q13 rubric (5 marks).** One mark each for: **intended use and out-of-scope** as the first gate on reuse (§5.1, L02);
**users affected and the evaluation sets** — whether the new segment is represented at all (§5.3); **subgroup results**,
so the new population's slice can be checked or flagged as unmeasured (L08); **known limitations and failure modes**
observed in the current context (L14); and **an explicit statement of what must be re-measured** before reuse — a new
evaluation set for the new segment, new slice gates, and a card revision. An answer that just says "check the card"
scores 1.

---

<a id="m10-l16"></a>
## M10-L16 — NIST AI RMF, Legal Requirements vs Voluntary Frameworks, Residual Risk

**Answers: C · B · D · D · A · A · B · D · A · C · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | GOVERN, MAP, MEASURE, MANAGE. **A** is the NIST Cybersecurity Framework; **B** is the plan-do-check-act cycle; **D** is invented. |
| 2 | **B** | MEASURE, at 3 of 16 lessons. **A** was 8, **C** and **D** were 7 each. |
| 3 | **D** | Gap analysis — find the questions you cannot answer. **A** is ISO/IEC 42001's territory and is a different activity; **B** is false, the controls are yours; **C** is a by-product, not the use. |
| 4 | **D** | Version pinning is pure engineering discipline; no framework asks for it. **A** and **B** are obligations; **C** is a framework expectation. |
| 5 | **A** | It wastes effort and erodes trust once someone checks. **C** is the consequence of the *opposite* error; **B** is invented; **D** does not follow. |
| 6 | **A** | 1.09% per year after five partial controls. **B** is the residual with the strongest control removed; **C** is the error the section exists to correct; **D** is the value after three controls. |
| 7 | **B** | Each control acts on what the previous one left. **A** confuses likelihood with impact; **C** is a recommendation, not a mechanism; **D** is a unit, not a reason. |
| 8 | **D** | Controls sharing a dependency fail together, so they do not multiply. **A** and **B** do not affect independence; **C** affects accuracy of the estimates, not the assumption. |
| 9 | **A** | Reduce, accept in writing with a named person and review date, or do not ship. **B** is the non-answer the section rules out; **C** moves the goalposts; **D** is estimate-shopping. |
| 10 | **C** | Whoever bears the consequence should accept it. **A** is unsupported; **B** is backwards — the organisation assigns it; **D** is an efficiency argument, not the reason. |
| 11 | **B** | None of the four worked. **A**, **C** and **D** contradict the output. |
| 12 | **C** | A control has a measurement that shows it works; an artefact only exists. **A**, **B** and **D** are all properties an ineffective artefact can have. |

**Q13 rubric (5 marks).** One mark each for: **a MEASURE-column measurement** — e.g. the MDE of the evaluation set against
the tolerance the gate claims (§5.1, L12); **a slice measurement**, showing which populations the set can actually resolve
(L08); **an operational measurement** — time-to-detect and the quiet-period false-alarm rate of the monitors (L14); **a
records measurement** — retention against complaint lag, or an "explain this request" attempt on a real old request (L13);
and **the framing**, that the review asked whether artefacts exist while these ask whether controls work (§5.5). An answer
that lists documents to produce scores 1.

---

*Module 10 answer key complete: all 16 lessons.*
