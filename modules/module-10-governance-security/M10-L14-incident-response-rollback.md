# M10-L14 — Incident Response, Rollback and Change Management

| | |
|---|---|
| **Lesson ID** | M10-L14 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M10-L12](M10-L12-release-gates.md), [M10-L13](M10-L13-versioning-auditability.md), [M8-L11](../module-08-agentic-ai/M8-L11-read-only-vs-state-changing.md) |

---

## 1. Learning objectives

1. **Compare** detection strategies on both time-to-detect and false-alarm rate, and choose deliberately.
2. **Compute** blast radius as exposure × detection time, and use rollout size as a cap on unknown mistakes.
3. **Classify** changes as reversible or one-way doors, and prepare the reverse path before shipping the forward one.
4. **Apply** a severity rule driven by the kind of harm rather than the number of users.
5. **Keep** changes small and independently revertible so that attribution during an incident is possible at all.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Incident** | An unplanned event that is harming users, data or the business, requiring coordinated response. |
| **Time to detect (TTD)** | From the start of the problem to someone knowing about it. |
| **Time to mitigate (TTM)** | From knowing to the harm stopping — usually a rollback, not a fix. |
| **Blast radius** | How many users or records the problem reached before it stopped. |
| **One-way door** | A change whose effects cannot be undone by reverting the change. |
| **Severity (SEV)** | A classification that decides who responds, how fast, and who is told. |
| **Mitigate, then diagnose** | Stop the harm first; understand it afterwards. |
| **Blameless review** | A post-incident review that produces control changes, not blame. |

---

## 3. Plain-language explanation

### 3.1 Detection is a choice with two costs

§7.1 runs a regression that raises the bad-answer rate from 2% to 14%. Waiting for user reports detects it in **17.5
hours** on average. An hourly automated check detects it in **1.0 hour** — **17× sooner**. A canary at 5% of traffic takes
**4.0 hours**, because it has fewer samples to work with.

The second column is the one teams forget. In a **quiet** fortnight with no incident, the hourly alert fires anyway in
**62%** of runs; the canary check in **3%**. An alert that cries wolf two weeks in three is not a detector — it is
training for the on-call engineer to ignore it.

### 3.2 Blast radius is exposure multiplied by time

§7.2 combines them: a big-bang rollout detected in an hour delivers **144** bad answers; a 5% canary detected in four
hours delivers **18**; a 1% canary, **4**. The canary is *slower* to detect and still harms far fewer people, because
exposure dominates.

### 3.3 "We can always roll back" is half true

§7.3 classifies ten changes: **5 of 10 are one-way doors**. Prompts, model versions, decoding parameters, retrieval
settings and guardrail policies revert cleanly. A re-embedded corpus, a schema migration, forty invoices the agent has
already emailed, records a tool deleted, and a price quoted to a customer do not.

### 3.4 Severity is about the kind of harm

§7.4 applies one rule to eight events. "One tenant sees another tenant's documents" affects **few** users and is **SEV1**.
"Answers slower than usual" affects **many** and is **SEV2**. Volume adjusts urgency; it does not set the class.

### 3.5 Big deploys make incidents unsolvable

§7.5: at 12 changes per deploy, an incident has **12 suspects**, reverting the deploy takes back **11 innocent changes**,
and isolating the guilty one costs **3.7 bisect steps** — each one a deploy, under time pressure. At one change per
deploy: 1 suspect, 0 innocent reverts, 0 steps.

---

## 4. Analogy

**A kitchen fire.** You do not begin by working out which pan caused it. You turn off the heat, cover it, get people out —
*then* you investigate. A smoke alarm in every room detects fast and goes off when you make toast; one alarm in the hallway
is quieter and slower. And some damage cannot be reverted: the extinguisher saves the kitchen, but the meal is gone and
the guests already left.

### Where the analogy breaks

- **Fires are visible; a quality regression is a statistic.** You cannot smell a nine-point drop on French queries — it has
  to be measured, on a slice, continuously (§5.1, L12).
- **Fires stop when extinguished; an agent's side effects persist.** Half the incident is undoing what the system did to
  the outside world (§5.4).

---

## 5. Detailed technical explanation

### 5.1 Detection: what to watch, and the false-alarm budget

`[REAL, simulated]` §7.1 — 17.5 h / 1.0 h / 4.0 h to detect; 100% / 62% / 3% false-alarm rates in a quiet fortnight.

| Signal class | Examples | Detects |
|---|---|---|
| **Availability** | error rate, timeouts, 5xx, provider failures | Outages, quota exhaustion |
| **Behaviour** | refusal rate, abstention rate, tool-error rate, output length distribution | Prompt or model changes |
| **Quality proxies** | citation validity, schema-validation failures, retrieval hit rate | Silent regressions |
| **Slice metrics** | the L08 slices, tracked separately | Regressions the aggregate hides |
| **Safety** | unsafe-output rate, blocked rate, injection-detector hits | Security and safety incidents |
| **Cost** | tokens per request, spend per hour | Runaway loops (M8-L15) |
| **Human** | complaints, thumbs-down, escalations to support | Everything, slowly |

The false-alarm result is the practical lesson: a threshold on a **small hourly sample** near the base rate will fire
constantly. Fix it with a larger window (compare a rolling 6-hour window), a bound rather than a point estimate (L12
§5.3), or a two-stage rule — alert on a sustained breach of *two consecutive* windows. Whatever you choose, **measure the
quiet-period firing rate before you rely on it**.

### 5.2 Blast radius, and rollout as a cap

`[REAL, computed]` §7.2: 144 / 72 / 18 / 4 bad answers across the four rollouts.

```text
harm ≈ request_rate × exposure × (incident_rate − base_rate) × (TTD + TTM)
```

Every term is a lever. Exposure is the cheapest one to control and the only one you decide *in advance* — it is a cap on
the size of a mistake you have not yet found. The canary-detects-slower objection is real and usually loses to the
arithmetic, because exposure is a multiplier and detection time is an addend.

### 5.3 Rolling back

Rollback is the default mitigation because it is the fastest well-understood action. It requires three things prepared
beforehand: the **previous version pinned and still deployable** (L13), a **revert path that does not require a build**,
and a **decision rule** that says who may call it without a meeting.

```text
Rollback criteria (agreed in advance):
  - any SEV1  -> roll back immediately, diagnose after
  - SEV2 with a known-good previous version -> roll back, then diagnose
  - SEV2 with no rollback path (one-way door) -> mitigate at the boundary:
      disable the tool, switch to read-only, route to humans, feature-flag off
  - the on-call engineer may call any rollback alone. No approval required.
```

**Mitigate, then diagnose.** The commonest failure in incident response is spending the first hour working out *why*
while the harm continues. The second commonest is a fix-forward that introduces a second incident.

### 5.4 One-way doors

`[REAL, classified]` §7.3 — 5 of 10.

| Type | Preparation that makes it survivable |
|---|---|
| Index rebuild / re-embedding | Keep the previous index until the new one is gated; alias-swap to switch |
| Schema migration | Write the reverse migration in the same change; deploy expand → migrate → contract |
| Agent side effects (emails, payments, tickets) | Idempotency keys, approval gates, per-run caps, a compensating action (M8-L10, M8-L12) |
| Deletions | Soft-delete with a retention window; backups in scope and *tested* |
| Commitments to customers | Human approval before anything binding; a correction process that is a first-class path |

For the agent classes, the real control is upstream: **limit what the system can do irreversibly** (M8-L11, M9-L13). An
incident that can only produce wrong text is a different kind of incident from one that can produce wrong payments.

### 5.5 Severity and the response

`[REAL, rule applied]` §7.4 — 3 SEV1, 4 SEV2, 1 SEV3 across eight events.

```text
SEV1  data exposed across a boundary, safety harm, or unrecoverable money movement
      -> page now, incident channel, named commander, comms path opened
SEV2  feature broken for many users, or money/cost impact with a workaround
      -> page within hours, incident channel
SEV3  degraded quality on a slice, or cosmetic
      -> ticket, next working day, tracked to a fix
```

Roles matter more than headcount: an **incident commander** who decides and is not also debugging, a **communications**
owner, and a **scribe** keeping the timeline. The timeline is the input to the review and, for anything touching personal
data, to the notification decision — which is a legal question, taken with the people who own it (L16).

Publish the classification rule in advance. Classifying during an incident, with the author of the change in the room,
produces optimistic severities.

### 5.6 Change management that survives contact with an incident

`[REAL, computed]` §7.5: 1 / 4 / 12 suspects, 0 / 3 / 11 innocent reverts, 0 / 2.0 / 3.7 bisect steps.

- **Small changes, deployed independently.** This is an incident-response control (§7.5), not an aesthetic.
- **One risky change at a time.** Never ship a model bump and a retrieval change together; you will not know which broke it.
- **A change record per change**, linked to the run fingerprint (L13) so production behaviour maps to a commit.
- **Feature flags** so mitigation does not require a deploy.
- **A freeze rule**: what may ship while an incident is open — normally, only the mitigation.

### 5.7 After: the review

The output of a review is **changes to controls**, each with an owner and a date:

1. **Timeline** from the audit records (L13), not from memory.
2. **Detection**: how long, and which signal *would* have caught it sooner?
3. **Mitigation**: how long, and what slowed it down?
4. **Blast radius**: measured — who was affected, and do they need telling (L09)?
5. **Gate gap**: which L12 gate would have blocked this? If none would, that is the finding.
6. **Risk register update** (L04): new rows, or likelihood revised on existing ones.

"Be more careful" is not an action item. "Add a French-slice gate at −2 points to the release suite, owner X, by date Y"
is.

### 5.8 Assumptions and limitations

- Traffic volume, incident rate, report probability, rollback duration and the severity rule are invented; the arithmetic
  and the simulations are real.
- The false-alarm figures depend entirely on the threshold and window chosen — measure yours rather than reusing these.
- Regulatory breach-notification duties are jurisdiction-specific and out of scope (L16).

---

## 6. Worked example — the rollback that could not roll back

**The situation.** A team improved retrieval by re-embedding the corpus with a newer embedding model and switching the
index in place. Offline gates passed. It shipped at 100%.

**What happened.**

1. Four hours later, support noticed complaints about "the assistant can't find our returns policy" (§5.1 — no automated
   quality signal existed; detection was by report).
2. The team reverted the application deploy. **Nothing changed**: the code revert did not un-embed the corpus (§5.4).
3. The previous index had been **deleted** to save storage after the new one passed its gates.
4. Rebuilding took **six hours**, during which the mitigation was a banner and routing to human agents — which worked,
   and which nobody had prepared, so it took 40 minutes to arrange (§5.3).
5. The review found the cause: the new embedding model had a different maximum sequence length, silently truncating the
   longest policy documents at ingestion (M7-L06).

| # | What went wrong | Fix |
|---|---|---|
| 1 | No automated quality signal | Retrieval hit-rate and citation-validity monitors, per slice (§5.1) |
| 2 | Index change treated as reversible | Keep the previous index; switch by alias; delete only after a soak period |
| 3 | No prepared mitigation for a non-revertible change | Feature flag to the previous behaviour; documented degraded mode |
| 4 | Rollout at 100% | Canary at 5%; §7.2 arithmetic |
| 5 | Truncation not detected at ingestion | Ingestion assertions on document coverage; gate on retrieval metrics (L12) |

**The general rule.** **Before you ship, know exactly how you would take it back — and if the answer is "we couldn't", that
is a design decision, not a detail.**

---

## 7. Practical activity

**File:** [`labs/m10/l14_incident_response.py`](../../labs/m10/l14_incident_response.py)

**No API key, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m10/l14_incident_response.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Seeded with `random.Random(1014)`; run twice, output
identical.

```text

============================================================================
1. HOW LONG BEFORE ANYONE KNOWS?
============================================================================
  regression raises the bad-answer rate from 2% to 14%, 600 requests/hour

  detection strategy                               mean     p90   false alarms in a quiet fortnight
  waiting for user reports (3, then triage)      17.5 h    24 h    100% of quiet fortnights
  hourly alert on a 200-request sample            1.0 h     1 h     62% of quiet fortnights
  canary at 5% of traffic, min n=100              4.0 h     4 h      3% of quiet fortnights

  automated checking detects ~17x sooner than waiting to be told,
  and the canary ~4x sooner while exposing 5% of users (section 2).
  The false-alarm column is the cost: a detector nobody trusts is not a
  detector. Tune the threshold and the sample size together (M13-L12).

============================================================================
2. HOW MANY PEOPLE ARE HARMED BEFORE IT STOPS?
============================================================================
  bad answers delivered = requests x exposure x (incident rate - base rate)
  rollback takes 1 h once the decision is made

  rollout                      detect   exposed   bad answers
  big bang (100% at once)       1.0 h     100%           144
  50% rollout                   1.0 h      50%            72
  canary 5% then full           4.0 h       5%            18
  canary 1% then full           4.0 h       1%             4

  Two levers, and they multiply: detect sooner, and expose fewer people while
  you do. A slow rollout is not caution for its own sake -- it is a cap on the
  size of the mistake you have not found yet (M13-L14).

============================================================================
3. WHICH CHANGES CAN YOU ACTUALLY TAKE BACK?
============================================================================
  change                                reversible   how
  prompt template edit                         yes   redeploy previous hash
  model version bump                           yes   repoint to the pinned previous version
  decoding parameter change                    yes   config revert
  retrieval k / filter change                  yes   config revert
  guardrail policy update                      yes   policy version revert
  re-embedding the whole corpus                 NO   needs the old index kept, or a full rebuild (hours)
  schema migration on the store                 NO   needs a reverse migration written IN ADVANCE
  emails already sent by the agent              NO   cannot be unsent; only corrected (M8-L11)
  records deleted by a tool call                NO   recoverable only from backups, if in scope
  customer-visible price quote                  NO   commercially binding; a correction is a new event

  one-way doors: 5/10
  'We can always roll back' is true of configuration and false of effects. Know
  which of your changes are which BEFORE the incident, and write the reverse
  migration at the same time as the forward one (M8-L11, M8-L12).

============================================================================
4. SEVERITY: WHAT IS THIS, AND WHO GETS WOKEN?
============================================================================
  event                                       severity   action
  answers slower than usual                       SEV2   page in hours, incident channel
  one tenant sees another tenant's docs           SEV1   page now, incident channel, exec comms path
  agent emailed 40 wrong invoices                 SEV1   page now, incident channel, exec comms path
  assistant produced unsafe advice                SEV1   page now, incident channel, exec comms path
  citations broken on all answers                 SEV2   page in hours, incident channel
  cost per request tripled overnight              SEV2   page in hours, incident channel
  French answers regressed 9 points               SEV3   ticket, next working day
  model provider outage, feature down             SEV2   page in hours, incident channel

  {'SEV2': 4, 'SEV1': 3, 'SEV3': 1}
  Note what does NOT depend on user count: one tenant seeing another's
  documents affects 'few' users and is still the highest severity, because
  severity is about the KIND of harm, not the volume (M10-L07).

============================================================================
5. ATTRIBUTION: WHICH CHANGE CAUSED IT?
============================================================================
   1 changes per deploy, 21 deploys/week ->  21 changes/week,   1 suspects,  0.0 innocent changes reverted,  0.0 bisect steps to isolate
   4 changes per deploy, 21 deploys/week ->  84 changes/week,   4 suspects,  3.0 innocent changes reverted,  2.0 bisect steps to isolate
  12 changes per deploy, 21 deploys/week -> 252 changes/week,  12 suspects, 11.0 innocent changes reverted,  3.7 bisect steps to isolate

  Bisecting a batch of twelve means twelve suspects and, usually, a rollback of
  eleven innocent changes. Small, independently revertible changes are an
  incident-response control, not a style preference (M11-L18).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every detection time, exposure count, severity classification and
  candidate-cause count above is computed by simulation or by the stated rule.

  ILLUSTRATIVE: traffic volume, incident rate, report probability, rollback
  duration and the severity rule itself are invented -- yours will differ.

  NOT SHOWN: on-call rotas, customer communication templates, regulatory
  breach notification, and the blameless review meeting itself (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's third column is the point of the section.** The fastest detector is also the noisiest; a 62% quiet-period
firing rate is how alerts get muted.

**Section 2 shows why the canary wins despite detecting later**: exposure multiplies, detection time adds.

**Section 3's five NO rows** are the changes that need a plan before they ship, not after.

**Section 5 is an argument for small deploys** stated in incident-response terms.

---

## 8. Common mistakes and troubleshooting

1. **Diagnosing before mitigating.** §5.3 — stop the harm, then understand it.
2. **Relying on user reports.** §7.1 — 17.5 hours, and only for the problems users notice.
3. **Alert thresholds never tested on quiet periods.** §7.1 — 62% false-alarm rate.
4. **Assuming every change is revertible.** §7.3 — half were not.
5. **Deleting the previous index/model once the new one passes.** Keep it through a soak period.
6. **Classifying severity by user count.** §7.4 — a cross-tenant leak is SEV1 at one user.
7. **Batching a dozen changes into one deploy.** §7.5 — twelve suspects.
8. **Reviews producing "be more careful".** §5.7 — produce control changes with owners and dates.
9. **No named commander.** Everyone debugs, nobody decides, nobody communicates.

| Symptom | Likely cause | Fix |
|---|---|---|
| Alerts are muted | Threshold too tight on small samples | Larger window, confidence bound, two-window rule |
| Rollback did not fix it | The change had one-way effects | Prepare reverse paths; keep previous artefacts |
| Nobody knew who could decide | No commander role or rollback authority | Name the roles; give on-call unilateral rollback |
| Cause never identified | Batched deploys, no run fingerprint | Small deploys; stamp requests with config hashes (L13) |
| Same incident recurs | Review produced advice, not controls | Gate, monitor or limit — with an owner and a date |

---

## 9. Security, privacy, reliability, cost

- **Security.** A security incident adds containment (revoke credentials, disable tools), evidence preservation, and a
  notification decision that is not the engineering team's alone (L10, L16).
- **Privacy.** Cross-boundary exposure is SEV1 regardless of volume. Preserve the audit records; they are the evidence for
  both the review and any notification (L06, L13).
- **Reliability.** Rollout size and detection are the two reliability levers you set in advance; both are cheap and both
  are usually skipped under launch pressure.
- **Cost.** Cost anomalies are incidents: a runaway agent loop is a SEV2 with a spend curve (M8-L15, M11-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which detector in §7.1 was fastest, and what did it cost?
2. How many bad answers did the 1% canary deliver, versus big bang?
3. List the five one-way doors from §7.3 and one preparation for each.
4. Why is a cross-tenant document leak SEV1?
5. How many innocent changes get reverted with a 12-change deploy?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Raise the alert threshold to 8% and report both TTD and false alarms.
2. Add a "two consecutive windows" rule to the hourly detector and measure the trade-off.
3. Add a change of your own to §7.3 and classify it.
4. Add two events to §7.4 and check whether the rule classifies them as you would.
5. Write your team's rollback criteria in the §5.3 format, including who may call it.

### Exercise 3 — Challenge (~60 min)

1. Run an incident drill: inject a regression behind a flag in a test environment and time TTD and TTM for real.
2. Build one quality monitor with a measured quiet-period false-alarm rate below 5%.
3. Write the reverse migration for a schema change you have pending, and test it.
4. Produce a review document for a past incident using §5.7's six headings, from audit records.
5. Add the resulting gate or monitor to the L12 suite, with an owner and a date.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l14).)*

**Q1.** What is the first action when a SEV1 is confirmed?

- A. Identify the change that caused it
- B. Notify affected customers
- C. Stop the harm, usually by rolling back
- D. Open a review document and start the timeline

**Q2.** In §7.1, how long did waiting for user reports take on average?

- A. 4.0 hours
- B. 17.5 hours
- C. 1.0 hour
- D. 24 hours

**Q3.** What did the false-alarm column reveal about the hourly alert?

- A. It never fired outside an incident
- B. It fired on 3% of quiet fortnights
- C. It detected slower than user reports
- D. It fired on 62% of quiet fortnights, which erodes trust in it

**Q4.** Why does a 5% canary harm fewer users despite detecting later?

- A. Canary traffic is routed to a more reliable model
- B. Exposure multiplies the harm while detection time only adds to it
- C. Canary users are internal and excluded from the count
- D. The base error rate is lower in small cohorts

**Q5.** Which of these is a one-way door?

- A. A decoding-parameter change
- B. A guardrail policy version bump
- C. A retrieval `k` change
- D. Invoices the agent has already emailed

**Q6.** What should be written at the same time as a forward schema migration?

- A. The reverse migration
- B. The incident review template
- C. The customer communication
- D. The updated model card

**Q7.** Why is "one tenant sees another tenant's documents" SEV1 with few users affected?

- A. Cross-tenant traffic is always high volume
- B. Severity is set by the kind of harm, not the number of users
- C. It always triggers a regulatory notification
- D. Isolation failures are irreversible by definition

**Q8.** In §7.5, how many innocent changes are reverted when a 12-change deploy is rolled back?

- A. Three
- B. Twelve
- C. Eleven
- D. None, if the guilty change is identified first

**Q9.** What is the purpose of the incident commander role?

- A. To decide and coordinate without also debugging
- B. To perform the rollback personally
- C. To approve the on-call engineer's actions
- D. To write the post-incident review

**Q10.** What should a post-incident review produce?

- A. An assessment of who made the error
- B. A summary circulated to leadership
- C. An estimate of revenue impact
- D. Control changes, each with an owner and a date

**Q11.** A change cannot be rolled back and a SEV2 is open. What is the mitigation?

- A. Fix forward as quickly as possible
- B. Wait for the next scheduled deploy window
- C. Mitigate at the boundary — flag off, read-only, route to humans
- D. Downgrade the severity since no rollback exists

**Q12.** Why keep the previous index after a rebuild passes its gates?

- A. So the switch can be reverted by pointing the alias back
- B. So both indexes can serve traffic simultaneously
- C. Because embeddings degrade over time
- D. To satisfy the retention policy for personal data

**Q13.** *(Written, rubric-graded.)* In under 150 words: your agent has sent 40 incorrect emails to customers over three
hours before anyone noticed. Describe your response in order, and the three controls you would add afterwards.

---

## 12. Revision notes

- **Detection has two costs**: user reports **17.5 h**; hourly alert **1.0 h** but **62%** false alarms in quiet
  fortnights; canary **4.0 h** at **3%**.
- **Blast radius = exposure × (TTD + TTM)**: **144 / 72 / 18 / 4** bad answers across big bang, 50%, 5%, 1%.
- **Half of changes are one-way doors** (**5/10** in the lab): re-embedding, migrations, sent emails, deletions,
  commitments.
- **Mitigate, then diagnose.** On-call may roll back alone; SEV1 rolls back immediately.
- **Severity by kind of harm**: a cross-tenant leak is SEV1 at one user.
- **Small deploys are an incident control**: 12 changes → **12 suspects, 11 innocent reverts, 3.7 bisect steps**.
- **Reviews produce controls with owners and dates**, and update the risk register (L04).

---

## 13. Completion checklist

- [ ] I have automated detection for quality and safety, with a measured quiet-period false-alarm rate.
- [ ] New changes roll out to a canary cohort before full traffic.
- [ ] I know which of my changes are one-way doors, and each has a prepared mitigation.
- [ ] Severity classification and rollback authority are written down before the incident.
- [ ] Deploys are small and independently revertible; each maps to a run fingerprint.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M10-L12 (gates the incident should have failed) and M10-L13 (audit records that build the timeline) `[STABLE]`
- M8-L11 (read-only vs state-changing), M8-L12 (idempotency) and M8-L10 (approval) — limiting irreversible action `[STABLE]`
- M10-L09 (telling users) and M10-L04 (risk register updates after review) `[STABLE]`
- M13-L14 (canary releases, reliability targets, runbooks) and M13-L12 (online monitoring) `[STABLE]`
- M11-L18 (CI/CD and rollback mechanics) and M11-L16 (CloudWatch alarms) `[STABLE]`

---

## 15. Next lesson

→ [M10-L15 — Model Cards and System Documentation](M10-L15-model-cards-documentation.md) turns everything recorded in
L02–L14 into the documents other people rely on: what this system is, what it is not, and how it was evaluated.
