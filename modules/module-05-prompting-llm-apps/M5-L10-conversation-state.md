# M5-L10 — Conversation State: What You Store and What You Resend

| | |
|---|---|
| **Lesson ID** | M5-L10 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M4-L16](../module-04-genai-llm-internals/M4-L16-knowledge-vs-context.md) |

---

## 1. Learning objectives

1. **Explain** why a conversation appears to have memory, and name what actually carries it across requests.
2. **Compute** the token and cost growth of resending full history, and state why it is quadratic, not linear.
3. **Compare** four conversation-state strategies on cost and on what each one loses.
4. **Design** a state record that separates what you store from what you send, and survives a deletion request.
5. **Recognise** cross-conversation state leakage as a class of bug, and state the fix.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Conversation state** | Whatever your application carries forward from earlier turns into the next request. |
| **Full-history resend** | Sending every prior turn, verbatim, with each new request. |
| **Sliding window (last-N)** | Keeping only the most recent N turns and dropping the rest. |
| **Rolling summary** | A model-generated prose condensation of older turns, updated as the conversation grows. |
| **Structured state** | A schema of named fields (facts) extracted from the conversation, instead of prose. |
| **Context budget** | The token allowance you set aside for history, distinct from the model's context window. |
| **Store vs send** | What your database retains (audit, support) versus what goes into the next prompt. |
| **Retention policy** | The rule for how long a record is kept and when it must be deleted. |
| **State drift** | Errors that compound when a summary is generated from a previous summary rather than the source. |

---

## 3. Plain-language explanation

### 3.1 The model has no memory — your application does the remembering

M4-L16 established this and it is worth restating precisely, because everything in this lesson follows
from it:

> **Every API request is independent. The model retains nothing between requests.**

A conversation feels continuous because *your application* resends the prior turns on every request.
"Conversation state" is not a model feature you switch on — it is code you write, and every design
choice in it is yours to get wrong.

### 3.2 Resending everything costs more than it looks like it should

Each turn adds a fixed amount to the history. **Every later turn pays for that addition again.** Ten
turns of conversation do not cost ten times what one turn costs — they cost roughly fifty-five times
what one turn costs, because turn 10 also resends turns 1 through 9, turn 9 resends 1 through 8, and so
on. §7.3 puts a number on it: an 80-turn conversation sends **662,400** input tokens in total, against
**30,400** if only the new turn were sent each time.

### 3.3 There is no free lunch, only priced trade-offs

You can stop paying that bill by not resending everything — a sliding window, a summary, a structured
record. Each one is cheaper. **None of them is free**, because each one is also a decision about what
the model is allowed to forget. §7.4 measures that loss directly, not by guessing but by asking twelve
concrete follow-up questions and checking which strategies can still answer them.

### 3.4 Two different questions get answered as if they were one

*"What do we keep?"* and *"what do we resend?"* sound like the same question. They are not. Your audit
trail, your support team and your analytics all want the full transcript, kept for years. Your next API
call wants the smallest thing that lets the model do its job, resent every few seconds. Conflating the
two is where most of the mistakes in this lesson come from.

---

## 4. Analogy

A locum doctor covering a hospital ward has never met any of the patients. Each shift, they read the
handoff note the previous shift left: current medication, the last set of readings, what to watch for.
They treat the patient competently *from the note* — not from memory, because there is none to draw on.

If the note is thorough, the locum picks up exactly where the last shift left off. If the note-writer
condensed six hours of observations into two lines, whatever they judged unimportant is gone — not
hidden, not recoverable from the patient's chart of *this* shift, simply absent from what the next
doctor can act on. And if two patients' folders ever get mixed up at the nurses' station, the locum will
confidently treat the wrong person from someone else's notes, because nothing about reading a folder
tells you whether it is the *right* folder.

### Where the analogy breaks

- **A locum can ask the patient directly** to fill a gap the notes missed. A model can only work from
  what is in the prompt; there is no patient to interrupt with a question.
- **A human note-writer has judgment about what matters medically.** A summarization prompt has whatever
  judgment you wrote into it, applied identically every time, including the times it is wrong.
- **A folder mix-up at a hospital is rare and visible.** A conversation-state mix-up is silent — the
  assistant does not know it has the wrong record, and neither, at first, does anyone reading its output.

---

## 5. Detailed technical explanation

### 5.1 The quadratic cost of full history

`[REAL arithmetic; illustrative prices]` System + tool definitions 320 tok, a 60-tok user turn, a
140-tok assistant turn, $0.50/M in, $2.00/M out:

| Turn | Input tokens | Cost this turn | Cumulative | vs turn 1 |
|---|---|---|---|---|
| 1 | 380 | $0.00047 | $0.0005 | 1.0× |
| 2 | 580 | $0.00057 | $0.0010 | 1.2× |
| 5 | 1,180 | $0.00087 | $0.0033 | 1.9× |
| 10 | 2,180 | $0.00137 | $0.0092 | 2.9× |
| 20 | 4,180 | $0.00237 | $0.0284 | 5.0× |
| 40 | 8,180 | $0.00437 | $0.0968 | 9.3× |
| **80** | **16,180** | $0.00837 | **$0.3536** | **17.8×** |

**Read the mechanism, not just the numbers.** Turn 80's input is **42.6×** turn 1's — for a user message
that is, on its own terms, no more valuable than their first one. It costs more only because it now
drags 79 prior turns behind it. Sum that cost across all 80 turns and you get **662,400** input tokens
sent in total. If the model had memory and you sent only the new turn each time, the same conversation
would cost **30,400** tokens — a **21.8×** difference. That factor is the price of statelessness, paid
in full unless you do something about it.

### 5.2 Where the tokens actually go

`[REAL]` An eight-turn support exchange, tokenized with `tiktoken`:

| # | Role | Tokens | Text |
|---|---|---|---|
| 1 | user | 14 | "My order GB-4471 arrived damaged, the screen…" |
| 2 | assistant | 36 | "I'm sorry to hear that. I can see order GB-44…" |
| 3 | user | 4 | "A refund please." |
| 4 | assistant | 32 | "Of course. I've noted a refund request for GB…" |
| 5 | user | 5 | "Yes that's right." |
| 6 | assistant | 38 | "Thank you. The refund of 42.50 GBP to the car…" |
| 7 | user | 7 | "No that's all, thanks." |
| 8 | assistant | 22 | "You're very welcome. I've emailed a confirmat…" |
| | **TOTAL** | **158** | |

The facts a later turn actually needs are five: `GB-4471, damaged, refund, 4412, 42.50`. Written as a
state record — `"order GB-4471 damaged; refund agreed; card 4412; amount 42.50 GBP"` — that is **21
tokens against 158**, a **7.5× smaller** send.

**That ratio is simultaneously the opportunity and the risk.** The saving is real. So is the fact that
*you* decided what counted as "the facts a later turn needs" — and anything you did not put in that
sentence is gone the moment the raw transcript stops being sent.

### 5.3 Four strategies, priced

`[REAL arithmetic]` A 4,000-token budget for history, 200 tokens per exchange, measured at turn 40:

| Strategy | Turns kept | Input tokens | |
|---|---|---|---|
| Send everything | 39 | 8,180 | **OVER BUDGET** |
| Last N (N=6) | 6 | 1,580 | |
| Summary + last 4 | 4 | 1,270 | |
| Structured state + last 2 | 2 | 815 | |

| Strategy | Cost/turn at 40 | vs everything |
|---|---|---|
| Send everything | $0.00437 | 100% |
| Last N (N=6) | $0.00107 | 24% |
| Summary + last 4 | $0.00091 | 21% |
| Structured state + last 2 | $0.00069 | **16%** |

**Cost is not the interesting column — §5.4 is.** Every non-full strategy is dramatically cheaper. That
tells you nothing about what it still knows.

### 5.4 What each strategy loses

`[MOCK]` Twelve questions a user might plausibly ask at turn 40, each needing a fact from a specific
earlier turn:

| Strategy | Questions answered (of 12) |
|---|---|
| Send everything | **12** |
| Last N (N=6) | 1 |
| Summary + last 4 | 7 |
| Structured state + last 2 | 7 |

**Read the rows that fail for summary and structured state but not for "everything."** Every one of them
is a detail nobody thought to put in the summary or the schema — the exact wording used, a second option
that was offered and declined, an offhand remark twelve turns back. They are not retrievable now, and
the model will not say so — **it will answer confidently from whatever it has.**

**Summary and structured state score the same here and fail differently.** Structured state's omissions
are *predictable*: the schema states exactly which fields exist, so you know in advance what it cannot
answer. A prose summary's omissions are whatever the summarizer happened to leave out this time — which
can change between runs of the identical conversation.

### 5.5 Designing a structured-state record

If §5.4's predictability is the reason to prefer structured state, here is what "predictable" requires
in practice:

- **A small, named schema** — `order_id`, `issue`, `resolution`, `payment_method_last4` — not a
  free-text field that quietly becomes a second summary.
- **A primary key that identifies the *person*, not the interaction.** §6 is what goes wrong when this
  is skipped.
- **An owner check on every read.** Fetching a record because a key matches is not the same as
  confirming it belongs to the party you are currently talking to.
- **An explicit TTL or invalidation trigger**, tied to the same event that ends the underlying case —
  not a second, independently-guessed expiry living in a different system.
- **A version tag on the extraction prompt that produced it**, for the same reason covered next.

### 5.6 Store is not send

| Concern | Store | Send |
|---|---|---|
| Full transcript | Yes, with a retention policy | No |
| Structured state | Yes — it is the record | Yes |
| Summaries | Yes, and version them | Yes |
| Tool call arguments | Names + outcomes only | Yes, current turn |
| PII in messages | Only with a lawful basis | Minimise |
| Deleted-account data | Must be erasable | n/a |

Three consequences people discover late:

1. **A deletion request must reach the summary too.** A summary derived from a deleted message still
   contains it, until the summary is regenerated or edited (M10-L06).
2. **A summary is a derived artefact and must be versioned with the prompt that produced it.** Without
   that, you cannot reproduce or explain a stored conversation's summary later (M5-L12).
3. **Context is not memory.** Two users sharing a session, a shared inbox, an agent taking over a
   ticket — all of these put one person's data in another's context if state is keyed loosely. §6 is the
   worked case.

**And the failure mode nobody tests for:** in a 40-turn conversation resent in full every turn, the
*first* message is transmitted 40 times and the last one once — **20.5 times on average** across the
whole conversation. A card number typed by mistake in turn 3 has gone to the provider **38 times** by
turn 40. Redacting it from your own database afterwards does not unsend those 38 transmissions, and a
retention clock that starts when *you* store it started 37 transmissions too late.

### 5.7 Assumptions and limitations

- §5.1, §5.2, §5.3 and §5.6 are real: token counts come from `tiktoken`, the cost tables are arithmetic
  on stated inputs.
- §5.4's survival rules are a simplification — "the last N turns, plus whatever a summary happens to
  contain." Real summarizers keep and drop things less predictably than that, which makes the real
  picture **worse**, not better.
- Prices, TTFT-independent as this lesson is, are still illustrative and dated; check current pricing.
- Presence in context is not the same as the model using it. A fact that survives your state strategy
  can still be missed at inference time — that is a separate failure mode (M4-L06, M7-L11).

---

## 6. Worked example — the assistant that remembered the wrong customer

**The system.** A support widget stores conversation state in a small key-value store, keyed
`conv:{ticket_id}`. When a customer opens a new chat, the app looks up state for the ticket the helpdesk
just assigned and, if present, injects it into the prompt so the assistant "remembers" the case.

**The incident.** Ticket numbers are recycled by the helpdesk platform 18 months after closure. A
customer, Tom, opens a new chat and is assigned ticket `#48213` — a number last used 19 months earlier
for a different customer, Priya, whose case had long since been closed and purged from the primary
ticket database. Nobody had wired the conversation-state store's deletion to that purge; its own TTL had
been extended during a migration and never re-checked. The app finds a record at `conv:48213`, assumes
it belongs to the current conversation, and injects it.

**What Tom sees, as the assistant's opening message:**

```
Hi Priya, following up on your replacement laptop for order GB-2201 —
has it arrived yet? Let me know if the tracking number I sent still
looks right.
```

Tom is not Priya. He has never heard of order `GB-2201`. He has now been shown another customer's name,
order number and delivery status.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | State keyed by `ticket_id`, a value the ticketing platform can reissue | A reused key silently pointed at a different person's record |
| 2 | No ownership check before injecting fetched state into the prompt | "A record exists at this key" was treated as sufficient, when it should have meant nothing without a matching identity |
| 3 | Retention lived in two disconnected systems — the ticket database's purge, and the conversation store's own TTL | Deleting the ticket did not delete the state; the two clocks drifted apart |

**Note what did not go wrong.** The model was not hallucinating — it accurately reported the contents of
the record it was given. The bug is entirely in what was fetched and handed to it, which is exactly the
class of bug that §5.6's ownership check exists to catch.

### The fix

```python
record = state_store.get(key=f"conv:{ticket_id}")
if record and record.customer_id != authenticated_user.id:
    record = None                     # never trust a key match alone
```

- **Key by verified customer identity**, with `ticket_id` carried as a secondary field, not the primary
  key. An identity cannot be reissued to a stranger the way a ticket number can.
- **Check ownership on every read**, not just at write time. A key that resolves to *something* is not
  the same as a key that resolves to *this* customer.
- **One source of truth for retention.** Deleting or purging the parent case should cascade into the
  conversation-state store directly, rather than relying on a second, independently configured TTL to
  eventually agree.

**The general rule.** A state record is a database record like any other: it needs a primary key that
cannot be reissued to a different person, an ownership check before every read, and deletion that
cascades from one place. The full version of this problem — enforcing who is allowed to see what, across
tools and retrieval, not just chat state — is developed in M7-L15 and M9-L13.

---

## 7. Practical activity

**File:** [`labs/m5/l10_conversation_state.py`](../../labs/m5/l10_conversation_state.py)

**No API key, no network beyond the tokenizer's one-time download, no cost.**

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l10_conversation_state.py
```

**Sections 1, 2, 3 and 5 are real** — token counts from `tiktoken`, cost figures are arithmetic on
stated inputs. Section 4's twelve-question survival check is a deliberately simplified mock; a real
summarizer's omissions are less predictable, not more.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, tiktoken 0.14.0, NumPy 2.2.6.

```text
============================================================================
1. THE COST OF A CONVERSATION IS QUADRATIC
============================================================================
  Tokenizer: tiktoken cl100k_base

  system + tools 320 tok, user turn 60 tok,
  assistant turn 140 tok, $0.50/M in $2.00/M out  [ILLUSTRATIVE]

    turn  input tokens   output  cost this turn   cumulative  cost vs t1
       1           380      140        $0.00047      $0.0005        1.0x
       2           580      140        $0.00057      $0.0010        1.2x
       5         1,180      140        $0.00087      $0.0033        1.9x
      10         2,180      140        $0.00137      $0.0092        2.9x
      20         4,180      140        $0.00237      $0.0284        5.0x
      40         8,180      140        $0.00437      $0.0968        9.3x
      80        16,180      140        $0.00837      $0.3536       17.8x

  Turn 80's INPUT is 42.6x the input of turn 1 -- for a message
  the user would say is no more valuable than their first one.

  The mechanism is simple and worth stating precisely: each turn adds
  a fixed amount to the history, and every LATER turn pays for it
  again. n turns cost O(n^2) tokens in total.

  An 80-turn conversation: 662,400 input tokens sent in total.
  If the model had memory and you sent only the new turn: 30,400.
  Ratio: 21.8x. That factor is what statelessness costs.

============================================================================
2. WHERE THE TOKENS ACTUALLY GO
============================================================================
  A real eight-turn support conversation, tokenized.

    #  role        tokens   text                                            
    1  user            14   My order GB-4471 arrived damaged, the screen …  
    2  assistant       36   I'm sorry to hear that. I can see order GB-44…  
    3  user             4   A refund please.                                
    4  assistant       32   Of course. I've noted a refund request for GB…  
    5  user             5   Yes that's right.                               
    6  assistant       38   Thank you. The refund of 42.50 GBP to the car…  
    7  user             7   No that's all, thanks.                          
    8  assistant       22   You're very welcome. I've emailed a confirmat…  
       TOTAL          158

  The facts a later turn actually needs: GB-4471, damaged, refund, 4412, 42.50
  As a state record: 'order GB-4471 damaged; refund agreed; card 4412; amount 42.50 GBP'
  21 tokens vs 158 -- 7.5x smaller.

  That ratio is the whole opportunity, and also the whole risk: the
  compressed version is a LOSSY summary you wrote, and everything it
  omits is gone for good.

============================================================================
3. FOUR STRATEGIES, PRICED
============================================================================
  A 4,000-token context budget for history, 200 tokens per exchange.

  strategy                    turns kept at turn 40   input tok, turn 40
  send everything                                39                8,180  OVER BUDGET
  last N (N=6)                                    6                1,580
  summary + last 4                                4                1,270
  structured state + last 2                       2                  815

  strategy                     cost/turn at 40   vs everything
  send everything                     $0.00437           100%
  last N (N=6)                        $0.00107            24%
  summary + last 4                    $0.00091            21%
  structured state + last 2           $0.00069            16%

  Cost is not the interesting column. Section 4 is.

============================================================================
4. WHAT EACH STRATEGY LOSES  [MOCK]
============================================================================
  Twelve questions a user might ask at turn 40, each needing a fact
  from a particular earlier turn. Can the strategy still answer?

  question                                     all  lastN   summ  state
  what is my order number?                     yes     --    yes    yes
  what was wrong with it?                      yes     --    yes    yes
  did I ask for a refund or a replacement?     yes     --    yes    yes
  which card?                                  yes     --    yes    yes
  how much?                                    yes     --    yes    yes
  what did you say the delivery date was?      yes     --     --     --
  did I mention I'd already contacted you o…   yes     --     --     --
  what was the exact wording I used?           yes     --     --     --
  what did I say about the packaging?          yes     --     --     --
  what was the second option you offered?      yes     --     --     --
  did I agree to the email confirmation?       yes     --    yes    yes
  what did we just decide?                     yes    yes    yes    yes

                                                12      1      7      7  of 12

  Read the rows that fail for 'summ' and 'state' but not for 'all'.
  Every one of them is a detail nobody thought to put in the summary:
  the exact wording, the second option offered, an offhand remark 28
  turns ago. They are unanswerable now, and the model will not say so
  -- it will answer from what it has, confidently.

  THAT is the real cost of compression, and it is not a cost you
  can see in a token count. You chose what to forget when you wrote
  the summary prompt, weeks before the user asked.

  Note that 'structured state' scores the same as 'summary' here but
  fails DIFFERENTLY: its omissions are predictable, because the schema
  says exactly which fields exist. A prose summary's omissions are
  whatever the summarizer felt like leaving out this time.

============================================================================
5. WHAT YOU STORE IS NOT WHAT YOU SEND
============================================================================
  Two different questions, constantly conflated:

    STORE  -- what your database keeps, for audit, support, analytics
    SEND   -- what goes in the next request's context

  concern                 store                       send                    
  full transcript         yes, with retention policy  no                      
  structured state        yes, it is the record       yes                     
  summaries                yes, and version them       yes                     
  tool call arguments     names + outcomes only       yes, current turn       
  PII in messages          only if lawful basis        minimise                
  deleted-account data     must be erasable            n/a                     

  Three consequences people discover late:

  1. A deletion request must reach the SUMMARY too. A summary derived
     from a deleted message still contains it (M10-L06).
  2. A summary is a derived artefact and must be versioned with the
     prompt that produced it. Otherwise you cannot reproduce a
     conversation, and you cannot explain one (M5-L12).
  3. Context is not memory. Two users in the same session, a shared
     inbox, a support agent taking over -- all of these put one
     person's data in another's context if state is keyed loosely.

  And the failure mode nobody tests for:

  In a 40-turn conversation resent in full every turn, the
  FIRST message is transmitted 40 times and the last once --
  20.5 times on average across the conversation.

  If turn 3 contained a card number the user typed by mistake, it has
  gone to the provider 38 times. Redacting it from your
  database does not unsend those, and a retention clock that starts
  when you store it started 37 transmissions too late.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: sections 1, 2, 3 and 5. Token counts come from
  tiktoken cl100k_base; the cost tables are arithmetic on stated inputs.

  MOCK: section 4's survival rules are a simplification -- 'the last
  N turns, plus whatever a summary happens to contain'. Real
  summarizers keep and drop things less predictably than that, which
  makes the real picture WORSE, not better.

  NOT SHOWN: whether a model actually uses a fact that IS present in
  its context. Presence is necessary, not sufficient -- retrieval
  from a long context is its own failure mode (M4-L06, M7-L11).

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Turn 80 vs turn 1 input tokens (full resend) | **42.6×** |
| Total tokens across an 80-turn conversation, full resend vs with memory | 662,400 vs 30,400 — **21.8×** |
| 8-turn real transcript vs its structured-state record | 158 tok vs 21 tok — **7.5× smaller** |
| "Send everything" at turn 40 against a 4,000-tok budget | 8,180 tok — **over budget** |
| Cost per turn at turn 40, structured state vs send-everything | $0.00069 vs $0.00437 — **16%** |
| Questions answered correctly at turn 40, of 12 | all 12 · last-N 1 · summary 7 · structured state 7 |
| Average transmission count of the first message, 40-turn full resend | **20.5×** |

**Four things worth taking away.**

**1. Quadratic growth is not a rounding effect.** 21.8× total tokens, 42.6× on the last turn alone, for
an 80-turn conversation that is entirely ordinary in length.

**2. The compression ratio (7.5×) is the opportunity and the risk in the same number.** It is real
savings, purchased with a lossy summary whose contents you chose in advance.

**3. Cheapest is not the same as most correct.** Last-N was the cheapest non-full option and answered
only 1 of 12 follow-up questions. Summary and structured state cost more but preserved seven — and fail
in different, differently-debuggable ways.

**4. Full resend means early messages travel repeatedly.** 20.5× on average across a 40-turn
conversation, 38 times for something typed in turn 3 — with real consequences for anything sensitive
typed early and never meant to be repeated.

---

## 8. Common mistakes and troubleshooting

1. **Believing the model remembers you between requests.** It is your application resending history —
   nothing persists in the model (M4-L16).
2. **Resending full history with no budget.** Cost grows quadratically and the conversation eventually
   exceeds the context window outright.
3. **Truncating with last-N and being surprised early facts vanish.** §7.3's "1 of 12" is that surprise,
   measured.
4. **Summarizing a summary, repeatedly, without ever revisiting the source transcript.** Errors compound
   silently — state drift.
5. **Putting raw PII in a prose summary with no redaction.** The summary is now a second copy of
   sensitive data, often retained under a *different* policy than the source message.
6. **Deleting the source message but not the derived summary.** The deleted content survives inside the
   summary until that is regenerated or edited too.
7. **Keying state by something reissuable — a ticket number, a session cookie — instead of a stable
   identity.** §6 is what that produces.
8. **Not versioning the summarization prompt.** You cannot reproduce or explain an old conversation's
   summary later (M5-L12).
9. **Treating "store" and "send" as one policy.** They answer different questions and can have different
   correct answers for the same data.
10. **Assuming presence in context guarantees use.** A fact your state strategy kept can still be missed
    at inference time (M4-L06, M7-L11).
11. **No ownership check before injecting fetched state into a prompt.** A key that resolves to
    *something* is not the same as a key that resolves to *this* user.
12. **Forgetting that a deletion request must reach every derived copy**, not just the row it named.

| Symptom | Likely cause | Fix |
|---|---|---|
| Cost per conversation rising with no change in traffic | Full-history resend, no budget | Cap history; add a strategy from §5.3 |
| Assistant "forgets" something from ten turns ago | Sliding window too narrow | Move to summary or structured state |
| Assistant states a fact confidently that is simply wrong | A gap in the summary/schema, filled by the model | Widen the schema; do not trust confident absence of hedging |
| Deleted message content reappears | Summary not regenerated or edited after deletion | Cascade deletion into every derived artefact |
| Two users see each other's details | State keyed by a reissuable identifier, no ownership check | Key by verified identity; check ownership on every read |
| Can't explain why an old conversation's summary says what it says | Summarization prompt unversioned | Version prompts alongside the summaries they produce |
| Support team's transcript view is missing turns | Store policy conflated with send policy | Separate the two; store the full transcript regardless of what you send |

---

## 9. Security, privacy, reliability, cost

- **Security/Privacy.** Never inject fetched state into a prompt on key match alone — verify it belongs
  to the authenticated party of the current request (§6).
- **Privacy.** A deletion request must reach every derived artefact — summaries and structured state
  included, not just the source message (M10-L06).
- **Privacy.** Prefer structured, access-controlled fields for sensitive facts over folding them into a
  free-text summary, which is harder to redact selectively.
- **Reliability.** Periodically regenerate summaries from the source transcript rather than only from the
  previous summary, to bound drift.
- **Reliability.** Presence in context is necessary, not sufficient — do not assume a fact your strategy
  kept is a fact the model will use (M4-L06, M7-L11).
- **Cost.** Full-history resend is quadratic in conversation length; a budget-triggered strategy from
  §5.3 caps it before it becomes a surprise on the invoice.
- **Cost.** A stable, unchanging prefix (system prompt, tool definitions) is a caching opportunity
  independent of how you manage the rest of history (M5-L16).
- **Reproducibility.** Version the summarization prompt with its output, or you cannot explain an old
  conversation's summary when asked (M5-L12).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why does a conversation appear to have memory, if the model itself is stateless?
2. Why is the cost of resending full history quadratic rather than linear in the number of turns?
3. Name the two questions "store" and "send" answer, and give one case where the answers differ.
4. Which of the four strategies in §5.3 answered the most follow-up questions correctly? Which was
   cheapest? Are they the same strategy?
5. Why must a deletion request reach a summary, not just the message it was derived from?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the exact multiplier between turn-1 and turn-80 input tokens, and explain the
   mechanism in one sentence.
2. Take the eight-turn transcript in the lab and write your own structured-state record for it. Compare
   its token count with the lab's 21-token version and explain any difference.
3. Design a context-budget policy: at what token threshold do you switch from full history to a sliding
   window, and from a window to a summary? Justify the thresholds.
4. Write a rolling-summary prompt and show it operating over three successive updates. Identify one
   piece of information it drops.
5. Implement an ownership check for a structured-state lookup, and write a test that proves it refuses a
   record belonging to a different user.

### Exercise 3 — Challenge (~50 min)

1. Reproduce §6's incident as a runnable scenario (two synthetic customers, a recycled key) and show the
   fix preventing the leak.
2. Build a hybrid strategy — structured state plus the last 2 turns plus a rolling summary of everything
   older — and score it against the lab's twelve questions.
3. Design a deletion-cascade: given a deleted message, trace every derived artefact (summary,
   structured-state fields, cached prefix) that must also change, and write the invalidation logic.
4. Measure, for a traffic profile you state, the monthly cost difference between "send everything capped
   at the context window" and "structured state + last 2," and state the point at which the savings
   justify the added complexity.
5. Write the versioning scheme for summarization prompts and stored summaries that would let you explain,
   eighteen months from now, exactly why a given conversation's summary says what it says.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l10).)*

**Q1.** A conversation appears to "remember" earlier turns because:

- A. The model caches previous requests server-side.
- B. Your application resends the prior turns as part of each new request.
- C. The provider stores conversation state keyed by your API key.
- D. Fine-tuning updates the model's weights after each turn.

**Q2.** In an 80-turn, full-history conversation, turn 80's input token count was roughly how many times
turn 1's?

- A. About 2×.
- B. About 10×.
- C. About 43×.
- D. About 80×.

**Q3.** The mechanism behind quadratic, rather than linear, growth across n turns is:

- A. Every turn resends all prior turns, so each turn's fixed addition is paid for again by every later
  turn.
- B. Each turn's own message grows longer than the previous one.
- C. The tokenizer becomes less efficient as input grows.
- D. The system prompt is duplicated once per turn in the token count.

**Q4.** An 8-turn transcript was 158 tokens; a structured-state record of its key facts was 21 tokens —
about 7.5× smaller. This ratio represents:

- A. Free compression with no downside.
- B. Proof that summaries are always safe to send instead of the transcript.
- C. The fixed token overhead of any state schema.
- D. Both the opportunity (cost) and the risk — a lossy summary whose contents were chosen in advance.

**Q5.** "Summary + last 4" and "structured state + last 2" answered the same number of the lab's twelve
follow-up questions. What actually differs between them?

- A. Nothing; they are interchangeable, so pick whichever is cheaper.
- B. Structured state's omissions are predictable — bounded by its schema; a prose summary's omissions
  are whatever the summarizer happened to leave out this time.
- C. Structured state is strictly worse because it retains fewer raw turns.
- D. A prose summary never omits information a schema would have kept.

**Q6.** "Send everything" answered all twelve questions correctly at turn 40 but was flagged over the
4,000-token budget. This shows:

- A. A strategy can be informationally perfect and still be the wrong choice once cost and context
  limits are counted.
- B. Completeness and affordability are the same thing in practice.
- C. Sending everything is always the correct default regardless of budget.
- D. The budget in the lab was set too low to be realistic.

**Q7.** "Store" and "send" are:

- A. The same policy, applied twice for emphasis.
- B. Only relevant once a conversation exceeds the context window.
- C. Two different questions — what your database retains for audit and support, and what goes into the
  next request's context — which can have different correct answers for the same data.
- D. Interchangeable terms both meaning "conversation history."

**Q8.** A user asks you to delete a message containing an old address. You remove the raw message row.
Is that sufficient?

- A. Yes — deleting the source row satisfies any downstream copy automatically.
- B. Yes, provided the message is also purged from server logs.
- C. No — deletion cannot be honoured once any conversation has begun.
- D. No — a rolling summary derived from that message still contains the address until it is also
  regenerated or edited.

**Q9.** A summarization prompt should be versioned alongside the summaries it produces because:

- A. Without it you cannot reproduce or explain how a stored conversation's summary was derived, which
  matters for support and audit.
- B. Providers require a version tag on every prompt.
- C. It prevents the summarizer from ever hallucinating.
- D. Versioning reduces the token cost of the summary itself.

**Q10.** In a 40-turn, full-resend conversation, a card number typed by mistake in turn 3 was
transmitted to the provider approximately how many times before the conversation ended?

- A. Once.
- B. About 20 — the conversation's average.
- C. 38 — every turn from turn 3 through turn 40.
- D. Zero — turn 3 falls outside the model's context window by turn 40.

**Q11.** *(§6)* The root cause of the assistant addressing the wrong customer by another customer's name
and order details was:

- A. The model hallucinating a name and order number.
- B. A prompt-injection attack carried out by the second customer.
- C. A bug in the summarization prompt used to compress the conversation.
- D. Structured state keyed by a reissuable ticket ID, fetched and injected with no ownership check.

**Q12.** The general fix for the leak in §6 is:

- A. Switch from structured state to prose summaries.
- B. Key state by a stable, verified identity, check ownership on every read, and cascade deletion from
  one source of truth.
- C. Disable conversation state entirely and start every chat from nothing.
- D. Encrypt the state store at rest.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes storing every
conversation's full transcript and resending it in full on every turn, forever, "so we never lose
anything." State what you would tell them and what you would propose instead.

---

## 12. Revision notes

- **The model has no memory. Your application resends history, and that resend is what creates the
  illusion of continuity.**
- **Full-history cost is quadratic**: 21.8× total tokens and 42.6× on the last turn alone across an
  80-turn conversation.
- **Compression buys cost savings and spends information** — a 7.5× smaller state record is a *chosen*
  lossy summary, not free compression.
- **Cheapest is not the same as most correct.** Last-N was cheapest and answered 1 of 12 follow-ups;
  summary and structured state cost more and answered 7.
- **Structured state fails predictably** (bounded by its schema); **a prose summary fails however the
  summarizer felt that run.**
- **Store and send are different questions.** Keep the full transcript for audit; send only what the
  next request needs.
- **A deletion request must reach every derived artefact** — summaries and structured state included —
  not just the row it named.
- **Version the summarization prompt with its output**, or you cannot explain an old conversation's
  summary later.
- **Never inject fetched state on key match alone.** Check that it belongs to the authenticated party of
  the current request.
- **Key state by a stable identity, not a reissuable identifier**, and cascade deletion from one source
  of truth.
- **Early messages in a full-resend conversation are transmitted repeatedly** — 20.5× on average over 40
  turns — with real consequences for anything sensitive typed early.

---

## 13. Completion checklist

- [ ] I can explain why the model appears to remember a conversation.
- [ ] I can state why full-history cost is quadratic, not linear, in turns.
- [ ] I can compare at least three state strategies on both cost and information loss.
- [ ] My design separates "what I store" from "what I send."
- [ ] My deletion path reaches summaries and structured state, not just the source message.
- [ ] My structured-state lookups check ownership before injecting into a prompt.
- [ ] My state records are keyed by a stable identity, not a reissuable one.
- [ ] I version summarization prompts alongside the summaries they produce.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Liu, N. F., et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts*.
  <https://arxiv.org/abs/2307.03172> `[UNVERIFIED]`
- GDPR, Article 17 — Right to erasure ("right to be forgotten").
  <https://gdpr-info.eu/art-17-gdpr/> `[UNVERIFIED]`
- Anthropic — Prompt caching documentation.
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching> `[UNVERIFIED]`
- OpenAI — Managing conversation state.
  <https://platform.openai.com/docs/guides/conversation-state> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L11 — Context Engineering: Summarization, Truncation, Budgets](M5-L11-context-engineering.md)

You now know why history has a cost and what the four broad strategies trade off. Next: the mechanics
of running those strategies in production — when to trigger a summary, how to set a hard budget, and
what breaks when you get the threshold wrong.
