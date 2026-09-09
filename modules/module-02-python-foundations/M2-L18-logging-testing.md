# M2-L18 — Logging and Automated Testing with pytest

| | |
|---|---|
| **Lesson ID** | M2-L18 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L10](M2-L10-exceptions-debugging.md) |

---

## 1. Learning objectives

1. **Configure** logging with levels, structured fields and a correlation ID.
2. **Explain** why `print` is not logging, and what you lose by using it.
3. **Write** pytest tests using fixtures, parametrisation and exception assertions.
4. **Test** code that is nondeterministic or calls external services.
5. **Decide** what to test, and **recognise** tests that provide false confidence.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Log level** | Severity: DEBUG, INFO, WARNING, ERROR, CRITICAL. |
| **Logger** | A named channel; usually one per module. |
| **Handler** | Where records go: console, file, a collector. |
| **Formatter** | How a record is rendered. |
| **Structured logging** | Emitting machine-parseable fields rather than prose. |
| **Correlation ID** | An identifier tying every log line of one request together. |
| **`logger.exception`** | Logs at ERROR **with** the current traceback. |
| **pytest** | The standard Python test framework. |
| **Fixture** | Reusable setup, requested by naming it as a parameter. |
| **Parametrise** | Run one test function against many inputs. |
| **`pytest.raises`** | Asserts that a block raises a given exception. |
| **`monkeypatch`** | Temporarily replaces attributes or environment variables. |
| **Golden test** | Compares output against a stored expected value. |
| **Flaky test** | Passes and fails without code changes. |

---

## 3. Plain-language explanation

**Logging** is how you find out what happened in production, where you cannot attach a debugger.
**Testing** is how you find out whether it works before it gets there. Neither can be added
convincingly after the fact.

**`print` is not logging.** It has no severity, no timestamp, no source, no structure, no way to be
switched off, and it always goes to stdout.

```python
import logging

logger = logging.getLogger(__name__)     # one per module, named after it

logger.debug("chunk sizes: %s", sizes)          # diagnostic detail
logger.info("classified ticket %s", ticket_id)  # normal operation
logger.warning("retrying after 429")            # recoverable oddity
logger.error("classification failed")           # a real failure
logger.exception("unexpected error")            # ERROR + full traceback
```

**Use `%s` placeholders, not f-strings.** `logger.debug("sizes: %s", sizes)` only formats the string
*if DEBUG is enabled*; `logger.debug(f"sizes: {sizes}")` builds it every time, even when discarded.
On a hot path that is measurable, and it can also stringify an object you did not intend to touch.

---

## 4. Analogy

**Logging is a flight recorder; tests are pre-flight checks.**

The recorder tells you what happened after an incident. The checks stop you taking off broken.

### Where the analogy breaks

1. **A flight recorder captures everything. Logging everything is a privacy and cost problem** —
   request bodies contain personal data and volume costs money.
2. **Pre-flight checks are exhaustive and standardised. Tests are chosen**, and a passing suite means
   only that the cases you thought of pass.
3. **Recorders are write-only. Logs are read by people under pressure**, so a log nobody can search
   or correlate is nearly useless. Hence correlation IDs.
4. **Aircraft are deterministic. LLM output is not** (M1-L10), so tests must assert *properties*,
   never exact text (§5.6).

---

## 5. Detailed technical explanation

### 5.1 Configuration and levels

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
)
```

| Level | Use for |
|---|---|
| DEBUG | Detail useful only when diagnosing |
| INFO | Normal significant events: request handled, job finished |
| WARNING | Something unexpected but handled: a retry, a fallback |
| ERROR | An operation failed |
| CRITICAL | The process cannot continue |

**Configure logging once, at the application entry point** — never in a library or an imported module,
because whoever imports it loses control of their own configuration.

### 5.2 Structured logging and correlation IDs

Prose logs cannot be queried. Compare:

```
Classified ticket T-001 as billing with confidence 0.92 in 431ms
```
```json
{"event":"ticket_classified","ticket_id":"T-001","category":"billing",
 "confidence":0.92,"duration_ms":431,"request_id":"req_7f3c","model":"claude-sonnet-5"}
```

The second answers *"what is the p95 latency for billing classifications this week?"* The first
requires a regular expression that breaks when someone rewords the message.

```python
logger.info("ticket_classified", extra={
    "ticket_id": ticket_id, "category": result.category,
    "confidence": result.confidence, "duration_ms": elapsed_ms,
    "request_id": request_id,
})
```

**The correlation ID is the single most valuable field.** One request produces log lines from
retrieval, the model call, validation and the response. Without a shared ID they are unrelated lines
in a stream of thousands. With one, `request_id=req_7f3c` reconstructs the entire request. This
becomes agent tracing in M8-L17.

### 5.3 What must never be logged

| Never log | Why |
|---|---|
| API keys, tokens, `Authorization` headers | Logs are widely readable and long-lived |
| Passwords, even hashed | No reason to |
| Full request/response bodies | Personal data at volume (M10-L06) |
| Complete prompts containing user content | Same |
| `os.environ` | Every secret at once |

Log **identifiers and metrics**, not payloads: `ticket_id`, token counts, durations, statuses. If you
must sample bodies for debugging, sample deliberately, redact, and set a short retention.

**A dataclass `__repr__` prints every field** (M2-L07 §9), so `logger.info("user %s", user)` can emit
an email address you never intended. Log `user.id`.

### 5.4 pytest basics

```python
# tests/test_chunking.py
import pytest
from myapp.chunking import chunk_text

def test_returns_expected_number_of_chunks():
    chunks = chunk_text("a" * 25, size=10, overlap=3)
    assert len(chunks) == 4

def test_rejects_overlap_greater_than_size():
    with pytest.raises(ValueError, match="must be less than"):
        chunk_text("abc", size=10, overlap=15)
```

Run with `pytest -q`. Files are `test_*.py`, functions `test_*`, and plain `assert` is used — pytest
rewrites it to show the actual values on failure.

**Parametrisation** — one function, many cases:

```python
@pytest.mark.parametrize("size,overlap,expected", [
    (10, 0, 3), (10, 3, 4), (25, 0, 1),
])
def test_chunk_counts(size, overlap, expected):
    assert len(chunk_text("a" * 25, size=size, overlap=overlap)) == expected
```

Each case is reported separately, so a failure names the exact inputs.

**Fixtures** — reusable setup:

```python
@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    yield conn                 # the test runs here
    conn.close()               # teardown, even if the test failed
```

**`monkeypatch`** — for environment variables and attributes, undone automatically:

```python
def test_settings_require_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not set"):
        load_settings()
```

### 5.5 What to test

| Test | Value | Notes |
|---|---|---|
| Business logic and branches | **High** | Cheap, fast, catches real bugs |
| Boundary and error paths | **High** | Where bugs live; usually untested |
| Validation rules | **High** | Cheap and precise |
| Integration through your own API | Medium | `TestClient` (M2-L15) |
| Third-party libraries | **Low** | Not your job |
| Getters, trivial wrappers | **Low** | Cost without benefit |

**The habit worth building: when you fix a bug, write the failing test first.** It proves you
understood the cause and prevents the regression. A bug fixed without a test is a bug you will fix
again.

### 5.6 Testing nondeterministic and external code

This is the part specific to AI work, and the reason M2-L15's `dependency_overrides` and M2-L12's
`MockTransport` were introduced.

**Never assert exact model output.** It varies (M1-L10). Assert **properties**:

```python
def test_classification_is_valid(fake_model):
    result = classify("I was charged twice", model=fake_model)
    assert result.category in {"billing", "technical", "account", "sales"}
    assert 0.0 <= result.confidence <= 1.0
    assert result.reason                     # non-empty
```

**Seed anything random**, so a failure reproduces:

```python
random.seed(42)
```

**Inject the model client**, do not call the real one in unit tests — they would be slow, expensive,
flaky and would fail when offline.

**Golden tests** compare against a stored expected output. Useful for deterministic transforms
(chunking, prompt rendering); wrong for generation.

### 5.7 Tests that give false confidence

Recognising these matters as much as writing tests:

1. **Asserting what the code does rather than what it should do.** Written by reading the
   implementation, they pass forever and catch nothing.
2. **Mocking so heavily that only the mocks are tested.** If every collaborator is faked, the test
   asserts your fakes agree with each other.
3. **No assertion.** A test that only checks "it did not raise" passes when the output is nonsense.
4. **Testing the framework.** Verifying that FastAPI parses JSON is not your job.
5. **Flaky tests tolerated.** A suite people re-run until green is a suite nobody trusts. Fix or
   delete.

Coverage percentage measures *lines executed*, not *behaviour verified*. 100% coverage with weak
assertions is worse than 60% with sharp ones, because it produces confidence you have not earned.

### 5.8 Assumptions and limitations

- pytest 9.1.1 `[VERIFIED 2026-09-08]` by installation and execution here.
- Structured logging to JSON usually wants a library (`structlog`, `python-json-logger`); the
  standard library needs a custom formatter.
- Tests verify the cases you wrote. They do not prove correctness.

---

## 6. Worked example — making a function observable and tested

```python
def classify(text: str) -> dict:
    response = model.complete(text)
    return json.loads(response)
```

No logging, no error handling, untestable without the real model, and unvalidated output.

**Step 1 — inject the dependency.**

```python
def classify(text: str, *, model: ModelClient) -> Classification:
    ...
```

Now a fake can be passed in. This is M2-L07 composition, and it is what makes the rest possible.

**Step 2 — validate the output.**

```python
raw = model.complete(text)
return Classification.model_validate_json(raw)
```

**Step 3 — log the useful fields, not the payload.**

```python
def classify(text: str, *, model: ModelClient, request_id: str) -> Classification:
    started = time.perf_counter()
    try:
        raw = model.complete(text)
        result = Classification.model_validate_json(raw)
    except ValidationError:
        logger.exception("classification_invalid_output",
                         extra={"request_id": request_id, "chars": len(text)})
        raise
    logger.info("ticket_classified", extra={
        "request_id": request_id,
        "category": result.category,
        "confidence": result.confidence,
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "chars": len(text),
    })
    return result
```

**Note what is logged and what is not.** `chars=len(text)` rather than the text; the category and
confidence, which are useful and not personal; the duration; and the correlation ID. The ticket's
content — which may name a customer, an order or a complaint — never reaches the log.

**Step 4 — the tests.**

```python
class FakeModel:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[str] = []
    def complete(self, text: str) -> str:
        self.calls.append(text)
        return self.response

def test_classify_returns_validated_result():
    model = FakeModel('{"category":"billing","confidence":0.9,"reason":"refund"}')
    result = classify("I want a refund", model=model, request_id="req_1")
    assert result.category == "billing"
    assert 0.0 <= result.confidence <= 1.0
    assert model.calls == ["I want a refund"]        # it was called correctly

def test_classify_rejects_invalid_output():
    model = FakeModel('{"category":"nonsense","confidence":5}')
    with pytest.raises(ValidationError):
        classify("x", model=model, request_id="req_2")

def test_classify_logs_no_ticket_text(caplog):
    model = FakeModel('{"category":"billing","confidence":0.9,"reason":"r"}')
    with caplog.at_level(logging.INFO):
        classify("SECRET customer complaint", model=model, request_id="req_3")
    assert "SECRET" not in caplog.text                # privacy is asserted, not hoped for
```

**The third test is the interesting one.** Privacy properties can be *tested*. "We do not log user
content" is a claim; `assert "SECRET" not in caplog.text` is a check that fails in CI when someone
adds a helpful debug line. Make your governance commitments executable (M10-L13).

---

## 7. Practical activity

**File:** [`labs/m2/l18_logging_testing.py`](../../labs/m2/l18_logging_testing.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m2/l18_logging_testing.py
```

Demonstrates levels and filtering, the `%s`-versus-f-string cost, structured logs with a correlation
ID, redaction, and then **runs a real pytest suite in-process** — including a deliberately failing
test so you can read pytest's output, and the privacy test above.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `logger.debug("x: %s", value)` | Deferred formatting — only built if DEBUG is enabled. |
| `logger.exception(...)` | ERROR plus the full traceback. |
| `extra={...}` with a custom formatter | Structured fields alongside the message. |
| `caplog` | pytest fixture capturing log records for assertions. |
| `pytest.main([...])` | Runs the suite in-process so the lab is self-contained. |
| `assert "SECRET" not in caplog.text` | A privacy property, tested. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with pytest 9.1.1, pydantic 2.13.5, Python 3.12.3. Timings and temporary
paths vary:

```
==========================================================================
LOGGING AND TESTING
==========================================================================

--------------------------------------------------------------------------
1. LEVELS - what gets through
--------------------------------------------------------------------------
  logger level = WARNING
    WARNING  retrying after 429
    ERROR    classification failed

  logger level = DEBUG
    DEBUG    cache lookup took 2ms
    INFO     ticket classified
    WARNING  retrying after 429
    ERROR    classification failed

  At WARNING, the debug and info calls produced nothing. The code
  ran; the records were discarded. That is the control you lose
  entirely by using print().

--------------------------------------------------------------------------
2. WHY %s AND NOT AN f-STRING
--------------------------------------------------------------------------
  2000 logger.debug calls with DEBUG DISABLED:
    logger.debug('value: %s', obj)        0.4 ms   __str__ called 0 times
    logger.debug(f'value: {obj}')       526.9 ms   __str__ called 2000 times

  The f-string version formatted every single record that was then
  thrown away. On a hot path this is real cost - and it can also
  touch an object you did not intend to serialise.

--------------------------------------------------------------------------
3. STRUCTURED LOGGING WITH A CORRELATION ID
--------------------------------------------------------------------------
  One request, four components, one correlation ID:

{"level": "INFO", "logger": "m2l18", "event": "request_received", "request_id": "req_7f3c1e", "route": "/classify"}
{"level": "INFO", "logger": "m2l18", "event": "retrieval_completed", "request_id": "req_7f3c1e", "chunks": 5, "duration_ms": 42}
{"level": "INFO", "logger": "m2l18", "event": "ticket_classified", "request_id": "req_7f3c1e", "category": "billing", "confidence": 0.92, "duration_ms": 431, "chars": 128}
{"level": "INFO", "logger": "m2l18", "event": "response_sent", "request_id": "req_7f3c1e", "status": 200, "duration_ms": 495}

  Every line is machine-parseable, and request_id=req_7f3c1e
  reconstructs the whole request from a stream of thousands.

  Note what is NOT there: the ticket text. Only chars=128.

--------------------------------------------------------------------------
4. REDACTION - a backstop, not a substitute for discipline
--------------------------------------------------------------------------
  Someone adds a 'helpful' debug line:
    calling provider with key sk-***REDACTED*** and Bearer ***REDACTED***
    aws credential AKIA***REDACTED*** in config

  The filter caught all three. But note it is pattern-based: a
  credential in an unexpected format passes straight through.
  Redaction reduces damage; it does not remove the need to never
  log secrets in the first place.

--------------------------------------------------------------------------
5. A REAL PYTEST RUN
--------------------------------------------------------------------------
  Running: pytest -q (one test fails on purpose)

............F                                                            [100%]
=================================== FAILURES ===================================
__________________________ test_deliberately_failing ___________________________

    def test_deliberately_failing():
        """Included so you can read pytest's failure output."""
>       assert len(chunk_text("a" * 25, size=10, overlap=3)) == 99
E       AssertionError: assert 4 == 99
E        +  where 4 = len(['aaaaaaaaaa', 'aaaaaaaaaa', 'aaaaaaaaaa', 'aaaa'])
E        +    where ['aaaaaaaaaa', 'aaaaaaaaaa', 'aaaaaaaaaa', 'aaaa'] = chunk_text(('a' * 25), size=10, overlap=3)

/tmp/tmp99tibjql/test_chunking.py:82: AssertionError
=========================== short test summary info ============================
FAILED ../../../../../../tmp/tmp99tibjql/test_chunking.py::test_deliberately_failing
1 failed, 12 passed in 0.11s

  Read the failure block. pytest rewrote the assert to show the
  ACTUAL value (4) against the expected one (99). You did not have
  to write assertEqual or a message.

  Note three tests in that suite:
    test_classify_does_not_log_ticket_text - asserts a PRIVACY
      property. 'We do not log user content' becomes something CI
      enforces, and it fails the day someone adds a debug line.
    test_correlation_id_is_recorded - inspects caplog.RECORDS, not
      caplog.text. caplog.text renders only the message, so an
      assertion on an `extra` field fails there even though the
      field WAS logged. A real trap worth meeting once.
    test_that_passes_but_proves_nothing - passes, asserts nothing,
      and would still pass if classify() returned garbage.

==========================================================================
```

### 7.3 Reading the result

**Section 2 quantifies the `%s`-versus-f-string argument, and the numbers are larger than most people
expect:**

| Form | Time for 2,000 disabled DEBUG calls | `__str__` calls |
|---|---|---|
| `logger.debug("value: %s", obj)` | **0.4 ms** | **0** |
| `logger.debug(f"value: {obj}")` | **515.4 ms** | **2,000** |

DEBUG was **disabled**. Every one of those 2,000 strings was built and immediately discarded. The
`__str__` counter is the honest measure: the deferred form never touched the object at all.

The cost matters on a hot path, but the second column matters more. `__str__` ran 2,000 times on an
object you only meant to log conditionally — and if that object is a dataclass holding user data, the
f-string form serialises it whether or not the record is ever emitted.

**Section 3** shows what a request looks like when it is queryable. Four components, four JSON lines,
one `request_id`. You can answer "what is p95 latency for billing classifications this week?" with a
query rather than a regular expression. And the ticket text is absent — only `chars: 128`.

**Section 5's pytest run is where the lab found a real trap**, and it is worth reading carefully.

The first version of `test_correlation_id_is_recorded` asserted `"req_3" in caplog.text` — and
**failed**, even though `request_id` was definitely logged. The reason:

```
assert 'req_3' in 'INFO  chunking:chunking.py:56 ticket_classified\n'
```

**`caplog.text` renders only the message**, using its own formatter. Your `extra` fields are not in
it. They live on the record objects, so the correct assertion inspects `caplog.records`:

```python
record = next(r for r in caplog.records if r.getMessage() == "ticket_classified")
assert record.request_id == "req_3"
assert not hasattr(record, "text")      # the ticket body is never attached
```

This is a genuine trap: a developer writing this test the obvious way concludes their correlation ID
is missing and starts debugging the logging configuration. Worse, the *inverse* mistake is dangerous
— asserting `"SECRET" not in caplog.text` **passes** even if the secret were in an `extra` field,
because `caplog.text` would not show it. For privacy assertions on structured fields, check the
records.

Note also which assertions passed: `"SECRET" not in caplog.text` and `"Jane Doe" not in caplog.text`.
**A privacy commitment became a test.** "We do not log user content" is now something CI enforces, and
it will fail on the day someone adds a helpful debug line during an incident.

**The deliberate failure** shows pytest's assertion rewriting doing its job:

```
E   AssertionError: assert 4 == 99
E    +  where 4 = len(['aaaaaaaaaa', 'aaaaaaaaaa', 'aaaaaaaaaa', 'aaaa'])
```

It printed the actual value, the expression that produced it, and the full intermediate list — from a
bare `assert`, with no message and no `assertEqual`.

**And `test_that_passes_but_proves_nothing` passed**, as it always will. It calls `classify` and
asserts nothing. It would pass if the function returned an empty object, the wrong category, or
`None`. It contributes to your coverage percentage and verifies nothing at all — which is exactly why
§5.7 says coverage is not evidence.

**Verification:** confirm the f-string form shows ~2,000 `__str__` calls against 0, that exactly one
test fails, and that the failure output shows `assert 4 == 99` with the actual list.

---

## 8. Common mistakes and troubleshooting

1. **`print` instead of logging.**
2. **f-strings in log calls.** Formats even when the level is disabled.
3. **`logging.basicConfig` inside a library.** Hijacks the application's configuration.
4. **Logging secrets, bodies or whole objects.**
5. **No correlation ID.**
6. **`except: logger.error(...)` without `exception`** — losing the traceback.
7. **Asserting exact LLM output.**
8. **Tests with no assertions.**
9. **Tolerating flaky tests.**
10. **Chasing a coverage number.**

| Symptom | Cause | Fix |
|---|---|---|
| No log output | Level too high, or config never ran | `basicConfig(level=...)` at entry point |
| Duplicate log lines | `basicConfig` called twice, or handlers added repeatedly | Configure once |
| Tests pass locally, fail in CI | Unseeded randomness, time or path assumptions | Seed; use `tmp_path`; avoid CWD |
| `ModuleNotFoundError` in tests | Package not installed | `pip install -e .` (M2-L06) |
| Test suite slow | Real network or database calls in unit tests | Inject fakes |
| Coverage high, bugs still shipping | Weak assertions | Assert behaviour, not execution |

---

## 9. Security, privacy, reliability and cost

- **Privacy.** Logs are the most common accidental data-export route in AI applications. Prompts
  contain user text; responses contain more. Log identifiers and metrics; if you sample content,
  redact and expire it (M10-L06).
- **Security.** Never log credentials or `Authorization` headers (M2-L11 §7.3). Tracebacks may
  contain sensitive locals — log server-side, return an ID to the user (M2-L10 §9).
- **Reliability.** A correlation ID is what makes a production incident diagnosable. Add it before
  you need it.
- **Cost.** Log volume costs money at scale, and DEBUG in production is expensive and risky. Control
  it with configuration, not by deleting lines.
- **Governance.** Tests that assert privacy and authorization properties turn policy into something
  CI enforces (M10-L12).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Configure logging at INFO and emit one record at each of the five levels. Note which appear.
2. Change to DEBUG and re-run. Explain the difference.
3. Write a function that catches an exception and logs it with `logger.error`, then with
   `logger.exception`. Compare the output and state which you would want at 3am.

### Exercise 2 — Intermediate (~30 min)

Take `chunk_text` from M2-L05 §6 and:

1. Write six tests: normal case, empty input, whitespace-only input, `overlap >= size`, `size <= 0`,
   and a boundary case where the text length is an exact multiple of the step.
2. Parametrise the chunk-count test over at least four `(size, overlap, expected)` triples.
3. Add a fixture providing a sample document used by several tests.
4. Add logging that records document length and chunk count — **not the text** — and write a test
   asserting the text does not appear in the logs.
5. Run with `pytest -q` and report the summary line.

### Exercise 3 — Challenge (~30 min)

1. Write a `FakeModel` returning a scripted sequence of responses, including one invalid.
2. Test a `classify` function against it: valid output, invalid output raising `ValidationError`, and
   correct arguments passed to the model.
3. Write a test that would **wrongly pass**: assert only that no exception was raised. Explain what
   it fails to catch.
4. Write a genuinely flaky test using unseeded randomness. Run it 20 times and count failures. Then
   fix it and explain what you changed.
5. Add a JSON formatter emitting one object per line with `request_id`, `level`, `event` and any
   extras. Prove the output parses with `json.loads`.
6. Add a redacting filter replacing anything matching `sk-[A-Za-z0-9-]+` with `***`. Test it against
   a log line containing a fake key.

---

## 11. Quiz

**Q1.** Why use `logger.info("x: %s", value)` rather than an f-string?

- A. f-strings are not supported.
- B. The `%s` form defers formatting, so the string is only built if that level is enabled.
- C. It is shorter.
- D. f-strings cannot contain variables.

**Q2.** What does `logger.exception(...)` add over `logger.error(...)`?

- A. Nothing.  B. It logs at ERROR and includes the current traceback.
- C. It re-raises.  D. It exits the program.

**Q3.** Why is a correlation ID the most valuable structured field?

- A. It is short.
- B. One request produces log lines from many components; a shared ID is what lets you reconstruct
  the whole request from a stream of thousands of interleaved lines.
- C. It replaces timestamps.
- D. It is required by the logging module.

**Q4.** Which should never appear in logs?

- A. Ticket IDs  B. Durations  C. Full request bodies and `Authorization` headers  D. Status codes

**Q5.** Why must you not assert exact LLM output in a test?

- A. It is slow.
- B. Generation is nondeterministic, so the test fails for reasons unrelated to correctness — assert
  properties instead.
- C. Assertions cannot compare strings.
- D. You should assert exact output.

**Q6.** What is wrong with a test that only checks no exception was raised?

- A. Nothing.
- B. It passes when the output is completely wrong — it verifies the code ran, not that it produced
  a correct result.
- C. It is too slow.
- D. It cannot be parametrised.

**Q7.** Where should `logging.basicConfig` be called?

- A. In every module.
- B. Once, at the application entry point — never in a library, which would hijack the importing
  application's configuration.
- C. In each test.
- D. It is not needed.

**Q8.** What does 100% test coverage prove?

- A. The code is correct.
- B. Only that every line executed during the tests — with weak assertions it can accompany serious
  bugs, and it may create confidence you have not earned.
- C. There are no bugs.
- D. The tests are fast.

**Q9.** How do you test that user content is not being logged?

- A. Read the code carefully.
- B. Capture logs with `caplog` and assert the sensitive string is absent — turning a policy claim
  into a check CI enforces.
- C. It cannot be tested.
- D. Disable logging in tests.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain what you would log for one LLM
request in production, and what you would deliberately omit.

---

## 12. Revision notes

- **`print` is not logging**: no level, no timestamp, no source, no structure, cannot be switched off.
- One logger per module: `logging.getLogger(__name__)`. **Configure once, at the entry point.**
- **`%s` placeholders, not f-strings** — deferred formatting.
- **`logger.exception`** for ERROR + traceback.
- **Structured fields** beat prose; **the correlation ID is the most valuable one**.
- **Never log:** credentials, `Authorization`, bodies, prompts with user content, `os.environ`,
  whole objects (dataclass `__repr__` prints everything).
- pytest: `test_*.py`, plain `assert`, `pytest.raises`, `@parametrize`, fixtures with `yield`
  teardown, `monkeypatch`, `caplog`, `tmp_path`.
- **Test logic, boundaries and error paths.** Do not test the framework.
- **When you fix a bug, write the failing test first.**
- **Never assert exact LLM output — assert properties.** Seed randomness. Inject fakes.
- False confidence: no assertions · over-mocking · testing the implementation · tolerated flakiness ·
  **coverage as a goal**.
- **Privacy and authorization properties can be asserted in tests.** Make governance executable.

---

## 13. Completion checklist

- [ ] I configure logging once, at the entry point, with levels.
- [ ] I use `%s` placeholders and `logger.exception`.
- [ ] My logs carry a correlation ID and no payloads.
- [ ] I wrote parametrised tests and a fixture with teardown.
- [ ] I tested an error path with `pytest.raises`.
- [ ] I wrote a test asserting user content is not logged.
- [ ] I can name three kinds of test that give false confidence.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python docs, `logging` HOWTO. <https://docs.python.org/3/howto/logging.html> `[UNVERIFIED]`
- pytest documentation. <https://docs.pytest.org/> `[UNVERIFIED]`; pytest 9.1.1
  `[VERIFIED 2026-09-08]` by installation and execution here.
- OWASP Logging Cheat Sheet.
  <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L19 — Secret Handling](M2-L19-secrets.md)

You now know not to log secrets. Next: where they should actually live, how they reach your process,
and what to do when one leaks.
