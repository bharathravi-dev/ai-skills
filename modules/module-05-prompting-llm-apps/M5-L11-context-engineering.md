# M5-L11 — Context Engineering: Summarization, Truncation, Budgets

| | |
|---|---|
| **Lesson ID** | M5-L11 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M5-L10](M5-L10-conversation-state.md), [M4-L06](../module-04-genai-llm-internals/M4-L06-context-windows.md) |

---

## 1. Learning objectives

1. **Choose** a trigger for switching conversation-state strategy, and explain why a fixed turn count is
   a token-count trigger wearing a disguise.
2. **Measure** the drift that accumulates when a summary is repeatedly summarised, and state how
   checkpointing bounds it — and what that bound costs.
3. **Assemble** one request budget that arbitrates across system prompt, tools, retrieved documents and
   conversation state, with a single explicit drop order.
4. **Monitor** how often a production system actually crosses its own trigger thresholds, and say why
   that number, not the demo, defines the service.
5. **Decide** whether a fact belongs in prose or in structured state, based on what kind of fact it is.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Context engineering** | Deciding, per request, what enters the model's context and in what form. |
| **Trigger threshold** | The condition — tokens, turns, time — that fires a switch to a cheaper strategy. |
| **Cascading summarization** | Summarising the previous summary, rather than the original source material. |
| **Checkpoint resummarization** | Periodically regenerating a summary from source instead of from the last summary, to bound drift. |
| **State drift** | Errors that compound when state is derived from prior state rather than source (M5-L10). |
| **Budget assembler** | The component that fits every prompt piece into one window under one drop order. |
| **Component priority** | The order, decided in advance, in which pieces are downgraded or dropped under pressure. |
| **Graceful degradation** | A system whose quality falls smoothly under load rather than failing outright. |
| **Refusal (budget)** | Declining to build a request rather than silently truncating a component that must not be cut (M4-L06). |

---

## 3. Plain-language explanation

### 3.1 Two lessons, one production problem

M4-L06 gave you a budget mechanism for a single request: components, priorities, headroom, an explicit
drop order. M5-L10 gave you four strategies for conversation history specifically, priced and scored
for what each one loses. Neither lesson told you **when** to switch strategies, or how history's budget
interacts with everything else sharing the same window.

**Context engineering is running both, live, on every request.** It is the operational layer between a
one-off budget calculation and a policy your service actually enforces at 2 a.m. on a conversation
nobody tested.

### 3.2 A summary is not a one-time operation

A short conversation gets summarised once. A long one gets summarised repeatedly, as new turns keep
arriving. The obvious way to do this — feed the last summary plus the newest turns back into the
summarizer — is called **cascading summarization**, and it has a property that does not show up until
you run it for a while: **each pass compounds the error of every pass before it.**

M5-L10 named this **state drift** and left it there. This lesson measures it, and gives you the other
option: **checkpoint resummarization** — periodically throwing the chain away and re-deriving the
summary from the actual source. That costs more, because it re-reads material a cascading pass would
have skipped. §7 prices both sides of that trade exactly.

### 3.3 A trigger is a policy decision

"Summarise every 10 turns" sounds precise. It is not — it is a **token-count trigger measured in the
wrong unit**. Ten turns of a terse conversation and ten turns of a verbose one arrive at wildly different
context sizes, so a turn-count rule fires at a different *budget position* every time, depending entirely
on how your users happen to write. §7.1 measures the gap directly.

### 3.4 The budget assembler must know about every lever, not just documents

M4-L06's budget dropped retrieved documents under pressure. That is one lever. M5-L10 added a second:
the conversation-state strategy itself can be downgraded — full history, then last-N, then a summary,
then structured state — each one cheaper and each one losing more. **A real assembler needs an explicit
order across *both* levers**, decided before the budget gets tight, not improvised when it does.

---

## 4. Analogy

**A ship's logbook, kept by a rotating watch.** Each new officer reads yesterday's entries before their
shift. The logbook has finite pages, so once a week the crew condenses the week's entries into one
**passage summary** and archives the originals. Officers on later weeks read the passage summaries, not
the raw log.

If every week's passage summary is written by condensing **last week's summary** rather than that week's
actual log entries, small omissions compound: a course correction mentioned once, three weeks back, and
never restated, quietly disappears from every summary after it. The fix a careful ship keeps is to
**check the passage summary against the raw log periodically** — not every week, because that is as
much work as never summarising at all, but often enough that no single omission survives unchallenged
for the whole voyage.

### Where the analogy breaks

- **A human editor notices when something feels important** and preserves it disproportionately. An
  automated summarizer follows the same instruction every time — which sounds worse, but is actually the
  useful property: its omissions are **systematic**, not incidental, so you can find and fix them by
  reading the summarization prompt (§7.2's disclaimer, and §6's worked example).
- **A logbook's page limit is physically visible.** A token budget is not — nobody notices it filling up
  until a request is refused or an answer is quietly wrong.
- **An officer can ask a crewmate what actually happened.** A summarization pass has no other source; if
  the fact is not in what you feed it, it does not exist for that pass.

---

## 5. Detailed technical explanation

### 5.1 Trigger policies compared

A turn-count trigger and a token-count trigger are supposed to mean the same thing: "history is getting
expensive, do something about it." §7.1 shows they do not agree.

| Profile | tok/exchange | "every 10 turns" fires at | "every 3,000 tokens" fires at |
|---|---|---|---|
| Chatty (short messages) | 75 | 750 tokens | turn 40 |
| Verbose (long messages) | 600 | 6,000 tokens | turn 5 |

**The same rule, "every 10 turns," fires at an 8× difference in token cost** depending on how your users
happen to write. The token-threshold trigger fires at a consistent *budget position* regardless — which
is the thing you actually meant to bound. **Trigger on tokens, not turns**, unless you have measured that
your traffic is uniform enough for turn count to be a safe proxy.

### 5.2 Cascading drift, and what checkpointing buys

Model each fact in a conversation as surviving one summarization pass with some fixed probability. A
cascading pass compresses the *previous summary*, so a fact must survive **every pass since the
conversation began** to still be present. §7.2 measured this exactly, at a 90%-per-pass survival rate,
across 15 facts and 12 passes:

| Pass | Cascade | Checkpoint-3 | Checkpoint-5 |
|---|---|---|---|
| 1 | 15/15 | 15/15 | 15/15 |
| 6 | 10/15 | 15/15 | 13/15 |
| 12 | **4/15 (27%)** | **15/15 (100%)** | **12/15 (80%)** |

**Cascading decays toward zero** because loss compounds — one bad pass is permanent for every pass after
it. **Checkpointing resets the clock periodically**, by re-deriving the summary from source rather than
from the last summary, and the difference at pass 12 is stark: 27% survival against 100%.

That recovery is not free:

| Strategy | Tokens read over 12 passes | vs cascade |
|---|---|---|
| Cascade | 3,480 | 1.0× |
| Checkpoint-3 | 17,320 | **5.0×** |
| Checkpoint-5 | 10,400 | **3.0×** |

**A checkpoint pass re-reads the whole transcript so far, not just the last summary.** More frequent
checkpointing (every 3 passes) recovers more fidelity and costs more; less frequent (every 5) is a
cheaper, looser bound. **Neither number is universal — it is a dial you set against how expensive being
wrong is for your application**, exactly the kind of trade-off a support-ticket summary and a medical
intake summary would set very differently.

### 5.3 One budget, every lever

Extend M4-L06's budget with the levers M5-L10 priced. Fixed components (system, tools, current message,
output reserve) are never dropped. Under pressure, two things degrade, in an order you choose in
advance: §7.3 uses **documents first, conversation-state strategy second**.

| Scenario | Usable budget | Conversation state picked | Docs kept |
|---|---|---|---|
| Generous | 113,850 tok | full history (8,180 tok) | 10 of 10 |
| Tight | 5,000 tok | structured state + last 2 (815 tok) | 3 of 10 |
| Very tight | 700 tok | — | **REFUSED** |

**The very-tight case refuses rather than serving a broken request** — the fixed components alone
(1,700 tokens: system + tools + current message) exceed the usable budget, so nothing can be built. This
is the same principle M4-L06 established for the system prompt, applied to the whole fixed set: **a
budget that silently drops something marked "never drop" is worse than one that fails loudly.**

### 5.4 Truncation vs summarization: which lever for which content

| | Truncation (M4-L06) | Summarization (M5-L10, §5.2 here) |
|---|---|---|
| Cost | Free — just cut | An extra model call, every trigger |
| What it preserves | Whichever part you keep, verbatim | The gist, in the summarizer's words |
| Good for | Content whose value is **positional** — recent messages, top-ranked documents | Content whose value is **aggregate** — the shape of a long history you still need the gist of |
| Failure mode | Loses a known fraction, predictably | Can silently misstate what it kept (§6) |

**Use truncation where recency or rank already tells you what matters.** Use summarization only where you
need the gist of material you cannot afford to keep verbatim — and once you do, §5.2's drift applies.

### 5.5 Monitoring: what actually happens, not what the demo showed

§7.4 takes a traffic percentile table and a token-threshold trigger and asks a plain question: **how much
of your real traffic ever reaches the trigger?**

| Percentile | Turns | Reduction trigger (turn 15) |
|---|---|---|
| p50 | 6 | does not fire |
| p75 | 12 | does not fire |
| p90 | 22 | **FIRES** |
| p99 | 61 | **FIRES** |

**At least 10% of conversations (everything at or above p90) cross the trigger**, and at least 1% reach
lengths where even the cheapest state option is under real pressure. At 100,000 conversations a month,
that 1% is 1,000 conversations experiencing your most aggressive degradation — not an edge case, a
population. **What to track in production**: the % of requests hitting any reduction, the % hitting the
cheapest option, the % refused outright, and — the check people skip — whether degraded requests
correlate with your **longest, most engaged users**, who are usually your most valuable ones and the
first to feel a badly-tuned trigger.

### 5.6 Assumptions and limitations

- §7.2's per-pass survival probability is a deliberate simplification. Real summarization failures are
  frequently **systematic** — the same clause shape dropped every time — not the independent-random
  model used here. §6 shows a systematic failure; treat §7.2 as showing the *shape* of drift, not a
  forecast for any specific summarizer.
- §7.4's traffic percentiles are illustrative. Measure your own conversation-length distribution before
  setting a threshold.
- Nothing here calls a real model. Whether a given summarizer preserves a given fact is an empirical
  question about that model and that prompt — test it directly before trusting it in production.

---

## 6. Worked example — the assistant that resurrected a feature the user had cut

**The system.** A coding assistant keeps a rolling summary of "what has been decided" across a long
session, updated each pass from the previous summary plus the newest few turns — exactly the cascading
pattern in §5.2.

**Turn 4.** User: *"Add a CSV export to the reports page."* Turn 5, implemented. Summary updates to:
*"Added CSV export (reports page)."*

**Turn 22.** User: *"Security flagged CSV export for PII exposure — please remove it entirely, and don't
add it back."* The assistant removes it. The summarizer, instructed to "keep the summary to short
bullet points," compresses the two-clause outcome — *added, then removed at security's request* — down
to its shortest noun phrase. The new summary reads: **"CSV export: added (reports page)."** The removal
is gone. This did not take twelve cascading passes to happen; **it happened on the very next pass**,
because the instruction rewarding brevity discarded the qualifying clause the first time it appeared.

**Turns 23–45.** Unrelated work. Nothing contradicts the wrong bullet, so it survives, unchanged, in
every summary from here on — there is no checkpoint back to source, and no new signal to disturb it.

**Turn 46.** User: *"Can you add a PDF export next to the CSV one?"* — a request that assumes CSV export
still exists. Working from the summary, the assistant agrees, and generates a PDF export that reuses the
CSV export code path — **reintroducing exactly the feature security had asked to have removed.**

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The summarizer compressed a status *reversal* into a bare positive statement, in one pass | The most recent, most consequential fact was the one lost |
| 2 | No checkpoint ever re-derived the summary from source or from an authoritative record | The error had 23 turns to become load-bearing before anyone asked a question that exposed it |
| 3 | "Is CSV export currently enabled" was tracked in prose, not as a status field | A two-valued fact, changed exactly once, was exactly the kind §5.4 says belongs in structured state |

### The fix

**Track feature status as structured state, not prose:**

```python
features = [
    {"name": "csv_export", "status": "removed",
     "changed_at_turn": 22, "reason": "security review"},
]
```

Sent alongside — or instead of — the rolling summary. A status field cannot be silently reworded away
the way a prose clause can; it is either `"removed"` or it is not.

**Add a periodic checkpoint** (§5.2) that re-derives status fields from the actual source — the real
transcript, or better, the real codebase's feature flags — rather than trusting the chain of prior
summaries indefinitely.

**Fix the summarization prompt itself**, since this failure is systematic and therefore fixable:
instruct it explicitly to preserve status changes and negations verbatim, and never compress a "removed"
or "reversed" decision into a bare positive statement.

**The general rule.** **Any fact whose value is "still true or not" belongs in structured state, not
prose** — because prose compression fails exactly where the negation is, and a fixed summarization
instruction fails there **the same way every time you ask it to be brief.**

---

## 7. Practical activity

**File:** [`labs/m5/l11_context_engineering.py`](../../labs/m5/l11_context_engineering.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l11_context_engineering.py
```

Sections 1, 3 and 4 are real token/cost arithmetic on stated inputs. Section 2 uses a deterministic mock
compressor — real arithmetic on a simplified, clearly-labelled model of summarization loss — to make the
shape of cascading drift measurable without needing a live model call.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6, tiktoken 0.14.0.

```text
============================================================================
1. TRIGGER POLICIES: A FIXED TURN COUNT LIES TO YOU
============================================================================
  Same task, two very different conversations. Per-exchange size
  200 tok/exchange throughout (M5-L10's figures).

  Two trigger policies: every 10 turns, or once history
  exceeds 3,000 tokens.

  profile                                tok/exchange  turn-trigger fires at  token-trigger fires at
  chatty (short messages, many turns)              75                750 tok                 turn 40
  verbose (long messages, few turns)              600              6,000 tok                  turn 5

  Read the turn-trigger column: the SAME rule ('every 10 turns')
  fires at wildly different token totals depending on how chatty the
  conversation is. A turn-count trigger is really a token-count
  trigger in disguise, with an error bar the width of your users'
  writing style. The token-threshold trigger fires at a materially
  more consistent BUDGET POSITION across both profiles -- which is
  the thing you actually meant to bound.

============================================================================
2. CASCADING SUMMARIZATION DRIFT  [MOCK compressor, REAL arithmetic]
============================================================================
  15 facts established once, at the start of a conversation.
  Each summarization pass keeps a fact with probability 90%
  (10% chance of loss per pass) -- a simplified stand-in
  for a real summarizer's imperfect compression. Two strategies:

    CASCADE      -- always summarise the previous summary
    CHECKPOINT-K -- every K passes, re-derive the summary from the
                    original source material instead of the last
                    summary, resetting every fact to 'present'

   pass   cascade    checkpoint-3    checkpoint-5
      1     15/15           15/15           15/15
      2     15/15           15/15           15/15
      3     14/15           15/15           14/15
      4     14/15           15/15           14/15
      5     12/15           13/15           15/15
      6     10/15           15/15           13/15
      7      8/15           13/15           11/15
      8      8/15           12/15           10/15
      9      6/15           15/15            8/15
     10      6/15           15/15           15/15
     11      5/15           13/15           13/15
     12      4/15           15/15           12/15

  At pass 12: cascade keeps 4/15 facts (27%)
  checkpoint-3 keeps 15/15 facts (100%) after 12 passes
  checkpoint-5 keeps 12/15 facts (80%) after 12 passes

  Cascading decays toward zero because loss compounds: a fact must
  survive EVERY pass since the start to still be present. Checkpointing
  resets that clock periodically, trading a bounded, recurring cost
  for a bounded, recurring recovery.

  Cost: a cascade pass reads only the last summary + new turns --
  290 tok/pass, 3,480 tok over 12 passes.

  strategy          tokens read over 12 passes   vs cascade
  cascade                                3,480         1.0x
  checkpoint-3                          17,320         5.0x
  checkpoint-5                          10,400         3.0x

  Checkpointing costs more -- it periodically re-reads the whole
  transcript instead of a short summary -- and that is the price of
  bounding drift rather than merely delaying it.

============================================================================
3. ONE BUDGET, FOUR COMPONENTS
============================================================================
  window 128,000, output reserve 1,500, system 900, tools 600, user msg 200, headroom 90%
  conversation-state levers (from M5-L10, priced at turn 40):
    full history                  8,180 tok
    last N (N=6)                  1,580 tok
    summary + last 4              1,270 tok
    structured state + last 2       815 tok
  retrieved documents: 750 tok/doc, ranked, drop lowest first

  generous request  (10 docs wanted)  (usable budget 113,850 tok)
    keep   system + tools + user msg             1,700
    pick   conversation state: full history                 8,180
    keep   retrieved docs (10 of 10 wanted, 750 tok each)     7,500
    input total                                17,380
    output reserved                             1,500
    window used                                14.8%

  tight request     (10 docs wanted, smaller budget)  (usable budget 5,000 tok)
    keep   system + tools + user msg             1,700
    pick   conversation state: structured state + last 2      815
    keep   retrieved docs (3 of 10 wanted, 750 tok each)     2,250
    DROP   7 lowest-ranked document(s)
    input total                                 4,765
    output reserved                             1,500
    window used                                 4.9%

  very tight request (10 docs wanted, tiny budget)  (usable budget 700 tok)
    REFUSED: fixed components (1,700) exceed the usable budget (700) -- this request cannot be built
  Note what changed as the budget shrank: first the DOCUMENT count
  dropped, then the CONVERSATION-STATE strategy downgraded to a
  cheaper one -- an explicit order, decided in advance, not whichever
  component happened to be assembled last.

============================================================================
4. HOW OFTEN DOES THE TRIGGER ACTUALLY FIRE?
============================================================================
  A synthetic conversation-length distribution across a day's traffic
  (illustrative percentiles; measure your own):

  percentile    turns   approx tokens
  p50               6          1,200
  p75              12          2,400
  p90              22          4,400
  p99              61         12,200
  max             140         28,000

  The 3,000-token reduction trigger fires at turn 15.
    p50 (6 turns): does not fire
    p75 (12 turns): does not fire
    p90 (22 turns): FIRES
    p99 (61 turns): FIRES
    max (140 turns): FIRES

  Reading the table: at least 10% of conversations (p90) cross the
  reduction trigger, and at least 1% (p99) reach lengths where even
  the cheapest conversation-state option plus a full document
  allocation is under real pressure. Those are not edge cases you
  can ignore -- at 100,000 conversations/month, p99 alone is 1,000
  conversations experiencing your MOST aggressive degradation.

  What to actually monitor in production, per day:
    - % of requests that triggered ANY reduction
    - % that triggered the CHEAPEST conversation-state option
    - % that were REFUSED outright (section 3's failure mode)
    - whether degraded requests correlate with your longest, most
      engaged conversations -- often your most valuable users, and
      the ones a naive fixed trigger degrades hardest

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: sections 1, 3 and 4 -- exact arithmetic on stated inputs,
  using tiktoken cl100k_base for the M5-L10 figures re-used in section 3.

  MOCK: section 2's compressor. 'A fact survives a pass with fixed
  probability, independent of the others' is a simplification. Real
  summarization failures are often SYSTEMATIC rather than random --
  the same kind of clause gets dropped every time -- which is worse
  in one way (predictably repeatable) and better in another (you can
  find and fix it by reading the summarization prompt). See the
  lesson's worked example for a systematic failure, not a random one.

  ILLUSTRATIVE: section 4's traffic percentiles. Measure your own
  conversation-length distribution before setting a trigger threshold.

  NOT SHOWN: an actual model call. Whether a real summarizer keeps a
  given fact is an empirical question about that model and that
  prompt -- this lab measures the SHAPE of the drift and cost
  trade-off, not any particular summarizer's behaviour.

Done.
```

### 7.3 Reading the result

**Section 1 makes the disguise literal.** "Every 10 turns" fires at 750 tokens for a chatty profile and
6,000 for a verbose one — an 8× spread from the same rule. A token-threshold trigger fires at a
consistent budget position across both. If your trigger is turn-based today, this is the argument for
changing it, in one measured number.

**Section 2 is the lesson's central result.** Cascading summarization keeps 27% of facts after 12
passes; checkpointing every 3 passes keeps 100%, at 5× the token cost of never checkpointing at all.
Neither number is universal, but the **shape** is: cascading decays because loss compounds, and
checkpointing trades a recurring cost for a recurring reset. Decide the checkpoint interval by how
expensive being wrong is for your application, not by a default.

**Section 3 shows the two levers working together.** As the budget shrank across three scenarios, the
assembler dropped documents first (10 → 3) and only then downgraded the conversation-state strategy
(full history → structured state), and when even the fixed components did not fit, it **refused** rather
than silently cutting something marked never-drop. That refusal message states both numbers — the fixed
cost and the usable budget — which is the difference between a bug report you can act on and a truncated
prompt nobody notices went wrong.

**Section 4 turns the trigger into an operational metric.** At least 10% of conversations in the stated
traffic profile cross the reduction trigger; at 100,000 conversations a month that is a five-figure
population experiencing degraded context, not a rounding error. The uncomfortable follow-up question —
whether those are disproportionately your longest, most engaged users — is the one worth asking before
tuning a threshold purely for cost.

---

## 8. Common mistakes and troubleshooting

1. **Triggering summarization on turn count.** Trigger on tokens; §7.1 measures the gap.
2. **Cascading forever with no checkpoint.** Drift compounds silently until a question exposes it (§6).
3. **Checkpointing every pass "to be safe."** That is the cascade's token cost with none of its savings —
   pick an interval, don't default to the extremes.
4. **Putting a status fact in a prose summary.** Negations and reversals are exactly what brevity-tuned
   summarization drops first (§6). Use structured state.
5. **Only budgeting for documents, forgetting conversation state is also a lever.** §5.3's assembler needs
   both.
6. **Silently truncating a "never drop" component when the budget is too tight.** Refuse, and say why
   (M4-L06, §5.3).
7. **Assuming the demo's conversation length represents production.** §7.4: measure your own percentile
   distribution.
8. **Not monitoring how often the trigger fires.** A threshold that never fires in testing can fire for
   10% of real traffic.
9. **Treating summarization as free.** It is an extra model call, every time it triggers, and checkpoints
   cost more still.
10. **Assuming a real summarizer's failures are random.** They are usually systematic — a fixable prompt
    bug, not an unavoidable cost (§7.2, §6).

| Symptom | Likely cause | Fix |
|---|---|---|
| Assistant contradicts a decision made many turns ago | Cascading drift with no checkpoint | Add checkpoint resummarization; move the fact to structured state |
| Trigger never fires in staging, fires constantly in production | Turn-count trigger, chattier real users | Switch to a token-threshold trigger |
| Costs spike after adding checkpointing | Checkpoint interval too tight | Widen the interval; price it as in §7.2 |
| Requests fail unpredictably at long conversation lengths | No refusal path for over-budget fixed components | Add an explicit refusal, stated in tokens |
| A status the user explicitly reversed reappears later | Reversal compressed into a bare positive statement | Track status as structured state; fix the summarization prompt |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** A summary that silently drops a reversal is a correctness bug, not a cosmetic one —
  §6's assistant reintroduced a feature a security review had removed. Track status facts as structured
  state precisely to avoid this class of failure.
- **Reliability.** Refuse a request whose fixed components do not fit the budget. A silently truncated
  system prompt or tool definition is a worse failure than a declined request (M4-L06).
- **Security.** A removed or restricted capability that reappears because of summarization drift is a
  security regression, not just a UX bug — treat status-of-security-relevant-features as structured
  state with an audit trail, not prose.
- **Cost.** Checkpoint resummarization costs materially more than cascading — §7.2 measured 3–5× more
  tokens read over the same number of passes. Set the interval deliberately against how costly being
  wrong is, not by default.
- **Cost.** A token-count trigger, unlike a turn-count one, keeps your worst-case request size bounded
  regardless of how verbose your users get — which also bounds latency and KV cache cost (M4-L06 §5.6).
- **Privacy.** A checkpoint pass that re-reads the full transcript re-exposes everything in it to the
  summarization call, including anything that should have been redacted since — apply redaction before
  the checkpoint, not only before display.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why does a "summarise every 10 turns" rule fire at different token totals for different users?
2. In one sentence, why does cascading summarization decay while checkpointing does not?
3. Name the two levers a full budget assembler must arbitrate between, beyond fixed components.
4. What should a budget do when even its fixed, never-drop components do not fit?
5. Give one example of a fact that belongs in structured state rather than prose, and say why.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the fact-survival percentage for cascading vs checkpoint-3 at pass 12, and the
   token cost ratio between them.
2. Change `SURVIVAL_P` to 0.95 and 0.80 and re-run section 2. Describe how sensitive the pass-12 result
   is to this single number.
3. Extend the §7.3 budget assembler with a fifth component (e.g. few-shot examples) and give it an
   explicit priority position. Test a scenario where it is the first thing dropped.
4. Using your own recent chat history with an AI assistant (or a synthetic one), estimate its token
   growth curve and state at what turn a 3,000-token trigger would have fired.
5. Write a monitoring query (pseudocode is fine) that reports, per day, the % of requests hitting each
   degradation level from §7.4's list.

### Exercise 3 — Challenge (~50 min)

1. Build a `ContextEngineer` that combines M4-L06's `TokenBudget` and M5-L10's four conversation-state
   strategies behind one `assemble()` call with an explicit, testable priority order across documents and
   conversation state.
2. Implement checkpoint resummarization for a synthetic long conversation, with a configurable interval,
   and measure fidelity vs cost at three intervals of your choosing.
3. Design a structured-state schema for a domain of your choice (support tickets, a coding session, a
   booking flow) that captures every fact whose value is "still true or not," and justify each field
   against §5.4's criterion.
4. Reproduce §6's failure with a real model: write a summarization prompt, feed it a reversal across two
   passes, and check whether the reversal survives. If it does not, fix the prompt and re-test.
5. Write the on-call runbook entry for "a user reports the assistant referencing something they explicitly
   removed" — the checks, in order, from symptom to root cause.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l11).)*

**Q1.** A "summarise every 10 turns" rule fires at 750 tokens for one user profile and 6,000 for another.
The reason is:

- A. A bug in the token counter.
- B. Ten turns is not a fixed amount of text; the rule is really a token-count trigger in disguise.
- C. The two profiles use different models.
- D. Turn-count triggers are always more reliable than token triggers.

**Q2.** Cascading summarization decays toward zero over many passes because:

- A. The model's context window shrinks over time.
- B. Each pass introduces independent noise unrelated to earlier passes.
- C. A fact must survive every pass since the conversation began to still be present, so loss compounds.
- D. Later summaries are always shorter than earlier ones by design.

**Q3.** At pass 12, cascading kept 27% of facts and checkpoint-3 kept 100%. The cost of that recovery
was:

- A. Nothing — checkpointing is free.
- B. A reduction in the model's context window.
- C. The loss of the ability to summarise at all.
- D. About 5× more tokens read over the same 12 passes.

**Q4.** In the §5.3 budget assembler, as the budget shrank across scenarios, what degraded first?

- A. The number of retrieved documents, before the conversation-state strategy changed.
- B. The system prompt.
- C. The output reservation.
- D. The user's current message.

**Q5.** When even the fixed, never-drop components of a request do not fit the usable budget, the
assembler should:

- A. Truncate the system prompt to make room.
- B. Refuse the request and state both numbers.
- C. Drop the output reservation instead.
- D. Silently proceed with whatever fits.

**Q6.** Which fact is the best candidate for structured state rather than a prose summary?

- A. A general description of the user's mood across the conversation.
- B. A paraphrase of the user's opening message.
- C. The overall tone the assistant should use.
- D. Whether a specific feature is currently enabled or removed.

**Q7.** In §6, the CSV-export bug occurred because:

- A. The summarizer compressed "added, then removed" into "added," in a single pass, favouring brevity.
- B. The model hallucinated a feature that was never built.
- C. The conversation exceeded the context window and lost the removal turn entirely.
- D. The user never actually asked for the removal.

**Q8.** According to §7.2's disclaimer, real summarization failures are usually:

- A. Purely random, and therefore impossible to fix.
- B. Identical in every model and every prompt.
- C. Systematic — the same kind of clause dropped every time — which makes them findable and fixable.
- D. Limited to very long conversations only.

**Q9.** At p90 of the §7.4 traffic distribution, the reduction trigger:

- A. Never fires, since p90 is a rare case.
- B. Only fires for conversations above the maximum observed length.
- C. Fires for exactly 90% of conversations.
- D. Fires, meaning at least 10% of conversations cross it.

**Q10.** Checkpoint resummarization differs from cascading summarization in that it:

- A. Never re-reads the source material.
- B. Periodically regenerates the summary from source instead of from the last summary, bounding drift at a higher token cost.
- C. Produces a shorter summary every time.
- D. Is always cheaper than cascading.

**Q11.** The general rule this lesson draws from §6 is:

- A. Never use rolling summaries for anything.
- B. Summarization should always run on every single turn.
- C. Any fact whose value is "still true or not" belongs in structured state, not prose.
- D. Checkpointing should happen after every pass, without exception.

**Q12.** A budget assembler should degrade components in:

- A. An explicit priority order decided in advance, consistent across requests.
- B. Whatever order they happen to be assembled in code.
- C. Random order, to distribute risk.
- D. Alphabetical order of component name.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's assistant has been running for three
months with a rolling summary that cascades with no checkpoint. A user just reported the assistant
confidently referencing a decision that was reversed six weeks ago. State what you would check first,
what you would change, and how you would verify the fix without waiting another six weeks for the same
bug to resurface.

---

## 12. Revision notes

- **A turn-count trigger is a token-count trigger in disguise** — the same rule fires at an 8× different
  budget position depending on how verbose your users are. Trigger on tokens.
- **Cascading summarization decays because loss compounds**: a fact must survive every pass since the
  start to still be present. Measured: **27% survival after 12 passes.**
- **Checkpoint resummarization bounds drift by re-deriving from source periodically** — measured
  **100% survival at 3–5× the token cost** of never checkpointing. Set the interval by how costly being
  wrong is.
- **A full budget has two degradable levers, not one**: retrieved documents and the conversation-state
  strategy itself. Order them explicitly, in advance.
- **Refuse rather than silently truncate a "never drop" component** — a stated refusal with both numbers
  beats a silently broken prompt.
- **Real summarization failures are usually systematic, not random** — the same clause shape dropped
  every time — which means they are findable by reading the prompt, and fixable.
- **Any fact whose value is "still true or not" belongs in structured state, not prose** — a status field
  cannot be silently reworded away the way a summary's clause can.
- **Measure your own trigger-firing rate in production.** A threshold that never fires in testing can
  fire for 10%+ of real traffic, and it is often your longest, most valuable conversations that hit it
  hardest.

---

## 13. Completion checklist

- [ ] My summarization trigger is token-based, not turn-based.
- [ ] I know, for my own system, whether it cascades or checkpoints — and I chose that deliberately.
- [ ] I can state the cost multiple of checkpointing over cascading for my chosen interval.
- [ ] My budget assembler has an explicit, documented order for degrading documents vs conversation state.
- [ ] My budget refuses rather than silently truncating a "never drop" component.
- [ ] Every status-type fact ("is X still true") lives in structured state, not a prose summary.
- [ ] I monitor the % of production requests that hit each degradation level.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Liu, N. F., et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts*.
  <https://arxiv.org/abs/2307.03172> `[UNVERIFIED]`
- Anthropic — Prompt caching documentation (relevant to the cost of repeated checkpoint reads).
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching> `[UNVERIFIED]`
- OpenAI — Managing conversation state.
  <https://platform.openai.com/docs/guides/conversation-state> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L12 — Prompt Versioning and Regression Testing](M5-L12-prompt-versioning.md)

You can now decide what enters the context and when it changes shape. Next: treating the prompts
themselves — including the summarization prompt this lesson leaned on — as versioned artefacts you can
test, compare and roll back.
