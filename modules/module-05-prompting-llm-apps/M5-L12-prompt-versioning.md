# M5-L12 — Prompt Versioning and Regression Testing

| | |
|---|---|
| **Lesson ID** | M5-L12 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L18](../module-02-python-foundations/M2-L18-logging-testing.md) |

---

## 1. Learning objectives

1. **Define** a prompt artefact as everything that can change model behaviour — template, model,
   parameters and tool schema — not the template text alone.
2. **Distinguish** exact-match from property-based assertions, and explain why exact-match
   systematically underreports a good prompt's true quality.
3. **Determine** how many samples per golden case a regression test needs before a pass-rate drop is
   trustworthy rather than noise.
4. **Design** a CI gate keyed to the whole artefact's fingerprint, not a template-file diff.
5. **Version** a prompt artefact so that rollback and audit are both one lookup, not an investigation.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Prompt artefact** | The versioned unit: template + model id + parameters + tool schema, treated as one thing. |
| **Fingerprint** | A hash over every field that can change model behaviour, used to detect any change to the artefact. |
| **Golden case** | A fixed input paired with a checkable expectation, used to catch regressions (M2-L18). |
| **Exact-match assertion** | Passes only if output is byte-identical to a stored string. |
| **Property assertion** | Passes if the output satisfies a stated rule (category, schema, bound), regardless of exact wording. |
| **Prompt regression** | A golden case whose true pass rate drops after an artefact change. |
| **False alarm** | A gate reporting a regression in an artefact that did not actually get worse. |
| **Catch rate** | The fraction of real regressions a gate actually detects. |
| **Rollback** | Reverting to a previously kept artefact version. |

---

## 3. Plain-language explanation

### 3.1 A prompt is not a string

Most codebases version code and leave the prompt as a string constant or a line in a config file. That
works until someone changes the model, the temperature, `max_tokens`, or a tool's schema — none of which
touch the string — and the system's behaviour changes anyway, with no version bump and no record of why.

**Treat the prompt as an artefact**: the template plus everything that co-determines behaviour with it.
Change any field, and it is a new version, whether or not the wording moved.

### 3.2 Prompt regression testing is not code regression testing

A unit test for ordinary code expects one exact answer, because the code is deterministic. An LLM is
not: the same artefact can produce differently-worded — sometimes differently-correct — output on two
runs. **Exact-match assertions, borrowed straight from code testing, quietly become the wrong tool** —
§7.2 measures a case where a prompt that is truly right 95% of the time passes an exact-match suite only
67% of the time, because it is also being tested on formatting it was never asked to hold constant.

### 3.3 A single test run is not evidence

Because output is stochastic, a golden suite run once can look fine when the prompt has regressed, or
look broken when it has not. §7.3 turns this into a number: at one sample per case, a healthy prompt
trips a regression alert **19% of the time**, and a genuinely regressed one is caught only **63% of the
time**. Neither number is acceptable for a gate that blocks deploys. **How many samples you need is a
question with a measurable answer, not a guess.**

### 3.4 The gate has to watch the artefact, not the file a human remembers to check

A CI check that diffs the prompt's template file will not notice a model swap or a parameter change,
because neither touches that file. §7.4 replays exactly this as an incident: the same change that
drops true quality from 90% to 75% produces an **empty template diff** and an **unchanged fingerprint
check would have caught it** — two gates, one real change, one silent failure.

---

## 4. Analogy

**A recipe card in a professional kitchen.** The card lists ingredients and steps, but a dish also
depends on the oven, the specific brand of an ingredient, and altitude — none written on the card. Swap
the oven for a cheaper model and keep the card unchanged, and the dish changes with no line on the card
to explain why.

A **tasting panel** before service is the regression suite: taste a sample of dishes against a
reference, allow for the ordinary variation between platings (surface variation, §7.2), and flag the
ones that are actually wrong (a real quality drop) rather than merely plated differently. One taste of
one dish, though, tells a chef very little — a panel that samples several plates of the same dish is
what makes "this batch is off" a finding rather than a guess.

### Where the analogy breaks

- **A human taster brings judgement a fixed rule cannot.** A property assertion can check "is this the
  right category," but genuinely open-ended quality still needs something closer to a taster — an
  LLM-graded assertion, a heavier tool covered in M5-L18 and M13-L13.
- **A kitchen tastes a handful of plates before service.** Your suite can run thousands of golden cases,
  many times each, for a cost measured in cents — §7.3's whole argument only works because sampling more
  is cheap.
- **The oven change is obvious to a chef who walks into the kitchen.** A model or parameter change in a
  config file is invisible to a gate that only reads the recipe card — which is precisely §7.4's point.

---

## 5. Detailed technical explanation

### 5.1 The artefact and its fingerprint

`[REAL]` §7.1 defines a `PromptArtefact` — template, model, temperature, `max_tokens`, tool schema — and
hashes every behaviour-affecting field:

```python
@dataclass(frozen=True)
class PromptArtefact:
    id: str
    version: str
    template: str
    model: str
    temperature: float
    max_tokens: int
    tool_schema: tuple

    def fingerprint(self) -> str:
        payload = json.dumps({
            "template": self.template, "model": self.model,
            "temperature": self.temperature, "max_tokens": self.max_tokens,
            "tool_schema": self.tool_schema,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]
```

| Change | Template diff? | Fingerprint changed? |
|---|---|---|
| Wording edited (v1 → v2) | **True** | **True** — expected |
| Model + `max_tokens` changed, wording untouched (v1 → v3) | **False** | **True** |

**The second row is the one that matters.** A template-only diff reports nothing for v3; the fingerprint
changes because it is computed over the fields that can actually change what the model does, not only
the one a human is likely to remember to check.

### 5.2 Exact-match vs property assertions

`[REAL arithmetic on a MOCK model]` §7.2 simulates a categorizer whose true correctness is a known,
fixed number (`quality`), and separately simulates harmless formatting drift on otherwise-correct
answers. Two ways to grade the same output:

| Assertion | Checks | Fails on |
|---|---|---|
| Exact-match | Byte-identical to a stored string | Any correct answer worded, spaced or ordered differently |
| Property | A stated rule (e.g. `category == expected`) | Only genuinely wrong answers |

| Version (true quality) | Exact-match rate | Property rate |
|---|---|---|
| Current, q=0.95 | **67%** | **98%** |
| Cost-cut, q=0.75 | 50% | 73% |

**Read the top row.** A prompt that is right 95% of the time passes an exact-match suite barely two
times in three, because a third of its correct answers are formatted differently from the one string
stored as "the" golden answer. **Exact-match is measuring formatting stability, not correctness** — use
it only where the output truly must be byte-identical (a fixed enum value, a schema-validated field),
and use property assertions everywhere output has legitimate surface variation.

### 5.3 Sizing the suite

`[REAL simulation]` §7.3 asks the actual operational question: at a given number of samples per golden
case, how often does the suite cry wolf on a healthy prompt, and how often does it catch a real drop
from 90% to 75%?

| Samples/case | Total draws | False-alarm rate | Catch rate |
|---|---|---|---|
| 1 | 8 | **19%** | 63% |
| 5 | 40 | 10% | 91% |
| 10 | 80 | 5% | **98%** |
| 30 | 240 | **0%** | **100%** |

**At one sample per case the suite is close to useless as a gate** — it is wrong in both directions at
once. By ten samples per case, both numbers are near their ideal ends. **The number of samples a
regression test needs is not a stylistic choice; it is the same kind of sizing question any statistical
test requires, and it has a measurable answer for your own quality gap and your own risk tolerance.**

### 5.4 Gating on the artefact, not the file

`[REAL logic]` §7.4 defines two gate functions and runs both on the same change:

```python
def gate_by_text_diff(old, new): return old.template != new.template
def gate_by_fingerprint(old, new): return old.fingerprint() != new.fingerprint()
```

| Gate | Re-runs the suite on v1 → v3? |
|---|---|
| `gate_by_text_diff` | **False** |
| `gate_by_fingerprint` | **True** |

**The text-diff gate ships the change with zero golden cases re-run.** §5.3's numbers say ten samples
per case would have caught this cleanly — but a suite that never runs catches nothing. **Fingerprint the
whole artefact, and gate on that**, not on whichever file happens to be the one a reviewer's eye lands
on.

### 5.5 Keep every version

Once an artefact has a version and a fingerprint, two things follow almost for free:

- **Rollback is a lookup, not a rebuild.** If v3 regresses in production, reverting to v1 means pointing
  at a stored version, not reconstructing what v1's exact configuration was from memory or git
  archaeology.
- **Every historical output is attributable.** Tag outputs with the fingerprint that produced them, and
  "what changed between the output we liked and the one we didn't" becomes a diff between two known
  artefacts, not a guess (M5-L10 §5.6 makes the same argument for conversation state; M10-L13 generalises
  it to full audit trails).

### 5.6 Assumptions and limitations

- §7.2 and §7.3's "quality" and "surface variation" are chosen simulation parameters, not measurements of
  any real model. Measure your own golden set's history before setting a threshold.
- §7.3's false-alarm and catch rates are specific to the stated 90%/75% gap and 85% threshold. Recompute
  for your own numbers — the *method* (simulate, then count) transfers; the specific rates do not.
- Real prompt output is not always independent draw-to-draw the way the simulation assumes — a model
  having a bad day can correlate errors across cases in ways this lab does not model.
- This lesson stops at property assertions. Open-ended output that needs semantic judgement requires an
  LLM-graded assertion, with its own cost and reliability trade-offs — M5-L18, M13-L13.

---

## 6. Worked example — the cost-cut that shipped with an empty diff

**The system.** A support-ticket categorizer (the same shape as Project 5) has run in production for
months on artefact v1: a fixed template, a specific model, `temperature=0`, `max_tokens=300`. Its golden
suite is green.

**The change.** Chasing a cost-reduction target (M5-L15's territory), an engineer swaps the model to a
cheaper one and lowers `max_tokens` to 120. The prompt template file is not touched. The pull request's
diff is a single line in a config file; the review is quick, because "the prompt didn't change."

**What actually happened, measured.** §7.1's fingerprint for this exact change (v1 → v3) differs, because
model and `max_tokens` are part of the artefact. §7.2's simulation of the same change shows true quality
falling from 95% to 75% — the cheaper model handles the categorization task measurably worse, and the
shorter `max_tokens` occasionally truncates the JSON before the category field closes.

**Why nobody caught it before deploy.** The CI gate ran `git diff` against the template file only. That
diff was empty, so the golden suite never re-ran. §7.4 states this exactly: `gate_by_text_diff` returns
`False` for this change; `gate_by_fingerprint` returns `True`.

**How it surfaced instead.** Two days later, a downstream team notices a rise in tickets mis-routed to
the wrong queue. Tracing it back costs far more than re-running an eight-case suite would have — and
during the investigation, nobody can immediately answer "what changed," because the change that mattered
left no trace in the file everyone was watching.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The versioned unit was the template text; model and `max_tokens` were "just config" | A behaviour-changing edit produced an empty diff |
| 2 | The CI gate watched a file, not the artefact | The golden suite never ran on the change that needed it most |
| 3 | No fingerprint or version id tied production outputs back to a specific configuration | The regression was found by symptom, days later, instead of by gate, before merge |

### The fix

**Fingerprint the whole artefact** (§5.1) and gate every deploy on that fingerprint changing, not on a
template diff. **Re-run the golden suite at a sized sample count** (§5.3 — ten samples per case would
have caught a 95%→75% drop with a 98% catch rate and a 5% false-alarm rate) before any fingerprint change
reaches production. **Tag every stored version**, so that if this ships anyway, rollback is "point back
at v1," not a reconstruction effort.

**The general rule.** **If changing it can change the output, it is part of the prompt version — not
"config," not an implementation detail, not something a template diff will show you.**

---

## 7. Practical activity

**File:** [`labs/m5/l12_prompt_versioning.py`](../../labs/m5/l12_prompt_versioning.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l12_prompt_versioning.py
```

Section 1 and section 4's gate logic are real, deterministic code — hashing and diffing, no model
involved. Sections 2 and 3 use a seeded mock model to make exact-match brittleness and sampling noise
exactly measurable.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. A PROMPT ARTEFACT IS MORE THAN ITS TEXT
============================================================================
  Same logical prompt, three artefact states:

  version           template changed?   model              max_tok   fingerprint
  1.4.0             n/a                 claude-sonnet-5        300  a6af315bff54
  1.5.0             True                claude-sonnet-5        300  8f8db9b7d95d
  1.4.0-cost-cut    False               claude-haiku-4-5       120  6e776bf9cd70

  v1 -> v2: template text changed (True), fingerprint changed (True). Expected.
  v1 -> v3: template text changed (False), fingerprint changed (True).

  v3's template is byte-identical to v1's. A tool that only diffs the
  template file sees NOTHING. The fingerprint -- computed over the
  model, temperature, max_tokens and tool schema as well -- changes
  anyway, because all four can change what the model actually does.

============================================================================
2. EXACT-MATCH TESTS FORMATTING; PROPERTY TESTS TEST CORRECTNESS
============================================================================
  8 golden cases. Surface variation (harmless formatting drift on an
  otherwise-correct answer): 35%.

  v1 current  (q=0.95)
    case  expected    got           exact  property
    c1    billing     billing        PASS      PASS
    c2    technical   account        fail      fail
    c3    account     account        PASS      PASS
    c4    other       other          PASS      PASS
    c5    billing     billing        PASS      PASS
    c6    technical   technical      PASS      PASS
    c7    account     account        fail      PASS
    c8    other       other          PASS      PASS
    single-run pass rate: exact-match 6/8, property 7/8

  v3 cost-cut (q=0.75)
    case  expected    got           exact  property
    c1    billing     billing        PASS      PASS
    c2    technical   account        fail      fail
    c3    account     account        PASS      PASS
    c4    other       other          fail      PASS
    c5    billing     billing        PASS      PASS
    c6    technical   technical      PASS      PASS
    c7    account     account        PASS      PASS
    c8    other       billing        fail      fail
    single-run pass rate: exact-match 5/8, property 6/8

  Averaged over 40 simulated runs per case (a stable estimate,
  not one draw):

  version                   exact-match rate   property rate
  v1 current  (q=0.95)                  67%             98%
  v3 cost-cut (q=0.75)                  50%             73%

  Read the current version's row: its TRUE correctness is 95% by
  construction, but exact-match reports far less, because it fails
  every correct answer that happens to be formatted differently from
  the stored golden string. Exact-match is measuring formatting
  stability, not the thing you actually care about. Property
  assertions -- 'is the category right', ignoring surface form --
  track true quality far more closely.

============================================================================
3. HOW MANY SAMPLES DOES A REGRESSION NEED?
============================================================================
  True property-pass rate: 90% (current) vs 75% (regressed). Alert threshold: observed suite rate < 85%.
  8 golden cases, 500 simulated suite runs per row.

   samples/case  total draws   false-alarm rate  catch rate
              1            8                19%         63%
              5           40                10%         91%
             10           80                 5%         98%
             30          240                 0%        100%

  At 1 sample/case (8 draws total) the suite is a noisy coin flip on
  BOTH questions: it cries wolf on a healthy prompt and misses a real
  drop from 90% to 75% often enough to be useless as a gate. More
  samples per case make both numbers do what you want: false alarms
  fall toward zero and the catch rate rises toward one. A single run
  of your golden set is not evidence. Decide your samples/case and
  your threshold BEFORE you need them, the same way you would size
  any other statistical test.

============================================================================
4. THE INCIDENT: A GATE THAT ONLY READS THE TEMPLATE FILE
============================================================================
  Same v1 -> v3 change as section 1: model swapped to cut cost,
  max_tokens lowered, template untouched. Two CI gates, one change:

  gate                           re-runs the golden suite?
  gate_by_text_diff(v1, v3)                          False
  gate_by_fingerprint(v1, v3)                         True

  The text-diff gate ships v3 without a single golden case re-run,
  because its diff of the template file is empty. Section 2 showed
  what v3's real property-pass rate is: 75%, against v1's
  90%. Section 3 showed that gap is easily caught at 10
  samples/case -- a suite that never ran cannot catch anything.

  The fingerprint gate re-runs the suite because it hashes every
  field that can change model behaviour, not only the one file a
  human is likely to remember to check.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1's hashing and diffing, and the CI-gate logic in
  section 4 -- both are exact, deterministic code with no LLM in the
  loop. Sections 2 and 3's ARITHMETIC is real: exact counts and rates
  from many simulated trials.

  MOCK: sections 2 and 3's model. 'Quality q' standing in for a real
  model's true accuracy, and the surface-variation rate, are chosen
  parameters, not measurements of any real model or provider.

  ILLUSTRATIVE: the 90%/75% quality gap and the 0.85 threshold. Pick
  your own from your own golden set's history before relying on a gate.

  NOT SHOWN: an LLM-graded assertion (semantic similarity, a judge
  model) for outputs too open-ended for a property check. That is a
  heavier tool with its own failure modes -- see M5-L18 and M13-L13.

Done.
```

### 7.3 Reading the result

**Section 1 makes the disguise literal.** v1 and v3 share an identical template — a template diff shows
nothing — yet their fingerprints differ, because the fingerprint covers model and `max_tokens` too. This
is the single fact the rest of the lab depends on.

**Section 2 quantifies a trap most teams fall into once.** A prompt that is genuinely correct 95% of the
time (its measured property rate, 98%, confirms the simulation is close to its target) passes an
exact-match suite only **67%** of the time. Every one of those "failures" is a false signal about
formatting, not correctness. Property assertions track the true number far more closely — the gap
between 67% and 98% is the cost of using the wrong assertion type.

**Section 3 is the number most regression suites never compute.** At one sample per golden case, the
suite is nearly a coin flip in both directions: **19% false-alarm, 63% catch rate**. Nobody would accept
those odds from a monitoring system they were told about explicitly — yet a single-run golden suite has
exactly those odds, silently. By ten samples per case both numbers are near their ideal ends. **Decide
your sample count by simulating your own quality gap**, the way §7.3 does here.

**Section 4 closes the loop.** The exact change from section 1, replayed as a real gate decision:
text-diff gating ships it silently; fingerprint gating catches it. Nothing here is subtle once the
artefact is defined correctly — the entire fix is asking the gate to look at the right thing.

---

## 8. Common mistakes and troubleshooting

1. **Treating the prompt template as the whole prompt.** Model, parameters and tool schema are part of
   it too (§5.1).
2. **Gating CI on a template-file diff.** Fingerprint the artefact instead (§5.4).
3. **Using exact-match assertions on free-text or loosely-formatted output.** Use property assertions;
   reserve exact-match for genuinely fixed values.
4. **Trusting a single golden-suite run.** §7.3: one sample per case is close to useless as a gate.
5. **Picking a sample count and threshold without simulating them first.** Both interact; size them
   together against your own measured quality gap.
6. **Overwriting the previous prompt version instead of keeping it.** Rollback requires the old version
   to still exist.
7. **Not tagging outputs with the artefact version that produced them.** Makes later "what changed"
   investigations far slower than a lookup.
8. **Bumping the model "just to save cost" without re-running the golden suite.** §6, exactly.
9. **Never growing the golden set.** A suite that never changes only proves you haven't broken what it
   already tests.
10. **Assuming temperature 0 makes output deterministic across providers.** Some providers do not
    guarantee this. `[UNVERIFIED — check yours]`.

| Symptom | Likely cause | Fix |
|---|---|---|
| Golden suite is green, production quality drops | Gate watched the wrong file, or too few samples/case | Fingerprint the artefact; size the suite (§5.3, §5.4) |
| Suite flags a regression that isn't real | Too few samples/case | Increase samples/case; recompute the false-alarm rate |
| Can't explain why an old output looked different | No version tag on stored outputs | Tag outputs with the artefact fingerprint (§5.5) |
| Rollback takes hours, not minutes | Previous versions were overwritten, not kept | Store every version; never mutate in place |
| Exact-match suite fails constantly on "correct" output | Wrong assertion type for free-text output | Switch to a property assertion |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** A gate that only diffs the template file will not catch a model or parameter change —
  fingerprint the whole artefact (§5.4, §6).
- **Reliability.** A regression suite run once is not evidence in either direction (§5.3). Size the
  sample count against your own quality gap before trusting the gate.
- **Cost.** Increasing samples per golden case increases suite cost linearly, but §7.3 shows the return
  is steep early — the jump from 1 to 10 samples/case buys most of the reliability for a fraction of the
  cost of going further.
- **Cost.** A cheaper model swapped in without a regression run can cost more in incident response than
  it saved in inference (§6).
- **Security.** A tool schema change is part of the artefact fingerprint for the same reason a wording
  change is — a widened or narrowed tool schema changes what the model can do (M5-L08), and must gate
  the same way.
- **Privacy/audit.** Tag every production output with the fingerprint of the artefact that produced it.
  Without that tag, "what configuration generated this" becomes reconstruction rather than lookup
  (M10-L13).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name four fields that belong in a prompt artefact besides the template text.
2. Why does an exact-match assertion fail on some genuinely correct outputs?
3. What is wrong with trusting a single run of a golden suite?
4. What should a CI gate hash to decide whether to re-run the suite?
5. Why must old prompt versions be kept rather than overwritten?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the exact-match and property pass rates for both versions in section 2, and
   explain the gap in one sentence.
2. Change `SURFACE_VARIATION` to 0.10 and 0.60 in section 2 and re-run. How does the exact-match rate
   respond, and does the property rate change at all? Explain why.
3. Pick your own quality gap (e.g. 0.92 vs 0.80) and threshold in section 3, and report the samples/case
   needed to get the catch rate above 95% while keeping the false-alarm rate under 5%.
4. Build a `PromptArtefact` for a prompt you have written in an earlier lesson's lab. Compute its
   fingerprint, then change one non-template field and confirm the fingerprint changes.
5. Write a `gate_by_fingerprint`-style check as an actual CI step (pseudocode or a real script) that
   fails the build if the artefact fingerprint changed without a corresponding golden-suite run.

### Exercise 3 — Challenge (~50 min)

1. Build a small prompt registry: store artefacts keyed by id and version, support "get current," "get by
   version," and "rollback to version," and test all three.
2. Extend the lab's simulation to model *correlated* failures (a model having a "bad batch" that fails
   several cases together) rather than independent draws, and compare the false-alarm/catch-rate table
   under correlation to §7.3's independent-draw version.
3. Design and justify a sample-count and threshold policy for a real domain (support, code review, medical
   intake) where you state the cost of a false alarm and the cost of a missed regression, and derive the
   policy from those costs rather than a default.
4. Add an LLM-graded assertion (a judge prompt, real or simulated) for one golden case whose correctness
   cannot be expressed as a simple property, and discuss what new failure mode it introduces (M5-L18,
   M13-L13 preview this — you do not need to have read them).
5. Write the incident postmortem for §6, in your organisation's usual format, including the specific gate
   change that prevents a recurrence.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l12).)*

**Q1.** A prompt artefact should include:

- A. The template, model, parameters and tool schema together.
- B. Only the template text, since that is what a human edits.
- C. Only the model id, since it determines cost.
- D. Only fields that appear in the git diff of a pull request.

**Q2.** A prompt that is truly correct 95% of the time passed an exact-match suite only 67% of the time
in the lab. The gap is because:

- A. The model is unreliable and should not be trusted.
- B. 67% is a rounding artefact of the simulation.
- C. The golden set had the wrong expected answers.
- D. Exact-match also fails correct answers that are formatted differently from the stored string.

**Q3.** A property assertion, compared to exact-match, checks:

- A. Byte-identical output only.
- B. Whether a stated rule about the output holds, regardless of exact wording.
- C. Whether the output arrived within a time limit.
- D. Whether the model used the cheapest available option.

**Q4.** At one sample per golden case, the lab measured a false-alarm rate of 19% and a catch rate of
63%. This means:

- A. The suite is reliable enough to gate production deploys.
- B. The threshold was set too low and should be raised.
- C. A single run is close to a coin flip on both whether a regression is real and whether one is missed.
- D. The prompt itself is regressing 19% of the time.

**Q5.** Going from 1 to 10 samples per golden case in the lab changed the false-alarm and catch rates by:

- A. Dropping false alarms toward 5% and raising the catch rate to 98%.
- B. Making both worse.
- C. Leaving both roughly unchanged.
- D. Only affecting the catch rate, not the false-alarm rate.

**Q6.** In section 1, v1 and v3 share an identical template but different fingerprints because:

- A. The fingerprint function is nondeterministic.
- B. v3's version string differs from v1's.
- C. Fingerprints always differ between any two artefacts.
- D. The fingerprint is computed over model, temperature, max_tokens and tool schema as well as the template.

**Q7.** A CI gate that only diffs the template file, applied to the v1 → v3 change in §6:

- A. Correctly re-runs the golden suite, since behaviour changed.
- B. Reports an empty diff and skips the golden suite.
- C. Refuses the deploy outright.
- D. Automatically rolls back to v1.

**Q8.** The general rule this lesson draws from §6 is:

- A. Never change the model or parameters of a shipped prompt.
- B. Only the template text needs to be reviewed before a deploy.
- C. If changing it can change the output, it is part of the prompt version, not "just config."
- D. Golden suites should be run only after an incident, not before.

**Q9.** Why must old prompt artefact versions be kept rather than overwritten?

- A. Because rollback and output attribution both depend on the old version still existing.
- B. To reduce storage costs.
- C. Because providers require it.
- D. It is not necessary if the fingerprint is recorded.

**Q10.** Reserve exact-match assertions for:

- A. Any free-text explanation the model produces.
- B. Every field in every golden case, for consistency.
- C. Cases where the model's temperature is above zero.
- D. Genuinely fixed values, like an enum field, where byte-identical output is actually required.

**Q11.** The lab's false-alarm and catch-rate table is described as:

- A. A universal result that applies to any prompt and any quality gap.
- B. A measurement of a specific real model's behaviour.
- C. A method demonstration — recompute the specific rates for your own quality gap and threshold.
- D. Only relevant to categorization tasks.

**Q12.** A tool schema change (M5-L08) should be treated by the versioning system as:

- A. Irrelevant, since it is not part of the prompt text.
- B. Part of the artefact, fingerprinted and gated the same way as a wording change.
- C. Something to review only if the model also changes.
- D. Something that never needs a golden-suite re-run.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team wants to skip building a golden suite
for a new prompt because "we'll just watch production closely instead." State the risk in that plan and
what minimum version of a regression suite you would ask for before agreeing.

---

## 12. Revision notes

- **A prompt artefact is template + model + parameters + tool schema** — fingerprint all of it; a
  template-only diff misses real behaviour changes (measured: v1 → v3, empty diff, changed fingerprint).
- **Exact-match tests formatting, not correctness.** Measured: a prompt correct 95% of the time passed
  exact-match only 67% of the time. Use property assertions for anything with legitimate surface
  variation.
- **A single golden-suite run is not evidence.** Measured: at 1 sample/case, 19% false-alarm rate and
  63% catch rate. Size your sample count against your own quality gap before trusting a gate.
- **More samples per case buy reliability fast.** Measured: 10 samples/case reached a 98% catch rate and
  a 5% false-alarm rate in the lab's setup.
- **Gate deploys on the artefact fingerprint, not a template-file diff.** The whole §6 incident is one
  gate watching the wrong thing.
- **Keep every version.** Rollback and output attribution both require the old configuration to still
  exist, not just be remembered.
- **If changing it can change the output, it's part of the version** — model, temperature, `max_tokens`,
  tool schema included, no exceptions for "just config."

---

## 13. Completion checklist

- [ ] My prompt artefact definition includes model, parameters and tool schema, not just the template.
- [ ] I compute a fingerprint over every behaviour-affecting field.
- [ ] My CI gate re-runs the golden suite on a fingerprint change, not a template-file diff.
- [ ] I use property assertions for output with legitimate surface variation, exact-match only for truly
      fixed values.
- [ ] I have sized my sample-count and threshold by simulating my own quality gap.
- [ ] Every prompt version I have shipped is still retrievable, not overwritten.
- [ ] My stored/logged outputs are tagged with the artefact version that produced them.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pytest documentation — parametrised tests and fixtures (the mechanics a golden suite is built on).
  <https://docs.pytest.org/en/stable/how.html> `[UNVERIFIED]`
- Python `hashlib` documentation.
  <https://docs.python.org/3/library/hashlib.html> `[UNVERIFIED]`
- Anthropic — prompt engineering and evaluation guidance.
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L13 — Prompt Injection: Attack Catalogue and Real Defences](M5-L13-prompt-injection.md)

You can now version a prompt and catch a regression before it ships. Next: a class of failure no
regression suite catches by default, because the "bad" input comes from outside your test set entirely —
untrusted content trying to rewrite the model's instructions.
