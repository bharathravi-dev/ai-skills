# M5-L06 — Structured Outputs and JSON Schemas

| | |
|---|---|
| **Lesson ID** | M5-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M2-L08](../module-02-python-foundations/M2-L08-pydantic.md), [M5-L01](M5-L01-prompt-anatomy.md), [M4-L15](../module-04-genai-llm-internals/M4-L15-stop-conditions.md) |

---

## 1. Learning objectives

1. **Distinguish** parsing from validation, and explain why neither substitutes for the other.
2. **Handle** the output shapes real models emit, without writing a repair that invents data.
3. **Configure** Pydantic so it reports the failures you need rather than silently absorbing them.
4. **Design** a schema that refuses wrong answers instead of asking for right ones.
5. **Cost** schema complexity in failed requests per hundred thousand.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Structured output** | A response required to conform to a machine-readable shape. |
| **Parsing** | Turning text into a data structure. Succeeds or raises. |
| **Validation** | Checking that a parsed structure means something permissible. |
| **Coercion** | Silently converting a value to the declared type — `"5"` to `5`. |
| **Strict mode** | Pydantic configuration that rejects rather than coerces. |
| **`extra="forbid"`** | Rejecting fields the schema did not declare. |
| **Constrained decoding** | The provider restricting token choice so output must match a grammar. |
| **JSON mode** | A provider setting that makes output valid JSON — not necessarily *your* JSON. |
| **Repair** | Editing malformed output until it parses. Frequently a mistake. |
| **`finish_reason`** | Why generation stopped — the field that says whether output is complete (M4-L15). |

---

## 3. Plain-language explanation

### 3.1 Two different questions

> **Parsing:** is this text a data structure?
> **Validation:** is this data structure an acceptable answer?

They fail differently and they are fixed differently, and conflating them produces both of this
lesson's expensive bugs:

- Text that will not parse, "repaired" until it does — and now means something else (§5.2).
- Text that parses perfectly and authorises a refund of £1,000,000 (§5.4).

**A JSON parser has no opinion about whether £1,000,000 is a sensible refund.** Something else has to,
and that something is a schema, not a sentence in your prompt.

### 3.2 Why "return JSON" is not enough

The model is producing tokens that look like the JSON in its training data (M4-L12). Most of that
training data is JSON *embedded in prose* — in a code fence, after a sentence like "Here's the JSON you
asked for", with a trailing comma because a human wrote it.

So the model does what it learned. §7.3 runs the stdlib parser over fourteen outputs models actually
emit: **6 of 14 parse**. The failures are a code fence and a polite preamble — the two most natural
things a chat model does.

**This is not the model disobeying.** It is the model doing precisely what "return JSON" describes,
inside a message.

### 3.3 The three layers, in order of strength

| Layer | What it does | Strength |
|---|---|---|
| **Instruction** — "return JSON" | Asks | Suggestion |
| **JSON mode** — provider setting | Guarantees valid JSON | Structural, but not *your* shape |
| **Constrained decoding / tool schema** | Restricts tokens to your grammar | Strongest available |
| **Validation** — Pydantic | Rejects unacceptable *meanings* | **Required regardless of the above** |

**The last row is not optional even when the row above it is perfect.** A grammar guarantees shape. It
cannot know that this account is not entitled to a refund.

---

## 4. Analogy

A web form versus a note left on a desk.

The note says "please include your date of birth in DD/MM/YYYY". Most people will. Some will write
`3rd March`, some will use MM/DD, one will attach a photo of their passport.

The form has a date input. It will not submit until there is a date, and the value that arrives at your
server is a date. **The constraint moved from the request to the mechanism.**

### Where the analogy breaks

- **A form validates on the client and you re-validate on the server**, because the client is
  untrusted. A model's output is exactly that: an untrusted client. **Validate every time, at the
  boundary, in your own code** (M2-L08).
- **A form field can be made impossible to submit wrongly.** Constrained decoding is close, but the
  *values* inside a well-formed shape are still generated text — a valid `refund` field can hold any
  number the grammar allows.
- **Nobody has to pay per character for a form.** Every field in your schema is tokens on every
  request, and §7.3 shows fields also cost *compliance*.

---

## 5. Detailed technical explanation

### 5.1 What a real model's output looks like

§7.3 runs `json.loads` over fourteen realistic outputs. **6 parse. 8 do not.**

| Output | `json.loads` |
|---|---|
| Clean object | parses |
| In a code fence | **fails** |
| After "Sure! Here is the JSON:" | **fails** |
| Trailing comma | **fails** |
| Single quotes | **fails** |
| Truncated | **fails** |
| `NaN` for a number | **parses** |
| `"42.5"` instead of `42.5` | **parses** |
| Two objects in one response | **fails** |

**Note the `NaN` row.** Python's `json` accepts `NaN` and `Infinity` by default, which are *not* valid
JSON. It parses here and detonates in whatever consumes it — a database write, an arithmetic operation,
a comparison that is false against everything. Pass `parse_constant` to reject them:

```python
json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(
    ValueError(f"invalid JSON constant: {c}")))
```

### 5.2 Repair: the strategies, and the one that is dangerous

§7.3 adds one repair at a time and counts not just what parses but **what parses into the wrong
thing**:

| Strategy | Parsed | Correct | **Wrong** |
|---|---|---|---|
| `json.loads` only | 6 | 2 | 4 |
| + strip code fences | 8 | 4 | 4 |
| + take the first `{...}` | 9 | 5 | 4 |
| + **balance braces** | 11 | 5 | **6** |

**Read the last row.** Brace-balancing raised the parse count from 9 to 11 and the correct count not at
all. Both new successes were wrong:

```
raw     : {"category":"billing","refund":42.5,"urg
repaired: {"category":"billing","refund":42.5}
parsed  : {'category': 'billing', 'refund': 42.5}
MISSING KEY: urgent
```

**The truncated response did not fail. It succeeded, as a different object.** Nothing downstream can
tell that `urgent` was cut off mid-word rather than deliberately omitted.

In M4-L15 this same pattern produced `{"action": "delete_records"}` with the filter truncated away — a
repair that widened a delete to everything.

> **Never repair a truncated response.** Check `finish_reason` first (M4-L15). If it is not a natural
> stop, the output is not data, it is debris.

The two repairs worth having — stripping fences and taking the first object — are **lossless
extraction**: they discard text that was never part of the JSON. Brace-balancing is different in kind,
because it *adds* structure the model did not emit.

```python
def parse_model_json(text: str, finish_reason: str) -> dict:
    if finish_reason != "stop":                    # M4-L15
        raise IncompleteResponse(finish_reason)
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    body = m.group(1) if m else text
    i, j = body.find("{"), body.rfind("}")
    if i == -1 or j <= i:
        raise NoJSONFound(text[:200])
    return json.loads(body[i:j + 1], parse_constant=_reject)
```

**No brace balancing, no quote fixing, no comma stripping.** Those failures are a signal that the
prompt or the model needs fixing — silencing them removes your only evidence.

### 5.3 What Pydantic accepts when you do not ask it not to

Same JSON, two models. **Lax is the default:**

| Output | Lax | Strict |
|---|---|---|
| Clean | `billing/42.5/False` | `billing/42.5/False` |
| `NaN` for refund | **`billing/nan/False`** | rejected |
| `"42.5"`, `"false"` | **`billing/42.5/False`** | rejected |
| Extra field `approved_by` | **accepted, field passed through** | rejected |
| Trailing comma | rejected | rejected |
| Wrong enum value | rejected | rejected |

Three rows where **lax accepted and strict rejected**, and each is a distinct hazard:

**`NaN` reached a float field.** Not caught, because `float('nan')` is a float. It will now compare
false against every threshold you test it with, silently.

**`"42.5"` became `42.5`.** This is usually what you wanted — and it means your validator **cannot tell
you that the model stopped emitting numbers as numbers**. That is exactly the signal you need after a
model or version change (M5-L17). Coercion converts a monitorable event into a silent one.

**`approved_by` passed straight through.** Without `extra="forbid"`, a field you never declared arrives
in your object, where something downstream may read it. This is mass assignment (M2-L15) arriving via
the model instead of the request body.

```python
class Decision(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    category: Category                       # an Enum, not a str
    refund: Decimal = Field(ge=0, le=500)    # Decimal for money (M2-L02)
    urgent: bool
    reason: str = Field(min_length=1, max_length=400)
```

**A recommendation and its cost.** Strict mode will reject outputs a lax model would have accepted, so
your error rate goes *up* the day you enable it. That is the point: those errors were always happening,
and you were absorbing them. Turn it on with a metric in place, and expect to tune the schema.

Where you genuinely want a coercion, make it explicit and visible — a validator that converts *and
records that it converted* — rather than a global setting that converts and says nothing.

### 5.4 What a schema catches that no instruction can

Four outputs that are **valid JSON and wrong**:

| Output | Valid JSON | Lax model | Strict model |
|---|---|---|---|
| `refund: 1000000` | yes | **accepted** | rejected |
| `refund: -50` | yes | **accepted** | rejected |
| `category: "escalation"` | yes | rejected (enum) | rejected |
| `approved: true` | yes | **accepted** | rejected |

Parsing cannot help with any of them. What rejects them is three lines of schema: `ge`/`le` bounds, an
`Enum`, and `extra="forbid"`.

> **An instruction asks. A schema refuses. Only one of them is a control.**

This is the same principle as M2-L16's parameterised query and M5-L05's nonce: **put the constraint in
the mechanism, not in the request.** And note where it puts the injection defence from M5-L05 — an
injected instruction that persuades the model to approve a £1M refund produces output that fails
`le=500`, **regardless of why the model produced it.** Output validation is the control that does not
care about the attacker's cleverness.

### 5.5 Schema complexity has a price

`[MOCK — rates specified, shape only]`

| Schema | Fields | Depth | Compliance | Failures per 100k |
|---|---|---|---|---|
| 3 flat fields, 1 enum | 3 | 1 | 95.9% | 4,139 |
| 8 flat fields | 8 | 1 | 89.1% | 10,899 |
| 8 fields, 1 nested object | 8 | 2 | 80.4% | 19,599 |
| 15 fields, 3 levels | 15 | 3 | 66.1% | 33,900 |
| 25 fields, 4 levels | 25 | 4 | 51.0% | 48,980 |

**Design against the right-hand column.** Even the simplest schema is 4,139 failures per 100,000 — a
retry budget, an error rate and a support queue, not a rounding error.

**Flatten before you deepen.** Two calls with flat schemas beat one call with a nested one: each is
independently validated, independently retried, and independently attributable when it fails.

### 5.6 Provider features and what they actually promise

| Feature | Promises | Does not promise |
|---|---|---|
| "JSON mode" | Output is valid JSON | That it matches *your* schema |
| Constrained decoding / structured outputs | Output matches your schema's shape | That the values are correct or permitted |
| Tool/function schemas | Arguments match the declared shape | That the call should be made (M5-L08) |

`[UNVERIFIED — availability, naming and exact guarantees differ by provider and change. Check the
current documentation for the model you use, and test it.]`

**Even with a perfect grammar guarantee, §5.4 is unchanged.** A schema-conforming object can still hold
a refund of one million. **Validate the values, always, in your code.**

### 5.7 Assumptions and limitations

- §7.3's sections 1–4 are real: stdlib `json` and pydantic 2.13.5. They are reproducible facts about
  the libraries, not simulations.
- The fourteen failure modes are representative, not exhaustive, and not weighted by real frequency.
  Measure the distribution in your own logs.
- §7.3's section 5 rates are specified. Only the shape transfers.
- Coercion behaviour is version-specific. Pin pydantic and re-check on upgrade.

---

## 6. Worked example — the refund extractor that authorised £1,000,000

**The system.** Support emails are read by a model; the output drives an automated refund.

**The prompt.** *"Read the email and return JSON with the category, the refund amount, and whether it's
urgent."*

**The code.**

```python
data = json.loads(response.text.strip("`").replace("json", ""))
issue_refund(data["refund"], data["category"])
```

**Four defects, three of which are invisible in testing:**

| # | Defect | When it bites |
|---|---|---|
| 1 | `strip("`")` and `replace("json", "")` | The moment an email contains the word "json" — it is removed from the *content* |
| 2 | No `finish_reason` check | The response is truncated; §5.2's repair invents a complete object |
| 3 | No validation of the parsed data | Any number reaches `issue_refund` |
| 4 | No bound on the amount | £1,000,000 is as acceptable as £10 |

**The failure.** A customer's email includes the sentence *"I want a full refund of the 1000000 KRW I
was charged"* — a legitimate amount in a currency the system does not handle. The model extracts
`1000000`. It parses. It is issued.

**Nothing in this chain was a model error.** The model extracted the number in the email. Every other
layer had no opinion.

### The fix

```python
class Category(str, Enum):
    billing = "billing"
    technical = "technical"
    account = "account"
    other = "other"


class RefundDecision(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    category: Category
    refund_minor_units: int = Field(ge=0, le=50_000)   # £500 in pence
    currency: Literal["GBP"]
    urgent: bool
    evidence: str = Field(min_length=10, max_length=500)


def decide(response) -> RefundDecision:
    if response.finish_reason != "stop":
        raise IncompleteResponse(response.finish_reason)
    return RefundDecision.model_validate_json(extract_json(response.text))
```

| Change | What it stops |
|---|---|
| `Decimal`/minor units, never `float` | Floating-point money (M2-L02) |
| `le=50_000` | The £1M refund, whatever produced it |
| `Literal["GBP"]` | The KRW confusion — the currency must be stated and must be one you handle |
| `strict=True` | `"1000000"` as a string passing as a number |
| `extra="forbid"` | An invented `approved: true` |
| `evidence` required | The model must quote the email — a human can check the decision |
| `finish_reason` check | A truncated response repaired into a confident one |

**And the control that does not appear in the schema at all:** refunds above a threshold go to a person.
The schema bounds what the model can *say*; the approval bounds what the system can *do*. §5.4 gets you
the first. Only the second means a bad output cannot become a bad outcome.

---

## 7. Practical activity

**File:** [`labs/m5/l06_structured_output.py`](../../labs/m5/l06_structured_output.py)

**No API key, no network, no cost.**

### 7.1 Run it

```bash
source .venv/bin/activate
python labs/m5/l06_structured_output.py
```

**Sections 1–4 use no model.** They run the real `json` module and real pydantic against a catalogue of
malformed outputs. Those rows are facts about the libraries you will ship.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.12.3, pydantic 2.13.5, NumPy 2.5.3.

```text
============================================================================
1. WHAT PLAIN json.loads DOES WITH REAL MODEL OUTPUT
============================================================================
  No model, no mock: the stdlib json module against 14 outputs of the
  kind models actually emit.

  raw output              json.loads                                       error
  clean                       parses                                            
  fenced                       FAILS                             Expecting value
  preamble                     FAILS                             Expecting value
  preamble+fence               FAILS                             Expecting value
  trailing comma               FAILS  Expecting property name enclosed in double
  single quotes                FAILS  Expecting property name enclosed in double
  truncated                    FAILS             Unterminated string starting at
  truncated deep               FAILS                             Expecting value
  nan                         parses                                            
  string numbers              parses                                            
  extra field                 parses                                            
  wrong enum                  parses                                            
  null for number             parses                                            
  two objects                  FAILS                                  Extra data

  6/14 parse. The failures are not exotic -- a code
  fence and a polite preamble are the two most common things a chat
  model does, and neither is an error from its point of view.

  Note 'nan' PARSED. Python's json accepts NaN and Infinity by default,
  which is not valid JSON. It will parse here and explode in whatever
  consumes it. Pass parse_constant to reject it.

============================================================================
2. REPAIR STRATEGIES -- AND THE ONES THAT SUCCEED DANGEROUSLY
============================================================================
  Each stage adds one repair. 'correct' means the parsed object equals
  what the model meant. 'WRONG' means it parsed into something else.

  strategy                 parsed   correct   WRONG               what silently changed
  json.loads only               6         2       4                  nan,string numbers
  + strip fences                8         4       4                  nan,string numbers
  + first {...}                 9         5       4                  nan,string numbers
  + balance braces             11         5       6            truncated,truncated deep

  Now look at what brace-balancing actually produced:

    truncated:
      raw    : {"category":"billing","refund":42.5,"urg
      repaired: {"category":"billing","refund":42.5}
      parsed  : {'category': 'billing', 'refund': 42.5}
      MISSING KEYS: ['urgent']
    truncated deep:
      raw    : {"category":"billing","refund":42.5,"filters":{"account":"A-1","region":
      repaired: {"category":"billing","refund":42.5,"filters":{"account":"A-1"}}
      parsed  : {'category': 'billing', 'refund': 42.5, 'filters': {'account': 'A-1'}}
      MISSING KEYS: ['urgent']

  This is the failure that matters. The truncated output did not
  fail -- it succeeded, as a DIFFERENT object. A repair that produces
  valid JSON from an incomplete response has invented a complete
  answer out of a partial one, and nothing downstream can tell.

  If the missing key had been a filter on a delete, the repair would
  have widened the operation to everything (M4-L15).

  Rule: NEVER repair a truncated response. Check finish_reason first;
  if it is not a natural stop, the response is not data, it is debris.

============================================================================
3. VALIDATION: WHAT PYDANTIC ACCEPTS WHEN YOU DO NOT ASK IT NOT TO
============================================================================
  Same JSON, two models. 'lax' is what you get by default.

  raw output                                   lax                      strict
  clean                         billing/42.5/False          billing/42.5/False
  fenced                        billing/42.5/False          billing/42.5/False
  preamble                      billing/42.5/False          billing/42.5/False
  preamble+fence                billing/42.5/False          billing/42.5/False
  trailing comma                      rejected (1)                rejected (1)
  single quotes                       rejected (1)                rejected (1)
  truncated                           rejected (1)                rejected (1)
  truncated deep                      rejected (1)                rejected (1)
  nan                            billing/nan/False                rejected (1)
  string numbers                billing/42.5/False                rejected (2)
  extra field                   billing/42.5/False                rejected (1)
  wrong enum                          rejected (1)                rejected (1)
  null for number                     rejected (1)                rejected (1)
  two objects                         rejected (1)                rejected (1)

  Rows where lax ACCEPTED and strict rejected: nan, string numbers, extra field

  Read the 'string numbers' row. Lax turned "42.5" into 42.5 and
  "false" into False, and reported success. That is usually what you
  wanted -- and it means your validator cannot tell you that the model
  stopped emitting numbers as numbers, which is exactly the signal
  you need after a model upgrade (M5-L17).

  Read the 'extra field' row. Without extra='forbid', approved_by
  passes straight through your validator and into your code, where
  something may well read it (M2-L15, mass assignment).

============================================================================
4. WHAT A SCHEMA CATCHES THAT AN INSTRUCTION CANNOT
============================================================================
  Four outputs that are valid JSON and wrong. Which layer stops them?

  output                valid JSON                 lax model    strict model
  refund of 1e6                yes   billing/1000000.0/False    rejected (1)
  negative refund              yes       billing/-50.0/False    rejected (1)
  invented label               yes              rejected (1)    rejected (1)
  extra authority              yes        billing/10.0/False    rejected (1)

  Every one of these is well-formed JSON. Parsing cannot help. The
  bounds (ge/le), the enum and extra='forbid' are what reject them,
  and each one is a line of schema rather than a sentence of prompt.

  An instruction asks. A schema refuses. Only one of them is a control.

============================================================================
5. SCHEMA COMPLEXITY vs COMPLIANCE  [MOCK]
============================================================================
  The one thing real libraries cannot show: whether the MODEL manages
  to produce the shape. Rates below are specified, not measured.

  schema                              fields  depth   compliance   per 100k requests
  3 flat fields, 1 enum                    3      1        95.9%               4,139
  8 flat fields, 2 enums                   8      1        89.1%              10,899
  8 fields, 1 nested object                8      2        80.4%              19,599
  15 fields, 3 levels deep                15      3        66.1%              33,900
  25 fields, 4 levels deep                25      4        51.0%              48,980

  The right-hand column is the one to design against. The simplest
  schema here is 95.9% -- which is 4,139 failed requests per 100,000, a retry
  budget and a support queue, not a rounding error.

  The largest schema is 51.0%. Between the two rows nothing
  changed about the task or the model: only the shape you asked for.

  Flatten before you deepen: two calls with flat schemas beat one call
  with a nested one, and each can be validated and retried alone.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL (sections 1-4): the stdlib json module and pydantic 2.13.5 on
  this machine. Those rows are reproducible facts about the libraries
  you will actually ship, including the coercion behaviour -- which is
  the finding most likely to surprise you in production.

  MOCK (section 5): compliance rates are specified. Only the shape
  transfers -- more fields and more depth cost compliance.

  NOT SHOWN: constrained decoding. Where a provider can guarantee the
  grammar, section 5's problem largely disappears and sections 1-4 do
  NOT -- a guaranteed-valid JSON object can still carry a refund of
  1,000,000. Validation is not parsing, and neither is a substitute
  for the other.

Done.
```

### 7.3 What it measured

| Finding | Number |
|---|---|
| Realistic model outputs that `json.loads` accepts | **6 / 14** |
| `NaN` accepted by stdlib `json` | yes — not valid JSON |
| Brace-balancing: parses gained | 9 → 11 |
| Brace-balancing: **correct** results gained | **5 → 5** |
| Brace-balancing: wrong results | 4 → **6** |
| Rows where lax pydantic accepted and strict rejected | `NaN`, string numbers, extra field |
| Valid-JSON-but-wrong outputs stopped by strict schema | **4 / 4** |
| Compliance, 3 flat fields vs 25 fields at depth 4 `[MOCK]` | 95.9% vs 51.0% |

**Four things worth taking away.**

**1. "Return JSON" gets you a parse rate of 6 in 14.** Not because the model disobeyed, but because it
produced JSON the way its training data contains JSON: fenced, prefaced, and explained.

**2. The most popular repair adds no correct answers and two wrong ones.** Brace-balancing turned two
truncated responses into confident, complete-looking objects with a key missing. **Check
`finish_reason` and refuse.**

**3. Lax validation converts monitorable failures into silent ones.** `"42.5"` becoming `42.5` is
convenient right up to the model upgrade that changes number formatting — and then you have no signal,
because your validator absorbed it.

**4. Every valid-JSON-but-wrong output was stopped by three lines of schema.** Bounds, an enum, and
`extra="forbid"` rejected a £1M refund, a negative refund, an invented category and an invented
authority field. **An instruction asks; a schema refuses.**

**What transfers:** sections 1–4 completely — they are library behaviour, and the lab is in the
repository. **What does not:** section 5's compliance rates, and the frequency distribution of the
fourteen failure modes, which will differ in your traffic.

---

## 8. Common mistakes and troubleshooting

1. **Parsing without validating.** `json.loads` has no opinion about £1,000,000.
2. **Repairing a truncated response.** Check `finish_reason` first (M4-L15).
3. **Brace-balancing.** It adds structure the model never emitted.
4. **`.strip("`").replace("json","")`.** Removes the word "json" from the *content* too.
5. **Leaving pydantic in lax mode.** `NaN`, string numbers and extra fields all pass.
6. **Omitting `extra="forbid"`.** Mass assignment, arriving via the model.
7. **`str` where an `Enum` belongs.** A free string cannot be wrong, which means it cannot be checked.
8. **`float` for money.** Use `Decimal` or integer minor units (M2-L02).
9. **Deep nested schemas.** Compliance falls with depth; flatten and split the call.
10. **Trusting JSON mode to enforce your schema.** It enforces JSON, not your shape.
11. **No bounds on numbers.** The one field that would have stopped §6.
12. **Retrying a validation failure with the same prompt.** Fix the schema or the prompt (M5-L07).

| Symptom | Likely cause | Fix |
|---|---|---|
| `Expecting value: line 1 column 1` | Code fence or preamble | Extract the first `{...}` |
| Intermittent `KeyError` downstream | Truncation repaired into valid JSON | Check `finish_reason`, refuse |
| Numbers arrive as strings sometimes | Lax coercion hiding a format change | `strict=True`, alert on the change |
| A field you never declared in your object | No `extra="forbid"` | Add it |
| Comparisons all false for one record | `NaN` in a float field | `parse_constant`; strict mode |
| Failure rate rose after adding fields | Schema complexity | Flatten; split into two calls |
| Works in testing, fails in production | Real inputs are longer and odder | Build the catalogue from real logs |

---

## 9. Security, privacy, reliability, cost

- **Security.** **Output validation is the injection control that does not depend on the attacker's
  cleverness** (M5-L05 §5.5). A £1M refund fails `le=500` no matter how persuasive the injected text
  was.
- **Security.** `extra="forbid"` blocks a model-supplied `approved: true` reaching code that reads it —
  mass assignment via the model (M2-L15).
- **Reliability.** Never repair truncation. A repaired object is a confident wrong answer, which is
  worse than an error (M2-L10).
- **Reliability.** Pin pydantic. Coercion behaviour is version-specific, and an upgrade can change what
  your validator silently accepts.
- **Privacy.** Validation errors are logged, and the invalid value is usually in the message. **A
  `ValidationError` on a field containing personal data puts that data in your logs** (M2-L18). Log the
  field name and the error type, not the value.
- **Cost.** Every schema field is tokens on every request, and §7.3 shows fields also cost compliance —
  so an unused field is billed twice.
- **Cost.** A validation-failure retry loop is a cost multiplier. Bound retries by count *and* budget
  (M2-L14, M5-L07).

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. State the difference between parsing and validation in one sentence each.
2. Give three outputs that parse successfully and are still wrong.
3. Why must `finish_reason` be checked before parsing?
4. What does `extra="forbid"` prevent, and what is the equivalent HTTP-layer bug?
5. Why is `Enum` better than `str` for a category field?

### Exercise 2 — Intermediate (~45 min)

1. Run the lab. Report which two outputs brace-balancing turned into wrong objects, and what was lost.
2. Add three failure modes of your own to `RAW` — a Markdown table, an object wrapped in `{"result":
   ...}`, and a response in another language — and re-run sections 1–3.
3. Write the `Decision` model from §5.3 and prove with tests that it rejects each output in §5.4.
4. Enable `strict=True` on an existing model in your own code and report which previously-passing
   inputs now fail.
5. Compute the monthly cost of a 25-field schema at 100,000 requests, at a token price you state,
   including the retry cost implied by §5.5's compliance rate.

### Exercise 3 — Challenge (~60 min)

1. Build the catalogue as a `pytest` fixture and write a parser that scores at least 12/14 **without**
   inventing data. State which two you refuse and why refusing is correct.
2. Implement "coerce but record": a validator that accepts `"42.5"`, converts it, and emits a metric —
   so the convenience is kept and the signal is not lost.
3. Design a schema for the §6 refund task where the *most damaging possible* well-formed output is
   harmless. State what remains unprotected and what non-schema control covers it.
4. Measure how a `ValidationError` message treats a field containing an email address, and write the
   logging code that keeps it out of your logs.
5. Take a nested three-level schema from your own work, split it into two flat calls, and compare
   token cost, latency and failure attribution.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l06).)*

**Q1.** Of fourteen realistic model outputs, how many did plain `json.loads` accept?

- A. 13 — almost all, since models are reliable at JSON.
- B. 6.
- C. 1 — only the perfectly clean one.
- D. 14, since Python's parser is lenient.

**Q2.** Adding brace-balancing to a repair pipeline raised parses from 9 to 11. The correct count:

- A. Stayed at 5 — both new successes were wrong.
- B. Rose from 5 to 6.
- C. Rose from 5 to 7, matching the parses.
- D. Fell, because balancing corrupts valid input.

**Q3.** Before parsing a model's JSON you must check:

- A. That the response length is under the context limit.
- B. That the temperature was set to zero.
- C. That the model version matches the one you tested.
- D. `finish_reason`, because a truncated response must be refused, not repaired.

**Q4.** Default (lax) Pydantic given `{"refund": "42.5"}` for a `float` field will:

- A. Reject it, since a string is not a float.
- B. Coerce it to `42.5` and report success.
- C. Coerce it and emit a warning.
- D. Store the string unchanged.

**Q5.** Why is that coercion a problem even though the value is right?

- A. It converts a monitorable change in model behaviour into a silent one.
- B. It loses precision on large numbers.
- C. It is slow at high request volumes.
- D. It is deprecated in Pydantic 2.

**Q6.** `json.loads('{"refund": NaN}')` in Python:

- A. Raises, since `NaN` is not valid JSON.
- B. Returns `None` for that field.
- C. Returns the string `"NaN"`.
- D. Succeeds, producing a float `nan` that compares false against everything.

**Q7.** A model returns `{"category":"billing","refund":1000000}`. What rejects it?

- A. `json.loads`, since the value is implausible.
- B. A bound such as `Field(le=500)` on the schema.
- C. JSON mode enabled at the provider.
- D. An instruction in the prompt to keep refunds reasonable.

**Q8.** `extra="forbid"` protects against:

- A. Fields being omitted from the response.
- B. Numbers arriving as strings.
- C. Responses exceeding the token limit.
- D. A model-supplied field your code might read — mass assignment via the model.

**Q9.** Provider "JSON mode" guarantees:

- A. That the output matches your schema exactly.
- B. That values are within the ranges you declared.
- C. That the output is valid JSON — not that it is your shape.
- D. That no extra fields appear.

**Q10.** As a schema grows from 3 flat fields to 25 fields at four levels, the lab's mock compliance:

- A. Is unaffected; shape does not influence compliance.
- B. Falls from about 96% to about 51%.
- C. Falls slightly, from 96% to about 90%.
- D. Improves, because more structure guides the model.

**Q11.** Which is the strongest reason output validation is a security control?

- A. It rejects an impermissible action regardless of what persuaded the model to propose it.
- B. It prevents the model from seeing untrusted input.
- C. It stops prompt injection from reaching the model.
- D. It encrypts the response in transit.

**Q12.** A `ValidationError` on a field containing a customer's email address is a risk because:

- A. Pydantic transmits errors to the provider.
- B. Validation errors cannot be caught.
- C. The error message usually contains the invalid value, which then reaches your logs.
- D. Email addresses cannot be validated by a schema.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague's extraction service parses fine in
testing but corrupts one field in production about 2% of the time, always on long documents. Give your
first hypothesis, how you would confirm it in one query against existing logs, and the fix.

---

## 12. Revision notes

- **Parsing and validation are different questions.** `json.loads` has no opinion about £1,000,000.
- **"Return JSON" yields 6/14.** Fences and preambles are what models learned, not disobedience.
- **Two safe repairs:** strip fences, take the first `{...}`. Both are lossless extraction.
- **Never balance braces.** In the lab it added **zero** correct results and **two** wrong ones — a
  truncated response reborn as a confident complete object with a key missing.
- **Check `finish_reason` before parsing.** Not a natural stop means debris, not data (M4-L15).
- **`json` accepts `NaN`.** Pass `parse_constant` and reject it.
- **Lax pydantic accepted `NaN`, `"42.5"` and an undeclared field.** Use `strict=True` and
  `extra="forbid"`, and expect your error rate to rise — those failures were always there.
- **Coercion trades a signal for a convenience.** After a model change it is the signal you want.
- **Enum, bounds and `extra="forbid"` rejected all four valid-JSON-but-wrong outputs.** Three lines of
  schema, no prompt engineering.
- **An instruction asks; a schema refuses.** Same principle as parameterised SQL (M2-L16) and the
  nonce (M5-L05): the constraint belongs in the mechanism.
- **Output validation is the injection control that ignores the attacker's cleverness.**
- **Complexity costs compliance:** 95.9% at 3 flat fields, 51.0% at 25 fields four levels deep
  `[MOCK]`. **Flatten before you deepen.**
- **JSON mode guarantees JSON, not your JSON.** Validate anyway, always.
- **Money is `Decimal` or integer minor units**, never `float` (M2-L02).

---

## 13. Completion checklist

- [ ] I check `finish_reason` before I parse.
- [ ] My repair pipeline extracts and never invents.
- [ ] My models use `strict=True` and `extra="forbid"`.
- [ ] Every numeric field has a bound and every category field is an Enum.
- [ ] I know that JSON mode does not enforce my schema.
- [ ] My validation errors do not log field values.
- [ ] I can state the failures-per-100k implied by my schema's compliance rate.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Pydantic docs — Strict mode. <https://docs.pydantic.dev/latest/concepts/strict_mode/> `[UNVERIFIED]`
- Pydantic docs — Conversion table.
  <https://docs.pydantic.dev/latest/concepts/conversion_table/> `[UNVERIFIED]`
- Python docs — `json`. <https://docs.python.org/3/library/json.html> `[UNVERIFIED]`
- JSON Schema specification. <https://json-schema.org/> `[UNVERIFIED]`
- Willard & Louf (2023), *Efficient Guided Generation for LLMs*.
  <https://arxiv.org/abs/2307.09702> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L07 — Output Validation and Repair Loops](M5-L07-validation-repair.md)

You can define the shape you want and reject what does not fit. Next: what to do with the rejects —
when to retry, how to ask differently, and when a retry is the wrong answer entirely.
