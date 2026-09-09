# M2-L02 — Variables, Numbers, Strings and f-strings

| | |
|---|---|
| **Lesson ID** | M2-L02 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M2-L01](M2-L01-setup-terminal-venv-pip.md) |

---

## 1. Learning objectives

1. **Use** Python's core scalar types and **predict** the result of mixed-type arithmetic.
2. **Explain** why `0.1 + 0.2 != 0.3` and **choose** the correct numeric type for money.
3. **Format** strings with f-strings, including alignment, precision and debugging syntax.
4. **Distinguish** `==` from `is`, and **state** when each is correct.
5. **Predict** Python's truthiness rules and **avoid** the two bugs they cause.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Variable** | A name bound to an object. Python names are *references*, not boxes. |
| **Dynamic typing** | A variable's type is determined by its current value, not declared. |
| **Strong typing** | Python does not silently convert between unrelated types. `"1" + 1` is an error. |
| **Immutable** | Cannot be changed after creation. `str`, `int`, `float`, `bool`, `tuple` are immutable. |
| **`int`** | An integer of unlimited size. |
| **`float`** | A 64-bit binary floating-point number. |
| **`Decimal`** | An exact base-10 number from the `decimal` module. Use for money. |
| **`bool`** | `True` or `False`. A subclass of `int`. |
| **`None`** | The absence of a value. Python's single null. |
| **f-string** | A string literal prefixed with `f`, allowing `{expression}` interpolation. |
| **Truthiness** | The boolean value an object has in a condition. |
| **Identity** | Whether two names refer to the *same object*. Tested with `is`. |
| **Equality** | Whether two objects have the same *value*. Tested with `==`. |

---

## 3. Plain-language explanation

Python's basics look like every other language, and mostly behave like it. This lesson concentrates
on the handful of places where it does not, because those are where your JavaScript instincts will
produce bugs.

**Variables are names bound to objects.**

```python
count = 5
name = "Bharath"
price = 19.99
active = True
missing = None
```

No `let`, `const` or `var`. No type declaration. Names are conventionally `snake_case`, and constants
are `UPPER_SNAKE_CASE` by convention only — Python does not enforce immutability of names.

**Python is dynamically typed but strongly typed.** The type is decided by the value, but Python will
not guess conversions:

```python
"1" + 1        # TypeError - JavaScript would give "11"
```

This is a genuine improvement. JavaScript's `[] + {}` school of coercion has no Python equivalent, and
the errors you get instead are the errors you want.

### The JavaScript comparison table

| Concept | JavaScript | Python | Consequence |
|---|---|---|---|
| Declaration | `let x = 1` | `x = 1` | — |
| Null-ish | `null` **and** `undefined` | `None` only | Simpler; no `??` needed |
| String concat with number | `"1" + 1` → `"11"` | `TypeError` | Bugs surface immediately |
| Integers | One `Number` type (float64) | `int` (unbounded) **and** `float` | `2**100` is exact in Python |
| Equality | `==` coerces, `===` does not | `==` compares value, **no coercion** | Python's `==` behaves like `===` |
| Identity | `===` on objects | `is` | Different meaning — see §5.4 |
| Template literal | `` `hi ${name}` `` | `f"hi {name}"` | Nearly identical |
| Truthy empty string | falsy | falsy | Same |
| Truthy `[]` | **truthy** | **falsy** | ⚠️ **Real difference** |
| Truthy `{}` | **truthy** | **falsy** | ⚠️ **Real difference** |
| Truthy `0` | falsy | falsy | Same |

The two ⚠️ rows cause real bugs when moving between the languages, in both directions. In Python,
`if items:` is the *idiomatic* way to check for a non-empty list — which reads wrong to a JavaScript
developer and is correct here.

---

## 4. Analogy

**Names are luggage tags, not suitcases.**

```python
a = [1, 2, 3]
b = a          # b is a SECOND TAG on the SAME suitcase
b.append(4)
print(a)       # [1, 2, 3, 4]  - a changed too
```

You did not copy the list. You attached a second label to it.

### Where the analogy breaks

1. **It only bites for mutable objects.** Rebinding a name (`b = [9]`) moves the tag to a different
   suitcase and leaves `a` alone. Only *mutating* through the reference affects both.
2. **Immutable objects make the distinction invisible.** `x = 5; y = x; y += 1` leaves `x` at 5,
   because `+=` on an `int` creates a new object. So the same syntax behaves differently depending on
   the type — which is exactly why the rule must be learned rather than intuited.
3. **The tag metaphor suggests the suitcase is freed when tags are removed.** Roughly true —
   CPython reference-counts — but cycles need the garbage collector, and this is not something you
   manage.
4. **Function arguments.** Python passes the *reference by value*. Reassigning the parameter inside a
   function does not affect the caller; mutating the object does. M2-L05 covers this properly, and it
   is the source of a classic bug you will meet there.

---

## 5. Detailed technical explanation

### 5.1 Numbers

```python
a = 7
b = 2

a + b       # 9
a - b       # 5
a * b       # 14
a / b       # 3.5   <- TRUE DIVISION, always returns float
a // b      # 3     <- FLOOR division, rounds toward negative infinity
a % b       # 1     <- remainder
a ** b      # 49    <- exponent (not ^, which is bitwise XOR)
```

Two traps:

- **`/` always returns a float**, even for `4 / 2` (→ `2.0`). Use `//` when you want an integer.
- **`//` rounds toward negative infinity, not toward zero.** `-7 // 2` is `-4`, not `-3`. This
  differs from C, Java and JavaScript's `Math.trunc`, and it will surprise you.

**Integers are unbounded.** No overflow, ever:

```python
2 ** 100    # 1267650600228229401496703205376  - exact
```

This is genuinely different from JavaScript, where `Number.MAX_SAFE_INTEGER` is about 9×10¹⁵.

### 5.2 Floats, and why money is different

```python
0.1 + 0.2           # 0.30000000000000004
0.1 + 0.2 == 0.3    # False
```

This is not a Python bug. `float` is IEEE-754 binary floating point, and 0.1 cannot be represented
exactly in binary — just as ⅓ cannot be written exactly in decimal. Every language using float64 has
this, JavaScript included.

**Consequences and fixes:**

| Situation | Do this |
|---|---|
| Comparing floats | `math.isclose(a, b)`, never `==` |
| Money | `decimal.Decimal`, or store integer minor units (pence/cents) |
| Accumulating many values | Beware compounding error; `math.fsum` for sums |
| Displaying | `f"{value:.2f}"` |

```python
from decimal import Decimal

Decimal("0.1") + Decimal("0.2") == Decimal("0.3")   # True
```

Note `Decimal("0.1")` takes a **string**. `Decimal(0.1)` passes the already-inexact float in and
inherits the error — a subtle and common mistake.

**This matters directly for AI work.** In M5-L15 you will compute token costs, and in Module 12 AWS
spend. Both are money. Both should use `Decimal` or integer minor units. A rounding error in a cost
report is embarrassing in a way a rounding error in a similarity score is not.

### 5.3 Strings

Strings are **immutable**. Every "modification" creates a new string.

```python
name = "bharath"
name.upper()        # "BHARATH"  - a NEW string
print(name)         # "bharath"  - unchanged
name = name.upper() # rebind to keep it
```

Useful methods:

```python
text = "  Hello, World  "
text.strip()                    # "Hello, World"
text.lower()                    # "  hello, world  "
text.replace("World", "Python") # "  Hello, Python  "
"a,b,c".split(",")              # ['a', 'b', 'c']
", ".join(["a", "b", "c"])      # "a, b, c"
"hello".startswith("he")        # True
"abc" in "xxabcxx"              # True   - substring test
len("hello")                    # 5
```

`"".join(list_of_strings)` is the idiomatic way to build a string from parts. Repeated `+=` in a loop
creates a new string each time — fine for a handful, quadratic for thousands.

**Slicing** — `[start:stop:step]`, `stop` exclusive:

```python
s = "abcdefgh"
s[0]        # 'a'
s[-1]       # 'h'      negative indexes count from the end
s[1:4]      # 'bcd'    includes 1, excludes 4
s[:3]       # 'abc'
s[3:]       # 'defgh'
s[::2]      # 'aceg'   every second character
s[::-1]     # 'hgfedcba'  reversed
```

Slicing never raises `IndexError` — `s[10:20]` on a short string returns `''`. Indexing does. That
asymmetry catches people.

### 5.4 f-strings

The standard way to build strings since Python 3.6.

```python
name = "Bharath"
score = 0.8734
count = 7

f"Hello, {name}"                  # 'Hello, Bharath'
f"{count} items"                  # '7 items'
f"{score:.2f}"                    # '0.87'      2 decimal places
f"{score:.1%}"                    # '87.3%'     as a percentage
f"{count:>5}"                     # '    7'     right-align in width 5
f"{name:<10}|"                    # 'Bharath   |'  left-align
f"{name:^11}|"                    # '  Bharath  |'  centre
f"{1234567:,}"                    # '1,234,567'  thousands separator
f"{score=}"                       # 'score=0.8734'  <- debugging form
f"{count * 2}"                    # '14'  any expression works
```

Two worth memorising:

- **`f"{value=}"`** prints both the expression and its value. It replaces most `print("x is", x)`
  calls and you will use it constantly.
- **Alignment specifiers** (`:<`, `:>`, `:^`, `:,`) are how every table in this course's labs is
  formatted. Read `f"{name:<30}{score:>8.2f}"` as "name left-aligned in 30 columns, then score
  right-aligned in 8 columns with 2 decimals".

**One safety rule, carried forward:** never build SQL with an f-string (M2-L16), and be careful
building prompts with them (M5-L05). Interpolating untrusted text into a command string is the shape
of both SQL injection and prompt injection.

### 5.5 `==` versus `is`

| Operator | Asks | Use for |
|---|---|---|
| `==` | Do these have the same **value**? | Almost everything |
| `is` | Are these the **same object** in memory? | `None`, `True`, `False` only |

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b      # True  - same contents
a is b      # False - two different list objects

x = None
x is None   # True   <- CORRECT
x == None   # works, but wrong style
```

**The rule: always `is None`, never `== None`.** `==` can be overridden by a class's `__eq__`, so a
badly-behaved object could compare equal to `None`. `is` cannot be overridden.

**The trap that teaches this badly.** CPython caches small integers (−5 to 256), so `is`
*accidentally* works for them:

```python
int("256") is int("256")    # True   - both are the one cached 256 object
int("257") is int("257")    # False  - outside the cache, two distinct objects
int("257") == int("257")    # True   - equal, which is what you actually care about
```

There is a second, separate effect that muddies this further. Written as plain literals inside one
function, **both** comparisons return `True`:

```python
a, b = 257, 257
a is b      # True - but NOT because of the small-int cache
```

Here the compiler stores a single shared constant for both `257` literals in the same code object.
That is *constant interning*, a different mechanism from the small-integer cache. The lab builds the
values with `int("257")` specifically to separate the two.

**The point is not to learn either mechanism.** It is that two unrelated implementation details
independently produced a misleading `True`, and neither is guaranteed by the language. This is
exactly why `is` must never be used to compare numbers or strings — only `None`, `True` and `False`.

### 5.6 Truthiness

These are **falsy**: `False`, `None`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `()`.
Everything else is truthy.

```python
items = []
if items:                    # False - empty list is falsy
    print("has items")
if not items:                # idiomatic empty check
    print("empty")
```

**The bug this causes.** These are not equivalent:

```python
if value:            # False for None, 0, "", [], and False
if value is not None:  # False only for None
```

If `value` is a count that can legitimately be `0`, or a score that can be `0.0`, the first form
silently treats a valid value as missing. This is a real and common bug in configuration handling and
in scoring code:

```python
def apply_discount(percent=None):
    if not percent:              # BUG: 0 is a valid discount
        percent = DEFAULT
    ...

def apply_discount(percent=None):
    if percent is None:          # CORRECT
        percent = DEFAULT
```

**Rule: use truthiness for collections, `is None` for optional values.**

### 5.7 Assumptions and limitations

- Small-integer caching (§5.5) is a CPython implementation detail, not part of the language.
- `Decimal` is exact for decimal fractions but slower than `float`, and is not suitable for
  scientific computation where `float`'s speed matters.
- String methods are Unicode-aware, but `len()` counts code points, not user-perceived characters —
  an emoji with a skin-tone modifier has `len() > 1`. Relevant when counting characters for display.

---

## 6. Worked example — a cost calculator, done wrong then right

You must compute the cost of 1,000 LLM calls at £0.003 each. Preview of M5-L15.

**Attempt 1 — floats.**

```python
price = 0.003
total = 0.0
for _ in range(1000):
    total += price
print(total)            # 3.0000000000000027
print(total == 3.0)     # False
```

Accumulating a float 1,000 times compounds the representation error. The answer is wrong in the 15th
significant figure — harmless for display, but `total == 3.0` is `False`, and any code branching on
that comparison is broken. (The exact wrong digits depend on your platform's floating-point
behaviour; the lab prints what your machine produces.)

**Attempt 2 — multiply instead of accumulate.**

```python
total = 0.003 * 1000
print(total)            # 3.0000000000000004
```

Better — one operation instead of 1,000 — but still not exact.

**Attempt 3 — `Decimal`.**

```python
from decimal import Decimal

price = Decimal("0.003")
total = price * 1000
print(total)            # 3.000
print(total == Decimal("3"))   # True
```

Exact. Note `Decimal("0.003")` from a **string**, and that `Decimal` preserves significant digits
(`3.000`, not `3`).

**Attempt 4 — integer minor units**, the approach most payment systems use:

```python
price_millipence = 3          # £0.003 = 3 millipence
total_millipence = price_millipence * 1000     # 3000
pounds = total_millipence / 1000               # 3.0 for display only
```

All arithmetic in integers; convert to a decimal string only for display. Immune to float error and
fast.

**Which to use:** `Decimal` when the arithmetic is varied and readability matters (cost reports).
Integer minor units when performance matters or you are interoperating with a payment system.
**Never plain `float` for money.**

---

## 7. Practical activity

**File:** [`labs/m2/l02_types_and_strings.py`](../../labs/m2/l02_types_and_strings.py)

```bash
python3 labs/m2/l02_types_and_strings.py
```

Demonstrates every trap in this lesson with real output: float representation, `//` rounding
direction, the truthiness table, `is` vs `==` including the small-int cache, f-string formatting, and
the `not value` versus `is None` bug side by side.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `f"{value!r}"` | `!r` calls `repr()` instead of `str()`, so strings show their quotes. Essential when debugging whitespace or type confusion. |
| `Decimal("0.1")` | String argument. `Decimal(0.1)` inherits the float's error. |
| `math.isclose(a, b)` | The correct float comparison. |
| `f"{a:<28}{b:>12}"` | The alignment pattern used by every table in this course. |
| `id(obj)` | The object's identity. What `is` actually compares. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3:

```
======================================================================
PYTHON TYPES, STRINGS AND TRUTHINESS
======================================================================

----------------------------------------------------------------------
1. NUMBERS - division and rounding
----------------------------------------------------------------------
  7 / 2                          = 3.5                        / ALWAYS returns float
  4 / 2                          = 2.0                        even when it divides evenly
  7 // 2                         = 3                          // floors
  -7 // 2                        = -4                         <-- FLOORS toward -inf, not toward zero
  int(-7 / 2)                    = -3                         int() truncates toward zero - different!
  7 % 2                          = 1                          
  -7 % 2                         = 1                          sign follows the divisor, unlike C/Java
  2 ** 10                        = 1024                       ** is power; ^ is bitwise XOR
  7 ^ 2                          = 5                          <-- XOR, not power. A classic slip.

  Integers are UNBOUNDED - no overflow:
  2 ** 100                       = 1267650600228229401496703205376 
  (JavaScript's Number.MAX_SAFE_INTEGER is about 9.0e15.)

----------------------------------------------------------------------
2. FLOATS - why 0.1 + 0.2 is not 0.3
----------------------------------------------------------------------
  0.1 + 0.2                      = 0.30000000000000004        <-- not 0.3
  0.1 + 0.2 == 0.3               = False                      
  math.isclose(0.1+0.2, 0.3)     = True                       the correct test

  Why: 0.1 has no exact binary representation.
  0.1 to 20 decimal places = 0.10000000000000000555
  0.2 to 20 decimal places = 0.20000000000000001110
  0.3 to 20 decimal places = 0.29999999999999998890

  MONEY: accumulate 0.003 one thousand times
  float accumulation             = 3.0000000000000027         wrong in the 13th decimal
  float multiplication           = 3.0                        better, still not exact
  Decimal("0.003") * 1000        = Decimal('3.000')           EXACT
  == Decimal("3")                = True                       

  And the trap inside the fix:
  Decimal("0.1")                 = Decimal('0.1')             from a string: exact
  Decimal(0.1)                   = Decimal('0.1000000000000000055511151231257827021181583404541015625') <-- from a float: inherits the error

----------------------------------------------------------------------
3. STRINGS - immutability and slicing
----------------------------------------------------------------------
  name                           = 'bharath'                  
  name.upper()                   = 'BHARATH'                  returns a NEW string
  name (after .upper())          = 'bharath'                  <-- unchanged: strings are immutable

  s                              = 'abcdefgh'                 
  s[0]                           = 'a'                        
  s[-1]                          = 'h'                        negative counts from the end
  s[1:4]                         = 'bcd'                      start inclusive, stop exclusive
  s[:3]                          = 'abc'                      
  s[3:]                          = 'defgh'                    
  s[::2]                         = 'aceg'                     every 2nd character
  s[::-1]                        = 'hgfedcba'                 reversed
  s[10:20]                       = ''                         <-- slices NEVER raise; indexing does

  Building strings: use join, not += in a loop
  ", ".join(parts)               = 'alpha, beta, gamma'       

----------------------------------------------------------------------
4. F-STRINGS - the formatting you will use constantly
----------------------------------------------------------------------
  f"{score:.2f}"                 = '0.87'                     2 decimal places
  f"{score:.1%}"                 = '87.3%'                    as a percentage
  f"{count:,}"                   = '1,234,567'                thousands separator
  f"{name:>12}|"                 = '     Bharath|'            right-align in 12
  f"{name:<12}|"                 = 'Bharath     |'            left-align
  f"{name:^12}|"                 = '  Bharath   |'            centre
  f"{score=}"                    = 'score=0.8734'             <-- debugging form: name AND value
  f"{count * 2}"                 = '2469134'                  any expression works

  The table pattern used throughout this course:
    f"{label:<22}{value:>10.3f}"
    precision                  0.873
    recall                     0.651
    f1                         0.747

----------------------------------------------------------------------
5. == vs is
----------------------------------------------------------------------
  a == b                         = True                       same VALUE
  a is b                         = False                      <-- different OBJECTS
  a is c                         = True                       c is another name for the same list
  id(a)=126283639606080  id(b)=126283638633856  id(c)=126283639606080

  Mutating through one name is visible through the other:
  a (after c.append(4))          = [1, 2, 3, 4]               <-- a changed too

  None must be tested with 'is':
  value is None                  = True                       CORRECT

  The small-integer cache - an implementation detail, NEVER rely on it:
  256 is 256 (literals)          = True                       cached by CPython
  257 is 257 (literals)          = True                       <-- also True, but NOT the cache

  Why is the second one True? Because both 257 literals sit in the
  SAME compiled function, and CPython stores one shared constant for
  them. That is constant interning, not the small-int cache.
  Build the numbers at runtime instead and the two effects separate:
  int("256") is int("256")       = True                       True: small-int cache
  int("257") is int("257")       = False                      <-- False: outside the cache
  int("257") == int("257")       = True                       but EQUAL, which is what matters

  Two separate implementation details produced the same misleading
  result. That is exactly why 'is' must never be used to compare
  numbers or strings - only None, True and False.

----------------------------------------------------------------------
6. TRUTHINESS - and the bug it causes
----------------------------------------------------------------------
  value           bool()    note
  False           False     
  None            False     
  0               False     
  0.0             False     
  ''              False     
  []              False     <-- TRUTHY in JavaScript!
  {}              False     <-- TRUTHY in JavaScript!
  set()           False     
  ()              False     
  '0'             True      
  'False'         True      
  [0]             True      
  {'a': 1}        True      
  -1              True      
  0.1             True      

  THE BUG: 'not value' vs 'value is None'

  input       not value     value is None   outcome
  None        True          True            default / default
  0           True          False           default / 0  <-- WRONG
  ''          True          False           default / ''  <-- WRONG
  0.0         True          False           default / 0.0  <-- WRONG
  5           False         False           5 / 5
  'x'         False         False           'x' / 'x'

  A discount of 0 percent, an empty search string and a score of
  0.0 are all VALID values that 'if not value' silently replaces
  with a default. Use truthiness for collections, 'is None' for
  optional values.

======================================================================
```

### 7.3 The five lines worth staring at

1. **`-7 // 2 = -4` but `int(-7 / 2) = -3`.** Two ways of "dividing and making it an integer" that
   disagree on negative numbers. `//` floors toward −∞; `int()` truncates toward zero. If you are
   computing an index, a page number or a batch count from a value that can be negative, this is a
   live bug.

2. **`7 ^ 2 = 5`.** `^` is XOR, not exponentiation. Written in a hurry it silently produces a plausible
   wrong number instead of an error, which is the worst kind of typo.

3. **`0.1` to 20 decimal places is `0.10000000000000000555`.** This is the whole floating-point story
   in one line. The error is not introduced by addition; it is already present in the literal.

4. **`Decimal(0.1)` prints `0.1000000000000000055511151231257827021181583404541015625`.** The fix
   applied incorrectly faithfully reproduces the very error it was meant to avoid. Always pass a
   string.

5. **The truthiness bug table.** Three of six inputs — `0`, `''`, `0.0` — are silently replaced by a
   default under `not value` and correctly preserved under `is None`. A zero-percent discount, an
   empty search query and a score of 0.0 are all legitimate values that the natural-looking code
   throws away.

**Verification:** confirm `-7 // 2 = -4`, `int("257") is int("257") = False`, and that the truthiness
table flags exactly three rows as `<-- WRONG`.

---

## 8. Common mistakes and troubleshooting

1. **`==` on floats.** Use `math.isclose`.
2. **`float` for money.** Use `Decimal` or integer minor units.
3. **`Decimal(0.1)` instead of `Decimal("0.1")`.**
4. **`if not value` for an optional that can legitimately be `0` or `""`.** Use `is None`.
5. **Expecting `//` to truncate toward zero.** It floors: `-7 // 2 == -4`.
6. **Expecting `/` to give an integer.** It never does.
7. **Relying on `is` for numbers or strings.** Implementation detail.
8. **Building strings with `+=` in a large loop.** Use `"".join(parts)`.
9. **Assuming `[]` is truthy** because it is in JavaScript.

| Error / symptom | Cause | Fix |
|---|---|---|
| `TypeError: can only concatenate str (not "int") to str` | Mixing types with `+` | `f"{a}{b}"` or `str(b)` |
| Comparison of equal-looking floats is `False` | Binary representation | `math.isclose` |
| A `0` value silently replaced by a default | Truthiness | `is None` |
| `IndexError: string index out of range` | Indexing past the end | Check `len`, or slice — slices do not raise |
| `AttributeError: 'str' object has no attribute 'push'` | JavaScript method name | `list.append`; strings are immutable |
| Totals off by a fraction of a penny | Float accumulation | `Decimal` |

---

## 9. Security, privacy, reliability and cost

- **Security.** f-strings interpolate arbitrary values into text. That is fine for logs, dangerous
  for SQL (M2-L16) and for prompts (M5-L05). The habit to build now: **notice when an f-string is
  constructing a command or instruction rather than a message.**
- **Privacy.** f-strings make it trivially easy to log personal data by accident —
  `logger.info(f"user {user}")` may serialise an entire object including an email address. M2-L18 and
  M10-L06.
- **Reliability.** Float comparison bugs are intermittent and hard to reproduce. Use `math.isclose`
  everywhere by default.
- **Cost.** Every cost figure in this course is money and should be `Decimal` or minor units. You
  will build a real token-cost calculator in M5-L15.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Predict each result **before** running it, then check:

```python
7 / 2            #
7 // 2           #
-7 // 2          #
7 % 2            #
-7 % 2           #
2 ** 10          #
"5" * 3          #
[0] * 3          #
bool([])         #
bool([0])        #
bool("False")    #
0.1 + 0.2 == 0.3 #
```

Note every one you got wrong. Those are your real gaps.

### Exercise 2 — Intermediate (~20 min)

Write a function `format_cost_report(rows)` where `rows` is a list of
`(model_name, calls, price_per_call)` tuples. It must return a string containing:

- A header row.
- One line per model: name left-aligned in 22 columns, call count right-aligned in 8 with thousands
  separators, unit price right-aligned in 12 showing 4 decimal places, total right-aligned in 12
  showing 2 decimals.
- A total line.

Use `Decimal` for all money. Test with:

```python
rows = [
    ("claude-haiku",  120_000, "0.0008"),
    ("claude-sonnet",  15_400, "0.0030"),
    ("claude-opus",       820, "0.0150"),
]
```

Verify the grand total is exact — compare against `Decimal` arithmetic done by hand.

### Exercise 3 — Challenge (~25 min)

1. Write a function `safe_get(config, key, default)` that returns `config[key]` **unless it is
   absent or `None`**, in which case it returns `default`. A value of `0`, `""` or `False` must be
   returned as-is, not replaced.
2. Write five test cases covering exactly those edge cases and run them.
3. Now write the naive version using `config.get(key) or default` and show which of your five tests
   it fails.
4. Explain in two sentences why the naive version is the more "natural-looking" code, and what that
   tells you about reviewing other people's Python.
5. Find one place in the Module 1 lab scripts (`labs/m1/`) where truthiness is used on a collection.
   State whether it is correct there and why.

---

## 11. Quiz

**Q1.** What does `-7 // 2` evaluate to?

- A. `-3`  B. `-3.5`  C. `-4`  D. `3`

**Q2.** Why is `0.1 + 0.2 == 0.3` `False`?

- A. A bug in Python's arithmetic.
- B. `0.1` and `0.2` cannot be represented exactly in binary floating point, so the sum differs from
  the closest float to `0.3` by a tiny amount.
- C. Python rounds all floats to 2 decimal places.
- D. The comparison operator is wrong.

**Q3.** Which is the correct way to check that an optional integer parameter was not supplied, given
that `0` is a valid value?

- A. `if not value:`  B. `if value == None:`  C. `if value is None:`  D. `if len(value) == 0:`

**Q4.** What is the difference between `==` and `is`?

- A. They are identical.
- B. `==` compares values; `is` compares object identity — whether both names refer to the same
  object in memory.
- C. `is` compares values; `==` compares identity.
- D. `is` is only for strings.

**Q5.** Which of these is **truthy** in Python but **falsy** would be wrong to assume from
JavaScript?

- A. `""`  B. `0`  C. `[]` is falsy in Python but truthy in JavaScript  D. `None`

**Q6.** Which produces `'87.3%'` from `score = 0.8734`?

- A. `f"{score}%"`  B. `f"{score:.1%}"`  C. `f"{score:.1f}%"`  D. `f"{score * 100}%"`

**Q7.** Why should `Decimal("0.1")` be written with a string rather than `Decimal(0.1)`?

- A. `Decimal` only accepts strings.
- B. `Decimal(0.1)` receives a float that is already inexact, so the `Decimal` faithfully reproduces
  that error rather than representing 0.1 exactly.
- C. Strings are faster.
- D. There is no difference.

**Q8.** What does `f"{count=}"` produce when `count = 7`?

- A. `7`  B. `count`  C. `count=7`  D. A syntax error

**Q9.** `a = [1,2,3]; b = a; b.append(4); print(a)` prints what, and why?

- A. `[1,2,3]` — `b` is a copy.
- B. `[1,2,3,4]` — `b` and `a` are two names bound to the same list object, so mutating through one
  is visible through the other.
- C. `[4]` — append replaces the list.
- D. Raises an error.

**Q10.** *(Written, rubric-graded.)* In under 70 words, explain to a JavaScript developer the two
truthiness differences in Python that will most likely cause them a bug.

---

## 12. Revision notes

- Names are **references**. `b = a` on a mutable object gives two tags on one suitcase.
- Dynamic but **strongly** typed: `"1" + 1` is a `TypeError`, not `"11"`.
- `/` always gives a float · `//` **floors** (`-7 // 2 == -4`) · `**` is power, not `^`.
- **`int` is unbounded.** No overflow.
- `0.1 + 0.2 != 0.3`. Compare floats with `math.isclose`. **Money → `Decimal("...")` or integer minor
  units**, never `float`.
- Strings are **immutable**; methods return new strings. Build with `"".join(parts)`.
- Slices never raise; indexes do.
- f-strings: `{x:.2f}` `{x:.1%}` `{x:>8}` `{x:<20}` `{x:^10}` `{x:,}` `{x=}`.
- **`is None`, never `== None`.** `is` compares identity and cannot be overridden.
- Falsy: `False None 0 0.0 "" [] {} set() ()`. **`[]` and `{}` are falsy in Python, truthy in JS.**
- Truthiness for collections; `is None` for optionals that may legitimately be `0`/`""`/`False`.
- f-strings building SQL or prompts is the shape of injection. Notice it.

---

## 13. Completion checklist

- [ ] I predicted all twelve Exercise 1 expressions and checked them.
- [ ] I can explain the float representation problem and name two fixes.
- [ ] I wrote the `Decimal` cost report in Exercise 2 and verified exactness.
- [ ] I can state when to use `is` and when to use `==`.
- [ ] I found the `not value` bug in Exercise 3 and can explain it.
- [ ] I know the alignment f-string specifiers by sight.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "An Informal Introduction to Python".
  <https://docs.python.org/3/tutorial/introduction.html> `[UNVERIFIED]`
- Python docs, `decimal` module. <https://docs.python.org/3/library/decimal.html> `[UNVERIFIED]`
- Python docs, "Format Specification Mini-Language" — the full f-string grammar.
  <https://docs.python.org/3/library/string.html#formatspec> `[UNVERIFIED]`
- "What Every Computer Scientist Should Know About Floating-Point Arithmetic", Goldberg (1991).
  `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L03 — Collections: list, tuple, dict, set](M2-L03-collections.md)

Scalars done. Next: the four container types, when each is the right choice, and the mutable-default
bug that catches everyone exactly once.
