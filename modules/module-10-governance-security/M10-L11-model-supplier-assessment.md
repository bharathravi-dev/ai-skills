# M10-L11 — Model and Supplier Assessment

| | |
|---|---|
| **Lesson ID** | M10-L11 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M4-L18](../module-04-genai-llm-internals/M4-L18-hosted-vs-local.md), [M10-L05](M10-L05-data-provenance-licensing.md) |

---

## 1. Learning objectives

1. **Separate** must-pass requirements from scored criteria, and apply gates before any weighted comparison.
2. **Test** how much a supplier ranking depends on the weights you chose.
3. **Compare** list price with total cost at your volume, including engineering effort.
4. **Quantify** lock-in as the provider-specific surface a design uses.
5. **Re-assess** suppliers on events — terms changes, deprecations, incidents, acquisitions — not only at purchase.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Must-pass requirement (gate)** | A yes/no fact that disqualifies a supplier if unmet — data handling, region, deletion commitments. |
| **Scored criterion** | Something better or worse by degree — quality, latency, support, roadmap. |
| **Sub-processor** | A third party your supplier uses to process your data. |
| **Lock-in** | The cost of leaving, measured in what you would have to rebuild. |
| **Total cost** | Usage price plus support tiers, egress, engineering, and the cost of switching later. |
| **Re-assessment trigger** | An event that invalidates the previous assessment. |

---

## 3. Plain-language explanation

### 3.1 Gates first, scores second

§7.1 scores five suppliers on quality, latency, support and roadmap, and checks three must-pass requirements: data not
used for training, an EU region available, and a 30-day deletion commitment. The **highest-scoring supplier fails two of
the three gates**. Only **2 of 5** suppliers pass all gates, and the best eligible one ranks **second** on points.

A weighted average lets a strong quality score pay for a failed data-handling requirement. That is precisely what a gate
prevents: it is answered before scoring, and it is not tradeable.

### 3.2 Check whether your weights are doing the deciding

§7.2 re-ranks under four plausible weightings. Here the **top choice is stable** and only places two and three swap under
an operations-led weighting. That is worth knowing rather than assuming: when a reasonable reweighting *does* change the
winner, the decision is being made by the weights, and an explicit trade-off conversation is more honest than a number.

### 3.3 List price is not cost

§7.3 prices 40M tokens a month. The cheapest **per token** (self-hosted open weights, £0 per token) is the **most
expensive overall** once engineering time is counted; a mid-priced provider with no support tier is cheapest overall.
**4 of 5** positions differ between the two orderings.

### 3.4 Lock-in is a count, not a feeling

§7.4 compares three designs. A portable design uses two features, both standard. A convenient design uses five, of which
**three are provider-specific**. An all-in design uses eight, **six provider-specific**. Switching cost is the list of
things you would rebuild.

### 3.5 Assessments expire

§7.5: **4 of 5** suppliers need re-assessment — an assessment from January against terms updated in June and a model
deprecated in August; a supplier acquired after a security incident; a licence changed last month.

---

## 4. Analogy

**Hiring a contractor for work on your house.** Insurance, certification and references are gates: no amount of charm or a
low quote compensates. Only then do you compare price, availability and quality. The quote is not the cost — access, making
good, and your own time are part of it. Using their proprietary fittings means the next contractor has to replace them.
And the certificate you checked two years ago may have lapsed.

### Where the analogy breaks

- **A contractor's work is finished; a model supplier's product changes weekly.** Deprecations and silent model updates are
  routine, so re-assessment is scheduled and event-driven (§5.5).
- **You can inspect a finished wall; you cannot inspect a provider's training pipeline.** Assurance comes from contracts,
  documentation and your own measurements, not from inspection (§5.1).

---

## 5. Detailed technical explanation

### 5.1 What to assess

| Area | Ask for | Evidence, not assertion |
|---|---|---|
| **Data handling** | Is our data used for training? Retention? Deletion commitment and SLA? Sub-processors? | The contract or DPA text, the sub-processor list, the deletion mechanism |
| **Location and transfer** | Which regions process and store data? | Region documentation; a configuration you can verify |
| **Security** | Certifications, penetration tests, incident history and notification terms | Report summaries, incident notification clauses |
| **Model behaviour** | Quality on **your** tasks, refusal behaviour, subgroup performance | Your own evaluation (M5-L18, L08) — not a public benchmark |
| **Change management** | Deprecation notice periods, model pinning, silent-update policy | Documented policy; a pinned version in the contract |
| **Availability** | Uptime commitments, rate limits, quota increases, regional failover | SLA text and observed behaviour under load |
| **Commercial** | Price, minimums, support tiers, exit terms, data export | The full price sheet at your volume |
| **Viability** | Funding, ownership, roadmap, customer base | Public filings, references, acquisition history |

The distinction that matters: **facts you require** (gates) versus **qualities you compare** (scores). Data handling,
region and deletion are usually gates. Quality and latency are usually scores — unless your use case makes one of them a
threshold, in which case say so and make it a gate.

### 5.2 Gates before scores

`[REAL, measured]` §7.1: the top-scoring supplier fails two gates; 2 of 5 suppliers are eligible; the best eligible ranks
second on points.

Practical format for a decision record:

```text
Must-pass (yes/no, evidenced):
  [x] our data is not used for training          -- DPA clause 4.2
  [x] EU region available and configured          -- provider docs + our terraform
  [ ] deletion within 30 days                     -- FAILS: 90 days in current terms
Scored (only for suppliers passing every gate):
  quality 4/5 (our eval, 2026-09-02, n=300), latency 4/5, support 3/5, roadmap 4/5
Decision: Provider B. Residual risks: support tier, single-region failover (register rows R12, R13).
```

### 5.3 Weight sensitivity

`[REAL, measured]` §7.2: one supplier ranked first under all four weightings; two positions moved under the
operations-led weighting.

Run the check anyway — it costs a minute — and report it. If the winner changes across plausible weightings, stop
optimising the spreadsheet: shortlist the candidates that win under *some* reasonable weighting and make the trade-off
explicitly, with the people who will live with it.

### 5.4 Total cost and lock-in

`[REAL, measured, ILLUSTRATIVE prices]` §7.3: cheapest per token ≠ cheapest overall; 4 of 5 positions differ.

Include in the comparison: usage at **your** volume and token profile (M5-L15), support tiers, egress, the engineering to
integrate and to operate (self-hosting includes on-call), the cost of evaluation and re-evaluation, and a switching
estimate.

`[REAL, measured]` §7.4: 0, 3 and 6 provider-specific features across three designs. Keep the provider-specific surface
deliberate: an abstraction at the call site (M5-L17), a note in the design record of which lock-in you accepted and why,
and a rough estimate of the switching work. "We could switch in a fortnight" is a claim to test, not to assume.

### 5.5 Re-assessment

`[REAL, measured]` §7.5: 4 of 5 suppliers are due, for a mix of age and events.

Triggers: terms or DPA changes; sub-processor additions; a model deprecation or a silent update; a security incident at
the supplier; acquisition or change of control; licence changes for open-weight models; a material price change; and your
own use changing (new data classes, new region, new audience — the L02 rule again).

Keep the supplier's row in the inventory (L03) with `last_assessed`, the gate results, and the evidence links, so the
question "are we still comfortable?" has an owner and a date.

### 5.6 Assessing the model itself

Supplier assessment is not model evaluation. Even a supplier that passes every gate needs its model measured **on your
tasks**:

- Your evaluation set, your metrics, your subgroups (M5-L18, L08).
- Behaviour under your prompts, including refusals and formatting stability (M5-L14, M9-L07).
- Cost and latency at your context sizes (M5-L15).
- Regression when the provider updates: pin versions where you can, and re-run the suite when you move (L12, M13-L06).

### 5.7 Assumptions and limitations

- Every figure in the lab is invented; the arithmetic is real, the suppliers are not.
- Contractual and regulatory obligations for processors and sub-processors are jurisdiction-specific and out of scope (L16).
- Procurement processes vary; this lesson covers the technical assessment that feeds them.

---

## 6. Worked example — the cheapest provider that cost the most

**The situation.** A team chose a new provider for a summarisation feature on price: a quarter of the incumbent's per-token
cost, with a strong benchmark score. The decision memo was a weighted table; the winner scored highest.

**What happened over six months.**

1. The provider's terms permitted **training on customer content** unless you opted out in the console — a gate question
   nobody asked, discovered during a client security review (§5.1).
2. The integration needed **structured-output workarounds** because the provider's JSON mode behaved differently; two
   weeks of engineering, then ongoing repair logic (M5-L07).
3. Latency was good at launch and degraded under load; there was no SLA, and support was a community forum (§5.1
   availability row).
4. The provider was **acquired**; the new owner deprecated the model with 30 days' notice. The team migrated in a rush —
   and discovered the summariser's prompts had been tuned to that model's quirks (§5.4 lock-in).

**Recomputed at the end:** the "cheap" provider cost roughly four times the incumbent once engineering and migration were
counted, and the client review cost more than either.

| # | What was missing | Fix |
|---|---|---|
| 1 | Data-handling gate | Gates answered yes/no with evidence, before scoring |
| 2 | Total cost at real volume | Price at volume + support + engineering + switching estimate |
| 3 | Availability commitments | SLA, rate limits and support tier as gates for production use |
| 4 | Re-assessment triggers | Register acquisition, deprecation and terms changes as triggers |
| 5 | Lock-in unmeasured | Count provider-specific features; keep an abstraction at the call site |

**The general rule.** **Price is the easiest number to compare and the least likely to decide the outcome.**

---

## 7. Practical activity

**File:** [`labs/m10/l11_supplier_assessment.py`](../../labs/m10/l11_supplier_assessment.py)

**No API key, no network, no third-party dependencies.** All suppliers, scores and prices are invented.

```bash
source .venv/bin/activate
python labs/m10/l11_supplier_assessment.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. WEIGHTED SCORE VS MUST-PASS REQUIREMENTS
============================================================================
  rank supplier                                 weighted score   must-pass failures
  1    Provider A (frontier, US)                          4.60   eu_region_available, deletion_sla_30d
  2    Provider B (frontier, EU region)                   3.80   none
  3    Provider E (incumbent vendor add-on)               3.40   deletion_sla_30d
  4    Provider C (cheap, new)                            3.05   data_not_used_for_training, deletion_sla_30d
  5    Provider D (self-hosted open weights)              2.60   none

  ranking by score alone puts 'Provider A (frontier, US)' first; it fails 2 must-pass requirement(s).
  eligible suppliers after gates: 2/5 -> best eligible: 'Provider B (frontier, EU region)'
  A weighted average lets a strong score on quality pay for a failed requirement
  about data handling. Gates are answered yes/no BEFORE any scoring.

============================================================================
2. HOW MUCH DOES THE RANKING DEPEND ON THE WEIGHTS?
============================================================================
  as chosen        Provider A > Provider B > Provider E > Provider C > Provider D
  quality-led      Provider A > Provider B > Provider E > Provider C > Provider D
  operations-led   Provider A > Provider E > Provider B > Provider C > Provider D
  equal weights    Provider A > Provider B > Provider E > Provider C > Provider D

  distinct suppliers ranked first across four weightings: 1
  positions that move relative to the chosen weighting: quality-led: 0, operations-led: 2, equal weights: 0
  Here the top choice is stable and only places 2-3 swap, which is a useful
  thing to have checked rather than assumed. When a plausible reweighting DOES
  change the winner, the weights are deciding rather than the evidence -- and a
  short-list plus an explicit trade-off conversation is the honest alternative.

============================================================================
3. LIST PRICE VS TOTAL COST  [ILLUSTRATIVE FIGURES]
============================================================================
  at 40M tokens/month

  supplier                                    tokens     other    total/mo
  Provider A (frontier, US)                      280     1,500       1,780
  Provider B (frontier, EU region)               320         0         320
  Provider C (cheap, new)                         80     2,500       2,580
  Provider D (self-hosted open weights)            0     9,400       9,400
  Provider E (incumbent vendor add-on)           440         0         440

  cheapest by list price : Provider D
  cheapest by total cost : Provider B
  positions that differ between the two orderings: 4/5
  Self-hosting trades price per token for engineering time; a cheap provider
  that needs its own integration is not cheap at this volume (M4-L18, M12-L14).

============================================================================
4. LOCK-IN: HOW MUCH PROVIDER-SPECIFIC SURFACE DOES THE DESIGN USE?
============================================================================
  portable design      uses 2 features, 0 provider-specific: none
  convenient design    uses 5 features, 3 provider-specific: structured output constrained decoding, provider-hosted vector store, provider-specific caching header
  all-in design        uses 8 features, 6 provider-specific: structured output constrained decoding, provider-hosted vector store, provider-specific caching header, fine-tuned model on provider, batch API with provider queue, provider-specific safety filters config

  Switching cost is not a number in a contract; it is the count of things you
  would have to rebuild. Decide deliberately which provider-specific features
  are worth the lock-in, and keep an abstraction at the call site (M5-L17).

============================================================================
5. IS THE ASSESSMENT STILL TRUE?
============================================================================
  Provider A (frontier, US)                RE-ASSESS: assessed 2026-01-10; terms updated 2026-06; model deprecated 2026-08
  Provider B (frontier, EU region)         current
  Provider C (cheap, new)                  RE-ASSESS: assessed 2025-11-02; security incident 2026-03; acquired 2026-07
  Provider D (self-hosted open weights)    RE-ASSESS: licence change 2026-09
  Provider E (incumbent vendor add-on)     RE-ASSESS: assessed 2026-02-14; sub-processor added 2026-05

  4/5 suppliers need re-assessment.
  Supplier assessment is not a purchase-time activity: terms change, models are
  deprecated, companies are acquired, and licences are revised (M10-L14).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every ranking, sensitivity count, total and lock-in count above is
  computed from the encoded scores, prices and feature lists.

  ILLUSTRATIVE: the suppliers are fictional and every price and score is
  invented. Real assessments use the supplier's own documentation, contracts,
  security reports and your measured results (M5-L18, M10-L12).

  NOT SHOWN: contract negotiation, procurement process, and jurisdiction-specific
  obligations for processors and sub-processors (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's first row is the pattern to recognise**: highest score, two failed requirements.

**Section 2 is a check, not a finding.** The winner happened to be stable; you only know that because it was tested.

**Section 3 shows why "cheapest per token" is a trap** at any volume where engineering time is real.

---

## 8. Common mistakes and troubleshooting

1. **Scoring data handling instead of gating it.** §5.2.
2. **Not testing weight sensitivity.** §5.3.
3. **Comparing list prices.** §5.4 — 4 of 5 positions changed once total cost was computed.
4. **Ignoring engineering cost in self-hosting.** §5.4.
5. **Accepting benchmark scores as evidence of quality on your task.** §5.6.
6. **Assessing at purchase only.** §5.5 — 4 of 5 suppliers were due for re-assessment.
7. **Unmeasured lock-in.** §5.4 — count the provider-specific features.

| Symptom | Likely cause | Fix |
|---|---|---|
| A security review blocks a launch over data handling | Gate treated as a scored criterion | Answer gates first, with evidence |
| Costs exceed the business case | List price compared, not total | Model volume, support, engineering, switching |
| A provider change breaks production | No deprecation policy or pinning | Make notice periods and pinning gates; re-assess on change |
| Switching estimate is guesswork | Lock-in never measured | Count provider-specific features; test a migration path |
| Nobody knows if terms changed | No re-assessment triggers | Register triggers; assign an owner and a date (L03) |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Data handling, sub-processors and deletion are gates because they cannot be traded against quality (L06).
- **Security.** Incident history and notification terms matter more than certificates: ask how you would learn of a breach,
  and how fast.
- **Reliability.** Deprecation notice periods and SLAs are what let you plan; measure observed behaviour too (M13-L11).
- **Cost.** Compare at your volume and token profile; recompute when volume changes by an order of magnitude (M12-L14).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Classify as gate or score: EU region; latency; sub-processor list; roadmap; deletion SLA; support quality.
2. Why did the top-scoring supplier in §7.1 fail?
3. What changed between the list-price and total-cost orderings?
4. Count the provider-specific features in a design you know.
5. List four events that should trigger re-assessment.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a supplier that passes every gate but scores 2/5 on quality; what should the decision be?
2. Change the volume in §7.3 to 400M tokens/month and re-rank.
3. Add "notice period for deprecation ≥ 12 months" as a gate and see who survives.
4. Write the decision record for your choice using §5.2's format.
5. Score the lock-in of your current design and state which provider-specific features you would give up.

### Exercise 3 — Challenge (~60 min)

1. Build the assessment template your organisation would use, with evidence fields for every gate.
2. Run a real evaluation of two providers on your own task and report quality, cost and latency with intervals (M5-L18).
3. Estimate the switching cost of your current design by attempting a migration in a branch, and record what breaks.
4. Design the monitoring that would tell you a provider silently changed a model (M13-L12).
5. Write the re-assessment policy: triggers, owner, evidence, and what happens if a gate now fails.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l11).)*

**Q1.** What is a must-pass requirement?

- A. The criterion with the highest weight
- B. A score above an agreed threshold
- C. A yes/no fact that disqualifies if unmet
- D. A contractual term that can be negotiated later

**Q2.** In §7.1, what was true of the highest-scoring supplier?

- A. It passed every gate
- B. It failed two must-pass requirements
- C. It was the cheapest by total cost
- D. It was excluded for lock-in

**Q3.** How many of the five suppliers passed all gates?

- A. 2 suppliers
- B. 3 suppliers
- C. 4 suppliers
- D. 5 suppliers

**Q4.** What did the weight-sensitivity check show in §7.2?

- A. Every weighting produced a different winner
- B. The eligible set changed with the weights
- C. Scores became meaningless above four criteria
- D. The winner was stable; places 2-3 swapped

**Q5.** Why run the sensitivity check at all?

- A. It improves the accuracy of the scores
- B. It shows whether the weights are deciding
- C. It is required for supplier audits
- D. It reduces the number of criteria needed

**Q6.** In §7.3, which supplier was cheapest by list price?

- A. The self-hosted open-weights option
- B. The frontier provider with an EU region
- C. The incumbent vendor add-on
- D. The cheap new provider

**Q7.** Why was it not cheapest overall?

- A. Its per-token price rose with volume
- B. It required a paid support tier
- C. Engineering and operating effort dominated
- D. Its egress charges exceeded token costs

**Q8.** How does the lab quantify lock-in?

- A. By the length of the contract term
- B. By the price difference between providers
- C. By the number of tokens processed monthly
- D. By counting provider-specific features used

**Q9.** Which design had six provider-specific features?

- A. The all-in design
- B. The convenient design
- C. The portable design
- D. None of them

**Q10.** Which event should trigger re-assessment?

- A. A new release of your own application
- B. A change in your team's on-call rota
- C. The supplier being acquired
- D. An increase in your evaluation set size

**Q11.** What evidence should support a data-handling gate?

- A. The supplier's marketing page
- B. A benchmark score on public tasks
- C. A reference from another customer
- D. The contract or DPA clause, and the deletion mechanism

**Q12.** What does supplier assessment *not* replace?

- A. Contract negotiation
- B. Evaluating the model on your own tasks
- C. Maintaining an inventory entry
- D. Recording residual risks

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team wants to switch to a cheaper model provider. Describe
the assessment you would run before agreeing, and what would make you refuse regardless of price.

---

## 12. Revision notes

- **Gates before scores.** Measured: the top-scoring supplier failed **2 of 3** gates; only **2 of 5** were eligible; the
  best eligible ranked second on points.
- **Weight sensitivity:** test it. Here the winner was stable and places 2–3 moved under an operations-led weighting.
- **Total cost ≠ list price:** cheapest per token was the most expensive overall; **4/5** positions differed.
- **Lock-in = count of provider-specific features** (0, 3, 6 across three designs); keep an abstraction at the call site.
- **Re-assess on events:** terms, sub-processors, deprecations, incidents, acquisitions, licence changes — **4/5**
  suppliers were due.
- **Assessment ≠ evaluation:** measure the model on your own tasks regardless of who the supplier is.

---

## 13. Completion checklist

- [ ] I separate must-pass requirements from scored criteria and evidence each gate.
- [ ] I test whether my weights decide the outcome.
- [ ] I compare total cost at my volume, including engineering.
- [ ] I count and record the provider-specific surface I depend on.
- [ ] I re-assess on events, with an owner and a date.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M4-L18 (hosted vs local models) and M5-L17 (provider portability) — the technical trade-offs behind the gates `[STABLE]`
- M5-L15 (token accounting) and M12-L14 (cost per request on AWS) — how to price at your volume `[STABLE]`
- M5-L18 (evaluation datasets) and M10-L08 — measuring the model on your own tasks `[STABLE]`
- ISO/IEC 42001 and NIST AI RMF *Govern* — third-party and supply-chain expectations; see M10-L16 `[UNVERIFIED]`

---

## 15. Next lesson

→ [M10-L12 — Release Evaluation Gates](M10-L12-release-gates.md) turns evaluation results into a decision procedure: what
must be true before a change ships, and how gates fail when they ignore uncertainty.
