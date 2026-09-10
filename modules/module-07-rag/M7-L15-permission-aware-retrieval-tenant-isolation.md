# M7-L15 — Permission-Aware Retrieval and Tenant Isolation

| | |
|---|---|
| **Lesson ID** | M7-L15 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M6-L09](../module-06-embeddings-search/M6-L09-metadata-filtering.md), M2-L15 |

---

## 1. Learning objectives

1. **Implement** tenant isolation, ensuring a query from one tenant can never retrieve another tenant's
   documents.
2. **Explain** why pre-filtering versus post-filtering permissions is a security-critical distinction, not
   merely a performance trade-off, extending M6-L09's mechanics.
3. **Implement** role-based permission filtering within a single tenant.
4. **Design** a defense-in-depth second authorization check, and explain what single point of failure it
   protects against.
5. **Connect** this lesson's user-context pattern to a real dependency-injection pattern (M2-L15).

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Tenant isolation** | Guaranteeing that a query scoped to one tenant (customer, organization) can never retrieve another tenant's data. |
| **Role-based permission** | An access rule requiring a user to hold a specific role (or higher) before a document is retrievable to them. |
| **Pre-filtering (permissions)** | Restricting the candidate set to authorized documents before any scoring or ranking occurs. |
| **Post-filtering (permissions)** | Scoring and ranking the full candidate set first, then removing unauthorized documents from the results. |
| **Defense in depth** | Applying more than one independent enforcement mechanism for the same security property, so a single implementation bug cannot cause a full failure. |

---

## 3. Plain-language explanation

### 3.1 M6-L09 built filtering mechanics; this lesson applies them to security

M6-L09 covered pre-filtering, post-filtering, and filtered-ANN as retrieval-quality techniques, with the
choice between them framed mainly as a cost and recall trade-off. This lesson revisits the identical
mechanics for a case where the choice has security consequences, not just performance ones.

### 3.2 Tenant isolation is a hard requirement, not a ranking preference

§7.1 establishes the floor: two tenants' documents can be textually identical, score identically, and
still must never cross tenant boundaries in a result. This isn't about relevance at all — it's about a
document belonging to someone else entirely.

### 3.3 Where filtering happens changes what's actually at risk

§7.2 is this lesson's central argument: pre- and post-filtering can produce the *same final answer* while
having a completely different risk profile along the way. A document excluded from final results by
post-filtering was still present — scored, ranked, available to whatever else touches that intermediate
list — before it was removed.

### 3.4 Tenant boundaries aren't the only boundary that matters

§7.3 shows that even within one tenant, different users legitimately see different things — role-based
permissions are a second, independent axis of access control layered on top of tenant isolation, not
subsumed by it.

### 3.5 One enforcement point is one point of failure

§7.4 closes with a deliberately reintroduced, realistic bug — and shows a second, independent check
catching its consequence. The bug still needs fixing at its source; the second check is what stands
between that bug and an actual data leak in the meantime.

---

## 4. Analogy

**A multi-tenant office building with badge access.** Tenant isolation is the building's own separation —
Company A's floor and Company B's floor are different physical spaces, and a Company A badge simply cannot
open Company B's door, regardless of how "relevant" Company B's floor might be to whatever Company A's
employee is looking for. Role-based permission is a second layer within Company A's own floor — a general
employee badge doesn't open the HR records room, even though it's on the same floor. Pre-filtering is
checking a badge at the building's front door, before anyone reaches any floor at all. Post-filtering is
letting everyone walk every floor first, then having a guard at the end who confiscates anything they
weren't supposed to see — which means, for a moment, they were standing in the room.

### Where the analogy breaks

- **A building's badge system is usually a single, well-tested mechanism.** §7.4's bug scenario is
  specifically about custom application logic being reimplemented imperfectly — a badge reader doesn't
  typically have the equivalent of "forgot to check one of two conditions."
- **A confiscated document in the physical analogy is still just paper.** §7.2's "leak" risk (logging,
  caching, reranking) has no clean physical parallel — the danger is specifically about *where computed
  data flows* inside a software system, not about physical possession.

---

## 5. Detailed technical explanation

### 5.1 Tenant isolation, measured

`[REAL, measured]` §7.1 ran BM25 (M6-L03's exact formula) over a corpus containing two tenants' documents,
including a case where ACME's and GLOBEX's remote-work policies are worded identically and **score
identically (2.980 each)**. **Nothing about relevance distinguishes them — only tenant membership does**,
and an ACME employee's query must resolve to ACME-P1 alone, regardless of GLOBEX-P1's score.

### 5.2 Pre-filtering vs. post-filtering: a security property, not a performance choice

`[REAL, measured]` §7.2 compared both filtering orders for the same query. **Post-filtering's raw
candidate list, before the final filter ran, genuinely contained GLOBEX-P1** — confirmed directly
(`True`). **Pre-filtering never let GLOBEX-P1 enter any intermediate structure at all** — confirmed
directly (`False`). Both approaches produced the identical final answer here. **The difference is not in
the final result — it's in everything that touches the pipeline before the final result is assembled**: a
raw candidate list is exactly what gets logged for debugging, cached for reuse, handed to a reranker
(M6-L12), or fused across retrieval methods (M6-L11) — any of which can leak an excluded document's
presence or content before the intended filter ever runs. **This is why permission filtering specifically
needs pre-filtering (or an equivalent that never exposes unauthorized candidates), unlike M6-L09's generic
metadata filtering, where the pre/post choice was mainly about cost and recall.**

### 5.3 Role-based permissions, within a tenant

`[REAL, measured]` §7.3 ran the identical salary-related query as two different ACME users. **The
employee's authorized candidate set never included ACME-P2 at all** (it requires the `hr` role), so their
result was empty of relevant content. **The HR user's query correctly retrieved it.** Same tenant, same
query, genuinely different results — **tenant isolation alone does not imply correct access control within
an organization**; role-based filtering is a distinct, necessary layer.

### 5.4 Defense in depth, demonstrated with a real bug

`[REAL, measured]` §7.4 deliberately reintroduced a realistic implementation bug: a filter that checks
role correctly but **forgets to check tenant membership at all**. Run alone, this bug **genuinely leaked
GLOBEX-P1** into an ACME employee's result. A second, independent authorization check — applied to
whatever the retrieval stage produces, regardless of how — **caught and removed the leaked document before
it reached the final result.** **The bug in the retrieval stage still needs fixing** — the second check is
not a substitute for correct filtering logic, it is insurance against exactly one bug being enough to leak
data when only one enforcement point exists.

### 5.5 Assumptions and limitations

- `CurrentUser` in this lab stands in for what a real FastAPI dependency (M2-L15's `Depends()`) would
  resolve from an authenticated request — this lab simulates the resolved user context directly, not an
  actual HTTP request/response cycle or token validation.
- This lesson does not cover how a real vector database implements tenant-scoped indexes (separate
  per-tenant indexes vs. a shared index with a mandatory filter, each with real trade-offs), nor
  enforcement entirely outside the model at the infrastructure level, which is M9-L13's dedicated topic.

---

## 6. Worked example — the incident that traced back to a missing tenant clause

**The system.** A multi-tenant support-knowledge-base product retrieves and reranks candidates using a
shared index across all customers, with a permission filter applied as a post-processing step after
reranking, for implementation simplicity.

**What went wrong.** A security review found that reranking logs — retained for debugging quality issues —
contained snippets of other tenants' documents that had been scored and reranked before the final
permission filter removed them from the response. No end user ever saw another tenant's content directly,
but the raw, pre-filter candidate data had been persisted in a system with broader internal access than the
final, filtered API response.

**Why post-filtering looked safe until the review.** Per §5.2, the final answers had always been correctly
filtered — the bug wasn't in what reached the user, it was in what reached *everything else* the pipeline
touched along the way. Nothing about a correct final answer proves the intermediate stages were safe.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Permission filtering was applied only as a final post-processing step | Every intermediate stage (reranking, logging) had access to unfiltered, cross-tenant candidate data |
| 2 | Reranking logs were retained without considering their own access-control requirements | Cross-tenant content persisted in a system that hadn't been designed to hold it |
| 3 | No second, independent authorization check existed on the final API response | The single point of enforcement, had it also failed, would have leaked data directly to users |

### The fix

**Move to pre-filtering (or an equivalent that never exposes unauthorized candidates to any intermediate
stage)**, per §5.2 — this is the direct fix for the actual defect found.

**Apply the same access-control requirements to any persisted intermediate data (logs, caches) that a
post-filtering design would otherwise expose**, if pre-filtering cannot be adopted everywhere immediately.

**Add a second, independent authorization check on the final response**, per §5.4, as insurance
independent of whichever filtering approach the retrieval stage uses.

**The general rule.** **A correct final answer does not prove a permission-aware pipeline is safe — every
intermediate stage the unfiltered candidate set touches is a real surface for exposure, and pre-filtering
exists specifically to remove that surface, not just to save computation.**

---

## 7. Practical activity

**File:** [`labs/m7/l15_permission_aware_retrieval.py`](../../labs/m7/l15_permission_aware_retrieval.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l15_permission_aware_retrieval.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. TENANT ISOLATION: A QUERY MUST NEVER SEE ANOTHER TENANT'S DOCUMENTS
============================================================================
  Query: 'remote work policy', asked by u1 (tenant=acme, role=employee)

  Full BM25 ranking, IGNORING tenant/role entirely:
    ACME-P1 (tenant=acme, score=2.980): 'Remote work policy allows employees to work from home t'...
    GLOBEX-P1 (tenant=globex, score=2.980): 'Remote work policy allows employees to work from home t'...
    ACME-P2 (tenant=acme, score=0.000): 'Salary bands range from level 1 to level 8 with compens'...
    ACME-P3 (tenant=acme, score=0.000): 'The acquisition roadmap targets three companies for the'...
    GLOBEX-P2 (tenant=globex, score=0.000): 'Salary bands range from level 1 to level 6 with compens'...

  ACME-P1 and GLOBEX-P1 are near-identical policy text -- ACME's own
  employee must see ONLY ACME-P1. GLOBEX-P1 belongs to a different
  tenant entirely and must never appear, no matter how well it scores.

============================================================================
2. PRE-FILTERING VS POST-FILTERING -- WHY THIS ISN'T JUST A PERFORMANCE CHOICE HERE
============================================================================
  POST-filtering (retrieve top-2 globally, filter after):
    Raw candidate list BEFORE filtering: ['ACME-P1', 'GLOBEX-P1']
    Final result AFTER filtering: ['ACME-P1']
    GLOBEX-P1 present in the RAW candidate list at any point: True

  PRE-filtering (filter to authorized documents FIRST, retrieve top-2 from only those):
    Result: ['ACME-P1']
    GLOBEX-P1 ever scored, ranked, or present in any intermediate list: False

  Both approaches produce the SAME final answer here -- but post-
  filtering's raw candidate list genuinely CONTAINED a cross-tenant
  document, even though it was later removed. In a real system, that
  raw list is exactly what gets logged for debugging, cached for reuse,
  handed to a reranker (M6-L12), or fused across methods (M6-L11) --
  any one of which can leak the excluded document's presence, content,
  or existence before the final filter ever runs. Pre-filtering never
  lets an unauthorized document enter ANY intermediate structure at
  all. For permissions specifically, this is a security property, not
  a performance tuning choice -- unlike M6-L09's generic metadata
  filtering, where pre- vs post- was mainly a recall/cost trade-off.

============================================================================
3. ROLE-BASED PERMISSIONS WITHIN ONE TENANT
============================================================================
  Query 'salary bands compensation' as u1 (tenant=acme, role=employee): ['ACME-P1']
  Query 'salary bands compensation' as u2 (tenant=acme, role=hr): ['ACME-P2', 'ACME-P1']

  The employee sees nothing relevant -- ACME-P2 (salary bands) requires
  the 'hr' role, which this user does not have, so it never entered
  their authorized candidate set at all. The HR user, same tenant,
  correctly retrieves it. Same tenant, same query, genuinely different
  results -- role, not just tenant, has to gate what's retrievable.

============================================================================
4. DEFENSE IN DEPTH: A SECOND CHECK BEFORE RESULTS ARE EVER RETURNED
============================================================================
  Simulating a real, plausible bug: the retrieval filter checks ROLE
  but forgets to check TENANT.
  Buggy pre-filter's result for u1 (tenant=acme): ['ACME-P1', 'GLOBEX-P1']
  GLOBEX-P1 (wrong tenant) leaked through: True

  A SECOND, independent authorization check applied to whatever the
  retrieval stage returns, regardless of how it was produced:
  Final result after the second check: ['ACME-P1']
  GLOBEX-P1 present in the FINAL result: False

  The bug still exists in the retrieval stage -- it should be fixed
  there too -- but the second, independent check caught its consequence
  before anything leaked to the user. Relying on exactly one place in
  the pipeline to enforce permissions means exactly one bug is enough
  to leak data; a second, independent check is real insurance against
  that single point of failure.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: BM25 scoring is M6-L03's exact formula; every authorization,
  pre-filter, post-filter, and defense-in-depth check in this lab is
  genuinely computed against the stated tenant/role data, including
  the deliberately reintroduced bug in section 4 and its real,
  measured consequence.

  ILLUSTRATIVE: CurrentUser stands in for what a real FastAPI
  dependency (M2-L15's Depends()) would resolve from an authenticated
  request -- this lab simulates the resolved user context directly,
  not an actual HTTP request/response cycle or auth token validation.

  NOT SHOWN: how a real vector database implements tenant-scoped
  indexes (separate indexes per tenant vs. a shared index with a
  mandatory filter, each with real trade-offs); actual authentication
  and token validation; and enforcing permissions outside the model
  entirely, at the infrastructure level, which is M9-L13's dedicated
  topic.

Done.
```

### 7.3 Reading the result

**Section 1's tied score (2.980 for both) is deliberately chosen, not a coincidence to work around.** If
GLOBEX-P1 had scored lower than ACME-P1, tenant isolation's importance would be less visible — the tie
makes clear that relevance and authorization are completely independent questions.

**Section 2's "same final answer, different risk" framing is the lesson's central point, and it's worth
resisting the urge to conclude "so it doesn't matter which one you use."** The final answer being identical
is exactly what makes this dangerous to overlook — nothing about the final output reveals which
architecture produced it, or what that architecture exposed along the way.

**Section 4's bug is deliberately realistic, not contrived.** "Checks role, forgets tenant" (or the
reverse) is an easy, plausible mistake in real filter logic — precisely why the section exists to show a
second check catching it rather than assuming correct logic on the first attempt.

---

## 8. Common mistakes and troubleshooting

1. **Applying permission filtering only after retrieval and reranking.** §5.2 — this exposes unauthorized
   candidates to every intermediate stage (logs, caches, rerankers) even if the final output is correctly
   filtered.
2. **Assuming tenant isolation alone provides correct access control.** §5.3 — role-based permissions
   within a tenant are a separate, necessary layer.
3. **Relying on a single enforcement point for permission filtering.** §5.4 — one implementation bug is
   then enough to leak data with nothing to catch it.
4. **Treating a correct final answer as proof the pipeline is secure.** §6 — intermediate stages can still
   have been exposed to unauthorized data even when the final output looks fine.
5. **Not persisting logs or caches with the same access-control rigor as the final API response.** §6 —
   a system's own internal debugging data can become an unintended exposure surface.
6. **Fixing a leaked-data bug only at the point it was caught, not at its actual source.** §5.4 — a second
   check is insurance, not a substitute for fixing the underlying filtering logic.

| Symptom | Likely cause | Fix |
|---|---|---|
| A security review finds cross-tenant content in logs or caches, even though user-facing answers were correct | Permission filtering was applied only as a post-processing step | Move to pre-filtering, or apply equivalent access controls to all intermediate data (§5.2, §6) |
| Two users in the same organization see different results for the same query | This is expected if their roles differ — verify it's intentional, not a bug (§5.3) | Confirm role-based filtering is applied correctly and deliberately |
| A permission-filtering bug is found and fixed, but the team has no confidence similar bugs aren't elsewhere | Only one enforcement point existed for the fixed bug | Add a second, independent authorization check as a standing safeguard (§5.4) |
| A retrieval pipeline change (e.g. adding reranking or hybrid fusion) is suspected of introducing a permission risk | New intermediate stages may now touch an unfiltered candidate set | Confirm permission filtering happens before any new stage sees candidate data (§5.2) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Apply permission and tenant filtering before or during retrieval, never only as a final
  post-processing step, so unauthorized candidates never enter logs, caches, or reranking stages (§5.2).
- **Reliability.** Treat tenant isolation and role-based permissions as two distinct, both-necessary
  layers, not one mechanism that subsumes the other (§5.3).
- **Reliability.** Implement a second, independent authorization check on final results as defense in
  depth — never rely on exactly one enforcement point for a security-critical property (§5.4).
- **Privacy.** Apply the same access-control rigor to logs, caches, and any other persisted intermediate
  data that a post-filtering design would otherwise expose (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why must GLOBEX-P1 never appear for an ACME user, regardless of its relevance score?
2. What did the post-filtering approach's raw candidate list contain that pre-filtering's never did?
3. Why is this difference described as a security property rather than a performance trade-off?
4. Why did the employee and the HR user get different results for the identical query?
5. What did the second authorization check in §7.4 accomplish, and what did it NOT fix?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's tied scores and §7.4's leak-then-catch result on your own machine.
2. Add a third tenant and a third role level (e.g. "manager," between "employee" and "hr") and confirm
   filtering behaves correctly for a user with that role.
3. Construct a query where post-filtering's raw candidate list would contain TWO unauthorized documents
   instead of one, and confirm pre-filtering still excludes both entirely.
4. Design and implement a different realistic bug (e.g. checking tenant but forgetting role) and confirm
   the second authorization check still catches its consequence.
5. Using M6-L09's filtered-ANN concept, describe how permission pre-filtering could be combined with
   approximate nearest-neighbor search at scale, rather than exact BM25 as in this lab.

### Exercise 3 — Challenge (~50 min)

1. Implement a tenant-scoped index design (separate corpus_tokens dictionaries per tenant) instead of a
   single shared corpus with a filter, and compare its structure and guarantees to this lab's approach.
2. Design and implement a logging function that redacts or omits any candidate a user is not authorized to
   see, even when logging intermediate retrieval state for debugging.
3. Research (conceptually) how a real multi-tenant vector database product typically implements tenant
   isolation (separate indexes vs. shared index with mandatory filtering), and compare the trade-offs.
4. Extend the defense-in-depth pattern to three independent checks (e.g. tenant check, role check, and a
   final combined check) and design a test that would catch a bug in any single one of them.
5. Using this lesson's §6 worked example as a model, design a security review checklist for a
   permission-aware RAG pipeline, specifically covering intermediate data (logs, caches, reranking state).

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l15).)*

**Q1.** Per §7.1, why must GLOBEX-P1 never appear for an ACME employee's query, even though it scores
identically to ACME-P1?

- A. Because GLOBEX-P1's text is written in a different language than ACME-P1's.
- B. It belongs to a different tenant entirely — tenant isolation must hold regardless of how textually relevant a cross-tenant document is.
- C. Because GLOBEX-P1 was never actually stored in the corpus at all.
- D. Because ACME-P1 always scores higher than GLOBEX-P1 under BM25.

**Q2.** Per §7.2's measured result, what did the post-filtering approach's raw candidate list contain,
before the final filter ran?

- A. The raw candidate list was completely empty in every case.
- B. Only ACME's own documents ever appeared in the raw candidate list.
- C. The raw candidate list could not be computed due to a formatting error.
- D. GLOBEX-P1, a cross-tenant document, was genuinely present in the raw candidate list, even though it was excluded from the final result.

**Q3.** Per §7.2, why is pre-filtering described as providing a security property rather than just a
performance choice, specifically for permissions?

- A. An unauthorized document never enters any intermediate structure at all (logs, caches, rerankers, fusion steps) under pre-filtering, whereas post-filtering's raw candidate list can leak its presence or content through any of those paths before the final filter runs.
- B. Pre-filtering is always faster to compute than post-filtering in every case.
- C. Post-filtering always produces a different final answer than pre-filtering.
- D. Pre-filtering eliminates the need for any authorization check ever again.

**Q4.** Per §7.2, how does this lesson's framing of pre- vs. post-filtering differ from M6-L09's original
treatment of the same mechanics?

- A. M6-L09 never discussed pre-filtering or post-filtering at all.
- B. This lesson treats pre- vs. post-filtering as purely a performance question, identical to M6-L09's treatment.
- C. M6-L09 treated pre- vs. post-filtering mainly as a recall/cost trade-off; this lesson treats it as a security-critical distinction when the filter is enforcing permissions rather than generic metadata.
- D. M6-L09's treatment and this lesson's treatment are in direct contradiction with no reconciliation possible.

**Q5.** Per §7.3's measured result, why did the employee's salary-related query return no relevant results
while the HR user's identical query succeeded?

- A. The employee's query contained a spelling error that prevented any results.
- B. ACME-P2 requires the "hr" role, which the employee does not have, so it was excluded from their authorized candidate set before scoring ever happened; the HR user's role satisfied the requirement.
- C. The employee and the HR user belong to different tenants entirely.
- D. BM25 cannot process queries about salary information under any circumstances.

**Q6.** Per §7.3, does tenant isolation alone guarantee correct access control within an organization?

- A. Yes, tenant isolation alone is always fully sufficient for correct access control.
- B. Yes, because all users within a tenant always share identical access levels by definition.
- C. The lesson takes no position on whether role-based permissions matter within a tenant.
- D. No — role-based permissions are also required, since users within the same tenant can still have different authorized access levels.

**Q7.** Per §7.4, what specific bug was deliberately simulated in the "buggy" pre-filter?

- A. The filter checked the user's role correctly but forgot to check tenant membership at all, allowing a cross-tenant document through.
- B. The filter checked tenant membership correctly but forgot to check role entirely.
- C. The filter rejected every document regardless of tenant or role.
- D. The filter randomly selected documents with no regard to any authorization logic.

**Q8.** Per §7.4's measured result, what happened when only the buggy pre-filter ran, with no second
check?

- A. No documents were returned at all, for any user.
- B. Only correctly authorized documents were returned, with no leak of any kind.
- C. GLOBEX-P1, belonging to a different tenant, leaked through into the retrieval result.
- D. The buggy filter crashed with an unhandled exception.

**Q9.** Per §7.4, what did the second, independent authorization check accomplish?

- A. It introduced a new bug into the retrieval stage that had not existed before.
- B. It caught and removed the leaked cross-tenant document from the final result, regardless of how the retrieval stage had produced its candidate list.
- C. It had no effect on the final result at all.
- D. It re-ran the entire retrieval process from scratch using a different algorithm.

**Q10.** Per §7.4, does catching the bug's consequence with a second check mean the underlying bug in the
retrieval stage doesn't need fixing?

- A. Yes, once a second check catches the bug's consequence, the underlying retrieval-stage bug never needs to be fixed.
- B. Yes, because the second check permanently replaces the need for the first filtering stage entirely.
- C. The lesson takes no position on whether the underlying bug should still be fixed.
- D. No — the lesson states the bug should still be fixed at its source; the second check is insurance against a single point of failure, not a replacement for fixing the actual defect.

**Q11.** Per §7.5, what does `CurrentUser` stand in for in a real system, per M2-L15's connection?

- A. What a real FastAPI dependency (Depends()) would resolve from an authenticated request — this lab simulates the resolved user context directly, not an actual HTTP request/auth cycle.
- B. A real, live database connection used to store the corpus itself.
- C. The BM25 scoring function, renamed for this specific lesson.
- D. An actual HTTP server that this lab starts and runs during execution.

**Q12.** What is the general lesson this lab demonstrates about permission-aware retrieval?

- A. Permission filtering should always happen after retrieval and generation are both complete, never before.
- B. A single enforcement point is always sufficient for permission-aware retrieval, provided it is implemented correctly once.
- C. Permission and tenant filtering must be enforced before or during retrieval (not only after), and relying on a single enforcement point is risky — a second, independent check provides real protection against an implementation bug in the first one.
- D. Tenant isolation and role-based permissions are the same mechanism and require no separate handling.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a teammate proposes implementing permission
filtering as a final step, right before returning results to the user, for simplicity. Based on this
lesson, what would you point out, and what would you propose instead?

---

## 12. Revision notes

- **Tenant isolation must hold regardless of relevance** — measured directly: two tenants' identically
  worded, identically scored documents still require strict separation, since authorization and relevance
  are independent questions.
- **Pre-filtering and post-filtering can produce the same final answer while having very different risk
  profiles** — measured directly: post-filtering's raw candidate list genuinely contained a cross-tenant
  document; pre-filtering's never did, at any point.
- **For permissions specifically (unlike M6-L09's generic metadata filtering), pre- vs. post-filtering is a
  security-critical distinction** — an unfiltered candidate list is a real exposure surface for logs,
  caches, reranking, and fusion, not just a performance question.
- **Role-based permissions are a distinct, necessary layer on top of tenant isolation** — measured
  directly: two users in the same tenant received genuinely different results for the identical query,
  based on role alone.
- **A single enforcement point is a single point of failure** — measured directly: a realistic,
  deliberately reintroduced bug (checking role, forgetting tenant) leaked a cross-tenant document, and a
  second, independent check caught it before it reached the final result.
- **A second check is insurance, not a substitute for fixing the underlying bug** — the retrieval-stage
  defect still needs a real fix; defense in depth buys protection while that fix is made, not permission
  to skip it.

---

## 13. Completion checklist

- [ ] I can implement tenant isolation that holds regardless of document relevance.
- [ ] I can explain why pre-filtering is a security requirement, not just a performance choice, for
      permission enforcement.
- [ ] I can implement role-based permission filtering within a single tenant.
- [ ] I can design a defense-in-depth second authorization check and explain what it protects against.
- [ ] I apply the same access-control rigor to intermediate data (logs, caches) as to final results.
- [ ] I connect this lesson's user-context pattern to a real dependency-injection pattern (M2-L15).
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- OWASP, *Access Control Cheat Sheet* (general reference on authorization design principles).
  `[UNVERIFIED]`
- FastAPI documentation, *Dependencies* (M2-L15's `Depends()` pattern this lesson's `CurrentUser`
  parallels). <https://fastapi.tiangolo.com/tutorial/dependencies/> `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L16 — Incremental Updates and Deletion Propagation

You now have permission-aware retrieval that never exposes unauthorized content. Next: what happens when a
document is deleted or a user's access is revoked — making sure that change actually propagates through the
entire index, not just the source document.
