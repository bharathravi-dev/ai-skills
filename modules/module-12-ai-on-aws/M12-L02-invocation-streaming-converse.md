# M12-L02 — Invocation, Streaming and the Converse API

| | |
|---|---|
| **Lesson ID** | M12-L02 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M12-L01](M12-L01-bedrock-concepts-model-access.md), [M5-L09](../module-05-prompting-llm-apps/M5-L09-streaming.md) |

---

## 1. Learning objectives

1. **Explain** what a unified request shape buys, counted in call sites that change on a model swap.
2. **Describe streaming honestly**: it changes perceived latency, not total latency, and it costs you things.
3. **Enumerate every timeout on the path** and identify the smallest, which is your real one.
4. **Trace a tool-use loop** in round trips and accumulated tokens.
5. **Read the stop reason and usage on every response**, and act on `max_tokens`.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Converse API** | Bedrock's unified invocation surface: the same request and response shape across providers. |
| **`messages`** | The conversation, as alternating `user` and `assistant` turns of content blocks. |
| **Content block** | A piece of a message: text, an image, a `toolUse` request, a `toolResult`. |
| **`inferenceConfig`** | Decoding settings: `maxTokens`, `temperature`, `topP`, `stopSequences`. |
| **`toolConfig`** | Tool declarations and the tool-choice policy. |
| **`stopReason`** | Why generation ended: `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, guardrail intervention. |
| **`usage`** | Input, output and total token counts on the response. |
| **`ConverseStream`** | The streaming variant, delivering events as the answer is produced. |
| **Time to first token (TTFT)** | How long before the first output appears. |

---

## 3. Plain-language explanation

### 3.1 One shape means a model swap is a configuration change

§7.1 counts eleven things application code does around a model call. With a per-provider API, **all eleven** change when
you switch models. With a unified API, **one** does — the model id. That is the whole argument for the Converse API, and
it is M5-L17's portability point made concrete.

Model-specific extras are passed through, and each one you use puts a place back on the list.

### 3.2 Streaming changes perception, not speed

§7.2: 400 tokens at 18 ms each, first token at 640 ms. Non-streaming, the user sees nothing for **7,840 ms**. Streaming,
they see the first word at **640 ms** — and the total is **identical**.

The second figure matters more: reading 300 words takes about **75 seconds**, **9.6×** the generation time. A streamed
answer arrives faster than anyone can read it, so the perceived wait is 640 ms.

Streaming is not a performance optimisation. It costs you every timeout on the path, and the ability to validate the whole
output before showing it.

### 3.3 The smallest timeout on the path is your real one

§7.3: six layers, and the effective timeout is the **application HTTP client at 10 seconds** — a library default nobody
chose. A 180-second research-style answer would be cut by **all six**.

An idle timeout is usually reset by each streamed chunk, which is why streaming survives some of them — **but only if
nothing on the path buffers**. A buffering proxy turns your stream back into one long silence.

### 3.4 A tool-use loop is several round trips, and the history grows

§7.4: one user question becomes **3 model round trips**, **1,040 input tokens and 455 output tokens**. The conversation
is resent each turn, so input tokens accumulate faster than the answer length suggests, and the latency is the sum of the
round trips plus tool execution.

### 3.5 The stop reason is not optional reading

§7.5: `max_tokens` means the output was **truncated** — which for structured output means valid-looking text that is a
broken JSON object, failing in a parser at the worst moment.

---

## 4. Analogy

**Dictating a letter versus receiving it in the post.** Dictation lets you hear the first sentence immediately; the letter
takes just as long to finish either way. You can start reading before it is done — and you cannot check the whole thing
for mistakes before the recipient hears the opening. And if the phone line drops after ninety seconds, it does not matter
how good the letter was going to be.

### Where the analogy breaks

- **A dictated letter can be corrected mid-sentence; a streamed token is already on the user's screen** — which is why
  validation and guardrails behave differently under streaming (§5.3, L06).
- **One phone line has one timeout; a web request crosses six**, each with a default someone else chose (§5.4).

---

## 5. Detailed technical explanation

### 5.1 The request shape

```python
response = client.converse(
    modelId=MODEL_ID,                       # pinned (M10-L13)
    system=[{"text": SYSTEM_PROMPT}],       # hashed and versioned (M5-L12)
    messages=[
        {"role": "user", "content": [{"text": question}]},
    ],
    inferenceConfig={"maxTokens": 800, "temperature": 0.2, "stopSequences": []},
    toolConfig={"tools": TOOLS, "toolChoice": {"auto": {}}},
)
```

The response carries `output.message` (role and content blocks), `stopReason`, `usage` and `metrics`. That structure is
the same whichever provider's model you named — which is what §7.1 measures.

Two disciplines from earlier modules apply directly: the system prompt is an artefact with a **content hash**
(M10-L13 §5.2), and `maxTokens` is a **cost cap** as well as a length limit (M8-L15, M11-L06).

### 5.2 Streaming

`[REAL, computed]` §7.2 — 640 ms versus 7,840 ms to first output; identical totals.

What you gain: perceived responsiveness, and the ability to show progress on long answers.

What you give up:

| Cost | Consequence |
|---|---|
| Whole-output validation | You cannot check a JSON object you have not finished receiving (M5-L07) |
| Simple guardrail application | Output filtering must work on partial text, or buffer (L06) |
| Simple error handling | A failure mid-stream leaves a partial answer on the screen |
| Simple retries | You cannot silently retry something the user has already read (M8-L13) |
| Path simplicity | Every hop must not buffer (§5.4) |

A workable compromise for structured output: **stream the prose, buffer the structure**. If the response must be valid
JSON, do not stream it to the user; stream a status instead.

### 5.3 Timeouts

`[REAL, compared — ILLUSTRATIVE values]` §7.3.

```text
effective timeout = min(client, CDN/proxy, gateway, load balancer, app HTTP client, SDK)
```

The practical checklist:

1. **Enumerate every layer** for one real request path and write down its current value.
2. **Set them deliberately**, from p99 including the full stream (M13-L11).
3. **Verify nothing buffers** — test with a slow endpoint and watch when bytes arrive.
4. **Set the SDK's read timeout explicitly**; the default is rarely right for a long generation.
5. **Decide what the user sees** when a stream is cut mid-answer (M10-L09).

### 5.4 Tool use

`[REAL, counted]` §7.4 — 3 round trips, 1,040 in / 455 out.

The loop:

```text
send messages + toolConfig
  -> stopReason "tool_use", content contains a toolUse block {toolUseId, name, input}
     execute the tool YOURSELF, under YOUR permissions (M9-L13, M12-L08)
  -> append an assistant message with the toolUse, then a user message with a
     toolResult block {toolUseId, content, status}
  -> repeat until stopReason is "end_turn"
```

Three things the API does not do for you, all from Module 8: **validate the tool arguments** against the schema before
executing (M8-L05); **bound the loop** with a step limit and a cost ceiling (M8-L15); and **decide what is allowed at
all** — the tool's permissions are the role's permissions, not the prompt's (M9-L13, L08).

The input-token accumulation in §7.4 is the standard agent cost surprise: the history is resent every turn (M5-L15).

### 5.5 Reading the response

`[REAL, computed]` §7.5.

| `stopReason` | What your code must do |
|---|---|
| `end_turn` | Normal completion; validate the output anyway (M5-L07) |
| **`max_tokens`** | **Treat as an error for structured output.** Retry with a larger budget, or a shorter task |
| `stop_sequence` | Expected if you configured one; otherwise investigate |
| `tool_use` | Run the tool and continue the loop (§5.4) |
| Guardrail intervention | Handle as a policy outcome, not a failure (L06, M5-L14) |

Record `usage` on **every** call: it is the cost signal (M11-L06 §5.1), the runaway detector (M8-L15) and part of the
audit record (M10-L13). Emit it as a metric, not only into a log line (M11-L16 §5.1).

### 5.6 Assumptions and limitations

- All timings, token counts, prices and timeout values are invented; the response field names follow the documented
  Converse structure.
- Default timeouts differ by client library and change; verify yours.
- Multimodal content blocks, prompt caching and the older per-model `InvokeModel` surface are out of scope.

---

## 6. Worked example — the JSON that was valid until it was not

**The situation.** A classification service asked a model for a JSON object with six fields, parsed it, and wrote the
result to a database. It worked for months.

**Then the input documents got longer.**

1. Longer inputs produced longer outputs. Some responses hit `maxTokens` and stopped **mid-object** (§7.5).
2. `stopReason` was never read. The code parsed the text, which raised a JSON error, which was caught by a broad
   `except` and logged at debug level (M2-L10).
3. The fallback wrote a default record. Roughly **0.4%** of documents were silently misclassified.
4. It surfaced when a downstream report showed an implausible category distribution — three weeks later.
5. Streaming had been enabled for the user-facing path at the same time, so partial objects were also being *displayed*
   before validation (§5.3).

| # | What went wrong | Fix |
|---|---|---|
| 1 | `stopReason` not read | Treat `max_tokens` as an error for structured output (§5.5) |
| 2 | Parse failure swallowed | Narrow the exception; alarm on parse-failure rate (M11-L16) |
| 3 | Silent default on failure | Abstain and route to review (M7-L13) |
| 4 | No output-validity metric | Emit schema-validation success as a metric and gate on it (M10-L12) |
| 5 | Structured output streamed | Stream prose, buffer structure (§5.3) |

**The general rule.** **`stopReason` is part of the answer. Code that ignores it will eventually parse half an object and
tell you it succeeded.**

---

## 7. Practical activity

**File:** [`labs/m12/l02_invocation_streaming_converse.py`](../../labs/m12/l02_invocation_streaming_converse.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m12/l02_invocation_streaming_converse.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. ONE REQUEST SHAPE, OR ONE PER PROVIDER?
============================================================================
  what the code does                   unified API   per-provider API
  build the request body                         0                  1
  set the system prompt                          0                  1
  set max tokens / temperature                   0                  1
  parse the response text                        0                  1
  read the stop reason                           0                  1
  read token usage                               0                  1
  declare tools                                  0                  1
  parse a tool call                              0                  1
  return a tool result                           0                  1
  handle the streaming events                    0                  1
  the model id itself                            1                  1
  TOTAL places to change                         1                 11

  switching models touches 1 place with a unified API and 11 without it.
  That is the entire argument for the Converse API: the request and response
  shape is the same across providers, so a model swap is a configuration
  change rather than a rewrite (M5-L17). The exception is the model-specific
  extras, which the API passes through -- and every one you use puts a place
  back on the list.

============================================================================
2. STREAMING: WHAT THE USER ACTUALLY WAITS FOR
============================================================================
  400 output tokens, 18 ms/token, first token at 640 ms

  mode                         user sees nothing for      total
  non-streaming                             7,840 ms   7,840 ms
  streaming                                   640 ms   7,840 ms

  the total is IDENTICAL: 7,840 ms. Streaming changes only when the first
  word appears -- 8% of the way through instead of 100%.
  it also matters that reading 300 words takes about 75 s, which is
  9.6x the generation time: a streamed answer arrives faster than the
  user can read it, so the perceived wait is the 640 ms, not the 7.8 s.
  Streaming is not a performance optimisation. It is a perception change, and
  it costs you every timeout on the path (section 3) and the ability to
  validate the whole output before showing it (M5-L07, M12-L06).

============================================================================
3. EVERY TIMEOUT ON THE PATH
============================================================================
  a streamed answer takes 7.8 s end to end

  layer                                   timeout   fits?   note
  browser / client SDK default               30 s     yes   often the first to fire
  CDN or proxy                               60 s     yes   may also buffer, defeating streaming
  API Gateway integration (default)          29 s     yes   raiseable on REST APIs by quota
  load balancer idle timeout                 60 s     yes   configurable into minutes
  application HTTP client                    10 s     yes   the default in many libraries
  Bedrock SDK read timeout                   60 s     yes   set it explicitly

  the effective timeout is the SMALLEST on the path: application HTTP client at 10 s.
  now take a long answer of 180 s (a research-style response):
    layers that would cut it: 6/6 -- browser / client SDK default, CDN or proxy, API Gateway integration, load balancer idle timeout, application HTTP client, Bedrock SDK read timeout
  An idle timeout is usually reset by each streamed chunk, which is why
  streaming SURVIVES some of these and a non-streamed call does not -- but
  only if nothing on the path BUFFERS. A proxy that buffers the response
  converts your stream back into one long silence (M11-L09, M11-L13).

============================================================================
4. THE TOOL-USE LOOP, COUNTED
============================================================================
  step                                    input tok  output tok   what it is
  user question                                 620           0   you send messages + toolConfig
  model asks for a tool                           0          40   stopReason = tool_use; a toolUse block
  you run the tool, send the result             180           0   a toolResult block in a user message
  model asks for a second tool                    0          35   stopReason = tool_use again
  you run it, send the result                   240           0   another toolResult
  model answers                                   0         380   stopReason = end_turn
  TOTAL                                        1040         455

  3 model round trips for one user question.
  Two consequences. The CONVERSATION GROWS: every turn resends the whole
  history, so input tokens accumulate faster than the answer suggests
  (M5-L15). And the latency is the SUM of the round trips plus the tool
  execution time, which is why an agent feels slow even when each step is
  fast (M8-L03, M13-L10). Cap the loop (M8-L15).

============================================================================
5. TOKEN ACCOUNTING FROM THE RESPONSE
============================================================================
  a response carries what you need to account for it:

{
  "output": {
    "message": {
      "role": "assistant",
      "content": [
        {
          "text": "The refund policy allows 30 days..."
        }
      ]
    }
  },
  "stopReason": "end_turn",
  "usage": {
    "inputTokens": 1040,
    "outputTokens": 455,
    "totalTokens": 1495
  },
  "metrics": {
    "latencyMs": 4180
  }
}

  cost of this ONE question: $0.00995 [ILLUSTRATIVE $3.0/M in, $15.0/M out]
  at 40,000 questions/day: $398/day, $11,934/month

  stopReason            what it means for your code
  end_turn              the model finished normally
  max_tokens            TRUNCATED -- your output is incomplete, and may be invalid JSON
  stop_sequence         a stop sequence you configured was produced
  tool_use              the model wants a tool result before continuing
  guardrail_intervened  a guardrail blocked or modified the response (M12-L06)

  Read the stop reason on EVERY response. 'max_tokens' is the one that
  silently breaks structured output: you get valid-looking text that is a
  truncated JSON object, and a parser that fails at the worst moment
  (M5-L06, M5-L07). Record usage on every call -- it is your cost signal
  and your runaway detector (M11-L06, M11-L16).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count, latency figure, timeout comparison, token total and cost
  above is computed from the values in this script.

  DOCUMENTED SHAPE: the response fields shown -- output.message, stopReason,
  usage.inputTokens/outputTokens, metrics.latencyMs -- follow the Converse API's
  documented structure, as do the stop reasons.

  ILLUSTRATIVE: all timings, token counts, prices and the timeout values are
  invented. Measure your own; the timeout defaults in particular vary by
  client library and change over time.

  NOT SHOWN: the actual SDK calls, multimodal content blocks, guardrail
  configuration (M12-L06), and prompt caching.

Done.
```

### 7.3 Reading the result

**Section 1's total row** — 1 place versus 11 — is the portability argument in one number.

**Section 2's two rows have the same total.** Streaming moved 7.2 seconds of waiting, not 7.2 seconds of work.

**Section 3's "smallest on the path"** is almost always a library default nobody chose.

**Section 5's `max_tokens` row** is the one that breaks structured output silently.

---

## 8. Common mistakes and troubleshooting

1. **Writing per-provider request builders.** §7.1 — eleven places to change.
2. **Treating streaming as a speed improvement.** §7.2 — the total is identical.
3. **Streaming structured output.** §5.3 — you cannot validate what you have not finished receiving.
4. **Only setting the timeout you thought of.** §7.3 — the smallest wins.
5. **A buffering proxy in front of a stream.** The user waits for the whole answer anyway.
6. **Ignoring `stopReason`.** §6 — silent truncation.
7. **Not recording `usage`.** No cost signal, no runaway detection (M11-L06).
8. **Letting the model execute tools.** It requests; you execute, under your permissions (M9-L13).
9. **An unbounded tool loop.** M8-L15 — cap steps and cost.

| Symptom | Likely cause | Fix |
|---|---|---|
| Occasional JSON parse failures | `max_tokens` truncation | Read `stopReason`; raise the budget; abstain on failure |
| Streaming works locally, not in production | A proxy or gateway buffering | Verify byte arrival through every hop |
| Request cut at exactly 10 or 30 seconds | A client-library default | Enumerate and set every timeout (§5.4) |
| Agent costs far more than expected | History resent each turn | Measure accumulated input tokens (M5-L15) |
| A model swap became a two-week project | Per-provider call sites | Move to the unified shape (§5.1) |

---

## 9. Security, privacy, reliability, cost

- **Security.** The model asks for a tool; your code decides whether to run it, under the task role's permissions
  (M9-L13, L08).
- **Privacy.** The request body is the data you send — the control M11-L01 §5.3 said was always yours. Hash and store it
  once (M10-L13).
- **Reliability.** Timeouts and `stopReason` handling are the two most common causes of user-visible failure in this
  layer.
- **Cost.** `usage` on every call, emitted as a metric; `maxTokens` as a cap; and awareness that tool loops multiply input
  tokens (M11-L06, L14).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. How many call sites change on a model swap with and without a unified API?
2. What is the total latency difference between streaming and non-streaming in §7.2?
3. Which layer in §7.3 is the effective timeout, and why is that surprising?
4. How many model round trips does the tool loop in §7.4 take?
5. What does `stopReason: max_tokens` mean for a JSON response?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the answer to 2,000 tokens and re-read sections 2 and 3.
2. Add your own client and proxy timeouts to §7.3.
3. Add a third tool call to §7.4 and recompute the token totals.
4. Compute the cost of the tool loop at your own prices.
5. Write the handler that treats each `stopReason` correctly (§5.5).

### Exercise 3 — Challenge (~60 min)

1. Enumerate every timeout on one real request path and set each from your p99.
2. Test for buffering end to end and record when the first byte actually arrives.
3. Implement the tool loop with argument validation, a step cap and a cost ceiling (M8-L05, M8-L15).
4. Emit `usage` as a metric and build an alarm on tokens per hour (M11-L16, M11-L06).
5. Measure how much of your input tokens are resent history, across a real conversation.

---

## 11. Quiz

*(Answers: [`answer-keys/module-12-answers.md`](../../answer-keys/module-12-answers.md#m12-l02).)*

**Q1.** What does a unified invocation API primarily buy you?

- A. Lower per-token pricing across providers
- B. A model swap becomes a configuration change rather than a rewrite
- C. Automatic failover between providers
- D. Higher throughput through connection reuse

**Q2.** In §7.1, how many call sites change on a model swap without a unified API?

- A. One
- B. Three
- C. Eleven
- D. None

**Q3.** What does streaming change?

- A. Total latency, by producing tokens faster
- B. Both total latency and time to first token
- C. Neither; it only changes the transport
- D. Time to first token, not total latency

**Q4.** Why does that matter so much for a user?

- A. Streaming reduces the number of tokens generated
- B. The answer arrives faster than the user can read it, so the perceived wait is the first token
- C. Streamed responses are cheaper per token
- D. Partial answers can be cached more effectively

**Q5.** What does streaming cost you?

- A. The ability to validate the whole output before showing it
- B. The ability to use tools in the same request
- C. Accurate token accounting
- D. Compatibility with the unified request shape

**Q6.** What is your effective timeout on a request path?

- A. The one configured in the SDK
- B. The load balancer's idle timeout
- C. The smallest one on the path
- D. The sum of all of them

**Q7.** Why can a streamed response survive an idle timeout that a non-streamed one does not?

- A. Streaming uses a different protocol that ignores idle timeouts
- B. Each chunk resets the idle timer — unless something on the path buffers
- C. Streamed responses are exempt from gateway limits
- D. The client reconnects automatically between chunks

**Q8.** In §7.4, how many model round trips did one user question require?

- A. One
- B. Two
- C. Three
- D. Six

**Q9.** Why do input tokens accumulate faster than the answer length suggests?

- A. Tool schemas are re-tokenised on each call
- B. Streaming duplicates the prompt
- C. Guardrails append text to each request
- D. The conversation history is resent on every turn

**Q10.** Who executes a tool the model asks for?

- A. The model, within the service
- B. Your code, under its own permissions
- C. The Bedrock service, using the caller's role
- D. Whichever the `toolChoice` policy specifies

**Q11.** What should a `stopReason` of `max_tokens` mean for structured output?

- A. Treat it as an error — the output is truncated and may be invalid
- B. Accept it; the model finished its answer early
- C. Retry the same request unchanged
- D. Strip the final field and parse the rest

**Q12.** Why record `usage` on every call?

- A. It is required for the request to be logged in CloudTrail
- B. It determines which quota tier applies
- C. It is the cost signal, the runaway detector and part of the audit record
- D. It is needed to compute the stop reason

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team wants to stream the assistant's answers to users. What
do you check and change before enabling it?

---

## 12. Revision notes

- **Unified shape**: **1** call site changes on a model swap, versus **11** with per-provider APIs.
- **Streaming changes perception, not speed**: first token at **640 ms**, total **7,840 ms** either way — and reading the
  answer takes **9.6×** the generation time.
- **It costs**: whole-output validation, simple guardrails, simple retries, and a path where nothing buffers.
- **Effective timeout = the smallest on the path.** In the lab, a **10-second client-library default**.
- **Tool loop**: **3 round trips**, history resent each turn, latency is the sum plus tool execution. Validate arguments,
  cap the loop, and execute tools yourself.
- **Read `stopReason` every time**; `max_tokens` is silent truncation. Record `usage` as a metric.

---

## 13. Completion checklist

- [ ] My model calls use the unified shape, with the model id pinned in configuration.
- [ ] I can state the total-latency effect of streaming honestly, and what it costs.
- [ ] Every timeout on the request path is enumerated and set from p99; nothing buffers.
- [ ] Structured output is not streamed to users unvalidated.
- [ ] `stopReason` is handled per case, and `max_tokens` is an error for structured output.
- [ ] `usage` is emitted as a metric on every call.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon Bedrock — Converse and ConverseStream: `messages`, `system`, `inferenceConfig`, `toolConfig`, `stopReason`,
  `usage` `[STABLE structure — verify current field details]`
- M5-L09 (streaming), M5-L06 and M5-L07 (structured output and repair), M5-L15 (token accounting) `[STABLE]`
- M5-L17 (provider portability) — what the unified shape is worth `[STABLE]`
- M8-L03 and M8-L05 (tool loop, argument validation), M8-L15 (step and cost limits) `[STABLE]`
- M11-L09 and M11-L13 (timeouts and buffering at the edge), M11-L16 (usage as a metric) `[STABLE]`

---

## 15. Next lesson

→ [M12-L03 — Embeddings on Bedrock](M12-L03-embeddings-on-bedrock.md) turns to the other model call in a RAG system —
and to the reason its version discipline is stricter than a generation model's: change the embedding model and every
vector you have ever stored becomes meaningless.
