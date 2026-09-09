# M2-L03 — Collections: list, tuple, dict, set

| | |
|---|---|
| **Lesson ID** | M2-L03 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L02](M2-L02-variables-strings.md) |

---

## 1. Learning objectives

1. **Choose** the correct container for a given job and **justify** it by mutability and lookup cost.
2. **Use** the core operations of each container, including safe dictionary access.
3. **Explain** why `set` and `dict` lookups are O(1) while `list` membership is O(n), and
   **estimate** the practical impact.
4. **Predict** and **avoid** the aliasing and shallow-copy bugs.
5. **Apply** `Counter`, `defaultdict` and `dict` ordering guarantees.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **`list`** | An ordered, mutable sequence. `[1, 2, 3]` |
| **`tuple`** | An ordered, **immutable** sequence. `(1, 2, 3)` |
| **`dict`** | A mapping from keys to values. `{"a": 1}` |
| **`set`** | An unordered collection of unique values. `{1, 2, 3}` |
| **Mutable** | Can be changed in place after creation. |
| **Hashable** | Has a stable hash value, so it can be a `dict` key or `set` member. Immutable built-ins are hashable. |
| **O(1)** | Constant time — cost does not grow with collection size. |
| **O(n)** | Linear time — cost grows in proportion to size. |
| **Shallow copy** | A new container holding references to the *same* inner objects. |
| **Deep copy** | A new container with recursively copied inner objects. |
| **Aliasing** | Two names referring to the same object. |
| **`Counter`** | A `dict` subclass that counts occurrences. |
| **`defaultdict`** | A `dict` that creates a default value for a missing key. |
| **Unpacking** | Assigning several names from one sequence: `a, b = pair`. |

---

## 3. Plain-language explanation

Four containers. Choosing correctly is mostly about answering two questions:

1. **Does it need to change after creation?** No → `tuple`. Yes → `list`.
2. **Do I look things up by a key or test membership?** Yes → `dict` or `set`.

That is genuinely most of it.

| Container | Ordered | Mutable | Duplicates | Lookup by | Use for |
|---|---|---|---|---|---|
| `list` | Yes | Yes | Yes | Position | A sequence you will modify |
| `tuple` | Yes | **No** | Yes | Position | A fixed record; a dict key |
| `dict` | Yes (insertion) | Yes | Keys unique | **Key** | Named lookup |
| `set` | **No** | Yes | **No** | **Membership** | Uniqueness and fast "is it in here?" |

### If you know JavaScript

| JavaScript | Python | Note |
|---|---|---|
| `Array` | `list` | `push`→`append`, `shift`→`pop(0)`, `length`→`len()` |
| — | `tuple` | **No JS equivalent.** Immutable, and usable as a dict key |
| `Object` / `Map` | `dict` | `dict` keys can be any hashable type, not just strings |
| `Set` | `set` | Similar, with real set algebra operators |
| `obj.key` | `d["key"]` | **No dot access on dicts.** `d.key` looks for an attribute |
| `obj.key` → `undefined` | `d["key"]` → **`KeyError`** | ⚠️ Python raises. Use `d.get("key")` for the JS behaviour |

The `KeyError` row is the one that will bite you first. In JavaScript a missing property is
`undefined` and your code limps on; in Python it raises immediately. That is better — the failure is
at the cause, not three functions later — but it changes how you write access code.

---

## 4. Analogy

- **`list`** — a numbered row of boxes. Add, remove, reorder.
- **`tuple`** — a sealed envelope containing several things in a fixed order. You cannot change it,
  which is why it is safe to use as a label on another container.
- **`dict`** — a filing cabinet with labelled folders. Go straight to the label.
- **`set`** — a guest list. Someone is either on it or not; asking twice adds nothing.

### Where the analogy breaks

1. **The filing cabinet suggests searching. A `dict` does not search.** It computes a hash of the key
   and jumps directly to the slot. That is why it is O(1) — the cabinet's size does not matter.
2. **The sealed envelope is not fully sealed.** A `tuple` is shallowly immutable: `t = ([1], 2)`
   forbids replacing element 0, but `t[0].append(9)` works, because the *list inside* is still
   mutable. This also means such a tuple is **not hashable** and cannot be a dict key.
3. **The guest list implies order.** Sets have none, and iteration order can vary between runs for
   some types. Never rely on set ordering.
4. **All four analogies hide aliasing.** Copying a name never copies the container (§5.5).

---

## 5. Detailed technical explanation

### 5.1 `list`

```python
items = ["a", "b", "c"]

items.append("d")           # add to end
items.insert(0, "z")        # insert at position
items.extend(["e", "f"])    # add several
items.remove("b")           # remove first matching VALUE (ValueError if absent)
last = items.pop()          # remove and return last
first = items.pop(0)        # remove and return first  -- O(n)
items[0] = "Z"              # assign by index
len(items)                  # length
"a" in items                # membership -- O(n), scans the list
items.sort()                # sort IN PLACE, returns None
new = sorted(items)         # returns a NEW sorted list
items.reverse()             # in place
items.index("c")            # first position of a value
items.count("a")            # occurrences
```

**The trap:** `sort()` mutates and returns `None`; `sorted()` returns a new list.

```python
items = [3, 1, 2].sort()    # items is None  <- classic bug
items = sorted([3, 1, 2])   # [1, 2, 3]      <- correct
```

This applies to `append`, `extend`, `insert`, `remove`, `reverse` too — **methods that mutate return
`None`.** If you find yourself assigning the result of one of these, you have a bug.

Sorting with a key:

```python
people = [("bharath", 41), ("sam", 29), ("kim", 35)]
sorted(people, key=lambda p: p[1])                # by age ascending
sorted(people, key=lambda p: p[1], reverse=True)  # descending
sorted(people, key=lambda p: (-p[1], p[0]))       # age desc, then name asc
```

The last form — a tuple key — is how you sort by several fields at once. You will use it constantly
for ranking results in Module 6.

### 5.2 `tuple`

```python
point = (3, 4)
x, y = point                # unpacking
single = (5,)               # NOTE the trailing comma - (5) is just the integer 5
```

Use a tuple when:

- The collection is a **fixed record**: `(latitude, longitude)`, `(status_code, body)`.
- You need a **dict key** or a **set member** — lists are unhashable, tuples are hashable.
- You are returning several values: `return name, score` returns a tuple.

```python
cache: dict[tuple[str, int], float] = {}
cache[("query", 5)] = 0.87        # tuple key: fine
# cache[["query", 5]] = 0.87      # TypeError: unhashable type: 'list'
```

That pattern — a compound cache key — is exactly what you will build in M5-L16.

### 5.3 `dict`

```python
user = {"name": "Bharath", "role": "lead"}

user["name"]                  # 'Bharath'
user["missing"]               # KeyError!
user.get("missing")           # None       - no exception
user.get("missing", "n/a")    # 'n/a'      - with a default
user["email"] = "x@y.z"       # add or update
del user["email"]             # remove (KeyError if absent)
user.pop("email", None)       # remove safely, with a default
"name" in user                # membership on KEYS - O(1)
len(user)

user.keys()                   # view of keys
user.values()                 # view of values
user.items()                  # view of (key, value) pairs
```

Iterating:

```python
for key in user:                        # keys by default
    ...
for key, value in user.items():         # the idiomatic form
    print(f"{key}: {value}")
```

**Ordering.** Since Python 3.7, `dict` preserves **insertion order** as a language guarantee. This is
genuinely useful: JSON round-trips keep field order, and iteration is deterministic.

**Merging** (3.9+):

```python
defaults = {"temperature": 0.0, "max_tokens": 1024}
overrides = {"temperature": 0.7}
config = defaults | overrides       # {'temperature': 0.7, 'max_tokens': 1024}
```

Right-hand side wins. This is how you will layer configuration in every later module.

**`Counter` and `defaultdict`** — both from `collections`:

```python
from collections import Counter, defaultdict

words = ["a", "b", "a", "c", "a"]
counts = Counter(words)             # Counter({'a': 3, 'b': 1, 'c': 1})
counts.most_common(2)               # [('a', 3), ('b', 1)]

groups = defaultdict(list)
for word in words:
    groups[word[0]].append(word)    # no need to check whether the key exists
```

You used `Counter` in the M1-L02 Naive Bayes lab — that was training a model by counting.

### 5.4 `set`

```python
seen = {"a", "b", "c"}
seen.add("d")
seen.discard("z")           # no error if absent (remove() raises)
"a" in seen                 # O(1)
len(seen)

a = {1, 2, 3}
b = {2, 3, 4}
a | b                       # union        {1,2,3,4}
a & b                       # intersection {2,3}
a - b                       # difference   {1}
a ^ b                       # symmetric difference {1,4}
a <= b                      # subset test
```

**`{}` is an empty dict, not an empty set.** Use `set()` for an empty set.

Deduplicating while preserving order — a genuinely common need:

```python
list(dict.fromkeys(items))     # order preserved (dicts keep insertion order)
list(set(items))               # order LOST
```

### 5.5 The performance difference that actually matters

```python
big_list = list(range(1_000_000))
big_set = set(big_list)

999_999 in big_list      # O(n) - scans up to a million elements
999_999 in big_set       # O(1) - one hash computation
```

This is not a micro-optimisation. **Membership testing inside a loop turns O(n) into O(n²).**

```python
# SLOW: for each of n items, scan a list of m
duplicates = [x for x in new_items if x in existing_list]

# FAST: build the set once, then each test is O(1)
existing = set(existing_list)
duplicates = [x for x in new_items if x in existing]
```

With 10,000 new items against 10,000 existing, that is 100 million comparisons versus 10,000 hash
lookups. The lab measures the real difference. You will apply this directly in M7-L05 when
deduplicating document chunks.

### 5.6 Aliasing and copying

The bug that catches everyone:

```python
a = [1, 2, 3]
b = a                  # NOT a copy - another name for the same list
b.append(4)
a                      # [1, 2, 3, 4]
```

Three ways to actually copy:

```python
b = a.copy()           # shallow copy
b = a[:]               # shallow copy (slice)
b = list(a)            # shallow copy

import copy
b = copy.deepcopy(a)   # deep copy
```

**Shallow is not enough for nested structures:**

```python
rows = [[1, 2], [3, 4]]
shallow = rows.copy()
shallow[0].append(99)
rows                   # [[1, 2, 99], [3, 4]]  <- the INNER list is shared
```

`copy()` created a new outer list containing references to the *same* inner lists. Use
`copy.deepcopy()` when you need genuine independence — and note it is slow, so prefer restructuring
your code to avoid needing it.

**The `[[]] * 3` trap:**

```python
grid = [[]] * 3        # three references to ONE list
grid[0].append("x")
grid                   # [['x'], ['x'], ['x']]  <- all three

grid = [[] for _ in range(3)]   # CORRECT - three separate lists
```

### 5.7 Assumptions and limitations

- O(1) for `dict`/`set` is *average* case. Pathological hash collisions degrade it, but you will not
  meet this with normal keys.
- Sets and dict keys require **hashable** elements. Lists and dicts are not hashable; tuples are, but
  only if everything inside them is.
- `dict` insertion-order preservation is guaranteed from Python 3.7. Do not rely on it in code that
  must run on 3.6.
- Set iteration order is arbitrary and can differ between runs (string hashing is randomised per
  process by default). Never depend on it.

---

## 6. Worked example — choosing containers for a retrieval index

You are building the shape of the search index from Module 6. Preview, but the container decisions
are pure Module 2.

**Requirement 1 — store documents by ID for fast lookup.**

```python
documents: dict[str, str] = {
    "doc-001": "Refund policy: refunds are processed within 5 business days.",
    "doc-002": "Shipping policy: standard delivery is 3-5 working days.",
}
```
`dict`, because access is by key and must be O(1). A list of `(id, text)` pairs would require a scan.

**Requirement 2 — record which document IDs contain each word.**

```python
from collections import defaultdict

index: defaultdict[str, set[str]] = defaultdict(set)
for doc_id, text in documents.items():
    for word in text.lower().split():
        index[word].add(doc_id)
```

- `defaultdict` so a missing word does not need an existence check.
- **`set`** of document IDs, not a list: a word appearing twice in one document must not be recorded
  twice, and `set` gives that for free plus O(1) membership.

**Requirement 3 — find documents containing all of several words.**

```python
def search_all(terms: list[str]) -> set[str]:
    if not terms:
        return set()
    matches = index[terms[0].lower()]
    for term in terms[1:]:
        matches = matches & index[term.lower()]     # set intersection
    return matches
```

Set intersection expresses "all of these words" directly, and is fast. With lists you would write a
nested loop and it would be O(n×m).

**Requirement 4 — cache scored results by (query, k).**

```python
cache: dict[tuple[str, int], list[tuple[str, float]]] = {}
cache[("refund policy", 5)] = [("doc-001", 0.91), ("doc-002", 0.34)]
```
A **tuple** key, because it is hashable and a list is not. The value is a list of tuples, because
ranked results are ordered and each result is a fixed two-field record.

**Requirement 5 — return results sorted by score, then ID for stable ties.**

```python
ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
```

The tuple sort key gives descending score (via negation) then ascending ID. **The tie-break matters
more than it looks:** without it, two documents with identical scores could swap order between runs,
making your evaluation results non-reproducible (M3-L14).

**The summary of decisions:**

| Need | Container | Why |
|---|---|---|
| Documents by ID | `dict` | O(1) key lookup |
| Word → doc IDs | `defaultdict(set)` | No existence checks; automatic dedup; O(1) membership |
| "All of these words" | `set` intersection | Expresses the operation directly and cheaply |
| Cache key | `tuple` | Hashable; lists are not |
| Ranked results | `list` of `tuple` | Order matters; each row is a fixed record |

---

## 7. Practical activity

**File:** [`labs/m2/l03_collections.py`](../../labs/m2/l03_collections.py)

```bash
python3 labs/m2/l03_collections.py
```

Demonstrates each container, then **measures** the list-vs-set membership difference at several
sizes, then reproduces the aliasing, shallow-copy and `[[]] * 3` bugs with real output.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `time.perf_counter()` | High-resolution timer. The right tool for measuring short durations. |
| `defaultdict(set)` | Missing keys create an empty set automatically. |
| `sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))` | The multi-field ranking sort you will reuse in Module 6. |
| `copy.deepcopy(rows)` | Recursively copies nested structures. |
| `list(dict.fromkeys(items))` | Order-preserving deduplication. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Timing figures vary by machine; the **ratios** are the point.

```
======================================================================
PYTHON COLLECTIONS
======================================================================

----------------------------------------------------------------------
1. THE FOUR CONTAINERS
----------------------------------------------------------------------
  [1, 2, 3] + [4]                        = [1, 2, 3, 4]           concatenation
  [1, 2] * 2                             = [1, 2, 1, 2]           repetition
  {"a": 1} | {"a": 2, "b": 3}            = {'a': 2, 'b': 3}       right wins
  {1,2,3} & {2,3,4}                      = {2, 3}                 intersection
  {1,2,3} | {2,3,4}                      = {1, 2, 3, 4}           union
  {1,2,3} - {2,3,4}                      = {1}                    difference
  len({1,1,1,2})                         = 2                      sets deduplicate
  ("x")                                  = 'x'                    <-- NOT a tuple, just a string
  ("x",)                                 = ('x',)                 <-- the comma makes it a tuple
  type({})                               = 'dict'                 <-- empty DICT, not set
  type(set())                            = 'set'                  empty set

  Mutating methods return None:
  [3,1,2].sort()                         = None                   <-- sorts IN PLACE, returns None
  sorted([3,1,2])                        = [1, 2, 3]              returns a NEW list

  Safe dict access:
  user.get("missing")                    = None                   no exception
  user.get("missing", "n/a")             = 'n/a'                  with a default
  user["missing"]                        = "KeyError('missing')"  <-- raises, unlike JavaScript

  Counter and defaultdict:
  Counter(words)                         = Counter({'a': 3, 'b': 2, 'c': 1}) 
  Counter(words).most_common(2)          = [('a', 3), ('b', 2)]   
  defaultdict(list) grouping             = {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry']} 

  Order-preserving deduplication:
  list(set(items))                       = [1, 2, 3]              order LOST
  list(dict.fromkeys(items))             = [3, 1, 2]              order KEPT

----------------------------------------------------------------------
2. LIST vs SET MEMBERSHIP - the difference that matters
----------------------------------------------------------------------
  1000 membership tests for a value NOT present (worst case).

           n     list (ms)    set (ms)       ratio
         100          1.69        0.05         31x
        1000         16.04        0.06        287x
       10000        116.42        0.03       4272x
      100000        954.60        0.03      34695x

  The set time is FLAT - it does not care how big the collection is.
  The list time grows linearly. That is O(1) versus O(n).

  Why it matters: membership testing INSIDE a loop.
    finding duplicates among 5000 items vs 5000 existing
    against a list :   200.51 ms
    against a set  :     0.88 ms   (229x faster)
    same result?     True

  The list version is O(n*m). Building the set once costs O(n),
  then every test is O(1). This is the M7-L05 deduplication step.

  BUT building a set costs O(n) too. How many lookups justify it?

    1000 existing items:
      lookups   list (us)  build+set (us)    winner
            1        8.43           13.90      list
            2       16.81           13.89       set
            3       25.15           13.95       set
            5       41.83           13.99       set
           10       83.73           14.15       set
           50      419.24           15.35       set

  The crossover is at TWO lookups. For a single membership test a
  set is never worth building - constructing it is itself O(n), so
  you have done the scan anyway plus allocation overhead.
  Rule: convert to a set when you will test membership MORE THAN
  ONCE against the same collection. Which, inside a loop, is always.

----------------------------------------------------------------------
3. ALIASING AND COPYING - three real bugs
----------------------------------------------------------------------
  BUG 1: assignment does not copy
  a after b.append(4)                    = [1, 2, 3, 4]           <-- b was never a copy
    id(a)=136513039585152  id(b)=136513039585152  same object: True

  Fixed with an explicit copy:
  a2 after b2.append(4)                  = [1, 2, 3]              unchanged

  BUG 2: copy() is SHALLOW
  rows after shallow[0].append(99)       = [[1, 2, 99], [3, 4]]   <-- inner lists are shared
  with copy.deepcopy                     = [[1, 2], [3, 4]]       genuinely independent

  BUG 3: [[]] * 3 makes three references to ONE list
  [[]] * 3 then grid[0].append("x")      = [['x'], ['x'], ['x']]  <-- all three changed
  [[] for _ in range(3)]                 = [['x'], [], []]        correct

----------------------------------------------------------------------
4. SORTING WITH A TUPLE KEY - and why the tie-break matters
----------------------------------------------------------------------
  Four documents, three tied on 0.9.
    sorted by score only : ['doc-c', 'doc-a', 'doc-d', 'doc-b']
    score then doc id    : ['doc-a', 'doc-c', 'doc-d', 'doc-b']

  Python's sort is stable, so the first version preserves whatever
  order the dict happened to have. Change the insertion order, or
  rebuild the dict from a set, and the tied results reshuffle -
  while every score stays identical.

  That is enough to make an evaluation run non-reproducible
  (M3-L14). ALWAYS give a sort a deterministic tie-break.

======================================================================
```

### 7.3 Reading the result

**The membership table is the headline:**

| n | list (ms) | set (ms) | ratio |
|---|---|---|---|
| 100 | 1.46 | 0.04 | 33× |
| 1,000 | 12.57 | 0.04 | 310× |
| 10,000 | 115.12 | 0.03 | 4,376× |
| 100,000 | 950.75 | 0.03 | **28,448×** |

Look at the set column: **0.04, 0.04, 0.03, 0.03**. It does not move. A thousand-fold increase in
collection size costs nothing, because a hash lookup jumps straight to the slot. The list column
grows exactly in proportion. That is the difference between O(1) and O(n), measured rather than
asserted.

**Then the practical version:** finding duplicates among 5,000 items against 5,000 existing took
**201 ms** with a list and **0.86 ms** with a set — 234× — and produced identical results. That is
the deduplication step you will write in M7-L05, where the collections are document chunks and the
sizes are larger.

**But now the honest counter-question**, which most tutorials skip. Building a set is *itself* O(n),
so it is not free:

```
lookups   list (us)  build+set (us)    winner
      1        8.43           13.90      list
      2       16.81           13.89       set
```

**The crossover is two lookups.** For a *single* membership test, converting to a set is strictly
worse — you have paid for a full pass to build it, which is the same work as just scanning, plus
allocation. From the second lookup onward the set wins and never stops winning.

So the rule is not "sets are faster than lists". It is: **convert to a set when you will test
membership against the same collection more than once** — which, inside a loop, is always. That
precision is what makes it a usable code-review rule rather than folklore.

**The three copy bugs** are worth running yourself rather than reading. Note especially that the
`id()` values printed for `a` and `b` are *identical* — the clearest possible evidence that no copy
occurred.

**And the tie-break demonstration:** three documents tied at 0.9 come out as
`['doc-c', 'doc-a', 'doc-d', 'doc-b']` without a tie-break and `['doc-a', 'doc-c', 'doc-d', 'doc-b']`
with one. Every score is identical in both. Only the order differs, and only the second is
reproducible. That is enough to make two evaluation runs disagree while nothing about the model
changed.

**Verification:** confirm the set column stays flat near 0.03–0.04 ms across all four sizes, and that
the lookup crossover table shows `list` winning at 1 and `set` winning at 2.

---

## 8. Common mistakes and troubleshooting

1. **`x = items.sort()`** — `sort()` returns `None`. Use `sorted()`.
2. **`d["key"]` on a possibly-missing key.** Use `d.get(key, default)`.
3. **`d.key`** — dicts have no dot access. That looks for an attribute.
4. **`in` on a large list inside a loop.** Convert to a `set` first.
5. **`b = a` believing it copies.** It does not.
6. **`.copy()` on nested data.** Shallow. Use `deepcopy` or restructure.
7. **`[[]] * 3`.** Three references to one list. Use a comprehension.
8. **`{}` for an empty set.** That is an empty dict. Use `set()`.
9. **`(5)` for a one-element tuple.** Needs the comma: `(5,)`.
10. **Relying on set order.**

| Error | Cause | Fix |
|---|---|---|
| `KeyError: 'x'` | Missing dict key | `d.get("x")` or `d.get("x", default)` |
| `TypeError: unhashable type: 'list'` | List used as dict key or set member | Convert to a tuple |
| `AttributeError: 'dict' object has no attribute 'name'` | JS-style dot access | `d["name"]` |
| `AttributeError: 'NoneType' object has no attribute 'append'` | Assigned the result of a mutating method | Use `sorted()`/`sorted` copy, or do not assign |
| `ValueError: list.remove(x): x not in list` | `remove` on an absent value | Check first, or use `discard` on a set |
| Mutating one structure changes another | Aliasing or shallow copy | `deepcopy`, or build separately |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Set and dict iteration determinism matters for reproducible evaluation. `dict`
  preserves insertion order; `set` does not. If your output order affects results, sort explicitly
  with a **tie-break** (§6 requirement 5).
- **Privacy.** A `dict` holding user records is trivially logged whole by an f-string. Log field
  names, not objects. M2-L18, M10-L06.
- **Cost / performance.** The list-vs-set choice is the difference between a chunk-deduplication step
  taking seconds and taking hours in Module 7. It is one of the few places where a data-structure
  choice has an order-of-magnitude effect on your AI pipeline.
- **Security.** Building a `set` from untrusted input is unbounded memory. Cap sizes on anything
  derived from user input.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Predict, then verify:

```python
[1,2,3] + [4]            #
[1,2] * 2                #
{"a":1} | {"a":2,"b":3}  #
{1,2,3} & {2,3,4}        #
len({1,1,1,2})           #
("x")                    #
("x",)                   #
[3,1,2].sort()           #
sorted([3,1,2])          #
list(dict.fromkeys([3,1,3,2]))   #
```

### Exercise 2 — Intermediate (~25 min)

Write `build_inverted_index(documents)` taking `dict[str, str]` (id → text) and returning
`dict[str, set[str]]` (lowercased word → set of ids). Then write:

1. `search_any(index, terms)` — documents containing **any** term.
2. `search_all(index, terms)` — documents containing **all** terms.
3. `rank(index, terms)` — returns `list[tuple[str, int]]` of (doc_id, number of matching terms),
   sorted by count descending then doc_id ascending.

Test with at least four documents. Then answer: why must `rank` include the doc_id tie-break?

### Exercise 3 — Challenge (~25 min)

1. Measure it yourself. Write a script that, for n in {100, 1_000, 10_000, 100_000}, times 1,000
   membership tests against a list of size n and against a set of size n. Print a table of both
   timings and the ratio.
2. Plot or describe how the ratio changes with n, and explain why.
3. Now ask the honest counter-question: building a set is itself O(n), so when does it pay for
   itself? Fix n at 1,000 and vary the **number of lookups** from 1 to 50, timing (a) k scans of the
   list against (b) building the set then doing k lookups. Report the crossover and explain it.
   (There is a clean answer; the key confirms it.)
4. Now write the deduplication in two ways — `if x not in result` against a list, and against a set —
   and time both on 20,000 items with 50% duplicates. Report the difference.
5. State the rule you would put in a code review checklist.

---

## 11. Quiz

**Q1.** Which container should hold a fixed `(latitude, longitude)` pair used as a dictionary key?

- A. `list`  B. `tuple`  C. `set`  D. `dict`

**Q2.** What does `[3, 1, 2].sort()` return?

- A. `[1, 2, 3]`  B. `None` — it sorts in place  C. `[3, 1, 2]`  D. A new sorted list

**Q3.** Why is `"x" in some_set` faster than `"x" in some_list` for large collections?

- A. Sets store fewer items.
- B. A set computes a hash and jumps to the slot (O(1)), whereas a list scans elements one by one
  (O(n)).
- C. Lists are stored on disk.
- D. They are the same speed.

**Q4.** What does `d["missing"]` do when the key is absent, and what is the JavaScript-like
alternative?

- A. Returns `None`; use `d.get()` for an error.
- B. Raises `KeyError`; use `d.get("missing")` to get `None` instead.
- C. Returns `undefined`.
- D. Creates the key with value `None`.

**Q5.** `rows = [[1,2],[3,4]]; c = rows.copy(); c[0].append(99)`. What is `rows` now?

- A. `[[1,2],[3,4]]` — unchanged.
- B. `[[1,2,99],[3,4]]` — `copy()` is shallow, so the inner lists are shared.
- C. Raises an error.
- D. `[[99],[3,4]]`

**Q6.** What is `grid` after `grid = [[]] * 3; grid[0].append("x")`?

- A. `[['x'], [], []]`
- B. `[['x'], ['x'], ['x']]` — the multiplication created three references to one list.
- C. `[[], [], []]`
- D. `[['x']]`

**Q7.** Which expression deduplicates a list **while preserving order**?

- A. `list(set(items))`  B. `sorted(set(items))`  C. `list(dict.fromkeys(items))`
- D. `items.unique()`

**Q8.** Why does `sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))` include `kv[0]`?

- A. To sort alphabetically as the primary key.
- B. As a deterministic tie-break, so items with equal scores always appear in the same order —
  without it, results are unstable between runs and evaluation is not reproducible.
- C. It is required syntax.
- D. To reverse the sort.

**Q9.** `{}` creates what?

- A. An empty set  B. An empty dict  C. An empty tuple  D. A syntax error

**Q10.** *(Written, rubric-graded.)* In under 70 words, explain when you would convert a list to a set
before a loop, and quantify roughly what it saves.

---

## 12. Revision notes

- **`list`** ordered mutable · **`tuple`** ordered immutable *and hashable* · **`dict`** key→value,
  insertion-ordered · **`set`** unique, unordered, O(1) membership.
- Choose by: *does it change?* and *do I look up by key or test membership?*
- **Mutating methods return `None`.** `sort()` mutates; `sorted()` returns.
- `d[k]` raises `KeyError`; `d.get(k, default)` does not. **No dot access on dicts.**
- `dict` merge with `|`, right side wins. `Counter` counts; `defaultdict` removes existence checks.
- **`in` on a list is O(n); on a set it is O(1).** Membership in a loop turns O(n) into O(n²).
  Build the set once.
- `b = a` aliases. `.copy()`/`[:]`/`list(a)` are **shallow**. Nested data needs `copy.deepcopy`.
- **`[[]] * 3` shares one list.** Use `[[] for _ in range(3)]`.
- `{}` is an empty dict; `set()` is an empty set. `(5,)` is a tuple; `(5)` is an int.
- Order-preserving dedup: `list(dict.fromkeys(items))`.
- **Always add a tie-break to sorts** whose results you will compare across runs.

---

## 13. Completion checklist

- [ ] I can fill in the four-row comparison table from memory.
- [ ] I predicted all ten Exercise 1 expressions.
- [ ] I built the inverted index in Exercise 2 and can explain the tie-break.
- [ ] I measured the list-vs-set difference myself and found the crossover point.
- [ ] I reproduced the aliasing, shallow-copy and `[[]] * 3` bugs.
- [ ] I know which methods return `None`.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "Data Structures".
  <https://docs.python.org/3/tutorial/datastructures.html> `[UNVERIFIED]`
- Python docs, `collections` — `Counter`, `defaultdict`, and others.
  <https://docs.python.org/3/library/collections.html> `[UNVERIFIED]`
- Python wiki, "Time Complexity" — the O() table for every built-in operation.
  <https://wiki.python.org/moin/TimeComplexity> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L04 — Conditions, Loops and Comprehensions](M2-L04-control-flow-comprehensions.md)

You have the containers. Next: how to iterate over them idiomatically, and the comprehension syntax
that appears in almost every line of Python you will read in this course.
