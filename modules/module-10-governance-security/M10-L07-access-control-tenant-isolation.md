# M10-L07 — Access Control and Tenant Isolation as Governance Controls

| | |
|---|---|
| **Lesson ID** | M10-L07 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L15](../module-07-rag/M7-L15-permission-aware-retrieval-tenant-isolation.md), [M9-L13](../module-09-mcp/M9-L13-permission-enforcement-outside-model.md) |

---

## 1. Learning objectives

1. **Identify** every place an authorization context must appear — including caches and prompt caches.
2. **Choose** between pre-filtering and post-filtering in retrieval, judging both leaks and false denials.
3. **Enforce** access at the data layer rather than per handler, and explain why that survives future code.
4. **Govern** break-glass access: scope, logging, visibility and expiry.
5. **Evidence** each isolation control with an automated test, and feed that into the risk register.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Tenant** | A customer or organisation whose data must never mix with another's. |
| **Authorization context** | The identity, tenant and scopes a request acts under. |
| **Pre-filter** | Applying the tenant predicate *inside* the search, so only permitted candidates are ranked. |
| **Post-filter** | Ranking globally, then discarding results the caller may not see. |
| **Data-layer enforcement** | One accessor that applies the predicate for every query, rather than a check per handler. |
| **Break-glass** | Deliberate elevated access for support or incident work. |
| **Isolation test** | An automated test proving one tenant cannot reach another's data by any route. |

---

## 3. Plain-language explanation

### 3.1 Isolation fails in the plumbing, not the policy

Everyone agrees tenants must be separated. §7.1 shows how that agreement fails: a response cache keyed on the **question
text alone** served **80 answers to the wrong tenant** out of 300 requests. Adding the tenant to the key: **0**. Nothing
in the retrieval logic changed — the leak lived in a dictionary key.

### 3.2 Filters can leak, or can quietly deny

§7.2 runs three retrieval designs. With **no filter**, 200 of 300 returned documents belonged to another tenant. With
**post-filtering**, 0 leaked — but **20 of 60 queries returned nothing**, because the tenant's own documents never made
the global top five. With **pre-filtering** inside the index: 0 leaks, 0 empty results.

Post-filtering is the design that passes a security review and fails users, which is why it survives so long: the failure
looks like "the assistant isn't very good".

### 3.3 Where the check lives decides whether it survives

§7.3 compares checks written in each handler with one enforced data accessor. Both are correct for the two endpoints that
existed at design time. A `bulk_export` endpoint added later has no check in the first design: **180 cross-tenant records
returned**. In the second: **0**, because the accessor applies the predicate and the new endpoint could not have
forgotten it.

### 3.4 Break-glass is normal; unlogged break-glass is not

§7.4 compares four support-access designs. Unscoped, unlogged admin access reaches **all 90 records** with no record that
it happened. Scoping to the tenant on the ticket, logging, making the access visible to the customer and time-boxing it
reduces reach to **30** and leaves evidence.

### 3.5 A control is a control when it has a test

§7.5 lists six isolation controls: **3** have CI tests, **1** is a manual monthly review, **2** have no evidence at all —
including "vector search pre-filters by tenant", the control §7.2 just showed to matter most.

---

## 4. Analogy

**A shared office building.** The policy — "each company's floor is private" — is not in dispute. The failures are
mundane: a lift that remembers the last floor pressed (the cache), a cleaner's master key with no sign-out sheet
(break-glass), a new goods entrance built after the access-control review (the late endpoint), and a directory in the
lobby that lists everyone's staff (the unfiltered index).

### Where the analogy breaks

- **Buildings have doors you can see; a cache key is invisible until someone measures it.** That is why §7.5's evidence
  column matters: you cannot walk the floor and check.
- **A cleaner's key opens rooms one at a time; a bulk export opens all of them at once.** Scale changes the risk
  qualitatively, which is why §7.3's late endpoint is the dangerous one.

---

## 5. Detailed technical explanation

### 5.1 Carry the authorization context everywhere

The tenant (or user, or scope set) must appear in:

| Place | What goes wrong without it |
|---|---|
| The query filter | Cross-tenant retrieval (§5.2) |
| **Every cache key** — answers, embeddings, retrieval results, prompt caches | §7.1's 80 wrong answers |
| Rate limits and quotas | One tenant exhausting another's budget |
| Logs and traces | Cannot investigate, or investigating exposes the wrong tenant's content |
| Evaluation and debug tooling | Test harnesses that read all tenants become an exposure path |
| Background jobs | Reindexing, summarising, digesting — running as "system" with no tenant |

M9-L06's `cacheScope` makes the same point at protocol level: anything caller-specific is `private`, and shared caches
must key by authorization context.

### 5.2 Pre-filter, not post-filter

`[REAL, measured]` §7.2, 60 queries across three tenants, K = 5:

| Design | Returned | Other tenants' documents | Empty result sets |
|---|---|---|---|
| No filter | 300 | **200** | 0 |
| Post-filter | 100 | 0 | **20/60** |
| Pre-filter | 300 | 0 | 0 |

Post-filtering gets worse as tenants grow: the more documents the other tenants hold, the less of any tenant's own corpus
reaches the top K. In vector indexes this is the filtered-ANN problem from M6-L09 — pre-filtering needs index support
(metadata filters, per-tenant namespaces or separate indexes), and that requirement belongs in the design, not in a
post-processing step.

**Namespace or shared index?** Per-tenant namespaces make isolation structural and simplify deletion (L06), at the cost
of more indexes to manage. A shared index with metadata filters is cheaper but puts the whole burden on a predicate that
must never be omitted — which is §5.3's argument.

### 5.3 Enforce at the data layer

`[REAL, measured]` §7.3: 180 cross-tenant records via a later endpoint with per-handler checks; 0 with one enforced
accessor.

Patterns that make omission impossible rather than unlikely:

- **A single accessor** that takes the authorization context as a required argument — no context, no query.
- **Row-level security in the database**, so even ad-hoc queries are constrained.
- **Per-tenant credentials or namespaces**, so the wrong data is not reachable by the connection at all.
- **Type-level enforcement**: a `TenantScopedSession` that cannot be constructed without a tenant.

The MCP equivalent from M9-L13 is the same rule: deny by default, centrally, so a new tool added later is unusable until
someone decides who may call it.

### 5.4 Break-glass access

`[REAL, measured]` §7.4: unscoped and unlogged reaches 90 records with no evidence; scoped to the ticket's tenant reaches
30, logged and visible.

Design rules:

1. **Scope it** to the tenant, the records and the task at hand.
2. **Require a reason** captured at use — a ticket reference, not a free-text box nobody reads.
3. **Log it immutably** (L13's hash-chained log) with who, what, when and why.
4. **Time-box it** — access that expires beats access someone must remember to revoke.
5. **Review the log with someone else**, and tell the customer where that is the agreement.
6. **Count it**: break-glass frequency is a health metric. Rising use means the normal path is inadequate.

### 5.5 Evidence and the register

`[REAL, measured]` §7.5: 3 automated, 1 manual, 2 with no evidence.

Every isolation control needs a test that a future change will break:

- **Data layer:** a test that asserts a query without a tenant context raises, and that a cross-tenant id returns nothing.
- **Cache:** a test that asserts the key includes the context (and a test that two tenants asking the same question get
  different answers).
- **Retrieval:** a test that a tenant with few documents still gets its own top results when other tenants have many —
  which catches post-filtering.
- **Endpoints:** a parametrised test that every route rejects a cross-tenant id (add the route list to the test, not the
  test to each route).
- **Break-glass:** a test that admin access without a reason is refused, and that use is logged.

These test ids are the evidence column in the risk register (L04) and the control list in a system card (L15).

### 5.6 Assumptions and limitations

- Three tenants and 120 documents; the mechanisms are real, the scale is not.
- Encryption per tenant, identity federation and policy engines (ABAC) are alternative implementations of the same rule,
  not covered here.
- Isolation of *models* — fine-tuning on one tenant's data, or a shared prompt cache at a provider — is a related question
  handled in M13.

---

## 6. Worked example — the empty search results that hid a leak

**The situation.** A B2B analytics product added a RAG assistant over customer documents, with a shared vector index and
tenant metadata on each chunk. The team applied a post-filter after retrieval. A security review approved the design; an
isolation test confirmed no cross-tenant document had ever been returned.

**Two symptoms, months apart.**

1. Small customers complained the assistant "doesn't know anything about our documents". Their corpora were a few hundred
   chunks against one customer's several million, so almost nothing of theirs entered the global top 50 — §7.2's 20/60
   empty results, at production scale.
2. When the team added a "related documents" side panel, it used the same retrieval call but rendered results **before**
   the post-filter ran. Three customers saw other customers' document titles.

**Analysis.**

1. Post-filtering was **safe only where it was applied**, and a new caller bypassed it — the §7.3 pattern: correctness
   living in the caller rather than the accessor.
2. The isolation test only covered the original endpoint, so it proved nothing about the panel (§5.5).
3. The quality complaints and the leak had the **same root cause**, and the quality complaints arrived first — which is
   the useful signal to remember.

| # | Fix | Where |
|---|---|---|
| 1 | Pre-filter inside the index; per-tenant namespaces for the largest customers | §5.2 |
| 2 | One retrieval accessor requiring the authorization context; panel uses it | §5.3 |
| 3 | Isolation tests parametrised over every route, including new ones | §5.5 |
| 4 | Recall check per tenant size, so "small tenant, no results" fails the build | §5.2, M6-L13 |

**The general rule.** **If your isolation design degrades quality, it is also fragile.** The design that makes the wrong
data unreachable usually makes the right data more reachable too.

---

## 7. Practical activity

**File:** [`labs/m10/l07_access_control_isolation.py`](../../labs/m10/l07_access_control_isolation.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l07_access_control_isolation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. CACHE KEYS: THE CHEAPEST WAY TO LEAK ACROSS TENANTS
============================================================================
  key = question               cache hits: 117   answers served to the WRONG tenant:  80
  key = (tenant, question)     cache hits: 111   answers served to the WRONG tenant:   0

  The leak is not in the retrieval code at all: it is one missing component
  of a cache key. Every cache, memo and prompt-cache in the path needs the
  tenant (or the authorization context) in its key (M9-L06's cacheScope).

============================================================================
2. RETRIEVAL FILTERS: PRE-FILTER, POST-FILTER, OR NONE
============================================================================
  none         results returned:  300   other tenants' documents:  200   empty result sets:   0/60
  post-filter  results returned:  100   other tenants' documents:    0   empty result sets:  20/60
  pre-filter   results returned:  300   other tenants' documents:    0   empty result sets:   0/60

  Post-filtering is safe but lossy: the tenant's own documents never reach the
  top K, so correct queries return nothing (M6-L09). Pre-filtering inside the
  index is both safe and useful -- and it is the only one that scales as one
  tenant's corpus grows.

============================================================================
3. WHERE THE CHECK LIVES: API LAYER VS DATA LAYER
============================================================================
  checks in each handler       other tenants' records returned across 3 endpoints x 3 tenants: 180
  one enforced data accessor   other tenants' records returned across 3 endpoints x 3 tenants: 0

  Nothing changed about the policy -- only where it is enforced. A handler
  written six months later cannot forget a check it never had to write.

============================================================================
4. BREAK-GLASS ADMIN ACCESS
============================================================================
  support admin can read any tenant, no record             reachable records:  90  logged: False visible to customer: False
  support admin, logged                                    reachable records:  90  logged: True  visible to customer: False
  support admin, logged + customer-visible + time-boxed    reachable records:  90  logged: True  visible to customer: True
  support admin scoped to one tenant on ticket             reachable records:  30  logged: True  visible to customer: True

  Break-glass access is legitimate; unlogged, unbounded break-glass is not a
  control, it is a second system with no governance. Scope it, log it, expire it,
  and review the log with someone other than the person who used it.

============================================================================
5. EVIDENCE: WHICH CONTROLS HAVE A TEST BEHIND THEM?
============================================================================
  [CI  ] Tenant predicate applied in the data accessor    test_isolation_data_layer (CI, every commit)
  [CI  ] Cache keys include the tenant                    test_cache_key_contains_tenant (CI, every commit)
  [NONE] Vector search pre-filters by tenant              -
  [CI  ] Bulk export requires tenant scope                test_bulk_export_scoped (CI, added after incident)
  [manual] Admin access is logged and reviewed              monthly access review (manual, last done 2026-06)
  [NONE] Embeddings are stored per tenant namespace       -

  automated: 3/6   manual: 1   no evidence: 2
  In a governance review, the first three columns of the risk register come
  from this table: control, evidence, last verified (M10-L04).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every leak count, empty-result count, exposure count and evidence
  tally above is computed by running these implementations.

  ILLUSTRATIVE: three tenants, 120 documents and a scoring function standing in
  for a real index; the endpoints are functions rather than a service.

  NOT SHOWN: identity federation, attribute-based policy engines, row-level
  security in databases, and encryption per tenant -- all of which are ways to
  implement the same rule closer to the data.

Done.
```

### 7.3 Reading the result

**Section 1 is the cheapest lesson here**: 80 wrong-tenant answers from one missing key component.

**Section 2's third column is the one teams miss.** Post-filtering's 20 empty result sets are a product failure that
nobody attributes to the isolation design.

**Section 5 is what a reviewer should ask for.** Not "do you isolate tenants?" but "which test proves it, and when did it
last run?"

---

## 8. Common mistakes and troubleshooting

1. **Caches keyed without the authorization context.** §5.1 — including prompt and embedding caches.
2. **Post-filtering after retrieval.** §5.2 — safe, lossy, and bypassable by the next caller.
3. **Per-handler checks.** §5.3 — the endpoint added next year is the one that leaks.
4. **Background jobs running as "system".** §5.1.
5. **Unscoped or unlogged break-glass access.** §5.4.
6. **Isolation tests covering one route.** §5.5, §6.
7. **Treating a security sign-off as evidence.** §5.5 — evidence is a test with a date.

| Symptom | Likely cause | Fix |
|---|---|---|
| A tenant sees another's answer | Cache key missing tenant | Add context to every cache key; test it |
| Small tenants get poor or empty results | Post-filtering | Pre-filter in the index or use namespaces |
| A new endpoint leaks | Checks in handlers | One enforced accessor; parametrised route tests |
| Cannot answer "who accessed this customer's data?" | Break-glass unlogged | Immutable, reviewed access log |
| Reviewers keep asking the same questions | Controls with no evidence | Name the test and its last run (L04, L15) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Isolation is the control that bounds every other AI failure in a multi-tenant system: an injection that
  reaches a tool still cannot reach another tenant's data if the accessor requires the context (M9-L13).
- **Privacy.** Cross-tenant leaks are reportable incidents in most regimes; the cache-key variant is both the most common
  and the easiest to prevent.
- **Reliability.** Pre-filtering keeps quality stable as tenants grow; post-filtering degrades silently.
- **Cost.** Per-tenant namespaces cost more to operate; the trade-off is a design decision to record with its rationale
  (L04).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List five places the tenant must appear besides the query filter.
2. Why did post-filtering produce empty result sets?
3. Why did the late `bulk_export` endpoint leak under per-handler checks?
4. What four properties should break-glass access have?
5. Which two controls in §7.5 have no evidence, and why does that matter?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Make one tenant ten times larger and re-run section 2; how do the empty result sets change?
2. Add a "related documents" endpoint to section 3 that forgets the check, and show both designs' results.
3. Implement a cache-key test that fails if the tenant is missing, and prove it fails on the broken design.
4. Add an "admin used break-glass N times this month" metric and decide a threshold that should trigger review.
5. Write the isolation test list for a system you work on, with the route list parametrised.

### Exercise 3 — Challenge (~60 min)

1. Implement pre-filtering in a real vector store (M6-L08/L09) with per-tenant namespaces, and measure recall for a small
   tenant before and after.
2. Add row-level security in PostgreSQL for the records table and show that an ad-hoc query cannot bypass it.
3. Design the break-glass workflow end to end: request, approval, scope, expiry, logging, review, customer notification.
4. Build a "leak canary": a synthetic document per tenant that must never appear in another tenant's results, checked in
   production continuously.
5. Write the evidence table for a system card (L15): control, mechanism, test, last verified, owner.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l07).)*

**Q1.** In §7.1, what caused answers to be served to the wrong tenant?

- A. The retrieval filter was disabled
- B. Two tenants shared an index namespace
- C. The model memorised earlier answers
- D. The cache key omitted the tenant

**Q2.** How many wrong-tenant answers did the question-only cache key produce?

- A. 0 of 300 requests
- B. 80 of 300 requests
- C. 117 of 300 requests
- D. 300 of 300 requests

**Q3.** What is the cost of post-filtering, per §7.2?

- A. Correct queries return nothing
- B. Other tenants' documents leak
- C. Latency rises with corpus size
- D. Embeddings must be recomputed

**Q4.** Which retrieval design leaked nothing and denied nothing?

- A. No filter, with a trusted model
- B. Post-filter with a larger K
- C. Pre-filter inside the index
- D. Post-filter plus a cache

**Q5.** Why did the `bulk_export` endpoint leak under per-handler checks?

- A. It was written after the checks were designed
- B. It used a different database connection
- C. It ran as a background job
- D. It bypassed the cache

**Q6.** What makes data-layer enforcement more durable?

- A. It is faster than checking in handlers
- B. It removes the need for authentication
- C. It allows admin access to be logged
- D. A new caller cannot omit a check it never writes

**Q7.** Which property is missing from "support admin can read any tenant, no record"?

- A. Scope only
- B. Logging and scope
- C. Encryption at rest
- D. Multi-factor authentication

**Q8.** What should rising break-glass usage indicate?

- A. That the log is being tampered with
- B. That tenants are growing
- C. That the normal path is inadequate
- D. That access has expired correctly

**Q9.** In §7.5, how many isolation controls had automated tests?

- A. 6 of 6 controls
- B. 1 of 6 controls
- C. 0 of 6 controls
- D. 3 of 6 controls

**Q10.** Which test would catch a post-filtering design?

- A. A small tenant still gets its own top results
- B. A cross-tenant id returns nothing
- C. A query without a context raises an error
- D. Admin access without a reason is refused

**Q11.** In §6, which symptom appeared first?

- A. Titles from other customers in a side panel
- B. A failed isolation test in CI
- C. Small customers getting no useful results
- D. A regulator's enquiry about a breach

**Q12.** What does M9-L06's `cacheScope` contribute to this lesson?

- A. It encrypts cached answers per tenant
- B. Caller-specific results must not be shared across authorization contexts
- C. It sets how long a cached answer stays fresh
- D. It requires per-tenant vector namespaces

**Q13.** *(Written, rubric-graded.)* In under 150 words: a reviewer asks "how do you know tenants are isolated?" Answer
with the specific mechanisms and the evidence you would show.

---

## 12. Revision notes

- **Context everywhere:** filters, **every cache key**, quotas, logs, background jobs, test tooling. Measured: 80
  wrong-tenant answers from a question-only cache key; 0 once keyed by tenant.
- **Pre-filter** (0 leaks, 0 empty) beats **post-filter** (0 leaks, **20/60 empty**) and no filter (**200 leaked
  documents**).
- **Data-layer enforcement**: a late endpoint leaked **180** records under per-handler checks, **0** with one accessor.
- **Break-glass:** scope, reason, immutable log, expiry, independent review, and a usage metric.
- **Evidence:** 3 of 6 controls had CI tests; a control without a test is not a control (L01, L04).

---

## 13. Completion checklist

- [ ] The authorization context is in every filter, cache key, quota and job.
- [ ] Retrieval pre-filters, and I measure small-tenant recall.
- [ ] Access is enforced by one accessor, not per handler.
- [ ] Break-glass is scoped, logged, time-boxed and reviewed.
- [ ] Every isolation control names a test and its last run.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M7-L15 (permission-aware retrieval and tenant isolation) and M6-L09 (filtered ANN) — the retrieval mechanisms `[STABLE]`
- M9-L06 (`cacheScope`) and M9-L13 (deny by default, centrally) — the same rules at protocol level `[STABLE]`
- OWASP API Security Top 10: Broken Object Level Authorization — the general form of the leak `[STABLE]`
- M10-L13 — immutable, hash-chained logs for break-glass evidence `[STABLE]`

---

## 15. Next lesson

→ [M10-L08 — Bias and Subgroup Evaluation](M10-L08-bias-subgroup-evaluation.md) moves from who may see what to whether the
system works equally well for everyone it is used on.
