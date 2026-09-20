# M10-L13 — Versioning Datasets, Models, Prompts and Configuration; Auditability

| | |
|---|---|
| **Lesson ID** | M10-L13 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M5-L12](../module-05-prompting-llm-apps/M5-L12-prompt-versioning.md), [M10-L04](M10-L04-risk-registers.md), [M10-L12](M10-L12-release-gates.md) |

---

## 1. Learning objectives

1. **Enumerate** every artefact that can change an answer, and stamp all of them on each run.
2. **Compute** a run fingerprint from content hashes rather than from labels people type.
3. **Explain** why floating model aliases make results unreproducible and releases untested.
4. **Design** an audit record from the questions it must answer, not from what is convenient to log.
5. **Set** a retention period from the arrival lag of real questions, balanced against minimisation.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Run fingerprint** | A hash over every artefact version that could affect the output of a request. |
| **Content hash** | A hash of the artefact's bytes — true regardless of what the version label says. |
| **Pinned version** | An immutable identifier (`model@2026-06-11`), as opposed to a floating alias (`@latest`). |
| **Silent drift** | The behaviour of a dependency changing without any change on your side. |
| **Audit record** | The per-request evidence that lets you reconstruct what happened and why. |
| **Reproducibility** | The ability to re-obtain a past result from recorded versions, within stated tolerance. |
| **Retention period** | How long records are kept before deletion — a governance decision, not a storage default. |
| **Arrival lag** | Days between a request and the complaint, audit or investigation that asks about it. |

---

## 3. Plain-language explanation

### 3.1 The answer depends on more things than you are recording

§7.1 fingerprints a complete configuration and then changes **one** thing at a time: the model alias, the temperature,
`k`, the embedding model, the chunk overlap, the system prompt, the guardrail policy, the app commit. **All eight change
the fingerprint** — they all change what the user sees.

A log that records only *model* and *prompt* — the common case — produces the **same** fingerprint for **6 of those 8**
changes. Re-embedding the corpus, re-chunking it, changing `k`, swapping the guardrail policy and deploying new code all
look identical in that log.

### 3.2 "The prompt is the same" is a claim about a hash

§7.2 shows four prompts that render near-identically in a terminal, a ticket or a diff view: one has a double space, one a
trailing space, one a zero-width character. **All four hash differently.** If your record stores the label "v3" rather
than the bytes, you cannot tell which of the four was sent.

### 3.3 A floating alias is a release you never tested

§7.3 simulates 26 weeks against `vendor-x-large@latest`. **6 distinct builds** actually served traffic, changing in weeks
**8, 12, 17, 21, 22 and 25**. The pinned service saw **1 build and 0 changes**. Every one of those six is a production
change that skipped your gates (L12), your evaluation and your change record.

### 3.4 Design the record from the questions

§7.4 asks nine questions an incident or an audit will ask. A minimal log answers **1 of 9**. A typical "model + output"
log answers **3 of 9**. An audit-ready record answers **9 of 9** — because it was designed from the list.

### 3.5 Keep it exactly long enough

§7.5: with the illustrative lag distribution (median **36** days, p90 **95** days), a 7-day retention can answer **26.5%**
of questions, 30 days **45.4%**, and 90 days **88.5%**. Minimisation says delete early; auditability says keep. The
resolution is a number chosen from data and written down, per data class.

---

## 4. Analogy

**A pharmacy dispensing record.** It is not enough to record "gave the patient their tablets". The record carries the drug,
the **batch number**, the strength, the quantity, the prescriber, the pharmacist, the date and the patient. When a batch is
recalled, that record answers "who received it" in minutes. The batch number is the point: "paracetamol" is a label,
"batch 7742A, expiry 2027-03" is an identity.

### Where the analogy breaks

- **A drug batch is physical and fixed; your stack has a dozen moving parts** — model, index, embeddings, chunker, prompt,
  guardrails, code — and any of them can move independently (§5.1).
- **Pharmacy retention is set by regulation; yours usually is not.** You choose it, which means you must justify it
  (§5.6).

---

## 5. Detailed technical explanation

### 5.1 What belongs in the stamp

`[REAL, measured]` §7.1 — eight single changes, eight different fingerprints.

| Artefact | Pin as | Why it changes answers |
|---|---|---|
| Model | Immutable version id, not an alias | Different weights, different behaviour (§5.3) |
| Decoding parameters | temperature, top_p, max_tokens, seed if available | Sampling changes the output (M4-L14) |
| System and task prompts | **Content hash** of the exact bytes | §7.2 |
| Retrieval index | Index name **and** build id | Different documents retrieved (M7-L16) |
| Embedding model | Version | Re-embedding changes neighbours entirely (M6-L02) |
| Chunking config | size, overlap, splitter version | Changes the text the model sees (M7-L06) |
| Retrieval params | k, filters, reranker version | Changes the evidence set (M7-L10) |
| Tool definitions | Schema hash + server version | Changes what the model can do (M8-L05, M9-L07) |
| Guardrail/policy config | Version | Changes what is blocked (M12-L06) |
| Application code | Commit sha | Assembly, truncation and post-processing live here |
| Evaluation set | Version + row count | A result is meaningless without it (L12) |

The rule: **if changing it can change the output, it goes in the fingerprint.**

### 5.2 Hash content, not labels

`[REAL, measured]` §7.2: four visually identical prompts, four distinct hashes.

```python
import hashlib, json

def fingerprint(cfg: dict) -> str:
    blob = json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]
```

Two properties matter: **sorted keys** (so key order cannot change the hash) and **the actual bytes** of every text
artefact. Store the hash on every request and the full artefact once, keyed by hash — a prompt store, not a prompt copied
into every log line.

A label is still useful for humans (`support-answer/v3`), but the label maps to the hash, never replaces it.

### 5.3 Floating aliases

`[REAL, simulated]` §7.3: 6 builds in 26 weeks under `@latest`; 1 under a pin.

What you lose with an alias:

- **Reproducibility**: the result you recorded in March cannot be re-obtained in September.
- **Gating**: L12's suite ran against a build that is no longer serving.
- **Attribution**: a quality complaint cannot be traced to a change, because there is no change record.
- **Rollback**: "revert to the previous model" is not a well-defined action.

Pin, and treat a version bump as a normal change: gate it, canary it (M13-L14), record it. Where a provider offers no
immutable id, record the observed build metadata from the response and monitor for changes (M13-L12) — and treat the gap
as a supplier finding (L11).

### 5.4 Designing the audit record

`[REAL, measured]` §7.4 — coverage 1/9, 3/9, 9/9 across three levels.

An audit-ready record per request:

```json
{
  "request_id": "req_7f31...", "ts": "2026-09-16T10:22:41Z",
  "identity": {"user": "u_881", "tenant": "t_14", "roles": ["agent"]},
  "release": {"code": "app@9f2c1ab", "cohort": "canary-3", "config": "cfg_5182d44aaae5"},
  "model": {"id": "vendor-x-large@2026-06-11", "temperature": 0.2, "max_tokens": 800},
  "prompt": {"system_sha": "eb4171e7e428", "template": "support-answer/v3", "input_sha": "9b1c..."},
  "retrieval": {"index": "kb-v7#build-2026-08-30", "embedding": "embed-3@2026-02", "k": 8,
                "doc_ids": ["d_991#r4", "d_120#r9"], "filters": {"tenant": "t_14"}},
  "tools": [{"name": "get_order", "args_sha": "31ac...", "status": "ok", "ms": 240}],
  "output": {"text_sha": "77de...", "tokens": 412, "blocked_by": null},
  "decision": {"gate": "pass", "escalated": false}
}
```

Note what is a **hash** rather than the text: prompts, user input and output. That keeps the log small, lets you prove
what was sent, and keeps personal data in one governed store with one retention rule (L06) rather than scattered through
logs. Store `doc_ids` **with their revision** — "document 991" is not reproducible if the document was edited.

### 5.5 Reproducibility has a tolerance

Exact reproduction is possible when everything is pinned and decoding is deterministic. It often is not: sampling without
a seed, provider-side nondeterminism, batching effects, and index rebuilds all break exactness. State what you promise:

| Level | Promise | Needs |
|---|---|---|
| **Exact** | Same bytes out | Full pin + temperature 0 + provider determinism |
| **Statistical** | Same metrics within an interval, over the recorded set | Full pin of everything but sampling |
| **Evidential** | We can show what was sent, retrieved, called and returned | The audit record alone |

Most teams need **evidential** for incidents and **statistical** for evaluation. Promising "exact" and failing is worse
than promising the level you can actually meet.

### 5.6 Retention: two pressures, one number

`[REAL, computed, ILLUSTRATIVE distribution]` §7.5: 26.5% / 45.4% / 88.5% / 99.95% answerable at 7 / 30 / 90 / 180 days.

Set it per class of record:

| Class | Typical driver | Note |
|---|---|---|
| Request metadata (hashes, versions, ids) | Audit and incident lag | Small; keep longest |
| Prompt and output text | Minimisation, complaint window | Personal data — shortest defensible period (L06) |
| Retrieved doc ids and revisions | Reproducing a past answer | Requires document revisions to be retained too |
| Evaluation runs and gate decisions | Release audit | Keep with the release record |

Write the period, the owner and the reason into the inventory row (L03); a retention period nobody can justify is
either a risk or a cost, and usually both.

### 5.7 Assumptions and limitations

- Hashing proves *identity*, not *integrity against tampering*: an attacker who can rewrite logs can rewrite hashes.
  Append-only storage and access control are the controls there (M11-L16).
- The lab's drift probability and complaint-lag distribution are invented; the method is what transfers.
- Legal retention obligations vary by jurisdiction and sector and are out of scope (L16).

---

## 6. Worked example — the answer nobody could explain

**The situation.** A customer complained that the assistant had told them a policy that did not exist. The screenshot was
four months old. The team was asked: what produced this?

**What they had.** Timestamp, user id, output text. Model name without a version. No prompt hash, no retrieval record.

**What they could establish.** That the request happened. Nothing else.

1. The model name mapped to a **floating alias**; the provider had served at least two builds in that window (§5.3).
2. The prompt template had been edited **three times** since; the repository had the current text and a diff history, but
   no link from a request to a template revision (§5.2).
3. The knowledge base had been **re-indexed** with a new embedding model in the interim, so re-running the question
   retrieved a different document set (§5.1).
4. The document that most likely caused it had been **edited** — the old revision existed in the CMS, but nothing recorded
   which revision had been retrieved (§5.4).
5. The team could not say whether the answer had been a hallucination or a correct summary of a since-corrected page.
   They apologised and could not explain — the worst available outcome (L09).

| # | Missing | Fix |
|---|---|---|
| 1 | Immutable model version | Pin; record the version on every request |
| 2 | Prompt content hash | Hash bytes; keep a prompt store keyed by hash |
| 3 | Index and embedding build ids | Record index build, embedding version, chunker version |
| 4 | Document revisions | Record `doc_id#revision`; retain revisions as long as the logs |
| 5 | Retention shorter than the complaint lag | Set retention from the lag distribution (§5.6) |

**The general rule.** **You cannot investigate what you did not record, and you will not know which field you needed until
the day you need it.**

---

## 7. Practical activity

**File:** [`labs/m10/l13_versioning_auditability.py`](../../labs/m10/l13_versioning_auditability.py)

**No API key, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m10/l13_versioning_auditability.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Seeded with `random.Random(1013)`; run twice, output
identical.

```text

============================================================================
1. THE RUN FINGERPRINT: WHAT ACTUALLY DECIDES THE ANSWER
============================================================================
  baseline run fingerprint: 5182d44aaae5

  single change                         new fingerprint   differs?
  model pinned -> floating alias        f799ed951c5a      yes
  temperature 0.2 -> 0.7                d20dc9880594      yes
  k 8 -> 12                             6fc9fbc2b464      yes
  re-embedded with embed-4              d3ed2f6c35bb      yes
  chunk overlap 120 -> 200              0148ab293a26      yes
  system prompt reworded                a32fe82f110e      yes
  guardrail policy v4 -> v5             7cba6e81f24e      yes
  app code deploy                       687bcda87a94      yes

  a log that records only model + prompt has fingerprint 9e51b6499d1b for ALL of
  6 of the changes above: they are invisible to it.
  Everything that can change the answer belongs in the stamp, including the
  index, the embedding model, the chunker, the guardrail config and the code.

============================================================================
2. TWO PROMPTS THAT LOOK THE SAME
============================================================================
  as written           len=56    sha=eb4171e7e428   rendered: You answer only from the provided context. Cite sources.
  double space         len=57    sha=06d1b176b17d   rendered: You answer only from the provided context.  Cite sources.
  trailing space       len=57    sha=3fc6ed27197f   rendered: You answer only from the provided context. Cite sources. 
  zero-width space     len=57    sha=bf62ea3979e5   rendered: You answer only from the provided context. Cite sources​.

  distinct prompts above: 4 -- all four render near-identically in a terminal,
  a ticket, or a pull-request description. 'The prompt is the same' is a claim
  about a hash, not about how the text looks (M5-L12).

============================================================================
3. SILENT DRIFT UNDER A FLOATING ALIAS
============================================================================
  a service calling 'vendor-x-large@latest' for 26 weeks
  distinct underlying builds actually served : 6
  weeks on which the build changed           : [8, 12, 17, 21, 22, 25]
  the pinned service calling '@2026-06-11'   : 1 build, 0 changes

  Every change above is a release you did not test, did not gate (L12) and
  cannot reproduce. Pin the version; upgrade deliberately, through the gates.

============================================================================
4. WHAT CAN THE LOG ANSWER?
============================================================================
  question                                                   minimal       typical   audit-ready
  Which model version answered this request?                      no           yes           yes
  What exact prompt text was sent?                                no            no           yes
  Which documents were retrieved, and from which index?            no            no           yes
  Who was the user and what were they permitted to see?            no           yes           yes
  Which tool calls ran, with what arguments?                      no            no           yes
  What did the user actually see?                                yes           yes           yes
  Which config and guardrail policy were in force?                no            no           yes
  Was this request part of the canary or the baseline?            no            no           yes
  Can we reproduce the answer exactly today?                      no            no           yes

  minimal (timestamp + text)     answers 1/9 questions
  typical (model + output)       answers 3/9 questions
  audit-ready                    answers 9/9 questions

  The cost of the audit-ready level is storage and a retention policy (L06).
  The cost of the others is discovering, during an incident, that the question
  you most need to answer was never recorded (M10-L14).

============================================================================
5. RETENTION VS THE WINDOW IN WHICH QUESTIONS ARRIVE
============================================================================
  retention    7 days ->  26.50% of questions still answerable (2940 of 4000 arrive after the logs are gone)
  retention   30 days ->  45.38% of questions still answerable (2185 of 4000 arrive after the logs are gone)
  retention   90 days ->  88.52% of questions still answerable ( 459 of 4000 arrive after the logs are gone)
  retention  180 days ->  99.95% of questions still answerable (   2 of 4000 arrive after the logs are gone)
  retention  365 days -> 100.00% of questions still answerable (   0 of 4000 arrive after the logs are gone)

  median lag 36 days, 90th percentile 95 days [ILLUSTRATIVE distribution]
  Retention is a governance decision with two opposing pressures: minimisation
  (L06) says delete early, auditability says keep long enough to answer. Set it
  from the actual lag distribution, per data class, and write it down.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every hash, fingerprint comparison, drift count, coverage count and
  retention percentage above is computed by this script.

  ILLUSTRATIVE: the configuration values, the drift probability and the
  complaint-lag distribution are invented.

  NOT SHOWN: the storage system itself, tamper-evidence and log integrity,
  and legal retention requirements (M10-L16, M11-L16).

Done.
```

### 7.3 Reading the result

**Section 1's last paragraph is the finding**: six of eight answer-changing edits are invisible to a model-plus-prompt log.

**Section 2 is why labels are not versions.** Four prompts, one appearance, four hashes.

**Section 4 is a design method**, not a table: write your nine questions first, then the record that answers them.

**Section 5 is the trade-off** between L06's minimisation and this lesson's auditability, resolved with a measurement.

---

## 8. Common mistakes and troubleshooting

1. **Pinning the model and nothing else.** §5.1 — index, embeddings, chunker, guardrails and code all move.
2. **Storing a prompt label instead of a content hash.** §5.2.
3. **Using `@latest` in production.** §5.3 — six untested changes in six months.
4. **Recording document ids without revisions.** §5.4 — the document may have been edited.
5. **Copying full prompts and outputs into application logs.** Personal data spread across systems with no retention rule
   (L06); store hashes and keep the text in one governed store.
6. **Designing the log from what the framework emits.** §5.4 — design it from the questions.
7. **Promising exact reproducibility.** §5.5 — state the level you can meet.
8. **Retention set by a storage default.** §5.6 — 7 days answers a quarter of the questions.

| Symptom | Likely cause | Fix |
|---|---|---|
| "It worked last month" and nobody can prove it | No run fingerprint | Stamp every request with the full config hash |
| Quality moved with no deploy | Floating alias or index rebuild | Pin; record index build ids; monitor for drift |
| Two teams disagree about "the prompt" | Label-based versioning | Content hashes; a prompt store keyed by hash |
| Cannot re-run an old answer | Document revisions not retained | Store `doc_id#revision`; align document and log retention |
| Audit request cannot be answered | Retention shorter than arrival lag | Measure the lag; set retention per record class |

---

## 9. Security, privacy, reliability, cost

- **Security.** Audit logs are an attack target and an exfiltration source. Restrict access, store append-only, and treat
  the log store as in scope for the threat model (L10, M11-L16).
- **Privacy.** Hash prompts and outputs in logs; hold the text once, with a retention rule and a deletion path that
  reaches the logs too (L06).
- **Reliability.** Pinning is a reliability control: it removes a whole class of "nothing changed" incidents (L14).
- **Cost.** Per-request audit records are cheap as metadata and expensive as full text. The hash-plus-store design is
  usually an order of magnitude smaller.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List every artefact in your system that could change an answer.
2. In §7.1, how many changes were invisible to a model-plus-prompt log?
3. Why did the four prompts in §7.2 hash differently?
4. How many builds served traffic under the floating alias in §7.3?
5. Which two of §7.4's nine questions does a "typical" log answer beyond the output?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a change to `CHANGES` that does *not* affect the answer and decide whether it belongs in the stamp.
2. Write the `fingerprint()` function into a small script that stamps a request in your own code.
3. Add two more audit questions to §7.4 and see which level still answers them.
4. Change the lag distribution's mean to 10 days and re-derive a retention period.
5. Draft the retention table for your system, per record class, with an owner for each row.

### Exercise 3 — Challenge (~60 min)

1. Implement a prompt store: content-addressed, with human labels mapping to hashes, and migrate one prompt to it.
2. Add run fingerprints to your evaluation harness so every result row carries the config that produced it.
3. Build the "explain this request" tool: given a request id, print the full reconstruction from §5.4.
4. Test it by investigating a request from at least a month ago, and record every field you wished you had.
5. Write the reproducibility promise your team can actually meet, at each of §5.5's three levels.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l13).)*

**Q1.** What belongs in a run fingerprint?

- A. The model version and the prompt label
- B. The model version and the application commit
- C. Whatever the logging framework emits by default
- D. Every artefact whose change could change the output

**Q2.** In §7.1, how many of the eight single changes were invisible to a model-plus-prompt log?

- A. Two of eight
- B. Six of eight
- C. Four of eight
- D. None — all eight were visible

**Q3.** Why hash prompt bytes rather than store a label?

- A. Hashes compress the prompt for storage
- B. Labels cannot be indexed efficiently
- C. Visually identical texts can differ, and labels hide that
- D. Hashes prevent the prompt from being edited

**Q4.** What did §7.3 show about a floating model alias?

- A. It produced identical behaviour to a pinned version
- B. Six distinct builds served traffic over 26 weeks
- C. It reduced latency at the cost of reproducibility
- D. Drift was detectable from the alias name alone

**Q5.** Why is silent drift a governance problem, not just a technical one?

- A. The changes bypassed gates, evaluation and the change record
- B. Provider aliases are prohibited by most AI frameworks
- C. It increases per-token cost unpredictably
- D. It invalidates the inventory's ownership field

**Q6.** How should an audit record be designed?

- A. From the fields the model provider returns
- B. From a standard template applied across all systems
- C. From what fits within the log budget
- D. From the questions an incident or audit will ask

**Q7.** How many of §7.4's nine questions did the "typical" log answer?

- A. One of nine
- B. Three of nine
- C. Five of nine
- D. Nine of nine

**Q8.** Why store `doc_id#revision` rather than `doc_id`?

- A. Revisions make retrieval faster
- B. Document ids are not unique across tenants
- C. The document may have been edited since the answer
- D. Revisions are required for citation formatting

**Q9.** What does "evidential" reproducibility promise?

- A. That you can show what was sent, retrieved, called and returned
- B. That the same bytes are produced on re-run
- C. That metrics match within a confidence interval
- D. That the provider guarantees model stability

**Q10.** In §7.5, what fraction of questions could a 30-day retention answer?

- A. 26.5%
- B. 88.5%
- C. 45.4%
- D. 99.95%

**Q11.** What are the two opposing pressures on retention?

- A. Storage cost and query latency
- B. Provider terms and index size
- C. Canary size and rollback speed
- D. Data minimisation and auditability

**Q12.** Why keep prompt and output *text* in one governed store rather than in application logs?

- A. It gives the personal data one retention rule and one deletion path
- B. Logs cannot store text reliably at volume
- C. Hashes are unreadable to investigators
- D. Log aggregation systems do not support long strings

**Q13.** *(Written, rubric-graded.)* In under 150 words: a user complains about an answer from three months ago. List
what you would need recorded to explain it, and what you would change today if you could not.

---

## 12. Revision notes

- **Stamp everything that can change the answer**: all **8** single changes altered the fingerprint; **6 of 8** were
  invisible to a model-plus-prompt log.
- **Hash bytes, not labels**: **4** visually identical prompts, **4** distinct hashes.
- **Pin versions**: `@latest` served **6** builds in 26 weeks, changing in weeks 8, 12, 17, 21, 22, 25; a pin served 1.
- **Design the record from the questions**: coverage **1/9**, **3/9**, **9/9** across minimal, typical and audit-ready.
- **Reproducibility has levels**: exact, statistical, evidential — promise the one you can meet.
- **Retention from the lag**: **26.5% / 45.4% / 88.5%** answerable at 7 / 30 / 90 days; set it per record class.

---

## 13. Completion checklist

- [ ] Every request carries a fingerprint over model, prompts, retrieval, config and code.
- [ ] Prompts and outputs are content-hashed; the text lives in one governed store.
- [ ] No production path uses a floating model alias.
- [ ] My audit record answers the questions I wrote down before designing it.
- [ ] Retention is set per record class from measured arrival lag, with an owner.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M5-L12 (prompt versioning and A/B discipline) and M10-L12 (gates that reference set versions) `[STABLE]`
- M7-L08 (metadata, provenance, versioning in ingestion) and M7-L16 (incremental updates, deletion propagation) `[STABLE]`
- M10-L06 (retention and deletion) and M10-L03 (inventory rows that carry the retention owner) `[STABLE]`
- M11-L16 (CloudWatch and CloudTrail) — where audit records live on AWS `[STABLE]`
- M13-L12 (offline vs online monitoring — detecting drift you did not cause) `[STABLE]`

---

## 15. Next lesson

→ [M10-L14 — Incident Response, Rollback and Change Management](M10-L14-incident-response-rollback.md) uses these records
under time pressure: detecting that something is wrong, deciding to roll back, and managing the change that caused it.
