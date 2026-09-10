# M7-L14 — Conflicting, Duplicated and Outdated Sources

| | |
|---|---|
| **Lesson ID** | M7-L14 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L08](M7-L08-metadata-provenance-versioning.md) |

---

## 1. Learning objectives

1. **Implement** a real, computable conflict-detection check between two retrieved sources on the same
   topic.
2. **Distinguish** genuine conflict (multiple current, legitimate sources that disagree) from false
   conflict (stale data that versioning metadata should have filtered out).
3. **Compare** three resolution strategies for genuine conflict, and explain when each is appropriate.
4. **Demonstrate** why a textual-similarity-only deduplication step can silently discard a genuine
   disagreement between two near-duplicate sources.
5. **Design** a source-conflict handling policy that connects versioning (M7-L08), deduplication
   (M7-L05), and abstention (M7-L13) into one coherent response.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Conflicting sources** | Two or more retrieved sources that make contradictory claims about the same fact. |
| **False conflict** | An apparent disagreement between sources that is actually just outdated data not filtered by currency metadata. |
| **Genuine conflict** | A disagreement between two or more sources that are all legitimately current — versioning alone cannot resolve it. |
| **Authority signal** | A real, trustworthy basis for preferring one source over another in a conflict (e.g. an organizational hierarchy), distinct from an arbitrary tie-break. |
| **Fact-agreement check** | Verifying that two textually similar chunks actually assert the same underlying facts, not just similar wording, before treating them as duplicates. |

---

## 3. Plain-language explanation

### 3.1 M7-L13 decided when to answer; this lesson asks what to do when the evidence disagrees

M7-L13 built a calibrated decision for refusing to answer when retrieval or groundedness signals are weak.
This lesson covers a different, harder case: retrieval succeeded, confidence is high, and the system
correctly decides to answer — but the evidence it retrieved doesn't agree with itself.

### 3.2 Not every apparent conflict is a real one

§7.1–§7.2 draw the lesson's most important distinction early: two sources with different numbers on the
same topic *look* identical whether they're genuinely disagreeing or whether one is simply an outdated
version of the other. Only one of these is actually new territory — the other is M7-L08's versioning
problem wearing a different name.

### 3.3 Some conflicts genuinely can't be filtered away

§7.3 shows the case versioning cannot fix: two sources, both legitimately current, that still disagree.
There is no "older" one to discard, because neither is wrong by virtue of age.

### 3.4 Resolving genuine conflict has real options, each with a real cost

§7.4 compares three concrete strategies — transparency, authority-based preference, and abstention — none
universally correct, each appropriate under different, specific conditions.

### 3.5 Deduplication can hide a conflict instead of resolving one

§7.5 connects back to M7-L05: a dedup step that only checks wording similarity can collapse two chunks
that are almost identically worded but assert different facts, silently discarding one of two genuinely
conflicting numbers instead of surfacing the disagreement.

---

## 4. Analogy

**Two witnesses describing the same event.** If witness A saw the event on Monday and witness B saw a
different event entirely on Tuesday, there's no real conflict — they're describing different things
(false conflict, or simply irrelevant). If both witnesses watched the exact same event, at the exact same
time, and still describe it differently, that's a genuine conflict no amount of "which one saw it more
recently" can resolve — recency isn't the axis that matters here. A good investigator doesn't pick
whichever witness sounds more confident; they either present both accounts honestly, weigh them against a
known-reliable authority (a video recording, if one exists), or say plainly that the account can't be
settled from what's available.

### Where the analogy breaks

- **Human witnesses can be cross-examined for more detail.** §7.4's strategies operate on fixed, already-
  retrieved text — there's no equivalent of asking a source a follow-up question.
- **A recording is an obvious, universally trusted authority.** §7.4's "authority signal" (Strategy 2) is
  domain-specific and must be deliberately designed — there is no default, universal tie-breaker a system
  can assume exists.

---

## 5. Detailed technical explanation

### 5.1 Detecting conflict, for real

`[REAL, measured]` §7.1 compared two chunks about the same PTO policy fact — one from a corporate-wide HR
policy (15 days), one from a team handbook (20 days). A shingle-based topic-similarity check (M7-L05's
mechanism) confirmed they're about the same fact (0.600, above a 0.5 threshold), and number extraction
(M7-L12's mechanism) confirmed they assert different values. **Both checks together — same topic, different
numbers — is a real, computable conflict signal**, available before generation ever happens.

### 5.2 False conflict: versioning's job, not a new one

`[REAL, measured]` §7.2 ran the identical detection logic on two versions of the same policy — v1 (15
days, `is_current=False`) and v2 (20 days, `is_current=True`). Raw detection flags this the same way as
§7.1. **But filtering to `is_current=True` first (M7-L08's own mechanism) leaves exactly one source — the
"conflict" disappears entirely**, because it was never a genuine disagreement between two valid sources; it
was one fact's history, retrievable only because currency filtering hadn't been applied.

### 5.3 Genuine conflict: when filtering doesn't help

`[REAL]` §7.3 returns to §7.1's pair and confirms both chunks are marked `is_current=True` simultaneously.
**Filtering to current sources changes nothing here — both already pass.** This is the case M7-L08's
mechanism cannot resolve by design: two legitimately different, simultaneously valid documents (a
corporate policy and a team-specific handbook) that disagree on a real fact, with no "older" version to
discard.

### 5.4 Three resolution strategies, compared

`[REAL]` §7.4 implemented three genuinely different responses to §7.3's conflict:

1. **Transparent** — state both sources and their claims explicitly, leaving the decision to the user.
2. **Authority-based** — prefer one source using a real, predetermined hierarchy (here: corporate policy
   over team handbook), stating which source won and why.
3. **Abstain and escalate** — decline to resolve, flagging for human review, reusing M7-L13's mechanism but
   triggered by detected conflict rather than low retrieval confidence.

**None is universally correct.** Transparency is always honest but pushes the burden back to the user.
Authority-based resolution is decisive but **requires a real, trustworthy hierarchy to already exist** —
inventing one arbitrarily would be worse than not resolving at all. Abstention is safest when no reliable
authority signal exists and a wrong guess would be costly — **the same cost asymmetry M7-L13 measured for
abstention generally**, now triggered by a different signal.

### 5.5 Deduplication can hide conflict instead of resolving it

`[REAL, measured]` §7.5 compared two near-identically worded chunks (an HR mirror site and an archive copy)
describing PTO accrual with different numbers (15 vs. 18). Text similarity (M7-L05/M7-L11's shingling
method) came in at 0.636 — **above the 0.5 dedup threshold, meaning a naive dedup step would collapse these
into one, silently keeping only one of the two disagreeing numbers.** A dedup step checking only wording
similarity cannot see this — it needs an explicit fact-agreement check (number extraction, or §5.1's
conflict detector) before collapsing near-duplicates, not just a wording-similarity threshold.

### 5.6 Assumptions and limitations

- This lesson's shingle-based similarity check uses k=2, not M7-L05's own k=3 default — chosen because a
  single differing word in these short sentences corrupts a larger fraction of overlapping shingles at
  k=3 than is useful here, per M7-L05's own k-sensitivity finding.
- The authority hierarchy in §5.4 (corporate policy over team handbook) is hand-authored for this lesson —
  a real system's authority signal is domain-specific and must be deliberately designed, not assumed to
  exist generically.
- This lesson's conflict detection covers numeric claims only; detecting contradictory qualitative
  statements needs a more general method, not demonstrated here.

---

## 6. Worked example — the two-answer incident that turned out to be one real disagreement

**The system.** A company-wide policy assistant retrieves from both a central HR knowledge base and
several team-specific wikis, all treated as equally valid, current sources with no conflict detection.

**What happened.** Two employees in different teams asked the identical PTO question the same week and
received confidently different answers, each correctly cited to a real, current source. Support treated
this initially as a bug — "the system gave two different answers to the same question" — and escalated it
as a retrieval defect.

**What the investigation actually found.** Both answers were individually correct, in the narrow sense that
each accurately reflected its cited source. The real issue, once conflict detection (§5.1) was retroactively
applied, was that the corporate policy and one team's handbook had genuinely diverged — not a retrieval bug
at all, but an actual, unresolved policy inconsistency that predated the RAG system and had simply gone
unnoticed until a system started surfacing both sources reliably.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No conflict detection ran before answers were generated | Two contradictory, individually well-supported answers shipped with no signal that anything was amiss |
| 2 | The underlying policy inconsistency between corporate HR and the team handbook had never been caught | The RAG system exposed a real organizational problem it did not create |
| 3 | The initial investigation assumed a retrieval bug rather than checking for genuine source conflict first | Time was spent looking for a defect that didn't exist, in the wrong part of the system |

### The fix

**Add conflict detection as a standing pipeline check**, per §5.1, so disagreements between current
sources are caught before an answer ships, not after a user reports two different ones.

**Distinguish genuine conflict from false conflict before investigating further**, per §5.2–§5.3 — this
determines whether the fix belongs in versioning (M7-L08) or requires a real resolution strategy (§5.4).

**Treat a detected genuine conflict as a signal worth escalating to the source owners**, not only to the
RAG pipeline's engineers — per this incident, the underlying inconsistency was an organizational problem
the system correctly surfaced, not a defect it introduced.

**The general rule.** **A RAG system retrieving from multiple legitimate sources will eventually surface
a real disagreement between them — treat this as expected, detectable behavior with a designed response,
not as evidence the retrieval pipeline itself is broken.**

---

## 7. Practical activity

**File:** [`labs/m7/l14_conflicting_duplicated_outdated_sources.py`](../../labs/m7/l14_conflicting_duplicated_outdated_sources.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l14_conflicting_duplicated_outdated_sources.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. DETECTING CONFLICT: TWO SOURCES, SAME TOPIC, DIFFERENT NUMBERS
============================================================================
  Chunk A (Global HR Policy (corporate-wide)): 'Full-time employees accrue 15 days of PTO per year.'
  Chunk B (Engineering Team Handbook): 'Full-time employees accrue 20 days of PTO per year.'

  Topic similarity (M7-L05's shingling method): 0.600 (>= 0.5 -> same topic)
  Numbers in A: ['15']   Numbers in B: ['20']
  Conflict detected: True

  Both chunks are clearly about the SAME fact (same topic, high shingle
  overlap) but assert DIFFERENT numbers -- a real, computable signal
  that something needs resolving before an answer is generated, not
  after the fact.

============================================================================
2. FALSE CONFLICT: STALE DATA M7-L08's VERSIONING WOULD HAVE CAUGHT
============================================================================
  Chunk C (v1, is_current=False): 'Full-time employees accrue 15 days of PTO per year.'
  Chunk D (v2, is_current=True): 'Full-time employees accrue 20 days of PTO per year.'

  Raw conflict detection (ignoring version metadata): True
  After filtering to is_current=True (M7-L08's own fix): ['PTO#v2'] remain -- 1 source, no conflict possible.

  This LOOKS like section 1's problem -- two sources, same topic,
  different numbers -- but it isn't genuine conflict at all. It's a
  single fact that CHANGED over time, retrievable as two versions
  only because M7-L08's currency filtering wasn't applied. The fix here
  is M7-L08's, not a new mechanism: filter to current sources FIRST,
  and this specific 'conflict' disappears entirely.

============================================================================
3. GENUINE CONFLICT: BOTH SOURCES ARE CURRENT, AND THEY STILL DISAGREE
============================================================================
  Back to section 1's Chunk A and Chunk B: both marked is_current=True.
  Chunk A is_current: True   Chunk B is_current: True
  Both current simultaneously: True

  Filtering to 'current only' (section 2's fix) does NOTHING here --
  both sources already pass that filter. This is not stale data hiding
  behind missing version metadata; it is two legitimately different,
  simultaneously valid documents that genuinely disagree -- a company-
  wide policy and a team-specific handbook, neither one wrong by
  virtue of being older. Versioning (M7-L08) cannot resolve this,
  because there is no 'older' version here to discard.

============================================================================
4. THREE RESOLUTION STRATEGIES FOR GENUINE CONFLICT, COMPARED
============================================================================
  STRATEGY 1 -- transparent, surface both:
    'Sources disagree: Global HR Policy (corporate-wide) states 15 days, while Engineering Team Handbook states 20 days. Please confirm which applies to your situation.'

  STRATEGY 2 -- prefer by a real authority rule (corporate policy
  outranks a team handbook, a genuine, if domain-specific, business rule):
    'Full-time employees accrue 15 days of PTO per year. (Source: Global HR Policy (corporate-wide) -- takes precedence per corporate policy hierarchy)'

  STRATEGY 3 -- abstain and escalate (M7-L13's mechanism, triggered by
  conflict rather than low retrieval score):
    "I found conflicting information from two current sources (Global HR Policy (corporate-wide) and Engineering Team Handbook) and can't confidently resolve which applies. Flagging for human review rather than guessing."

  None of these is universally correct. Strategy 1 is honest but pushes
  the decision back to the user. Strategy 2 is decisive but REQUIRES a
  real, trustworthy authority signal to exist -- guessing one would be
  worse than not resolving at all. Strategy 3 is safest when no
  authority signal exists and the disagreement matters enough that a
  wrong guess would be costly -- the same asymmetry M7-L13 measured for
  abstention generally, applied here to a conflict-triggered case.

============================================================================
5. NEAR-DUPLICATES THAT AREN'T ACTUALLY DUPLICATES
============================================================================
  Chunk E (HR Mirror Site): 'Full time staff accrue 15 days of PTO each year.'
  Chunk F (HR Archive Copy): 'Full time staff accrue 18 days of PTO each year.'

  Text similarity (M7-L05/M7-L11's shingling method): 0.636
  Would a naive dedup step (threshold 0.5) collapse these into one, keeping only the first? True

  But the actual NUMBERS differ: ['15'] vs ['18'] -- these are
  not really duplicates, they are two DIFFERENT claims that happen to
  be worded almost identically. A dedup step (M7-L05, M7-L11) that only
  checks textual similarity would silently discard one of two genuinely
  conflicting numbers, hiding a real disagreement behind what LOOKS
  like harmless redundancy. Deduplication needs a fact-agreement check
  (this section's number-extraction, or section 1's conflict detector)
  BEFORE collapsing near-duplicates, not just a wording-similarity check.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: shingle-based topic similarity (M7-L05's mechanism -- word
  shingles plus Jaccard similarity -- at k=2 rather than M7-L05's own
  k=3 default, chosen per M7-L05's own k-sensitivity finding: these
  short sentences differ in only one word, which k=3 over-penalizes);
  number extraction (M7-L12's exact method); and every conflict/dedup
  determination in this lab are genuinely computed from the stated
  chunk text, not scripted to fit the narrative.

  ILLUSTRATIVE: the specific chunks, sources, and authority ranking
  (corporate policy over team handbook) are hand-authored for this
  lesson -- a real system's authority hierarchy is domain-specific and
  must be deliberately designed, not assumed.

  NOT SHOWN: automatically inferring an authority hierarchy from
  metadata alone (a hard, general problem); combining conflict
  detection with M7-L13's abstention decision into one unified
  pipeline stage; and detecting conflicts that don't involve numbers
  (contradictory qualitative statements), which needs a more general
  method than number extraction.

Done.
```

### 7.3 Reading the result

**Sections 1 and 2 are deliberately structured to look almost identical at first glance, and that's the
point.** Both show two sources, the same topic, different numbers — only the `is_current` metadata reveals
which one is genuine conflict and which is a versioning gap wearing a conflict's clothes.

**Section 5's honest bug-fix (documented in §5.6) is worth noting explicitly.** The k=2 vs. k=3 shingle-size
adjustment wasn't cosmetic — at k=3, these short sentences' single-word difference corrupted enough
shingles that genuinely similar text scored as dissimilar, exactly the sensitivity M7-L05 first measured,
now encountered again in a new context.

**Section 4's three strategies are deliberately left without a declared "winner."** This lesson's job is
naming the real trade-offs, not prescribing one universal answer — the right choice depends on whether a
trustworthy authority signal actually exists and how costly a wrong resolution would be.

---

## 8. Common mistakes and troubleshooting

1. **Treating every numeric discrepancy between sources as the same kind of problem.** §5.2–§5.3 —
   distinguish false conflict (a versioning gap) from genuine conflict (legitimately disagreeing current
   sources) before choosing a fix.
2. **Applying an authority-based resolution without a real, predetermined hierarchy.** §5.4 — an invented
   or arbitrary authority ranking is worse than acknowledging the conflict honestly.
3. **Deduplicating retrieved chunks using only textual similarity.** §5.5 — this can silently discard a
   genuine factual disagreement between two near-identically worded chunks.
4. **Investigating a "the system gave two different answers" report as a retrieval bug by default.** §6 —
   check for genuine source conflict first; the system may be correctly surfacing a real inconsistency.
5. **Assuming versioning (M7-L08) alone is sufficient to prevent all source disagreements.** §5.3 — it only
   resolves disagreements caused by staleness, not disagreements between simultaneously valid sources.
6. **Picking one strategy (transparency, authority, or abstention) as universally correct.** §5.4 — the
   right choice depends on whether a trustworthy authority signal exists and how costly a wrong resolution
   would be.

| Symptom | Likely cause | Fix |
|---|---|---|
| Two users receive different, both-cited answers to the same question | Genuine conflict between two current sources, or a versioning gap | Run conflict detection; check is_current on both sources to distinguish the two cases (§5.1-§5.3) |
| A retrieved answer silently reflects only one of two disagreeing sources | Deduplication collapsed near-duplicate chunks without checking factual agreement | Add a fact-agreement check before deduplication (§5.5) |
| An authority-based conflict resolution produces a confidently wrong answer | The authority ranking used was invented or unreliable, not a real, predetermined hierarchy | Only use authority-based resolution with a genuinely trustworthy signal; otherwise use transparency or abstention (§5.4) |
| A "two different answers" bug report leads nowhere after investigating retrieval | The actual cause is a genuine, pre-existing inconsistency between source documents | Check for source-level conflict directly, and escalate to source owners if confirmed (§6) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Run conflict detection as a standing check before generation, distinguishing genuine
  conflict from false (versioning-related) conflict (§5.1–§5.3).
- **Reliability.** Never apply authority-based conflict resolution without a real, predetermined,
  trustworthy hierarchy — an invented one is worse than transparency or abstention (§5.4).
- **Reliability.** Check near-duplicate chunks for factual agreement, not just textual similarity, before
  deduplication collapses them (§5.5).
- **Cost.** Treat a detected genuine source conflict as a signal to escalate to source owners, not only a
  pipeline concern — it may indicate a real, pre-existing inconsistency worth fixing at the source (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, how does this lesson's conflict detector decide two chunks disagree?
2. Why is the discrepancy in §7.2 called a "false conflict"?
3. Why couldn't versioning resolve the conflict in §7.3?
4. Name the three resolution strategies from §7.4, and one condition under which each is appropriate.
5. Why can deduplication based only on textual similarity be dangerous?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's conflict detection and §7.5's dedup-threshold result on your own machine.
2. Construct a new pair of chunks with a genuine conflict (your own topic) and confirm the detector flags
   it correctly.
3. Construct a pair of chunks that are near-duplicates AND genuinely agree on their facts, and confirm the
   dedup step correctly collapses them without losing any real disagreement.
4. Design a different authority hierarchy (e.g. "most recently reviewed source wins" using a stated review
   date) and implement Strategy 2 using it instead of the department-based ranking.
5. Using M7-L13's framework, decide which of §7.4's three strategies you would combine with an abstention
   threshold, and justify your choice.

### Exercise 3 — Challenge (~50 min)

1. Extend the conflict detector to handle qualitative (non-numeric) disagreements, using a keyword-based
   contradiction check (e.g. "allowed" vs. "not allowed") rather than number extraction.
2. Design and implement a combined pipeline stage that runs deduplication with a built-in fact-agreement
   check, so near-duplicates are only collapsed when their extracted facts genuinely match.
3. Research (conceptually) how a real organization might formally define an authority hierarchy for
   conflicting policy documents, and design a metadata schema (extending M7-L08) that would support it.
4. Implement a conflict-aware version of M7-L13's abstention decision, where detected genuine conflict
   triggers Strategy 3 (abstain and escalate) automatically, and test it end to end.
5. Using this lesson's §6 worked example as a model, write an escalation policy for what a team should do
   when a RAG system surfaces a genuine, previously-unknown source conflict.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l14).)*

**Q1.** Per §7.1, how was conflict between Chunk A and Chunk B detected?

- A. By checking whether the two chunks were retrieved at different times.
- B. Both chunks scored above a shingle-similarity threshold (same topic) but asserted different numbers for what is clearly the same fact.
- C. By comparing the two chunks' source URIs character by character.
- D. By checking whether either chunk contained a citation marker.

**Q2.** Per §7.2, why is the discrepancy between Chunk C (v1) and Chunk D (v2) described as a FALSE
conflict rather than a genuine one?

- A. Because the two chunks were retrieved from completely unrelated topics.
- B. Because one of the two chunks contained a spelling error.
- C. Because the numbers in both chunks were actually identical.
- D. It's a single fact that changed over time, retrievable as two versions only because currency (is_current) filtering wasn't applied — filtering to the current version alone makes the apparent conflict disappear.

**Q3.** Per §7.2, which prior lesson's mechanism directly resolves this specific case?

- A. M7-L08's versioning/currency metadata (is_current) — filtering to current sources first.
- B. M6-L03's BM25 formula, applied here for the first time.
- C. M7-L07's chunking-strategy comparison.
- D. M7-L04's hard-format extraction techniques.

**Q4.** Per §7.3, why couldn't M7-L08's versioning fix resolve the conflict between Chunk A and Chunk B?

- A. Because M7-L08's versioning mechanism does not actually exist as a real technique.
- B. Because both chunks were missing their is_current field entirely.
- C. Both chunks are already marked is_current=True — there is no older, superseded version to discard, since they are two legitimately different, simultaneously valid sources.
- D. Because the two chunks were actually identical in every respect.

**Q5.** Per §7.4, what does Strategy 1 (transparent, surface both) do?

- A. It automatically deletes one of the two conflicting sources.
- B. It presents both conflicting sources and their respective claims explicitly, pushing the final decision back to the user rather than picking one.
- C. It silently picks a value at random with no explanation.
- D. It refuses to mention that any conflict exists at all.

**Q6.** Per §7.4, what does Strategy 2 (resolve by authority) require to be used safely?

- A. No requirements at all; it can be applied safely in any situation without further information.
- B. It requires the two conflicting sources to have identical text.
- C. It requires the conflict to already have been resolved by some other method first.
- D. A real, trustworthy authority signal (such as a genuine organizational hierarchy) — guessing one arbitrarily would be worse than not resolving the conflict at all.

**Q7.** Per §7.4, when is Strategy 3 (abstain and escalate) described as the safest choice?

- A. When no reliable authority signal exists and a wrong guess would be costly — the same cost asymmetry M7-L13 measured for abstention generally.
- B. Strategy 3 is described as never appropriate under any circumstances.
- C. Only when the two conflicting sources are textually identical.
- D. Only when a reliable authority signal already exists and has been applied.

**Q8.** Per §7.5, what did the shingle-based similarity check reveal about Chunk E and Chunk F?

- A. Their similarity was far too low for any dedup step to ever consider them related.
- B. They were found to be completely unrelated documents about different topics.
- C. Their similarity was high enough (above the dedup threshold) that a naive dedup step would collapse them into one, keeping only one of two disagreeing numbers.
- D. Their similarity check could not be computed due to a formatting error.

**Q9.** Per §7.5, why is it dangerous for a dedup step to rely only on textual similarity?

- A. Textual similarity checks are always completely reliable and this risk does not actually exist.
- B. Two chunks can be worded almost identically while asserting genuinely different facts (different numbers), and a wording-only similarity check cannot tell the difference — collapsing them silently discards a real disagreement.
- C. This risk only applies to chunks written in different languages.
- D. Deduplication is never affected by the specific numbers a chunk contains.

**Q10.** Per §7.5's stated fix, what should a dedup step check before collapsing near-duplicate chunks?

- A. Whether the two chunks have the same file size in bytes.
- B. Whether the two chunks were ingested on the same calendar date.
- C. Whether the two chunks share the same source URI exactly.
- D. Whether the near-duplicate chunks actually agree on the underlying facts (e.g., via number extraction or the same conflict-detection method as section 1), not just whether their wording is similar.

**Q11.** Per §7.6, why did this lab use a shingle size of k=2 instead of M7-L05's own default of k=3?

- A. M7-L05's own k-sensitivity finding — on these short sentences differing in only one word, k=3 over-penalizes the difference, obscuring genuine topical similarity.
- B. Because k=2 is required by definition for any shingling computation to function at all.
- C. Because M7-L05 never actually established a default shingle size.
- D. Because the corpus in this lesson is written in a different language than M7-L05's.

**Q12.** What is the general lesson this lab demonstrates about conflicting, duplicated, and outdated
sources?

- A. All disagreements between retrieved sources should always be resolved by simply picking the most recently retrieved one.
- B. Deduplication and conflict detection are entirely unrelated problems with no connection to each other.
- C. A system must distinguish genuine conflict (multiple current, legitimate sources disagreeing) from false conflict (stale data not properly filtered), and must check duplicate-looking sources for factual agreement, not just textual similarity, before either resolving or collapsing them.
- D. Conflicting sources should always be silently merged into a single averaged answer.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your RAG system's users start reporting that it
sometimes gives different answers to the same question. Based on this lesson, what would you check first,
and how would that shape your next steps?

---

## 12. Revision notes

- **Conflict between two sources can be detected computationally**: same topic (shingle similarity above a
  threshold) plus different asserted numbers — measured directly at 0.600 similarity with disagreeing
  values.
- **Not every apparent conflict is genuine** — two sources with different numbers on the same topic can be
  a real disagreement, or a single fact's history exposed by missing currency filtering (M7-L08). Checking
  `is_current` on both sources distinguishes the two cases.
- **Genuine conflict — both sources current, still disagreeing — cannot be resolved by versioning alone**,
  because there is no older version to discard.
- **Three resolution strategies for genuine conflict** — transparency, authority-based preference, and
  abstention — each have a real cost, and none is universally correct; authority-based resolution
  specifically requires a real, trustworthy hierarchy to exist, not an invented one.
- **Deduplication based only on textual similarity can silently discard a genuine disagreement** — measured
  directly: two near-identically worded chunks with different numbers (15 vs. 18) scored 0.636 similarity,
  above a typical dedup threshold, meaning a naive dedup step would keep only one of the two disagreeing
  facts.
- **A RAG system surfacing a real inconsistency between its sources is expected, detectable behavior**, not
  necessarily evidence of a retrieval bug — the underlying inconsistency may be a genuine, pre-existing
  problem worth escalating to source owners.

---

## 13. Completion checklist

- [ ] I can implement a computable conflict-detection check between two retrieved sources.
- [ ] I can distinguish genuine conflict from false (versioning-related) conflict.
- [ ] I can compare transparency, authority-based, and abstention-based conflict resolution strategies and
      explain when each applies.
- [ ] I check near-duplicate chunks for factual agreement before deduplication, not just textual
      similarity.
- [ ] I investigate a "different answers to the same question" report for genuine source conflict before
      assuming a retrieval bug.
- [ ] I treat a detected genuine conflict as a signal worth escalating to source owners, not only engineers.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, guidance on handling conflicting or ambiguous source material where available.
  `[UNVERIFIED]`
- Chen, H. et al., *Benchmarking Large Language Models in Retrieval-Augmented Generation* (general
  reference on conflicting-evidence handling in RAG systems). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L15 — Permission-Aware Retrieval and Tenant Isolation

You now have a way to detect and respond to disagreeing sources. Next: a different kind of source-level
concern — making sure retrieval never surfaces a document a specific user isn't actually permitted to see
in the first place.
