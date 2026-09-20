# M10-L05 — Data Provenance, Licensing and Permitted Use

| | |
|---|---|
| **Lesson ID** | M10-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L08](../module-07-rag/M7-L08-metadata-provenance-versioning.md), [M10-L03](M10-L03-ai-inventories.md) |

> **Scope note.** This lesson is about the **engineering** of provenance and permitted use: what to record, how it
> propagates, and how to enforce it. It is not legal advice, and licence terms differ by jurisdiction and by contract.
> Get the actual permissions from the people who can grant them.

---

## 1. Learning objectives

1. **Record** provenance and permitted use per source, in the fields a system can act on.
2. **Distinguish** use classes — internal retrieval, customer-facing answers, verbatim quotation, training, sharing — and
   check a source against each.
3. **Propagate** licence attributes from source to chunk to retrieval to answer, and **measure** what leaks without them.
4. **Carry** attribution requirements into generated output.
5. **Trace** derived datasets to their roots, so "may we train on this?" stays answerable.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Provenance** | Where a piece of data came from, through every transformation, recorded per record. |
| **Permitted use** | What you may do with it — which is several questions, not one. |
| **Use class** | A specific use: internal retrieval, customer-facing answer, verbatim quotation, training, redistribution. |
| **Attribution** | A credit or notice the licence requires to travel with the material. |
| **Share-alike** | A licence condition requiring derivative works to carry the same licence. |
| **Taint** | The way unknown or restricted provenance propagates into everything derived from it. |
| **Licence filter** | A retrieval-time filter that excludes chunks not permitted for this audience or use. |

---

## 3. Plain-language explanation

### 3.1 "Can we use it?" is not one question

§7.1 takes a 12-source corpus of the kind any company assembles — its own docs, a supplier manual, a paid standard,
open-source documentation, news articles, scraped forum posts, support transcripts, an ebook chapter, HR policies. Then
it asks five different questions. **11 of 12** may be used for internal retrieval. Only **5** may be used in a
customer-facing product. Only **4** may be quoted verbatim, only **4** may be used to train a model, and **4** require
attribution whenever they are used.

The corpus is the same in every row. The permission is not.

### 3.2 A licence in a spreadsheet cannot stop anything

§7.2 runs four realistic queries against an index built from all 12 sources. Without a licence filter, **5 chunks reach an
audience they are not licensed for** — a supplier's manual and a news article quoted to a customer, a paid standard's text
shown outside its three named readers. With the licence carried on the chunk and filtered at retrieval, **0** — and 7
chunks remain to answer from.

### 3.3 Attribution has to survive the answer template

Three of the permitted answers in §7.3 came from sources requiring credit — an Apache-2.0 notice, a public-sector
information statement, a CC BY-SA author credit and share-alike. The answer template included none of them: **3 required,
3 omitted**. Attribution is a condition of the licence, not a courtesy.

### 3.4 Derived data inherits what you did not record

§7.5 builds five derived datasets from the corpus, two of them from other derived datasets. `finetune-mix-v1` resolves
back to **seven original sources**, including the scraped forum posts with **unknown licence** — two levels down. If
provenance is not carried per record, that question becomes unanswerable, and the honest answer to "may we train on this
mix?" is *no, because we cannot tell*.

---

## 4. Analogy

**A kitchen's ingredient labels.** A restaurant can use the same tomatoes for staff lunch, for a dish on the menu, and
for a jarred sauce it sells — but the supplier's terms, the allergen labelling and the "not for resale" stamp differ
across those uses. If the label is on a clipboard in the office rather than on the crate, the line cook cannot honour it.
And once three ingredients are blended into a base sauce with no record, nobody can answer "does this contain the
not-for-resale batch?"

### Where the analogy breaks

- **Ingredients are consumed; data is copied.** A restriction that is violated once in a customer answer has been
  published, and cannot be recalled the way a plate can.
- **Kitchens have one regulator and one set of labels.** Data terms come from contracts, open-source licences, sector
  rules and privacy law at once, and they can conflict — which is why §5.1 records the *terms*, not a single "licence: OK".

---

## 5. Detailed technical explanation

### 5.1 What to record per source

| Field | Why |
|---|---|
| `origin` | Where it came from, specifically — a URL, a contract reference, a system export |
| `acquired_on`, `acquired_by` | When and by whom; terms change over time |
| `licence` / `terms_ref` | The actual licence name or contract clause, not a summary |
| `internal_use`, `commercial_use`, `redistribute_verbatim`, `train_on` | The use classes your systems act on |
| `attribution` | The exact notice required, if any |
| `expiry` / `review_date` | Licences and contracts end |
| `data_classes` | Personal data, confidential, public (feeds L06) |
| `derived_from` | Parent datasets, for provenance chains (§5.5) |

Two engineering points. **Store booleans your code can evaluate**, alongside the human-readable terms — a retriever cannot
parse "internal use only, except with written consent". And **default to deny**: an unknown licence is not "probably
fine"; §7.1's scraped forum posts are the only source usable for nothing at all, and that is the correct treatment.

### 5.2 Use classes

`[REAL, measured]` §7.4, 12 sources:

| Use | Permitted |
|---|---|
| Retrieval for internal staff | 11/12 |
| Retrieval for customer-facing answers | 5/12 |
| Verbatim quotation to customers | 4/12 |
| Fine-tuning a model we deploy | 4/12 |
| Sharing the index with a partner | 4/12 |

The gap between rows one and two is where most incidents live: a corpus assembled for an internal assistant is
re-pointed at a customer-facing product, and nobody re-asks the question.

**Retrieval versus training** deserves its own note. Retrieval uses the text at answer time and can cite it; training
absorbs it into weights, cannot be cited, and cannot be removed without retraining (M13-L01). Many contracts and
licences permit the first and not the second, so the boolean must be separate.

### 5.3 Propagation into the index

`[REAL, measured]` §7.2: without a licence filter, 5 chunks reached the wrong audience; with one, 0, and 7 chunks
remained usable.

Implementation, following M7-L08 and M6-L09:

1. Attach `source_id`, `licence`, `use_class` booleans and `attribution` to **every chunk** at ingestion.
2. Filter at retrieval by audience and use class — a metadata filter, evaluated in the index, not after (M6-L09's
   filtered-ANN pitfalls apply).
3. Carry the attributes through re-ranking and context assembly so the answer layer still knows them (M7-L11).
4. Re-check on **re-ingestion**: a source whose contract has lapsed must leave the index (L06's deletion propagation).

### 5.4 Attribution in generated output

`[REAL, measured]` §7.3: 3 required, 3 omitted.

Attribution must be part of the **answer contract**, next to citations (M7-L12): when a chunk with an attribution
requirement contributes to an answer, the notice is rendered with it. Share-alike terms go further — they can constrain
what you may do with the *output* — which is a reason many teams exclude share-alike sources from customer-facing
corpora entirely and record that decision.

### 5.5 Provenance chains

`[REAL, measured]` §7.5: `finetune-mix-v1` resolves to seven roots including one unknown-licence source, two levels down;
`eval-set-v2` inherits the same taint.

- Record `derived_from` on every dataset and make resolution automatic, as the lab does.
- **Taint rules:** unknown licence taints; "no training" taints any mix used for training; share-alike propagates its
  condition.
- Keep a **manifest hash** per dataset version so a later question maps to an exact set of records (L13, M13-L03).
- Quarantine, do not delete, sources whose status is unresolved: deleting loses the evidence of what happened.

### 5.6 Assumptions and limitations

- Five booleans is a simplification of real terms; production systems usually need per-clause notes and human review for
  edge cases.
- Licence interpretation varies by jurisdiction, and some questions about training on third-party content are actively
  disputed. Record facts; get decisions from people authorised to make them.
- Personal-data rules are **separate** and apply even to data you own outright (L06).

---

## 6. Worked example — the internal assistant that became a product

**The situation.** A software company built an internal support assistant over a corpus of its own docs, a partner's API
reference (under NDA), several open-source manuals, and a paid industry standard licensed to three named engineers. It
worked well. Eight months later, the company launched a customer-facing version — same index, new front end.

**What went wrong.** Within a fortnight, three separate problems surfaced:

1. A customer answer quoted two paragraphs of the **paid standard** verbatim. The standards body's licence covered three
   named readers.
2. Another answer reproduced part of the **partner's NDA'd API reference**, which the partner found via a search of their
   own text.
3. An open-source manual under **CC BY-SA** was summarised without attribution, and the share-alike condition raised a
   question about the output.

**Reading it through the artefact.**

1. **The corpus was assembled for one use class.** Every source had been checked for "can we index this internally?" —
   §7.4's first column, 11/12 — and none for "can we show this to customers?", where the answer was 5/12.
2. **Licences lived in a spreadsheet**, not on the chunks, so the retriever could not honour them (§5.3).
3. **Attribution was not in the answer contract**, so even permitted sources were used incorrectly (§5.4).
4. Nobody re-ran the question at launch, because **no change event triggered a re-review** (L02).

| # | Fix | Where |
|---|---|---|
| 1 | Licence and use-class booleans on every chunk; filter by audience at retrieval | §5.3 |
| 2 | Attribution rendered with citations; share-alike sources excluded from the customer corpus by policy | §5.4 |
| 3 | "New audience" added to the change events forcing re-review of intended use and corpus | L02 |
| 4 | Quarantine and re-ingestion pipeline for sources whose terms lapse | §5.5, L06 |

**The general rule.** **Permission is per use, per audience and per source — and it has to travel with the data, because
that is where the decision is made.**

---

## 7. Practical activity

**File:** [`labs/m10/l05_data_provenance_licensing.py`](../../labs/m10/l05_data_provenance_licensing.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l05_data_provenance_licensing.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. PERMITTED USE ACROSS THE CORPUS
============================================================================
  usable in a commercial product                5/12  S01, S04, S05, S08, S10
  internal use only                             6/12  S02, S03, S06, S09, S11, S12
  not usable at all (unknown or prohibited)     1/12  S07
  may be quoted verbatim to a customer          4/12  S01, S04, S05, S10
  may be used to train or fine-tune a model     4/12  S01, S04, S05, S10
  requires attribution when used                4/12  S03, S04, S05, S10

  'We have the file' and 'we may use the file for this' are different questions,
  and the second one has several answers depending on WHICH use.

============================================================================
2. PROPAGATION: SOURCE -> CHUNK -> RETRIEVAL -> ANSWER
============================================================================
  customer asks how to configure the widget            audience=customer
    retrieved 4 chunk(s); not permitted for this audience: S02-c3, S06-c1
  customer asks what the standard requires             audience=customer
    retrieved 3 chunk(s); not permitted for this audience: S03-c2
  agent asks for an internal HR answer                 audience=internal
    retrieved 2 chunk(s); not permitted for this audience: none
  customer asks for a summary of recent coverage       audience=customer
    retrieved 3 chunk(s); not permitted for this audience: S06-c2, S07-c1

  without a licence filter: 5 chunk(s) reached an audience they were not licensed for
  with a licence filter at retrieval: 0 (and 7 chunk(s) still available to answer from)
  The licence is an attribute of the CHUNK, not a note in a spreadsheet about
  the source. If it is not in the index, the retriever cannot honour it.

============================================================================
3. ATTRIBUTION THAT THE ANSWER TEMPLATE DROPS
============================================================================
  customer asks how to configure the widget            attribution MISSING: S04-c2 -> Apache-2.0 notice
  customer asks what the standard requires             attribution MISSING: S10-c1 -> contains public sector information
  customer asks for a summary of recent coverage       attribution MISSING: S05-c3 -> author + share-alike

  3 attribution(s) required and 3 omitted.
  Attribution is a condition of the licence, not a courtesy: CC BY-SA and
  Apache-2.0 both require notices to travel with the material.

============================================================================
4. THE SAME SOURCE, DIFFERENT USE CLASSES
============================================================================
  source  origin                                internal    customer    verbatim   fine-tune   share idx
  S01     our own product docs                       yes         yes         yes         yes         yes
  S02     supplier manual (contract)                 yes          NO          NO          NO          NO
  S03     public standard (paid)                     yes          NO          NO          NO          NO
  S04     open-source project README                 yes         yes         yes         yes         yes
  S05     open-source docs                           yes         yes         yes         yes         yes
  S06     news article                               yes          NO          NO          NO          NO
  S07     scraped forum posts                         NO          NO          NO          NO          NO
  S08     customer support transcripts               yes         yes          NO          NO          NO
  S09     partner API reference                      yes          NO          NO          NO          NO
  S10     government dataset                         yes         yes         yes         yes         yes
  S11     ebook chapter                              yes          NO          NO          NO          NO
  S12     internal HR policies                       yes          NO          NO          NO          NO

  retrieval for internal staff    : 11/12 sources permitted
  retrieval for customers         :  5/12 sources permitted
  verbatim quotation to customers :  4/12 sources permitted
  fine-tuning a model we deploy   :  4/12 sources permitted
  sharing the index with a partner:  4/12 sources permitted

  A corpus assembled for one use is not automatically available for the next.
  Fine-tuning is the sharpest example: 4 of 12 sources permit it (M13-L02).

============================================================================
5. DERIVED DATA: UNKNOWN PROVENANCE IS INHERITED
============================================================================
  clean-docs-v3      roots: S01, S04, S10
                     unknown licence: none;  not permitted for training: none
  support-qa-pairs   roots: S02, S08
                     unknown licence: none;  not permitted for training: S02, S08
  community-answers  roots: S05, S07
                     unknown licence: S07;  not permitted for training: S07
  eval-set-v2        roots: S02, S05, S07, S08
                     unknown licence: S07;  not permitted for training: S02, S07, S08
  finetune-mix-v1    roots: S01, S02, S04, S05, S07, S08, S10
                     unknown licence: S07;  not permitted for training: S02, S07, S08

  'finetune-mix-v1' inherits one unknown-licence source through two levels of
  derivation. Provenance has to be recorded per record and carried forward, or
  the answer to 'may we train on this?' becomes unknowable (M10-L13).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count, filter result and provenance resolution above is computed
  from the encoded corpus and derivation graph.

  ILLUSTRATIVE: the licences are simplified to five booleans. Real licence terms
  are text, they differ by jurisdiction, and some questions have no settled
  answer yet -- this course gives no legal advice (M10-L16).

  NOT SHOWN: personal-data rules, which are a separate question from licensing
  and apply even to data you own (M10-L06).

Done.
```

### 7.3 Reading the result

**Section 1's first two rows are the ones to internalise**: 11/12 internally, 5/12 for customers, from the same corpus.

**Section 2 shows where enforcement has to live.** The filter works because the licence is on the chunk.

**Section 5's `finetune-mix-v1` row** is what an unanswerable question looks like: seven roots, one unknown, two levels
down.

---

## 8. Common mistakes and troubleshooting

1. **Treating "we have it" as "we may use it".** §5.2.
2. **One "licence: OK" flag for all uses.** §5.2 — the answer differs per use class.
3. **Licence metadata outside the index.** §5.3 — the retriever cannot enforce what it cannot see.
4. **Dropping attribution in the answer template.** §5.4.
5. **No `derived_from`, so provenance stops at the first transformation.** §5.5.
6. **Treating "unknown licence" as permissive.** §5.1 — default deny.
7. **Assuming a licence permitting retrieval also permits training.** §5.2, M13-L01.

| Symptom | Likely cause | Fix |
|---|---|---|
| A customer answer quotes restricted material | No licence attributes on chunks, or no audience filter | Attach and filter at retrieval |
| Required notices never appear in answers | Attribution not part of the answer contract | Render with citations |
| "May we train on this dataset?" cannot be answered | No provenance chain | Record `derived_from`; resolve to roots |
| A lapsed contract's content is still answerable | No re-ingestion or expiry handling | Expiry dates + deletion propagation (L06) |
| Legal asks which sources are in the index | Manifest not versioned | Per-version manifest hash (L13) |

---

## 9. Security, privacy, reliability, cost

- **Security.** NDA'd and confidential material in a shared index is an access-control problem as much as a licensing one
  (L07, M7-L15).
- **Privacy.** Licensing and personal data are independent: owning the copyright in support transcripts says nothing
  about your right to process the personal data in them (L06).
- **Reliability.** Licence filters change what is retrievable; measure answer quality per audience, or a compliant system
  will quietly become a useless one (M7-L19).
- **Cost.** Re-licensing or removing a source after launch costs far more than asking the five questions in §7.4 during
  ingestion.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List the five use classes in §7.4 and give a source that is permitted for one but not the next.
2. Why must licence attributes live on the chunk rather than in a register?
3. What are the three attributions §7.3 required, and where would you render each?
4. Why is "unknown licence" treated as deny?
5. What does `finetune-mix-v1` inherit, and from where?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a source under a licence permitting customer answers but forbidding verbatim quotation, and add a
   query that retrieves it. What must the answer layer do?
2. Add an `expiry` field; expire one source and re-run the filters.
3. Implement the attribution rendering so permitted answers carry their notices, and show the output.
4. Add a `share_alike` flag and a policy that excludes such sources from the customer corpus; report what is lost.
5. Extend the derivation graph with a dataset built from `finetune-mix-v1` and confirm taint resolution.

### Exercise 3 — Challenge (~60 min)

1. Design the ingestion checklist that must be completed before any source enters an index, with the fields from §5.1 and
   who signs each off.
2. Implement retrieval-time licence filtering in a real vector store (M6-L08/L09) and measure recall before and after.
3. Write the quarantine workflow for a source whose terms lapse mid-quarter: what happens to the index, the caches, the
   evaluation sets and the logs.
4. Produce a per-version dataset manifest with hashes (M10-L13) and show how you would answer "which records trained this
   model?"
5. Draft the one-page summary you would give a non-technical stakeholder explaining why the customer-facing corpus is
   smaller than the internal one.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l05).)*

**Q1.** In §7.1, how many of the 12 sources may be used in a customer-facing product?

- A. 11 of 12 sources
- B. 5 of 12 sources
- C. 12 of 12 sources
- D. 1 of 12 sources

**Q2.** Why record use-class booleans rather than one "licensed" flag?

- A. Booleans compress better in an index
- B. Licences change more often than sources
- C. Attribution text cannot be stored otherwise
- D. Permission differs per use, audience and source

**Q3.** In §7.2, what happened without a licence filter at retrieval?

- A. Retrieval returned no results for customers
- B. Attribution notices were duplicated
- C. Five chunks reached an audience not licensed for them
- D. The index rejected the restricted chunks

**Q4.** Where must licence attributes live to be enforceable?

- A. On every chunk, filterable at retrieval
- B. In the source register, checked quarterly
- C. In the model's system prompt
- D. In the contract repository only

**Q5.** What did §7.3 measure about attribution?

- A. Notices were rendered for every source
- B. Only share-alike sources needed notices
- C. Attribution was required for 3 of 12 sources overall
- D. Three were required in answers and three were omitted

**Q6.** Why is "permitted for retrieval" not "permitted for training"?

- A. Training data must be public domain
- B. Training absorbs text into weights, uncitable and hard to remove
- C. Retrieval copies data while training does not
- D. Licences never mention training

**Q7.** How should an unknown licence be treated?

- A. As deny, until resolved
- B. As permissive for internal use
- C. As permissive with attribution added
- D. As equivalent to the corpus default

**Q8.** What does `finetune-mix-v1` inherit in §7.5?

- A. Only its direct parents' licences
- B. Attribution requirements but not restrictions
- C. An unknown-licence root two levels down
- D. Nothing; derivation resets provenance

**Q9.** Which field makes provenance chains resolvable?

- A. `acquired_on`
- B. `derived_from`
- C. `data_classes`
- D. `attribution`

**Q10.** In §6, what was the root cause of quoting the paid standard to a customer?

- A. The standards body changed its licence terms
- B. The retriever ignored its metadata filter
- C. The chunk was mislabelled at ingestion
- D. The corpus was assessed only for internal use

**Q11.** Which change should have triggered a re-review in §6?

- A. A new embedding model
- B. An index rebuild
- C. A new audience for the same corpus
- D. A change of cloud region

**Q12.** How do licensing and personal-data rules relate?

- A. They are independent questions, both of which apply
- B. Owning the copyright settles the privacy question
- C. Personal data is exempt where a licence permits use
- D. Licensing applies only to third-party data

**Q13.** *(Written, rubric-graded.)* In under 150 words: you are asked to reuse an internal support corpus for a
customer-facing assistant. List the checks you would run before agreeing, and what you would record.

---

## 12. Revision notes

- **Same corpus, different answers:** 11/12 internal retrieval, **5/12** customer-facing, 4/12 verbatim, **4/12 training**,
  4/12 requiring attribution.
- **Licence attributes belong on the chunk**, filtered at retrieval: 5 leaks → 0, with 7 chunks still usable.
- **Attribution is a licence condition**: 3 required, 3 omitted by a template that did not render them.
- **Unknown licence = deny.** Quarantine rather than delete.
- **Provenance chains:** `derived_from` per dataset; taint propagates — one unknown root made a fine-tuning mix
  unanswerable.
- **Re-ask permission on a new audience or a new use class**, not just on a new source.

---

## 13. Completion checklist

- [ ] I record origin, terms, use-class booleans and attribution per source.
- [ ] I attach licence attributes to chunks and filter at retrieval by audience.
- [ ] I render required attributions with answers.
- [ ] I record `derived_from` and can resolve any dataset to its roots.
- [ ] I treat unknown provenance as deny and re-review on new audiences or uses.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M7-L08 (metadata, provenance and versioning in RAG) and M6-L09 (metadata filtering) — the mechanisms this lesson governs `[STABLE]`
- M13-L01/L02 (fine-tuning decisions and dataset preparation) — why the training boolean is separate `[STABLE]`
- Apache-2.0, CC BY-SA 4.0 and the UK Open Government Licence — three licences whose attribution conditions differ `[UNVERIFIED — read the current text of any licence you rely on]`
- M10-L06 — personal-data rules, which apply independently of licensing `[STABLE]`

---

## 15. Next lesson

→ [M10-L06 — Personal and Sensitive Data: Minimization, Retention, Deletion](M10-L06-personal-sensitive-data.md) takes the
second question about the same material: not "may we use it?" but "whose data is it, how little can we keep, and can we
actually delete it?"
