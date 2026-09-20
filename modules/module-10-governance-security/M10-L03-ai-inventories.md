# M10-L03 — AI Inventories

| | |
|---|---|
| **Lesson ID** | M10-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M10-L02](M10-L02-intended-use-limitations-ownership.md) |

---

## 1. Learning objectives

1. **Discover** AI usage across a codebase from concrete signals, and state what a scan cannot tell you.
2. **Reconcile** what is running with what is registered: shadow systems, ghost entries and wrong details.
3. **Judge** inventory record quality: required fields, staleness, and what an out-of-date field invalidates.
4. **Compute** blast radius from a dependency graph — including components nobody registered.
5. **Use** risk tiers to turn an inventory into required work.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **AI inventory** | The authoritative list of AI systems an organisation runs, with owner, purpose, data, model and risk tier. |
| **Shadow AI** | AI use that exists in production but is not in the inventory. |
| **Ghost entry** | An inventory entry for something that no longer runs. |
| **Risk tier** | A classification (e.g. high / medium / low) that determines which artefacts are mandatory. |
| **Blast radius** | Everything affected when one shared dependency changes. |
| **Reconciliation** | Comparing discovered reality with the register, and resolving every difference. |

---

## 3. Plain-language explanation

### 3.1 The list comes first

Everything else in this module is per-system work: a risk register entry, an evaluation, a card, an incident plan. None
of it happens for a system nobody knows about. The inventory is the index that makes the rest possible, and the first
honest question it answers is *how much AI are we actually running?*

### 3.2 Asking is not enough; scanning is not enough either

§7.1 scans a synthetic codebase for five kinds of signal — provider SDK imports, calls to provider endpoints, model
identifiers, local ML libraries, and prompt assets — and finds AI in **7 of 8** components. §7.2 then reconciles that
with the inventory: **4** registered systems are really there, **3 are shadow** (in code, not in the inventory), and
**1 is a ghost** (registered, not in the code).

Both directions matter. Shadow systems have no owner and no artefacts. A ghost entry hides that a control you believe is
protecting something is protecting nothing.

### 3.3 Wrong details are worse than missing ones

Reconciliation also compares recorded details with reality. In §7.2, `hr-screening`'s inventory says
`anthropic.claude-3-sonnet` and the code says `claude-3-haiku`. A CV-screening system, in the highest risk tier, has been
evaluated — and its fairness argued — against a model it is not running.

### 3.4 Records rot, and dependencies bind

§7.3: one entry is missing two required fields and was last reviewed in November 2025; two more are past their review
date. §7.4 computes blast radius: the **Anthropic API** row covers three components, **two of which are not in the
inventory**; the shared prompt library covers three, one unregistered. A provider deprecating a model is a change to
every component in that row, including the ones nobody will think to check.

### 3.5 Tiering turns a list into work

§7.5 checks each system against the artefacts its tier requires. `hr-screening`, a high-tier system, is missing its
evaluation, its card and its subgroup analysis. The shadow systems have no tier at all — which is the real finding: they
were never assessed to *have* one.

---

## 4. Analogy

**An asset register for electrical equipment.** Facilities keeps a list of every appliance, who owns it, when it was last
tested, and which circuit it sits on. Two things break it: a team plugs in a heater nobody registered (shadow), and an
appliance is scrapped but stays on the list (ghost). When the electrician needs to isolate a circuit, the register's
accuracy is what determines whether the right people are warned — the blast-radius question.

### Where the analogy breaks

- **Appliances are visible; a model call is three lines in a file.** Discovery needs scanning, procurement records, egress
  logs and billing data — which is why §7.6 lists what code scanning cannot see.
- **A heater does the same thing each year; an AI system's behaviour changes when the provider updates a model.** The
  register has fields — model, provider, version — that go stale without anyone touching your code (M10-L13).

---

## 5. Detailed technical explanation

### 5.1 What an inventory entry holds

| Field | Why | Feeds |
|---|---|---|
| `id`, `name` | Stable reference | Everything |
| `owner` | Named accountable individual | L02, L14 |
| `purpose_ref` | Link to the intended-use statement | L02 |
| `provider`, `model` (and version) | What is actually running | L11, L13 |
| `data_classes` | What data it touches | L05, L06 |
| `environments` | Where it runs (prod, internal, pilot) | L12 |
| `tier` | Risk tier | This lesson, L04 |
| `last_review` | When this was last confirmed true | L02, L13 |
| `dependencies` | Providers, shared prompts, indexes | §5.4 |
| `artefacts` | Which governance artefacts exist | L04, L08, L12, L15 |

`[REAL, measured]` §7.3: 8/8 fields for two entries, 6/8 for one, and three entries past a six-month review threshold —
including a high-tier system reviewed in February.

### 5.2 Discovery signals

`[REAL, measured]` §7.1 found AI in 7 of 8 components using:

| Signal | Example |
|---|---|
| Provider SDK import | `from anthropic import Anthropic`, `import openai`, `boto3.client('bedrock-runtime')` |
| Provider endpoint | `fetch('https://api.anthropic.com/v1/messages')` |
| Model identifier | `claude-sonnet-5`, `gpt-4o-mini`, `anthropic.claude-3-haiku` |
| Local ML library | `sklearn`, `joblib`, `sentence_transformers`, `torch` |
| Prompt asset | A file containing "You are a … assistant" |

**What code scanning misses** — and where the rest of the inventory comes from:

- SaaS features with AI switched on by another department (procurement and expense records);
- models embedded in vendor products (supplier questionnaires, L11);
- staff use of public chatbots (egress logs, policy);
- notebooks, spreadsheets and scripts on laptops;
- pilots that never reached a repository.

A scan also cannot tell you **whether a use matters**: `ops-dashboard` summarising internal metrics and `hr-screening`
ranking candidates look similar in code and differ completely in consequence. Discovery produces candidates; people
assign tiers.

### 5.3 Reconciliation

`[REAL, measured]` §7.2: 4 matched, **3 shadow**, **1 ghost**, and **1 of 2 checkable model fields wrong**.

Resolve every difference, with a rule for each class:

| Finding | Action |
|---|---|
| Shadow system | Register it, assign an owner and tier within a fixed window, or switch it off |
| Ghost entry | Confirm decommissioning, record the date, and remove the controls that only existed for it |
| Wrong model or provider | Correct the record **and** re-check anything evaluated against the old value (L12, L13) |
| Missing fields | Assign to the owner with a deadline; block tier-required artefacts until filled |

The mismatch check in §7.2 skips entries with no hosted model id (`billing-classifier`, `docs-search`), which is worth
noticing: **automated reconciliation has blind spots of its own**, and reporting what it skipped is part of reporting
what it found.

### 5.4 Dependencies and blast radius

`[REAL, measured]` §7.4:

| Dependency | Components affected | Not in the inventory |
|---|---|---|
| Anthropic API | 3 | 2 |
| shared-prompt-lib | 3 | 1 |
| vector-index | 2 | 0 |
| OpenAI API | 1 | 1 |

Blast radius answers questions you will be asked under time pressure: *a provider is deprecating a model in 30 days —
what breaks?*; *the shared prompt library changed — what needs re-evaluating?*; *this index is being rebuilt — whose
answers change?* Without dependency edges in the inventory, each of those becomes a manual hunt, and the unregistered
components are found last or not at all.

### 5.5 Tiering

Tier by **consequence**, not by technology: what decision does it affect, whose data does it touch, can a person
intervene, how reversible is the outcome? A reasonable starting rubric:

| Tier | Typical criteria | Required artefacts |
|---|---|---|
| High | Affects people's access to money, jobs, health, housing; personal or special-category data; low reversibility | Risk register entry, evaluation, subgroup evaluation, card, named oversight |
| Medium | Internal decisions with human review; business data | Risk register entry, evaluation |
| Low | Assistive, easily reversible, no personal data | Risk register entry |

`[REAL, measured]` §7.5: `hr-screening` (high) is missing **card, evaluation and subgroup evaluation**;
`support-assistant` (high) is missing its subgroup evaluation; `legacy-chatbot` has no evaluation. Shadow systems have
no tier at all.

This is what makes an inventory more than a spreadsheet: the tier says which of the following lessons are **mandatory**
for that system, and the missing-artefact list is the backlog.

### 5.6 Keeping it current

- **Register at creation.** Make an inventory entry part of the definition of done for any AI feature, with owner and tier.
- **Re-run discovery on a schedule**, in CI if possible, and open a ticket per difference.
- **Re-review on change events** (M10-L02): model swap, new data source, new automated action, new user population.
- **Publish the gaps.** The list of shadow systems and missing artefacts is the useful output; a green dashboard nobody
  challenges usually means discovery is too narrow.

### 5.7 Assumptions and limitations

- The "codebase" is twelve snippets and the signals are regular expressions; real scanning needs dependency manifests,
  egress and billing data, and still misses non-code use.
- Tier rubrics vary by organisation and sector; the one above is a starting point, not a standard.
- Nothing here is a legal classification of risk; frameworks and law define their own categories (L16).

---

## 6. Worked example — the inventory that was complete, on paper

**The situation.** A mid-sized insurer built an AI register after a board request. Twelve systems were listed, each with
an owner and a tier; the dashboard was green. Three months later, a customer complained that a "fraud triage" score had
delayed their claim, and the complaint reached the regulator's attention.

**What the investigation found.**

1. The fraud triage model **was not in the register**. It had been built inside the claims platform by a data engineer
   and shipped as part of a normal release — §7.2's shadow case.
2. The register's `claims-summariser` entry recorded a model the team had **stopped using six months earlier**. Its
   evaluation, and the fairness section of its card, referred to the old model — §7.2's mismatch case.
3. Two registered systems shared a **prompt library** that a third, unregistered service also used. A change to it a
   month earlier had been tested against one system only — §7.4's blast-radius case.
4. The register had no **dependency** or **data-class** fields, so the question "which systems touch claimant health
   data?" required a week of interviews.

| # | Cause | Fix |
|---|---|---|
| 1 | Registration was voluntary and manual | Registration in the definition of done; scheduled discovery scans; reconcile every difference |
| 2 | Fields never re-confirmed | Review on change events; invalidate evaluations when the model field changes |
| 3 | No dependency edges | Record providers, shared prompts and indexes; compute blast radius before changes |
| 4 | Minimal schema | Add data classes, environments, dependencies and artefact status; tier drives required artefacts |

**The general rule.** **An inventory's value is the differences it surfaces, not the rows it contains.** A register that
never produces a reconciliation finding is not being checked against reality.

---

## 7. Practical activity

**File:** [`labs/m10/l03_ai_inventory.py`](../../labs/m10/l03_ai_inventory.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l03_ai_inventory.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. DISCOVERY: WHAT IN THE CODEBASE USES A MODEL?
============================================================================
  billing-classifier   AI: local ML model
  docs-search          AI: local ML model, provider endpoint
  hr-screening         AI: model identifier, provider SDK
  intranet-bot         AI: provider SDK, provider endpoint
  marketing-copy       AI: model identifier, provider SDK
  ops-dashboard        AI: model identifier, provider SDK
  payroll              no AI signal found
  support-assistant    AI: model identifier, prompt asset, provider SDK

  7 of 8 components show at least one signal.
  Note what a scan cannot tell you: whether the use is important, what data it
  touches, or whether anyone owns it. Discovery starts the conversation.

============================================================================
2. RECONCILIATION: SHADOW SYSTEMS AND GHOST ENTRIES
============================================================================
  registered and found in code : 4  ['billing-classifier', 'docs-search', 'hr-screening', 'support-assistant']
  SHADOW (in code, not in the inventory): 3  ['intranet-bot', 'marketing-copy', 'ops-dashboard']
  GHOST (in the inventory, not in code) : 1  ['legacy-chatbot']

  recorded model does not match the code: 1  (checked 2 of 4; skipped billing-classifier, docs-search -- no hosted model id recorded)
    hr-screening         inventory says 'anthropic.claude-3-sonnet', code says 'claude-3-haiku'

  Shadow systems are the reason inventories are built by SCANNING as well as
  asking. Ghosts matter too: a decommissioned entry hides that nothing is
  running, and an out-of-date model field invalidates every evaluation result
  recorded against it.

============================================================================
3. RECORD QUALITY
============================================================================
  support-assistant    8/8 fields   current
  billing-classifier   8/8 fields   current
  docs-search          6/8 fields   missing: purpose_ref, model; last reviewed 2025-11-02
  hr-screening         8/8 fields   last reviewed 2026-02-17
  legacy-chatbot       8/8 fields   last reviewed 2024-09-30

  An inventory nobody maintains becomes a list of things that were once true.
  Tie each entry's review to the system's own change events (M10-L02).

============================================================================
4. DEPENDENCIES: BLAST RADIUS OF ONE CHANGE
============================================================================
  Anthropic API            affects 3 component(s): intranet-bot, ops-dashboard, support-assistant
                           of which not in the inventory: intranet-bot, ops-dashboard
  shared-prompt-lib        affects 3 component(s): hr-screening, marketing-copy, support-assistant
                           of which not in the inventory: marketing-copy
  vector-index             affects 2 component(s): docs-search, support-assistant
  OpenAI API               affects 1 component(s): marketing-copy
                           of which not in the inventory: marketing-copy

  A provider deprecating a model, or a shared prompt library changing, is a
  change to every component in that row -- including the ones nobody registered.

============================================================================
5. TIERING: DOES EACH SYSTEM HAVE THE ARTEFACTS ITS TIER REQUIRES?
============================================================================
  support-assistant    tier=high   missing artefacts: subgroup_eval
  billing-classifier   tier=medium missing artefacts: none
  docs-search          tier=low    missing artefacts: none
  hr-screening         tier=high   missing artefacts: card, evaluation, subgroup_eval
  legacy-chatbot       tier=medium missing artefacts: evaluation

  shadow systems have NO tier and NO artefacts at all: intranet-bot, marketing-copy, ops-dashboard
  Tiering is how an inventory turns into work: the tier decides which artefacts
  from the rest of this module are mandatory (M10-L04, L08, L12, L15).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count, match and blast-radius set above is computed from the
  encoded codebase, inventory and dependency graph in this file.

  ILLUSTRATIVE: the 'codebase' is twelve short snippets, and the signals are
  regular expressions -- a real scan needs dependency manifests, network egress
  logs, cloud billing data and procurement records to catch what code misses.

  NOT SHOWN: SaaS features bought by other departments, models embedded in
  vendor products, and staff use of public chatbots -- all of which belong in a
  complete inventory and none of which appear in your repositories.

Done.
```

### 7.3 Reading the result

**Section 2 is the whole lesson in four lines**: matched, shadow, ghost, wrong details.

**Section 4's second column** — components affected but not in the inventory — is what makes shadow AI operationally
dangerous rather than merely untidy.

**Section 5 turns the register into a backlog.** "Missing artefacts" is a work list with owners attached.

---

## 8. Common mistakes and troubleshooting

1. **Building the inventory by asking teams once.** §5.2 — scanning found three systems nobody declared.
2. **Scanning code only.** §5.2 — SaaS, vendor-embedded models and staff chatbot use are invisible there.
3. **Treating the inventory as a compliance artefact rather than an operational index.** §5.4.
4. **No dependency edges.** §5.4 — blast radius becomes a manual hunt.
5. **Leaving ghost entries in place.** §5.3 — they hide missing systems and stale controls.
6. **Tiering by technology** ("LLM = high") instead of by consequence. §5.5.
7. **Not recording what reconciliation skipped.** §5.3 — unchecked is not the same as clean.

| Symptom | Likely cause | Fix |
|---|---|---|
| A system in production has no owner | Shadow AI | Scheduled discovery + registration at creation |
| Evaluation results do not match live behaviour | Model field out of date | Reconcile details; invalidate old evaluations |
| "Which systems use provider X?" takes days | No dependency edges | Record dependencies per entry |
| High-risk systems lack evaluations | Tier not linked to required artefacts | Make tier drive a mandatory artefact list |
| The register is always green | Discovery too narrow, or differences not reported | Publish shadow and gap counts |

---

## 9. Security, privacy, reliability, cost

- **Security.** Unregistered systems are unpatched, unmonitored and unowned; they are also the ones with credentials
  nobody rotates (M9-L12).
- **Privacy.** `data_classes` is the field that answers "where is personal data being processed?" — the question that
  starts every deletion or breach response (L06).
- **Reliability.** Blast radius is what makes provider deprecations survivable (L14, M13-L08).
- **Cost.** Inventories surface duplicate systems: §7.1's three near-identical summarisation uses are a consolidation
  opportunity as well as a governance gap.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name five discovery signals and one thing each would miss.
2. Define shadow AI and ghost entry, and say why each is a problem.
3. Which field, when wrong, invalidates an evaluation?
4. Compute the blast radius of `shared-prompt-lib` from §7.4 and say who you would tell.
5. Which artefacts does a high-tier system require in §5.5's rubric?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add two components to `CODEBASE` — one clearly AI, one borderline — and see what the scan says.
2. Add a `dependencies` field to the inventory records and compute blast radius from the register rather than a separate
   graph.
3. Write the reconciliation report you would send to owners: one section per finding class, with deadlines.
4. Add an `environments` check: flag any prod system whose entry lists only `pilot`.
5. Re-tier the five registered systems using §5.5's rubric and justify any change.

### Exercise 3 — Challenge (~50 min)

1. Write a real scanner for a repository you have access to (imports, endpoints, model ids, prompt files) and report
   candidates — without recording anything sensitive.
2. Design the intake form for registering a new AI system in under five minutes, and say which fields you would
   auto-fill.
3. Propose how to discover SaaS AI features from expense data, and what false positives you expect.
4. Model the deprecation of one provider model in 30 days: which systems, which owners, what evidence you need, what you
   would do first.
5. Argue for or against making the inventory public inside the company, including the shadow list.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l03).)*

**Q1.** What is shadow AI?

- A. A model that runs only in staging environments
- B. An inventory entry for a retired system
- C. A model whose weights are not published
- D. AI use in production that is not in the inventory

**Q2.** In §7.2, how many shadow systems did reconciliation find?

- A. 1 shadow system
- B. 3 shadow systems
- C. 4 shadow systems
- D. 7 shadow systems

**Q3.** Why does a ghost entry matter?

- A. It inflates the organisation's licence costs
- B. It cannot be removed without board approval
- C. It hides that a control now protects nothing
- D. It blocks new systems from being registered

**Q4.** `hr-screening`'s inventory records a different model from the code. What does that invalidate?

- A. Evaluations and fairness claims recorded against the old model
- B. The system's access to its data sources
- C. The provider's contractual commitments
- D. The owner's accountability for the system

**Q5.** Which of these would a code scan typically miss?

- A. A `from anthropic import Anthropic` line
- B. A SaaS feature enabled by another department
- C. A hard-coded model identifier in config
- D. A prompt file in the repository

**Q6.** In §7.4, how many components depend on the Anthropic API, and how many of those are unregistered?

- A. 2 components, 1 unregistered
- B. 3 components, 0 unregistered
- C. 1 component, 1 unregistered
- D. 3 components, 2 unregistered

**Q7.** What question does blast radius answer?

- A. How much compute a model consumes per request
- B. How many users a system serves at peak
- C. What breaks when a shared dependency changes
- D. How far an attacker can move after a breach

**Q8.** On what basis should a system be tiered?

- A. The consequence of its decisions and the data it touches
- B. Whether it uses a large language model
- C. The size of the team that maintains it
- D. The cloud spend it generates per month

**Q9.** In §7.5, which artefacts was `hr-screening` missing?

- A. Only its subgroup evaluation
- B. Only its risk register entry
- C. Nothing; it was complete
- D. Card, evaluation and subgroup evaluation

**Q10.** Why does the lab report which entries its mismatch check skipped?

- A. Skipped entries are automatically compliant
- B. Skipping indicates the system is decommissioned
- C. Unchecked is not the same as clean
- D. The check is only valid for high-tier systems

**Q11.** What makes an inventory operational rather than decorative?

- A. Board-level approval of the register
- B. Reconciliation findings and a tier-driven backlog
- C. A published count of AI systems
- D. A single spreadsheet owner

**Q12.** In §6, why did "which systems touch claimant health data?" take a week?

- A. The register had no data-class field
- B. The register was stored offline
- C. Health data was not considered personal data
- D. The systems were all owned by one team

**Q13.** *(Written, rubric-graded.)* In under 150 words: describe how you would build an AI inventory for an
organisation that believes it has "about five" AI systems, and what you would expect to find.

---

## 12. Revision notes

- **Discovery signals:** provider SDKs, provider endpoints, model ids, local ML libraries, prompt assets — found AI in
  **7/8** components. Scans miss SaaS, vendor-embedded models and staff chatbot use.
- **Reconciliation:** 4 matched, **3 shadow**, **1 ghost**, **1 wrong model field** (high-tier CV screening).
- **Record quality:** required fields plus a review date; stale or missing fields invalidate the artefacts that cite them.
- **Blast radius:** Anthropic API → 3 components, 2 unregistered; shared prompt library → 3, 1 unregistered.
- **Tiering by consequence** drives mandatory artefacts; missing-artefact lists are the backlog; shadow systems have no
  tier at all.
- **An inventory's value is the differences it surfaces.**

---

## 13. Completion checklist

- [ ] I can scan for AI usage and say what the scan cannot see.
- [ ] I can reconcile discovery against a register and classify each difference.
- [ ] I keep model, provider, data-class and review fields current.
- [ ] I record dependencies and can compute blast radius.
- [ ] I tier by consequence and use the tier to require artefacts.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M10-L02 (intended use and ownership) — the per-system statement each entry points to `[STABLE]`
- M10-L13 (versioning and auditability) — why an out-of-date model field invalidates evidence `[STABLE]`
- NIST AI RMF, *Map* function — context and categorisation of AI systems; see M10-L16 `[UNVERIFIED — checked in M10-L16]`
- ISO/IEC 42001 (AI management systems) — requires a documented set of AI systems and responsibilities `[UNVERIFIED]`

---

## 15. Next lesson

→ [M10-L04 — Risk Registers and Risk Assessment](M10-L04-risk-registers.md) takes the tiered list and asks, per system:
what could go wrong, how likely is it, how bad would it be, and what are we doing about it?
