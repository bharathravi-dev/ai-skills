# M5-L16 — Caching and Model Routing

| | |
|---|---|
| **Lesson ID** | M5-L16 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M5-L15](M5-L15-token-accounting.md) |

---

## 1. Learning objectives

1. **Distinguish** a response cache from M5-L15's prompt/prefix cache, and compare exact-match against
   semantic hit rates and their respective risks.
2. **Explain** why a semantic cache's higher hit rate comes with a defect a wrong-hit an exact-match
   cache cannot produce.
3. **Compute** the classifier accuracy above which a model router saves money, and below which it costs
   more than never routing at all.
4. **Order** a cache-then-route pipeline correctly, and state what the wrong order wastes.
5. **Decide**, for a given system, whether building a router is justified by a measured number rather
   than an assumption.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Response cache** | Caching a complete model response, keyed by the request, to skip the model call entirely on a hit. |
| **Exact-match cache** | A response cache that hits only on a byte-identical (or normalised-identical) request. |
| **Semantic cache** | A response cache that hits on requests judged similar enough by some similarity measure, not identical. |
| **Wrong hit** | A cache hit that returns an incorrect answer for the specific request that triggered it. |
| **Model router** | A component that decides which model handles a request before it is sent. |
| **Routing classifier** | The heuristic or model that makes the routing decision. |
| **Misroute** | A request sent to a model unsuited to it — overpaying (easy→expensive) or needing a fallback (hard→cheap). |
| **Break-even accuracy** | The classifier accuracy above which routing costs less than never routing at all. |
| **Fallback re-ask** | Sending a request to a stronger model after a cheaper one's answer fails. |

---

## 3. Plain-language explanation

### 3.1 Two different things people call "caching"

M5-L15 covered **prompt caching** — a discount on a stable *prefix* that still gets sent, still gets
processed, just at a lower price. This lesson covers **response caching** — skipping the model call
**entirely** when a matching request has already been answered. Different mechanism, different economics,
and a failure mode prompt caching cannot have.

### 3.2 A response cache can be wrong, not just miss

An exact-match cache is safe in a specific sense: every hit is provably the answer to the *identical*
question. A **semantic** cache trades that guarantee for a much higher hit rate — it serves a cached
answer when a new request is judged *similar enough*, not identical. §7.1 measures both the gain and the
cost: more hits, and some of those hits are **silently wrong**.

### 3.3 Routing is a bet, and the bet has a break-even point

Sending easy requests to a cheap model and hard ones to an expensive model sounds like free money. It
is — **if your classifier is good enough.** A request routed to the wrong model does not fail for free:
an easy request sent to the expensive model just overpays, but a hard request sent to the cheap model
usually needs a **second, expensive call** to fix it — meaning that request now pays for both attempts.
§7.2 computes exactly where that arithmetic flips from savings to loss.

### 3.4 Pipeline order is a cost decision too

If your routing classifier runs on every request before you ever check the cache, you pay for
classification on requests that were about to be served for free. §7.3 prices the fix, which is a
one-line reordering, not a better classifier.

---

## 4. Analogy

**A pharmacy that keeps pre-filled prescriptions on a shelf.** For a customer requesting the *exact* same
medication, dose and quantity as one already filled, handing over the shelved one is safe — it is
provably identical. A pharmacy that instead hands out a "close enough" prescription to anyone whose
request merely sounds similar is faster on average, but occasionally hands someone the wrong dose with
complete confidence, because "sounds similar" and "is the same" are different claims.

The same pharmacy also has a junior staff member **triaging** which customers a pharmacist must see
personally versus which can be handled by a technician. A triage call that is right often enough saves
the pharmacist's time. A triage call that sends complex cases to the technician means those cases come
back to the pharmacist anyway — now having cost the technician's time *and* the pharmacist's, which is
worse than sending everyone to the pharmacist in the first place.

### Where the analogy breaks

- **A pharmacist can visually double-check a shelved prescription before handing it over.** A semantic
  cache's wrong hits are not flagged for review — that is precisely why they are dangerous (§5.1).
- **A pharmacy's triage error rate is usually visible in complaints.** A misrouted LLM request can look
  identical to a correctly routed one in your logs unless you specifically track routing outcomes.
- **A pharmacy has one triage step, once.** A real system may check a cache, route, and cache again
  downstream — ordering compounds, and §5.3's fix is about getting that order right the first time.

---

## 5. Detailed technical explanation

### 5.1 Exact-match vs semantic: hit rate against defect rate

`[REAL arithmetic, ILLUSTRATIVE traffic mix]` §7.1 modelled 1,000 queries: 15% literal duplicates, 25%
paraphrases of a prior query, 60% genuinely novel:

| Cache type | Hit rate | Model calls avoided | Silently wrong answers |
|---|---|---|---|
| Exact-match | 15% | 150 | **0** |
| Semantic | 40% | 400 | **50** |

**Semantic caching avoided 250 more model calls — real savings.** But 50 of those served answers were
wrong for the specific query that triggered them, with nothing distinguishing a wrong hit from a correct
one in the response itself. **A wrong hit is worse than a miss**: a miss falls through to a normal model
call that is presumably right; a wrong hit delivers an incorrect answer with the apparent confidence of a
cache. This is the same recall/precision shape M3-L14 taught applied to caching — a higher hit rate is not
a free upgrade if some of the additional hits are wrong.

### 5.2 The break-even accuracy for a router

`[REAL arithmetic, ILLUSTRATIVE prices and mix]` §7.2 modelled 1,000 requests, half easy and half hard,
routed between a cheap model (4× cheaper, uniformly) and an expensive one:

| Classifier accuracy | Routed total cost | vs always-expensive |
|---|---|---|
| 95% | $0.8603 | −11.8% (cheaper) |
| 70% | $0.9431 | −3.3% (cheaper) |
| 65% | $0.9597 | −1.6% (cheaper) |
| **60%** | $0.9762 | **+0.1% (more expensive)** |
| 40% | $1.0425 | +6.9% (more expensive) |

**The exact crossover, solved rather than read off the table: 60.4%.** Below that accuracy, routing costs
more in total than simply always calling the expensive model — because a misrouted hard request pays for
**both** the failed cheap attempt and the expensive fallback that fixes it, while a misrouted easy request
only overpays. **A router earns its keep only above a computable bar, not merely by being "better than
guessing."**

### 5.3 Check the cache before you spend on routing

`[REAL arithmetic]` §7.3 priced running a routing classifier on every request versus only on cache
misses, at 100,000 requests/month and a 40% cache hit rate (§5.1's semantic cache):

| Order | Monthly classification spend |
|---|---|
| Route first, check cache after | $4.00 |
| **Cache first, route only on a miss** | **$2.40** |

**$1.60/month wasted from ordering alone**, on top of whatever the classifier saves or costs at the model
layer (§5.2). The fix is a one-line pipeline reorder: **check the cache before spending anything on a
routing decision** — a cache hit needed no routing decision at all.

### 5.4 What this lesson does not cover

Building the semantic-similarity mechanism itself (embeddings, similarity thresholds) is an M6 topic.
Production-grade fallback chains across more than two models, retry budgets specific to routing, and SLA-
driven routing policy belong to **M13-L08**, which builds directly on this lesson's economics.

### 5.5 Assumptions and limitations

- §7.1's traffic mix and wrong-hit rate are stated parameters, not measured from a real semantic cache.
  Measure your own duplicate/paraphrase rates and your own similarity threshold's error rate before
  relying on these figures.
- §7.2's prices, traffic mix and the resulting 60.4% break-even are specific to the stated inputs.
  Recompute for your own cheap/expensive prices and your own easy/hard traffic split — the *method*
  (solve for the crossover) transfers; the number does not.
- "Always cheap" was cheaper in dollar terms than every routed strategy in §7.2, but the lesson does not
  recommend it — hard requests answered by a cheap model carry a real quality risk that a token-cost
  table cannot capture on its own. Quality must be measured separately (M3-L14, M5-L18).

---

## 6. Worked example — the router that made the bill worse

**The system.** A team adds a router in front of two models: a cheap one for simple lookups, an
expensive one for complex reasoning. A lightweight heuristic classifier — prompt length and a handful of
keywords — decides which model handles each request. Nobody measures the classifier's actual accuracy
before shipping it; the team's reasoning is "even a rough classifier should save money versus always
using the expensive model."

**What shipped.** The heuristic turns out to be right about 55% of the time — barely better than a coin
flip on genuinely ambiguous requests, which turn out to be common. Per §5.2's exact arithmetic, **55% sits
below the 60.4% break-even point** for this system's prices and traffic mix.

**What the team saw on the next invoice.** Total spend was *higher* than the prior always-expensive
baseline, not lower. The reason traces directly to §5.2's mechanism: every hard request the heuristic
misrouted to the cheap model failed validation, triggered a fallback re-ask on the expensive model, and
so paid for **both** calls. At 45% of hard requests misrouted, that surcharge outweighed the genuine
savings on correctly-routed easy requests.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No accuracy measurement before shipping the router | The team could not know they were below break-even until the invoice arrived |
| 2 | No break-even calculation for their own prices and traffic mix | "Should save money" was an assumption, not a computed claim |
| 3 | No monitoring of misroute/fallback rate in production | The mechanism causing the overspend was invisible until someone went looking |

### The fix

**Measure classifier accuracy on a held-out set before shipping**, the same discipline M5-L12 applies to
prompt changes generally.

**Compute the break-even accuracy for your own prices and traffic mix** (§5.2's closed form) before
building or keeping a router — it is a few lines of arithmetic, not a guess.

**Monitor misroute and fallback rate in production**, not just total spend, so a router that drifts below
its break-even point is caught by a metric, not an invoice.

**The general rule.** **A router is a bet with a computable break-even point. Build one only after
checking which side of that point your classifier actually lands on — and keep checking, because
accuracy drifts as traffic does.**

---

## 7. Practical activity

**File:** [`labs/m5/l16_caching_routing.py`](../../labs/m5/l16_caching_routing.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l16_caching_routing.py
```

Pure Python, no dependencies. Every number is exact arithmetic on stated inputs — no embedding
similarity, classifier, or model call is actually run anywhere in this lab.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11.

```text
============================================================================
1. EXACT-MATCH VS SEMANTIC CACHING: HIT RATE VS SILENT WRONG ANSWERS
============================================================================
  1,000 queries: 15% literal duplicates, 25% paraphrases of a prior query, 60% genuinely novel.

  cache type        hit rate   hits avoided (model calls)   silently WRONG answers
  exact-match            15%                          150                        0
  semantic               40%                          400                       50

  Semantic caching serves 250 more queries
  from cache than exact-match -- real cost and latency saved. But
  50 of those served queries get an answer that is
  actually wrong for what THIS query asked, silently, because
  'similar enough to hit the cache' is not the same claim as
  'identical enough to share an answer'. An exact-match cache cannot
  produce this failure at all -- its hit rate is lower, but every hit
  is provably the right answer to the exact same question.

  This is the same shape as any recall/precision trade M3-L14
  taught: a higher hit rate is not a free upgrade if some of the
  extra hits are wrong, and a WRONG cache hit is worse than a MISS
  -- a miss just costs a normal model call; a wrong hit costs an
  incorrect answer delivered with the confidence of a cache.

============================================================================
2. ROUTING ECONOMICS: WHEN A BAD CLASSIFIER COSTS MORE THAN NO ROUTING
============================================================================
  1,000 requests: 50% easy (300in/100out tok), 50% hard (800in/600out tok).
  Cheap model: $0.12/M in, $0.50/M out. Expensive: $0.50/M in, $2.00/M out.

  Always expensive: $0.9750 total (500 hard requests handled at full quality)
  Always cheap:     $0.2437 total (500 hard requests get a cheap-model answer of unknown quality -- not $-quantifiable, a real risk, not modelled here)

   classifier accuracy   routed total cost     vs always-expensive
                   95%             $0.8603        -11.8% (cheaper)
                   90%             $0.8769        -10.1% (cheaper)
                   80%             $0.9100         -6.7% (cheaper)
                   70%             $0.9431         -3.3% (cheaper)
                   65%             $0.9597         -1.6% (cheaper)
                   60%             $0.9762  +0.1% (MORE EXPENSIVE)
                   50%             $1.0094  +3.5% (MORE EXPENSIVE)
                   40%             $1.0425  +6.9% (MORE EXPENSIVE)

  Exact crossover (solved, not read off the table): routing beats always-expensive only above 60.4% classifier accuracy.

  At 95%-90% accuracy, routing clearly saves money against always
  using the expensive model. Read down the table: the saving shrinks
  and then REVERSES. Below roughly the crossover point, misrouted
  hard requests -- which pay for BOTH the cheap attempt that failed
  AND the expensive fallback that fixed it -- cost enough that
  routing is now WORSE than never routing at all. A router is only
  worth building if its accuracy clears this bar, and the bar is
  computable, not a guess.

============================================================================
3. PIPELINE ORDER: CHECK THE CACHE BEFORE YOU SPEND ON ROUTING
============================================================================
  100,000 requests/month, classifier costs $0.00004 each,
  cache hit rate 40% (section 1's semantic cache).

    route-first (classify every request, then check cache): $4.00/month spent on classification alone
    cache-first (check cache, only classify on a MISS):      $2.40/month
    wasted classification spend from the wrong order: $1.60/month

  This is on top of whatever the classifier saves or costs at the
  MODEL layer (section 2) -- routing-first pays the classification
  cost even on requests that were about to be served from cache for
  free. The fix is one line of pipeline order, not a smarter
  classifier: check the cache FIRST, route only on a miss.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every number is exact arithmetic given the stated inputs. No
  model behaviour, embedding similarity, or classifier is actually
  run -- all rates are stated parameters standing in for them.

  ILLUSTRATIVE: the traffic mix, prices, and accuracy figures are
  chosen to make the arithmetic legible, not measured from any real
  system. Measure your own duplicate/paraphrase rates, your own
  cheap/expensive prices, and your own classifier's real accuracy
  before setting a routing policy from this lab's numbers.

  NOT SHOWN: how to build the semantic-similarity cache or the
  routing classifier itself (that's an embeddings/retrieval problem,
  M6), and production-grade fallback chains across more than two
  models, which is M13-L08's job, building on this lesson.

Done.
```

### 7.3 Reading the result

**Section 1's 50 wrong answers are the number to hold onto.** They are not 50 misses — they are 50
requests that received a confident, cached, incorrect answer. Whether semantic caching is worth deploying
depends entirely on how costly a silent wrong answer is for your domain, a question this lab deliberately
does not answer for you.

**Section 2's exact crossover — 60.4%, solved rather than eyeballed — is the lesson's central result.**
The table shows the shape (savings shrink, then reverse); the closed-form calculation shows precisely
where. Any router shipped without first computing this number for its own prices and traffic is a bet
placed without checking the odds.

**Section 3's $1.60/month looks small in isolation and is not the point.** It is a pure, avoidable tax on
top of section 2's economics, caused entirely by pipeline order — the cheapest fix in the whole lesson,
worth checking in any system that has both a cache and a router.

---

## 8. Common mistakes and troubleshooting

1. **Confusing response caching with prompt/prefix caching (M5-L15).** Different mechanisms, different
   economics, different failure modes.
2. **Deploying a semantic cache without measuring its wrong-hit rate.** §5.1 — the hit rate alone is not
   the whole story.
3. **Building a router without measuring classifier accuracy first.** §6, exactly.
4. **Assuming "better than always-expensive" without computing the break-even accuracy.** §5.2's closed
   form is a few lines of arithmetic.
5. **Treating "always cheap" as free money because it's cheaper in dollars.** It carries a quality risk no
   token-cost table captures (§5.5).
6. **Running the routing classifier before checking the cache.** Wastes classification spend on requests
   that were about to be free (§5.3).
7. **Not monitoring misroute or fallback rate in production.** A router's accuracy can drift below its
   break-even point with nothing but the invoice to notice.
8. **Assuming a wrong cache hit is rare enough to ignore.** It scales linearly with cache traffic — flag
   it, don't assume it away.
9. **Building routing and caching as two unrelated features.** Their interaction (§5.3) has its own,
   separate cost.
10. **Not revisiting the break-even calculation as prices or traffic mix change.** A router that cleared
    the bar at launch may not clear it after a price change or a shift in query difficulty.

| Symptom | Likely cause | Fix |
|---|---|---|
| Bill went up after adding a router | Classifier accuracy below the break-even point | Measure accuracy; compute break-even for current prices (§5.2) |
| Users occasionally get a clearly wrong, confident answer | Semantic cache wrong-hit | Track and bound the wrong-hit rate; consider exact-match for high-stakes queries |
| Classification cost is a bigger line item than expected | Classifier runs before the cache check | Reorder: cache first, route only on a miss (§5.3) |
| Router's savings shrink over time with no obvious cause | Classifier accuracy drifting as traffic shifts | Monitor misroute/fallback rate continuously, not just at launch |
| Hard requests silently get worse answers | "Always cheap" or a too-aggressive router, no quality check | Add output validation (M5-L07) independent of cost routing |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** A wrong cache hit is a silent correctness failure, not a visible error — instrument
  and bound it, especially for a semantic cache (§5.1).
- **Cost.** Compute a router's break-even accuracy for your own prices before building or keeping it.
  §7.2 measured a real, non-trivial crossover (60.4%) — routers are not free money by default.
- **Cost.** Check the cache before running a routing classifier. §7.3 priced the waste from the wrong
  order at $1.60/month in one stated scenario; the ratio scales with cache hit rate and traffic volume.
- **Privacy.** A semantic cache can serve a cached answer — possibly containing details relevant to a
  different user's earlier query — to a new, similar-looking request. Scope cache keys to the appropriate
  trust and tenancy boundary, not just semantic similarity (M7-L15 covers this formally for retrieval).
- **Reliability.** Monitor misroute and fallback rate as first-class production metrics, not just total
  spend — a router drifting below its break-even point looks identical to "normal operation" until the
  invoice.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what is the difference between prompt caching (M5-L15) and response caching (this
   lesson)?
2. Why can a semantic cache produce a wrong answer that an exact-match cache cannot?
3. What two things does a misrouted hard request pay for?
4. Why should a cache be checked before a routing classifier runs?
5. What is a break-even accuracy, in your own words?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the exact crossover accuracy from section 2 and confirm it matches the lesson.
2. Change the easy/hard traffic split in section 2 to 80/20 and recompute the crossover. Does routing
   become easier or harder to justify, and why?
3. Using section 1's model, compute the wrong-hit count at a lower similarity threshold (assume a 10%
   wrong-hit rate on paraphrases instead of 20%) and compare.
4. Derive section 2's closed-form crossover formula yourself from the `routed_cost` function, and verify
   it against the lab's printed value.
5. Design a monitoring dashboard (fields and alert thresholds) for a production router, covering
   accuracy, misroute rate, and fallback rate.

### Exercise 3 — Challenge (~50 min)

1. Build a small `ResponseCache` class supporting both exact-match and a mock "semantic" mode (a
   configurable similarity function), and test that only the semantic mode can produce a wrong hit.
2. Implement the break-even accuracy formula as a reusable function taking arbitrary prices and traffic
   mix, and validate it against three different scenarios you construct.
3. Design a router that also checks its own confidence and falls back directly to the expensive model
   for low-confidence classifications, and analyse whether this changes the break-even accuracy
   calculation.
4. Extend section 3's pipeline-order analysis to a three-stage pipeline (cache, router, tool-permission
   check) and determine the cost-minimising order.
5. Write the design doc for a router in a real or plausible system of your choice, including the
   break-even calculation, the monitoring plan, and the criteria for turning it off if it underperforms.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l16).)*

**Q1.** Semantic caching served 250 more queries from cache than exact-match in §7.1, but also produced
50 silently wrong answers. The general lesson is:

- A. A higher cache hit rate is not automatically better — some of the extra hits can be wrong, and a wrong hit is worse than a miss.
- B. Semantic caching should always be preferred because its hit rate is higher.
- C. Exact-match caching is obsolete now that semantic caching exists.
- D. Wrong hits only occur when the cache is misconfigured.

**Q2.** Both routing and semantic caching failure modes in this lesson (wrong hits, misrouted requests
needing a fallback) share the property that:

- A. They only occur above 90% classifier accuracy.
- B. They are always more expensive than doing nothing at all.
- C. They are invisible in normal operation unless specifically instrumented for — nothing raises an error.
- D. They are eliminated automatically once a system reaches sufficient scale.

**Q3.** In §7.2, routing cost fell steadily as classifier accuracy rose from 40% to 95%. This happened
because:

- A. Higher accuracy reduces the number of tokens each request uses.
- B. The cheap model becomes free above a certain accuracy threshold.
- C. Higher accuracy always eliminates the need for a cache.
- D. Fewer misroutes mean fewer requests that pay for both a failed cheap attempt and a corrective expensive one.

**Q4.** The exact crossover point computed in §7.2 (60.4%) means:

- A. 60.4% of all requests should be routed to the cheap model regardless of difficulty.
- B. Below that classifier accuracy, routing costs more in total than simply always using the expensive model.
- C. The cache hit rate must exceed 60.4% for routing to be worthwhile.
- D. 60.4% is a fixed constant that applies to every routing system.

**Q5.** Why does a misrouted hard request cost more than a misrouted easy request, per §5.2?

- A. Hard requests are always billed at a premium regardless of routing.
- B. Easy requests are never actually billed.
- C. A misrouted hard request needs a full expensive-model fallback on top of the wasted cheap attempt, while a misrouted easy request just overpays for a correct answer.
- D. Misrouted easy requests are always retried three times.

**Q6.** Per §5.3, why should a response cache be checked before running a routing classifier?

- A. A cache hit skips the model call entirely, so classifying first wastes the classification cost on requests that never needed routing at all.
- B. Routing classifiers are always more accurate after a cache check.
- C. Providers require caches to be checked first by policy.
- D. It has no effect on cost, only on latency.

**Q7.** §7.3 found the wrong pipeline order wasted $1.60/month in a stated scenario. This number would
grow if:

- A. The cache hit rate were lower, since fewer requests would reach the classifier.
- B. The classifier were replaced with a more expensive model.
- C. The total request volume were reduced.
- D. The cache hit rate were higher, since more requests would be classified unnecessarily before ever reaching the cache check.

**Q8.** An easy query misrouted to the expensive model, per §5.2's table, results in:

- A. A validation failure requiring escalation.
- B. A correct answer at a higher cost than necessary, not a failure requiring a fallback.
- C. No response at all.
- D. The same cost as a correctly routed easy query.

**Q9.** The "always cheap" strategy in §7.2 was much less expensive than "always expensive," but the
lesson does not recommend it because:

- A. Hard requests would get a cheap-model answer of genuinely unknown quality, a real risk that a token-cost table cannot capture.
- B. It is technically infeasible to implement.
- C. Providers prohibit using only the cheap model.
- D. It would violate the break-even accuracy calculation.

**Q10.** This lesson's routing analysis differs from M5-L14's retry/fallback material mainly in that:

- A. M5-L14 is only about caching, not retries.
- B. Routing decisions are always made by the model itself, not the application.
- C. This lesson's routing has no relationship to M5-L14's fallback concepts at all.
- D. It evaluates a proactive classify-then-choose decision made before any model call, not a reactive response to a failure that already happened.

**Q11.** The general principle this lesson establishes about building a router is:

- A. Any classifier better than random guessing justifies building a router.
- B. A router is only worth building if its measured accuracy clears a computable cost break-even point, not merely "better than nothing."
- C. Routers should never be used with caching in the same pipeline.
- D. Routing decisions should be made independently of price.

**Q12.** In §6's incident, the router made the bill worse because:

- A. The cache was misconfigured.
- B. The expensive model's price increased mid-month.
- C. The classifier's accuracy (about 55%) was shipped without measurement and turned out to sit below the system's own break-even point (60.4%).
- D. The team used exact-match caching instead of semantic caching.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes adding a cheap/expensive
model router "since even a rough classifier should save money." State what assumption this skips and what
you would ask them to measure and compute before shipping it.

---

## 12. Revision notes

- **Response caching (this lesson) and prompt caching (M5-L15) are different mechanisms** — one skips
  the model call entirely; the other discounts part of a call that still happens.
- **A semantic cache trades hit rate for a new failure mode.** Measured: 250 more hits than exact-match,
  50 of them silently wrong. A wrong hit is worse than a miss.
- **A router has a computable break-even accuracy.** Measured: 60.4% for one stated price and traffic
  mix. Below it, routing costs more than never routing; misrouted hard requests pay for both a failed
  cheap attempt and an expensive fallback.
- **"Always cheap" is not free money** — it is cheaper in dollars and carries an unmeasured quality risk
  on every hard request, which a cost table alone cannot capture.
- **Check the cache before running a routing classifier.** Measured: $1.60/month wasted from the wrong
  order in one stated scenario, purely from ordering.
- **Never ship a router without first measuring its accuracy and computing its break-even point** for
  your own prices and traffic — "should save money" is an assumption until it is a calculation.
- **Monitor misroute and fallback rate continuously.** A router's accuracy can drift below break-even
  with nothing but the invoice to notice, unless you track it directly.

---

## 13. Completion checklist

- [ ] I can distinguish response caching from prompt/prefix caching.
- [ ] I have measured (or would measure) my semantic cache's wrong-hit rate before relying on it.
- [ ] I have computed my router's break-even accuracy for my own prices and traffic mix.
- [ ] My pipeline checks the cache before running any routing classifier.
- [ ] I monitor misroute and fallback rate in production, not just total spend.
- [ ] I treat "always cheap" as a quality risk, not a free win, and validate hard-request output
      independently of routing.
- [ ] I revisit the break-even calculation when prices or traffic mix change.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic — prompt caching documentation (for contrast with response-level caching).
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching> `[UNVERIFIED]`
- Chen, L., et al. (2023), *FrugalGPT: How to Use Large Language Models While Reducing Cost and
  Improving Performance*. <https://arxiv.org/abs/2305.05176> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L17 — Provider Differences and Portability](M5-L17-provider-portability.md)

You can now decide when caching and routing pay for themselves. Next: what changes, and what doesn't,
when the same prompt has to run against a different provider entirely.
