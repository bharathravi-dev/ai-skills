# M2-L10 — Exceptions, Tracebacks and Debugging

| | |
|---|---|
| **Lesson ID** | M2-L10 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L05](M2-L05-functions-scope.md) |

---

## 1. Learning objectives

1. **Read** a traceback and identify the failing line, the call chain and the root cause.
2. **Catch** exceptions at the right level of specificity, and **explain** why bare `except` is
   harmful.
3. **Raise** custom exceptions carrying structured context.
4. **Use** `try/except/else/finally` and `raise ... from ...` correctly.
5. **Debug** with `breakpoint()` and targeted logging rather than scattered `print`.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Exception** | An object representing an error, which interrupts normal flow. |
| **Traceback** | The stack of calls that led to the exception. |
| **Raise** | To signal an exception. |
| **Catch / handle** | To intercept an exception with `except`. |
| **Bare except** | `except:` with no type — catches everything, including `KeyboardInterrupt`. |
| **Exception chaining** | `raise X from Y` — preserves the original cause. |
| **`finally`** | A block that always runs, whether or not an exception occurred. |
| **`else`** | A block that runs only if no exception was raised. |
| **Custom exception** | Your own subclass of `Exception`. |
| **Swallowing** | Catching an exception and doing nothing, hiding the failure. |
| **`breakpoint()`** | Drops into the interactive debugger at that line. |
| **EAFP** | "Easier to Ask Forgiveness than Permission" — try it and handle failure. |
| **LBYL** | "Look Before You Leap" — check first. |

---

## 3. Plain-language explanation

Exceptions are Python's way of saying "I cannot continue with this". They travel **up** the call stack
until something catches them, or the program stops.

```python
try:
    value = int(user_input)
except ValueError:
    value = 0
```

Three habits separate good exception handling from bad, and all three are about **information**:

1. **Catch the narrowest type you can.** `except ValueError` says you anticipated this specific
   failure. `except Exception` says you gave up.
2. **Never swallow silently.** A caught exception that produces no log, no metric and no changed
   behaviour is a bug you have hidden from yourself.
3. **Preserve the cause.** When you re-raise as something else, use `from` so the original is still
   in the traceback.

### Python prefers EAFP

Coming from other languages you may check before acting:

```python
if "priority" in row:                      # LBYL
    p = row["priority"]
```

Python idiom is usually to try and handle failure:

```python
try:                                       # EAFP
    p = row["priority"]
except KeyError:
    p = 3
```

EAFP is preferred where the failure is genuinely exceptional, and it **avoids race conditions**:
between `if path.exists()` and `open(path)` the file can vanish. There is no gap in the EAFP version.

For simple defaults, use the built-in: `row.get("priority", 3)`.

---

## 4. Analogy

**An exception is a fire alarm; the traceback is the building's floor plan showing where it started.**

The alarm propagates upward until someone responds. If nobody does, the building is evacuated (the
program exits).

### Where the analogy breaks

1. **A fire alarm tells you only that there is a fire; a traceback tells you the exact line.** People
   still fail to read it, which is the single most common debugging failure.
2. **You can respond to an alarm by silencing it — and in Python that is `except: pass`.** The fire
   continues, unobserved. Software makes it far too easy to do this.
3. **Alarms are always bad news; exceptions are often normal control flow.** `StopIteration` ends
   every `for` loop. A `ValidationError` at your API boundary is the system working correctly.
4. **A fire has one origin. Exceptions chain** — one causes another, and `raise ... from ...` is how
   you keep both visible.

---

## 5. Detailed technical explanation

### 5.1 Reading a traceback

```
Traceback (most recent call last):
  File "/app/main.py", line 42, in <module>
    report = build_report(path)
             ^^^^^^^^^^^^^^^^^^
  File "/app/report.py", line 18, in build_report
    rows = load_rows(path)
           ^^^^^^^^^^^^^^^
  File "/app/loader.py", line 9, in load_rows
    return [int(r["priority"]) for r in read_csv(path)]
            ^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'high'
```

**Read it from the bottom.**

1. **Last line first:** the exception type and message. `ValueError`, and the offending value is
   `'high'`.
2. **Second from bottom:** the frame where it was raised — `loader.py` line 9. **This is where to
   look.**
3. **Upward:** how you got there. `main` → `build_report` → `load_rows`.
4. The `^^^^` markers (Python 3.11+) point at the exact sub-expression.

"Most recent call last" means **your code is usually near the bottom, library code below that**. When
the bottom frames are all inside a library, scan upward for the last line in *your* files — that is
usually where the mistake is.

### 5.2 Catching

```python
try:
    result = risky()
except FileNotFoundError:
    ...                      # most specific first
except OSError:
    ...                      # broader; FileNotFoundError is a subclass
except (ValueError, TypeError) as exc:
    logger.warning("bad input: %s", exc)
    raise
else:
    ...                      # only if NO exception
finally:
    ...                      # always
```

**Order matters:** the first matching `except` wins, so specific types must precede their parents.

**`else` versus putting code in the `try`:** code in `else` is *not* protected by the handlers, which
is what you want — otherwise a `ValueError` raised by your success path is caught by a handler meant
for the risky call, and you debug the wrong thing.

**`finally` always runs**, including when an exception propagates. Use it for cleanup — though `with`
(M2-L09) is better where it applies.

### 5.3 What not to catch

```python
try:
    do_work()
except:                      # NEVER
    pass
```

This catches `KeyboardInterrupt` and `SystemExit` too, so **Ctrl-C stops working**. And `pass`
discards the evidence.

```python
except Exception:            # acceptable ONLY at a top-level boundary
    logger.exception("request failed")
    return error_response()
```

`except Exception` is legitimate in exactly one place: an outermost boundary (a request handler, a
worker loop) where you must not crash. Even there, **always log with `logger.exception`**, which
records the full traceback (M2-L18).

**The failure mode to recognise:**

```python
try:
    chunk = retrieve(query)
except Exception:
    chunk = None             # now a retrieval outage looks like "no results"
```

A network outage, a bad credential and a genuine empty result now look identical. The system reports
"I found nothing" and everyone believes it. This is a real and common way RAG systems fail silently
(M7-L20).

### 5.4 Custom exceptions with context

```python
class IngestionError(Exception):
    """Base for all ingestion failures."""

class ChunkTooLargeError(IngestionError):
    def __init__(self, doc_id: str, size: int, limit: int) -> None:
        super().__init__(f"chunk from {doc_id} is {size} tokens, limit is {limit}")
        self.doc_id = doc_id
        self.size = size
        self.limit = limit
```

Two benefits:

- **A base class per subsystem** lets callers write `except IngestionError` and catch everything from
  that area without catching unrelated failures.
- **Structured attributes** mean the handler can *act* — retry with a smaller chunk, report the
  document ID — rather than parsing an English message.

### 5.5 Chaining: `raise ... from ...`

```python
try:
    config = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise ConfigError(f"{path} is not valid JSON") from exc
```

The traceback then shows both:

```
json.decoder.JSONDecodeError: Expecting value: line 3 column 5

The above exception was the direct cause of the following exception:

ConfigError: /app/config.json is not valid JSON
```

You get your meaningful message **and** the precise underlying cause. Without `from`, Python still
shows "During handling of the above exception, another exception occurred", which is noisier and
implies an accident rather than a deliberate translation.

Use `from None` only when you genuinely want to hide an implementation detail from callers.

### 5.6 Debugging

**`breakpoint()`** — a built-in that drops into the debugger:

```python
def score(chunk):
    breakpoint()          # execution stops here
    return chunk.rank * 2
```

Commands: `n` next line · `s` step into · `c` continue · `l` list source · `p expr` print ·
`pp expr` pretty-print · `w` where (the stack) · `u`/`d` move up/down frames · `q` quit.

`PYTHONBREAKPOINT=0` disables every `breakpoint()` without editing code — useful in CI.

**When `print` is fine:** a quick one-off in a script. **When it is not:** anything you might commit.
Use logging (M2-L18), which has levels, timestamps and can be turned off.

**Post-mortem debugging** — inspect the state at the moment of an unhandled crash:

```bash
python -m pdb -c continue script.py
```

**Useful introspection when you are lost:**

```python
type(obj), vars(obj), dir(obj)
import traceback; traceback.print_exc()
```

### 5.7 Assumptions and limitations

- Exceptions are relatively slow. Do not use them for ordinary control flow in a hot loop.
- `finally` runs even on `return`, and a `return` inside `finally` **overrides** the original return
  or exception — a subtle bug worth avoiding.
- In async code (M2-L13) an exception inside an un-awaited task can be swallowed entirely.

---

## 6. Worked example — hardening a loader

**Version 1 — no handling.**

```python
def load_config(path):
    return json.loads(open(path).read())
```

Every failure surfaces as a library-level error naming none of your context: `FileNotFoundError`
pointing at your line, `JSONDecodeError` with a line number in a file the message does not name, or
`UnicodeDecodeError` from a non-UTF-8 file.

**Version 2 — over-caught.**

```python
def load_config(path):
    try:
        return json.loads(open(path).read())
    except Exception:
        return {}
```

**Worse than version 1.** A typo in the path, a corrupt file and a permissions problem now all
produce an empty config. The application starts with silent defaults and misbehaves in a way nobody
connects to the config file. **Returning a plausible value on failure is how errors become
mysteries.**

**Version 3 — correct.**

```python
class ConfigError(Exception):
    """Configuration could not be loaded."""

def load_config(path: Path) -> dict:
    """Load JSON config.

    Raises:
        ConfigError: If the file is missing, unreadable, or not valid JSON.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(
            f"Config file not found: {path}. Copy config.example.json to {path.name}."
        ) from exc
    except PermissionError as exc:
        raise ConfigError(f"Cannot read {path}: permission denied.") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path} is not valid UTF-8 text.") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
        ) from exc
```

**What this achieves:**

1. **Each failure gets an actionable message.** The missing-file case even tells the user what to do.
2. **The caller catches one type** — `ConfigError` — regardless of which of four things went wrong.
3. **`from exc` preserves the original** for the person debugging.
4. **It still raises.** It does not invent a default. The caller decides the policy.
5. **The docstring documents what is raised**, so callers can handle it without reading the body.

And at the top level:

```python
try:
    config = load_config(Path("config.json"))
except ConfigError as exc:
    print(f"Startup failed: {exc}", file=sys.stderr)
    sys.exit(1)
```

Fail fast, clearly, at startup — the M2-L09 principle applied.

---

## 7. Practical activity

**File:** [`labs/m2/l10_exceptions.py`](../../labs/m2/l10_exceptions.py)

```bash
python3 labs/m2/l10_exceptions.py
```

Standard library only. Shows a real multi-frame traceback, the three loader versions side by side,
chaining with and without `from`, the `except: pass` failure, custom exceptions carrying structured
data, and the `finally`-overrides-return trap.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `traceback.format_exc()` | Captures a traceback as a string so the lab can display it without dying. |
| `raise ConfigError(...) from exc` | Chains; shows "direct cause". |
| `exc.__cause__` / `exc.__context__` | `__cause__` is set by `from`; `__context__` is set automatically. |
| `logger.exception(...)` | Logs message *and* traceback (M2-L18). |
| `finally: return` | Demonstrates the override trap. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08, Python 3.12.3:

```
==========================================================================
EXCEPTIONS, TRACEBACKS AND DEBUGGING
==========================================================================

--------------------------------------------------------------------------
1. READING A TRACEBACK - bottom up
--------------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/bharathr/self/Learning/claude/ai/labs/m2/l10_exceptions.py", line 47, in traceback_demo
    build_report()
  File "/home/bharathr/self/Learning/claude/ai/labs/m2/l10_exceptions.py", line 40, in build_report
    rows = load_rows()
           ^^^^^^^^^^^
  File "/home/bharathr/self/Learning/claude/ai/labs/m2/l10_exceptions.py", line 36, in load_rows
    return [int(r["priority"]) for r in read_rows()]
            ^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'high'

  Read it BOTTOM UP:
    last line     -> ValueError, and the bad value: 'high'
    frame above   -> load_rows(), the int() call. LOOK HERE FIRST.
    frames above  -> how you got there: build_report -> load_rows
    the ^^^^ marks the exact sub-expression that failed

--------------------------------------------------------------------------
2. THREE LOADERS, THREE OUTCOMES
--------------------------------------------------------------------------
  valid file
    v1 no handling: returned {'model': 'claude-sonnet-5'}
    v2 catch-all  : returned {'model': 'claude-sonnet-5'}
    v3 correct    : returned {'model': 'claude-sonnet-5'}

  malformed JSON
    v1 no handling: JSONDecodeError: Expecting ',' delimiter: line 2 column 3 (char 21)
    v2 catch-all  : returned {}
    v3 correct    : ConfigError: broken.json is not valid JSON: Expecting ',' delimiter at line 2, column 3

  missing file
    v1 no handling: FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmp9pszcpby/missi
    v2 catch-all  : returned {}
    v3 correct    : ConfigError: Config file not found: missing.json. Copy config.example.json to missing.json.

  Look at the 'missing file' block. v2 returned {} - exactly what
  it returns for a VALID but empty config. The application starts
  with silent defaults and misbehaves later, and nobody connects
  the symptom to a missing file. v2 is worse than no handling.

--------------------------------------------------------------------------
3. raise X from exc  vs  plain raise X
--------------------------------------------------------------------------
  WITH 'from exc':
    __cause__   = JSONDecodeError
    __context__ = JSONDecodeError
    json.decoder.JSONDecodeError: Expecting ',' delimiter: line 2 column 3 (char 21)
    The above exception was the direct cause of the following exception:
    ConfigError: broken.json is not valid JSON: Expecting ',' delimiter at line 2, column 3

  WITHOUT 'from' (plain raise):
    __cause__   = None
    __context__ = JSONDecodeError
    During handling of the above exception, another exception occurred:

  Both keep the original visible, but 'from' says DELIBERATE
  TRANSLATION ('direct cause'), while plain raise reads as an
  accident ('during handling ... another exception occurred').

--------------------------------------------------------------------------
4. CUSTOM EXCEPTIONS CARRY DATA, NOT JUST TEXT
--------------------------------------------------------------------------
    message : chunk from policy-2026.pdf is 1800 tokens, limit is 1024
    doc_id  : policy-2026.pdf
    size    : 1800
    limit   : 1024
    -> the handler can ACT: retry policy-2026.pdf with chunk size 512

  Catching the base class (IngestionError) picks up every failure
  from this subsystem without catching unrelated ones. The
  attributes let the handler decide, instead of parsing English.

--------------------------------------------------------------------------
5. try / except / else / finally
--------------------------------------------------------------------------
  success path : try -> try-end -> else -> finally
  failure path : try -> except -> finally

  'else' runs only on success AND is not protected by the
  handlers - so an error in your success path is not caught by a
  handler meant for the risky call.

  THE finally TRAP:
    a function that raises ValueError returned: 'from finally'
    The exception was DESTROYED by 'return' inside finally.
    No traceback. No log. The caller sees a normal return value.
    Never put return (or break/continue) inside finally.

--------------------------------------------------------------------------
6. 'NO RESULTS' MUST NOT LOOK LIKE 'IT BROKE'
--------------------------------------------------------------------------
  query             backend   bad version     good version
  refund policy     True      ['chunk-1']     ['chunk-1']
  unknown topic     True      []              []
  refund policy     False     []              raises RetrievalError

  In the bad version, rows 2 and 3 are IDENTICAL: []. One means
  'we have nothing on that topic', the other means 'the database
  is down'. The assistant says 'I could not find anything' in
  both cases, users believe it, and the outage is invisible
  until someone checks a dashboard. (M7-L13, M7-L20.)

==========================================================================
```

### 7.3 Reading the result

**Section 2 is the argument of the whole lesson, in one table.** Compare the three loaders across
three different situations:

| Loader | Missing file | Malformed JSON | Valid but empty config |
|---|---|---|---|
| v1 (no handling) | `FileNotFoundError` with a full path | `JSONDecodeError` naming no file | `{}` |
| v2 (catch-all) | **`{}`** | **`{}`** | **`{}`** |
| v3 (correct) | `ConfigError: Config file not found: missing.json. Copy config.example.json...` | `ConfigError: broken.json is not valid JSON: Expecting ',' delimiter at line 2, column 3` | `{}` |

**Look at v2's row: three completely different situations produce an identical result.** A typo in a
path, a corrupt file and a legitimately empty config are now indistinguishable. The application
starts successfully with silent defaults and misbehaves somewhere else entirely, and nobody connects
the symptom back to the config file.

That is why v2 is **worse than v1**. v1 at least fails loudly and immediately. v2 took a loud failure
and converted it into a quiet, delayed, misattributed one — while looking like careful defensive
programming. This is the single most common way well-intentioned error handling makes a system worse.

v3's messages name the file, the problem, the position, and in the missing-file case, **what to do
about it**.

**Section 3** shows that both chaining forms preserve the original — `__context__` is set either way
— but the wording differs. `raise ... from exc` produces *"The above exception was the direct cause
of the following exception"*; a plain `raise` produces *"During handling of the above exception,
another exception occurred"*. The first reads as a deliberate translation, the second as an accident
inside your handler. Use `from`.

**Section 4** shows why a custom exception beats a formatted string. The handler caught
`IngestionError` — the *base* class, picking up every failure from that subsystem — then read
`exc.doc_id`, `exc.size` and `exc.limit` as data and computed a retry with a smaller chunk size. No
regular expressions over an English message.

**Section 5's `finally` trap deserves a second look:**

```
a function that raises ValueError returned: 'from finally'
```

The function raised. The caller received a string. **No traceback, no log, no exception.** A `return`
inside `finally` destroys the in-flight exception entirely — one of very few Python constructs that
can make an error vanish leaving no trace at all.

Note also the execution order the lab prints: `try → try-end → else → finally` on success, and
`try → except → finally` on failure. The `else` block runs only on success and is **not** protected
by the handlers, which is exactly why it exists.

**Section 6 is the one that matters most for the rest of the course:**

```
query             backend   bad version     good version
unknown topic     True      []              []
refund policy     False     []              raises RetrievalError
```

In the bad version those two rows are byte-identical. One means *"we have nothing on that topic"*;
the other means *"the vector store is down"*. Your assistant will say **"I could not find anything
about that"** in both cases — confidently, plausibly, and in the second case, falsely.

Users believe it. No error is logged. No alert fires. The outage stays invisible until somebody
happens to check a dashboard — and meanwhile you have been telling customers you hold no information
on topics you document thoroughly.

This exact failure recurs in M7-L13 (abstention) and M7-L20 (debugging RAG). The fix is always the
same: **never let a failure masquerade as a legitimate empty result.**

**Verification:** confirm v2 returns `{}` for both malformed and missing files, that the `finally`
demo returns `'from finally'` instead of raising, and that rows 2 and 3 of section 6 differ only in
the good version.

---

## 8. Common mistakes and troubleshooting

1. **Bare `except:`.** Breaks Ctrl-C.
2. **`except Exception: pass`.** Hides the failure.
3. **Returning a plausible default on error.** Turns an error into a mystery.
4. **Not reading the traceback.** The answer is usually on the last two lines.
5. **Catching too broadly, too early.** Handle at the level that can actually decide.
6. **Re-raising without `from`.**
7. **`return` inside `finally`.** Silently discards the exception.
8. **Catching an exception you cannot act on.** If you cannot fix it, let it propagate.

| Symptom | Cause | Fix |
|---|---|---|
| Ctrl-C does not stop the program | Bare `except:` | Catch specific types |
| Failures produce no logs | Swallowed exception | Log with `logger.exception` and re-raise |
| "No results" when the service is down | Broad catch around retrieval | Catch narrowly; distinguish empty from failed |
| Traceback points only into library code | Your call is further up | Scan upward for the last frame in your files |
| A function returns `None` unexpectedly | `finally: return`, or a swallowed exception | Remove the `return` from `finally` |
| Error message names no context | Library exception unwrapped | Wrap in a domain exception with `from` |

---

## 9. Security, privacy, reliability and cost

- **Privacy.** Tracebacks contain **local variable values** in some frameworks, and exception messages
  often contain the offending input — which may be personal data or a credential. Never return a raw
  traceback to a user. Log it server-side with an ID, and return the ID (M2-L18, M10-L06).
- **Security.** Detailed errors help attackers map your system. Return generic messages externally,
  detailed ones internally. Never include a secret in an exception message — it will be logged.
- **Reliability.** Distinguishing "no results" from "the service failed" is the difference between a
  correct empty answer and a silent outage. This distinction is load-bearing in M7-L13 and M8-L13.
- **Cost.** A swallowed exception in a retry loop can retry forever. Always bound retries (M2-L14).

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

For each traceback fragment, state the exception type, the file and line where it was raised, and
your first hypothesis:

1. `KeyError: 'priority'` raised in `loader.py` line 12, called from `main.py` line 5.
2. `TypeError: unsupported operand type(s) for +: 'int' and 'str'` in `score.py` line 30.
3. `AttributeError: 'NoneType' object has no attribute 'text'` in `render.py` line 8.

For #3, explain why the *real* bug is usually not on line 8.

### Exercise 2 — Intermediate (~25 min)

Rewrite this function properly:

```python
def fetch_and_parse(url):
    try:
        data = requests.get(url).json()
        return data["results"][0]["title"]
    except:
        return "Unknown"
```

Requirements: catch specific exceptions; distinguish network failure, bad status, invalid JSON and
missing keys; define a custom exception with structured attributes; chain with `from`; and never
return a plausible-looking default that hides a failure. Then write five tests, one per failure mode.
(Use a stub instead of a real network call — you have not covered httpx yet.)

### Exercise 3 — Challenge (~25 min)

1. Write a function whose traceback is **four frames deep** and trigger it. Annotate each frame with
   what it tells you.
2. Demonstrate the difference between `raise X from exc` and plain `raise X`, showing both tracebacks
   and the values of `__cause__` and `__context__`.
3. Write a function with `try/except/else/finally` where all four blocks print. Run it twice — once
   succeeding, once failing — and record the execution order.
4. Add `return "from finally"` inside the `finally` block of a function that raises. Show that the
   exception disappears. Explain why this is dangerous.
5. Write `safe_retrieve(query)` that distinguishes three outcomes: results found, no results
   (legitimate), and retrieval failed. Show why collapsing the last two into `return []` is a bug,
   using a concrete user-visible consequence.

---

## 11. Quiz

**Q1.** In a traceback, where is the line that actually raised the exception?

- A. The first line after "Traceback".  B. The last frame listed, immediately above the exception
  type and message.  C. Always in your own code.  D. It is not shown.

**Q2.** Why is bare `except:` harmful?

- A. It is slow.
- B. It catches `KeyboardInterrupt` and `SystemExit` as well as errors, so Ctrl-C stops working, and
  it gives no indication of what was anticipated.
- C. It is a syntax error.
- D. It cannot be combined with `finally`.

**Q3.** What does `raise ConfigError(...) from exc` add?

- A. Nothing.
- B. It records the original exception as the direct cause, so the traceback shows both your
  meaningful message and the underlying failure.
- C. It suppresses the original.
- D. It retries.

**Q4.** Why is returning `{}` on any config-loading failure worse than raising?

- A. It is slower.
- B. A missing file, a permissions error and corrupt JSON all become an application that starts with
  silent defaults and misbehaves later in a way nobody connects to the config.
- C. Empty dicts are invalid.
- D. It is not worse.

**Q5.** Where is `except Exception` legitimate?

- A. Anywhere.
- B. At an outermost boundary such as a request handler or worker loop that must not crash — and even
  there it must log the full traceback.
- C. Never.
- D. Only in tests.

**Q6.** What does the `else` block of a `try` statement do?

- A. Runs on exception.  B. Runs only if no exception was raised, and is not protected by the
  handlers.  C. Always runs.  D. Replaces `finally`.

**Q7.** A retrieval function catches `Exception` and returns `[]`. What is the user-visible
consequence?

- A. Nothing.
- B. A service outage is indistinguishable from a genuine empty result, so the system confidently
  reports "I found nothing" while broken.
- C. The program crashes.
- D. Retries happen automatically.

**Q8.** What happens if a `finally` block contains `return`?

- A. Nothing special.
- B. It overrides any pending return value or exception, so the exception silently disappears.
- C. It is a syntax error.
- D. The exception is re-raised afterwards.

**Q9.** `AttributeError: 'NoneType' object has no attribute 'text'` — where is the bug most likely?

- A. On the line that raised it.
- B. Earlier, wherever the value became `None` — often a function that returned `None` on a path
  nobody expected.
- C. In the Python interpreter.
- D. In the import statements.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why a caught-and-logged exception is
acceptable but a caught-and-ignored one is a bug, even when the program continues working.

---

## 12. Revision notes

- **Read tracebacks bottom-up:** exception type and message last, raising frame just above, call
  chain upward. `^^^^` marks the exact sub-expression.
- **Catch the narrowest type you can.** Specific handlers before general ones.
- **Never bare `except:`** (breaks Ctrl-C). **`except Exception` only at an outermost boundary**, and
  always with `logger.exception`.
- **Never swallow.** No log, no metric, no behaviour change = a hidden bug.
- **Never return a plausible default on failure.** It converts errors into mysteries.
- **`raise X from exc`** preserves the cause. Use `from None` only to hide implementation detail
  deliberately.
- **Custom exceptions:** a base class per subsystem, plus structured attributes the handler can act
  on.
- `try/except/else/finally` — `else` runs only on success and is unprotected; `finally` always runs.
  **Never `return` in `finally`.**
- EAFP over LBYL, especially for files (avoids check-then-act races).
- `breakpoint()` over `print`; `PYTHONBREAKPOINT=0` disables them.
- **Distinguish "empty" from "failed".** Collapsing them is a silent-outage generator.

---

## 13. Completion checklist

- [ ] I can read a traceback and name the raising frame.
- [ ] I never write bare `except:`.
- [ ] I rewrote the Exercise 2 function with specific handlers and a custom exception.
- [ ] I compared `raise X from exc` with plain `raise X` and inspected `__cause__`.
- [ ] I recorded the execution order of `try/except/else/finally` in both cases.
- [ ] I saw `return` in `finally` swallow an exception.
- [ ] I can explain why "no results" must differ from "retrieval failed".
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "Errors and Exceptions".
  <https://docs.python.org/3/tutorial/errors.html> `[UNVERIFIED]`
- Python docs, built-in exception hierarchy.
  <https://docs.python.org/3/library/exceptions.html> `[UNVERIFIED]`
- Python docs, `pdb`. <https://docs.python.org/3/library/pdb.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L11 — HTTP and REST: Methods, Headers, Status Codes, Auth](M2-L11-http-rest.md)

You now have the language fundamentals. The next five lessons build toward calling and serving APIs —
starting with the HTTP knowledge you already have, made precise where it matters for AI provider
APIs.
