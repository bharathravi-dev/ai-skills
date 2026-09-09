# M2-L08 — Type Hints and Pydantic v2 Validation

| | |
|---|---|
| **Lesson ID** | M2-L08 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L07](M2-L07-classes-dataclasses.md) |

---

> **This is the most important lesson in Module 2 for the rest of the course.** Pydantic is how you
> will validate LLM output in M5-L06/L07, define tool schemas in M5-L08 and M8-L05, describe MCP
> tool inputs in M9-L07, and specify FastAPI request bodies in M2-L15. Everything downstream assumes
> you are fluent here.

---

## 1. Learning objectives

1. **Write** type hints for common shapes, including optionals, unions, generics and callables.
2. **Explain** why hints are not enforced at runtime, and what tooling makes them useful.
3. **Define** Pydantic v2 models with field constraints and validators.
4. **Parse and validate** untrusted JSON, and **read** a `ValidationError` precisely.
5. **Choose** between coercion and strict mode, and **explain** the risk of each.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Type hint** | An annotation describing the expected type. Not enforced at runtime. |
| **Static type checker** | A tool (mypy, pyright) that checks hints without running the code. |
| **`Optional[X]` / `X \| None`** | May be `X` or `None`. |
| **Union** | `int \| str` — one of several types. |
| **Generic** | A type parameterised by another: `list[str]`, `dict[str, int]`. |
| **`Literal`** | A value restricted to specific constants. |
| **`Any`** | Opts out of checking. Use sparingly. |
| **Pydantic** | A library that validates and parses data at runtime using type hints. |
| **`BaseModel`** | The Pydantic class you subclass to define a schema. |
| **`Field`** | Declares constraints and metadata for one field. |
| **`ValidationError`** | Raised when input does not match the model. Contains structured details. |
| **Coercion** | Converting a compatible value: `"5"` → `5`. |
| **Strict mode** | Disables coercion; types must match exactly. |
| **JSON Schema** | A standard description of a JSON structure. Pydantic generates it. |
| **Validator** | A function running custom checks during validation. |

---

## 3. Plain-language explanation

You have now hit the same wall twice. Annotations describe intent; **nothing checks them at runtime**:

```python
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")      # runs fine, returns "helloworld"
```

Python does not check. It never has. Hints exist for **humans and tools**: editors, and static
checkers like mypy that read your code without running it.

That is fine for code you control. It is not fine for data arriving from **outside** your program.
A JSON body, a config file, an environment variable, an LLM's response — none of these can be trusted
to have the shape you expect.

**Pydantic closes that gap.** It takes the same type hints and enforces them at runtime, with clear
errors:

```python
from pydantic import BaseModel

class Ticket(BaseModel):
    ticket_id: str
    priority: int

Ticket(ticket_id="T-1", priority="high")
# ValidationError: 1 validation error for Ticket
# priority
#   Input should be a valid integer, unable to parse string as an integer
#     [type=int_parsing, input_value='high', input_type=str]
```

Compare that with M2-L07's `TypeError: bad operand type for unary -: 'str'` from a sort function
three modules away. The Pydantic error names the model, the field, the problem, the received value
and its type — **at the boundary, before the bad value can spread.**

That difference — *fail at the boundary with a precise message, rather than deep inside with a vague
one* — is the entire argument for this lesson.

### If you know TypeScript

| TypeScript | Python |
|---|---|
| `string`, `number`, `boolean` | `str`, `int`/`float`, `bool` |
| `string[]` | `list[str]` |
| `Record<string, number>` | `dict[str, int]` |
| `string \| null` | `str \| None` |
| `"a" \| "b"` | `Literal["a", "b"]` |
| `any` | `Any` |
| `interface` | `Protocol` (M2-L07) or a `BaseModel` |
| Types erased at compile time | Hints erased at runtime |
| **Zod** for runtime validation | **Pydantic** for runtime validation |

The last row is the key mapping. TypeScript types vanish at runtime and you reach for Zod; Python
hints are inert at runtime and you reach for Pydantic. Same problem, same shape of solution.

---

## 4. Analogy

**Type hints are the label on a box; Pydantic is the person who opens it and checks.**

A label saying "12 red mugs" is useful — until someone ships you 11 blue plates. The label was never
a guarantee. Pydantic opens every incoming box at the loading bay and rejects mismatches before they
reach the warehouse.

### Where the analogy breaks

1. **Pydantic does not merely check — it *converts*.** By default `"5"` becomes `5` and `"true"`
   becomes `True`. Helpful for HTTP (where everything is a string) and occasionally surprising. §5.5.
2. **The inspector only stands at the doors you place them at.** Pydantic validates where you call
   it. Data built internally bypasses it entirely.
3. **A label is free; inspection costs time.** Validating every item in a million-row loop is
   measurable. Validate at boundaries, not in inner loops.
4. **The analogy implies rejection is the only outcome.** Pydantic can also fill defaults, rename
   fields, and normalise values — it is a *parser*, not only a validator.

---

## 5. Detailed technical explanation

### 5.1 Type-hint syntax

```python
from typing import Any, Callable, Literal

name: str
count: int
ratio: float
active: bool
tags: list[str]
scores: dict[str, float]
pair: tuple[str, int]
maybe: str | None                      # Python 3.10+; older: Optional[str]
either: int | str
mode: Literal["strict", "lenient"]     # only these two values
handler: Callable[[str, int], bool]    # takes (str, int), returns bool
anything: Any                          # opt out

def search(query: str, k: int = 5) -> list[str]: ...
def log(message: str) -> None: ...
```

For a class attribute holding a mutable collection, annotate at assignment:

```python
self.cache: dict[str, float] = {}
```

**`from __future__ import annotations`** at the top of a file makes all annotations lazy strings.
Every lab in this course uses it. It allows forward references and avoids some import cycles. Note it
changes how some libraries read annotations at runtime; Pydantic v2 handles it correctly.

### 5.2 Static checking

Hints only pay off if something reads them:

```bash
pip install mypy
mypy src/
```

```
src/service.py:12: error: Argument 1 to "search" has incompatible type "int"; expected "str"
```

Add mypy to CI (M2-L18) and a class of bugs stops reaching review. **But remember it runs on your
source, not on your data.** No static checker can tell you whether the JSON a customer's API returns
matches your model. That is a runtime question, and it needs Pydantic.

### 5.3 Pydantic models

```python
from pydantic import BaseModel, Field

class Ticket(BaseModel):
    ticket_id: str
    text: str
    priority: int = Field(default=3, ge=1, le=5)
    channel: Literal["email", "chat", "phone"] = "email"
    tags: list[str] = Field(default_factory=list)
```

Note `default_factory` again — the M2-L05 rule persists everywhere.

Common `Field` constraints:

| Constraint | Meaning |
|---|---|
| `ge` / `le` / `gt` / `lt` | Numeric bounds |
| `min_length` / `max_length` | String or collection length |
| `pattern` | Regular expression for strings |
| `description` | Documentation; **appears in the generated JSON Schema** |
| `alias` | Accept a different incoming field name |

The `description` field matters more than it looks. In M5-L08 you will hand a generated JSON Schema
to a language model as a tool definition, and those descriptions become the model's instructions.

### 5.4 Validating input

```python
ticket = Ticket(ticket_id="T-1", text="Help")           # keyword arguments
ticket = Ticket.model_validate({"ticket_id": "T-1", ...})  # from a dict
ticket = Ticket.model_validate_json(raw_json_string)       # from JSON text

ticket.model_dump()          # -> dict
ticket.model_dump_json()     # -> JSON string
Ticket.model_json_schema()   # -> JSON Schema dict
```

**These are the v2 names.** Pydantic v1 used `parse_obj`, `dict()` and `json()`. Much material online
is still v1. `[VERIFIED 2026-09-07]` — this course uses **pydantic 2.13.5**, confirmed installed and
executed in this environment.

Handling failure:

```python
from pydantic import ValidationError

try:
    ticket = Ticket.model_validate(payload)
except ValidationError as exc:
    for error in exc.errors():
        print(error["loc"], error["msg"], error["input"])
```

`exc.errors()` returns a **structured list**, not a string. Each entry has `loc` (the field path, as
a tuple, so nested fields are traceable), `msg`, `type` and `input`. You can turn that straight into
an API error response or feed it back to a model for repair (M5-L07).

### 5.5 Coercion versus strict mode

By default Pydantic **coerces** compatible types:

| Input | Field type | Result |
|---|---|---|
| `"5"` | `int` | `5` ✅ |
| `5.0` | `int` | `5` ✅ |
| `5.7` | `int` | ❌ error — lossy |
| `"true"` | `bool` | `True` ✅ |
| `"high"` | `int` | ❌ error |

This is right for HTTP and forms, where everything arrives as a string. It can be wrong when you need
exactness — a field that must be an integer and receives `"5"` from an LLM might indicate the model
misunderstood the schema, and silently accepting it hides that.

```python
from pydantic import ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(strict=True)
    count: int          # now "5" is rejected
```

**Guidance:** coercion for HTTP and config; consider strict for LLM output when the distinction is
diagnostically useful. Whichever you pick, know which you picked.

**Also configure what happens to unexpected fields:**

```python
model_config = ConfigDict(extra="forbid")   # reject unknown fields
```

The default is `"ignore"` — silently dropping them. For LLM output, `extra="forbid"` is usually
better: a model inventing a field is a signal you want to see, not swallow.

### 5.6 Custom validators

```python
from pydantic import field_validator, model_validator

class Chunk(BaseModel):
    text: str
    start: int
    end: int

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v.strip()            # validators can NORMALISE, not just check

    @model_validator(mode="after")
    def check_range(self):
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be greater than start ({self.start})")
        return self
```

- `@field_validator` — one field. Can transform the value by returning a new one.
- `@model_validator(mode="after")` — runs once all fields are validated, so it can compare them.
  This is where cross-field rules live, such as the `overlap < size` check from M2-L05.

### 5.7 Nested models and JSON Schema

```python
class Citation(BaseModel):
    doc_id: str
    quote: str = Field(min_length=1, max_length=300)

class Answer(BaseModel):
    text: str
    citations: list[Citation] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
```

Nested models validate recursively, and error `loc` values become paths like
`("citations", 0, "quote")`, pinpointing the exact element.

**This `Answer` model is close to what you will actually use in Module 7.** Requiring at least one
citation *in the schema* means an uncited answer cannot be constructed — the abstention and grounding
rules become type-level guarantees rather than instructions the model may ignore.

`Answer.model_json_schema()` produces a JSON Schema you can hand to an LLM as the required output
format (M5-L06) or as a tool definition (M5-L08). **You define the shape once and it serves as
validation, documentation, API schema and model instruction.**

### 5.8 Assumptions and limitations

- Pydantic validates **at the boundary you place it**. Internal construction bypasses it.
- Validation costs time. Do it once per boundary crossing, not inside hot loops.
- A valid shape is not a correct value. `confidence: 0.99` passes every constraint and may be
  nonsense (M1-L10). **Schema validity is necessary, not sufficient.**
- Pydantic v1 and v2 APIs differ substantially; check which version a tutorial targets.

---

## 6. Worked example — hardening an LLM response

Preview of M5-L07, using only Module 2 tools.

**The naive version:**

```python
import json
data = json.loads(llm_output)
category = data["category"]
confidence = data["confidence"]
```

Failure modes, all of which happen in practice:

| Failure | Result |
|---|---|
| Output wrapped in ```` ```json ```` fences | `JSONDecodeError` |
| Missing `confidence` | `KeyError` |
| `"confidence": "high"` | Silently a string; comparisons misbehave |
| `"confidence": 1.7` | Out of range, silently accepted |
| `"category": "Billing "` | Trailing space breaks routing |
| `"category": "Refunds"` | Not a real category, silently accepted |
| Extra invented fields | Silently ignored |

**The Pydantic version:**

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "technical", "account", "sales"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("category", mode="before")
    @classmethod
    def normalise(cls, v):
        return v.strip().lower() if isinstance(v, str) else v
```

Now every row of that table is handled:

- `Literal` rejects invented categories **and** enumerates the valid ones in the JSON Schema, so the
  model is told what they are.
- `ge`/`le` reject out-of-range confidence.
- `mode="before"` normalises whitespace and case *before* the `Literal` check, so `"Billing "` is
  accepted as `"billing"` rather than rejected.
- `extra="forbid"` surfaces invented fields instead of hiding them.

**And the errors are actionable:**

```python
try:
    result = Classification.model_validate_json(llm_output)
except ValidationError as exc:
    for e in exc.errors():
        print(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']} (got {e['input']!r})")
```

That loop produces text you can put directly into a repair prompt: *"Your previous output was invalid:
confidence: Input should be less than or equal to 1 (got 1.7). Try again."* This is the repair loop of
M5-L07, and it works because `exc.errors()` is structured data rather than a message.

**What this still does not do.** A response of
`{"category": "billing", "confidence": 0.99, "reason": "because"}` is perfectly valid and may be
completely wrong. **Validation guarantees shape, never truth.** That is Module 7's problem.

---

## 7. Practical activity

**File:** [`labs/m2/l08_pydantic.py`](../../labs/m2/l08_pydantic.py)

**Requires the virtual environment** (`pydantic==2.13.5`):

```bash
source .venv/bin/activate
python labs/m2/l08_pydantic.py
```

Runs the `Classification` model against nine malformed LLM outputs, prints each error exactly as a
repair loop would see it, then shows coercion versus strict mode, nested-model error paths, and the
generated JSON Schema.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `model_config = ConfigDict(extra="forbid")` | Invented fields become errors rather than silence. |
| `Literal["billing", ...]` | Restricts values **and** documents them in the JSON Schema. |
| `@field_validator("category", mode="before")` | Normalises *before* type checking, so `"Billing "` passes. |
| `exc.errors()` | Structured errors: `loc`, `msg`, `type`, `input`. |
| `model_validate_json` | Parse and validate in one step. |
| `model_json_schema()` | The schema you hand to a model as its output contract. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with pydantic 2.13.5, Python 3.12.3:

```
==========================================================================
TYPE HINTS AND PYDANTIC VALIDATION
==========================================================================

--------------------------------------------------------------------------
1. NINE REAL LLM FAILURE MODES, VALIDATED
--------------------------------------------------------------------------
  valid
    OK -> category='billing' confidence=0.92 (float)

  messy case/space
    OK -> category='billing' confidence=0.8 (float)

  coercible number
    OK -> category='sales' confidence=0.75 (float)

  invented category
    REJECTED: category: Input should be 'billing', 'technical', 'account' or 'sales' (received 'refunds')

  confidence out of range
    REJECTED: confidence: Input should be less than or equal to 1 (received 1.7)

  confidence as word
    REJECTED: confidence: Input should be a valid number, unable to parse string as a number (received 'high')

  missing field
    REJECTED: reason: Field required (received {'category': 'billing', 'confidence': 0.5})

  invented extra field
    REJECTED: urgency: Extra inputs are not permitted (received 9)

  wrapped in code fences
    REJECTED: (root): Invalid JSON: expected value at line 1 column 1 (received '```json\n{"category": "billing", "confidence": 0.5, "reason": "ok"}\n```')


--------------------------------------------------------------------------
2. exc.errors() IS STRUCTURED DATA, NOT A STRING
--------------------------------------------------------------------------
  3 errors found in one payload:

    loc   : ('category',)
    type  : literal_error
    msg   : Input should be 'billing', 'technical', 'account' or 'sales'
    input : 'refunds'

    loc   : ('confidence',)
    type  : less_than_equal
    msg   : Input should be less than or equal to 1
    input : 1.7

    loc   : ('reason',)
    type  : string_too_short
    msg   : String should have at least 1 character
    input : ''

  Every one of those fields is programmatically accessible.
  That is what lets you build an API error body, or a repair
  prompt, without parsing English (M5-L07).

--------------------------------------------------------------------------
3. COERCION vs STRICT MODE
--------------------------------------------------------------------------
  input                           default (coercing)            strict=True
  {"count": "5", "flag": "true"}  {'count': 5, 'flag': True}    REJECTED
  {"count": 5.0, "flag": true}    {'count': 5, 'flag': True}    REJECTED
  {"count": 5.7, "flag": true}    REJECTED                      REJECTED

  Coercion is right for HTTP and forms, where everything arrives
  as a string. For LLM output, a string where you asked for a
  number may be a signal the model misread the schema - and
  strict mode makes that visible instead of hiding it.
  Note 5.7 -> int is rejected by BOTH: coercion never loses data.

--------------------------------------------------------------------------
4. NESTED MODELS - loc PINPOINTS THE FAILING ELEMENT
--------------------------------------------------------------------------
  citation missing doc_id
    loc=('citations', 1, 'doc_id')  Field required

  empty citations list
    loc=('citations',)  List should have at least 1 item after validation, not 0

  duplicate quotes
    loc=()  Value error, citations must not repeat the same quote

  Note loc=('citations', 1, 'doc_id'): list INDEX included. In a
  20-citation answer that tells you exactly which one is broken.

--------------------------------------------------------------------------
5. THE GENERATED JSON SCHEMA - your contract with the model
--------------------------------------------------------------------------
{
  "additionalProperties": false,
  "description": "A ticket classification returned by a language model.",
  "properties": {
    "category": {
      "enum": [
        "billing",
        "technical",
        "account",
        "sales"
      ],
      "title": "Category",
      "type": "string"
    },
    "confidence": {
      "description": "0-1 certainty",
      "maximum": 1.0,
      "minimum": 0.0,
      "title": "Confidence",
      "type": "number"
    },
    "reason": {
      "maxLength": 500,
      "minLength": 1,
      "title": "Reason",
      "type": "string"
    }
  },
  "required": [
    "category",
    "confidence",
    "reason"
  ],
  "title": "Classification",
  "type": "object"
}

  This is what you hand a language model as its required output
  format (M5-L06) or as a tool definition (M5-L08, M9-L07).
  Notice the enum lists the four valid categories, and the
  description text becomes instruction the model actually reads.
  One model definition serves as validation, API documentation,
  and the model's own contract.

--------------------------------------------------------------------------
6. THE LIMIT: VALID SHAPE IS NOT CORRECT CONTENT
--------------------------------------------------------------------------
  Validated successfully: confidence=0.97
  Citation doc_id: 'POLICY-2019-A'

  Every constraint passed. The document POLICY-2019-A may not
  exist. The quote may appear nowhere. The 90 days may be wrong.
  The confidence of 0.97 is a number the model emitted, not a
  measurement (M1-L10).

  Pydantic guarantees SHAPE. It cannot guarantee TRUTH.
  Verifying that doc_id exists and that the quote really appears
  in it is a separate, non-optional step - Module 7 (M7-L12).

==========================================================================
```

### 7.3 Reading the result

**Section 1 is the case for this lesson in one screen.** Nine things a language model actually does,
and what each becomes:

| LLM behaviour | Outcome |
|---|---|
| Correct output | Accepted |
| `"  Billing "` — stray case and whitespace | **Accepted**, normalised to `billing` by the `mode="before"` validator |
| `"confidence": "0.75"` — number as string | **Accepted**, coerced to `0.75` (a real float) |
| `"category": "refunds"` — invented category | Rejected, *and the error lists the four valid values* |
| `"confidence": 1.7` | Rejected — out of range |
| `"confidence": "high"` | Rejected — not parseable as a number |
| Missing `reason` | Rejected — field required |
| Invented `"urgency": 9` | Rejected by `extra="forbid"` |
| Wrapped in ```json fences | Rejected as invalid JSON |

Rows 2 and 3 matter as much as the rejections. A brittle parser would have failed on both; the model
*meant* the right thing and formatted it imperfectly, and the validator repairs rather than rejects.
**Good validation is not maximally strict — it is strict about what matters and forgiving about what
does not.**

Row 4's message is worth quoting: `Input should be 'billing', 'technical', 'account' or 'sales'`.
That sentence can be sent straight back to the model as a correction, because `Literal` both
constrains the value and documents the alternatives.

The last row is a reminder that validation happens *after* parsing. Code fences are a formatting
problem, not a schema problem, and you strip them before validating (M5-L07).

**Section 2 shows why `exc.errors()` matters.** One payload, three independent errors, each with a
`loc`, a machine-readable `type` (`literal_error`, `less_than_equal`, `string_too_short`), the
message, and the offending input. **Pydantic reports every problem at once**, not just the first —
so a repair prompt can fix all three in one retry instead of three round trips.

**Section 3's third row is the interesting one.** `5.7` into an `int` is rejected by *both* modes.
Coercion converts between representations of the same value; it never silently loses information.
That is a well-chosen default and worth knowing before you reach for strict mode.

**Section 4 shows the `loc` path doing real work:**

```
loc=('citations', 1, 'doc_id')   Field required
```

Not "a citation is invalid" but *the second one, its `doc_id` field*. In a twenty-citation answer
that is the difference between a five-second fix and a hunt. Note also that the cross-field
`model_validator` reports `loc=()` — an error about the object as a whole rather than any one field.

**Section 5 is the payoff.** One class definition produced a JSON Schema with `enum` listing the
valid categories, `minimum`/`maximum` on confidence, `minLength`/`maxLength` on reason,
`additionalProperties: false` from `extra="forbid"`, and your `description` text carried through.

**You wrote the shape once.** It now serves as runtime validation, API documentation, and the
contract you hand the model. When you reach M5-L06 and M9-L07 you will send this exact structure to a
model as its required output format — and the constraints you defined for safety become instructions
the model reads.

**Section 6 is the caveat you must not skip.** The fabricated answer passes *every* constraint:
`POLICY-2019-A` may not exist, the quote may appear nowhere, 90 days may be invented, and 0.97 is a
number the model emitted rather than a measurement (M1-L10).

**Pydantic guarantees shape. It cannot guarantee truth.** Checking that the document exists and that
the quote genuinely appears in it is a separate, non-optional step — M7-L12.

**Verification:** confirm 3 of 9 outputs are accepted, that `5.7` is rejected in both modes, that
the nested error shows `('citations', 1, 'doc_id')`, and that the schema contains an `enum` of four
categories.

---

## 8. Common mistakes and troubleshooting

1. **Believing hints are enforced.** They are not. Only Pydantic (or a checker) acts on them.
2. **Using v1 API names** (`parse_obj`, `.dict()`, `.json()`) with v2.
3. **Leaving `extra="ignore"`** for LLM output, hiding invented fields.
4. **Validating in a hot loop** rather than at the boundary.
5. **Catching `ValidationError` and logging `str(exc)`** instead of using `exc.errors()`.
6. **Assuming valid means correct.**
7. **Mutable defaults without `default_factory`.**
8. **Over-constraining**, so legitimate inputs are rejected in production.

| Error | Cause | Fix |
|---|---|---|
| `ValidationError: Field required` | Missing key | Add a default, or fix the producer |
| `Input should be a valid integer` | Uncoercible value | Fix upstream, or widen the type deliberately |
| `Extra inputs are not permitted` | `extra="forbid"` caught an unexpected field | Usually correct — investigate the producer |
| `AttributeError: 'Model' object has no attribute 'dict'` | v1 API on v2 | `model_dump()` |
| `JSONDecodeError` before validation | Output wrapped in code fences | Strip fences first (M5-L07) |
| Everything validates but behaviour is wrong | Shape is right, values are not | You need grounding, not validation (Module 7) |

---

## 9. Security, privacy, reliability and cost

- **Security.** Validation at the boundary is a **primary security control**. An unvalidated field
  flowing into a database query, a file path or a shell command is an injection. `extra="forbid"`
  also blocks mass-assignment, where an attacker sets fields you never intended to expose.
- **Security (AI-specific).** LLM output is untrusted input. It may be influenced by content in a
  retrieved document (prompt injection, M5-L13). Validating it against a strict schema is one of the
  few defences that does not itself rely on the model behaving.
- **Privacy.** `model_dump()` returns **every** field. Logging it wholesale exports personal data.
  Project the fields you need, or mark sensitive ones and exclude them (M10-L06).
- **Reliability.** A `ValidationError` is a *good* outcome — a caught failure at a known place.
  Design for it: retry, repair, or fall back (M5-L14).
- **Cost.** Validation is cheap relative to an LLM call. Rejecting a malformed response early and
  retrying once costs far less than a wrong answer reaching a customer.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Write type hints for:

1. A function taking a list of strings and returning a dict from string to int.
2. A variable that may hold a float or nothing.
3. A parameter accepting only `"asc"` or `"desc"`.
4. A function taking a callback of `(str) -> bool` and returning nothing.
5. A dict mapping a tuple of (string, int) to a list of floats.

Then run mypy on a file where you call one of them with the wrong type, and record the message.

### Exercise 2 — Intermediate (~30 min)

Build a `SearchRequest` Pydantic model for an API endpoint:

- `query`: string, 1–500 characters, whitespace stripped.
- `k`: integer, 1–50, default 5.
- `filters`: dict of string to string, default empty.
- `mode`: `"semantic"`, `"keyword"` or `"hybrid"`, default `"hybrid"`.
- `include_metadata`: bool, default False.
- Unknown fields rejected.
- A model validator rejecting `mode="keyword"` combined with `k > 20`, with a clear message.

Then write **eight** test cases: valid minimal, valid full, missing query, blank query, `k=0`,
`k=100`, invalid mode, and the cross-field rule. For each, print `exc.errors()` and note whether the
message would be useful to an API caller.

### Exercise 3 — Challenge (~30 min)

1. Define the `Answer` model from §5.7 with nested `Citation`.
2. Feed it five malformed JSON payloads including: a citation missing `doc_id`; an empty citations
   list; `confidence` of 1.5; a quote of 400 characters; and a completely invalid JSON string.
3. For each, print the full `loc` path. Show how the path pinpoints the failing element in a nested
   list.
4. Write `format_errors_for_repair(exc) -> str` producing a message you would send back to a model
   asking it to fix its output. Keep it under 200 characters.
5. Now construct a payload that **passes every validation and is factually wrong** (a fabricated
   `doc_id`, a confident tone, a plausible quote). Explain in three sentences what this proves about
   the limits of schema validation, and name the module that addresses it.

Part 5 is the most important. The answer key explains why.

---

## 11. Quiz

**Q1.** What happens at runtime when you call `add("a", "b")` on `def add(a: int, b: int) -> int`?

- A. `TypeError`.
- B. It runs normally and returns `"ab"` — hints are not enforced at runtime.
- C. A warning.
- D. mypy raises an error at runtime.

**Q2.** When is Pydantic the right tool rather than a dataclass?

- A. Always.
- B. When data comes from outside your program — HTTP, files, env vars, users, or LLM output — and
  must be validated and parsed.
- C. Only for databases.
- D. When you need inheritance.

**Q3.** What does `extra="forbid"` do, and why does it matter for LLM output?

- A. Nothing significant.
- B. Rejects fields not in the model; for LLM output this surfaces invented fields instead of
  silently dropping them, and it blocks mass-assignment.
- C. Forbids optional fields.
- D. Disables coercion.

**Q4.** By default, what does Pydantic do with `"5"` for a field typed `int`?

- A. Rejects it.  B. Coerces it to `5`.  C. Stores it as a string.  D. Returns `None`.

**Q5.** Why use `exc.errors()` rather than `str(exc)`?

- A. It is shorter.
- B. It returns structured data — `loc`, `msg`, `type`, `input` — which you can turn into an API
  response or a repair prompt, rather than a blob of text.
- C. `str(exc)` raises.
- D. There is no difference.

**Q6.** In §6, why is `mode="before"` used on the category validator?

- A. To run after all fields are set.
- B. So whitespace and case are normalised before the `Literal` check, letting `"Billing "` be
  accepted as `"billing"` rather than rejected.
- C. To improve performance.
- D. Because `Literal` requires it.

**Q7.** What does a `@model_validator(mode="after")` let you do that a `@field_validator` cannot?

- A. Change a field's type.
- B. Compare fields against each other, since it runs once every field has been validated.
- C. Reject the model entirely.
- D. Generate JSON Schema.

**Q8.** A payload passes every Pydantic constraint. What have you proved?

- A. The data is correct.
- B. Only that its shape is right — the values may still be false, fabricated or nonsensical.
- C. The LLM understood the task.
- D. No further checking is needed.

**Q9.** Where should validation happen in a pipeline?

- A. Inside every inner loop.
- B. At boundaries — where data enters your program — once per crossing.
- C. Only in tests.
- D. After processing.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why the team should
validate LLM responses with a schema even though the prompt already asks for that exact format.

---

## 12. Revision notes

- **Type hints are not enforced at runtime.** They serve humans and static checkers (mypy, pyright).
- **Pydantic enforces them at runtime.** TypeScript:Zod :: Python:Pydantic.
- **Decision rule: data from outside your program → Pydantic.** LLM output counts as outside.
- v2 API: `model_validate` · `model_validate_json` · `model_dump` · `model_dump_json` ·
  `model_json_schema`. (v1 used `parse_obj`, `.dict()`, `.json()`.)
- `Field(ge=, le=, min_length=, max_length=, pattern=, description=, default_factory=)`.
  **`description` becomes model-facing instruction in a JSON Schema.**
- `Literal[...]` restricts values *and* enumerates them in the schema.
- `ConfigDict(extra="forbid")` for LLM output. `ConfigDict(strict=True)` disables coercion.
- `@field_validator(..., mode="before")` normalises before type-checking;
  `@model_validator(mode="after")` does cross-field rules.
- **`exc.errors()` is structured** — use it for API responses and repair prompts, never `str(exc)`.
- **Validate at boundaries, not in hot loops.**
- **Valid shape ≠ correct content.** Grounding is Module 7's job.

---

## 13. Completion checklist

- [ ] I can write hints for optionals, unions, literals, generics and callables.
- [ ] I ran mypy and saw it catch a type error.
- [ ] I built a model with field constraints and both validator kinds.
- [ ] I read `exc.errors()` and used `loc` to locate a nested failure.
- [ ] I know the difference between coercion and strict mode, and which I want where.
- [ ] I generated a JSON Schema and can see how it becomes an LLM contract.
- [ ] I constructed a payload that is valid and wrong, and can explain what that proves.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Pydantic v2 documentation. <https://docs.pydantic.dev/latest/> `[UNVERIFIED]` link not re-checked
  2026-09-07; version 2.13.5 `[VERIFIED 2026-09-07]` by installation and execution here.
- Pydantic migration guide (v1 → v2).
  <https://docs.pydantic.dev/latest/migration/> `[UNVERIFIED]`
- Python docs, `typing`. <https://docs.python.org/3/library/typing.html> `[UNVERIFIED]`
- mypy documentation. <https://mypy.readthedocs.io/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L09 — Files, Paths, CSV, JSON and Environment Variables](M2-L09-files-json-env.md)

You can now define and enforce a data contract. Next: getting data in and out — files, paths, CSV,
JSON and the environment variables that will hold your API keys.
