# M10-L06 — Personal and Sensitive Data: Minimization, Retention, Deletion

| | |
|---|---|
| **Lesson ID** | M10-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M10-L05](M10-L05-data-provenance-licensing.md), [M7-L16](../module-07-rag/M7-L16-incremental-updates-deletion-propagation.md) |

> **Scope note.** Engineering practice only. Definitions of personal data, lawful bases and individuals' rights differ by
> jurisdiction and are not taught here (M10-L16). What this lesson gives you is the machinery: find it, keep less of it,
> delete it everywhere, and stop calling it anonymous when it is not.

---

## 1. Learning objectives

1. **Measure** what a detector finds and misses, and explain why detection alone is not a control.
2. **Apply** minimisation: compare fields collected with fields actually used, and cut what a model never needed.
3. **Implement** retention and deletion that reaches every derived store, and handle logs and backups explicitly.
4. **Trace** a single erasure request across stores, including a vector index.
5. **Test** whether "pseudonymised" data is re-identifiable, using k-anonymity on quasi-identifiers.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Personal data** | Data relating to an identifiable person — including data that identifies them in combination with other data. |
| **Special-category / sensitive data** | Categories treated as higher risk (health, biometrics, beliefs, sexual orientation, and similar), by law and by common sense. |
| **Minimisation** | Collecting, sending and keeping only what the task requires. |
| **Pseudonymisation** | Replacing direct identifiers with keys, while the data still relates to a person. |
| **Anonymisation** | Making re-identification infeasible. Rare, and easy to claim wrongly. |
| **Quasi-identifier** | A field that identifies someone in combination with others (postcode, birth date, job title). |
| **k-anonymity** | Every record shares its quasi-identifier combination with at least k−1 others. |
| **Deletion propagation** | Removing data from every derived store, not just the primary one. |

---

## 3. Plain-language explanation

### 3.1 Detection finds the easy half

§7.1 runs a regex detector over 120 synthetic messages. On the formats it was written for it finds emails, phones, card
numbers, postcodes and dates of birth at **100% recall**, with **0 false positives** — and finds **0 of 17 names**. Then
the same detector meets ten everyday **format variants**: `07700 900123`, `+44 7700 900123`, `sw1a 1aa`, `3 Feb 1975`,
`P.NAIR (at) example.com`. It finds **2 of 10**.

That is the honest shape of PII detection: excellent on the formats you anticipated, blind to the rest, and structurally
weak on names. Use it to find and reduce exposure, not to certify that a store is clean.

### 3.2 The cheapest privacy control is not sending the data

§7.2 takes a 14-field customer record. The prompt template renders **5** fields; the decision logic reads **3**. **Nine
fields are used by neither**, and **8 of those are personal or sensitive** — email, phone, both addresses, date of birth,
card last four, support history, IP address. Passing the whole record to a model would expose all eight to a third party,
to logs and to every trace viewer, for no benefit.

### 3.3 Deletion has to reach the copies

§7.3: with a 90-day policy, **404 of 500** conversations are past their date. A deletion job that only touches the primary
database leaves the data in the search index, the vector index, the answer cache, the application logs, the evaluation
dataset and the backups. With propagation implemented, two remain — **logs and backups** — and those need explicit
answers rather than silence.

### 3.4 One person, seven stores

§7.4 traces a single erasure request. Five stores can be cleared immediately; **application logs and nightly backups
cannot**. The vector index matters even though it stores numbers: the embeddings were derived from that person's words
and support retrieval about them.

### 3.5 Removing the name is not anonymisation

§7.5 builds 200 "pseudonymised" rows — names replaced by `U0001`-style keys, keeping postcode district, birth year and
department. **162 rows (81%) are the only row with their combination**, and **every row** sits in a group smaller than 5.
Generalising to postcode district plus birth *decade*, and dropping department, cuts unique rows to **3**.

---

## 4. Analogy

**A hospital discharge summary.** Blanking the patient's name does not make the note anonymous if it still says "62-year-old
retired lighthouse keeper from a village of 300". Minimisation is writing only what the next clinician needs. Retention is
the rule that says old notes are destroyed. Deletion propagation is remembering that the note was photocopied into three
other files — and that the archive box in the basement has its own schedule.

### Where the analogy breaks

- **Paper copies are countable; derived data is not obviously a copy.** An embedding, a cached answer, a fine-tuned weight
  and an evaluation example are all "the note", in forms that look nothing like it (§5.4, M13-L01).
- **A clinician reads one note at a time; a model's context can assemble a profile from fragments** that were individually
  innocuous — which is why minimisation at the prompt boundary matters so much (§5.3).

---

## 5. Detailed technical explanation

### 5.1 Finding it

`[REAL, measured]` §7.1: 100% recall on anticipated formats, **0%** on plain names, **2/10** on format variants, 0 false
positives on 17 clean texts.

Practical consequences:

- **Use detection for reduction, not assurance.** It is good for redacting logs (M9-L12), flagging fields at ingestion and
  spotting obvious leaks — not for proving a corpus contains no personal data.
- **Names and free text need different tools** (NER models, allow-listed vocabularies) and still miss cases. Budget for
  that rather than assuming a clean sweep.
- **Measure recall on *variants*, not on the examples your patterns were written from.** The in-sample/variant gap here —
  100% versus 20% — is the same overfitting trap as M9-L12's log redactor.
- **Prefer structure to search.** If a field is known to hold an email, you do not need to detect it; you need to decide
  whether to send it at all.

### 5.2 Minimisation, field by field

`[REAL, measured]` §7.2: 14 collected, 5 rendered, 3 read by logic, **8 personal fields used by nothing**.

A workable method:

1. Write the prompt template and the decision function first.
2. Extract the fields each actually reads (as the lab does with a regex over the template).
3. Build the payload from **that list**, not from the record object. `record.dict()` is how whole customer records end up
   in provider logs.
4. For fields needed only as keys, pass a pseudonym (`customer_ref`) and resolve locally.
5. Re-check when the prompt changes — a new sentence in a template can add a field silently.

Minimisation also applies to **what you keep**: shorter retention on transcripts, aggregate metrics instead of raw
examples, and evaluation sets built from consented or synthetic data (M5-L18) rather than live customer text.

### 5.3 Retention

`[REAL, measured]` §7.3: 404/500 records past a 90-day policy.

- Set retention **per data class**, not per system: transcripts, embeddings derived from them, evaluation examples, traces
  and logs may each need different periods.
- Make the deletion job **scheduled, monitored and alerting** — a silent failure looks identical to a clean database.
- Record an **exception register** for anything you cannot delete on time, with a reason, an owner and an expiry (L04).
- Track **age distribution**, not just the count deleted: 81% overdue is a system that has never run its job, and no
  dashboard would show that from deletion counts alone.

### 5.4 Deletion propagation

Every derived store is a copy:

| Store | Delete | Notes |
|---|---|---|
| Primary database | Row delete | Easy, and where most jobs stop |
| Search index | Document delete | Reindex if deletes are soft |
| **Vector index** | Delete chunk + vector | Some indexes cannot delete in place; rebuild (M6-L10) |
| Answer cache | Key-scoped invalidation | Keys must include the subject or source id (M9-L06) |
| Evaluation datasets | Remove examples | Then re-run baselines: your metrics change (M10-L12) |
| Traces / logs | Redact at write time; short retention | Deleting from logs after the fact is rarely feasible |
| Backups | Documented restore window; re-apply deletions after restore | Note the exception with an expiry |
| **Model weights** | Not deletable; retrain | The reason "retrieval, not training" is a privacy decision (M13-L01) |

`[REAL, measured]` §7.4: 5 of 7 stores clearable now; logs and backups not. An erasure workflow should state, per store,
*what happens and by when* — including the stores where the answer is "this is retained for N days in backups, then
overwritten".

### 5.5 Pseudonymisation versus anonymisation

`[REAL, measured]` §7.5: 81% of rows unique on three quasi-identifiers; 100% in groups smaller than 5; after
generalisation, 3 unique rows remain.

- **Pseudonymised data is still personal data.** It keeps every obligation: access control, retention, deletion, and
  inclusion in the inventory's `data_classes` (L03).
- **Test before claiming anonymity.** k-anonymity is crude — it says nothing about attribute disclosure or linkage to
  outside datasets — but it is enough to stop a bad claim, and it is three lines of code.
- **Generalise or suppress** to raise k: coarser geography, banded ages, dropped fields. Expect to lose analytical value;
  that trade-off is the decision, and it belongs in the register with a named owner.

### 5.6 Assumptions and limitations

- All data here is synthetic; the detector is deliberately simple; k-anonymity is one weak measure among several.
- Legal definitions, lawful bases, retention obligations and the scope of individuals' rights are jurisdiction-specific
  and out of scope (L16).
- Techniques such as differential privacy, secure enclaves and formal de-identification standards are not covered.

---

## 6. Worked example — the assistant that could not forget

**The situation.** A retailer's support assistant retrieved from a vector index built from customer conversations, and
kept an answer cache to cut costs. A customer exercised their right to erasure. The support team deleted the customer's
row and confirmed completion within a day.

**Six weeks later**, the same customer contacted support again — and the assistant's answer referred to their previous
complaint, by name.

**Investigation.**

1. The deletion job cleared the **primary database only** — §7.3's naive case.
2. The **vector index** still held 12 chunks embedded from their transcripts; deletion had been treated as a database
   problem, and vectors as "just numbers" (§5.4).
3. The **answer cache** held two answers containing their address, keyed by question text and never invalidated by
   subject.
4. An **evaluation example** built from their complaint remained in the regression set, so their words were being sent to
   a model on every release.
5. **Logs** held 47 lines with their email and IP, because redaction ran on ingestion but not on request logging.

| # | Fix | Where |
|---|---|---|
| 1 | Deletion propagates to search, vector, cache and evaluation stores | §5.4 |
| 2 | Cache keys include a subject reference so they can be invalidated | §5.4, M9-L06 |
| 3 | Evaluation sets built from consented or synthetic data; erasure removes examples and triggers a baseline re-run | §5.3, M10-L12 |
| 4 | Redaction at log write time, plus 30-day log retention | §5.4, M9-L12 |
| 5 | Documented backup window with expiry, and re-application of deletions after any restore | §5.3 |

**The general rule.** **Erasure is a property of the system, not of the database.** If you cannot list every store a
person's data reaches, you cannot honour a deletion request — and the vector index is the one teams forget.

---

## 7. Practical activity

**File:** [`labs/m10/l06_personal_data.py`](../../labs/m10/l06_personal_data.py)

**No API key, no network, no third-party dependencies.** All data is synthetic and generated in the file.

```bash
source .venv/bin/activate
python labs/m10/l06_personal_data.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. FINDING PERSONAL DATA: WHAT A REGEX DETECTOR CATCHES
============================================================================
  email     detected in 18/18 texts containing it   recall 100%
  phone     detected in 17/17 texts containing it   recall 100%
  card      detected in 17/17 texts containing it   recall 100%
  postcode  detected in 17/17 texts containing it   recall 100%
  dob       detected in 17/17 texts containing it   recall 100%
  name      detected in  0/17 texts containing it   recall 0%
  false positives on 17 texts with no personal data: 0

  the same detector on 10 everyday FORMAT VARIANTS: 2/10 found
    missed email     my address is P.NAIR (at) example.com
    missed phone     ring 07700 900123 after six
    missed phone     my mobile is +44 7700 900123
    missed card      the card ending 1234 was charged twice
    missed postcode  delivery to sw1a 1aa was late
    missed dob       I was born on 3 Feb 1975
    missed dob       d.o.b. 1975-02-03
    missed name      this is Priya Nair following up

  Names are the gap: without a title they look like any other words, and a
  pattern that matches capitalised pairs would flag product names and places.
  Detection finds structured identifiers; it does not make a system compliant.

============================================================================
2. MINIMISATION: COLLECTED VS ACTUALLY USED
============================================================================
  fields on the record            : 14
  fields the prompt renders       : 5  ['customer_name', 'delivery_status', 'items', 'order_id', 'order_total']
  fields the decision logic reads  : 3  ['delivery_status', 'order_id', 'order_total']
  fields used by neither           : 9  ['email', 'phone', 'billing_address', 'delivery_address', 'date_of_birth', 'card_last4', 'marketing_optin', 'support_history', 'ip_address']
  of those, personal or sensitive  : 8  ['email', 'phone', 'billing_address', 'delivery_address', 'date_of_birth', 'card_last4', 'support_history', 'ip_address']

  Sending the whole record to the model would expose 8 unnecessary personal fields
  to a third party, to logs, and to anyone who later reads the trace. Pass the
  fields the task needs, and pseudonymise the ones it needs only as a key.

============================================================================
3. RETENTION AND WHERE DELETION DOES NOT REACH
============================================================================
  500 support conversations; policy says delete after 90 days
  past the policy date: 404 (81%)

  a deletion job that only touches the primary store leaves data in:
    - search index
    - vector index
    - answer cache
    - application logs
    - evaluation dataset
    - nightly backups

  with propagation implemented, remaining: ['application logs', 'nightly backups']
  Logs and backups need their own answer: shorten log retention and redact at
  write time; for backups, record the maximum restore window as a documented
  exception with an expiry, and re-apply deletions after any restore.

============================================================================
4. ONE ERASURE REQUEST, TRACED
============================================================================
  primary database     row in customers, 14 orders                    deletable now
  search index         3 documents mentioning the name                deletable now
  vector index         12 chunks embedded from their transcripts      deletable now
  answer cache         2 cached answers containing their address      deletable now
  application logs     47 lines containing email and IP               NOT reachable by the job
  evaluation dataset   1 example built from their complaint           deletable now
  nightly backups      present in 35 daily snapshots                  NOT reachable by the job

  stores the deletion job cannot clear today: 2 (application logs, nightly backups)
  The vector index matters even though it holds numbers, not text: embeddings
  are derived from the person's words and can support retrieval about them, so
  they are in scope. Delete the chunk AND its vector, and rebuild if the index
  cannot delete in place (M6-L10).

============================================================================
5. 'PSEUDONYMISED' IS NOT 'ANONYMOUS': k-ANONYMITY
============================================================================
  200 rows, names replaced by pseudonyms
  distinct combinations of ('postcode_district', 'birth_year', 'dept'): 180
  rows that are the ONLY one with their combination (k=1): 162 (81%)
  rows in a group smaller than k=5: 200 (100%)

  after generalising: postcode district + birth DECADE, dropping dept
    distinct combinations: 35;  k=1 rows: 3

  Removing the name does not make a row anonymous. Quasi-identifiers
  re-identify people, so pseudonymised data is still personal data and still
  needs access control, retention and deletion (this lesson).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every recall figure, field count, retention count and k-anonymity
  statistic above is computed from the generated data in this file.

  ILLUSTRATIVE: all data is synthetic; the detector is deliberately simple; and
  k-anonymity is one crude measure of re-identification risk, not a guarantee.

  NOT SHOWN: any jurisdiction's legal definitions or lawful bases -- this course
  gives no legal advice (M10-L16). Differential privacy, secure enclaves and
  formal de-identification standards are out of scope.

Done.
```

### 7.3 Reading the result

**Section 1's two recall figures belong together**: 100% on anticipated formats, 2/10 on variants. Quoting the first
without the second is how "we scan for PII" becomes a false assurance.

**Section 2 is the cheapest control in this module.** Eight personal fields removed from every request by building the
payload from the template.

**Section 5's 81% is the number to remember** when someone says "we removed the names, so it's anonymous".

---

## 8. Common mistakes and troubleshooting

1. **Treating a PII scanner as assurance.** §5.1 — 2/10 on ordinary format variants.
2. **Sending whole records to a model.** §5.2 — 8 unnecessary personal fields.
3. **Deleting from the primary store only.** §5.4 — six other stores retain copies.
4. **Forgetting the vector index** because "it's only numbers". §5.4, §6.
5. **Building evaluation sets from live customer text.** §5.3 — it becomes undeletable in practice.
6. **Calling pseudonymised data anonymous.** §5.5 — 81% of rows were unique.
7. **No exception register for logs and backups.** §5.3 — silence is not a policy.

| Symptom | Likely cause | Fix |
|---|---|---|
| Deleted customer still appears in answers | No propagation to vector index or cache | Delete chunk + vector; subject-scoped cache keys |
| Provider logs contain more data than expected | Payload built from the record object | Build from the prompt template's fields |
| Retention dashboard looks fine, data is old | Job failing silently; counting deletions not ages | Monitor age distribution; alert on job failure |
| "Anonymised" export re-identified | Quasi-identifiers retained | Measure k; generalise or suppress |
| Erasure request cannot be answered | No inventory of stores per subject | Map stores and their deletion mechanisms (L03) |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Minimisation reduces every other risk in this lesson: what you never sent cannot leak, be logged, or need
  deleting.
- **Security.** Pseudonymised data still needs access control and tenant isolation (L07); re-identification is an attack,
  not a theoretical concern.
- **Reliability.** Deletion jobs and redaction need monitoring like any pipeline; both fail quietly.
- **Cost.** Shorter retention cuts storage, index size and re-embedding cost; removing eight fields from a prompt cuts
  tokens on every call (M5-L15).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why did the detector score 100% in-sample and 2/10 on variants?
2. Which eight fields in §7.2 were unnecessary, and what does each risk?
3. List the seven stores in §7.4 and say how deletion works in each.
4. Why is a vector derived from someone's words still their personal data?
5. What does k=1 mean for 162 of 200 rows?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add three more format variants and improve the detector; then write three new variants that defeat your
   improvements.
2. Change the prompt template to include `delivery_address` and re-run §7.2. What is the new exposure, and is it justified?
3. Implement a `build_payload(record, template)` function and use it to construct the request.
4. Add an eighth store (a partner's system) to §7.4 and describe the deletion path.
5. Raise k to at least 5 in §7.5 by generalising, and report what analytical value you lost.

### Exercise 3 — Challenge (~60 min)

1. Build a deletion-propagation test: insert a synthetic subject into every store, run erasure, and assert zero remaining
   references, with logs and backups handled as documented exceptions.
2. Design the retention schedule for a RAG assistant: raw transcripts, chunks, embeddings, caches, traces, evaluation
   examples — with a justification per class.
3. Measure re-identification risk with a second method (e.g. uniqueness under a linkage attack using an external
   attribute) and compare with k-anonymity.
4. Write the erasure runbook: intake, identification across stores, execution, verification, evidence, and the response to
   the individual.
5. Argue when a system should use synthetic evaluation data instead of real examples, and what it costs (M5-L18).

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l06).)*

**Q1.** In §7.1, how did the detector perform on plain names?

- A. It found none of the 17
- B. It found all 17
- C. It found 2 of 17
- D. It flagged names as postcodes

**Q2.** What did the format-variant test show?

- A. Recall improved outside the training formats
- B. False positives rose sharply
- C. Recall fell to 2 of 10
- D. Only card numbers were missed

**Q3.** What is the correct role for a PII detector?

- A. Certifying that a corpus is free of personal data
- B. Reducing exposure and flagging obvious leaks
- C. Replacing access control on personal data
- D. Proving compliance to an auditor

**Q4.** In §7.2, how many personal fields were used by neither the prompt nor the logic?

- A. 3 fields
- B. 5 fields
- C. 14 fields
- D. 8 fields

**Q5.** How should a request payload be built?

- A. From the full record object, then redacted
- B. From the fields the template and logic read
- C. From every field marked non-sensitive
- D. From the database view used by the UI

**Q6.** In §7.3, what proportion of conversations were past the 90-day policy?

- A. 81%
- B. 19%
- C. 50%
- D. 4%

**Q7.** Which two stores could not be cleared by the deletion job in §7.4?

- A. Vector index and answer cache
- B. Primary database and search index
- C. Evaluation dataset and vector index
- D. Application logs and nightly backups

**Q8.** Why is a vector index in scope for erasure?

- A. It stores the original text alongside vectors
- B. Vector stores are always regulated systems
- C. Embeddings derive from the person's words and support retrieval about them
- D. Indexes cannot be access-controlled

**Q9.** What does §7.5 show about removing names?

- A. 81% of rows remained uniquely identifiable
- B. The table became anonymous
- C. Only special-category rows stayed identifiable
- D. Pseudonyms prevented all linkage

**Q10.** What raised k in §7.5?

- A. Replacing pseudonyms with random ids
- B. Generalising geography and age, dropping a field
- C. Encrypting the quasi-identifiers
- D. Sorting rows by department

**Q11.** Which store's data cannot be deleted at all, only retrained away?

- A. The answer cache
- B. The search index
- C. The evaluation dataset
- D. Model weights

**Q12.** In §6, why did the assistant still recall the customer's complaint?

- A. The customer's row was never deleted
- B. The backup had been restored
- C. Vectors, cache and evaluation examples were never cleared
- D. The model had memorised the conversation

**Q13.** *(Written, rubric-graded.)* In under 150 words: design the erasure process for a RAG assistant, listing each
store, how deletion happens there, and how you would verify it.

---

## 12. Revision notes

- **Detection:** 100% recall on anticipated formats, **0/17 names**, **2/10 format variants**, 0 false positives. Use it to
  reduce exposure, never as assurance.
- **Minimisation:** 14 fields collected, 5 rendered, 3 read — **8 unnecessary personal fields**. Build payloads from the
  template's fields.
- **Retention:** 404/500 records overdue; monitor age distribution and job failures; keep an exception register.
- **Propagation:** primary, search, vector, cache, evaluation set — plus logs (redact at write, short retention) and
  backups (documented window, re-apply after restore). Weights cannot be deleted.
- **Pseudonymised ≠ anonymous:** 81% of rows unique on three quasi-identifiers; generalisation cut that to 3 rows.

---

## 13. Completion checklist

- [ ] I can state what my PII detection finds and misses, measured on variants.
- [ ] I build model payloads from the fields the task needs.
- [ ] My deletion reaches every derived store, with logs and backups documented.
- [ ] I can trace one subject across every store.
- [ ] I test re-identification before calling data anonymous.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M7-L16 (incremental updates and deletion propagation) and M6-L10 (index updates and deletion) — the mechanisms `[STABLE]`
- M9-L12 (logs, redaction and secrets) — why redaction belongs at write time `[STABLE]`
- M13-L01 (when fine-tuning is justified) — why training on personal data creates an undeletable copy `[STABLE]`
- L. Sweeney, *k-Anonymity: A Model for Protecting Privacy* (2002) — the origin of the measure used in §7.5 `[UNVERIFIED]`

---

## 15. Next lesson

→ [M10-L07 — Access Control and Tenant Isolation as Governance Controls](M10-L07-access-control-tenant-isolation.md) turns
to who may see what: the same data, governed by identity rather than by policy documents.
