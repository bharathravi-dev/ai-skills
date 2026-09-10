# M7-L12 — Citations and Evidence Verification

| | |
|---|---|
| **Lesson ID** | M7-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M7-L11](M7-L11-context-assembly-token-budgets.md) |

---

## 1. Learning objectives

1. **Explain** what a citation actually claims, per M7-L08's provenance framing.
2. **Implement** a citation-existence check, verifying a cited source was genuinely retrieved.
3. **Implement** a groundedness check, verifying a specific claim is actually supported by its cited
   source's text — and explain why this is a distinct, necessary check beyond citation existence.
4. **Distinguish** a fully grounded, a fully ungrounded, and a partially grounded claim, and explain why a
   pass/fail check cannot accurately describe the third case.
5. **Identify** what a narrow, hand-built groundedness check does and does not generalize to in a real
   production system.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Citation existence check** | Verifying that a cited source ID actually corresponds to a chunk that was genuinely retrieved, independent of whether the claim itself is accurate. |
| **Groundedness** | Whether a specific claim is actually supported by the text of the source it cites. |
| **Grounded claim** | A claim whose asserted content is verifiably present in its cited source. |
| **Ungrounded claim** | A claim whose asserted content is not supported by its cited source, despite citing a real, retrieved chunk. |
| **Partially grounded claim** | A claim that mixes genuinely supported content with unsupported or fabricated additions. |

---

## 3. Plain-language explanation

### 3.1 M7-L11 assembled a citable context; this lesson verifies the citations it enables

M7-L11 attached provenance metadata to every chunk specifically so a generated answer could cite its
sources. This lesson asks the question that metadata alone cannot answer: once a citation exists, is it
actually trustworthy?

### 3.2 A citation can be real and still wrong

§7.1–§7.2 establish the first, simpler check: does the cited source even correspond to something that was
genuinely retrieved? A citation to a source that was never in the retrieved context at all is fabricated at
the citation level — cheap to catch, and worth catching before anything more sophisticated.

### 3.3 A real citation doesn't mean the claim is true

§7.3 is this lesson's central point: a claim can cite a completely real, genuinely retrieved source and
still assert something that source doesn't actually say. Citation existence and groundedness are different
questions, and only one of them checks whether the specific words generated are true.

### 3.4 Some wrong claims are only partly wrong

§7.4 shows a subtler, arguably more common failure: a claim that gets most of its facts right and adds one
fabricated detail. A binary pass/fail check forces this into a category it doesn't belong in; a graded
score describes it honestly.

### 3.5 A narrow check demonstrates a real principle

§7.5 is honest about scope: this lesson's groundedness check only verifies numbers, because a number's
presence or absence is exactly checkable. Real systems check claims of every kind — the mechanism
demonstrated here is real; its scope is deliberately narrower than production practice.

---

## 4. Analogy

**Fact-checking a news article's footnotes.** A footnote pointing to a real, existing book is a good sign —
but it only tells you the book exists, not that the book actually says what the article claims it says. A
diligent fact-checker's job isn't done when they confirm the book is real; it's done when they open the
book to the cited page and confirm the specific sentence is actually there. An article that gets a quote
mostly right but embellishes one detail — a real event with a fabricated extra number added — is a
particularly dangerous kind of error, because the footnote looks completely legitimate at a glance.

### Where the analogy breaks

- **A human fact-checker reads for meaning, not just for specific numbers.** §7.5's narrow scope (numbers
  only) is a simplification chosen for this lab's checkability, not a claim that only numeric facts matter
  in practice.
- **A footnote's book doesn't change between printings.** M7-L08's versioning concerns (a citation to a
  now-outdated version of a source) add a dimension a static book citation doesn't have.

---

## 5. Detailed technical explanation

### 5.1 What a citation actually asserts

`[REAL]` §7.1 frames a citation like `[Source: P3]` as a provenance claim (M7-L08): this specific statement
comes from this specific retrieved chunk. That single claim decomposes into two independently checkable
questions, covered in §5.2 and §5.3.

### 5.2 Citation existence, checked

`[REAL, measured]` §7.2 checked two generated answers' citations against the actual retrieved context
(`{P3, P5}`). A citation to `P3` passed — it is genuinely present. A citation to `P9` failed — **P9 was
never retrieved at all**, so the citation is fabricated at the source-identity level, independent of
whatever claim it was attached to. This is the cheaper of the two checks: pure set membership, no
understanding of the claim's content required.

### 5.3 Groundedness: does the source actually say that?

`[REAL, measured]` §7.3 is this lesson's central demonstration. Two claims, both citing the same real
source (P3: "...15 days of PTO per year, increasing to 20 days after 3 years..."):

| Claim | Numbers asserted | Numbers in source | Groundedness |
|---|---|---|---|
| "...get 20 days of PTO after 3 years..." | 20, 3 | 15, 20, 3 | **1.00** |
| "...get 25 days of PTO after 3 years..." | 25, 3 | 15, 20, 3 | **0.50** |

**Both claims pass the citation-existence check from §5.2 — both cite a real, retrieved source.** Only the
groundedness check catches that the second claim's "25" appears nowhere in P3's actual text. **Citation
existence is necessary but not sufficient**: a real citation can sit next to a false claim just as easily as
a true one, and only checking the claim's content against the source's actual text catches the difference.

### 5.4 Partial groundedness

`[REAL, measured]` §7.4 tested a claim combining a genuinely supported fact (20 days, 3 years — both in
P3) with a fabricated addition (a further increase to 25 days at 5 years — neither number is in P3 at all).
**The resulting score was 0.50** — exactly 2 of 4 claimed numbers supported. **A pass/fail check would have
to force this claim into a category it doesn't belong in**: calling it "correct" hides the fabricated
addition; calling it "wrong" discards the genuinely accurate part. A graded score describes what actually
happened.

### 5.5 What this lab's check does and doesn't generalize to

`[CONCEPTUAL]` §7.5 states plainly that this lab's groundedness check verifies only numbers — a
deliberately narrow scope chosen because a number's presence in source text is exactly, unambiguously
checkable. Real production groundedness checking typically uses a separate model call, often framed as
natural language inference ("does this source text entail this claim?"), to catch fabricated or unsupported
claims of any kind — invented names, incorrect relationships between otherwise-real facts, or directionally
wrong statements that don't involve a number at all. **The mechanism this lab demonstrates — checking a
specific claim against its specific cited source, rather than trusting that citation existence implies
correctness — is real and load-bearing**, even though the check's scope here is narrower than a full
production system's.

### 5.6 Assumptions and limitations

- This lesson's example answers and claims are hand-authored, standing in for real LLM-generated output —
  consistent with this course's offline-first design (no real model call is made anywhere in this lab).
- The groundedness check covers only numeric claims; non-numeric claims (names, relationships, qualitative
  statements) need a more general checking method, not demonstrated here.
- This lesson does not cover what a system should do once an ungrounded or partially-grounded claim is
  detected (abstain, flag, regenerate) — that is M7-L13's dedicated topic.

---

## 6. Worked example — the support answer that cited a real policy for a fabricated number

**The system.** A support assistant answers policy questions with citations, and the team monitors for
citation existence — every generated citation is checked against the retrieved context, and any answer
citing a non-existent source is automatically rejected and regenerated.

**What went wrong anyway.** An employee received an answer stating a specific reimbursement threshold that
was **higher** than the company's actual policy, complete with a citation to the real, correct policy
document. The citation-existence check had passed — the cited document was genuinely retrieved and real —
so the answer shipped without any flag at all.

**Why citation-existence monitoring alone missed this.** Per §5.3, the citation-existence check answers
only "does this source exist," never "does this source actually say what the answer claims." The specific
dollar figure in the answer was simply wrong, generated with a real, legitimate-looking citation attached —
exactly the ungrounded-claim pattern §7.3 demonstrated directly.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Only citation existence was checked, never claim groundedness | A real citation attached to a wrong specific figure passed every automated check in place |
| 2 | No verification compared the claimed number against the cited source's actual text | The exact class of error §5.3 demonstrated went undetected by design, not by accident |
| 3 | The team's monitoring dashboard tracked "citation present: yes/no" as its only quality signal | A meaningfully wrong answer looked identical to a correct one on every metric being watched |

### The fix

**Add groundedness checking alongside citation-existence checking**, per §5.3 — the two catch genuinely
different failure classes, and existence checking alone leaves exactly this gap open.

**For numeric claims specifically, verify the asserted number actually appears in the cited source text**,
per §5.3's method — a cheap, exact, high-confidence check for one common and consequential error type.

**Track groundedness, not just citation presence, as a monitored quality signal** — per §6's own incident,
a dashboard measuring only citation existence cannot distinguish this failure from a fully correct answer.

**The general rule.** **A citation is a claim about where information came from, not a guarantee that the
information is correct — verifying the citation exists and verifying the claim is grounded are two
different checks, and a system that performs only the first has a real, exploitable gap.**

---

## 7. Practical activity

**File:** [`labs/m7/l12_citations_evidence_verification.py`](../../labs/m7/l12_citations_evidence_verification.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l12_citations_evidence_verification.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A CITATION CONNECTS A CLAIM TO A SPECIFIC RETRIEVED SOURCE
============================================================================
  Retrieved context available to generation: ['P3', 'P5']
  Generated answer: 'Full-time employees get 20 days of PTO after 3 years of service. [Source: P3]'

  A citation like '[Source: P3]' is a claim about PROVENANCE (M7-L08):
  'this specific statement comes from this specific retrieved chunk.'
  That claim can be checked two entirely different ways, covered next:
  does P3 actually exist in what was retrieved (section 2), and does
  P3's actual text actually support what was just said (section 3)?

============================================================================
2. CHECK 1 -- DOES THE CITED SOURCE EXIST IN THE RETRIEVED SET AT ALL?
============================================================================
  Answer: 'Employees get 20 days of PTO after 3 years. [Source: P3]'
    Cites 'P3' -- exists in retrieved context: True

  Answer: 'Employees get free gym membership after 1 year. [Source: P9]'
    Cites 'P9' -- exists in retrieved context: False

  P9 was never retrieved at all (it isn't in RETRIEVED_CONTEXT) -- a
  citation to it is fabricated at the CITATION level, regardless of
  whether the claim next to it happens to be true. This is the cheaper,
  simpler of the two checks: does the cited ID correspond to anything
  real that was actually handed to the model.

============================================================================
3. CHECK 2 -- DOES THE CITED TEXT ACTUALLY SUPPORT THE CLAIM?
============================================================================
  Claim: 'Full-time employees get 20 days of PTO after 3 years of service.'
    Numbers asserted in claim: ['20', '3']
    Numbers present in cited source (P3): ['15', '20', '3']
    Groundedness score: 1.00
    Citation exists (P3 is real): True -- but is the CLAIM correct? YES

  Claim: 'Full-time employees get 25 days of PTO after 3 years of service.'
    Numbers asserted in claim: ['25', '3']
    Numbers present in cited source (P3): ['15', '20', '3']
    Groundedness score: 0.50
    Citation exists (P3 is real): True -- but is the CLAIM correct? NO -- unsupported by the cited text

  Both claims cite a REAL, retrieved source (P3 exists, section 2's
  check would pass for both). Only the groundedness check catches the
  second claim's fabricated '25' -- the source says 20, not 25. A
  citation existing is necessary but NOT sufficient for a claim to be
  trustworthy; this is the specific gap groundedness checking closes.

============================================================================
4. A PARTIALLY GROUNDED CLAIM: REAL FACT MIXED WITH A FABRICATED DETAIL
============================================================================
  Claim: 'Full-time employees get 20 days of PTO after 3 years of service, increasing further to 25 days after 5 years.'
    Numbers asserted in claim: ['20', '25', '3', '5']
    Numbers present in cited source (P3): ['15', '20', '3']
    Groundedness score: 0.50  (2 of 4 claimed numbers actually supported)

  '20' and '3' are genuinely in the source; '25' and '5' are NOT -- P3
  says nothing about a further increase at 5 years at all. A pure pass/
  fail check would have to call this claim either entirely right or
  entirely wrong, neither of which is accurate. A PARTIAL score (0.50
  here) correctly flags this as a claim worth reviewing, not a clean
  pass -- exactly the kind of subtly fabricated addition a fluent,
  otherwise-accurate-sounding answer can smuggle in.

============================================================================
5. WHAT REAL PRODUCTION GROUNDEDNESS CHECKING ACTUALLY LOOKS LIKE
============================================================================
  `[CONCEPTUAL]` This lab's groundedness check is deliberately narrow:
  it verifies only NUMBERS, because a number either appears in the
  source or it does not -- a fact simple enough to check by hand and
  trust completely. Real production groundedness checking typically
  uses a separate model call (often framed as natural language
  inference: 'does this source text ENTAIL this claim?') to catch
  fabricated or unsupported claims of ANY kind, not just wrong numbers
  -- invented names, incorrect relationships between real facts, or
  claims that are directionally wrong without changing any number at
  all. `[UNVERIFIED -- specific NLI-based groundedness tools and their
  accuracy change quickly; confirm current best practice before
  relying on any specific one.]`

  The MECHANISM this lab demonstrates -- checking a specific,
  verifiable claim against the specific cited source text, rather than
  trusting that a citation existing means the claim is correct -- is
  real and load-bearing, even though the CHECK ITSELF here is
  narrower than a full production system's.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: citation extraction, citation-existence checking, and the
  numeric groundedness score are all genuinely computed on the stated
  text, not scripted -- the ungrounded and partially-grounded examples
  fail their checks because the numbers genuinely are or are not in
  the source text, checkable by hand.

  MOCK / ILLUSTRATIVE: the example answers and claims in this lab are
  hand-authored, standing in for real LLM-generated output -- no real
  model call was made, consistent with this course's offline-first
  design. The groundedness check itself is intentionally narrowed to
  numbers only, a real but partial instance of the broader NLI-style
  checking a production system would use.

  NOT SHOWN: checking non-numeric claims (names, relationships,
  qualitative statements) for groundedness, which needs a more general
  method than number-matching; and what a system should DO once an
  ungrounded or partially-grounded claim is detected -- abstaining or
  flagging the answer, which is M7-L13's dedicated topic next.

Done.
```

### 7.3 Reading the result

**Section 2 and section 3 are deliberately two separate checks, and the lesson's structure insists on
that separation.** It would be easy to conflate "has a citation" with "is trustworthy" — presenting them
as two distinct, sequential checks makes the gap between them impossible to miss.

**Section 3's table is the lesson's core evidence.** Two claims, one cited source, dramatically different
groundedness scores (1.00 vs. 0.50) — this is not a subtle effect, and it's measured, not asserted.

**Section 4 is arguably more realistic than section 3.** A claim that's completely fabricated is a
relatively easy case to imagine catching eventually; a claim that's mostly right with one smuggled-in
addition is the harder, more dangerous, and more common failure this section demonstrates directly.

---

## 8. Common mistakes and troubleshooting

1. **Treating citation existence as sufficient evidence a claim is correct.** §5.3 — a real citation can
   sit next to a false or fabricated claim just as easily as a true one.
2. **Using only a pass/fail groundedness check.** §5.4 — a partially grounded claim needs a graded score to
   be described accurately; forcing a binary verdict hides real information either way.
3. **Monitoring only citation presence as a quality signal.** §6 — this cannot distinguish a genuinely
   correct answer from one with a real citation attached to a wrong claim.
4. **Assuming a narrow, numeric-only groundedness check generalizes to all claim types.** §5.5 — non-numeric
   claims need a different, more general verification method.
5. **Skipping citation-existence checking because groundedness checking seems more important.** §5.2 — the
   two catch different failure classes; a fabricated citation to a non-existent source is a distinct,
   cheaper-to-catch problem worth checking regardless.
6. **Assuming a claim that gets most details right needs no further scrutiny.** §7.4 — a fluent, mostly
   accurate answer is exactly where a small fabricated addition is easiest to miss.

| Symptom | Likely cause | Fix |
|---|---|---|
| A generated answer cites a source that doesn't correspond to anything retrieved | The model fabricated a citation ID | Check every citation against the actual retrieved set (§5.2) |
| An answer with a valid citation still states an incorrect fact | The citation exists but the specific claim isn't supported by the source | Add groundedness checking that verifies claim content against source text (§5.3) |
| A groundedness check reports an answer as either fully correct or fully wrong, but neither feels accurate | The check is binary (pass/fail) rather than graded | Use a scored groundedness check that can represent partial support (§5.4) |
| Quality monitoring shows no issue, but users report factually wrong answers with citations | Only citation existence is being monitored, not groundedness | Track groundedness as a distinct, monitored quality signal (§6) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Check both citation existence and claim groundedness — they catch different failure
  classes, and checking only one leaves a real, exploitable gap (§5.2–§5.3, §6).
- **Reliability.** Use graded, not binary, groundedness scoring where a claim may be partially supported —
  a pass/fail check cannot accurately describe a mixed claim (§5.4).
- **Reliability.** Monitor groundedness, not just citation presence, as a production quality signal — per
  §6, citation-existence monitoring alone cannot catch a real citation attached to a wrong claim.
- **Cost.** A narrow, cheap check (like this lesson's numeric groundedness check) can catch a real and
  common error class without the cost of a full model-based groundedness check for every claim — consider
  layering narrow, cheap checks before more expensive general ones.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does a citation like "[Source: P3]" actually claim?
2. What does the citation-existence check verify, and what does it NOT verify?
3. Why did both example claims in §7.3 pass the citation-existence check?
4. What made the second claim in §7.3 ungrounded, specifically?
5. Why couldn't a pass/fail check accurately describe §7.4's partially grounded claim?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.3's two groundedness scores and §7.4's partial score on your own machine.
2. Construct a new claim citing P5 (the parental leave chunk) with one fabricated number, and confirm the
   groundedness check catches it.
3. Extend the groundedness checker to also verify a specific keyword (not just numbers) appears in the
   cited source, and test it on a claim with a fabricated keyword.
4. Construct a claim that cites a NON-existent source AND contains a fabricated number, and run both
   checks (existence and groundedness) on it, reporting both results.
5. Design a claim that would score exactly 0.75 groundedness (3 of 4 numbers supported) and verify it with
   the lab's checker.

### Exercise 3 — Challenge (~50 min)

1. Extend the groundedness check to handle number-word forms (e.g. "twenty" as well as "20") using a
   number-word-to-digit mapping, and test it against a source using spelled-out numbers.
2. Design and implement a simple keyword-overlap-based groundedness check (beyond numbers) for qualitative
   claims, and test it on a claim making an unsupported qualitative assertion.
3. Research (conceptually) how a real NLI (natural language inference) model would be used to check
   groundedness, and describe the three-way classification (entailment, contradiction, neutral) it
   typically produces.
4. Design a combined citation-verification pipeline that runs both existence and groundedness checks on
   every claim in a multi-claim answer, producing a per-claim report.
5. Using this lesson's §6 worked example as a model, design a monitoring dashboard specification that
   tracks both citation existence and groundedness as separate, visible metrics.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l12).)*

**Q1.** Per §7.1, what does a citation like "[Source: P3]" claim, per M7-L08's provenance framing?

- A. That the source document has been permanently deleted from the corpus.
- B. That the specific statement it follows comes from that specific retrieved chunk.
- C. That the model has independently verified the claim using outside knowledge.
- D. That the cited chunk is the only relevant document in the entire corpus.

**Q2.** Per §7.2, what does the citation-existence check verify?

- A. Whether the claim's grammar is correct.
- B. Whether the cited source is the single most relevant document available.
- C. Whether the claim contains any numbers at all.
- D. Whether the cited source ID actually corresponds to something that was genuinely retrieved and handed to generation, regardless of whether the claim itself is accurate.

**Q3.** Per §7.2's measured result, why was the citation to "P9" flagged as fabricated?

- A. P9 was never part of the retrieved context at all — the citation points to something that was never actually retrieved.
- B. P9 exists in the retrieved context but was formatted incorrectly.
- C. The claim next to the P9 citation was factually correct, which is why it was flagged.
- D. P9 is a real source that the check incorrectly rejected due to a bug.

**Q4.** Per §7.3, why did BOTH the grounded and ungrounded claims pass the citation-existence check?

- A. Because the citation-existence check does not actually run on either claim.
- B. Because both claims contained exactly the same text, word for word.
- C. Both cited P3, which is a real, retrieved source — citation existence alone says nothing about whether the specific claim made is actually supported by that source's text.
- D. Because the citation-existence check always returns True regardless of input.

**Q5.** Per §7.3's measured result, what specifically made the second claim ungrounded?

- A. It failed to include any citation marker at all.
- B. It asserted "25" days, a number that does not appear anywhere in the cited source text, which actually says "20."
- C. It cited a source that does not exist in the retrieved context.
- D. It was written in a different language than the source text.

**Q6.** Per §7.3, what is the relationship between citation existence and groundedness?

- A. Citation existence and groundedness are exactly the same check, performed twice.
- B. Groundedness is irrelevant as long as a citation exists.
- C. Citation existence is sufficient on its own to guarantee a claim is trustworthy.
- D. Citation existence is necessary but not sufficient for a claim to be trustworthy — a real citation can still support a false or unsupported claim.

**Q7.** Per §7.4, why couldn't a simple pass/fail groundedness check accurately describe the partially
grounded claim?

- A. The claim mixed a genuinely supported fact (20 days, 3 years) with a fabricated, unsupported detail (25 days after 5 years), so neither "fully correct" nor "fully wrong" was accurate.
- B. The claim contained no numbers at all, making any scoring impossible.
- C. The source text was missing entirely from the retrieved context.
- D. Pass/fail checks are always more accurate than partial scores in every situation.

**Q8.** Per §7.4's measured result, what groundedness score did the partially grounded claim receive, and
why?

- A. 1.00, because every number in the claim was found in the source.
- B. 0.00, because no number in the claim was found in the source.
- C. 0.50, because exactly 2 of the 4 numbers asserted in the claim were actually present in the cited source.
- D. The score could not be computed at all for this claim.

**Q9.** Per §7.5, how does this lab's groundedness check differ from real production groundedness
checking?

- A. This lab's check verifies grammar and spelling; production systems verify only numbers.
- B. This lab's check is narrowed to verifying only numbers; real production systems typically use a separate model call (often framed as natural language inference) to check claims of any kind, not just numeric ones.
- C. This lab's check and real production groundedness checking are identical in every respect.
- D. Real production systems never check groundedness at all, unlike this lab.

**Q10.** Per §7.5, is the underlying mechanism this lab demonstrates (checking a specific claim against its
cited source) real, or only illustrative?

- A. Neither the mechanism nor the specific check in this lab is real; both are entirely illustrative.
- B. The mechanism is illustrative, but the specific numeric check is a real, production-grade implementation.
- C. Both the mechanism and the specific check are exact replicas of a specific commercial product.
- D. The mechanism itself is real and load-bearing — what's narrowed for this lab is the scope of the check (numbers only), not the underlying principle.

**Q11.** Which topic does this lesson explicitly leave to M7-L13?

- A. What a system should do once an ungrounded or partially-grounded claim is detected — such as abstaining or flagging the answer.
- B. Citation-existence checking, which this lesson covers directly instead.
- C. Numeric groundedness scoring, which this lesson covers directly instead.
- D. Citation extraction from generated text, which this lesson covers directly instead.

**Q12.** What is the general lesson this lab demonstrates about citations in a RAG system?

- A. Any citation that exists automatically guarantees the claim it supports is fully correct.
- B. Citations are unnecessary in a RAG system as long as retrieval quality is high.
- C. A citation being present and pointing to a real source does not guarantee the claim it supports is actually correct — citation existence and claim groundedness are two distinct checks, both necessary.
- D. Groundedness checking makes citation-existence checking entirely redundant.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team monitors "citation present: yes/no" as
its only automated quality check for a RAG system, and it always shows 100% pass. Based on this lesson,
why might this still be missing real quality problems, and what would you add?

---

## 12. Revision notes

- **A citation is a provenance claim: this statement comes from this specific retrieved source** — that
  claim decomposes into two independently checkable questions: does the source exist, and does it support
  the claim.
- **Citation existence checking verifies only that a cited source was genuinely retrieved** — a cheap,
  exact, necessary check that catches fabricated citations to sources that were never part of the retrieved
  context.
- **Groundedness checking verifies the claim's actual content is supported by the cited source's text** —
  measured directly: two claims citing the identical real source scored 1.00 and 0.50, because one asserted
  a number (25) the source never states.
- **Citation existence is necessary but not sufficient** — a real citation can support a false claim just as
  easily as a true one, which is the specific gap groundedness checking closes.
- **A partially grounded claim needs a graded score, not a binary verdict** — measured directly: a claim
  mixing a real fact with a fabricated addition scored 0.50, correctly flagging it as neither fully correct
  nor fully wrong.
- **This lesson's numeric groundedness check is a real but narrow instance of a general principle** — real
  production systems typically use a broader, model-based (often NLI-style) check for claims of any kind,
  not just numbers.

---

## 13. Completion checklist

- [ ] I can explain what a citation actually claims about a statement's provenance.
- [ ] I can implement a citation-existence check against a retrieved context.
- [ ] I can implement a groundedness check that verifies claim content against cited source text.
- [ ] I can explain why citation existence is necessary but not sufficient for trustworthiness.
- [ ] I can distinguish fully grounded, ungrounded, and partially grounded claims, and score them
      appropriately.
- [ ] I monitor groundedness, not just citation presence, as a production quality signal.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, guidance on citations and grounding where available. `[UNVERIFIED]`
- Es, S. et al., *RAGAS: Automated Evaluation of Retrieval Augmented Generation*, 2023 (general reference
  for RAG groundedness/faithfulness metrics). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L13 — Abstention: teaching the system to say "I don't know"

You now have the tools to detect when a generated claim isn't actually supported by its evidence. Next:
what the system should do about it — building on M7-L01's own early abstention example into a full,
deliberate design for when and how a RAG system should decline to answer.
