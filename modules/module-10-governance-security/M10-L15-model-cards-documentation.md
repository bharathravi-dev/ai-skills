# M10-L15 — Model Cards and System Documentation

| | |
|---|---|
| **Lesson ID** | M10-L15 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M10-L02](M10-L02-intended-use-limitations-ownership.md), [M10-L09](M10-L09-transparency-oversight.md), [M10-L13](M10-L13-versioning-auditability.md) |

---

## 1. Learning objectives

1. **Write** a system card from a required-field list, and check coverage rather than assume it.
2. **Validate** the card against the questions specific readers bring to it.
3. **Reject** unfalsifiable claims and replace them with measurements that name a metric, set, size and date.
4. **Detect** staleness by comparing the card to the deployed configuration in CI.
5. **Generate** the fields that go stale, and write by hand only the fields that carry judgement.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Model card** | A document describing a *model*: training data, intended use, evaluation, limitations. |
| **System card** | A document describing the *deployed system*: the model plus retrieval, tools, oversight and controls. |
| **Required-field list** | The fields a card must contain for your organisation — a checkable contract. |
| **Falsifiable claim** | A statement someone could disagree with and settle by measurement. |
| **Staleness** | The card describing a configuration that is no longer deployed. |
| **Generated field** | A card field derived from an artefact (inventory, fingerprint, evaluation run). |
| **Written field** | A card field that requires a person's judgement and cannot be derived. |

---

## 3. Plain-language explanation

### 3.1 Three partial documents are not a card

§7.1 checks four documents against a 16-field list. The marketing one-pager covers **3/16**, the engineering README
**6/16**, the compliance template **8/16**. Each is complete in its own terms and none is a system card: none answers the
questions the other two answer. The card is one document containing all three views.

### 3.2 Check the card against readers, not against the template

§7.2 scores each document against five readers' questions. An end user gets **1/4** answers from the marketing page and
**4/4** from the system card. Someone deciding whether to reuse the system elsewhere — the highest-risk reader, because
they will change the context (L02) — gets **1/6** from the README and **6/6** from the card.

### 3.3 Half the sentences in a typical card cannot be checked

§7.3 classifies ten claims: **5 of 10 are unfalsifiable**. "The assistant is highly accurate", "we take privacy
seriously", "the system is unbiased", "humans review all high-risk outputs", "the model may occasionally make mistakes".
Each is replaced in the checkable half by a number with a metric, a set, a size and a date.

### 3.4 Cards go stale silently

§7.4 compares a card to the deployed configuration: **4 of 5 fields are stale** — a newer model, a rebuilt index, a
different prompt hash, `k` changed from 8 to 12. Nothing announced it. A card that is confidently wrong is worse than no
card, because people act on it.

### 3.5 Generate what rots; write what matters

§7.5: **10 of 16** fields can be generated from artefacts you already keep — the inventory row (L03), the ingestion
manifest, the run fingerprint (L13), the gated evaluation run (L12, L08), the retention policy (L06). The other **6**
require judgement: intended use, out of scope, known limitations, failure modes, human oversight, escalation.

---

## 4. Analogy

**A medicine's patient information leaflet.** It states what the medicine is for, what it is *not* for, who should not take
it, the measured rates of side effects, what to do if something goes wrong, and when it was last revised. It is regulated,
boring, and specific — nobody writes "this medicine is highly effective". It also comes in two registers: the leaflet for
patients and the summary of product characteristics for clinicians, from the same evidence.

### Where the analogy breaks

- **A medicine's formulation is fixed for years; your system changes weekly.** Hence CI checks against the deployed
  fingerprint (§5.5).
- **The leaflet's evidence comes from trials with a protocol; yours comes from an evaluation set you wrote.** The card must
  state the set and its size, because the reader cannot assume a standard (§5.4).

---

## 5. Detailed technical explanation

### 5.1 Model card vs system card

A model card describes the model. A **system card** describes what you deployed, which is where the risk lives:

| In a model card | Additionally in a system card |
|---|---|
| Model, version, training data summary | Retrieval corpus, index build, embedding model, chunking |
| Intended and out-of-scope uses | The *deployment's* intended use and users (L02) |
| Benchmark results | Results on **your** evaluation sets, per slice (L08, L12) |
| Known model limitations | Failure modes observed in *your* incidents (L14) |
| Ethical considerations | Human oversight, escalation, approval thresholds (L09, M8-L10) |
| — | Data handling, personal data classes, retention (L06) |
| — | Owner, review date, inventory id (L02, L03) |

If you use a hosted model, the provider's model card is an input to your system card, cited with its date — not a
substitute for it (L11).

### 5.2 The required-field list

`[REAL, measured]` §7.1 — 3/16, 6/16, 8/16, 16/16 coverage across four documents.

The 16 fields used in the lab, grouped by the question they answer:

| Question | Fields |
|---|---|
| Who owns this and when was it last looked at? | `owner`, `review_date` |
| What is it for, and not for? | `intended_use`, `out_of_scope`, `users_affected` |
| What does it run on? | `model_and_version`, `data_sources` |
| What data does it touch? | `personal_data`, `retention` |
| How good is it, and for whom? | `evaluation_sets`, `evaluation_results`, `subgroup_results` |
| How does it fail? | `known_limitations`, `failure_modes` |
| What happens when it does? | `human_oversight`, `escalation_path` |

Make the list explicit and check it mechanically. A field marked "not applicable" with a reason is a complete answer; a
field left blank is not.

### 5.3 Validate against readers

`[REAL, measured]` §7.2 — five readers, four documents.

| Reader | Brings the question |
|---|---|
| End user | Can I rely on this, and what do I do when it is wrong? |
| Integrator | What contract am I coding against, and how does it fail? |
| Security/privacy reviewer | What data, where, for how long, under whose control? |
| New on-call engineer | What is normal, what breaks, whom do I call? |
| Someone reusing it elsewhere | Does my context match the one it was evaluated in? |

The last reader is the one L02 exists for: **reuse in a new context is a new system**, and the card is what should stop
them — or tell them what to re-evaluate.

### 5.4 Falsifiable claims only

`[REAL, classified]` §7.3 — 5 of 10 checkable.

The replacement pattern is mechanical:

| Instead of | Write |
|---|---|
| "Highly accurate" | "Answer support 91.2% (CI 89.4–92.8), regression set v7, n=1200, 2026-09-02" |
| "We take privacy seriously" | "Prompts and outputs deleted after 30 days; metadata after 180" |
| "Unbiased" | "Worst-slice answer support 84.1% (French billing, n=260); slice list in §x" |
| "Humans review high-risk outputs" | "Refunds above £200 need approval; 412/412 approved by a named agent" |
| "May occasionally make mistakes" | "Abstention 6.4%; of 100 sampled abstentions, 88 were correct" |

The test: **could someone disagree with this sentence and settle it with a measurement?** Every number carries the set it
was measured on and the date — a number without them is a rumour with a decimal point.

### 5.5 Keeping the card true

`[REAL, measured]` §7.4 — 4 of 5 fields stale.

Make staleness a build failure:

```python
# docs/check_card.py -- run in CI
card = load_card("docs/system-card.yaml")
live = deployed_fingerprint()          # from L13
drift = {k: (card[k], live[k]) for k in live if card.get(k) != live[k]}
if drift:
    raise SystemExit(f"system card is stale: {drift}")
```

Plus a **review date** that expires: a card unreviewed for N months fails the inventory check (L03), even when the
generated fields match. Configuration drift and judgement drift are different problems and need different triggers.

### 5.6 Generate the perishable fields

`[REAL, classified]` §7.5 — 10 generated, 6 written.

```text
system-card.md
  ├── generated block  <- inventory row, ingestion manifest, run fingerprint,
  │                       latest gated evaluation, retention policy
  └── written block    <- intended use, out of scope, limitations, failure modes,
                          oversight, escalation
```

The generated block regenerates on every release and is never hand-edited. The written block changes when judgement
changes — after an incident (L14), a scope change (L02) or a new subgroup finding (L08) — and is reviewed by a person.
Keeping them separate is what stops the card becoming either stale or generic.

### 5.7 Publishing and registers

- **Internal** cards: complete, including the risk register references and incident history.
- **Customer-facing** summaries: the same facts in the same register as L09's user-facing communication — intended use,
  limitations, oversight, escalation — without internal identifiers or security detail.
- **Inventory link**: the card is the long form of the inventory row (L03); one id, two levels of detail, one owner.

### 5.8 Assumptions and limitations

- The 16-field list is this course's, not a standard. Frameworks differ (see L16); the practice of checking against an
  explicit list is what transfers.
- The lab's cards, claims and configuration are invented.
- Sector-specific documentation duties exist and are out of scope (L16).

---

## 6. Worked example — the card that was true in March

**The situation.** A team wrote a good system card at launch: intended use, out-of-scope list, evaluation results with
intervals, a named owner, an escalation path. It was reviewed and approved.

**Six months later**, a second team read it while deciding to reuse the assistant for a new customer segment.

1. The card said the model was `vendor-x-large@2026-06-11`. Production had moved to `@2026-09-01` under a routine
   upgrade (§5.5).
2. It reported 91.2% answer support on regression set **v7**. The set was now **v9** and the figure was 88.6% — still
   good, but the card's number had been measured on a different set (§5.4).
3. The out-of-scope list said "not for pricing or contractual questions". A tool had since been added that quoted
   delivery charges — a scope change nobody had taken back to the card (L02).
4. The reusing team relied on the card, deployed to the new segment, and hit the pricing case in week one.
5. The review found the card had **no review date** and no CI check.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Model version stale | Generate `model_and_version` from the run fingerprint; CI check (§5.5) |
| 2 | Results from a superseded set | Generate results from the latest gated run, with set version and date |
| 3 | Scope changed without the card | Scope change requires a card revision and re-approval (L02) |
| 4 | Reuse decided from a stale card | Card is the L02 gate for reuse; expire it |
| 5 | No review date | Review date in the inventory row; expiry fails the check (L03) |

**The general rule.** **A card is a claim about the system as it is today; if nothing checks that, it is a claim about the
day it was written.**

---

## 7. Practical activity

**File:** [`labs/m10/l15_model_cards.py`](../../labs/m10/l15_model_cards.py)

**No API key, no network, no third-party dependencies.** Fully deterministic (no randomness at all).

```bash
source .venv/bin/activate
python labs/m10/l15_model_cards.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. FOUR CARDS AGAINST A REQUIRED-FIELD LIST
============================================================================
  card                              present  missing   biggest gaps
  A: marketing one-pager                  3       13   out_of_scope, users_affected, data_sources...
  B: engineering README                   6       10   intended_use, out_of_scope, users_affected...
  C: compliance template                  8        8   data_sources, model_and_version, evaluation_sets...
  D: system card (this course)           16        0   none

  required fields: 16
  Card A describes the product. Card B describes the implementation. Card C
  describes the obligations. None of the three answers a question the other
  two answer -- which is why the card is ONE document with all of them.

============================================================================
2. WHOSE QUESTIONS DOES THE CARD ANSWER?
============================================================================
  reader                                         A     B     C     D
  an end user                                  1/4   0/4   2/4   4/4
  an integrator                                2/6   2/6   2/6   6/6
  a security reviewer                          1/5   3/5   4/5   5/5
  a new on-call engineer                       2/5   2/5   2/5   5/5
  someone deciding to reuse it elsewhere       1/6   1/6   3/6   6/6

  A card is not a form to complete; it is a set of answers for named readers.
  Write the reader list first, then check the card against it (M10-L09).

============================================================================
3. CAN THE CLAIM BE CHECKED?
============================================================================
  claim                                                                                         checkable
  The assistant is highly accurate.                                                                    NO
  Answer support was 91.2% (CI 89.4-92.8) on regression set v7, n=1200, 2026-09-02.                   yes
  We take privacy seriously.                                                                           NO
  Prompts and outputs are deleted after 30 days; metadata after 180.                                  yes
  The system is unbiased.                                                                              NO
  Worst-slice answer support was 84.1% (French billing, n=260).                                       yes
  Humans review all high-risk outputs.                                                                 NO
  Refunds above GBP 200 need approval; 412/412 such cases were approved by a named agent.             yes
  The model may occasionally make mistakes.                                                            NO
  Abstention rate 6.4%; of abstentions sampled (n=100), 88 were correct abstentions.                  yes

  checkable: 5/10
    NOT checkable: The assistant is highly accurate.                            -- no metric, no set, no number
    NOT checkable: We take privacy seriously.                                   -- no data class, no retention, no mechanism
    NOT checkable: The system is unbiased.                                      -- unfalsifiable as written; which subgroups, which metric?
    NOT checkable: Humans review all high-risk outputs.                         -- 'high-risk' undefined, 'review' undefined, no rate
    NOT checkable: The model may occasionally make mistakes.                    -- true of every system; carries no information

  The test: could someone disagree with this sentence and settle it with a
  measurement? If not, it is reassurance, and reassurance is not documentation.

============================================================================
4. HAS THE CARD GONE STALE?
============================================================================
  field         card says                     deployed                      status
  model         vendor-x-large@2026-06-11     vendor-x-large@2026-09-01     STALE
  index         kb-v7#build-2026-08-30        kb-v8#build-2026-09-10        STALE
  prompt_sha    eb4171e7e428                  a32fe82f110e                  STALE
  guardrail     safety-policy-v5              safety-policy-v5              ok
  k             8                             12                            STALE

  card fingerprint 071c33e573f1 vs deployed ced691c58c1a -> 4/5 fields stale
  A card written once and never checked becomes confidently wrong. Compare it
  to the deployed fingerprint in CI and fail the build on drift (M10-L13).

============================================================================
5. HOW MUCH OF THE CARD CAN BE GENERATED?
============================================================================
  field                 source                            generated?
  owner                 inventory row (L03)               auto
  intended_use          written by the owner (L02)        written
  out_of_scope          written by the owner (L02)        written
  users_affected        inventory row (L03)               auto
  data_sources          ingestion manifest (M7-L08)       auto
  personal_data         data map (L06)                    auto
  model_and_version     run fingerprint (L13)             auto
  evaluation_sets       evaluation harness                auto
  evaluation_results    latest gated run (L12)            auto
  subgroup_results      latest gated run (L08)            auto
  known_limitations     written, informed by failures     written
  failure_modes         incident history (L14) + written  written
  human_oversight       written by the owner (L09)        written
  escalation_path       written by the owner (L09)        written
  retention             retention policy (L06)            auto
  review_date           inventory row (L03)               auto

  auto-generated: 10/16    written by a person: 6/16
  The generated fields are the ones that go stale, so generate them. The written
  fields are the ones that carry judgement, so do not template them -- they are
  the reason a card is worth reading (M10-L02).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every coverage count, reader score, checkability verdict, staleness
  comparison and generated/written split above is computed by this script.

  ILLUSTRATIVE: the four cards, the claims and the deployed configuration are
  invented; the required-field list is this course's, not a standard.

  NOT SHOWN: published model cards from model providers, regulatory
  documentation duties, and the review process itself (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's three partial documents** are the normal state of affairs, and each team believes theirs is the document.

**Section 2's bottom row** — the reuse reader — is the one the card must serve, because they are creating a new system.

**Section 3's five NO rows** appear in almost every card ever written. Delete them or replace them with measurements.

**Section 4 is a CI check**, not an observation: 4 of 5 fields drifted with no announcement.

---

## 8. Common mistakes and troubleshooting

1. **Treating a provider's model card as your system card.** §5.1 — it describes the model, not your deployment.
2. **Filling a template rather than answering readers' questions.** §5.3.
3. **Unfalsifiable claims.** §5.4 — 5 of 10 in the lab, and probably more in yours.
4. **Numbers without a set version, size or date.** A result is meaningless without them (L12).
5. **Hand-editing fields that could be generated.** §5.6 — they will drift.
6. **Templating the fields that require judgement.** They become generic and unread.
7. **No review date or expiry.** The card outlives its truth.
8. **Scope changes that never reach the card.** L02 — reuse decisions are made from the card.

| Symptom | Likely cause | Fix |
|---|---|---|
| Nobody reads the card | Written for a template, not for readers | Rebuild from §5.3's reader list |
| Card contradicts production | No CI comparison | Fail the build on fingerprint drift |
| Reviewers ask for the same things every time | Missing required fields | Publish and check the field list |
| Evaluation numbers cannot be reproduced | Set version and date missing | Generate results from the gated run record |
| Card says "not for X" but the system does X | Scope change without card revision | Make card revision part of the change (L02) |

---

## 9. Security, privacy, reliability, cost

- **Security.** The internal card lists tools, data stores and boundaries — useful to an attacker. Publish a summary
  externally, not the internal document (L10).
- **Privacy.** Data classes, retention and deletion mechanisms are card fields, generated from the data map (L06).
- **Reliability.** Failure modes and escalation are what an on-call engineer reads at 3am; keep them concrete and current
  (L14).
- **Cost.** Generation makes cards nearly free to keep current; hand-maintained cards cost review time and drift anyway.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which of the 16 fields does your team's current documentation cover?
2. Why is the marketing one-pager not a system card, in §7.2's terms?
3. Rewrite "the system is unbiased" as a checkable claim.
4. Which field went stale in §7.4 without any model change?
5. Name three fields that must be written by a person and say why.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a fifth reader with their questions and score the four cards.
2. Add three claims from your own documentation to §7.3 and classify them honestly.
3. Add a field to `REQUIRED` that your organisation needs, and justify it.
4. Write the generated block for one system you work on, listing the source of each field.
5. Draft the customer-facing summary version of that card (§5.7).

### Exercise 3 — Challenge (~60 min)

1. Write the full system card for a system you own, all 16 fields.
2. Implement the CI staleness check against the deployed fingerprint and make it fail on drift.
3. Automate the generated block from your inventory, evaluation harness and fingerprint.
4. Have someone who has never seen the system read the card and list the questions it left open.
5. Add "card updated" to your change checklist for scope changes, and test it on the next one.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l15).)*

**Q1.** What does a system card describe that a model card does not?

- A. The deployment: retrieval, tools, oversight, data handling and owner
- B. The training data used to produce the model
- C. The benchmark results published by the provider
- D. The model's architecture and parameter count

**Q2.** In §7.1, how many of the 16 required fields did the engineering README cover?

- A. Three
- B. Sixteen
- C. Eight
- D. Six

**Q3.** How should a card be validated?

- A. By a governance committee sign-off
- B. Against the questions its named readers bring
- C. By checking it renders correctly in the documentation site
- D. By comparing it with a competitor's published card

**Q4.** Which reader is the reason L02's scope rules matter most?

- A. The end user
- B. The security reviewer
- C. Someone deciding to reuse the system elsewhere
- D. The new on-call engineer

**Q5.** What makes a claim checkable?

- A. It appears in the approved template
- B. It has been reviewed by two people
- C. It avoids naming specific numbers that may change
- D. Someone could disagree and settle it with a measurement

**Q6.** Which of these is *not* checkable as written?

- A. Humans review all high-risk outputs
- B. Abstention rate 6.4%, with 88 of 100 sampled abstentions correct
- C. Prompts and outputs deleted after 30 days
- D. Worst-slice answer support 84.1% on French billing, n=260

**Q7.** In §7.4, how many of the five fields had drifted from the deployed configuration?

- A. One
- B. Two
- C. Four
- D. Five

**Q8.** How should staleness be detected?

- A. During the quarterly governance review
- B. By a CI check comparing the card to the deployed fingerprint
- C. By asking the owner to confirm each release
- D. By version-controlling the card alongside the code

**Q9.** Which fields should be generated rather than written?

- A. Intended use and out-of-scope statements
- B. Known limitations and failure modes
- C. Versions, evaluation results, retention and owner
- D. Human oversight and escalation paths

**Q10.** Why should the judgement fields *not* be templated?

- A. Templated judgement produces generic text nobody reads
- B. Templates cannot represent uncertainty
- C. Regulators require free-text answers
- D. Generated fields would overwrite them

**Q11.** What should a customer-facing version of the card contain?

- A. The full internal document with identifiers removed
- B. The same facts in the register of user-facing communication, without security detail
- C. Only the intended-use statement
- D. The provider's model card plus your contact details

**Q12.** A card's numbers are correct but measured on evaluation set v7, while v9 is current. What is the problem?

- A. Nothing, provided the numbers were correct when measured
- B. Older sets tend to be smaller
- C. The set version does not need to be published
- D. The card reports results from a set the system is no longer evaluated on

**Q13.** *(Written, rubric-graded.)* In under 150 words: another team wants to reuse your assistant for a new customer
segment. Which parts of your system card should stop them, or tell them what to re-measure, and why?

---

## 12. Revision notes

- **One document, three views**: the lab's partial documents covered **3/16**, **6/16**, **8/16** fields.
- **Validate against readers**: the reuse reader scored **1/6** on a README and **6/6** on a system card.
- **Falsifiable only**: **5/10** lab claims were checkable; every number carries metric, set, size and date.
- **Cards go stale**: **4/5** fields had drifted; make it a CI failure against the deployed fingerprint (L13).
- **Generate 10, write 6**: generate what rots (versions, results, retention, owner); write what carries judgement
  (intended use, scope, limitations, failure modes, oversight, escalation).
- **The card is the reuse gate** (L02) and the long form of the inventory row (L03).

---

## 13. Completion checklist

- [ ] My system card covers an explicit required-field list, with "not applicable" reasons where used.
- [ ] I have validated it against at least four named readers' questions.
- [ ] Every claim in it is falsifiable, with a set version, size and date.
- [ ] A CI check fails the build when the card drifts from the deployed configuration.
- [ ] Generated and written blocks are separate, with the review date in the inventory.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M10-L02 (intended use, limitations, ownership) and M10-L03 (inventory rows the card expands) `[STABLE]`
- M10-L08 (subgroup results), M10-L12 (gated evaluation runs the card cites) `[STABLE]`
- M10-L09 (user-facing communication register) and M10-L13 (fingerprints for the staleness check) `[STABLE]`
- M. Mitchell et al., "Model Cards for Model Reporting" (2019) — origin of the model-card practice `[UNVERIFIED]`
- T. Gebru et al., "Datasheets for Datasets" (2018) — the dataset counterpart `[UNVERIFIED]`

---

## 15. Next lesson

→ [M10-L16 — NIST AI RMF, Legal Requirements vs Voluntary Frameworks, Residual Risk](M10-L16-frameworks-residual-risk.md)
places the whole module in context: which of these practices are obligations, which are choices, and what to do with the
risk that remains after every control is in place.
