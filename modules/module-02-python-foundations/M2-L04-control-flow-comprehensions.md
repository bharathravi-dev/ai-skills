# M2-L04 — Conditions, Loops and Comprehensions

| | |
|---|---|
| **Lesson ID** | M2-L04 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L03](M2-L03-collections.md) |

---

## 1. Learning objectives

1. **Write** conditionals and loops using Python's indentation-based blocks.
2. **Use** `enumerate`, `zip`, `range` and `items()` instead of index arithmetic.
3. **Convert** a loop to a comprehension and **decide** when *not* to.
4. **Use** generator expressions and **explain** the memory difference.
5. **Avoid** the four classic loop bugs: mutation during iteration, late binding, `else` on loops,
   and unbounded memory from list building.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Block** | A group of statements. Delimited by **indentation**, not braces. |
| **Iterable** | Anything you can loop over: list, tuple, dict, set, string, file, generator. |
| **Iterator** | An object producing items one at a time, consumed once. |
| **Comprehension** | Compact syntax building a list, dict or set from an iterable. |
| **Generator expression** | Like a comprehension but produces items lazily, one at a time. |
| **Lazy evaluation** | Computing values only when needed. |
| **`enumerate`** | Yields `(index, item)` pairs. |
| **`zip`** | Yields tuples pairing items from several iterables. |
| **Walrus operator** (`:=`) | Assigns a value inside an expression. |
| **Guard clause** | An early `return`/`continue` that removes nesting. |
| **Late binding** | A closure capturing a *variable*, not its value at creation time. |

---

## 3. Plain-language explanation

Python's control flow is conventional. Two things are different from what you are used to, and one
of them is genuinely important.

**Indentation is syntax.** No braces. The indentation *is* the block:

```python
if score > 0.8:
    print("high")
    print("still inside the if")
print("outside")
```

Use 4 spaces. Never mix tabs and spaces — Python will reject the file. Any editor configured for
Python handles this; just do not fight it.

**Iterate over things, not indices.** This is the important one. Coming from JavaScript or Java you
may write:

```python
for i in range(len(items)):        # works, but not idiomatic
    print(items[i])
```

Python wants:

```python
for item in items:                 # idiomatic
    print(item)
```

And when you genuinely need the index:

```python
for index, item in enumerate(items):
    print(f"{index}: {item}")
```

`range(len(x))` in Python code is a reliable signal that someone is writing another language in
Python syntax. There is almost always a better tool: `enumerate` for indices, `zip` for parallel
lists, `.items()` for dicts.

### JavaScript comparison

| JavaScript | Python |
|---|---|
| `if (x) { } else if (y) { } else { }` | `if x: ... elif y: ... else: ...` |
| `for (const x of arr)` | `for x in arr:` |
| `arr.forEach((x, i) => ...)` | `for i, x in enumerate(arr):` |
| `arr.map(f)` | `[f(x) for x in arr]` |
| `arr.filter(p)` | `[x for x in arr if p(x)]` |
| `arr.map(f).filter(p)` | `[f(x) for x in arr if p(x)]` — one pass |
| `Object.entries(o)` | `o.items()` |
| `x ? a : b` | `a if x else b` — **note the order** |
| `&&` `\|\|` `!` | `and` `or` `not` |
| `break` / `continue` | Same |

The ternary order catches everyone: Python puts the *value first*, then the condition.

---

## 4. Analogy

**A comprehension is a factory line description.**

`[clean(t) for t in tickets if t.is_open]` reads as: *"take each ticket, keep the open ones, clean
them, collect the results."* One line, one pass, no accumulator variable to mismanage.

### Where the analogy breaks

1. **A factory line can be arbitrarily long; a comprehension should not be.** Two conditions and a
   nested loop in one comprehension is unreadable. The moment you have to re-read it, use a loop.
2. **The line runs continuously; a list comprehension runs to completion immediately** and holds
   everything in memory. A *generator* expression is the one that behaves like a real line, producing
   items on demand.
3. **The analogy hides the ordering.** In a nested comprehension the loops read **left to right in
   the same order you would nest them** — which is the opposite of what most people guess. §5.4.

---

## 5. Detailed technical explanation

### 5.1 Conditions

```python
if score >= 0.9:
    grade = "A"
elif score >= 0.8:
    grade = "B"
else:
    grade = "C"

grade = "pass" if score >= 0.5 else "fail"     # ternary: value, condition, alternative
```

Chained comparisons work as mathematics does — and this is genuinely nicer than most languages:

```python
if 0 <= score <= 1:        # both bounds in one expression
if a < b < c:
```

Boolean operators are words: `and`, `or`, `not`. They **short-circuit**, and they return an
*operand*, not a boolean:

```python
name = user_name or "anonymous"     # returns user_name if truthy, else the default
```

That idiom is common and carries the M2-L02 truthiness trap: if `user_name` is `""`, you get
`"anonymous"`. For genuinely optional values use `if x is None`.

### 5.2 Loops

```python
for item in items: ...
for index, item in enumerate(items): ...
for index, item in enumerate(items, start=1): ...
for key, value in mapping.items(): ...
for a, b in zip(list_a, list_b): ...
for i in range(5): ...            # 0,1,2,3,4
for i in range(2, 10, 2): ...     # 2,4,6,8

while condition: ...
```

**`zip` stops at the shortest input.** That is silent data loss if the lists should have matched:

```python
zip([1,2,3], ["a","b"])                    # 2 pairs, third dropped SILENTLY
zip([1,2,3], ["a","b"], strict=True)       # raises ValueError (Python 3.10+)
```

**Use `strict=True` whenever the lengths ought to match.** This is exactly the `X`/`y` alignment
problem from M1-L04, and `strict=True` turns a silent bug into an exception.

`break` exits the loop; `continue` skips to the next iteration.

**Loop `else`** — runs only if the loop completed *without* `break`:

```python
for chunk in chunks:
    if chunk.matches(query):
        best = chunk
        break
else:
    best = None          # runs only if no break happened
```

It is genuinely useful for search loops, and genuinely confusing to read. Most style guides suggest
avoiding it; know what it means so you can read others' code.

### 5.3 Comprehensions

```python
squares      = [x * x for x in range(5)]                   # [0,1,4,9,16]
evens        = [x for x in range(10) if x % 2 == 0]        # filter
labelled     = [f"#{i}" for i in range(3)]                 # transform
pairs        = {k: len(v) for k, v in mapping.items()}     # dict comprehension
unique_words = {w.lower() for w in words}                  # set comprehension
```

With a conditional **expression** (note the position — before the `for`):

```python
[x if x > 0 else 0 for x in values]     # transform every item
[x for x in values if x > 0]            # filter items out
```

Those two are different operations and the syntax looks similar. `if` **after** the `for` filters;
`if/else` **before** the `for` transforms.

### 5.4 Nested comprehensions

```python
matrix = [[1, 2], [3, 4], [5, 6]]
flat = [value for row in matrix for value in row]      # [1,2,3,4,5,6]
```

Read the `for` clauses **left to right, exactly as you would nest them**:

```python
for row in matrix:
    for value in row:
        flat.append(value)
```

The output expression comes first but the loops read in normal order. Getting this backwards is the
single most common comprehension error.

**Two levels is the limit.** Three, or two plus conditions, should be a loop.

### 5.5 Generator expressions and memory

Round brackets instead of square:

```python
squares_list = [x * x for x in range(10_000_000)]     # builds 10M items in RAM
squares_gen  = (x * x for x in range(10_000_000))     # builds nothing yet
```

The generator computes items **one at a time as you consume them**. For an aggregate you never need
the list:

```python
total = sum(x * x for x in range(10_000_000))     # constant memory
```

**Where this matters in this course:** processing documents in Module 7. A list comprehension over
100,000 chunks holds all of them in memory; a generator streams them. The lab measures the
difference and it is large.

**The catch: a generator is consumed once.**

```python
gen = (x for x in range(3))
list(gen)      # [0, 1, 2]
list(gen)      # []   <- already exhausted
```

This causes real confusion — you iterate, it works; you iterate again and get nothing, with no error.

Useful functions that take any iterable: `sum`, `min`, `max`, `any`, `all`, `sorted`, `len` (lists
only). `any` and `all` **short-circuit**, so `any(is_bad(x) for x in huge)` stops at the first match.

### 5.6 The walrus operator

```python
if (n := len(items)) > 100:
    print(f"too many: {n}")           # n is available here
```

Assign and test in one expression. Use sparingly — it is easy to make unreadable — but it is genuinely
good for avoiding a duplicate function call.

### 5.7 The four classic bugs

**Bug 1 — mutating a list while iterating it.**

```python
items = [1, 2, 3, 4]
for x in items:
    if x % 2 == 0:
        items.remove(x)      # BUG - skips elements
# result: [1, 3, 4]  -- 4 survived
```

The iterator holds an index into a list whose length is changing underneath it. **Build a new list
instead:** `items = [x for x in items if x % 2 != 0]`.

**Bug 2 — late binding in closures.**

```python
funcs = [lambda: i for i in range(3)]
[f() for f in funcs]        # [2, 2, 2]  -- not [0, 1, 2]
```

Each lambda captured the *variable* `i`, not its value. After the loop, `i` is 2. **Fix with a
default argument:** `[lambda i=i: i for i in range(3)]`.

**Bug 3 — building a huge list when you only need an aggregate.** Use a generator.

**Bug 4 — `zip` silently truncating.** Use `strict=True`.

### 5.8 Assumptions and limitations

- Comprehensions have their own scope, so the loop variable does not leak (unlike Python 2).
- `zip(..., strict=True)` requires Python 3.10+.
- Generators cannot be indexed, have no `len()`, and cannot be reused.
- A comprehension is not always faster than a loop; it is usually *slightly* faster and always more
  declarative. Choose for readability first.

---

## 6. Worked example — scoring and filtering search results

Take a raw result set and produce a ranked, filtered, formatted output. This is the shape of code you
will write repeatedly in Modules 6 and 7.

**The data:**

```python
results = [
    {"id": "doc-001", "score": 0.91, "source": "policy", "text": "Refunds within 5 days."},
    {"id": "doc-002", "score": 0.44, "source": "blog",   "text": "Our shipping story."},
    {"id": "doc-003", "score": 0.78, "source": "policy", "text": "Returns need a receipt."},
    {"id": "doc-004", "score": 0.12, "source": "policy", "text": "Office opening hours."},
]
```

**Step 1 — filter by threshold. Loop version:**

```python
relevant = []
for r in results:
    if r["score"] >= 0.5:
        relevant.append(r)
```

**Comprehension version:**

```python
relevant = [r for r in results if r["score"] >= 0.5]
```

Three lines to one, no accumulator to initialise, and the intent is on one line. This is the case
where a comprehension is unambiguously better.

**Step 2 — two conditions.**

```python
relevant = [r for r in results if r["score"] >= 0.5 and r["source"] == "policy"]
```

Still fine. Adding a third condition would push it past comfortable — at that point extract a
predicate function:

```python
def is_relevant(r) -> bool:
    return r["score"] >= 0.5 and r["source"] == "policy" and len(r["text"]) > 10

relevant = [r for r in results if is_relevant(r)]
```

**This is the judgement the lesson is teaching.** The comprehension stays readable because the
complexity moved into a named function that can be tested independently.

**Step 3 — rank, with the tie-break from M2-L03.**

```python
ranked = sorted(relevant, key=lambda r: (-r["score"], r["id"]))
```

**Step 4 — number them for display.**

```python
lines = [
    f"{i}. [{r['score']:.2f}] {r['id']}: {r['text'][:40]}"
    for i, r in enumerate(ranked, start=1)
]
```

`enumerate(ranked, start=1)` gives 1-based numbering without index arithmetic. Note the nested
quotes: the f-string uses double quotes so `r['score']` uses single ones.

**Step 5 — aggregate without building a list.**

```python
total_score = sum(r["score"] for r in ranked)          # generator: no list built
any_low     = any(r["score"] < 0.6 for r in ranked)    # short-circuits at the first
all_policy  = all(r["source"] == "policy" for r in ranked)
```

**Step 6 — the token-budget loop**, where a comprehension is the *wrong* choice:

```python
budget = 100
selected, used = [], 0
for r in ranked:
    cost = len(r["text"])
    if used + cost > budget:
        break                 # stop as soon as the budget is exhausted
    selected.append(r)
    used += cost
```

This cannot be a comprehension: each decision depends on accumulated state from previous iterations,
and it needs to stop early. **Comprehensions are for independent per-item transformations.** Anything
carrying state forward is a loop. You will write exactly this loop in M7-L11 for context assembly.

---

## 7. Practical activity

**File:** [`labs/m2/l04_control_flow.py`](../../labs/m2/l04_control_flow.py)

```bash
python3 labs/m2/l04_control_flow.py
```

Works through the §6 pipeline, then demonstrates all four bugs with real output, then **measures**
list comprehension versus generator memory using `tracemalloc`.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `enumerate(ranked, start=1)` | 1-based numbering without index arithmetic. |
| `zip(a, b, strict=True)` | Raises instead of silently truncating. The M1-L04 alignment bug, caught. |
| `tracemalloc.get_traced_memory()` | Measures actual Python memory allocation — real evidence, not an estimate. |
| `sum(x for x in ...)` | Generator argument: no intermediate list. |
| `[lambda i=i: i for i in range(3)]` | Default argument binds the value *now*, fixing late binding. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Memory figures are real `tracemalloc` measurements:

```
======================================================================
CONTROL FLOW, COMPREHENSIONS AND GENERATORS
======================================================================

----------------------------------------------------------------------
1. THE SEARCH-RESULT PIPELINE
----------------------------------------------------------------------
  filtered (score >= 0.5)   : ['doc-001', 'doc-003']
  + source == 'policy'      : ['doc-001', 'doc-003']
  ranked (score desc, id)   : ['doc-001', 'doc-003']

  formatted with enumerate(start=1):
    1. [0.91] doc-001: Refunds within 5 days.
    2. [0.78] doc-003: Returns need a receipt.

  aggregates WITHOUT building intermediate lists:
    sum of scores  = 1.69
    any below 0.6  = False
    all are policy = True

  The token-budget loop - which CANNOT be a comprehension:
    took doc-001   cost=22  used=22
    took doc-003   cost=23  used=45
    selected: ['doc-001', 'doc-003']
    Each decision depends on state accumulated so far, and it must
    stop early. Comprehensions do neither.

----------------------------------------------------------------------
2. BUG 1 - mutating a list while iterating it
----------------------------------------------------------------------
  start: [2, 4, 6, 8]   removing EVERY even number with .remove()
  correct answer: []

    sees 2, removes it -> list is now [4, 6, 8]
    sees 6, removes it -> list is now [4, 8]
  result: [4, 8]   <-- 4 and 8 SURVIVED. Every one should have gone.

  Why: the iterator walks POSITIONS 0, 1, 2, ... through a list whose
  length is shrinking underneath it.
    position 0 -> 2, removed. List becomes [4, 6, 8]; everything
                  shifted left, so 4 is now at position 0 - already
                  passed. It is skipped.
    position 1 -> 6, removed. List becomes [4, 8].
    position 2 -> past the end (len is 2). Loop stops.
  Half the list was never examined.

  fix - build a NEW list instead of mutating: []

  NOTE how easily this hides. With [1,2,3,4] the same bug returns
  [1,3] - which is the RIGHT answer, purely because the skipped
  element happened not to need removing. The bug is present and
  invisible. That is why the rule is absolute: never mutate a list
  you are iterating.

----------------------------------------------------------------------
3. BUG 2 - late binding in closures
----------------------------------------------------------------------
  [lambda: i for i in range(3)] -> [2, 2, 2]   <-- not [0,1,2]

  Each lambda captured the VARIABLE i, not its value. When they are
  finally called, the loop has finished and i is 2.

  fix A - default argument binds NOW : [0, 1, 2]
  fix B - a factory gives each its own scope: [0, 1, 2]

----------------------------------------------------------------------
4. BUG 3 - zip() truncating silently
----------------------------------------------------------------------
  features: 3 rows, labels: 2 rows
  zip() gave 2 pairs - the third example vanished SILENTLY
  No error. No warning. Your training set just lost a row.

  with strict=True -> ValueError: zip() argument 2 is shorter than argument 1

  This is the M1-L04 X/y alignment bug in Python form. Make
  strict=True your default whenever the lengths ought to match.

----------------------------------------------------------------------
5. BUG 4 - building a list you do not need
----------------------------------------------------------------------
  sum over 2,000,000 squares
    list comprehension   peak memory:   81,127,752 bytes (81.1 MB)
    generator expression peak memory:          464 bytes (0.5 KB)
    ratio: 174,844x less memory
    same answer? True

  The list version materialises 2 million integers to add them up
  and throw them away. The generator holds one at a time.
  In Module 7 the items are document chunks, not integers.

----------------------------------------------------------------------
6. GENERATORS ARE CONSUMED ONCE
----------------------------------------------------------------------
  first  list(gen) -> [0, 1, 2]
  second list(gen) -> []   <-- empty, and NO error

  This is why a function returning a generator can work the first
  time a caller uses it and silently return nothing the second.

======================================================================
```

### 7.3 Reading the result

**The mutation bug is worse than it looks.** Removing every even number from `[2, 4, 6, 8]` leaves
`[4, 8]` — half the list untouched. The trace shows exactly why: after removing `2`, everything
shifts left, so `4` moves into position 0 which the iterator has already passed.

But read the closing note carefully. The *same bug* applied to `[1, 2, 3, 4]` returns `[1, 3]` —
**the correct answer**, purely because the element it skipped happened not to need removing. The
defect is fully present and completely invisible. That is why the rule is absolute rather than
situational: never mutate a list you are iterating, even when the output looks right.

**The memory measurement is the most consequential number in this lesson:**

| | Peak memory |
|---|---|
| `sum([x*x for x in range(2_000_000)])` | **81,127,752 bytes** (81.1 MB) |
| `sum(x*x for x in range(2_000_000))` | **464 bytes** |

**174,844×.** Identical answers. One bracket different. The list version materialises two million
integers in order to add them up and immediately discard them; the generator holds one at a time.

This is not a micro-optimisation and it is not theoretical. In Module 7 you will iterate over
document chunks rather than integers, on an instance with a fixed memory limit, and the list version
is how a pipeline that works on 1,000 documents dies on 100,000.

**The `zip` demonstration** is M1-L04's alignment bug reproduced in Python: 3 feature rows, 2 labels,
and `zip` silently produces 2 pairs. A training example vanished, no error was raised, and the model
would simply train on less data than you believe it has. `strict=True` turns that into a `ValueError`
naming the mismatch.

**And the generator exhaustion demo:** `list(gen)` returns `[0, 1, 2]` and then `[]`. No exception,
no warning. A function that returns a generator will work for the first consumer and silently give
nothing to the second.

**Verification:** confirm the mutation result is `[4, 8]`, the memory ratio is roughly 175,000×, and
`strict=True` raises `ValueError`.

---

## 8. Common mistakes and troubleshooting

1. **`for i in range(len(items))`.** Use `enumerate` or iterate directly.
2. **Mutating a list while iterating it.** Build a new one.
3. **`zip` without `strict=True`** when lengths should match.
4. **Comprehension doing too much.** Extract a predicate or use a loop.
5. **Reusing an exhausted generator.**
6. **Late binding in a loop of lambdas.**
7. **Building a list when you only need a sum or an `any`.**
8. **Ternary order.** `a if cond else b`, not `cond ? a : b`.
9. **Mixing tabs and spaces.**
10. **`if/else` before `for` versus `if` after** — transform versus filter.

| Error | Cause | Fix |
|---|---|---|
| `IndentationError: unexpected indent` | Inconsistent indentation | Use 4 spaces everywhere |
| `TabError: inconsistent use of tabs and spaces` | Mixed | Convert tabs to spaces |
| `ValueError: zip() argument 2 is shorter` | `strict=True` caught a length mismatch | Good — fix the data |
| Loop silently processes fewer items | `zip` truncation | `strict=True` |
| Elements skipped when removing | Mutation during iteration | Comprehension to build a new list |
| Second iteration yields nothing | Generator exhausted | Build a list, or recreate the generator |
| All closures return the same value | Late binding | `lambda x=x: ...` |
| `MemoryError` on a large dataset | List comprehension over everything | Generator expression |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** `zip(strict=True)` converts a silent data-corruption bug into an exception. Given
  M1-L04's alignment lesson, make it your default.
- **Cost / memory.** In Module 7 you will iterate over document chunks. A list comprehension over a
  large corpus can exhaust memory on a small instance; a generator streams in constant memory. This
  is a real deployment failure, not a theoretical one.
- **Security.** `any()`/`all()` short-circuit, which means the *time taken* can reveal where a match
  occurred. Irrelevant for search; relevant if you ever compare secrets — use
  `hmac.compare_digest` for that (M2-L19).
- **Privacy.** A comprehension over user records is an easy way to build a log line containing
  everything. Project only the fields you need.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Rewrite each loop as a comprehension:

```python
# 1
out = []
for x in range(10):
    if x % 3 == 0:
        out.append(x * 2)

# 2
lengths = {}
for word in ["alpha", "be", "gamma"]:
    lengths[word] = len(word)

# 3
initials = set()
for name in ["Ann", "Bob", "Amy"]:
    initials.add(name[0])

# 4  -- careful: should this be a comprehension at all?
total = 0
for x in [1, 2, 3, 4]:
    total += x
```

For #4, state what you would actually write and why.

### Exercise 2 — Intermediate (~25 min)

Using the `results` data from §6:

1. Produce `list[str]` of IDs with score above 0.5, sorted by score descending with an ID tie-break.
2. Produce `dict[str, int]` mapping source → number of results from that source.
3. Produce a set of every distinct word (lowercased, punctuation stripped) across all `text` fields.
4. Compute the mean score **without building an intermediate list**.
5. Write the token-budget loop from §6 step 6 with a budget of 60 characters, and explain in one
   sentence why it cannot be a comprehension.

### Exercise 3 — Challenge (~25 min)

1. Reproduce the mutation-during-iteration bug. Print the result and explain precisely which element
   was skipped and why.
2. Reproduce the late-binding bug and fix it in **two** different ways. Explain what each fix does.
3. Use `tracemalloc` to measure the peak memory of `sum([x*x for x in range(2_000_000)])` versus
   `sum(x*x for x in range(2_000_000))`. Report both figures and the ratio.
4. Write `first_match(items, predicate)` returning the first matching item or `None`, using loop
   `else`. Then rewrite it with `next()` and a generator expression. State which you would ship and
   why.
5. Take the `zip` truncation bug: write code where two lists of different lengths are zipped and the
   mismatch causes a *plausible but wrong* result rather than an obvious error. This is the M1-L04
   lesson in Python form.

---

## 11. Quiz

**Q1.** What is the idiomatic way to loop with an index?

- A. `for i in range(len(items)):`  B. `for i, item in enumerate(items):`
- C. `for item in items.keys():`  D. `while i < len(items):`

**Q2.** What does `zip([1,2,3], ["a","b"])` produce, and how do you make the mismatch an error?

- A. 3 pairs; there is no way to detect it.
- B. 2 pairs, silently dropping the third; add `strict=True` (Python 3.10+) to raise `ValueError`.
- C. Raises immediately.
- D. 3 pairs with `None` padding.

**Q3.** What is the difference between `[x for x in v if p(x)]` and `[x if p(x) else 0 for x in v]`?

- A. They are identical.
- B. The first filters (output may be shorter); the second transforms every item (output is
  the same length).
- C. The second is faster.
- D. The first is invalid syntax.

**Q4.** `flat = [v for row in matrix for v in row]` — in what order do the `for` clauses execute?

- A. Right to left, innermost first.
- B. Left to right, in the same order you would nest the loops.
- C. Simultaneously.
- D. It is undefined.

**Q5.** Why does `sum(x*x for x in range(10_000_000))` use far less memory than
`sum([x*x for x in range(10_000_000)])`?

- A. The generator uses a faster algorithm.
- B. The generator produces values one at a time as `sum` consumes them, so no intermediate list is
  ever built.
- C. `sum` optimises brackets away.
- D. There is no difference.

**Q6.** `funcs = [lambda: i for i in range(3)]; [f() for f in funcs]` gives what, and why?

- A. `[0,1,2]` — each lambda captured its value.
- B. `[2,2,2]` — each lambda captured the *variable* `i`, which is 2 after the loop ends.
- C. `[0,0,0]`
- D. Raises an error.

**Q7.** Why does removing items from a list while iterating it skip elements?

- A. Lists cannot be modified.
- B. The iterator advances through positions in a list whose length is shrinking, so removing the
  element at the current position causes the next one to be skipped.
- C. `remove` is broken.
- D. It does not skip elements.

**Q8.** Which task **cannot** reasonably be written as a comprehension?

- A. Doubling every number in a list.
- B. Filtering records above a threshold.
- C. Selecting documents until a cumulative token budget is exhausted, then stopping.
- D. Building a dict of word lengths.

**Q9.** A generator yields nothing on a second iteration. Why?

- A. It raised an error silently.
- B. Generators are consumed once; after exhaustion they yield nothing further, with no error.
- C. The variable was reassigned.
- D. Generators only work inside functions.

**Q10.** *(Written, rubric-graded.)* In under 70 words, give your rule for when to use a
comprehension and when to use an explicit loop.

---

## 12. Revision notes

- **Indentation is syntax.** 4 spaces, never mixed with tabs.
- Iterate over things, not indices. `enumerate` for index, `zip` for parallel, `.items()` for dicts.
  **`range(len(x))` is a smell.**
- **`zip(..., strict=True)`** — make it your default; silent truncation is the M1-L04 alignment bug.
- Ternary is `a if cond else b`. Booleans are `and or not` and they return an *operand*.
- Chained comparisons work: `0 <= x <= 1`.
- Comprehensions: `[f(x) for x in xs if p(x)]`. **`if` after `for` filters; `if/else` before `for`
  transforms.** Nested `for`s read left to right.
- **Generators** `( ... )` are lazy and constant-memory, but **consumed once**. Use with `sum`,
  `any`, `all`, `min`, `max`.
- Four bugs: mutate-while-iterating · late binding (`lambda i=i:`) · building lists you do not need ·
  `zip` truncation.
- **Comprehensions are for independent per-item work.** Anything with accumulated state or early
  exit is a loop.
- Loop `else` runs only if no `break` occurred. Know it; rarely write it.

---

## 13. Completion checklist

- [ ] I converted all four Exercise 1 loops and justified #4.
- [ ] I use `enumerate`/`zip`/`.items()` rather than index arithmetic.
- [ ] I made `strict=True` a habit.
- [ ] I reproduced and can explain all four classic bugs.
- [ ] I measured the generator memory difference myself.
- [ ] I can state when a comprehension is the wrong tool.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "More Control Flow Tools".
  <https://docs.python.org/3/tutorial/controlflow.html> `[UNVERIFIED]`
- Python docs, "List Comprehensions".
  <https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions> `[UNVERIFIED]`
- PEP 572 — the walrus operator. <https://peps.python.org/pep-0572/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L05 — Functions, Arguments, Scope and Return Values](M2-L05-functions-scope.md)

Next: functions — and the mutable-default-argument bug, which is the single most famous Python
gotcha and one you will meet in real codebases.
