# M5-L17 — Provider Differences and Portability

| | |
|---|---|
| **Lesson ID** | M5-L17 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M5-L08](M5-L08-tools.md) |

---

## 1. Learning objectives

1. **Distinguish** an envelope-level provider difference from a structural one, and name which category
   Claude-via-Bedrock falls into versus a genuinely different API family.
2. **Explain** why token counts for identical text differ by tokenizer, and why the difference is
   content-dependent, not uniform.
3. **Verify**, rather than assume, that a prompt's measured quality transfers to a new provider.
4. **Design** a request-building layer that isolates provider-specific shape from the rest of an
   application.
5. **List** the provider-specific mechanics this lesson does not cover, and where to verify them.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Wire format** | The actual JSON/HTTP shape a provider's API expects. |
| **Envelope change** | A porting change that wraps the same inner request differently, without altering its structure. |
| **Structural change** | A porting change that alters the request's internal shape — where fields live, how they nest. |
| **Adapter** | Code converting one neutral internal request representation into a specific provider's wire format. |
| **Tokenizer divergence** | The gap in token count for identical text between two different tokenizers. |
| **Quality transfer** | The (unsafe) assumption that a prompt's measured quality on one provider holds on another. |
| **Portability layer** | The part of an application isolating provider-specific request/response shape from business logic. |
| **Bedrock** | AWS's managed hosting for foundation models, including Claude, under AWS's own request envelope and auth. |
| **Model family drift** | Differences between versions or providers of "the same" model that a shared prompt does not account for. |

---

## 3. Plain-language explanation

### 3.1 "Portable" prompt text is not a portable application

The words in a system prompt travel reasonably well between providers — the instructions are still
instructions. **Everything wrapped around those words does not travel automatically**: message envelope
shape, tool schema format, token counts, and measured quality are all specific to the provider and model
you tested against, and porting means re-verifying each one, not assuming it carries over.

### 3.2 Two different kinds of "different"

Some provider differences are **envelope changes** — the same inner shape, wrapped differently. Claude on
Bedrock is the clearest example: the request body is the same Anthropic-shaped body, just placed inside
an AWS envelope with its own authentication. Other differences are **structural** — a genuinely different
API family (message roles, tool-schema nesting) changes the shape you have to build, not just the wrapper
around it. §7.1 makes this distinction concrete and measurable.

### 3.3 The same text is not the same number of tokens

M4-L03 taught you to count tokens for one tokenizer. A different provider very likely uses a **different**
tokenizer, and §7.2 shows the gap is not uniform: plain English and structured formats like code or JSON
can tokenize *identically* between two real, different encodings, while a non-Latin script or unusual
vocabulary can diverge by close to a third. **You cannot apply a single conversion factor** — you have to
re-count on content that resembles your actual traffic.

### 3.4 Quality does not travel on faith

A prompt tuned and passing its golden suite (M5-L12) on one provider is not guaranteed to pass at a
similar rate on another, unmodified. §7.3 shows this concretely, and shows something sharper: **a small
golden-suite sample can fail to detect a real quality gap at all** — the same sample-size lesson M5-L12
taught, now surfacing again the moment you change providers.

---

## 4. Analogy

**Shipping the same product through two different couriers.** One courier (Bedrock) takes your existing,
sealed package and simply puts it inside their own branded outer box with their own paperwork — the
contents are completely untouched. A different courier (a different API family) requires you to
**repack** the same contents into their specific container shapes, with items positioned differently
inside.

Both couriers will also weigh the package on their own scale, and the two scales do not agree exactly —
close enough for most parcels, meaningfully different for oddly-shaped or unusually dense ones. And
neither courier's delivery success rate for your specific type of parcel is known until you actually ship
a representative batch and check — a courier's *general* reputation is not a substitute for testing with
*your* parcels.

### Where the analogy breaks

- **A courier's outer box never affects what's inside.** An AI provider's differences are not purely
  cosmetic — token counts and measured quality are properties of the *specific* provider and model, not
  just the wrapper (§3.3, §3.4).
- **A physical scale disagreement is usually small and consistent.** Tokenizer divergence is
  content-dependent — near zero for some text, substantial for other text (§7.2) — not a fixed percentage
  you can apply everywhere.
- **You can weigh one parcel to learn the scale's behaviour for all similar parcels.** A golden suite's
  single small run can fail to reveal a real quality gap at all (§7.3) — you need enough samples, not just
  one.

---

## 5. Detailed technical explanation

### 5.1 Envelope vs structural change

`[REAL code, UNVERIFIED exact field names]` §7.1 built adapters converting one neutral request into three
illustrative wire shapes:

| Shape | Top-level keys | System prompt location |
|---|---|---|
| Anthropic direct | `model, system, messages, tools, max_tokens` | Top-level field |
| OpenAI-style | `model, messages, tools, max_tokens` | Inside `messages[0]`, `role="system"` |
| Bedrock (Claude) | `modelId, body` | Nested under `body` |

**Anthropic-direct and Bedrock share zero top-level keys — and that is exactly the point.** Bedrock's
`body` field *contains* the same Anthropic-shaped request, unchanged; only the outer envelope and the
authentication mechanism differ. **Anthropic-direct and an OpenAI-style API share four top-level keys**,
but the *system prompt has moved from a dedicated field into the message list itself* — a structural
change reaching into how the request is built, not just how it is wrapped. **Porting to Bedrock is
mechanically simpler than porting to a structurally different API family**, even though both are commonly
described with the same word, "portability."

### 5.2 Tokenizer divergence is content-dependent

`[REAL]` §7.2 compared two real, different tiktoken encodings on the same texts:

| Text | cl100k_base | o200k_base | Diff |
|---|---|---|---|
| Plain English question | 6 | 6 | 0 |
| Code / JSON | 20 | 20 | 0 |
| Rare English word | 20 | 18 | −2 |
| **Japanese sentence** | 22 | **15** | **−7 (−32%)** |

**Common English and structured formats tokenized identically here.** A rare word and a non-Latin script
both diverged substantially, with the Japanese sentence taking **32% fewer tokens** under the newer
encoding. This is not a claim about any specific provider's actual tokenizer — it is a real demonstration,
using two genuinely different encodings, that **divergence depends on content, not on a fixed ratio you
can apply everywhere.** Re-count on samples that resemble your real traffic before trusting a budget
(M4-L06) or a cost estimate (M5-L15) carried over from another provider.

### 5.3 Quality does not transfer, and a small sample can hide that fact

`[REAL arithmetic on ILLUSTRATIVE quality figures]` §7.3 ran M5-L12's golden-suite machinery against two
simulated providers:

| Provider | Single 8-case draw | 40-run average |
|---|---|---|
| Original (tuned here) | 7/8 | **97%** |
| New (same prompt, unmodified) | 7/8 | **80%** |

**Read the single-draw column first: it is identical for both providers**, despite a real 17-point quality
gap between them. This is M5-L12's own sample-size finding recurring: 8 samples were not enough to tell a
95%-quality provider from an 80%-quality one apart. **Only the averaged column reveals the gap.** The
practical consequence: verifying portability with one quick manual test is close to worthless — it is
exactly the scenario where a real difference can hide in plain sight. Run the same golden suite, at a
sample size sized per M5-L12 §5.3, against the actual target provider before switching.

### 5.4 A portability layer, and what it does and doesn't buy you

Centralising the adapters from §5.1 into one layer means switching providers is a change in **one place**,
not scattered across every call site — a direct application of M5-L12's artefact discipline to the request
*shape*, not just its text. **It does not, by itself, guarantee quality transfers** (§5.3) — a portability
layer solves the *format* problem; it does not solve the *quality* problem, which requires actually running
the suite.

### 5.5 What this lesson does not cover

Streaming event formats differ by provider (M5-L09 covers streaming mechanics generally; the exact SSE
framing is provider-specific). Authentication differs sharply — an API key versus AWS SigV4-signed
requests for Bedrock. Rate-limit structures, safety/refusal thresholds, and exact context-window sizes all
vary and change over time. **Check current documentation for any provider you actually use** — this
lesson gives you the categories to check, not a snapshot that will stay current.

### 5.6 Assumptions and limitations

- §7.1's wire shapes are simplified and illustrative. `[UNVERIFIED — verify exact current field names
  against each provider's own documentation before using this in real code.]`
- §7.2's tokenizer comparison uses two real tiktoken encodings as an honest stand-in for "tokenizers
  differ by provider." It does not measure any specific provider's actual current tokenizer.
- §7.3's quality figures (95%, 80%) are stated parameters chosen to illustrate a real, general risk —
  prompts do not transfer quality automatically — not a measurement of any two specific real providers.
- This lesson's own course design deliberately targets Claude via the direct API and via Bedrock as its
  two working environments; portability to other providers follows the same principles but was not tested
  here.

---

## 6. Worked example — the prompt that "just worked" until it didn't

**The system.** A team's support-triage prompt is developed and tuned against one provider, passes its
golden suite at 97% (§7.3's own figures), and ships. Months later, for cost or availability reasons, the
team switches the same prompt text to a different provider, without re-running the suite — "it's the same
prompt, it should just work."

**What a quick manual check showed.** Someone tries five or six sample tickets by hand against the new
provider. They look fine. The team ships.

**What was actually true.** Per §5.3's exact mechanism, a handful of manual samples has a real chance of
looking identical to the original provider's results even when the true quality has dropped substantially
— **not because anyone was careless, but because a small sample is structurally unable to distinguish a
real 17-point gap from noise.** The drop surfaced weeks later as a slow rise in miscategorised tickets,
traced back only after a support-quality review flagged it.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Assumed "same prompt text" meant "same behaviour" | No re-verification step existed at all |
| 2 | The manual check used far too few samples | It had a real chance of missing a genuine, substantial gap |
| 3 | No token/cost re-check against the new provider's tokenizer | A silent, separate error was compounding underneath the quality one |

### The fix

**Never port a prompt without re-running its golden suite** (M5-L12) against the actual target provider,
at a sample size established per M5-L12 §5.3 to reliably detect the gap you care about — not a quick
manual spot-check.

**Re-count tokens on real, representative content** for the new provider's tokenizer before reusing any
budget or cost figure (§5.2, M4-L06, M5-L15).

**Treat the wire-format and authentication change as its own, separate checklist item** (§5.1, §5.5), so
a successful format port is never mistaken for a successful quality port.

**The general rule.** **"Same prompt text" is not "same behaviour." Every dimension this lesson names —
format, tokens, quality — has to be verified against the specific target provider, not assumed from the
source one.**

---

## 7. Practical activity

**File:** [`labs/m5/l17_provider_portability.py`](../../labs/m5/l17_provider_portability.py)

**No API key, no network beyond tiktoken's one-time download.**

```bash
source .venv/bin/activate
python labs/m5/l17_provider_portability.py
```

Section 1's adapters and section 2's tokenizer counts are real, exact code. Section 3 reuses M5-L12's
mock-quality machinery, now varying provider instead of prompt version.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, tiktoken 0.14.0.

```text
============================================================================
1. THE SAME LOGICAL REQUEST, THREE WIRE FORMATS  [UNVERIFIED shapes]
============================================================================
  Illustrative shapes only -- verify exact current field names against
  each provider's own documentation before using this in real code.

  shape               top-level keys                               system location
  Anthropic direct    model, system, messages, tools, max_tokens   top-level field
  OpenAI-style        model, messages, tools, max_tokens           inside messages[0] with role='system'
  Bedrock (Claude)    modelId, body                                nested under body

  Anthropic vs OpenAI-style top-level keys in common: ['max_tokens', 'messages', 'model', 'tools']
  Anthropic vs Bedrock top-level keys in common: [] -- Bedrock wraps the SAME
  Anthropic-shaped body inside an envelope (modelId, body), rather
  than changing the inner shape itself. Porting Anthropic-direct to
  Bedrock is an ENVELOPE change; porting to an OpenAI-style API is a
  STRUCTURAL change reaching into the message list and the tool
  schema's nesting, not just the outside.

============================================================================
2. THE SAME TEXT, DIFFERENT TOKEN COUNTS
============================================================================
  Two REAL, different tiktoken encodings on the SAME text -- a
  concrete, honest stand-in for 'different providers tokenize
  differently'. This does NOT measure any specific provider's
  actual tokenizer; it measures two real, different encodings.

  text                                            cl100k_base  o200k_base   diff
  What is my order status?                                  6           6     +0
  Refund approved: GBP 940.00, ref #GB-4471, *             22          22     +0
  def calculate_refund(amount: float, cap: fl*             20          20     +0
  The pneumonoultramicroscopicsilicovolcanoco*             20          18     -2
  Tokyo meeting scheduled: 東京都渋谷区で会議があります。                 22          15     -7

  Plain English and structured formats (code, JSON) often match
  exactly between these two real encodings -- they share most of
  their everyday vocabulary. But a rare English word and a
  non-Latin script both diverge substantially: the Japanese
  sentence took 32% FEWER tokens under the newer encoding. A
  token budget (M4-L06), a cost estimate (M5-L15), and a
  context-window check are all tokenizer-specific -- porting a
  prompt to a new provider means RE-COUNTING for content that
  looks like your actual traffic, not assuming the old numbers
  hold, and not assuming EVERY string will move by the same
  amount either.

============================================================================
3. A GOLDEN SUITE (M5-L12) DOES NOT AUTOMATICALLY PORT
============================================================================
  The SAME prompt text and golden suite from M5-L12, run against two
  PROVIDERS instead of two prompt versions. Quality is a stated,
  illustrative parameter per provider -- not a measurement of any
  real model. Averaged over 40 runs/case, per M5-L12's own
  lesson that a single small-sample run is not evidence by itself.

  provider                                 single 8-case draw  40-run average
  original provider (tuned here)                          7/8             97%
  new provider (same prompt, unmodified)                  7/8             80%

  Look at the single-draw column first: it shows 7/8 for BOTH
  providers, identical, despite a real 17-point quality gap between
  them. This is not a bug in the lab -- it is M5-L12 section 3's
  finding happening again, live: 8 samples is not enough to tell a
  95%-quality provider from an 80%-quality one apart. Only the
  averaged column reveals the gap that was there all along.

  The averaged column is the number worth trusting -- 95% quality on
  the tuned provider does not carry over to the new one just because
  the prompt text is unchanged; wording that reads as a firm
  instruction to one model can read as a softer suggestion to
  another. The fix is not hope: it is running the EXACT SAME
  golden suite (M5-L12), at a sample size that can actually detect a
  drop (M5-L12 section 3), against the new provider before
  switching.

  (The delta above is stated by construction, chosen to be
  illustrative; real provider-to-provider gaps range from
  negligible to large depending on the prompt and the task, and are
  only known once measured.)

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1's adapter code and structural diff, and section 2's
  tiktoken counts, are exact and reproducible.

  ILLUSTRATIVE / UNVERIFIED: section 1's exact wire shapes are
  simplified and may not match any provider's current API precisely
  -- verify field names against current documentation before using
  them in real code. Section 3's per-provider quality figures are
  stated parameters illustrating a real, documented risk (prompts
  do not transfer quality automatically), not a measurement of any
  specific two providers.

  NOT SHOWN: differences in streaming event formats (M5-L09),
  authentication mechanics (API key vs AWS SigV4), rate-limit
  structures, or exact safety/refusal threshold differences --
  all real, all provider-specific, all worth checking directly
  against current documentation for any provider you actually use.

Done.
```

### 7.3 Reading the result

**Section 1 makes "portability" precise instead of vague.** Two changes that get described with the same
word — porting to Bedrock, porting to a structurally different API — are mechanically very different in
size. Knowing which kind you're facing tells you how much work to budget.

**Section 2's honest surprise is that most text didn't move at all.** Plain English and code matched
exactly across two real encodings; only unusual vocabulary and non-Latin script diverged, by a lot. The
lesson is not "always expect a big gap" — it is "you cannot know which without checking your own content."

**Section 3 is the sharpest result in the lesson, and it is almost invisible unless you look at both
columns.** A single small sample showed *no* difference between a 97%-quality provider and an 80%-quality
one. Anyone who ported this prompt and "spot-checked a few examples" would have shipped the regression
with complete confidence that nothing had changed.

---

## 8. Common mistakes and troubleshooting

1. **Assuming "same prompt text" means "same behaviour" on a new provider.** §6 — it does not.
2. **Manually spot-checking a handful of examples after a provider switch.** §5.3 shows this can fail to
   detect a real, large quality gap.
3. **Reusing token counts or cost estimates from the old provider.** Re-count with the new tokenizer on
   representative content (§5.2).
4. **Treating Bedrock and a structurally different API as the same kind of "port."** One is an envelope
   change; the other reaches into the request's structure (§5.1).
5. **Scattering provider-specific request-building code across many call sites.** Centralise it in
   adapters (§5.4).
6. **Assuming a portability layer alone guarantees quality transfers.** It solves the format problem, not
   the quality one.
7. **Not re-checking authentication, streaming, and rate-limit mechanics separately.** Each is its own,
   independent thing to verify (§5.5).
8. **Trusting a provider's general reputation instead of testing your specific prompt and traffic.**
9. **Assuming a tokenizer's divergence is a fixed percentage.** It is content-dependent (§5.2).
10. **Skipping the golden suite because "it's not a prompt change."** Per M5-L12, the model/provider is
    part of the artefact — switching it is exactly the kind of change that must gate a suite re-run.

| Symptom | Likely cause | Fix |
|---|---|---|
| Quality quietly drops after a provider switch, unnoticed at first | Spot-check too small to detect the gap | Run the golden suite at an adequate sample size (§5.3) |
| Requests fail after switching to Bedrock | Envelope/auth mismatch, not a prompt issue | Check request wrapping and AWS SigV4 auth separately from prompt content |
| Cost estimates are wrong after a provider switch | Old token counts reused | Re-count with the new provider's tokenizer on real content |
| Tool calls stop working after a switch | Tool schema nesting differs structurally between APIs | Update the adapter for the new API family's tool format |
| "It worked in my quick test" but fails at scale | Small manual sample masked a real gap | Replace manual spot-checks with a sized golden suite |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never port a prompt to a new provider without re-running its golden suite at a sample
  size that can actually detect a real quality gap (§5.3, M5-L12).
- **Reliability.** Distinguish envelope changes from structural changes before estimating porting effort
  — treating a Bedrock move like a full API rewrite, or vice versa, misallocates engineering time (§5.1).
- **Cost.** Re-count tokens on representative content before trusting a budget or cost estimate carried
  over from another provider (§5.2, M4-L06, M5-L15).
- **Security.** Authentication mechanics differ sharply by provider (API key vs AWS SigV4) — treat this
  as its own checklist item, not an assumption that "the request works, so auth must be fine."
- **Cost/Reliability.** A portability layer reduces the *format* migration cost but does not remove the
  need to verify quality and tokens on the new provider — budget for both separately.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what is the difference between an envelope change and a structural change?
2. Why did the Japanese sentence in §7.2 tokenize so differently between the two encodings, while the
   plain English question did not?
3. What did the single 8-case draw in §7.3 fail to reveal, and why?
4. Name two things a portability layer does not guarantee.
5. Name two provider-specific mechanics this lesson explicitly does not cover.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the token-count divergence for the Japanese sentence and confirm it matches the
   lesson.
2. Add a fourth provider adapter of your own design (real or hypothetical) to section 1, and classify it
   as an envelope or structural change relative to Anthropic-direct.
3. Using section 3's approach, simulate a smaller (95% vs 90%) and a larger (95% vs 60%) quality gap
   between two providers, and report at what sample size each becomes reliably detectable.
4. Using tiktoken (or another real tokenizer you have access to), test five samples of your own real
   content and report which diverge most between two encodings.
5. Design a portability checklist (a table, one row per §5.1–§5.5 dimension) for a real or hypothetical
   application you would move between providers.

### Exercise 3 — Challenge (~50 min)

1. Build a real `RequestAdapter` protocol/interface with at least two concrete implementations, and a
   test asserting that switching implementations requires no changes outside the adapter layer.
2. Extend section 3's simulation to three providers and determine, for a stated sample size, which pairs
   of providers would be reliably distinguished and which would not.
3. Research your own target providers' current documentation `[you must verify this yourself]` and
   rebuild section 1's shapes with real, current field names, noting every place your assumption in this
   lesson was wrong.
4. Design and implement a token-recount step that runs automatically whenever a prompt artefact's model
   field changes (tying to M5-L12's fingerprint), and test that it fires correctly.
5. Write the migration runbook for moving a real or hypothetical production prompt from one provider to
   another, covering format, tokens, quality, auth, and rollback.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l17).)*

**Q1.** In §7.1, Bedrock's wire shape shared zero top-level keys with the Anthropic-direct shape, while
an OpenAI-style shape shared four. The reason is:

- A. Bedrock does not support Claude models.
- B. The OpenAI-style shape is actually identical to Anthropic-direct.
- C. Bedrock wraps the same inner Anthropic-shaped body inside an envelope (modelId, body), while an OpenAI-style API changes the structure itself, including where the system prompt lives.
- D. Top-level key overlap is determined randomly by each provider.

**Q2.** Per §5.1, porting from Anthropic-direct to Bedrock (the same underlying model) is best described
as:

- A. Impossible without rewriting the prompt entirely.
- B. An envelope change — the inner request shape stays the same, just wrapped differently.
- C. Identical to porting to a completely different model family.
- D. A change that only affects billing, not the request itself.

**Q3.** In §7.2, most everyday English and structured text (code, JSON) tokenized identically between two
real encodings, but a Japanese sentence took 32% fewer tokens under the newer one. The general lesson is:

- A. Different tokenizers can diverge sharply for some content and not at all for other content — you cannot assume a uniform conversion factor.
- B. Non-English text should never be sent to any tokenizer.
- C. Token counts are identical across all tokenizers by design.
- D. Japanese text is always cheaper to process than English text.

**Q4.** Why does porting a prompt to a new provider require re-counting tokens rather than reusing old
counts?

- A. Token counting is illegal to automate.
- B. Providers charge a flat fee regardless of token count.
- C. Only output tokens ever change between providers.
- D. Token budgets, cost estimates, and context-window checks are all specific to the tokenizer that produced them, and a new provider very likely uses a different one.

**Q5.** In §7.3, a single 8-case golden-suite draw showed 7/8 for both the 95%-quality and the
80%-quality provider. This happened because:

- A. The two providers were actually identical.
- B. 8 samples is too few to reliably distinguish a real 17-point quality gap, echoing M5-L12's sample-size finding.
- C. The random seed was set incorrectly.
- D. Golden suites cannot detect quality differences under any circumstances.

**Q6.** The averaged result in §7.3 (97% vs 80%) revealed what the single draw could not. The general
lesson is:

- A. Averaging is only useful for cost calculations, not quality.
- B. A single manual spot-check is always sufficient to validate a provider switch.
- C. The same golden suite must be run at a sample size large enough to detect a real gap, not just run once, when comparing providers.
- D. Quality differences between providers are always too small to matter.

**Q7.** Why is it risky to assume a prompt that passes its golden suite on one provider will pass at a
similar rate on another, unmodified?

- A. Wording tuned to read as a firm instruction to one model can read as a softer suggestion to another, so quality does not automatically transfer.
- B. Golden suites are provider-agnostic by design and never need to be re-run.
- C. Providers guarantee identical output for identical prompts.
- D. This risk only applies to non-English prompts.

**Q8.** What is the recommended way to validate a prompt before switching providers, per §5.3?

- A. Trust the provider's marketing claims about compatibility.
- B. Skip validation if the prompt text is unchanged.
- C. Ask the model itself whether it understood the prompt correctly.
- D. Run the exact same golden suite, at an adequately sized sample count, against the new provider before switching.

**Q9.** Section 1's adapter functions convert one neutral internal request into three provider-shaped
requests. The practical benefit of this pattern is:

- A. It eliminates the need to ever test against a new provider.
- B. It makes every provider's API behave identically at the model level.
- C. Switching or supporting multiple providers becomes a change in one place (the adapters), not a change scattered across every call site.
- D. It automatically converts token counts between tokenizers.

**Q10.** Which of the following is explicitly listed as not covered by this lesson's lab, per §7.4?

- A. Token counting differences.
- B. Differences in streaming event formats and authentication mechanics.
- C. Wire-format structural differences.
- D. Golden-suite sample sizing.

**Q11.** The lesson's central practical rule is:

- A. Assume all providers behave identically once the prompt text is portable.
- B. Only verify token counts; quality and format can be assumed.
- C. Switching providers should be avoided entirely due to the risk.
- D. Verify wire format, token counts, and quality with the actual target provider before relying on any of them carrying over unchanged.

**Q12.** Section 1's wire-format shapes are explicitly marked `[UNVERIFIED]`. This means:

- A. The structural pattern (envelope vs structural change) is the durable lesson; the exact field names should be checked against current provider documentation before use in real code.
- B. The entire section should be disregarded.
- C. The shapes are guaranteed to be wrong.
- D. Verification is unnecessary since the lab executed successfully.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague wants to switch your application's
underlying model to a different provider this week, citing cost savings, and proposes shipping it with
"a quick manual test of a few examples." State the specific risk in that plan, referencing this lesson's
lab, and what you would insist on instead.

---

## 12. Revision notes

- **"Portable prompt text" is not "portable application."** Wire format, token counts, and quality are
  each their own thing to verify against the actual target provider.
- **Envelope changes and structural changes are different sizes of work.** Measured: Bedrock shares zero
  top-level keys with Anthropic-direct (wraps the same inner body); an OpenAI-style shape shares four but
  moves the system prompt into the message list — a genuine structural change.
- **Tokenizer divergence is content-dependent, not a fixed ratio.** Measured: plain English and code
  matched exactly between two real encodings; a Japanese sentence diverged by 32%. Re-count on your own
  representative content.
- **A small sample can completely hide a real quality gap.** Measured: a single 8-case draw showed 7/8
  for both a 95%-quality and an 80%-quality provider. Only a 40-run average revealed the true 17-point
  gap — the same sample-sizing lesson from M5-L12, recurring at the provider-switch moment specifically.
- **A manual spot-check after a provider switch is close to worthless as evidence.** Run the golden suite
  at an adequate sample size instead.
- **Centralise provider-specific request shape in an adapter layer** — it contains the format cost of
  switching, but does not by itself guarantee quality transfers.
- **Authentication, streaming, and rate limits are each their own separate check** — not covered by
  verifying format or quality alone.

---

## 13. Completion checklist

- [ ] I can classify a given provider switch as an envelope change or a structural change.
- [ ] I re-count tokens on representative content before trusting a budget or cost figure from another provider.
- [ ] I never rely on a manual spot-check to validate a provider switch — I run a sized golden suite.
- [ ] My request-building code is centralised in an adapter layer, not scattered across call sites.
- [ ] I treat authentication, streaming, and rate limits as separate checklist items when porting.
- [ ] I check current provider documentation rather than relying on any specific wire-format shape as fixed.
- [ ] I know, for my own system, what its golden-suite sample size needs to be to detect a real quality gap.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Amazon Bedrock — documentation for the Anthropic Claude models.
  <https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html>
  `[UNVERIFIED]`
- Anthropic — Messages API reference. <https://docs.anthropic.com/en/api/messages> `[UNVERIFIED]`
- OpenAI — Chat Completions API reference. <https://platform.openai.com/docs/api-reference/chat>
  `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L18 — Building an Evaluation Dataset You Can Trust](M5-L18-evaluation-dataset.md)

You can now verify a prompt's format, tokens and quality against a new provider. Next: building the
evaluation dataset that makes every "verify" in this module actually trustworthy, rather than a small
sample that happens to look fine.
