# M2-L05 — Functions, Arguments, Scope and Return Values

| | |
|---|---|
| **Lesson ID** | M2-L05 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L04](M2-L04-control-flow-comprehensions.md) |

---

## 1. Learning objectives

1. **Define** functions with positional, keyword, default and variadic parameters.
2. **Explain and avoid** the mutable default argument bug.
3. **Predict** whether a function mutates its caller's data, and **state** the passing semantics
   precisely.
4. **Use** keyword-only and positional-only parameters to make an API hard to misuse.
5. **Write** clear docstrings and **return** multiple values idiomatically.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Parameter** | A name in the function definition. |
| **Argument** | A value passed at the call site. |
| **Positional argument** | Matched by position: `f(1, 2)`. |
| **Keyword argument** | Matched by name: `f(x=1, y=2)`. |
| **Default value** | Used when an argument is omitted. **Evaluated once, at definition time.** |
| **`*args`** | Collects extra positional arguments into a tuple. |
| **`**kwargs`** | Collects extra keyword arguments into a dict. |
| **Keyword-only** | Parameters after a bare `*` that *must* be passed by name. |
| **Positional-only** | Parameters before a `/` that *cannot* be passed by name. |
| **Scope** | The region where a name is visible. |
| **LEGB** | The lookup order: Local → Enclosing → Global → Built-in. |
| **Closure** | A function capturing names from its enclosing scope. |
| **Docstring** | A string literal at the start of a function, its documentation. |
| **Pure function** | Returns a value with no side effects. |
| **Side effect** | Any change outside the function's return value. |

---

## 3. Plain-language explanation

```python
def score_ticket(text: str, threshold: float = 0.5) -> bool:
    """Return True if the ticket looks urgent."""
    return len(text) > 100 and threshold < 0.9
```

`def`, name, parameters, optional `-> return type`, colon, indented body. The string on the first
line is the **docstring** and is a real, inspectable object, not a comment.

Two behaviours differ from what you may expect, and both cause bugs.

**First: arguments can be passed by name, and this is normal Python style.**

```python
score_ticket("some text", 0.8)              # positional
score_ticket("some text", threshold=0.8)    # keyword - clearer
score_ticket(threshold=0.8, text="some")    # order does not matter for keywords
```

Keyword arguments are not an advanced feature here; they are the default way to call anything with
more than two parameters. `retrieve(query, 5, True, False)` is unreadable;
`retrieve(query, k=5, rerank=True, include_metadata=False)` is not.

**Second: default values are evaluated once, when the function is defined — not on each call.** For
immutable defaults (`0`, `""`, `None`) this is invisible. For mutable ones (`[]`, `{}`) it produces
the most famous bug in Python, covered in §5.3.

---

## 4. Analogy

**A function is a vending machine.** Put arguments in, get a return value out. Same input, same
output, no trace left behind — that is a **pure** function, and it is the easiest kind to test.

### Where the analogy breaks

1. **Python functions can reach outside the machine.** They can mutate a list you passed in, write a
   file, or call an API. Those are **side effects**, and they are why testing gets hard.
2. **The machine restocks between customers; a Python default does not.** A default value is created
   *once* at definition and reused by every call, forever. That is the §5.3 bug in one sentence.
3. **Vending machines take exact coins; Python is flexible** — positional, keyword, defaults,
   variadic. That flexibility is useful and also lets you build APIs that are easy to call wrongly.
4. **A machine returns one item; Python appears to return several** — `return a, b` is really one
   tuple, immediately unpacked at the call site.

---

## 5. Detailed technical explanation

### 5.1 Parameter kinds

```python
def retrieve(query, k=5, *extra, rerank=False, **options):
    ...
```

| Part | Kind | Notes |
|---|---|---|
| `query` | Positional-or-keyword, required | — |
| `k=5` | Positional-or-keyword with default | — |
| `*extra` | Variadic positional | Collects surplus positionals into a tuple |
| `rerank=False` | **Keyword-only** | Anything after `*` or `*args` must be named |
| `**options` | Variadic keyword | Collects surplus keywords into a dict |

**Making an API hard to misuse** — the practical use of this:

```python
def search(query: str, *, k: int = 5, rerank: bool = False) -> list[str]:
    ...

search("refunds", k=10, rerank=True)     # fine
search("refunds", 10, True)              # TypeError - and that is the point
```

The bare `*` forces every option to be named. Boolean positional arguments are unreadable at the call
site (`search(q, True, False, True)` means nothing to a reader) and this makes them impossible.
**Use `*` for any function with optional flags.** Every public function you write in this course
should do this.

Positional-only, using `/`, is rarer — mostly for parameters whose names you may want to change
later without breaking callers.

### 5.2 Argument unpacking

```python
args = ("refunds",)
opts = {"k": 10, "rerank": True}
search(*args, **opts)          # unpack a sequence and a mapping into arguments
```

You will meet this constantly when forwarding arguments through wrappers and decorators.

### 5.3 The mutable default argument bug

**This is the single most famous Python gotcha. Learn it once, properly.**

```python
def add_tag(tag, tags=[]):        # BUG
    tags.append(tag)
    return tags

add_tag("a")      # ['a']
add_tag("b")      # ['a', 'b']   <-- WHY?
add_tag("c")      # ['a', 'b', 'c']
```

**Why:** `tags=[]` creates **one list**, once, when the `def` statement executes. Every call that
omits the argument receives *that same list*. It accumulates forever, across calls, across
unrelated parts of your program — and it persists for the lifetime of the process.

**The fix — always:**

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []                 # a fresh list per call
    tags.append(tag)
    return tags
```

Note this is exactly why `is None` (M2-L02 §5.6) matters: if you wrote `if not tags:`, then passing a
legitimately empty list would be silently replaced by a new one, discarding the caller's object.

**The rule: never use a mutable value (`[]`, `{}`, `set()`, or an object instance) as a default.
Use `None` and create it inside.**

The same trap applies to defaults that are *computed*:

```python
def log(message, timestamp=datetime.now()):    # BUG: evaluated ONCE at import
```

Every log entry gets the time the module was imported. Use `timestamp=None` and default inside.

### 5.4 How arguments are passed

Python passes **references by value**. The precise consequence:

```python
def rebind(items):
    items = [9, 9]          # rebinds the LOCAL name only
def mutate(items):
    items.append(9)         # mutates the SHARED object

data = [1, 2]
rebind(data); print(data)   # [1, 2]  - unchanged
mutate(data); print(data)   # [1, 2, 9]  - changed
```

**Reassigning a parameter never affects the caller. Mutating the object always does.**

This is the M2-L02 luggage-tag idea applied to functions, and it is the source of a common real bug:
a function that "just normalises" its input and quietly modifies the caller's data.

```python
def normalise(records):              # DANGEROUS: mutates the caller's list
    for r in records:
        r["text"] = r["text"].strip()
    return records

def normalise(records):              # SAFE: returns new objects
    return [{**r, "text": r["text"].strip()} for r in records]
```

**Default to not mutating arguments.** If a function must mutate, say so in its name (`sort_in_place`)
and its docstring. This becomes important in Module 7 where document dictionaries pass through many
processing stages.

### 5.5 Scope and LEGB

Python resolves names in this order: **Local → Enclosing → Global → Built-in.**

```python
threshold = 0.5                 # Global

def outer():
    factor = 2                  # Enclosing (relative to inner)
    def inner():
        result = threshold * factor    # finds both by walking outward
        return result
    return inner()
```

**Assignment creates a local name**, which produces this surprise:

```python
count = 0
def increment():
    count = count + 1        # UnboundLocalError
```

Because `count` is assigned in the body, Python treats it as local *throughout the function* — so the
read on the right-hand side happens before assignment. `global count` fixes it; **not needing it is
better.** Take the value as a parameter and return the new one.

`nonlocal` does the same for an enclosing function's scope. Both are rarely the right answer; a
function that reads and writes module-level state is hard to test and hard to run concurrently
(M2-L13).

### 5.6 Returning values

```python
def analyse(text):
    return len(text), text.count(" "), text.isupper()

length, spaces, shouting = analyse("HELLO WORLD")
```

`return a, b, c` builds a tuple, unpacked at the call site. Beyond three values, return a
`dataclass` or a Pydantic model instead (M2-L07, M2-L08) — positional unpacking of five values is a
readability and correctness hazard.

A function with no `return` returns `None`. A bare `return` also returns `None`.

**Guard clauses** flatten nesting:

```python
def process(ticket):
    if ticket is None:
        return None
    if not ticket.get("text"):
        return None
    return ticket["text"].strip().lower()
```

Prefer this to a nested `if/else` pyramid. It is the dominant style in modern Python.

### 5.7 Docstrings

```python
def chunk_text(text: str, *, size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: The document text to split.
        size: Target chunk length in characters.
        overlap: Characters shared between consecutive chunks.

    Returns:
        A list of chunks. Empty input returns an empty list.

    Raises:
        ValueError: If overlap >= size.
    """
```

Accessible at runtime via `chunk_text.__doc__` and `help(chunk_text)`. Document what is **not**
obvious from the signature: edge cases, exceptions, units, and whether arguments are mutated.

### 5.8 Assumptions and limitations

- Type hints (`-> list[str]`) are **not enforced at runtime**. They document and enable tooling.
  Runtime enforcement is Pydantic's job (M2-L08).
- Closures capture variables, not values — the M2-L04 late-binding bug.
- Recursion is limited to roughly 1,000 frames by default; Python has no tail-call optimisation.

---

## 6. Worked example — designing a function well

Requirement: split a document into overlapping chunks for retrieval. This is the real M7-L06
function, built here for its *interface* rather than its algorithm.

**Attempt 1 — works, poor interface:**

```python
def chunk(t, s, o, k):
    ...
```

Problems: meaningless names; every argument required; caller writes `chunk(text, 500, 50, True)`
which is unreadable; no types; no docs.

**Attempt 2 — better names and defaults:**

```python
def chunk_text(text, size=500, overlap=50, keep_empty=False):
    ...
```

Better. But `chunk_text(text, 500, 50, True)` is still legal and still unreadable, and a caller could
swap `size` and `overlap` silently.

**Attempt 3 — keyword-only options:**

```python
def chunk_text(text: str, *, size: int = 500, overlap: int = 50,
               keep_empty: bool = False) -> list[str]:
```

Now `chunk_text(text, 500, 50)` is a `TypeError`. Callers *must* write
`chunk_text(text, size=500, overlap=50)`. Swapping them is now impossible, and the call site is
self-documenting.

**Attempt 4 — validate, and fail loudly:**

```python
def chunk_text(text: str, *, size: int = 500, overlap: int = 50,
               keep_empty: bool = False) -> list[str]:
    """Split text into overlapping chunks of roughly `size` characters.

    Args:
        text: Document text. Not modified.
        size: Target chunk length in characters. Must be > 0.
        overlap: Characters shared between consecutive chunks. Must be < size.
        keep_empty: If False, whitespace-only chunks are dropped.

    Returns:
        A list of chunks in document order. Empty or whitespace-only input
        returns an empty list.

    Raises:
        ValueError: If size <= 0, overlap < 0, or overlap >= size.
    """
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be less than size ({size})")

    if not text.strip():
        return []

    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(text), step):
        piece = text[start:start + size]
        if keep_empty or piece.strip():
            chunks.append(piece)
    return chunks
```

**Why `overlap >= size` must raise rather than being clamped.** If `overlap == size` then `step` is
0 and `range(0, n, 0)` raises an obscure `ValueError: range() arg 3 must not be zero`. If
`overlap > size`, `step` is negative and `range` produces nothing — the function silently returns an
empty list and your entire retrieval index ends up empty, with no error anywhere. **A validation
check turns a silent catastrophic failure into an immediate, named one.** This pattern — validate at
the boundary, fail with a message naming the offending value — is used throughout the rest of the
course.

Note also: the function **does not mutate `text`** (strings are immutable, so it could not), it
builds and returns a new list, and the docstring says so explicitly.

---

## 7. Practical activity

**File:** [`labs/m2/l05_functions.py`](../../labs/m2/l05_functions.py)

```bash
python3 labs/m2/l05_functions.py
```

Demonstrates the mutable default bug and its persistence across calls, the rebind-versus-mutate
distinction, `UnboundLocalError`, keyword-only enforcement, and runs the §6 `chunk_text` including
its validation failures.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `def add_tag(tag, tags=[])` | The bug, preserved deliberately. Watch the list grow across calls. |
| `id(tags)` | Proves it is the *same list object* every time. |
| `def search(query, *, k=5)` | The bare `*` makes everything after it keyword-only. |
| `{**r, "text": ...}` | Dict unpacking to build a **new** dict rather than mutating. |
| `chunk_text.__doc__` | Docstrings are runtime objects, not comments. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. The `id()` values will differ on your machine; what matters
is whether they are the **same** or **different** across calls.

```
======================================================================
FUNCTIONS, ARGUMENTS AND SCOPE
======================================================================

----------------------------------------------------------------------
1. THE MUTABLE DEFAULT ARGUMENT BUG
----------------------------------------------------------------------
  def add_tag(tag, tags=[]):  ...  tags.append(tag)

    add_tag_buggy("a") -> ['a']   id=138845418693760
    add_tag_buggy("b") -> ['a', 'b']   id=138845418693760
    add_tag_buggy("c") -> ['a', 'b', 'c']   id=138845418693760

  The SAME id every time: every call received the SAME list object,
  created once when the 'def' line executed. It accumulates for the
  lifetime of the process.

  def add_tag(tag, tags=None): if tags is None: tags = []

    add_tag_fixed("a")  -> ['a']   id=138845418694848
    add_tag_fixed("b")  -> ['b']   id=138845418694912
    add_tag_fixed("c")  -> ['c']   id=138845418694656

  Three distinct ids: 3 unique objects.
  A fresh list per call, and none of them accumulate.

  And the fix respects a deliberately-passed empty list:
    caller passed [] -> got ['x'], same object: True
    (Using 'if not tags:' instead of 'is None' would have thrown the
     caller's list away and returned a different one. M2-L02.)

----------------------------------------------------------------------
2. REBIND vs MUTATE
----------------------------------------------------------------------
  after rebind(data)  : [1, 2]   <-- unchanged
  after mutate(data)  : [1, 2, 9]   <-- changed

  Reassigning a parameter NEVER affects the caller.
  Mutating the object ALWAYS does.

  normalise_dangerous: caller's data is now [{'text': 'hello'}, {'text': 'world'}]
    The function 'just normalised' and silently rewrote the input.
  normalise_safe     : returned [{'text': 'hello'}, {'text': 'world'}]
                       caller's data still [{'text': '  hello  '}, {'text': ' world '}]

----------------------------------------------------------------------
3. SCOPE - why assignment makes a name local
----------------------------------------------------------------------
  counter = 0                 # module level
  def broken_increment():
      counter = counter + 1   # <-- assignment makes counter LOCAL

  UnboundLocalError: cannot access local variable 'counter' where it is not associated with a value

  Python decided 'counter' is local for the WHOLE function because
  it is assigned somewhere in the body. So the read on the right
  happens before any local value exists.

  Better than 'global': take it in, return it out.
    n after three increments: 3

----------------------------------------------------------------------
4. KEYWORD-ONLY PARAMETERS - making an API hard to misuse
----------------------------------------------------------------------
  def search(query, *, k=5, rerank=False)

  search('refunds', k=10, rerank=True)
    -> query='refunds' k=10 rerank=True

  search('refunds', 10, True)
    -> TypeError: search() takes 1 positional argument but 3 were given

  That TypeError is the feature. 'search(q, 10, True)' tells a
  reader nothing, and swapping two positional flags is a silent bug.

----------------------------------------------------------------------
5. VALIDATION AT THE BOUNDARY
----------------------------------------------------------------------
  text = 'abcdefghijklmnopqrstuvwxy' (25 chars)

  chunk_text(size=10, overlap=3) -> ['abcdefghij', 'hijklmnopq', 'opqrstuvwx', 'vwxy']
  chunk start positions: [0, 7, 14, 21]

  Now the failures the validation catches:
    size=10, overlap=10 -> ValueError: overlap (10) must be less than size (10)
    size=10, overlap=15 -> ValueError: overlap (15) must be less than size (10)
    size=0, overlap=0 -> ValueError: size must be positive, got 0

  WITHOUT the validation:
    overlap == size -> ValueError: range() arg 3 must not be zero
      An obscure error from deep inside range(). At least it fails.
    overlap  > size -> returned []
      NO ERROR. It returns an empty list. Every document produces
      zero chunks, your index is empty, retrieval finds nothing,
      and nothing anywhere reported a problem. THIS is why you
      validate at the boundary.

  Docstrings are real objects: chunk_text.__doc__ is 492 characters long.

======================================================================
```

### 7.3 Reading the result

**The buggy version prints the same `id` three times.** That is the proof: not "a list that looks
similar" but literally the same object in memory, created once when the `def` line executed and
handed to every call that omits the argument. It grew `['a'] → ['a','b'] → ['a','b','c']` across
three unrelated calls.

**The fixed version prints three distinct ids**, and the lab deliberately keeps all three alive to
show that. (If it did not, CPython would free each list immediately and reuse the same address,
making the ids look identical for a completely different reason — a nice illustration of why `id()`
is only meaningful for objects you are holding.)

**Note the last part of section 1:** passing a deliberately empty list returns *that same object*
(`same object: True`). The `is None` check distinguishes "not supplied" from "supplied as empty". Had
the fix used `if not tags:`, the caller's list would have been silently discarded and replaced — the
M2-L02 truthiness bug, in a new costume.

**Section 2 shows the mutation danger concretely.** `normalise_dangerous` returns the right answer
*and* rewrites the caller's dictionaries in place. The caller now has stripped text they never asked
to change, and nothing indicated it. `normalise_safe` returns new dicts and leaves
`[{'text': '  hello  '}, {'text': ' world '}]` untouched.

**Section 5 is the one to remember.** Three ways to call `chunk_text` badly:

| Call | Without validation | With validation |
|---|---|---|
| `overlap == size` | `ValueError: range() arg 3 must not be zero` — obscure, but at least it fails | `ValueError: overlap (10) must be less than size (10)` |
| `overlap > size` | **Returns `[]`. No error at all.** | `ValueError: overlap (15) must be less than size (10)` |
| `size = 0` | Same obscure `range` error | `ValueError: size must be positive, got 0` |

The middle row is the important one. A one-character configuration mistake makes every document
produce zero chunks. Your ingestion pipeline reports success, your index is empty, retrieval returns
nothing, and the first symptom is a user complaining that the assistant knows nothing — days later,
with no error anywhere in the logs.

**Three lines of validation converted a silent, delayed, catastrophic failure into an immediate one
that names the offending value.** That is the habit this lesson exists to install, and it recurs in
M5-L07, M7-L06 and M8-L05.

**Verification:** confirm the buggy ids are identical, the fixed ids are distinct, chunk starts are
`[0, 7, 14, 21]`, and `overlap > size` without validation returns `[]`.

---

## 8. Common mistakes and troubleshooting

1. **Mutable default arguments.** Use `None`.
2. **Computed defaults** like `datetime.now()`. Evaluated once at import.
3. **Mutating an argument without saying so.** Return new data by default.
4. **Boolean positional arguments.** Use keyword-only.
5. **Assigning to a global without `global`** → `UnboundLocalError`.
6. **Returning more than three values as a tuple.** Use a dataclass.
7. **Silently clamping invalid input** instead of raising.
8. **Believing type hints are enforced.** They are not (M2-L08).

| Error | Cause | Fix |
|---|---|---|
| `TypeError: f() takes 2 positional arguments but 3 were given` | Passing a keyword-only argument positionally | Name it |
| `UnboundLocalError: cannot access local variable 'x'` | Assigning to a name also read from an outer scope | Pass it in and return it |
| A list grows between unrelated calls | Mutable default | `=None`, create inside |
| Caller's data changed unexpectedly | Function mutated an argument | Build and return new objects |
| `TypeError: f() missing 1 required keyword-only argument` | Omitted a required named argument | Pass it by name |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** A mutable default is a **shared mutable global** with an innocent appearance. Under
  concurrency (M2-L13) it becomes a data race between unrelated requests. In a long-running FastAPI
  process it accumulates for the lifetime of the server.
- **Security.** A mutable default that accumulates across calls can leak data **between users** — a
  cache or list that one request populates and the next request reads. This is a genuine
  multi-tenancy vulnerability, not a style issue (M7-L15).
- **Reliability.** Validate at the boundary and raise with the offending value in the message. The
  `overlap >= size` case in §6 is a real example where the alternative is a silently empty index.
- **Privacy.** Do not put user data in default values or module-level state. It outlives the request.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Predict the output, then run it:

```python
def f(x, acc=[]):
    acc.append(x)
    return acc

print(f(1)); print(f(2)); print(f(3))

def g(items):
    items = items + [99]
    return items
def h(items):
    items.append(99)
    return items

a = [1]; g(a); print(a)
b = [1]; h(b); print(b)
```

Explain each result in one sentence.

### Exercise 2 — Intermediate (~25 min)

Rewrite this function to fix every problem you can find:

```python
def process(data, filters={}, verbose=False, strict=False, retries=3):
    for d in data:
        d['processed'] = True
    return data
```

Your version must: use no mutable defaults; not mutate the caller's data; make the three flags
keyword-only; have type hints; have a docstring stating whether input is modified; and validate
`retries`. Write three tests proving the caller's data is untouched.

### Exercise 3 — Challenge (~25 min)

1. Implement `chunk_text` from §6 yourself, then verify: `size=10, overlap=3` on a 25-character
   string produces chunks whose starts are 0, 7, 14, 21.
2. Show what happens with `overlap=size` if you remove the validation. Record the exact error.
3. Show what happens with `overlap > size` if you remove the validation. This one is worse than an
   error — explain why.
4. Write a `make_counter()` function returning a closure that increments and returns a count on each
   call, without using `global`. Explain which scope the counter lives in.
5. A colleague's function signature is `def send(msg, urgent, retry, silent, log)`. Rewrite the
   signature to be hard to misuse and explain each change in one line.

---

## 11. Quiz

**Q1.** `def f(x, acc=[]): acc.append(x); return acc`. What does the third call `f(3)` return?

- A. `[3]`  B. `[1, 2, 3]` — the default list is created once and shared by every call
- C. `[]`  D. Raises an error

**Q2.** Why is `tags=None` plus `if tags is None: tags = []` the correct fix?

- A. `None` is faster.
- B. It creates a fresh list on every call, and `is None` correctly distinguishes "not supplied" from
  a deliberately passed empty list.
- C. `[]` is not a valid default.
- D. It avoids type errors.

**Q3.** `def rebind(items): items = [9]`. After `data = [1,2]; rebind(data)`, what is `data`?

- A. `[9]`  B. `[1, 2]` — reassigning a parameter rebinds only the local name
- C. `[1, 2, 9]`  D. `None`

**Q4.** What does the bare `*` do in `def search(q, *, k=5, rerank=False)`?

- A. Collects extra positional arguments.
- B. Makes `k` and `rerank` keyword-only, so they cannot be passed positionally.
- C. Marks them as optional.
- D. Unpacks a list.

**Q5.** Why is making boolean options keyword-only good API design?

- A. It is faster.
- B. `search(q, True, False)` tells a reader nothing and allows silent argument swaps;
  `search(q, rerank=True, strict=False)` is self-documenting and cannot be reordered wrongly.
- C. Booleans cannot be positional.
- D. It reduces memory use.

**Q6.** `count = 0; def inc(): count = count + 1`. What happens?

- A. `count` becomes 1.
- B. `UnboundLocalError` — assigning to `count` in the body makes it local for the whole function, so
  the read on the right-hand side has no value yet.
- C. Silently does nothing.
- D. `SyntaxError`

**Q7.** `def log(msg, ts=datetime.now())` — what is wrong?

- A. Nothing.
- B. The default is evaluated once when the function is defined, so every call gets the import-time
  timestamp.
- C. `datetime.now()` cannot be a default.
- D. It is too slow.

**Q8.** In §6, why must `overlap >= size` raise rather than being clamped?

- A. Clamping is slower.
- B. `overlap == size` makes the step 0 and `range` raises an obscure error, while `overlap > size`
  makes the step negative and the function silently returns an empty list — producing an empty index
  with no error anywhere.
- C. It is required by the type system.
- D. It does not need to raise.

**Q9.** Which is the safest default policy for a function receiving a list of dicts?

- A. Mutate them in place; it is faster.
- B. Build and return new objects, and if mutation is genuinely required, say so in the name and
  docstring.
- C. Always `deepcopy` everything.
- D. Use a global.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why a mutable default argument is a
security concern in a long-running web server, not merely a style issue.

---

## 12. Revision notes

- `def name(params) -> Type:` with a **docstring** first. Docstrings are runtime objects.
- Parameter kinds: positional-or-keyword · defaults · `*args` · **keyword-only after `*`** ·
  `**kwargs`. `/` makes parameters positional-only.
- **Use `*` for any function with optional flags.** Boolean positionals are unreadable and swappable.
- **Defaults are evaluated once, at definition time.** Never `[]`, `{}`, `set()`, an object, or
  `datetime.now()`. Use `None` and create inside.
- **Reassigning a parameter never affects the caller; mutating the object always does.**
- Default to **not mutating arguments**. Return new data; name it if you must mutate.
- **LEGB**: Local → Enclosing → Global → Built-in. Assignment makes a name local for the whole
  function → `UnboundLocalError`. Prefer parameters and return values to `global`/`nonlocal`.
- `return a, b` is one tuple. Beyond three values, use a dataclass or model.
- **Guard clauses** over nested `if/else`.
- **Validate at the boundary and raise with the offending value.** Silent clamping hides
  catastrophic failures.
- Type hints are **not enforced at runtime**.

---

## 13. Completion checklist

- [ ] I predicted Exercise 1 correctly and can explain each result.
- [ ] I can write the mutable-default fix from memory.
- [ ] I can state the rebind-vs-mutate rule precisely.
- [ ] I use keyword-only parameters for optional flags by default.
- [ ] I implemented `chunk_text` and verified the chunk start positions.
- [ ] I saw what `overlap > size` does without validation.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "Defining Functions".
  <https://docs.python.org/3/tutorial/controlflow.html#defining-functions> `[UNVERIFIED]`
- PEP 3102 — keyword-only arguments. <https://peps.python.org/pep-3102/> `[UNVERIFIED]`
- PEP 257 — docstring conventions. <https://peps.python.org/pep-0257/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L06 — Modules, Packages and Project Layout](M2-L06-modules-packages.md)

You can write functions. Next: how to organise them into files and packages, and the import rules
that decide whether `from app.services import retrieve` works or raises.
