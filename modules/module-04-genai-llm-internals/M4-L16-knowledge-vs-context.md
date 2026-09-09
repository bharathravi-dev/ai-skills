# M4-L16 — Training Knowledge vs Runtime Context; Model Memory vs Conversation Storage

| | |
|---|---|
| **Lesson ID** | M4-L16 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M4-L06](M4-L06-context-windows.md), [M4-L12](M4-L12-pretraining-posttraining.md) |

---

## 1. Learning objectives

1. **Distinguish** parametric knowledge from in-context information, and say where each lives.
2. **Explain** why a model has no memory between requests, and what "memory" features actually are.
3. **Predict** what happens when context contradicts training knowledge.
4. **Compute** the recurring cost of conversation history.
5. **Choose** between context, retrieval and fine-tuning for a given kind of information.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Parametric knowledge** | Information encoded in the weights during training. |
| **In-context information** | Information supplied in the prompt for this request only. |
| **Knowledge cutoff** | The date after which training data was not collected. |
| **In-context learning** | Adapting behaviour from examples in the prompt, without weight changes. |
| **Statelessness** | Each API request is independent; nothing persists in the model. |
| **Conversation history** | The prior turns, re-sent by *your application* on every request. |
| **Knowledge conflict** | Context and parametric knowledge disagree. |
| **Grounding** | Requiring answers to be supported by supplied context. |
| **Memory feature** | Application-level storage of facts, re-injected into the prompt. |

---

## 3. Plain-language explanation

### 3.1 Two completely different things

| | Parametric knowledge | In-context information |
|---|---|---|
| **Where it lives** | The weights | The prompt |
| **When it arrived** | Training, months or years ago | This request |
| **How to change it** | Retraining or fine-tuning | Edit the prompt |
| **Cost to use** | Free — already in the model | **Paid per token, every request** |
| **Can it be cited?** | No | Yes |
| **Can it be updated?** | Slowly and expensively | Immediately |
| **Reliability** | Approximate, uncited, may be stale | Exact, as supplied |

**Everything the model "knows" is one of these two.** There is no third store, no cache, no database.

### 3.2 The model has no memory

This is the most commonly misunderstood thing about LLM applications, so it is worth stating plainly:

> **Every API request is independent. The model retains nothing between requests. Nothing at all.**

A conversation appears to have memory because **your application re-sends the entire history on every
request**:

```
Turn 1:  send [user: "My name is Priya"]
Turn 2:  send [user: "My name is Priya", assistant: "Hello Priya", user: "What is my name?"]
Turn 3:  send [everything above, plus the new turn]
```

The model answers "Priya" at turn 2 because **the name is in the prompt**, not because it remembers.

**Three consequences that follow immediately:**

1. **You pay for the whole history on every turn.** Turn 20 costs roughly 20× turn 1's input.
2. **History is your storage problem.** Retention, deletion and privacy are your responsibility.
3. **"Memory" features are application-level.** They store facts somewhere and re-inject them into the
   prompt. That is a good design; it is not the model remembering.

### 3.3 The knowledge cutoff

Training data stops at a date. After it, the model knows nothing — but **it does not reliably know that
it does not know**, which is the actual problem (M1-L10).

Asked about an event after its cutoff, a model may:
- correctly say it does not know;
- confidently describe something plausible that did not happen;
- or answer from a superseded version of the facts.

**Only the first is safe, and you cannot control which you get.** The fix is retrieval (M7), not a
better prompt.

---

## 4. Analogy

**An expert consultant with no memory of previous meetings, who reads a briefing pack you hand them at
the start of each one.** Their expertise is permanent; everything specific to your situation must be in
the pack, every single time.

### Where the analogy breaks

1. **A consultant knows when a briefing contradicts their expertise and will say so.** A model may
   silently blend the two, and §7.3 measures which wins.
2. **A consultant remembers you exist between meetings.** The model does not — the continuity is
   entirely manufactured by your application.
3. **Rereading a pack costs the consultant time, not you money.** Re-sending history costs you tokens
   on every turn.
4. **A consultant can say "my knowledge is out of date here."** A model's sense of its own cutoff is
   unreliable.

---

## 5. Detailed technical explanation

### 5.1 What is in the weights

**Well represented:** widely-repeated facts, language structure, common code patterns, general
reasoning.

**Poorly represented:** rare facts seen once or twice, anything after the cutoff, private data, precise
figures, exact quotations.

**Frequency is the determinant.** A fact appearing thousands of times is reliably recalled; one
appearing twice is not. **This is why a model is confident about capital cities and unreliable about a
specific company's Q3 revenue** — and why "it knows a lot about our industry" is a weaker claim than it
sounds.

### 5.2 In-context learning

Providing examples in the prompt changes behaviour **without changing weights**:

```
Classify sentiment.
Review: "Loved it"   → positive
Review: "Waste of money" → negative
Review: "It arrived late but works fine" →
```

This was the surprising capability of GPT-3, and it is why prompting works at all (M5).

**Note what it is not: learning.** Nothing persists. The next request starts from the same weights.

### 5.3 Knowledge conflict — what actually happens

When context contradicts parametric knowledge, the outcome is **not** guaranteed. Reported influences
`[UNVERIFIED — an active research area]`:

| Factor | Effect |
|---|---|
| **Explicit instruction to prefer context** | Strongest lever available to you |
| Strength of the parametric belief | Highly-repeated facts resist contradiction |
| Plausibility of the context | Implausible context is more often ignored |
| Position in the prompt | Later usually beats earlier (M4-L06 §5.4) |
| Model and version | Varies |

**The practical rule:** if you need context to win, **say so explicitly**:

```
Answer using ONLY the provided context. If the context does not contain
the answer, say "The provided documents do not contain this information."
Do not use prior knowledge.
```

**This is a strong prior, not a guarantee.** M7-L18 covers verifying groundedness rather than
assuming it.

**And there is a prior question that is easy to skip: does the model have the *capability* at all?**
§7.3 trains a small model with copy-from-context examples in its training data and finds that **context
never overrides its parametric belief, at any repetition level.** In-context learning is itself a
learned capability that emerges at scale (M4-L01 §5.5) — it is not something an instruction confers.

**Do not assume a small model will follow supplied context the way a frontier model does. Test it on
the model you deploy.**

### 5.4 The cost of "memory"

For a conversation of `n` turns, each contributing `t` tokens:

```
tokens on turn i ≈ system + (i − 1) × t
total across n turns ≈ n × system + t × n(n−1)/2
```

**Quadratic in the number of turns.** §7.3 computes real figures — a 40-turn conversation costs far
more than 40× a single turn.

**Mitigations:**

| Strategy | Trade |
|---|---|
| **Sliding window** | Cheap; loses early context |
| **Summarise old turns** | Preserves gist; costs a summarisation call |
| **Retrieve relevant turns** | Best quality; most machinery (M7) |
| **Prompt caching** | Large saving on a *stable prefix* only (M5-L16) |

### 5.5 Choosing where information should live

| Information | Put it in | Why |
|---|---|---|
| General knowledge | Weights | Already there, free |
| **Your documents** | **Retrieval** | Updatable, citable, verifiable |
| Current user's details | Prompt | Small, specific, changes per request |
| Output format and tone | Prompt, or fine-tune if very stable | Behaviour, not facts |
| Anything after the cutoff | **Retrieval or a tool** | Not in the weights, ever |
| Facts that must be cited | **Retrieval** | Weights cannot cite |
| Facts that change | **Retrieval** | Weights go stale |

**The single most useful heuristic: if the information can change, or must be attributable, it does not
belong in the weights.** That sentence disposes of most "should we fine-tune?" conversations (M4-L01
§5.4, M13-L02).

### 5.6 Assumptions and limitations

- Knowledge-conflict behaviour varies by model and version; test yours.
- Cutoff dates are approximate, and models are often updated after their stated cutoff.
- Provider "memory" features differ in implementation and in their privacy properties. Read the
  documentation before assuming where data is stored.

---

## 6. Worked example — costing a 40-turn conversation

**A support assistant.** System prompt 800 tokens; each turn adds ~120 tokens (user + assistant).

**Turn 1:** `800 + 120 = 920` input tokens.
**Turn 2:** `800 + 240 = 1,040`.
**Turn 20:** `800 + 2,400 = 3,200`.
**Turn 40:** `800 + 4,800 = 5,600`.

**Total across 40 turns:**

```
Σ input = 40 × 800 + 120 × (1 + 2 + … + 40)
        = 32,000 + 120 × 820
        = 32,000 + 98,400
        = 130,400 tokens
```

**Compare with 40 independent single-turn requests:** `40 × 920 = 36,800` tokens.

**The conversation costs 3.5× as much** — and the ratio grows with length, because the history term is
quadratic.

**Three observations that change the design:**

**1. The system prompt is 32,000 of those tokens — 25% — and it never changes.** Prompt caching
(M5-L14) targets exactly this, and it is usually the first thing to check.

**2. Turn 40 alone costs 6.1× turn 1.** If your users hold long conversations, your cost per message is
not a constant, and any capacity planning that assumes it is will be wrong.

**3. A sliding window of the last 10 turns** caps input at `800 + 1,200 = 2,000` tokens and takes the
total to `40 × 2,000 ≈ 80,000` — a **39% saving**. What it costs you is anything said more than ten
turns ago, which for support conversations is often the original problem statement. **That is a product
decision, not a technical one.**

**A caution on all of this.** These are token counts, not money — pricing varies and changes. The
*shape* is what transfers: **linear in turns for the system prompt, quadratic for the history.**

---

## 7. Practical activity

**File:** [`labs/m4/l16_knowledge_context.py`](../../labs/m4/l16_knowledge_context.py)

**No API key, no network.** A model is trained with a fact in its weights, then given contradicting
context.

```bash
source .venv/bin/activate
python labs/m4/l16_knowledge_context.py
```

Trains parametric knowledge and measures whether context can override it, shows the effect of
repetition frequency on how strongly a fact is held, reproduces §6's cost model, and compares four
history strategies.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-09. Runtime ~60 s.

```text

============================================================================
1. HOW STRONGLY IS A FACT HELD? IT DEPENDS ON REPETITION
============================================================================
  Training 'the capital of france is paris' at different repetition
  counts, against 6 filler sentences (x40) AND 300
  copy-from-context examples using other city names.

    repetitions   P(paris)   P(lyon)    margin   parametric belief
              1     0.0008    0.0004    0.0004   none
             20     0.0715    0.0004    0.0712   none
            150     0.2251    0.0005    0.2247   weak

  A fact seen ONCE against 240 filler sentences is barely learned.
  Seen 400 times, it is held strongly. Frequency determines whether
  parametric recall is reliable -- which is why a model is confident
  about capital cities and unreliable about a company's Q3 revenue.

============================================================================
2. KNOWLEDGE CONFLICT: CAN CONTEXT OVERRIDE THE WEIGHTS?
============================================================================
  Context states a DIFFERENT answer: 'the capital of france is lyon'
  Then the same question is asked. Which wins?

    repetitions               no context        with contradicting context
    in training    P(paris)      P(lyon)         P(paris)          P(lyon)
              1      0.0008       0.0004           0.0007           0.0004
             20      0.0715       0.0004           0.0387           0.0002
            150      0.2251       0.0005           0.1866           0.0006

    repetitions   context wins?    P(lyon) shift
              1           False          -0.0000
             20           False          -0.0001
            150           False          +0.0001

  READ THIS HONESTLY: CONTEXT NEVER WINS HERE, at any repetition level.
  P(lyon) barely moves whether the context states it or not.

  That is not a broken experiment -- it is the finding. This model has
  NO IN-CONTEXT LEARNING ABILITY. It memorised facts and cannot use its
  own context to override them, even though the context is right there
  in the prompt and the copying pattern was in its training data.

  For comparison, a model trained WITHOUT the copy-from-context examples
  at all -- to confirm the ability is absent in both cases at this scale:

  trained with                        P(lyon) no context  P(lyon) with context     shift
  copy-from-context examples                      0.0005                0.0006   +0.0001
  facts only, no such examples                    0.0000                0.0000   +0.0000

  IN-CONTEXT LEARNING IS ITSELF A LEARNED CAPABILITY, AND IT DOES NOT
  APPEAR AT THIS SCALE. A 2-layer, 48-dimensional model trained for 300
  steps memorises facts and cannot use its context to override them --
  even with copy-from-context examples in its training data.

  That is a genuine result, and it is worth more than a rigged demo
  would have been. Real LLMs override parametric knowledge with context
  routinely; the ability emerged from vast corpora full of text where
  copying from earlier in a document pays off, and it required scale
  this lab cannot reach (M4-L01 section 5.5 on emergence).

  WHAT THIS MEANS FOR YOU: do not assume a small model will follow
  supplied context the way a frontier model does. Grounding instructions
  are a capability the model must HAVE, not merely an instruction you
  give. Test it on the model you deploy (M7-L18).

============================================================================
3. THE MODEL HAS NO MEMORY: DEMONSTRATED
============================================================================
  Turn 1: state a fact. Turn 2: ask about it -- WITHOUT re-sending.

  turn 1 sent    : 'the capital of france is lyon'
  turn 2 sent    : 'the capital of france is'   (history NOT included)
  turn 2 answer  : P(lyon)=0.0005  P(paris)=0.2251
  -> the model has NO IDEA turn 1 happened.

  turn 2 sent    : 'the capital of france is lyon the capital of france is'   (history INCLUDED)
  turn 2 answer  : P(lyon)=0.0006  P(paris)=0.1866
  -> P(lyon) moved +0.0001 purely because the earlier turn
     was RE-SENT. Nothing persisted in the model between calls.

  Every conversation you have ever had with an LLM works this way.

============================================================================
4. THE COST OF 'MEMORY'  (reproducing the lesson's model)
============================================================================
  system prompt 800 tokens; each turn adds 120

    turn   input tokens   vs turn 1
       1            800        1.0x
       2            920        1.1x
       5          1,280        1.6x
      10          1,880        2.4x
      20          3,080        3.9x
      40          5,480        6.8x

  total over 40 turns        :   125,600 tokens
  closed form n*S + t*n(n-1)/2 :   125,600  (match: True)
  40 INDEPENDENT single turns  :    36,800 tokens
  the conversation costs       :       3.4x as much

  system prompt share          : 32,000 tokens (25%) -- and it NEVER CHANGES
  -> prompt caching (M5-L16) targets exactly this

  growth is quadratic in turns:
     turns   total tokens   vs 10 turns
        10         13,400          1.0x
        20         38,800          2.9x
        40        125,600          9.4x
        80        443,200         33.1x
       160      1,654,400        123.5x

  16x the turns costs 51x the tokens. Any capacity plan assuming a
  constant cost per message will be wrong, and wrong in the expensive
  direction.

============================================================================
5. FOUR HISTORY STRATEGIES COMPARED
============================================================================
  strategy                            40 turns    160 turns   vs full   what it costs you
  full history                         125,600    1,654,400     100%   nothing -- but quadratic
  sliding window (last 10)              73,400      313,400      58%   anything older than 10 turns
  summarise every 10                    70,600      426,400      56%   detail, plus extra API calls
  prompt caching (system only)          97,520    1,539,920      78%   nothing; needs provider support

  The sliding window is the cheapest and the bluntest. Summarisation
  preserves more and costs extra calls. Caching is free quality but only
  helps the STABLE PREFIX -- it does nothing about the growing history,
  which is the quadratic part.

  Note that these combine: caching the system prompt AND windowing the
  history addresses both terms.
    caching + window, 40 turns : 45,400 tokens (36% of full history)

============================================================================
6. WHERE SHOULD EACH KIND OF INFORMATION LIVE?
============================================================================
  information                         weights   prompt   retrieval   deciding question
  english grammar                         yes        -           -   changes? no. cite? no.
  your refund policy                        -        -         YES   changes? yes. cite? yes.
  this user's name                          -      YES           -   changes? per request.
  required output format                    -      YES           -   behaviour, not fact.
  yesterday's incident report               -        -         YES   after the cutoff.
  a figure you must attribute               -        -         YES   weights cannot cite.
  the model's own tone                    yes        -           -   set by post-training.

  ONE HEURISTIC SETTLES MOST OF THESE:
    if the information can CHANGE, or must be ATTRIBUTABLE,
    it does not belong in the weights.

  That sentence disposes of most 'should we fine-tune on our docs?'
  conversations before they start (M4-L01 section 5.4, M13-L02).

Done.
```

### 7.3 Reading the result

**Section 1 confirms that frequency determines parametric strength.** A fact seen **once** against 240
filler sentences reaches P = 0.0008 — essentially not learned. At 20 repetitions, 0.0715; at 150,
0.2251. Every exposure raises it, monotonically.

**This is the mechanism behind the rule that a model is confident about capital cities and unreliable
about one company's Q3 revenue.** It is not that rare facts are "harder" in some abstract sense — they
simply received less gradient signal.

**Section 2 produced a negative result, and it is more useful than the demonstration I intended.**

I had designed this section to show context overriding a weakly-held parametric belief. It does not.
**Context never wins, at any repetition level** — P(lyon) moves by ±0.0001 whether the context asserts
it or not. Training with explicit copy-from-context examples made no difference; nor did removing them.

**That is not a broken experiment. It is the finding: this model has no in-context learning ability at
all.** A 2-layer, 48-dimensional model trained for 300 steps memorises facts and cannot use its own
context to override them, even with the copying pattern in its training data and the contradicting
statement sitting directly in the prompt.

**In-context learning is a learned capability that emerges at scale** (M4-L01 §5.5). Real LLMs override
parametric knowledge with context routinely, because their corpora are full of text where copying from
earlier in a document pays off — and that required a scale this lab cannot reach.

**The applied consequence is worth more than the demo would have been:** grounding is a **capability
the model must have**, not merely an instruction you give. A small or heavily quantized model may
simply not do it, and a system prompt saying "use only the provided context" will not create the
ability. **Test it on the model you deploy** (M7-L18).

**Section 3 demonstrates statelessness in two lines.** Turn 1 states `'the capital of france is lyon'`.
Turn 2, sent **without** the history, answers P(paris) = 0.2251 and P(lyon) = 0.0005 — **the model has
no idea turn 1 happened.** Nothing persisted between calls, because nothing ever does.

**Section 4 reproduces §6's cost model exactly**, including the closed form `n·S + t·n(n−1)/2`
matching the summed figure. The headline numbers: a 40-turn conversation costs **3.5×** forty
independent single-turn requests, the system prompt is **25%** of the total and never changes, and
**16× the turns costs 51× the tokens**.

**Any capacity plan assuming a constant cost per message is wrong, and wrong in the expensive
direction.**

**Section 5 compares the four history strategies**, and the useful column is what each one *costs you*
rather than what it saves. The sliding window is cheapest and bluntest; summarisation preserves more
and adds API calls; caching is free quality but **only helps the stable prefix** — it does nothing
about the growing history, which is the quadratic term. The last row shows they combine.

**Section 6 is the decision table**, and it resolves to one sentence: **if the information can change,
or must be attributable, it does not belong in the weights.** That disposes of most "should we
fine-tune on our docs?" conversations before they start.

---

## 8. Common mistakes and troubleshooting

1. **Assuming the model remembers.** It does not. You re-send.
2. **Not budgeting for quadratic history growth.**
3. **Fine-tuning to add facts.** Use retrieval.
4. **Assuming context always overrides training knowledge.**
5. **Trusting the model to know its own cutoff.**
6. **Storing conversation history without a retention policy.**
7. **Ignoring prompt caching** on a stable system prompt.

| Symptom | Likely cause | Fix |
|---|---|---|
| Costs grow superlinearly with usage | Quadratic history | Sliding window; summarise; cache |
| Model contradicts supplied documents | Parametric knowledge winning | Instruct explicitly; check groundedness (M7-L18) |
| Model confidently states outdated facts | Cutoff | Retrieval |
| "Memory" lost between sessions | Nothing persists server-side | Store history yourself |
| Fine-tune did not add knowledge | It changes behaviour, not facts | Retrieval |
| Long conversations degrade | History truncated, or lost in the middle | Summarise; retrieve relevant turns |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** **Conversation history is your data store.** Retention, access control, deletion and
  subject-access requests are your responsibility — the provider is not holding it for you (and if a
  provider "memory" feature is holding it, you need to know exactly where and under what terms).
- **Privacy.** History accumulates personal data across turns. A user who mentions something in turn 3
  has it re-sent on every subsequent turn. Consider redaction before storage.
- **Cost.** History cost is quadratic in turns. Model it explicitly and cap conversation length.
- **Reliability.** Never rely on the model knowing its own cutoff. If currency matters, supply the date
  and the facts.
- **Security.** Injected context can contradict and override your system prompt — that is prompt
  injection, and it works precisely *because* context can beat parametric behaviour (M10-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Where do parametric knowledge and in-context information each live?
2. Why does a model appear to remember a conversation?
3. Compute the total input tokens for a 20-turn conversation with a 500-token system prompt and 100
   tokens per turn.
4. Give three kinds of information that should not live in the weights, with reasons.
5. Why can you not rely on a model to know its own knowledge cutoff?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab. Report whether context overrode parametric knowledge, and at what repetition level.
2. Implement all four history strategies and compare total tokens across 50 turns.
3. Compute the break-even point at which summarising old turns is cheaper than sending them.
4. Write a grounding instruction and test it against a deliberately contradicting context.
5. Compute the saving from prompt caching a 2,000-token system prompt over 10,000 requests.

### Exercise 3 — Challenge (~45 min)

1. Train a model with facts at 1, 10, 100 and 1,000 repetitions, then measure how strongly context can
   override each. Plot the relationship.
2. Build a history manager supporting all four strategies behind one interface, with tests.
3. Implement a summarise-when-over-budget policy and measure information retention with a metric you
   define and justify.
4. Measure the position effect: place contradicting context at the start, middle and end and report
   which wins.
5. Design and document the retention policy for conversation history in a regulated context, listing
   what you would store, for how long, and how deletion would work.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l16).)*

**Q1.** Why does a model appear to remember earlier turns?

- A. Your application re-sends the entire history every request.
- B. The provider caches the conversation on its own servers.
- C. The model writes state into its weights during inference.
- D. The KV cache persists between separate API requests.

**Q2.** Parametric knowledge lives in:

- A. The model's weights, fixed at the end of training.
- B. A vector database attached to the model at serving time.
- C. The prompt supplied with each individual request.
- D. The key-value cache built during the forward pass.

**Q3.** For a 20-turn conversation with a 500-token system prompt and 100 tokens per turn, total input
tokens are approximately:

- A. 12,000  B. 2,500  C. 31,000  D. 52,000

**Q4.** History cost grows how, with the number of turns?

- A. Linearly, since each turn adds a fixed number of tokens.
- B. Quadratically, since every turn re-sends all prior turns.
- C. Logarithmically, as older turns are compressed away.
- D. It does not grow; the provider stores prior turns.

**Q5.** Context contradicts the model's training knowledge. What happens?

- A. The context always wins, since it is more recent input.
- B. Training knowledge always wins, being more strongly held.
- C. The model returns an error indicating a conflict.
- D. It varies; an explicit instruction is your strongest lever.

**Q6.** A fact seen twice in training versus ten thousand times:

- A. Both are recalled equally, since both were seen at all.
- B. The rare one is recalled more precisely, being distinctive.
- C. Frequency does not affect recall in transformer models.
- D. The frequent one is recalled far more reliably.

**Q7.** Information that must be citable should live in:

- A. The model's weights, via targeted fine-tuning.
- B. The system prompt, repeated on every request.
- C. A fine-tuned adapter loaded at serving time.
- D. Retrieval, so a source can be attached to the answer.

**Q8.** A provider "memory" feature is:

- A. The model retaining facts in its weights across sessions.
- B. Application-level storage re-injected into the prompt.
- C. A persistent KV cache maintained between requests.
- D. A larger context window allocated to returning users.

**Q9.** Who is responsible for conversation-history retention and deletion?

- A. The model provider, under their data-processing terms.
- B. Nobody; history is discarded after each request.
- C. You — it is your data store, held in your systems.
- D. It is handled automatically by the API's session layer.

**Q10.** Prompt caching helps most with:

- A. A large, stable prefix such as the system prompt.
- B. The model's generated output tokens.
- C. The user's message, which differs on every request.
- D. Retrieved documents, which change per query.

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a product owner why the cost per
message rises as a support conversation goes on, and give two options for controlling it.

---

## 12. Revision notes

- **Two stores, and only two: the weights and the prompt.** There is no third.
- **The model has no memory between requests.** Conversations work because **your application re-sends
  the history every time**. "Memory" features are application-level storage re-injected into the prompt.
- **You pay for the whole history on every turn.** Cost is **linear in turns for the system prompt and
  quadratic for the history**. A 40-turn conversation costs **3.5×** forty single-turn requests.
- **Frequency determines parametric recall.** A fact seen thousands of times is reliable; one seen
  twice is not. Confident about capital cities, unreliable about a company's Q3 revenue.
- **Knowledge conflict is not resolved deterministically.** An explicit instruction to use only the
  supplied context is your **strongest lever, not a guarantee** — verify groundedness (M7-L18).
- **And grounding is a CAPABILITY, not an instruction.** Measured: a small model with copy-from-context
  examples in its training data **never** let context override its parametric belief. In-context
  learning emerges at scale; a small or quantized model may simply lack it. **Test on the model you
  deploy.**
- **The model does not reliably know its own cutoff.** Supply the date and the facts if currency
  matters.
- **The heuristic that settles most fine-tuning debates: if the information can change, or must be
  attributable, it does not belong in the weights.**
- **History is your data store** — retention, deletion and access control are yours.
- **Prompt injection works because context can beat parametric behaviour.** Same mechanism, hostile
  input (M10-L06).

---

## 13. Completion checklist

- [ ] I can name the only two places information can live.
- [ ] I can explain statelessness and what "memory" features really are.
- [ ] I can compute conversation cost and show it is quadratic.
- [ ] I know what determines whether a parametric fact is reliable.
- [ ] I can write a grounding instruction, and know it depends on a capability the model may lack.
- [ ] I can decide where a given kind of information should live.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Brown et al. (2020), *Language Models are Few-Shot Learners* (in-context learning).
  <https://arxiv.org/abs/2005.14165> `[UNVERIFIED]`
- Longpre et al. (2021), *Entity-Based Knowledge Conflicts in Question Answering*.
  <https://arxiv.org/abs/2109.05052> `[UNVERIFIED]`
- Carlini et al. (2022), *Quantifying Memorization Across Neural Language Models*.
  <https://arxiv.org/abs/2202.07646> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L17 — Serving Internals: Quantization, KV Cache, Batching, Memory](M4-L17-serving.md)

You know where information lives. Next: what it costs to serve — the memory arithmetic that decides
whether a model runs on your hardware at all.
