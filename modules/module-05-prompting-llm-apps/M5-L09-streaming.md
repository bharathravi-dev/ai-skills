# M5-L09 — Streaming and User Experience

| | |
|---|---|
| **Lesson ID** | M5-L09 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L13](../module-02-python-foundations/M2-L13-async.md), [M5-L06](M5-L06-structured-output.md) |

---

## 1. Learning objectives

1. **Decode** a byte stream correctly, and explain why the naive version passes your tests.
2. **State** what streaming buys and what it costs, in seconds and in capability.
3. **Decide** which parts of a response may stream and which must be buffered.
4. **Account** for tokens consumed by a stream that never finished.
5. **Recognise** that a streamed response cannot be validated before the user sees it.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Streaming** | Delivering the response incrementally as it is generated. |
| **TTFT** | Time to first token. |
| **Chunk** | One delivery from the transport — a byte count, not a character or token count. |
| **SSE** | Server-sent events, the usual transport for LLM streams. |
| **Incremental decoder** | A decoder holding partial multi-byte sequences between chunks. |
| **Grapheme cluster** | What a reader calls "a character" — may be several code points. |
| **Retraction** | Removing output the user has already seen. |
| **Buffering** | Collecting the whole response before showing any of it. |
| **Usage event** | The provider's final message carrying token counts. |

---

## 3. Plain-language explanation

### 3.1 Streaming does not make anything faster

The total time is identical. Every token still has to be generated.

**What changes is where the wait goes:** from *before the first word* to *between words*. That is a
real and often large improvement in how the wait feels — and it is not a performance improvement, which
matters when someone proposes streaming to fix a latency problem.

§7.3 prices it. At a 20-token response, streaming moves the wait from 0.81 s to 0.45 s — a difference
nobody notices. At 1,200 tokens it moves from 22 s to 0.45 s, which changes the product.

> **Streaming is worth its complexity in proportion to response length.** For short responses it is
> cost with no benefit.

### 3.2 What it costs

**You give up the ability to withhold output.** Every control in this module so far — validation
(M5-L06), repair (M5-L07), permission checks on tool calls (M5-L08) — assumed you could inspect the
response before acting. Streaming shows the user the response *while* it is being produced.

§7.3 measures the consequence: a JSON response first parses at **100%** of its length. There is no
prefix at which you can validate, so the whole thing is displayed and *then* rejected.

### 3.3 The bug that passes your tests

Transports deliver **bytes**. A chunk boundary falls where the network puts it, which may be in the
middle of a character.

`"£"` is two bytes. `"東"` is three. `"🇬🇧"` is eight. If a chunk ends between them, `chunk.decode()`
raises — or, worse, silently produces the wrong text.

**And it will pass your tests**, because your test data is ASCII and your chunks are large. §7.3 shows
naive decoding working at 64-byte chunks and failing at 16.

---

## 4. Analogy

A translator working live versus one who hands you a finished document.

Live, you hear the meaning develop; you are engaged from the first second. But if the speaker retracts
something, the translator can only say *"sorry — not that"*. **You already heard it.**

The finished document can be checked before you read a word. You wait longer, and nothing you read has
to be taken back.

### Where the analogy breaks

- **A translator works in units of meaning.** A stream arrives in units of bytes, which may not even be
  whole characters.
- **You can ask a translator to hold on.** A stream is already billed for what has been generated,
  whether or not you display it.
- **A human translator notices they are saying something wrong.** A model does not; the check is your
  code's, and your code cannot run it until the end.

---

## 5. Detailed technical explanation

### 5.1 Decode incrementally

`[REAL]` The same 191-byte response, chunked at different sizes:

| Chunk size | Naive `chunk.decode()` | Incremental decoder |
|---|---|---|
| 1 | `UnicodeDecodeError` | OK |
| 4 | `UnicodeDecodeError` | OK |
| 8 | `UnicodeDecodeError` | OK |
| 16 | `UnicodeDecodeError` | OK |
| **64** | **OK** | OK |
| **256** | **OK** | OK |

**Read the last two rows.** The naive version *passes* at larger chunk sizes — which is exactly how this
reaches production. ASCII test fixtures, large chunks, green pipeline, and then a user in Munich sees
`GrÃ¼ÃŸe`.

```python
import codecs

decoder = codecs.getincrementaldecoder("utf-8")()
for chunk in stream:                     # chunk is bytes
    text = decoder.decode(chunk)         # may return "" and hold the remainder
    if text:
        emit(text)
emit(decoder.decode(b"", final=True))    # flush; raises on a truncated sequence
```

**Three lines, and they are missing from a great deal of streaming code.** Note the final flush: without
it, a stream ending mid-character loses the last character silently rather than raising.

**And correct decoding is still not enough for display.** Decoding the first 10 bytes of
`"Ready 🇬🇧 done"` yields `"Ready 🇬"` — a perfectly valid string, and half a flag. Rendering each chunk
as it arrives means the user watches characters assemble themselves. For most prose this is
unnoticeable; for emoji, combining accents and some scripts it is not.

If you are using a provider SDK, it very likely handles UTF-8 for you. **Check, and write the test** —
this is a two-line test with a `£` in it.

### 5.2 You cannot validate a prefix

`[REAL]` Streaming a 151-character JSON response:

| % received | Parses? |
|---|---|
| 10% | no |
| 50% | no |
| 90% | no |
| 99% | no |
| **100%** | **yes** |

A JSON object is not valid until its closing brace. **There is no prefix at which you can validate, and
therefore none at which you can act.**

The consequence is sharper than it first looks:

| Failure | Bad field appears at | Detectable at | Shown meanwhile |
|---|---|---|---|
| Refund over the cap | char 24 (18%) | char 133 (100%) | **109 chars** |
| Invented category | char 1 (0%) | char 132 (100%) | **131 chars** |
| Invented field | char 113 (86%) | char 130 (100%) | 17 chars |

**The invalidating field arrives early and is actionable only at the end.** `"category":"escalation"` is
the first thing in the response and you cannot reject it until the last.

**Partial-JSON parsers exist and do not solve this.** They can tell you the object *so far*; they cannot
tell you the object is *complete and valid*, and a bound like `le=500` is meaningless until you know the
field is finished. A partial parser that reports `refund_pence: 4` while `4250` is still arriving is
worse than no parser.

### 5.3 What streaming buys, in seconds

`[REAL arithmetic; illustrative speeds]` TTFT 0.45 s, 55 tok/s generation, 5 tok/s reading:

| Response | Total time | Non-streaming wait | Streaming wait | Improvement | Reading time |
|---|---|---|---|---|---|
| 20 tok | 0.81 s | 0.81 s | 0.45 s | 0.36 s | 4 s |
| 60 tok | 1.54 s | 1.54 s | 0.45 s | 1.09 s | 12 s |
| 150 tok | 3.18 s | 3.18 s | 0.45 s | 2.73 s | 30 s |
| 400 tok | 7.72 s | 7.72 s | 0.45 s | 7.27 s | 80 s |
| **1,200 tok** | 22.27 s | **22.27 s** | **0.45 s** | **21.82 s** | 240 s |

**Total time is identical in every row.** Streaming moves the wait; it does not remove it.

**And note the last column.** At 55 tok/s the model outruns a reader by roughly 11×. Past a few hundred
tokens the user is reading, not waiting — so *further* generation speed buys nothing, and a faster model
would not improve this experience at all. **Know which of the two you are short of** before optimising.

### 5.4 The retraction problem

When a streamed response turns out to be unacceptable, you have two options and neither is good:

- **Retract** — remove text the user has read. Visible, looks like a malfunction, and impossible on a
  shared screen or a screenshot.
- **Append** — *"Actually, disregard that."* Honest, and you have still shown it.

Three honest designs:

| Design | What streams | Safe for |
|---|---|---|
| Stream everything | all output | Low-stakes prose |
| **Stream prose, buffer JSON** | the explanation only | **Most applications** |
| Buffer everything | nothing | Decisions, money, actions |

**The middle row is the default to reach for.** Structure the response in two parts — a human-readable
explanation and a machine-readable decision — and stream only the first. The user sees progress; your
code still validates before anything is acted on.

> **Never stream a tool call.** By the time you have seen enough to know what it does, you have shown
> the user an action you may be about to refuse (M5-L08). Buffer tool calls, always.

**And for anything moderated:** a moderation check that runs on the complete response runs after the
user has read it. If you need pre-display moderation, you need buffering — or a moderation pass that
works on chunks and accepts the false-positive rate that implies.

### 5.5 Accounting for streams that die

A stream that breaks at 60% has consumed everything generated so far. Most providers report usage
**only in the final event**, which never arrives.

`[REAL arithmetic; illustrative prices]`

| Stream failure rate | Uncounted $/month | Share of spend |
|---|---|---|
| 2% | $2 | 1.5% |
| 10% | $9 | 7.5% |
| **25%** | **$22** | **19.6%** |
| 50% | $44 | 42.3% |

**At a 2% failure rate the gap is small, and the size is not the point.** The error is
**one-directional**: your dashboard always under-reports, never over-reports. The gap is invisible until
the invoice, and it widens exactly when things are going badly — long responses, poor connections,
provider trouble.

```python
received_out_tokens = 0
for chunk in stream:
    received_out_tokens += estimate_tokens(chunk)      # count what ARRIVED
    ...
# reconcile with the provider's figure when a final usage event exists
```

**Count what you received; reconcile with the provider's number when you get one** (M5-L15).

**Retrying a broken stream is a second full charge.** A stream that dies at 60% and is retried costs 1.6
responses for one result — so M5-L07's retry budget applies here, and the **deadline** bound matters
more than usual, because a stalled stream holds a connection open in your process as well as theirs
(M2-L13).

### 5.6 Operational details that bite

| Issue | Consequence | Handling |
|---|---|---|
| **Stalled stream** | Connection held, worker occupied | Idle timeout *between chunks*, not just total |
| **Client disconnects** | You keep paying; provider keeps generating | Detect and cancel upstream |
| **Buffering proxy** | Your stream is silently un-streamed | Disable buffering on the path; test end to end |
| **`finish_reason` arrives last** | You cannot know it was truncated until the end | Never act on a stream you have not seen finish (M4-L15) |
| **Errors mid-stream** | HTTP 200 already sent; you cannot change the status | Carry an error *inside* the stream and handle it client-side |

**The last one is worth dwelling on.** By the time the first chunk is sent, your HTTP status is 200. A
failure at 70% cannot be a 500. Your stream format must be able to say "this went wrong", and your
client must handle that as a first-class case rather than treating a truncated stream as a complete one.

### 5.7 Assumptions and limitations

- Everything in §7.3 except the prices and speeds is real: codec behaviour, JSON prefix behaviour, and
  arithmetic on stated inputs.
- TTFT and tokens/second are illustrative and vary by model, load and region. Measure yours.
- Reading speed of 5 tok/s is a rough figure for prose scanning. It varies enormously.
- SSE framing, reconnection semantics and the exact shape of the final usage event differ by provider.
  `[UNVERIFIED — check current documentation.]`

---

## 6. Worked example — the assistant that promised a refund it could not give

**The system.** A support assistant streams its answer. The response is one message: prose explanation
plus a JSON decision block at the end.

**What the user sees, over four seconds:**

```
Thanks for getting in touch — I can see the duplicate charge on order
GB-4471 from 3 March. That's clearly our error, and I've arranged a full
refund of £940.00 back to your original payment method. It should appear
within 3–5 working days.

{"action":"refund","order_id":"GB-4471","amount_pence":94000}
```

**What happens next.** The JSON is validated. `amount_pence: 94000` exceeds the £500 cap. The refund is
refused.

**The user has already read that they are getting £940.**

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The prose asserted the outcome before it was authorised | The promise was made by a component with no authority to make it |
| 2 | Prose and decision in one streamed response | No way to withhold one without withholding both |
| 3 | Validation only at the end | Everything is shown before anything is checked |

**Note that the model was not wrong.** A £940 refund for a duplicate £940 charge is the right answer. The
*policy* says refunds over £500 need approval — and the policy lives in your code, where the model
cannot see it, and was applied after the user was told otherwise.

### The fix

**Two calls, not one, and only the second streams.**

```
1. Decide      →  buffered, validated, authorised     (no user-visible output)
2. Explain     →  streamed, given the AUTHORISED decision as input
```

```python
decision = validate(call_model(decide_prompt, doc))   # buffered
outcome = authorise(session, decision)                # your code, your policy
async for chunk in call_model(explain_prompt, outcome):
    yield chunk                       # the explanation cannot contradict it
```

**The explanation is generated from the authorised outcome**, so it cannot promise something the system
will not do. The user waits ~0.4 s longer for the decision call and then gets a streamed explanation of
a decision that is already true.

| Change | What it fixes |
|---|---|
| Decision buffered and validated first | Nothing is promised before it is authorised |
| Explanation generated *from* the outcome | The prose cannot contradict the decision |
| Only the explanation streams | The perceived-latency benefit is kept |
| Cap enforced before any output | The £940 becomes "approval needed" *in the prose* |

**And a cheaper partial fix**, if two calls are too expensive: keep one call, but **buffer until the
decision block has been parsed and validated**, then stream the prose. You lose TTFT on the prose but
keep it far below the full response time, and you never assert an unauthorised outcome.

**The general rule.** **Never stream a claim your system has not yet committed to.** Streaming is a
presentation choice; it must not be allowed to become a decision-making one.

---

## 7. Practical activity

**File:** [`labs/m5/l09_streaming.py`](../../labs/m5/l09_streaming.py)

**No API key, no network, no cost.**

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l09_streaming.py
```

**Almost all of this lab is real** — Python's codecs, the JSON format's own behaviour, and arithmetic on
stated inputs. Streaming is one of the few LLM topics where the hard parts belong to your transport code
rather than to the model, so a mock would be beside the point.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.12.3, NumPy 2.5.3.

```text
============================================================================
1. CHUNK BOUNDARIES SPLIT CHARACTERS
============================================================================
  A realistic response: currency symbols, accents, CJK, an emoji.

    165 characters, 191 bytes (26 bytes of multi-byte characters)

  Transports deliver BYTES. The chunk boundary falls wherever the
  network puts it -- not on character boundaries.

   chunk size   chunks   naive decode          incremental decode  
            1      191   UnicodeDecodeError    OK                  
            4       48   UnicodeDecodeError    OK                  
            8       24   UnicodeDecodeError    OK                  
           16       12   UnicodeDecodeError    OK                  
           64        3   OK                    OK                  
          256        1   OK                    OK                  

  The naive version is not merely fragile -- it fails on the FIRST
  multi-byte character whenever the chunk size does not happen to
  align with it. At 64 and 256 bytes it may pass, which is exactly
  how this reaches production: ASCII test data, large chunks, green.

  The fix is three lines and belongs in every streaming client:

    dec = codecs.getincrementaldecoder("utf-8")()
    for chunk in stream:  text = dec.decode(chunk)
    text += dec.decode(b"", final=True)   # flush at the end

  Even correct decoding does not give you whole GRAPHEMES. Decoding
  the first 10 bytes of 'Ready 🇬🇧 done' yields 'Ready 🇬' --
  a valid string, and half a flag. If you render each chunk as it
  arrives, the user watches characters assemble themselves.

============================================================================
2. YOU CANNOT VALIDATE A PARTIAL RESPONSE
============================================================================
  Streaming a JSON response. At each prefix, ask two questions:
  does it parse yet, and can I already tell it will be wrong?

  response is 151 characters

   % received  chars   parses   shown to user
           10     15       no              15
           25     37       no              37
           50     75       no              75
           75    113       no             113
           90    135       no             135
           99    149       no             149
          100    151      yes             151

  It first parses at 100% -- which is to say, at the end.
  A JSON object is not valid until its closing brace, so there is no
  prefix at which you can validate and no prefix at which you can
  safely act.

  Now the consequence. Suppose the completed response fails
  validation. How much had the user already seen?

  failure                 bad field appears at   detectable at   shown meanwhile
  refund over the cap            char 24 (18%) char 133 (100%)         109 chars
  invented category                char 1 (0%) char 132 (100%)         131 chars
  invented field                char 113 (86%) char 130 (100%)          17 chars

  The field that makes it invalid arrives EARLY -- but you cannot act
  on that, because a field is only invalid in the context of a schema
  you can only apply to a complete object. So the whole thing streams,
  and then you reject it.

  This is the streaming trade, stated exactly:
    you buy perceived latency with the ability to withhold output.

============================================================================
3. WHAT STREAMING ACTUALLY BUYS
============================================================================
  Arithmetic, not simulation. TTFT = time to first token.

  TTFT 0.45s, generation 55 tok/s, reading 5 tok/s  [ILLUSTRATIVE]

    response  total time  non-stream wait  stream wait  improvement  reading time
          20       0.81s            0.81s        0.45s        0.36s          4.0s
          60       1.54s            1.54s        0.45s        1.09s         12.0s
         150       3.18s            3.18s        0.45s        2.73s         30.0s
         400       7.72s            7.72s        0.45s        7.27s         80.0s
        1200      22.27s           22.27s        0.45s       21.82s        240.0s

  Two readings of that table.

  1. Streaming does not make anything faster. Total time is identical.
     It moves the wait from BEFORE the first word to BETWEEN words.
  2. The value depends entirely on length. At 20 tokens the user waits
     0.81s instead of 0.45s -- a difference nobody notices, for which
     you accepted every complication in this lab. At 1,200 tokens the
     wait falls from 22s to 0.45s, and that is transformative.

  And note the last column: at 55 tok/s the model outruns the reader
  by 11x. Past a few hundred tokens the user is reading, not waiting,
  so further generation speed buys nothing at all.

============================================================================
4. THE RETRACTION PROBLEM
============================================================================
  Three things you can do when a streamed response turns out bad.

  what went wrong                         % already shown           options
  validation failed at the end                       100%    retract/append
  moderation flagged it at the end                   100%    retract/append
  tool call was not permitted                        100%    retract/append
  the model contradicted itself midway                60%    retract/append

  'Retract' means removing text the user has already read. It is
  visible, it looks like a malfunction, and on a shared screen or a
  screenshot it is not retractable at all.

  The three honest designs:

  design                      streams                 safe for                  
  stream everything           all output              low-stakes prose          
  stream prose, buffer JSON   the explanation only    most applications         
  buffer everything           nothing                 decisions, money, actions 

  The middle row is the one to reach for: a two-part response where
  the human-readable part streams and the machine-readable part does
  not. The user sees progress; your code still validates before
  anything is acted on.

  What you must NOT do is stream a tool call. By the time you have
  seen enough of it to know what it does, you have shown the user an
  action you may be about to refuse (M5-L08).

============================================================================
5. ACCOUNTING AND FAILURE, MID-STREAM
============================================================================
  A stream that dies at 60% has still consumed everything generated
  so far, and most providers report usage only in the final event.

  100,000 requests, 2% of streams break at 60%  [ILLUSTRATIVE]

                                        requests    $/month    counted?
  completed streams                       98,000       $118         yes
  broken streams (still billed)            2,000         $2          NO

  $2/month never reaches your usage metrics, because
  the usage event never arrived -- 1.5% of spend.
  At this failure rate that is small, and the SIZE is not the point:
  the error is one-directional. Your dashboard always under-reports,
  never over-reports, so the gap is invisible until the invoice.

    stream failure rate   uncounted $/mo   share of spend
                     2%               $2             1.5%
                    10%               $9             7.5%
                    25%              $22            19.6%
                    50%              $44            42.3%

  A 25% failure rate is not hypothetical for long streams over
  mobile connections, and there the gap is material.

  Fix: count what you RECEIVED, not what the provider told you at the
  end. Increment a counter per chunk, and reconcile against the final
  event when there is one (M5-L15).

  Retrying a broken stream is a second full charge. A stream that
  dies at 60% and is retried costs 1.6 responses for 1 result -- so
  the retry budget from M5-L07 applies here too, and the deadline
  bound matters more, because a stalled stream holds a connection.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: everything above except the illustrative prices and speeds.
  The decoding results are properties of Python's codecs; the JSON
  prefix results are properties of the format; the latency and cost
  tables are arithmetic on stated inputs.

  NOT SHOWN: server-sent-event framing, reconnection semantics and
  the exact shape of each provider's final usage event. Those differ
  by provider and change; check current documentation.

  The single most useful line in this lab is the incremental decoder.
  It is three lines, it is missing from a great deal of streaming
  code, and its absence shows up as mojibake in exactly the languages
  your English-language tests do not cover.

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Naive decode at 16-byte chunks | `UnicodeDecodeError` |
| Naive decode at 64-byte chunks | **OK — which is why it ships** |
| Incremental decoder, all chunk sizes | OK |
| First prefix at which the JSON parses | **100%** |
| "Invented category": bad field at / detectable at | char 1 (0%) / char 132 (100%) |
| Streaming benefit, 20-token response | 0.81 s → 0.45 s |
| Streaming benefit, 1,200-token response | **22.27 s → 0.45 s** |
| Generation vs reading speed | 55 vs 5 tok/s — **11× faster than read** |
| Uncounted spend at a 25% stream-failure rate | **19.6%** |

**Four things worth taking away.**

**1. The decoding bug passes at large chunk sizes.** That is not a lucky escape, it is the mechanism by
which it reaches production: ASCII fixtures, big chunks, green tests, and mojibake for users writing in
languages your tests do not contain. Three lines of incremental decoder fix it permanently.

**2. There is no prefix at which a JSON response can be validated.** The field that makes a response
invalid can be the very first thing in it and still not be actionable until the last. Streaming and
validating the same output are mutually exclusive.

**3. Streaming's value is entirely a function of length.** 0.36 s at 20 tokens; 21.8 s at 1,200. And past
a few hundred tokens the model already outruns the reader by 11×, so the constraint stops being
generation speed altogether.

**4. Your usage metrics under-report, always in the same direction.** Broken streams consume tokens and
never send the usage event. Small at a 2% failure rate, nearly 20% of spend at 25% — and the failure
rate rises exactly when everything else is going wrong.

**What transfers:** the codec behaviour, the JSON prefix result, and the shape of every table. **What
does not:** the specific latency and price figures, which are illustrative and which you should measure
for your own provider and region.

---

## 8. Common mistakes and troubleshooting

1. **`chunk.decode("utf-8")` per chunk.** Use an incremental decoder.
2. **Forgetting the final flush.** A truncated sequence is dropped silently instead of raising.
3. **Streaming a tool call.** You show an action you may refuse (M5-L08).
4. **Streaming a decision before validating it.** §6, exactly.
5. **Validating a partial response.** It cannot be done; a partial parser answers a different question.
6. **Streaming a 20-token response.** All the complexity, 0.36 s of benefit.
7. **Counting tokens only from the final usage event.** Broken streams vanish from your metrics.
8. **No idle timeout between chunks.** A stalled stream holds a connection indefinitely.
9. **Not cancelling upstream when the client disconnects.** You pay for output nobody receives.
10. **A buffering proxy in the path.** Your stream is silently un-streamed; test end to end.
11. **Trying to return HTTP 500 mid-stream.** The status was sent with the first chunk.
12. **Assuming `finish_reason` is available early.** It arrives last; do not act before it does.

| Symptom | Likely cause | Fix |
|---|---|---|
| Mojibake for non-English users | Per-chunk decode | Incremental decoder + final flush |
| Last character occasionally missing | No final flush | `decoder.decode(b"", final=True)` |
| Text appears all at once despite streaming | Buffering proxy | Disable buffering on the path |
| Users shown outcomes that are then refused | Decision streamed before validation | Buffer the decision; stream the explanation |
| Usage dashboard lower than the invoice | Broken streams uncounted | Count received chunks |
| Connections exhausted under load | No idle timeout | Timeout between chunks, not just total |
| Emoji or accents flicker while rendering | Grapheme split across chunks | Render on grapheme boundaries or debounce |

---

## 9. Security, privacy, reliability, cost

- **Security.** **Never stream a tool call or an unvalidated decision.** Output the user has seen is
  output you have effectively committed to.
- **Security.** Moderation on a complete response runs after the user has read it. Pre-display
  moderation requires buffering.
- **Reliability.** An idle timeout *between chunks* is a different bound from a total deadline. You need
  both (M2-L12).
- **Reliability.** Errors after the first chunk cannot be an HTTP status. Carry them inside the stream
  and handle them as a first-class client case.
- **Cost.** Count tokens as they arrive. Metrics based on the final usage event under-report, always in
  the same direction.
- **Cost.** Cancel upstream on client disconnect, or you pay for output nobody sees.
- **Cost.** Retrying a broken stream is a second full charge; bound it (M5-L07).
- **Privacy.** Streaming often means logging chunks. Chunk logs reassemble into the full response, and
  they are frequently retained at a lower sensitivity than the response itself (M2-L18).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Does streaming reduce total response time? Explain in one sentence.
2. Why does the naive decoding bug pass a test suite?
3. At what fraction of a JSON response can you first validate it?
4. Give two things that must never be streamed.
5. Why do usage metrics under-report when streams break?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the smallest chunk size at which naive decoding survives, and why.
2. Write a streaming client with an incremental decoder and a test containing `£`, `東` and an emoji.
3. Add an idle timeout between chunks and prove it fires with a stalled generator.
4. Implement received-token counting and compare it with a simulated final usage event.
5. Restructure a one-call streamed response into the two-part form from §6.

### Exercise 3 — Challenge (~50 min)

1. Build the §6 failure and the fix, and measure the TTFT difference the user actually experiences.
2. Implement grapheme-safe rendering and demonstrate it on a flag emoji split across chunks.
3. Design an in-stream error format and a client that distinguishes error, truncation and success —
   with tests for all three.
4. Measure the cost of not cancelling upstream on disconnect, for a traffic profile you state.
5. Write the decision record for "which parts of our response stream", covering moderation, tool calls,
   validation and cost.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l09).)*

**Q1.** Streaming a response:

- A. Reduces total generation time by overlapping work.
- B. Leaves total time unchanged and moves the wait from before the first word to between words.
- C. Reduces token cost by discarding unread output.
- D. Improves model accuracy by shortening the context.

**Q2.** Naive `chunk.decode("utf-8")` passed at 64-byte chunks and failed at 16. The significance is:

- A. 64 bytes is the correct chunk size to configure.
- B. The bug is harmless above a threshold.
- C. It passes with large chunks and ASCII fixtures, which is how it reaches production.
- D. Python's decoder is unreliable at small sizes.

**Q3.** The incremental decoder's final `decode(b"", final=True)` call:

- A. Is optional cleanup with no behavioural effect.
- B. Flushes held bytes and raises on a truncated sequence, instead of losing it silently.
- C. Resets the decoder for the next stream.
- D. Converts the accumulated text to bytes.

**Q4.** At what fraction of a streamed JSON response could it first be parsed?

- A. About 90%, once most fields are present.
- B. About 50%, with a partial parser.
- C. 100% — a JSON object is not valid until its closing brace.
- D. It varies with the field order.

**Q5.** A response's invalid field appeared at character 1 of 132. You could reject it at:

- A. Character 1, as soon as the field was seen.
- B. Roughly halfway, once the field's value was complete.
- C. Never; streamed responses cannot be validated at all.
- D. Character 132 — validity requires the complete object.

**Q6.** Streaming benefit at 20 tokens vs 1,200 tokens was:

- A. 0.36 s vs 21.82 s.
- B. Identical, since TTFT is constant.
- C. 4 s vs 240 s.
- D. Proportional to token count in both cases.

**Q7.** At 55 tok/s generation and 5 tok/s reading, past a few hundred tokens:

- A. The user is reading, not waiting, so faster generation buys nothing.
- B. The stream should be throttled to save cost.
- C. Streaming should be disabled.
- D. The model becomes the bottleneck.

**Q8.** Which must never be streamed?

- A. A long prose explanation.
- B. A summary of a retrieved document.
- C. A translation.
- D. A tool call.

**Q9.** A stream breaks at 60%. The tokens generated so far are:

- A. Not billed, since the response was incomplete.
- B. Billed, and usually absent from your metrics because the usage event never arrived.
- C. Refunded automatically by the provider.
- D. Billed and reported normally.

**Q10.** Your service returns HTTP 200, streams 70% of a response, then the model errors. You should:

- A. Return HTTP 500.
- B. Close the connection silently and let the client infer failure.
- C. Retry transparently and continue the same stream.
- D. Carry the error inside the stream and handle it client-side.

**Q11.** In §6, the assistant told the user about a £940 refund that was then refused. The root cause
was:

- A. The model hallucinating an amount.
- B. The refund cap being set too low.
- C. Prose asserting an outcome before the decision was validated and authorised.
- D. A streaming bug in the transport layer.

**Q12.** The recommended default for most applications is:

- A. Stream the prose explanation, buffer the machine-readable decision.
- B. Buffer everything; streaming is not worth the complexity.
- C. Stream everything; retract when validation fails.
- D. Stream only to authenticated users.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes enabling streaming
everywhere to fix complaints about slow responses. Most of your responses are 30–60 tokens. State what
you would tell them and what you would investigate instead.

---

## 12. Revision notes

- **Streaming does not make anything faster.** Total time is identical; the wait moves from before the
  first word to between words.
- **Its value is proportional to length**: 0.36 s at 20 tokens, **21.8 s at 1,200**. For short responses
  it is complexity with no benefit.
- **Past a few hundred tokens the model outruns the reader 11×.** Generation speed stops being the
  constraint; know which you are short of.
- **Decode incrementally.** `codecs.getincrementaldecoder("utf-8")()`, and **flush at the end**. The
  naive version passes at 64-byte chunks and fails at 16 — that is how it ships.
- **Correct decoding still splits graphemes.** Half a flag is a valid string.
- **There is no prefix at which JSON can be validated** — it first parses at **100%**. The invalidating
  field can be character 1 and still not be actionable until character 132.
- **Streaming buys perceived latency with the ability to withhold output.** That is the whole trade.
- **Never stream a tool call or an unvalidated decision.**
- **Default design: stream the prose, buffer the decision** — and generate the prose *from* the
  authorised outcome so it cannot contradict it.
- **Never stream a claim your system has not committed to.**
- **Broken streams are billed and uncounted** — 19.6% of spend at a 25% failure rate, and the error is
  always in the same direction. Count what you receive.
- **After the first chunk you cannot return an HTTP error.** Carry errors inside the stream.
- **Idle timeout between chunks** is a separate bound from the total deadline; you need both.

---

## 13. Completion checklist

- [ ] My streaming client uses an incremental decoder and flushes at the end.
- [ ] I have a test containing a multi-byte character.
- [ ] I never stream tool calls or unvalidated decisions.
- [ ] My prose is generated from the authorised outcome, not alongside it.
- [ ] I count tokens as chunks arrive.
- [ ] I have an idle timeout between chunks and cancel upstream on disconnect.
- [ ] My stream format can carry an error after a 200 has been sent.
- [ ] I can state the streaming benefit in seconds for my median response length.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Python docs — `codecs.getincrementaldecoder`.
  <https://docs.python.org/3/library/codecs.html#codecs.getincrementaldecoder> `[UNVERIFIED]`
- MDN — Using server-sent events.
  <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events>
  `[UNVERIFIED]`
- Unicode Standard Annex #29 — Text Segmentation (grapheme clusters).
  <https://unicode.org/reports/tr29/> `[UNVERIFIED]`
- Nielsen, J., *Response Times: The 3 Important Limits*.
  <https://www.nngroup.com/articles/response-times-3-important-limits/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L10 — Conversation State: what you store and what you resend](M5-L10-conversation-state.md)

You can deliver a response as it is produced. Next: what happens across turns — what the model
remembers (nothing), what you resend, and what that costs on every message.
