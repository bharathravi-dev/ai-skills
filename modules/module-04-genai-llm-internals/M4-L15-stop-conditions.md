# M4-L15 — Stop Conditions, Truncated Output and Finish Reasons

| | |
|---|---|
| **Lesson ID** | M4-L15 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M4-L14](M4-L14-decoding.md), [M4-L06](M4-L06-context-windows.md) |

---

## 1. Learning objectives

1. **Name** the four ways generation ends and the `finish_reason` each produces.
2. **Detect** truncation reliably, and explain why output inspection alone cannot.
3. **Handle** a truncated response correctly for text, JSON and tool calls.
4. **Use** stop sequences correctly, including the boundary behaviour that surprises people.
5. **Design** a generation call that fails loudly rather than silently.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **EOS token** | The end-of-sequence special token the model emits when it considers the response complete. |
| **`max_tokens`** | Your cap on output length. |
| **Stop sequence** | A string that, when generated, halts generation. |
| **`finish_reason`** | The field reporting *why* generation stopped. |
| **Truncation** | Generation stopped before the model was finished. |
| **Content filter** | A provider-side check that can halt or replace output. |
| **Streaming** | Receiving tokens as they are produced. |
| **Partial JSON** | Structurally invalid JSON caused by truncation. |

---

## 3. Plain-language explanation

### 3.1 Four ways generation ends

| Cause | Typical `finish_reason` | Meaning |
|---|---|---|
| **The model emitted EOS** | `stop` / `end_turn` | It finished. This is the good one. |
| **`max_tokens` reached** | `length` / `max_tokens` | **Truncated.** The model had more to say. |
| **A stop sequence matched** | `stop` / `stop_sequence` | You told it to halt here. |
| **A filter or error intervened** | `content_filter`, `error` | Provider-side. |

`[UNVERIFIED — exact field names and values differ by provider; check your API's documentation.]`

**Only the first two matter for correctness**, and telling them apart is the entire subject of this
lesson.

### 3.2 Why you cannot detect truncation by looking at the text

A truncated response often *looks* complete:

```
"To reset your password, open Settings, select Security, and then"
```

There is no ellipsis, no error, no marker of any kind. **The stream simply stopped.** A response that
happens to be cut at a sentence boundary looks entirely finished.

**The only reliable signal is `finish_reason`.** It is one field, it is always present, and checking it
takes one line — and it is the most commonly skipped line in LLM application code.

```python
resp = client.generate(...)
if resp.finish_reason != "stop":
    raise TruncatedResponse(resp.finish_reason)   # do not parse this
```

### 3.3 Why truncated JSON is worse than truncated prose

Truncated prose is a degraded answer. **Truncated JSON is a parse error somewhere unrelated to the
cause:**

```json
{"order_id": "GB-4471", "items": [{"sku": "AB-1", "qty": 2}, {"sku": "CD-
```

Your JSON parser raises `Unterminated string at position 63`. Nothing in that message mentions
`max_tokens`, and the engineer who receives the alert at 3 a.m. will look at the parser, the schema and
the prompt before looking at the token limit.

**Check `finish_reason` before parsing.** It converts a confusing downstream failure into an accurate
one at the source.

---

## 4. Analogy

**A phone call that drops mid-sentence versus one that ends with "goodbye".** From the transcript alone
you cannot always tell which happened — but the call log records the reason, and it is right there.

### Where the analogy breaks

1. **A dropped call is obvious to the listener.** A truncated response frequently is not, especially if
   it stopped at a plausible boundary.
2. **You would call back.** Retrying a truncated generation costs money and may truncate again at the
   same place unless you change something.
3. **A call has one participant per end.** A truncated response may be *partially* correct and usable,
   which makes "discard it" the wrong default in some applications and the right one in others.
4. **Call logs are for humans. `finish_reason` is for your code**, and its value should change control
   flow.

---

## 5. Detailed technical explanation

### 5.1 The EOS token

The model learned during post-training (M4-L12) to emit an end-of-sequence token when a response is
complete. It is a **prediction**, exactly like any other token — so:

- It can be emitted **too early**, cutting a response short with `finish_reason: stop`.
- It can be **missed**, so the model rambles until `max_tokens`.
- Its probability is affected by temperature like everything else.

**`finish_reason: stop` therefore means "the model decided it was finished", not "the answer is
complete".** Those coincide most of the time and not always.

### 5.2 `max_tokens`

**Always set it.** Without it you risk a generation running to the context limit — which at a repetition
loop (M4-L14) is the *expected* outcome, not the unlucky one.

**Setting it correctly:**

```python
reserve = expected_length * 2        # headroom for variation
max_tokens = min(reserve, context_window - input_tokens)
```

**Too low truncates; too high risks runaway cost.** There is no way to know the right value except by
measuring your own outputs' length distribution — and then setting it at, say, the 99th percentile
plus margin.

### 5.3 Stop sequences

```python
stop = ["\n\nUser:", "```", "END"]
```

Generation halts when any of these is produced.

**Three behaviours that surprise people:**

1. **The stop sequence is usually *excluded* from the returned text.** If you stop on `` ``` `` you get
   the code block without its closing fence, and you must add it back.
2. **Matching is on the generated text, not on tokens.** A stop sequence can trigger mid-token in some
   implementations, or fail to match if it spans a token boundary awkwardly.
3. **`finish_reason` for a stop sequence is often the *same value* as for EOS.** Some providers
   distinguish them; some do not. **If you need to know which happened, check whether your stop string
   was produced** — do not rely on the reason field alone. `[UNVERIFIED — provider-dependent]`

**Use stop sequences to enforce a format**, not to control length. For length, use `max_tokens`.

### 5.4 Handling truncation, by output type

| Output | On truncation |
|---|---|
| **Prose** | Often still usable. Decide by policy, and mark it as partial. |
| **JSON** | **Never parse it.** Retry with a higher limit or a smaller request. |
| **Tool call** | **Never execute it.** A truncated argument list is a wrong action. |
| **Code** | Never run it. Syntactically valid truncated code is possible and dangerous. |
| **A list** | Drop the final item; it is probably incomplete. |

**The tool-call row is the serious one, and §7.3 measures why it is more subtle than it looks.**

**Raw truncated JSON almost never parses** — you would have to be cut at exactly a balanced closing
brace. So a pipeline that simply parses and fails is not the dangerous one.

**The dangerous pattern is the "repair" step people write when they tire of parse errors:** append
closing braces until it parses. §7.3 applies it to a truncated `delete_records` call:

| Cut at | Repaired? | Has `filter`? | Has `dry_run`? | Executing it would… |
|---|---|---|---|---|
| 123 (complete) | yes | ✅ | ✅ | delete archived only |
| 95 | **yes** | ✅ | **❌** | **delete for real — no dry run** |
| 44 | **yes** | **❌** | **❌** | **DELETE EVERY ROW** |

**The repair turns an unparseable truncation into valid JSON naming a real destructive action with its
safety arguments missing.** Every layer behaved reasonably: the model was cut off, the repair fixed the
syntax, the parser succeeded, and the executor did as it was told.

**Validate that every required argument is present, and check `finish_reason` before you get anywhere
near execution** (M8-L05).

### 5.5 A retry that actually helps

Retrying identically will truncate at the same place. **Change something:**

```python
def generate_complete(prompt, max_tokens=1000, attempts=3):
    for attempt in range(attempts):
        resp = client.generate(prompt, max_tokens=max_tokens)
        if resp.finish_reason == "stop":
            return resp.text
        max_tokens = min(max_tokens * 2, MODEL_LIMIT)      # change something
    raise TruncatedResponse(f"still truncated after {attempts} attempts")
```

**Better still: ask for less.** A prompt requesting a 200-word summary will not truncate at 1,000
tokens. Truncation is often a prompt problem wearing a configuration problem's clothes.

**Continuation** — sending the partial output back and asking the model to continue — works for prose
and is unreliable for structured output, because the model must resume mid-structure without having
generated the opening context itself.

### 5.6 Streaming

With streaming you receive tokens as produced, and the `finish_reason` arrives in the **final** chunk.

**The trap:** if you process chunks and forget to inspect the last one, you have built a system that
*cannot* detect truncation — you will have displayed a partial answer to a user and recorded a success.

```python
reason = None
async for chunk in stream:
    if chunk.finish_reason:
        reason = chunk.finish_reason
    yield chunk.text
if reason != "stop":
    yield "\n\n[Response was cut short.]"
```

### 5.7 Assumptions and limitations

- Field names and values are provider-specific and change. Everything here is marked `[UNVERIFIED]`
  where it depends on a provider.
- Some providers return a truncated response with a success status code. A `200` is not evidence of
  completeness (M2-L11).
- Content-filter behaviour varies from a modified response to a hard error.

---

## 6. Worked example — one bug, traced from symptom to cause

**The report:** *"About 2% of extractions fail with a JSON parse error. It works fine in testing."*

**The code:**

```python
resp = client.generate(prompt, max_tokens=200, temperature=0)
data = json.loads(resp.text)          # ← fails here, 2% of the time
```

**Step 1 — the error message.**

```
json.decoder.JSONDecodeError: Unterminated string starting at: line 1 column 187
```

**Nothing in this message mentions token limits.** It points at the parser and at character 187.

**Step 2 — the natural but wrong investigations.** An engineer will reasonably check: is the prompt
ambiguous? Is the model producing invalid JSON? Should we add a schema? Is temperature 0 set? Each of
these takes an hour and none of them is the cause.

**Step 3 — print `finish_reason`.**

```
finish_reason: "length"
```

**One line, and the investigation is over.** The model was not producing invalid JSON — it was
producing *valid* JSON and being cut off at 200 tokens.

**Step 4 — why exactly 2%?** Because output length has a distribution:

| Percentile | Output tokens |
|---|---|
| p50 | 95 |
| p90 | 150 |
| p95 | 178 |
| **p98** | **199** |
| p99 | 240 |

**`max_tokens=200` sits at the 98th percentile.** The 2% of documents with more line items exceed it.
The failures correlate with document complexity, which is exactly why they never appeared in a small
test set of simple examples (M3-L13 §5.4).

**Step 5 — the fix, in three parts:**

```python
resp = client.generate(prompt, max_tokens=600, temperature=0)

if resp.finish_reason != "stop":                    # 1. check FIRST
    raise TruncatedResponse(resp.finish_reason)     #    accurate error

data = validate_schema(json.loads(resp.text))       # 2. validate anyway
```

3. **Log the output-token distribution in production** so the limit can be set from data rather than
   guessed.

**Step 6 — the general lesson.** The bug was not in the parser, the prompt or the model. **It was a
missing one-line check that would have converted a confusing downstream error into an accurate one at
the source.** Every layer between `max_tokens` and `json.loads` faithfully passed along a truncated
string, and each did its job correctly.

---

## 7. Practical activity

**File:** [`labs/m4/l15_stop_conditions.py`](../../labs/m4/l15_stop_conditions.py)

**No API key, no network.** A mock generator reproduces every finish reason.

```bash
source .venv/bin/activate
python labs/m4/l15_stop_conditions.py
```

Reproduces §6's bug and its 2% failure rate from a realistic length distribution, shows truncated JSON
and truncated tool calls, demonstrates stop-sequence boundary behaviour, and compares a naive handler
with a correct one.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-09.

```text

============================================================================
1. THE FOUR WAYS GENERATION ENDS
============================================================================
  scenario                             finish_reason   tokens        text ends with
  small doc, generous limit                     stop       35  ' "price": 10.99}]}'
  large doc, tight limit                      length      100  '", "qty": 4, "pric'
  stop sequence matched                stop_sequence       10  'currency": "GBP", '
  provider filter (simulated)         content_filter        0                    ''

  Look at the 'text ends with' column for the first two rows. Neither
  gives any indication of which one was truncated. The text is the same
  KIND of string in both cases -- only finish_reason distinguishes them.

============================================================================
2. REPRODUCING THE LESSON'S BUG: WHY EXACTLY 2%?
============================================================================
  5,000 documents, output-token distribution:

    percentile   output tokens
           p50              69
           p90             136
           p95             170
           p98             193
           p99             215
         p99.9             283
          p100             350

    max_tokens   truncated   failure rate   cost vs p50
           100       1,516        30.32%          1.4x
           150         366         7.32%          2.2x
           200          95         1.92%          2.9x
           300           2         0.04%          4.3x
           600           0         0.00%          8.7x
          1000           0         0.00%         14.5x

  At max_tokens=200 the failure rate is 1.92%, because
  200 sits at the 98.1th percentile of output length.

  The failures correlate with DOCUMENT COMPLEXITY -- exactly the
  documents a small test set of simple examples would not contain
  (M3-L13 section 5.4). That is why it 'works fine in testing'.

============================================================================
3. WHAT THE ENGINEER ACTUALLY SEES
============================================================================
  finish_reason : 'length'
  output tokens : 200
  text (last 60): ...'15", "qty": 4, "price": 24.99}, {"sku": "AB-016", "qty": 1, '

  the naive pipeline:
    data = json.loads(resp.text)
    -> json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes at line 1 column 801

  NOTHING in that message mentions max_tokens. It names the PARSER and
  a character offset. An engineer will reasonably check the prompt, the
  schema, the temperature and the model before checking the token limit.

  the one line that ends the investigation:
    print(resp.finish_reason)  ->  'length'

============================================================================
4. THE DANGEROUS CASE: A TRUNCATED TOOL CALL THAT PARSES
============================================================================
  the intended call:
    {"action": "delete_records", "table": "orders", "filter": {"status": "archived", "before": "2020-01-01"}, "dry_run": false}

    cut at   parses?   raw truncated JSON
       123      True   ': "2020-01-01"}, "dry_run": false}'
       118     False   'fore": "2020-01-01"}, "dry_run": f'
        95     False   'tatus": "archived", "before": "202'
        60     False   '", "table": "orders", "filter": {"'
        44     False   ' "delete_records", "table": "order'
        30     False   '{"action": "delete_records", "'

  GOOD NEWS FIRST: raw truncated JSON almost never parses. You would
  need to be cut at exactly a balanced closing brace. So a pipeline that
  simply parses and fails is not the dangerous one.

  THE DANGEROUS PATTERN is the 'repair' step people write when they
  get tired of parse errors -- append closing braces until it parses:

    cut at  repaired?            action   filter?  dry_run?   what executing it would do
       123        yes    delete_records      True      True   deletes archived only
       118         no                 -         -         -   (rejected, correctly)
       108         no                 -         -         -   (rejected, correctly)
        95        yes    delete_records      True     False   deletes for real (no dry_run)
        60         no                 -         -         -   (rejected, correctly)
        44        yes    delete_records     False     False   DELETES EVERY ROW

  There it is. The repair step turns an unparseable truncation into
  VALID JSON that names a real destructive action with its safety
  arguments missing. Every layer behaved reasonably: the model was cut
  off, the repair 'fixed' the syntax, the parser succeeded, and the
  executor did what it was told.

  A schema validator that only asks 'is this valid JSON' passes it.
  You must check that every REQUIRED argument is present -- and check
  finish_reason before you get anywhere near execution (M8-L05).

  what a correct guard looks like:
  input                                    safe?   reason
  complete call, finish_reason=stop         True   ok
  complete call, finish_reason=length      False   finish_reason='length' -- refusing to execute
  truncated but valid JSON                 False   finish_reason='length' -- refusing to execute
  truncated, invalid JSON                  False   finish_reason='length' -- refusing to execute

  Note row 2: a COMPLETE call is still refused because finish_reason
  was wrong. That is deliberate -- fail closed.

============================================================================
5. STOP SEQUENCES: THE BOUNDARY BEHAVIOUR
============================================================================
  the model would produce:
    '```python\nprint("hello")\n```\nThat prints a greeting.'

  with stop=['```'] the returned text is:
    '```python\nprint("hello")\n'

  the closing fence is NOT included. Count them:
    fences in the returned text: 1  (should be 2 for valid markdown)
    valid markdown code block?   False

  the fix -- append it back:
    '```python\nprint("hello")\n```'
    fences: 2   valid: True

  And the reason field is ambiguous on many providers:
  ended by                   finish_reason    distinguishable?
  model emitted EOS                   stop                    
  stop sequence matched               stop NOT from this field

  If you need to know which happened, check whether YOUR stop string
  was produced. Do not rely on the reason field alone.

============================================================================
6. A NAIVE HANDLER vs A CORRECT ONE
============================================================================
  scenario         reason   naive handler                               correct handler                             
  small doc          stop   parsed (may be wrong)                       parsed                                      
  medium doc         stop   parsed (may be wrong)                       parsed                                      
  large doc        length   JSONDecodeError: Expecting property name en incomplete response: finish_reason='length  

  Both handlers FAIL on the large document -- the difference is the
  error they produce. The naive one names the parser and a character
  offset; the correct one names the actual cause and the fix.
  That difference is the whole value of the check: it does not prevent
  the failure, it makes the failure legible.

============================================================================
7. A RETRY THAT ACTUALLY HELPS
============================================================================
  document          attempts   trace (attempt, max_tokens, reason)
  small (2 items)          1   (1,100,stop)
  medium (12)              2   (1,100,length)  (2,200,stop)
  large (40)               4   (1,100,length)  (2,200,length)  (3,400,length)  (4,800,stop)
  huge (200)               4   (1,100,length)  (2,200,length)  (3,400,length)  (4,800,length)

  Doubling the limit each time converges quickly. Retrying with the
  SAME limit would truncate at exactly the same place every time --
  temperature 0 or not, nothing about the request has changed.

  But the better fix is usually upstream: ask for less output. A prompt
  requesting a 200-word summary does not truncate at 1,000 tokens.
  Truncation is often a prompt problem wearing a config problem's
  clothes.

Done.
```

### 7.3 Reading the result

**Section 1 is the whole argument in one table.** A completed response ends `' "price": 10.99}]}'`; a
truncated one ends `'", "qty": 4, "pric'`. **Neither ending tells you which is which** — the truncated
one simply stops, and if it had stopped two characters later it would have looked entirely finished.

**Section 2 reproduces §6's bug exactly.** From a realistic distribution of 5,000 documents:

| `max_tokens` | Failure rate | Cost vs p50 |
|---|---|---|
| 100 | **30.32%** | 1.4× |
| 200 | **1.92%** | 2.9× |
| 300 | 0.04% | 4.3× |
| 600 | 0.00% | 8.7× |

**`max_tokens = 200` gives a 1.92% failure rate because 200 sits at the 98.1st percentile** of output
length. The lesson's "about 2%" is not a round number chosen for the story — it falls out of where the
limit sits on the distribution.

And the failures correlate with **document complexity**, which is exactly the property a small test set
of simple examples will not have (M3-L13 §5.4). That is the mechanism behind "it works fine in
testing".

**Section 3 shows what the engineer actually receives:**

```
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes at line 1 column 801
```

**Nothing in that message mentions token limits.** It names the parser and a character offset. The
natural investigations — is the prompt ambiguous, is the schema wrong, is temperature set — each cost
an hour and none is the cause. **One line prints `'length'` and the investigation is over.**

**Section 4 corrected this lesson, and the correction makes the danger sharper rather than softer.**

I had written that a truncated tool call "may still parse". Measured, **raw truncated JSON almost never
parses** — five of six cut points were rejected outright. That is good news, and it means the naive
failure mode is safe.

**The dangerous path is the repair step.** Appending closing braces until the string parses — a pattern
that genuinely appears in production code — produces:

- at cut 95: valid JSON with `filter` but **no `dry_run`** → deletes for real
- at cut 44: `{"action": "delete_records"}` → **deletes every row in the table**

**Both are valid JSON naming a real action.** A validator that asks only "does this parse" passes both.

The correct guard refuses all four test cases including a **complete** call whose `finish_reason` was
`length` — failing closed rather than reasoning about whether the completeness was coincidental.

**Section 5 shows the stop-sequence boundary.** Stopping on `` ``` `` returns **one** fence where valid
markdown needs two, so the code block is malformed until you append it back. And the reason field is
**the same value** for "model finished" and "stop sequence matched" on many providers — so if you need
to distinguish them, check whether your stop string was produced.

**Section 6 makes the point of the check precise.** Both handlers *fail* on the large document. The
difference is the error: the naive one names the parser and column 801; the correct one names
`finish_reason='length'` and says to raise the limit.

**The check does not prevent the failure. It makes the failure legible** — which is the entire value,
and why it is worth one line in every call site.

**Section 7 shows a retry that converges** — doubling from 100 reaches `stop` in 2 attempts for a
medium document and 4 for a large one, while a 200-item document still fails after four. Retrying at
the *same* limit would truncate at exactly the same place every time, temperature 0 or not, because
nothing about the request has changed.

**And the closing note is the one to act on: truncation is often a prompt problem wearing a
configuration problem's clothes.** A prompt that asks for a 200-word summary does not truncate at 1,000
tokens.

---

## 8. Common mistakes and troubleshooting

1. **Not checking `finish_reason`.** The single most common omission in LLM code.
2. **Parsing JSON before checking it.**
3. **Executing a truncated tool call.**
4. **Not setting `max_tokens` at all.**
5. **Setting `max_tokens` from a guess** rather than a measured distribution.
6. **Retrying identically** after truncation.
7. **Ignoring the final streaming chunk.**
8. **Assuming the stop sequence is included** in the returned text.

| Symptom | Likely cause | Fix |
|---|---|---|
| Intermittent JSON parse errors | Truncation at `max_tokens` | Check `finish_reason`; raise the limit |
| Answers cut mid-sentence | Truncation | Same |
| Code block missing its closing fence | Stop sequence excluded | Append it back |
| Tool call executed with wrong arguments | Truncated call parsed anyway | Validate all required arguments |
| Works in tests, fails in production | Test inputs were shorter | Test with realistic length distribution |
| Streaming never reports truncation | Final chunk ignored | Capture the last chunk's reason |
| Costs spiked overnight | No `max_tokens` plus a repetition loop | Set a limit |

---

## 9. Security, privacy, reliability, cost

- **Security.** **Never execute a truncated tool call.** A partial argument set can be both valid and
  destructive — `{"action": "delete_records"}` missing its filter is the canonical example (M8-L05).
- **Reliability.** `finish_reason` should change control flow, not be logged and ignored. Treat
  anything other than a normal stop as a failed request.
- **Cost.** Always set `max_tokens`. Without it, a repetition loop generates to the context limit and
  you pay for every token (M4-L14).
- **Cost.** Log the output-length distribution. Setting `max_tokens` from p99 rather than a guess
  prevents both truncation and runaway cost.
- **Reliability.** A `200` status does not mean a complete response (M2-L11). Check the field.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Name the four ways generation ends and their typical `finish_reason`.
2. Why can truncation not be detected from the text?
3. What should you do with truncated JSON? With a truncated tool call?
4. Why is retrying identically after truncation pointless?
5. Where does `finish_reason` arrive when streaming?

### Exercise 2 — Intermediate (~30 min)

1. Run the lab and reproduce the 2% failure rate.
2. Write `generate_checked()` that raises on any non-normal finish reason, and test it against all four.
3. Given a length distribution, compute the `max_tokens` needed for a 99.9% success rate.
4. Demonstrate a truncated tool call that parses successfully and would be dangerous to execute.
5. Implement stop-sequence handling that re-appends the sequence when needed.

### Exercise 3 — Challenge (~40 min)

1. Build a retry policy that doubles `max_tokens`, caps at the model limit, and reports which attempt
   succeeded. Test all paths.
2. Implement continuation for prose and show it failing on structured output. Explain the mechanism.
3. Build a streaming handler that detects truncation and appends a marker, and test it with a stream
   that truncates.
4. Instrument a generation function to record the output-length distribution, then compute the
   `max_tokens` that would have prevented 99% of truncations at minimum cost.
5. Write the incident runbook for "intermittent JSON parse errors in extraction", ordered by cost to
   check.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l15).)*

**Q1.** How do you reliably detect that a response was truncated?

- A. Inspect the `finish_reason` field returned with the response.
- B. Compare the response length against the requested maximum.
- C. Check whether the text ends with sentence-final punctuation.
- D. Attempt to parse the output and catch any resulting error.

**Q2.** `finish_reason` is `length`. This means:

- A. The response exceeded the model's total context window.
- B. Generation stopped at `max_tokens` before the model finished.
- C. The prompt was too long to process in a single request.
- D. A stop sequence was matched in the generated output.

**Q3.** What should you do with truncated JSON?

- A. Parse it and use whichever fields were successfully returned.
- B. Do not parse it; retry with a higher limit or smaller request.
- C. Append closing braces and brackets to repair the structure.
- D. Log a warning and pass the partial string to the next stage.

**Q4.** Why is a truncated tool call especially dangerous?

- A. It always raises an exception in the tool-calling framework.
- B. Truncated calls are billed at a higher rate than complete ones.
- C. The model retries the call automatically without being asked.
- D. A repair step can make it valid while dropping a safety argument.

**Q5.** `finish_reason: stop` guarantees:

- A. The answer is complete and correct for the question asked.
- B. No stop sequence was matched during the generation.
- C. The model decided it was finished, which is not the same thing.
- D. The output will parse successfully as valid JSON.

**Q6.** Retrying identically after truncation:

- A. Usually succeeds, since sampling introduces variation.
- B. Will truncate again unless something is changed.
- C. Is prevented automatically by most provider SDKs.
- D. Doubles `max_tokens` by default on the second attempt.

**Q7.** When streaming, `finish_reason` arrives:

- A. In the first chunk, before any content is emitted.
- B. In the HTTP response headers, ahead of the body.
- C. In the final chunk of the stream.
- D. Only if you request it explicitly as a parameter.

**Q8.** A stop sequence matched. The returned text:

- A. Usually excludes the stop sequence itself.
- B. Always includes the stop sequence at the end.
- C. Includes it only when streaming is enabled.
- D. Is truncated at a token boundary before the sequence.

**Q9.** In §6, why did the bug appear in only 2% of cases?

- A. `max_tokens` sat at the 98th percentile of output length.
- B. The model produces invalid JSON at roughly that rate.
- C. Two percent of the documents contained malformed input.
- D. Temperature 0 still permits occasional format variation.

**Q10.** You should set `max_tokens` from:

- A. The model's documented maximum output length.
- B. A round number that is comfortably large.
- C. A measured percentile of your output-length distribution.
- D. The remaining space in the context window.

**Q11.** *(Written, rubric-graded.)* In under 100 words, write the incident note explaining why
extraction failed for 2% of documents, aimed at a team that has already spent a day on the parser.

---

## 12. Revision notes

- **Four ways generation ends:** EOS emitted (`stop`), `max_tokens` hit (`length` — **truncated**), a
  stop sequence matched, or a filter/error.
- **Truncation cannot be detected from the text.** There is no marker. **`finish_reason` is the only
  reliable signal**, and checking it is one line.
- **`finish_reason: stop` means the model decided it was finished** — not that the answer is complete.
- **Truncated JSON: do not parse.** The parse error names the parser, not the token limit, and sends
  the investigation to the wrong place.
- **Truncated tool call: do not execute.** Measured: raw truncated JSON almost never parses — but a
  **"repair" step that appends closing braces** turns it into valid JSON naming a real destructive
  action with `filter` and `dry_run` missing. **Validate every required argument, and fail closed on
  any non-normal finish reason** (M8-L05).
- **Always set `max_tokens`**, from a **measured percentile** of your own output lengths, not a guess.
  Measured: a limit at the 98.1st percentile produced a **1.92%** failure rate; moving to p99.9 removed
  it at 4.3× the p50 cost.
- **Retrying identically is pointless.** Change something — raise the limit, or ask for less.
- **When streaming, the reason is in the final chunk.** Ignore it and you have built a system that
  cannot detect truncation.
- **Stop sequences are usually excluded** from the returned text, and often share a `finish_reason`
  with EOS. **Use them for format, not length.**
- **A `200` is not evidence of completeness.**

---

## 13. Completion checklist

- [ ] I can name the four finish reasons and what each implies.
- [ ] I check `finish_reason` before parsing, in every call I write.
- [ ] I know why the JSON *repair* pattern is the dangerous one, not the parse failure.
- [ ] I set `max_tokens` from measured data, not a guess.
- [ ] I know where the reason arrives when streaming.
- [ ] I know stop sequences are usually excluded from the output.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- OpenAI API reference, *Chat Completions*. <https://platform.openai.com/docs/api-reference/chat>
  `[UNVERIFIED]`
- Anthropic API reference, *Messages*. <https://docs.anthropic.com/en/api/messages> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L16 — Training Knowledge vs Runtime Context](M4-L16-knowledge-vs-context.md)

You can tell a finished answer from a cut-off one. Next: the distinction between what the model *knows*
and what you *told it* — and why conflating them causes most of the confusion about memory.
