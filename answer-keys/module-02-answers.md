# Module 2 — Answer Key

**Do not read this until you have attempted the questions.**

Contents: [L01](#l01) · [L02](#l02) · [L03](#l03) · [L04](#l04) · [L05](#l05) · [L06](#l06) ·
[L07](#l07) · [L08](#l08) · [L09](#l09) · [L10](#l10) · [L11](#l11) · [L12](#l12) · [L13](#l13) ·
[L14](#l14) · [L15](#l15) · [L16](#l16) · [L17](#l17) · [L18](#l18) · [L19](#l19) · [L20](#l20) ·
[Module assessment](#module-assessment)

---

<a id="l01"></a>
## M2-L01 — Terminal, Python, venv, pip

### Quiz

**Q1 — B.** Activation prepends the venv's `bin` to `PATH` and sets `VIRTUAL_ENV`.
*Not A:* it links to the system interpreter rather than downloading one. *Not C:* the system Python is
untouched. *Not D:* nothing is compiled.

**Q2 — B.** `sys.prefix != sys.base_prefix`.
*Not A:* a `.venv` directory may exist without being active. *Not C/D:* neither indicates a venv.

**Q3 — C.** Create and activate a venv. *Not A:* `--break-system-packages` does what its name says.
*Not B:* `sudo` makes it worse. *Not D:* system tools depend on that Python.

**Q4 — B.** `python -m pip` guarantees the pip belonging to the running interpreter.
*Not A:* speed is identical. *Not C:* pip is not deprecated. *Not D:* it does not change the target.

**Q5 — B.** Distribution name ≠ import name: `python-dotenv` → `import dotenv`.
*Not A:* the install succeeded. *Not C/D:* neither is a real rule.

**Q6 — B.** Node isolates per project by default; Python isolation is opt-in.
*Not A:* size is incidental. *Not C:* both are deletable. *Not D:* the difference is the source of
most Python environment pain.

**Q7 — B.** `==` pins direct dependencies; transitive ones may still float. Full reproducibility needs
`pip freeze` or a lock tool.
*Not A:* overstates it. *Not C:* pins are honoured. *Not D:* platform matters but pins are not
Linux-only.

**Q8 — B.** The venv is working correctly — the package exists only inside it.
*Not A:* nothing is corrupted. *Not C:* installing globally is the mistake being avoided.
*Not D:* Python is fine.

**Q9 — C.** Delete and recreate; a venv is a rebuildable cache.
*Not A/D:* hand-editing hides the real problem. *Not B:* far too drastic.

**Q10 — Rubric.** Full marks require: (a) naming the reproducibility or conflict problem, (b) one
concrete consequence (breaking a system tool, a colleague's install differing, CI failing), (c) under
70 words.
*Model:* "Without a venv, every project shares one set of packages. Installing something for one
project can break another, or a system tool that depends on Python. And your machine accumulates
packages nobody declared — so your code works for you and fails in CI, because CI installs only what
`requirements.txt` names."

### Exercises

**E1.** Marks for capturing both outputs and noting the two changes: `sys.prefix` diverging from
`sys.base_prefix`, and the dependency count going from partial to 10/10.

**E2.** (1) `pip freeze` lists more lines than `requirements.txt` because it includes transitive
dependencies. (2) `pip show fastapi` lists `Requires: pydantic, starlette` and `Required-by:` empty
in a fresh install. (3) Only `httpx` present; demonstrates venvs are fully independent. (4) Deleting
`.venv-test` leaves `.venv` untouched.

**E3.**
1. `ModuleNotFoundError: No module named 'fastapi'`. Correct behaviour: the package was installed
   into the venv only, and the system Python cannot see it. That isolation is the point.
2. `pydantic.VERSION` reports `1.10.13`; re-running `pip install -r requirements.txt` restores
   `2.13.5`. **What it shows:** pip installs exactly what the pin says, including downgrades — the
   file is the source of truth, not "whatever is newest".
3. `python -c "import json; print(json.dumps({}))"` fails with `AttributeError: module 'json' has no
   attribute 'dumps'` (or similar), because your local `json.py` was found first. **Shadowing.** It
   is nasty because the failure appears inside code you did not write, and it can break a
   *dependency* rather than your own code.
4. *Acceptable rule:* never name a file after a standard-library module; check with
   `python -c "import <name>; print(<name>.__file__)"` if an import behaves strangely.

---

<a id="l02"></a>
## M2-L02 — Variables, numbers, strings

### Quiz

**Q1 — C.** `-4`. `//` floors toward −∞. *Not A:* that is `int(-7/2)`, which truncates toward zero.

**Q2 — B.** 0.1 and 0.2 have no exact binary representation.
*Not A:* every IEEE-754 language behaves this way. *Not C/D:* neither is true.

**Q3 — C.** `if value is None:`.
*Not A:* `not value` also catches `0`. *Not B:* works but `is None` is correct style and cannot be
overridden. *Not D:* `len()` fails on an int.

**Q4 — B.** `==` compares value; `is` compares object identity.

**Q5 — C.** `[]` is falsy in Python and truthy in JavaScript.

**Q6 — B.** `f"{score:.1%}"` → `'87.3%'`.
*Not C:* gives `0.9%`. *Not D:* gives `87.34000000000001%`.

**Q7 — B.** `Decimal(0.1)` receives an already-inexact float.

**Q8 — C.** `count=7` — the `=` suffix prints expression and value.

**Q9 — B.** `[1,2,3,4]`; two names, one list object.

**Q10 — Rubric.** Must name `[]` and `{}` being falsy in Python (truthy in JS), and ideally that
`==` does not coerce. Under 70 words.

### Exercises

**E1.** `3.5` · `3` · `-4` · `1` · `1` · `1024` · `'555'` · `[0,0,0]` · `False` · `True` · `True` ·
`False`. The commonly-missed ones are `-7 // 2`, `-7 % 2`, `"5" * 3` and `bool([0])`.

**E2.** Full marks require `Decimal` throughout and exact alignment. Grand total for the given rows:
`120000 × 0.0008 = 96.0000`, `15400 × 0.0030 = 46.2000`, `820 × 0.0150 = 12.3000`, total
**`154.5000`**. Verify with `Decimal("154.5") == total`.

**E3.** (1) `safe_get` must use `key in config and config[key] is not None`. (2) Test cases: absent
key, `None`, `0`, `""`, `False`. (3) `config.get(key) or default` fails on `0`, `""` and `False` —
three of five. (4) *Acceptable:* the naive form reads more naturally and is shorter, which is exactly
why it survives review; reviewing Python requires checking whether a falsy value is a legitimate
input. (5) Any correct example, e.g. `if not text.strip(): return []` in `chunk_text` — correct there
because an empty collection genuinely means "nothing to do".

---

<a id="l03"></a>
## M2-L03 — Collections

### Quiz

**Q1 — B.** `tuple` — immutable and hashable, so usable as a dict key.

**Q2 — B.** `None`; `sort()` mutates in place.

**Q3 — B.** Hash lookup is O(1); a list scan is O(n).

**Q4 — B.** `KeyError`; use `d.get()` for the JavaScript-like behaviour.

**Q5 — B.** `[[1,2,99],[3,4]]` — `copy()` is shallow.

**Q6 — B.** `[['x'],['x'],['x']]` — three references to one list.

**Q7 — C.** `list(dict.fromkeys(items))` preserves order.

**Q8 — B.** A deterministic tie-break, so equal-scoring items keep a stable order across runs.

**Q9 — B.** An empty dict. `set()` is an empty set.

**Q10 — Rubric.** Must state "when testing membership more than once against the same collection" and
quantify roughly (orders of magnitude at scale; ~2 lookups is break-even).

### Exercises

**E1.** `[1,2,3,4]` · `[1,2,1,2]` · `{'a':2,'b':3}` · `{2,3}` · `2` · `'x'` (a string!) · `('x',)` ·
`None` · `[1,2,3]` · `[3,1,2]`.

**E2.** Full marks require `defaultdict(set)`, both search functions using set operations, and `rank`
sorting by `(-count, doc_id)`. **The tie-break is required** because two documents matching the same
number of terms would otherwise appear in whatever order the dict iteration produced, making results
non-reproducible between runs.

**E3.** (1) Timings must show the set column flat and the list column growing linearly.
(2) The ratio grows in proportion to n. (3) **Verified in the authoring environment: for a *single*
lookup the list always wins**, because building the set is itself O(n) — so there is no n at which a
one-shot set conversion pays. (4) The set-based dedup is dramatically faster. (5) *Acceptable rule:*
"convert to a set when you will test membership against the same collection more than once."

---

<a id="l04"></a>
## M2-L04 — Control flow and comprehensions

### Quiz

**Q1 — B.** `enumerate`.

**Q2 — B.** 2 pairs, silently; `strict=True` raises.

**Q3 — B.** `if` after `for` filters; `if/else` before `for` transforms.

**Q4 — B.** Left to right, as you would nest them.

**Q5 — B.** The generator yields values one at a time; no list is built.

**Q6 — B.** `[2,2,2]` — late binding captures the variable.

**Q7 — B.** The iterator walks positions in a shrinking list.

**Q8 — C.** The token-budget loop: it carries state and must stop early.

**Q9 — B.** Generators are consumed once, silently.

**Q10 — Rubric.** Must distinguish independent per-item transformation (comprehension) from
accumulated state or early exit (loop), and mention readability limits.

### Exercises

**E1.** (1) `[x*2 for x in range(10) if x % 3 == 0]`. (2) `{w: len(w) for w in [...]}`.
(3) `{n[0] for n in [...]}`. (4) **Not a comprehension** — use `sum([1,2,3,4])`. Full marks for
recognising that a built-in already exists and that a comprehension here would be a step backwards.

**E2.** (1) `['doc-001','doc-003']`. (2) `{'policy': 3, 'blog': 1}`. (3) A set comprehension with
punctuation stripped. (4) `sum(r["score"] for r in results) / len(results)` — a generator, no list.
(5) Cannot be a comprehension because each decision depends on the running total and it must `break`.

**E3.** (2) Two fixes: default argument `lambda i=i: i`, or a factory function creating a new scope.
(3) Roughly 175,000× difference (list ~81 MB, generator ~464 bytes). (4) `next()` with a generator
expression and a `None` default is the version to ship — shorter and does not rely on loop-`else`,
which many readers misread. (5) Marks for a scenario where truncation produces a *plausible* result:
e.g. zipping 100 features with 98 labels silently trains on 98 rows and reports a normal-looking
accuracy.

---

<a id="l05"></a>
## M2-L05 — Functions, arguments, scope

### Quiz

**Q1 — B.** `[1,2,3]` — one list, created once at definition.

**Q2 — B.** Fresh list per call, and `is None` distinguishes "not supplied" from "supplied empty".

**Q3 — B.** `[1,2]` — rebinding affects only the local name.

**Q4 — B.** Everything after `*` is keyword-only.

**Q5 — B.** Positional booleans are unreadable and silently swappable.

**Q6 — B.** `UnboundLocalError`.

**Q7 — B.** The default is evaluated once, at definition time.

**Q8 — B.** `overlap == size` gives an obscure `range` error; `overlap > size` **silently returns an
empty list**, producing an empty index with no error anywhere.

**Q9 — B.** Build and return new objects by default; name it if you must mutate.

**Q10 — Rubric.** Must connect the shared mutable default to **cross-request data exposure** in a
long-running process, not merely to surprising behaviour.

### Exercises

**E1.** `[1]`, `[1,2]`, `[1,2,3]` — one shared list. `g` prints `[1]` (rebinding), `h` prints
`[1,99]` (mutation).

**E2.** Full marks require: `filters=None`, no mutation of `data` (build new dicts), `*` before the
flags, type hints, a docstring stating input is not modified, and `retries` validated as `>= 0`.
Three tests must assert the caller's original list and dicts are unchanged.

**E3.** (1) Starts at 0, 7, 14, 21. (2) `ValueError: range() arg 3 must not be zero`.
(3) Returns `[]` with **no error at all** — worse because it is silent and produces an empty index.
(4) The counter lives in the enclosing function's scope, captured by the closure; `nonlocal` is
needed to rebind it. (5) `def send(msg: str, *, urgent: bool = False, retry: bool = True,
silent: bool = False, log: bool = True) -> None` — keyword-only prevents swaps, defaults reduce the
call site, type hints document intent.

---

<a id="l06"></a>
## M2-L06 — Modules and packages

### Quiz

**Q1 — B.** `__init__.py` (for a regular package).

**Q2 — B.** The script's directory (or CWD in a REPL).

**Q3 — B.** The script directory is searched before the standard library.

**Q4 — B.** Callers depend on a stable public API, so internals can be reorganised.

**Q5 — B.** A module with relative imports was run directly.

**Q6 — B.** Without `src/`, imports succeed whether or not the package is correctly installed.

**Q7 — B.** Extract shared code to a third module.

**Q8 — B.** Module-level code running on import, including during test collection.

**Q9 — B.** It runs on first import, so every importer pays — including serverless cold starts.

**Q10 — Rubric.** Must say it hides a real packaging problem, breaks when the file moves or is
imported differently, and that `pip install -e .` is the correct fix.

### Exercises

**E1.** (1) `sys.path[0]` is `.../l06_demo`. (2) Still `.../l06_demo` — `sys.path[0]` is the
**script's** directory, not the CWD, so it works. (3) `python3 -c "import ticketkit"` fails because
`sys.path[0]` is now the CWD, which contains no `ticketkit`.

**E2.** (4) `run_demo.py` still works **unchanged** because it imports from `ticketkit`, and
`__init__.py` absorbed the move by updating its own import. That is precisely the value of a
re-exported public API.

**E3.** (1) `ImportError: cannot import name 'X' from partially initialized module`.
(2) Third module (cleanest, fixes the design); function-level import (works, hides the coupling);
`TYPE_CHECKING` (only for annotations). (3) `pathlib.py` breaks the demo with
`ImportError: cannot import name 'Path' from 'pathlib' (.../pathlib.py)` — **the parenthesised path
is the diagnosis**. `json.py` breaks nothing because the demo never imports `json`, which makes it a
latent bug. `__pycache__` must be cleared because a stale compiled copy can keep the failure alive.
(4) After `pip install -e .`, the package resolves from any directory because it is on the
interpreter's path rather than depending on the CWD.

---

<a id="l07"></a>
## M2-L07 — Classes and dataclasses

### Quiz

**Q1 — B.** `__init__`, `__repr__`, `__eq__`.

**Q2 — B.** It would be one list shared by every instance.

**Q3 — C.** It constructs fine and fails later somewhere unrelated.

**Q4 — B.** When data comes from outside your program.

**Q5 — B.** Hashability, which enables set-based deduplication.

**Q6 — B.** The same shared dict.

**Q7 — B.** Testable, swappable, shallow; duck typing removes the need for a base class.

**Q8 — B.** Structural typing checked statically.

**Q9 — B.** It prints every field, including secrets.

**Q10 — Rubric.** Must give the origin-of-data rule and mention that a dict offers no field checking.

### Exercises

**E1.** Frozen dataclass with `duration_minutes` as a `@property`. Two bugs prevented: a typo in a
field name becomes `AttributeError` instead of a silent new key; and the fields are documented and
autocompleted rather than discovered by reading call sites.

**E2.** (2) `frozen=True` is required because `set()` needs hashable items; without it,
`TypeError: unhashable type`. (5) `score="high"` constructs successfully and fails inside `sorted`
with `TypeError: bad operand type for unary -: 'str'` — a message naming neither the class, the
field, nor the origin. **That is the motivation for M2-L08.**

**E3.** (5) The inheritance version requires constructing a real retriever (and therefore a real
index) to test ranking logic, because the logic and the data access live in the same object.
(6) *Acceptable:* inheritance is right for a genuine is-a relationship with shared implementation —
exception hierarchies being the clearest case.

---

<a id="l08"></a>
## M2-L08 — Type hints and Pydantic

### Quiz

**Q1 — B.** It runs and returns `"ab"`.

**Q2 — B.** Data from outside your program.

**Q3 — B.** Rejects unknown fields; surfaces invented LLM fields and blocks mass assignment.

**Q4 — B.** Coerces to `5`.

**Q5 — B.** Structured data usable for API responses and repair prompts.

**Q6 — B.** Normalises before the `Literal` check.

**Q7 — B.** Compare fields against each other.

**Q8 — B.** Only that the shape is right.

**Q9 — B.** At boundaries, once per crossing.

**Q10 — Rubric.** Must state that the model may not comply, that the output is untrusted input
(possibly influenced by injected content), and that validation is the only check that does not itself
depend on the model behaving.

### Exercises

**E1.** `def f(items: list[str]) -> dict[str, int]` · `x: float | None` ·
`order: Literal["asc","desc"]` · `def f(cb: Callable[[str], bool]) -> None` ·
`d: dict[tuple[str,int], list[float]]`.

**E2.** Full marks require `model_config = ConfigDict(extra="forbid")`, a `field_validator` stripping
whitespace before the length check, and a `model_validator(mode="after")` for the cross-field rule.
Eight tests must include the cross-field case, and each must inspect `exc.errors()` rather than
`str(exc)`.

**E3.** (3) `loc` values such as `('citations', 0, 'doc_id')` pinpoint the element.
(5) **The key point:** a payload with a fabricated `doc_id`, a plausible quote and `confidence: 0.97`
passes every constraint. This proves validation guarantees **shape, never truth** — the citation must
be verified against the actual retrieved source, which is Module 7 (M7-L12).

---

<a id="l09"></a>
## M2-L09 — Files, CSV, JSON, env vars

### Quiz

**Q1 — B.** Platform separators and normalisation.

**Q2 — B.** Relative to the CWD, which differs under cron.

**Q3 — B.** The `csv` module handles line endings itself; universal newline translation mis-splits
quoted fields containing newlines.

**Q4 — B.** `str` — every CSV value is a string.

**Q5 — C.** `tuple` returns as a `list`.

**Q6 — B.** `True` — non-empty string.

**Q7 — B.** Otherwise a configuration error becomes an intermittent runtime error.

**Q8 — C.** Truncates immediately.

**Q9 — B.** Resolve and check `is_relative_to(base)`.
*Not A:* rejecting dots is both incomplete and breaks legitimate names. *Not C:* `os.path.join` is
not a safety mechanism. *Not D:* useful defence in depth, not sufficient.

**Q10 — Rubric.** Must say one bad row should not fail 10,000 good ones, and give a case where
aborting **is** right (a financial import where partial application is worse than none).

### Exercises

**E2.** (5) The `csv` module quotes the comma and the embedded newline correctly; a hand-joined
version produces a file that parses into the wrong number of columns, silently.

**E3.** (3) `bool("false")` is `True`; fix by comparing against a set of accepted strings.
(4) `safe_join` must block **both** `../../etc/passwd` and the absolute `/etc/passwd` — the latter
because an absolute right-hand operand discards the base entirely, which a `..`-only check misses.

---

<a id="l10"></a>
## M2-L10 — Exceptions and debugging

### Quiz

**Q1 — B.** The last frame, immediately above the exception.

**Q2 — B.** It catches `KeyboardInterrupt` and `SystemExit`.

**Q3 — B.** Records the original as the direct cause.

**Q4 — B.** Three different situations become one indistinguishable result.

**Q5 — B.** At an outermost boundary, with the full traceback logged.

**Q6 — B.** Runs only on success, and is not protected by the handlers.

**Q7 — B.** An outage is indistinguishable from a genuine empty result.

**Q8 — B.** It overrides the pending return value **or exception**.

**Q9 — B.** Earlier, wherever the value became `None`.

**Q10 — Rubric.** Must distinguish *handled and recorded* from *hidden*: a swallowed exception
removes the evidence that anything went wrong, so the failure is discovered by a user rather than by
you.

### Exercises

**E1.** (3) The real bug is wherever the `None` originated — commonly a function that returns `None`
on an unanticipated path. Line 8 is where it surfaced, not where it was created.

**E2.** Full marks require distinct handlers for `httpx.ConnectError` / `TimeoutException`,
`HTTPStatusError`, `json.JSONDecodeError` and `KeyError`/`IndexError`, a custom exception with
structured attributes, `raise ... from exc`, and **no** `return "Unknown"`.

**E3.** (3) Success: `try → try-end → else → finally`. Failure: `try → except → finally`.
(4) The exception vanishes; the caller receives a normal return value with no traceback or log.
(5) Concrete consequence: the assistant tells a user "I could not find anything about our refund
policy" while the vector store is down — the user believes it, no alert fires, and the outage is
invisible.

---

<a id="l11"></a>
## M2-L11 — HTTP and REST

### Quiz

**Q1 — B.** Retry `5xx`, `429`, `408`, `425`; never other `4xx`.

**Q2 — B.** `401` = who are you; `403` = you may not.

**Q3 — B.** Not idempotent; after a timeout you cannot tell whether it applied.

**Q4 — B.** Server de-duplicates; the key is generated **once**, before the first attempt.

**Q5 — B.** Only that the stream started.

**Q6 — B.** Reduces *perceived* latency.

**Q7 — B.** A total timeout either kills long answers or misses a stall.

**Q8 — B.** `request-id`.

**Q9 — B.** Wait at least 30 s; consider client-side throttling.

**Q10 — Rubric.** Must state the ambiguity: a `500` proves the server rejected the work, whereas a
timeout leaves you unable to tell whether the operation completed — so a retry may duplicate a
state-changing action.

### Exercises

**E1.** 1 `401` no · 2 `400` no · 3 `503`/`529` yes · 4 `403` no · 5 `429` yes after `Retry-After` ·
6 `413` no.

**E2.** (2) `409` normally means a genuine conflict that repeating will not resolve; it *can* be
retryable for an optimistic-concurrency conflict where you re-read and re-apply. (3) A status-only
check passes `200` with `{"error": "quota exceeded"}`; the fix inspects the body for an `error` key.

**E3.** (1) The distinguishing signal is the **terminal event** (`message_stop`); absence of it plus
a closed connection means truncation. (4) Same key returns the original result; a new key creates a
second record.

---

<a id="l12"></a>
## M2-L12 — httpx

### Quiz

**Q1 — B.** 5 seconds, far too short for LLM calls.

**Q2 — B.** Connection pooling avoids repeated DNS/TCP/TLS.

**Q3 — B.** Time between chunks.

**Q4 — B.** `httpx.ConnectError`.

**Q5 — B.** The server may have processed it.

**Q6 — B.** The error response flows on as ordinary data.

**Q7 — B.** Transport-layer interception; real client code runs.

**Q8 — B.** So you can debug and port between providers.

**Q9 — B.** A provider change becomes a one-file change.

**Q10 — Rubric.** Must name the three costs absent on loopback: DNS resolution, network round-trip
latency, TLS handshake.

### Exercises

**E1.** (1) `httpx.ReadTimeout` (or `ConnectTimeout` depending on the phase). (2) `httpx.ConnectError`
— it proves the request never reached the server, so a retry is unconditionally safe, whereas a
timeout is ambiguous. (3) Without `raise_for_status()` the code proceeds with an error body.

**E2.** Full marks require one reusable client, four-part timeouts, a domain `ApiError` carrying
status + message + request ID + `retryable`, and five `MockTransport` tests with **no network**.

**E3.** (2) DNS, network latency, TLS. (4) With `read=0.05` against a server sleeping 0.05 s between
chunks, the read timeout fires mid-stream — demonstrating that the per-chunk timeout measures the gap
between chunks, not total duration.

---

<a id="l13"></a>
## M2-L13 — Async and concurrency

### Quiz

**Q1 — B.** I/O-bound work.

**Q2 — B.** Blocks the entire event loop.

**Q3 — B.** A coroutine object is created and never runs.

**Q4 — B.** Rate limits, file descriptors, memory, and overwhelming the downstream service.

**Q5 — B.** Exceptions returned as values; successes preserved — but you must check for them.

**Q6 — B.** The GIL; async gives concurrency in waiting, not parallelism in computing.

**Q7 — C.** `ProcessPoolExecutor`.

**Q8 — B.** `TaskGroup` cancels siblings and raises an `ExceptionGroup`.

**Q9 — B.** It cannot yield, so it blocks the loop.

**Q10 — Rubric.** Must name a blocking call inside a coroutine as the likely cause and give the
diagnostic: find the `async def` with no `await`.

### Exercises

**E2.** (2) Without `return_exceptions=True`, `gather` raises on the first `500` and **all** the
successful results are lost. With it, 40 results and 10 exceptions are returned.

**E3.** (1) Expect: sequential baseline; `asyncio` ≈ no gain; threads **often slower than
sequential** (GIL plus coordination overhead); processes ~2–3× faster. (5) A task created without a
retained reference may be garbage-collected mid-execution, and its exception surfaces only as a
warning at destruction. Fix: keep it in a set with `add_done_callback(set.discard)`.

---

<a id="l14"></a>
## M2-L14 — Retries and backoff

### Quiz

**Q1 — C.** `401`.

**Q2 — B.** Jitter spreads retries *across* clients.

**Q3 — C.** Wait at least 20 s — the server's instruction beats your algorithm.

**Q4 — B.** Retries continue after the caller has given up.

**Q5 — C.** 27.

**Q6 — B.** `ConnectError` proves nothing happened; `ReadTimeout` does not.

**Q7 — B.** Sustained failure; retries turn every request into a slow failure.

**Q8 — B.** Semaphore = concurrency; token bucket = rate.

**Q9 — B.** `monotonic` never goes backwards.

**Q10 — Rubric.** Must describe the amplification loop: a degradation causes failures → retries
multiply load → the service degrades further → more failures. Credit for mentioning synchronised
retries (no jitter) or multi-layer amplification.

### Exercises

**E1.** 1 no · 2 yes, 20 s · 3 yes, jittered · 4 **only with an idempotency key** · 5 yes,
`uniform(0, min(30, 8))` · 6 no.

**E2.** (2) Exactly **one** call for a `400`. (3) The deadline must stop it, and the message should
name the deadline. (4) `Retry-After: 3` must override the jittered delay.

**E3.** (1) Fixed backoff puts all 500 clients in one bucket; full jitter reduces the peak to roughly
a tenth. (4) Semaphore bounds *simultaneous* requests; the bucket bounds requests *per second*;
retries handle *transient failure*. None substitutes for another: 10 sequential requests violate no
concurrency limit but can still exceed a rate limit.

---

<a id="l15"></a>
## M2-L15 — FastAPI

### Quiz

**Q1 — B.** Name in path → path; Pydantic model → body; otherwise → query.

**Q2 — B.** `422`.

**Q3 — B.** Filters the response to exactly the declared fields.

**Q4 — B.** Otherwise any client could act as another user.

**Q5 — B.** Mass assignment.

**Q6 — B.** `def` — the threadpool makes blocking safe.

**Q7 — B.** Substitute collaborators with no patching.

**Q8 — B.** `403` confirms existence, enabling enumeration.

**Q9 — B.** Once at startup via `lifespan`.

**Q10 — Rubric.** Must connect unvalidated input to a concrete exploit (injection, mass assignment,
resource exhaustion) rather than to "bad data".

### Exercises

**E2.** (2) `404` rather than `403` so the response does not confirm the ticket exists — log the real
reason server-side with the request ID. (3) Proof requires returning an object that **does** contain
`internal_cost` and showing it absent from the JSON.

**E3.** (4) Ten concurrent requests against a `def` route sleeping 0.5 s complete in roughly
0.5–1 s (threadpool); against an `async def` route using `time.sleep` they take ~5 s, because the
loop is blocked. This is the M2-L13 trap inside a web framework.

---

<a id="l16"></a>
## M2-L16 — SQL

### Quiz

**Q1 — B.** Attacker text becomes part of the statement.

**Q2 — B.** SQL and values travel separately.

**Q3 — B.** Identifiers; allow-list them.

**Q4 — B.** Comparison with `NULL` is never true.

**Q5 — B.** `WHERE` before grouping; `HAVING` after.

**Q6 — B.** 101 queries where a join would do.

**Q7 — B.** A transaction; it does not close the connection.

**Q8 — B.** It silently becomes an inner join.

**Q9 — B.** A function on the column, or a leading wildcard.

**Q10 — Rubric.** Must give the two different jobs: Pydantic produces a good error message at the
boundary for the caller; the database guarantees the invariant even when a script, migration or
second service writes directly.

### Exercises

**E2.** (2) `"priority; DROP TABLE tickets"` must be rejected by the allow-list, not escaped.
(4) N+1 issues 201 queries; the join issues 1.

**E3.** (1) `channel = "email' OR '1'='1"` returns **every** row from the vulnerable function and
**zero** from the safe one, because the payload becomes a literal channel name. (3) With
`foreign_keys = OFF` (SQLite's default) the orphan inserts happily; with it ON,
`IntegrityError: FOREIGN KEY constraint failed`. (4) Counts 501 / 500 / 501 — the middle query
silently drops the customer with no tickets.

---

<a id="l17"></a>
## M2-L17 — Git and dependencies

### Quiz

**Q1 — B.** Commit part of your working changes.

**Q2 — B.** Still in history and retrievable.

**Q3 — B.** Rotate the credential.

**Q4 — B.** It only stops untracked files being added.

**Q5 — B.** On pushed commits others may have based work on.

**Q6 — B.** Pinned, with a lockfile and a recorded Python version.

**Q7 — B.** `git log -S "string"`.

**Q8 — B.** Prompts, evaluation datasets, model IDs and settings, retrieval configuration.

**Q9 — B.** Python version and platform.

**Q10 — Rubric.** Must say instructions encode assumptions the author cannot see (installed tools,
existing files, remembered steps), so only executing them from a clean clone reveals the gaps.

### Exercises

**E2.** (3) `git show <sha>:.env` prints the key in full after the file has been deleted. **What it
proves:** deletion removes the file from the working tree, not from history; the credential remains
in every clone, fork and CI cache. (4) Rotation first, because it is the only step that stops the
leaked credential working; everything else is cleanup.

**E3.** (5) *Acceptable:* a grep-based script is a cheap backstop that catches the common formats,
but it cannot recognise credentials in unexpected formats, does not scan history, and is trivially
bypassed with `--no-verify` — so it complements CI scanning and push protection rather than replacing
them.

---

<a id="l18"></a>
## M2-L18 — Logging and testing

### Quiz

**Q1 — B.** Deferred formatting.

**Q2 — B.** ERROR plus the traceback.

**Q3 — B.** It reconstructs one request from interleaved lines.

**Q4 — C.** Full request bodies and `Authorization` headers.

**Q5 — B.** Generation is nondeterministic; assert properties.

**Q6 — B.** It passes when the output is completely wrong.

**Q7 — B.** Once, at the entry point.

**Q8 — B.** Only that every line executed.

**Q9 — B.** Capture logs and assert the sensitive string is absent.

**Q10 — Rubric.** Should log: request ID, model, token counts, duration, status, category or outcome.
Should omit: the prompt, the user's text, the full response, credentials.

### Exercises

**E2.** (5) Expect `10 passed` for a correct six-test + parametrised suite; the exact number depends
on your parametrisation.

**E3.** (3) A test that only checks "no exception" would pass if `classify` returned `None`, the
wrong category, or an empty object. (5) **Note the trap the lab demonstrates:** `caplog.text` renders
only the *message*, so asserting on an `extra` field there fails even though the field was logged —
inspect `caplog.records` instead. The inverse is more dangerous: `"SECRET" not in caplog.text` would
pass even if the secret were in an `extra` field.

---

<a id="l19"></a>
## M2-L19 — Secret handling

### Quiz

**Q1 — C.** Rotate and revoke.

**Q2 — B.** The generated `__repr__` prints every field.

**Q3 — B.** URLs are recorded by proxies, access logs and browser history.

**Q4 — C.** Short-lived credentials from an identity provider.

**Q5 — B.** Scope limits what an attacker can do even if the secret leaks.

**Q6 — B.** Nothing — the leaked credential still works.

**Q7 — B.** A diagnostic aid, not protection.

**Q8 — B.** Local development only.

**Q9 — B.** Humans reliably miss a few characters in a large diff.

**Q10 — Rubric.** Must state that the secret remains in history and in every clone, that you cannot
prove nobody copied it, and that only rotation removes the risk.

### Exercises

**E2.** (4) A loose pattern catches unusual formats and produces noise; a strict one is quiet and
misses real credentials. **The failure mode that matters is a noisy scanner being switched off.**

**E3.** (5) *Acceptable:* a short-lived credential cannot be exfiltrated usefully because it expires;
it is issued per-workload so the blast radius is bounded; and there is no static value to commit,
log or screenshot in the first place.

---

<a id="l20"></a>
## M2-L20 — Docker

### Quiz

**Q1 — B.** The expensive `pip install` layer stays cached across source edits.

**Q2 — B.** Present in the earlier layer and recoverable.

**Q3 — B.** The build command remains in the image metadata.

**Q4 — B.** Bound to `127.0.0.1` inside the container.

**Q5 — B.** The shell form does not forward signals.

**Q6 — B.** `.env`, `.git` and `.venv` being copied in.

**Q7 — B.** Reduces the blast radius on compromise.

**Q8 — B.** The final image keeps none of the builder's layers.

**Q9 — B.** A tag can be republished; a digest is immutable.

**Q10 — Rubric.** Must state that layers are immutable and additive, that the file is recoverable via
`docker save` and the command via `docker history`, and that the correct fix is runtime injection or
a BuildKit secret.

### Exercises

**E3.** (1) Extraction: `docker save`, untar, find the layer blob containing `app/.env`, read it.
(2) With one `RUN`, the file is gone but `docker history --no-trunc` still shows the command — the
metadata is a separate leak channel from the filesystem. (4) As root an attacker could install
packages, modify any file including the application, and attempt kernel-level container escapes that
require elevated capabilities; as `appuser` they are confined to files that user can write.

---

<a id="module-assessment"></a>
## Module 2 Assessment — Answer Key

**Scoring:** Section A 1 each (12) · Section B 3 each (24) · Section C 24. **Total 60.** Pass = 42.

### Section A (12 marks)

**A1 — C** (−4, floors) · **A2 — B** (shared default) · **A3 — B** (set once) ·
**A4 — C** (not enforced) · **A5 — B** (non-empty string) · **A6 — C** (`401`) ·
**A7 — B** (`ConnectError`) · **A8 — B** (blocks the loop) · **A9 — B** (spreads across clients) ·
**A10 — B** (filters the response) · **A11 — B** (`IS NULL`) · **A12 — C** (still in the layer).

### Section B (24 marks, 3 each)

**B1.** 1: `Decimal(0.1)` receives a float that is *already* inexact. 1: the `Decimal` then faithfully
represents that error (≈0.1000000000000000055511151231257827). 1: the string form parses the decimal
literal exactly.

**B2.** 1: `not percent` is true for `0`, so a legitimate 0% discount is silently replaced by the
default. 1: it is also true for `None`, so the two cases are indistinguishable. 1: fix with
`if percent is None:`.

**B3.** 1: attacker text becomes part of the statement, so it can change the query's meaning. 1:
parameterisation sends SQL and values separately, so no value can alter the structure. 1: identifiers
cannot be parameterised — validate against an allow-list, never escape.

**B4.** 1: a service outage becomes indistinguishable from a genuine empty result. 1: the system
reports "nothing found" confidently and users believe it. 1: no error is logged and no alert fires, so
the outage is invisible until someone checks a dashboard.

**B5.** 1: 3 × 3 × 3 = **27**. 1: during a partial degradation this multiplies load 27-fold. 1: at
exactly the moment the dependency can least absorb it, potentially converting a degradation into an
outage. (Bonus-worthy: retry at exactly one layer.)

**B6.** 1: otherwise a client could set `owner_id` to another user and create or read data as them.
1: `extra="forbid"` rejects unknown fields outright rather than silently ignoring them. 1: which
blocks mass assignment, including fields added to the model later.

**B7.** 1: rotate and **revoke** the old credential. 1: assess exposure, check for misuse, then clean
up history, then fix the cause. 1: rotation is first because it is the only step that stops the leaked
credential working — you cannot prove nobody copied it.

**B8.** 1: `%s` defers formatting, so nothing is built when the level is disabled. 1: measurable cost
on a hot path (the lab shows ~1,300× for 2,000 disabled calls). 1: it also avoids calling `__str__` on
an object you did not intend to serialise — which may itself be expensive or may render user data.

### Section C — Practical (24 marks)

**Task 1 — Audit (8 marks).** One mark per two correctly identified defects, to a maximum of 8.
A complete list:

| # | Defect | Severity | Lesson |
|---|---|---|---|
| 1 | Hard-coded API key in source | **Critical** | M2-L19 |
| 2 | SQL built by f-string in `INSERT` — injection | **Critical** | M2-L16 |
| 3 | SQL injection in the `SELECT` by title | **Critical** | M2-L16 |
| 4 | SQL injection in `ORDER BY {sort}` — no allow-list | **Critical** | M2-L16 |
| 5 | SQL injection in the per-row user lookup | **Critical** | M2-L16 |
| 6 | `owner_id` taken from the request body — impersonation | **Critical** | M2-L15 |
| 7 | No authentication or authorization at all | **Critical** | M2-L15 |
| 8 | `payload: dict` — no validation of any field | Major | M2-L08 |
| 9 | `payload["title"]` raises `KeyError` on a missing field → 500 | Major | M2-L10 |
| 10 | N+1 query in `list_documents` | Major | M2-L16 |
| 11 | Returns the raw row, leaking every column | Major | M2-L15 |
| 12 | `print` instead of logging, and it prints the document row | Major | M2-L18 |
| 13 | Module-level connection shared across threads | Major | M2-L16 |
| 14 | No transaction around insert-then-select | Minor | M2-L16 |
| 15 | Re-selecting by `title` is wrong — titles are not unique | Major | — |
| 16 | No `status_code=201` on creation | Minor | M2-L15 |
| 17 | No pagination on `list_documents` | Minor | M2-L15 |
| 18 | No `response_model` | Major | M2-L15 |

**Task 2 — Rewrite (10 marks).**

| Requirement | Marks |
|---|---|
| `DocumentCreate` with `extra="forbid"`, constrained fields, no `owner_id` | 2 |
| `DocumentOut` as a separate model, used as `response_model` | 1 |
| Authentication and authorization as dependencies; `owner_id` from the principal | 2 |
| All SQL parameterised; `sort` allow-listed with a comment | 2 |
| Insert returning the created row by **id**, inside a transaction | 1 |
| Domain exceptions translated at the boundary; no `HTTPException` in the data layer | 1 |
| Structured logging with a request ID and no document body | 1 |

**Task 3 — Tests (4 marks).** Half a mark per required test, to 4. All must run without a network.
The log test must assert the document body is absent from `caplog.text`.

**Task 4 — Note (2 marks).** 1 for choosing a defensible "first fix", 1 for the reasoning.

*Full-marks answers:* **the hard-coded key** (it is already compromised, rotation is urgent, and it is
a two-minute fix) or **`owner_id` from the body** (it is a complete authorization bypass exploitable
by anyone). Either is defensible. Choosing a minor defect, or listing everything without prioritising,
scores 0 for the first mark.

*Model answer:* "Fix the hard-coded key first. Everything else is a vulnerability someone might
exploit; that key is a credential that has already been distributed to everyone with repository
access and is sitting in Git history. It needs rotating today, not fixing. Once it is rotated I would
take the `owner_id` from the request body second — right now any caller can create documents as any
user, which is a complete authorization bypass and needs no skill to exploit. The SQL injection is
equally severe but slightly harder to reach, since it needs a crafted payload. The N+1 query and the
missing pagination are real, but they are performance problems, and performance problems do not leak
customer data."

### Remediation guidance

| Lost marks on | Re-read |
|---|---|
| A1, B1 | M2-L02 §5.1–5.2 |
| A2 | M2-L05 §5.3 |
| A3 | M2-L03 §5.5 |
| A4, B6 | M2-L07 §5.3, M2-L08 §3 |
| A5 | M2-L09 §5.5 |
| A6, A7, B5 | M2-L11 §5.2, M2-L12 §5.3, M2-L14 §5.1 |
| A8 | M2-L13 §5.5 |
| A9 | M2-L14 §5.3 |
| A10, C task 2 | M2-L15 §5.3–5.5 |
| A11, B3, C SQL items | M2-L16 §5.2–5.3 |
| A12, B7 | M2-L19 §5.6, M2-L20 §5.5 |
| B2 | M2-L02 §5.6 |
| B4 | M2-L10 §5.3 |
| B8 | M2-L18 §3 |
