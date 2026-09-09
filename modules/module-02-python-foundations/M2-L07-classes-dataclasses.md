# M2-L07 — Classes, Dataclasses and Composition over Inheritance

| | |
|---|---|
| **Lesson ID** | M2-L07 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L06](M2-L06-modules-packages.md) |

---

## 1. Learning objectives

1. **Write** a class with `__init__`, methods and properties, and **explain** what `self` is.
2. **Use** `@dataclass` and **state** exactly what it generates for you.
3. **Decide** between a dict, a dataclass, a plain class and a Pydantic model.
4. **Explain** why composition is preferred to inheritance for the code in this course, with an
   example of each.
5. **Use** `Protocol` for structural typing so components can be swapped and tested.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Class** | A template describing the data and behaviour of a kind of object. |
| **Instance** | One object created from a class. |
| **`self`** | The instance, passed automatically as the first argument to every method. |
| **`__init__`** | The initialiser, run when an instance is created. |
| **Attribute** | A value stored on an instance. |
| **Method** | A function defined in a class body. |
| **`@dataclass`** | A decorator generating `__init__`, `__repr__` and `__eq__` from annotations. |
| **`field(default_factory=...)`** | Supplies a fresh mutable default per instance. |
| **`frozen=True`** | Makes a dataclass immutable and hashable. |
| **`@property`** | Exposes a computed value as if it were an attribute. |
| **`@staticmethod`** | A function in a class namespace that takes no `self`. |
| **`@classmethod`** | Receives the class as `cls`; commonly used for alternative constructors. |
| **Inheritance** | A class deriving behaviour from a parent class. |
| **Composition** | A class holding other objects and delegating to them. |
| **Protocol** | A structural type: "anything with these methods", checked by type-checkers. |
| **Dunder** | A "double underscore" special method such as `__repr__`. |

---

## 3. Plain-language explanation

A class bundles data with the operations on that data.

```python
class Retriever:
    def __init__(self, index: dict[str, str], k: int = 5) -> None:
        self.index = index
        self.k = k

    def search(self, query: str) -> list[str]:
        hits = [doc_id for doc_id, text in self.index.items() if query in text]
        return hits[: self.k]

retriever = Retriever({"d1": "refund policy"}, k=3)
retriever.search("refund")
```

`self` is the instance. It is passed automatically — `retriever.search("refund")` calls
`Retriever.search(retriever, "refund")`. Python makes this explicit where other languages hide it,
which is unusual at first and then clearer.

**The more important question is when to use a class at all.** Coming from Java you may reach for one
by default. Python does not need that. A module of functions is often better, and this course uses
classes sparingly and deliberately.

| Situation | Use |
|---|---|
| A bag of related values, no behaviour | `@dataclass` |
| Values arriving from **outside** your program (API, file, user) | **Pydantic model** (M2-L08) |
| Behaviour with state carried between calls | A class |
| Behaviour with no state | A **function** in a module |
| A fixed set of named options | `Enum` |
| A quick internal structure, throwaway | `dict` |

**Default to functions and dataclasses.** Reach for a class when there is genuine state to carry.

---

## 4. Analogy

**A class is a form template; an instance is a filled-in form.** The template defines the fields;
each filled copy holds different values.

### Where the analogy breaks

1. **Templates are inert; classes carry behaviour.** A form does not compute.
2. **Class attributes are shared by every instance** — a mutable one is a shared global (§5.6). No
   paper form behaves like that.
3. **Python has no `private`.** A leading underscore is a convention. Anyone can read
   `obj._internal`.
4. **The template metaphor suggests inheritance is natural** — "a specialised form". In practice
   inheritance couples classes tightly and Python's duck typing makes it far less necessary than in
   Java or C#.

---

## 5. Detailed technical explanation

### 5.1 A plain class

```python
class TokenCounter:
    """Counts tokens across many calls."""

    def __init__(self, price_per_1k: float) -> None:
        self.price_per_1k = price_per_1k
        self.total_tokens = 0          # per-instance state

    def add(self, tokens: int) -> None:
        if tokens < 0:
            raise ValueError(f"tokens must be non-negative, got {tokens}")
        self.total_tokens += tokens

    @property
    def cost(self) -> float:
        """Computed on access; no parentheses at the call site."""
        return self.total_tokens / 1000 * self.price_per_1k

    def __repr__(self) -> str:
        return f"TokenCounter(tokens={self.total_tokens}, cost={self.cost:.4f})"
```

- Every method takes `self` first.
- `@property` makes `counter.cost` read like an attribute while running code. Use it for cheap
  derived values; if it is expensive or can fail, make it a method so the cost is visible.
- `__repr__` controls what you see in a debugger and in logs. **Always write one** for classes you
  will debug — the default `<object at 0x7f...>` tells you nothing.

### 5.2 `@dataclass`

Most classes are just data. `@dataclass` removes the boilerplate:

```python
from dataclasses import dataclass, field

@dataclass
class Chunk:
    chunk_id: str
    text: str
    doc_id: str
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
```

That generates, from the annotations alone:

- `__init__(self, chunk_id, text, doc_id, score=0.0, tags=None→[])`
- `__repr__` showing every field
- `__eq__` comparing field by field

Written by hand that is roughly 20 lines. Useful options:

| Option | Effect |
|---|---|
| `@dataclass(frozen=True)` | Immutable; assignment raises; instances become **hashable** so they can be dict keys or set members |
| `@dataclass(order=True)` | Generates `<`, `>` etc. for sorting |
| `@dataclass(slots=True)` | Uses `__slots__`: less memory, faster attribute access, no new attributes |
| `@dataclass(kw_only=True)` | All fields keyword-only — the M2-L05 API lesson, applied to constructors |

**`field(default_factory=list)` is mandatory for mutable defaults.** A bare
`tags: list[str] = []` raises `ValueError: mutable default <class 'list'> for field tags is not
allowed`. Dataclasses are one of the very few places Python protects you from the M2-L05 bug — and
the reason is that the same shared-object problem applies.

### 5.3 Dataclass versus dict versus Pydantic

| | `dict` | `@dataclass` | Pydantic model |
|---|---|---|---|
| Field names checked | ❌ typo = new key | ✅ typo = `AttributeError` | ✅ |
| Types **enforced at runtime** | ❌ | ❌ **hints only** | ✅ |
| Parses/coerces input | ❌ | ❌ | ✅ `"5"` → `5` |
| JSON in/out | manual | manual | ✅ built in |
| Speed | fastest | fast | slower (it validates) |
| Use for | throwaway internals | **internal structures you control** | **anything from outside** |

**The decisive line: does the data come from outside your program?** API request, file, environment
variable, another service, an LLM's output → **Pydantic** (M2-L08). Data you constructed yourself
and trust → dataclass.

A dataclass will happily accept `Chunk(chunk_id=42, text=None, doc_id=[], score="high")`. The
annotations are documentation; nothing checks them at runtime.

### 5.4 Composition over inheritance

**Inheritance** — a subclass *is a* parent:

```python
class BaseRetriever:
    def search(self, query: str) -> list[str]:
        raise NotImplementedError

class KeywordRetriever(BaseRetriever):
    def search(self, query: str) -> list[str]:
        ...
```

**Composition** — an object *has a* collaborator:

```python
class SearchService:
    def __init__(self, retriever, reranker, cache) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.cache = cache

    def search(self, query: str) -> list[str]:
        if (hit := self.cache.get(query)) is not None:
            return hit
        results = self.retriever.search(query)
        ranked = self.reranker.rerank(query, results)
        self.cache.set(query, ranked)
        return ranked
```

**Why this course prefers composition:**

1. **Testability.** Pass a fake retriever and a fake cache. No mocking framework, no patching.
2. **Flexibility.** Swap keyword for vector retrieval by passing a different object. Nothing else
   changes.
3. **Shallow, readable code.** Deep inheritance means reading five files to understand one method.
4. **Duck typing makes the base class unnecessary.** Any object with `.search(query)` works. Python
   does not require a declared parent.

Use inheritance when there is a genuine *is-a* relationship and shared implementation — exceptions
(M2-L10) are the clearest legitimate case.

### 5.5 `Protocol` — structural typing

Composition raises a question: how do you *describe* what a valid retriever looks like without
forcing a base class?

```python
from typing import Protocol

class Retriever(Protocol):
    def search(self, query: str, k: int) -> list[str]: ...

def build_service(retriever: Retriever) -> SearchService:
    ...
```

Any object with a matching `search` method satisfies `Retriever` — **no inheritance required, no
registration, nothing to import in the implementing class.** The type-checker verifies the shape;
at runtime nothing changes.

This is the Python equivalent of a TypeScript interface, and it is the right tool for the
swappable-component designs in Modules 7 and 8.

### 5.6 The class-attribute trap

```python
class Bad:
    cache = {}            # CLASS attribute - ONE dict shared by every instance

    def add(self, k, v):
        self.cache[k] = v

a, b = Bad(), Bad()
a.add("x", 1)
b.cache                   # {'x': 1}   <- b sees a's data
```

This is the M2-L05 mutable-default bug at class scope, and it has the same security consequence: in a
long-running server, one user's data becomes visible to another. **Mutable state belongs in
`__init__`**, so each instance gets its own:

```python
class Good:
    def __init__(self) -> None:
        self.cache: dict[str, int] = {}
```

Class attributes are fine for **immutable** constants (`MAX_RETRIES = 3`).

### 5.7 Assumptions and limitations

- Type annotations on dataclasses are not enforced at runtime. That is Pydantic's job.
- `frozen=True` is shallow: a frozen dataclass containing a list still allows the list to be mutated.
- `slots=True` blocks adding attributes at runtime, which some libraries rely on.
- `Protocol` is checked statically only; without a type-checker it documents but does not enforce.

---

## 6. Worked example — the same design three ways

Requirement: represent a retrieved chunk and rank a set of them.

**Version 1 — dicts.**

```python
chunk = {"chunk_id": "c1", "text": "Refunds in 5 days", "score": 0.91}
ranked = sorted(chunks, key=lambda c: (-c["score"], c["chunk_id"]))
```

Fast to write. Problems: `chunk["scor"]` is a silent new key on write and a `KeyError` on read;
nothing documents which fields exist; no editor autocompletion; `c["score"]` could be a string and
nothing notices until the sort produces nonsense.

**Version 2 — dataclass.**

```python
@dataclass(frozen=True, order=False)
class Chunk:
    chunk_id: str
    text: str
    doc_id: str
    score: float = 0.0

    @property
    def preview(self) -> str:
        return self.text[:60] + ("..." if len(self.text) > 60 else "")

ranked = sorted(chunks, key=lambda c: (-c.score, c.chunk_id))
```

Now `c.scor` is an immediate `AttributeError`, fields are documented by the class, editors
autocomplete, `frozen=True` means a chunk cannot be modified after retrieval — which matters, because
a chunk mutated mid-pipeline is a genuinely nasty bug — and being hashable, chunks can go in a `set`
for deduplication (M7-L05).

**It still does not validate.** `Chunk("c1", "text", "d1", score="high")` constructs happily and
fails later, inside the sort, with an error mentioning `str` and `float` and nothing about chunks.

**Version 3 — Pydantic (M2-L08 preview).**

```python
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    chunk_id: str
    text: str
    doc_id: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
```

Now `score="high"` raises immediately at construction, naming the field and the problem;
`score="0.91"` is coerced to `0.91`; `score=1.5` is rejected by the range constraint; and
`Chunk.model_validate_json(raw)` parses JSON straight into a validated object.

**The rule this produces, used for the rest of the course:**

| Data origin | Type |
|---|---|
| Constructed by your own trusted code | `@dataclass` |
| Arrived from an API, file, user, env var, **or an LLM** | **Pydantic** |

The last item is the one that matters most later. An LLM's JSON output is untrusted input from
outside your program, and M5-L06 treats it exactly that way.

---

## 7. Practical activity

**File:** [`labs/m2/l07_classes.py`](../../labs/m2/l07_classes.py)

```bash
python3 labs/m2/l07_classes.py
```

Standard library only. Shows what `@dataclass` generates, the mutable-default protection, `frozen`
and hashability, the class-attribute leak between instances, and composition with two interchangeable
retrievers.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `dataclasses.fields(Chunk)` | Introspects the generated fields — evidence rather than assertion. |
| `field(default_factory=list)` | Fresh list per instance. |
| `@dataclass(frozen=True)` | Immutable and hashable; enables `set` deduplication. |
| `class Bad: cache = {}` | The shared-class-attribute leak, demonstrated. |
| `SearchService(retriever=...)` | Composition: swap the collaborator, change the behaviour. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3:

```
======================================================================
CLASSES, DATACLASSES AND COMPOSITION
======================================================================

----------------------------------------------------------------------
1. WHAT @dataclass ACTUALLY GENERATES
----------------------------------------------------------------------
  __repr__ : Chunk(chunk_id='c1', text='Refunds are processed within 5 business days.', doc_id='d1', score=0.91)
  __eq__   : True
  property : 'Refunds are processed within 5 business ...'

  Fields discovered by introspection:
    chunk_id    str       default=(required)
    text        str       default=(required)
    doc_id      str       default=(required)
    score       float     default=0.0

  Generated methods present on the class:
    __init__    True
    __repr__    True
    __eq__      True
    __hash__    True

----------------------------------------------------------------------
2. DATACLASSES BLOCK THE MUTABLE DEFAULT BUG
----------------------------------------------------------------------
  Trying to define:  items: list[str] = []
    ValueError: mutable default <class 'list'> for field items is not allowed: use default_factory

  This is one of the very few places Python protects you from the
  M2-L05 bug, and for exactly the same reason: one list would be
  shared by every instance.

  With default_factory:  a.items=['book']  b.items=[]

----------------------------------------------------------------------
3. WHAT @dataclass DOES *NOT* DO - no runtime validation
----------------------------------------------------------------------
  Chunk(..., score='high') constructed with NO error: Chunk(chunk_id='c2', text='x', doc_id='d1', score='high')
  type(bad.score) = str

  The annotation said float. Nothing checked it. Now watch where
  it actually fails - a long way from the cause:
    TypeError: bad operand type for unary -: 'str'

  Read that message. It says 'bad operand type for unary -'.
  It does not mention Chunk. It does not mention chunk_id 'c2'.
  It does not mention the field name 'score', or the annotation
  that was ignored, or where the bad value came from. In a real
  pipeline that value may have been built in another module
  minutes earlier, and you now debug a sort function that is
  entirely innocent. THIS is the gap Pydantic closes (M2-L08).

----------------------------------------------------------------------
4. frozen=True MAKES DEDUPLICATION POSSIBLE
----------------------------------------------------------------------
  3 chunks in, 2 unique out (set-based dedup)
  ranked: ['c1', 'c2']

  Mutation blocked: FrozenInstanceError: cannot assign to field 'score'

  To 'change' one, build a new one: Chunk(chunk_id='c1', text='Refund policy', doc_id='d1', score=0.1)

  Without frozen=True, Chunk would be unhashable and set() would
  raise TypeError. Immutability is what buys deduplication.

----------------------------------------------------------------------
5. THE SHARED CLASS-ATTRIBUTE LEAK
----------------------------------------------------------------------
  class Leaky:  cache = {}        # class attribute
    user_a.add('account_number', 12345)
    user_b.cache -> {'account_number': 12345}   <-- user B can read user A's data
    same object? True

  class Correct:  def __init__(self): self.cache = {}
    ok_b.cache -> {}   <-- isolated

  In a long-running FastAPI server this is not a style issue.
  It is cross-tenant data exposure (M7-L15).

----------------------------------------------------------------------
6. COMPOSITION AND Protocol
----------------------------------------------------------------------
  with KeywordRetriever: search('refund') -> ['d1', 'd3']
  with StubRetriever   : search('anything') -> ['stub-1', 'stub-2']
  stub recorded calls  : [('anything', 3)]

  SearchService was tested with no index, no I/O, no mocking
  library and no patching - just a different object passed in.
  Neither retriever inherits from anything; the Protocol describes
  the required shape and the type-checker verifies it.

======================================================================
```

### 7.3 Reading the result

**Section 3 is the reason M2-L08 exists.** Look at what happened:

```
Chunk(..., score='high') constructed with NO error
TypeError: bad operand type for unary -: 'str'
```

The annotation said `score: float`. A string went in. Nothing objected. The object was built,
returned, passed around — and failed later inside an unrelated `sorted()` call with a message that
names **none** of: the class, the chunk id, the field, the annotation, or where the value came from.

In this eight-line lab you can see the cause immediately. In a real ingestion pipeline the bad value
is created in one module, stored, and blows up in another one minutes later. You would spend the
first twenty minutes debugging the sort function, which is entirely innocent.

**Section 4 shows why `frozen=True` is not just about safety.** Three chunks in, two out, using
`set()`. That only works because frozen dataclasses are **hashable**. Drop `frozen=True` and
`set(chunks)` raises `TypeError: unhashable type: 'Chunk'`. Immutability is what buys you set-based
deduplication — the exact operation you will need in M7-L05.

**Section 5 is a security demonstration, not a style note:**

```
user_a.add('account_number', 12345)
user_b.cache -> {'account_number': 12345}   <-- user B can read user A's data
same object? True
```

One mutable class attribute, and two different users share one dictionary. In a FastAPI process
serving many tenants, `user_a` and `user_b` are different customers. `same object? True` is the whole
vulnerability. This is the M2-L05 mutable-default bug promoted to class scope, and it has the same
fix: state goes in `__init__`.

**Section 6 shows what composition buys.** `SearchService` was exercised twice — once against a real
keyword index, once against a stub — with **no mocking library, no patching, and no base class**.
`stub.calls` recorded `[('anything', 3)]`, so the test can also assert *how* the collaborator was
called. Neither retriever inherits from anything; the `Protocol` describes the required shape and the
type-checker enforces it statically.

Try writing that test against an inheritance-based design and you will find yourself constructing a
real index just to test ranking logic. That difference is why this course composes.

**Verification:** confirm the mutable-default `ValueError` appears, `score='high'` constructs
successfully, dedup gives `2 unique out`, and `same object? True` in section 5.

---

## 8. Common mistakes and troubleshooting

1. **Mutable class attributes.** Put state in `__init__`.
2. **Believing dataclass annotations validate.** They do not.
3. **Deep inheritance hierarchies.** Prefer composition.
4. **No `__repr__`** on a class you will debug.
5. **`@property` doing expensive or failing work.** Make it a method.
6. **Using a class where a function would do.**
7. **Forgetting `self`** in a method signature.
8. **Mutating a frozen dataclass's inner list** and expecting protection.

| Error | Cause | Fix |
|---|---|---|
| `TypeError: method() takes 1 positional argument but 2 were given` | Missing `self` | Add `self` as the first parameter |
| `ValueError: mutable default <class 'list'> for field x is not allowed` | `= []` on a dataclass field | `field(default_factory=list)` |
| `AttributeError: 'Chunk' object has no attribute 'scor'` | Typo | Good — this is the dataclass earning its place |
| `dataclasses.FrozenInstanceError` | Assigning to a frozen instance | Build a new one with `dataclasses.replace` |
| `TypeError: unhashable type` | Non-frozen dataclass in a set | `frozen=True` |
| Instances sharing data | Mutable class attribute | Move it into `__init__` |

---

## 9. Security, privacy, reliability and cost

- **Security.** The shared-class-attribute leak (§5.6) is a **cross-tenant data exposure** in any
  long-running server. One request populates a class-level cache; the next request, from a different
  user, reads it. Treat any mutable class attribute as a bug (M7-L15).
- **Reliability.** `frozen=True` on data flowing through a pipeline prevents a whole class of
  action-at-a-distance bugs where a later stage silently modifies an earlier stage's object.
- **Privacy.** A generated `__repr__` prints **every field**. A dataclass holding an email address or
  API key will emit it into logs and tracebacks. For sensitive fields, write a custom `__repr__` that
  redacts (M2-L18, M10-L06).
- **Cost.** `slots=True` reduces memory noticeably for large collections of objects — relevant when
  holding hundreds of thousands of chunks (M7-L03).

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Convert this to a frozen dataclass with a `duration_minutes` property:

```python
def make_call(model, prompt_tokens, completion_tokens, started_at, ended_at):
    return {"model": model, "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "started_at": started_at, "ended_at": ended_at}
```

Then state two bugs the dataclass version prevents that the dict version allows.

### Exercise 2 — Intermediate (~25 min)

1. Write `Chunk` as a frozen dataclass with `chunk_id`, `text`, `doc_id`, `score`.
2. Write `dedupe(chunks)` returning unique chunks, **using a set**. Explain why `frozen=True` is
   required for this to work at all.
3. Write `rank(chunks, k)` returning the top `k` by score with an ID tie-break.
4. Add a `preview` property truncating text to 60 characters with an ellipsis.
5. Now demonstrate the gap: construct a `Chunk` with `score="high"` and show where it fails and what
   the error message says. Is that message helpful for debugging? This motivates M2-L08.

### Exercise 3 — Challenge (~30 min)

1. Define a `Retriever` `Protocol` with `search(query: str, k: int) -> list[str]`.
2. Write two implementations: `KeywordRetriever` (substring match) and `StubRetriever` (returns a
   fixed list). Neither may inherit from anything.
3. Write `SearchService` taking a retriever by composition, with a `search` method that de-duplicates
   and ranks.
4. Write two tests: one with the stub proving `SearchService` logic in isolation, one with the real
   retriever. Note how much setup each needed.
5. Now write the inheritance version — `SearchService(BaseRetriever)` — and try to test its logic
   without a real retriever. Describe precisely what makes it harder.
6. State in three sentences when you *would* choose inheritance.

---

## 11. Quiz

**Q1.** What does `@dataclass` generate from your annotations?

- A. Runtime type validation.
- B. `__init__`, `__repr__` and `__eq__`.
- C. JSON serialisation.
- D. Database mappings.

**Q2.** Why does `tags: list[str] = []` raise an error in a dataclass?

- A. Lists cannot be dataclass fields.
- B. It would be a single list shared by every instance — the mutable-default bug — so dataclasses
  reject it and require `field(default_factory=list)`.
- C. The annotation is wrong.
- D. Defaults must be keyword-only.

**Q3.** A dataclass field is annotated `score: float`. You construct it with `score="high"`. What
happens?

- A. `TypeError` at construction.
- B. It is coerced to a float.
- C. Nothing — annotations are not enforced at runtime, so the object is built and fails later
  somewhere unrelated.
- D. A warning is printed.

**Q4.** When should you use a Pydantic model instead of a dataclass?

- A. Always.
- B. When the data comes from outside your program — an API, a file, an environment variable, a user,
  or an LLM's output — and therefore needs validation and parsing.
- C. Only for database rows.
- D. When you need inheritance.

**Q5.** What does `frozen=True` give you besides immutability?

- A. Faster attribute access.
- B. Hashability, so instances can be dict keys or set members — which is what makes set-based
  deduplication possible.
- C. Runtime validation.
- D. JSON support.

**Q6.** `class Bad: cache = {}` — two instances, one calls `add`. What does the other see?

- A. Nothing; each instance has its own.
- B. The same data — `cache` is a class attribute, so a single dict is shared by every instance.
- C. An error.
- D. A copy.

**Q7.** Why does this course prefer composition to inheritance?

- A. Inheritance is not supported in Python.
- B. Composition allows collaborators to be swapped and faked directly in tests without patching,
  keeps call stacks shallow, and Python's duck typing removes the need for a shared base class.
- C. Composition is faster.
- D. Inheritance cannot be type-checked.

**Q8.** What does `Protocol` provide?

- A. Runtime enforcement of method signatures.
- B. Structural typing — any object with matching methods satisfies it, with no inheritance or
  registration, checked by the type-checker.
- C. Automatic implementation.
- D. Serialisation.

**Q9.** Why is a generated `__repr__` a privacy consideration?

- A. It is slow.
- B. It prints every field, so a dataclass holding an email address or API key will emit it into logs
  and tracebacks.
- C. It exposes the class name.
- D. It is not a consideration.

**Q10.** *(Written, rubric-graded.)* In under 80 words, give your decision rule for choosing between
`dict`, `@dataclass` and a Pydantic model.

---

## 12. Revision notes

- `self` is the instance, passed automatically. `__init__` initialises.
- **Default to functions and dataclasses.** Use a class when there is real state to carry.
- `@dataclass` generates `__init__`, `__repr__`, `__eq__`. Options: `frozen` (immutable **and
  hashable**), `order`, `slots`, `kw_only`.
- **Mutable dataclass defaults need `field(default_factory=...)`** — one of the few places Python
  blocks the M2-L05 bug.
- **Dataclass annotations are not enforced.** `score="high"` constructs fine and fails later.
- **Decision rule: data from outside your program → Pydantic. Data you built → dataclass. LLM output
  counts as outside.**
- **Composition over inheritance:** testable, swappable, shallow. `Protocol` describes the shape
  without a base class.
- **Mutable class attributes are shared by all instances** — a cross-tenant data leak in a server.
  Put state in `__init__`.
- Always write `__repr__` for classes you debug — but **redact sensitive fields**.

---

## 13. Completion checklist

- [ ] I can state the three methods `@dataclass` generates.
- [ ] I saw the mutable-default `ValueError` myself.
- [ ] I demonstrated that annotations are not enforced.
- [ ] I used `frozen=True` to deduplicate with a set.
- [ ] I reproduced the shared class-attribute leak.
- [ ] I wrote a `Protocol` and two implementations with no inheritance.
- [ ] I can state the dict/dataclass/Pydantic decision rule.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python docs, `dataclasses`. <https://docs.python.org/3/library/dataclasses.html> `[UNVERIFIED]`
- Python docs, `typing.Protocol`.
  <https://docs.python.org/3/library/typing.html#typing.Protocol> `[UNVERIFIED]`
- PEP 557 — Data Classes. <https://peps.python.org/pep-0557/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L08 — Type Hints and Pydantic v2 Validation](M2-L08-type-hints-pydantic.md)

You have now twice hit the same wall: annotations document but do not enforce. The next lesson closes
that gap, and it is the single most important lesson in Module 2 for the AI work ahead — Pydantic is
how you will validate LLM output in Module 5.
