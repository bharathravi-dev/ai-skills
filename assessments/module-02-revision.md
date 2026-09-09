# Module 2 — Revision Guide

Read this before the assessment. It condenses twenty lessons into the ideas that recur for the rest
of the course.

If a line here reads as unfamiliar rather than merely terse, return to that lesson.

---

## 1. One line per lesson

| Lesson | The thing to retain |
|---|---|
| L01 | Python isolation is **opt-in**. `venv` + `python -m pip` + pinned versions. |
| L02 | `is None` for optionals, truthiness for collections. **Money is `Decimal`.** |
| L03 | `in` on a list is O(n), on a set O(1) — **from two lookups onward, build the set**. |
| L04 | Comprehensions for independent per-item work; **generators for anything large**. |
| L05 | **Mutable defaults are shared across calls.** Validate at the boundary and raise. |
| L06 | Import resolution = script dir → PYTHONPATH → site-packages. `pip install -e .`. |
| L07 | Dataclass annotations **do not validate**. Mutable class attributes leak between users. |
| L08 | **Data from outside your program → Pydantic.** LLM output counts as outside. |
| L09 | Every CSV value is a string; env vars are strings; **`bool("false")` is `True`**. |
| L10 | Never swallow. **"Empty" must not look like "failed".** |
| L11 | `4xx` stop, `5xx`/`429` retry. `POST` is not idempotent. `200` on a stream means little. |
| L12 | Explicit timeouts; one client; **the exception type answers the retry question**. |
| L13 | I/O-bound → async. **Bound concurrency** — unbounded is often slower *and* unsafe. |
| L14 | Exponential backoff **with full jitter**. Bound by attempts, deadline **and cost**. |
| L15 | `response_model` filters; `extra="forbid"` blocks mass assignment; **identity from the token**. |
| L16 | **Parameterise values, allow-list identifiers.** `IS NULL`. Transactions. Indexes. |
| L17 | A committed secret is compromised — **rotate first**. Version prompts and datasets too. |
| L18 | `%s` not f-strings. Correlation IDs. **Privacy properties can be asserted in tests.** |
| L19 | **Scope beats storage.** `field(repr=False)`. Rotate → assess → check → clean up → fix. |
| L20 | Layers are additive — **a deleted secret is still recoverable**. Runtime config only. |

---

## 2. Numbers worth remembering

| Number | Source | Meaning |
|---|---|---|
| **28,448×** | L03 lab | Set vs list membership at n=100,000 |
| **2 lookups** | L03 lab | The break-even point for building a set |
| **174,844×** | L04 lab | List comprehension vs generator peak memory |
| **1,288×** | L18 lab | f-string vs `%s` in disabled debug logging |
| **134×** | L16 lab | Indexed vs unindexed query on 20,000 rows |
| **27.9×** | L12 lab | Pooled vs unpooled HTTP connections |
| **3× slower** | L13 lab | Unbounded `gather` vs `semaphore(10)` |
| **500 → 46** | L14 lab | Peak retry load with vs without jitter |
| **20,000 rows** | L16 lab | Returned by `channel = 'email' OR '1'='1'` |

---

## 3. The rules that are not negotiable

- **Never build SQL by formatting a value.** Parameterise. Allow-list identifiers.
- **Never trust an identity from the request body.** It comes from the verified token.
- **Never log** credentials, bodies, prompts with user content, or whole objects.
- **Never commit** `.env`, keys, `.venv/`, customer data.
- **Never put a secret in a Docker layer**, even if you delete it afterwards.
- **Never retry a `4xx`** (except 408/425/429).
- **Never assert exact LLM output** in a test.
- **Never use `float` for money.**
- **Never mutate a list you are iterating.**
- **Never let a failure look like an empty result.**

---

## 4. The decision tables

### Which container? (L03)

| Need | Use |
|---|---|
| Ordered, changes | `list` |
| Ordered, fixed, hashable | `tuple` |
| Key lookup | `dict` |
| Membership / uniqueness | `set` |

### Which model type? (L07, L08)

| Data origin | Use |
|---|---|
| Throwaway internal | `dict` |
| Internal, you control it | `@dataclass` |
| **From outside your program** | **Pydantic** |

### Retry or not? (L11, L12, L14)

| Signal | Retry |
|---|---|
| `ConnectError` | Yes — never reached the server |
| `ReadTimeout` | Reads yes; writes only with an idempotency key |
| `429`, `5xx`, `408`, `425` | Yes, with jitter; honour `Retry-After` |
| Other `4xx` | **No** |

### Concurrency tool? (L13)

| Work | Tool |
|---|---|
| Network / disk / DB | `asyncio` |
| Blocking library | `asyncio.to_thread` or a thread pool |
| CPU-heavy | `ProcessPoolExecutor` |
| One call | Plain synchronous code |

---

## 5. The recurring idea

Almost every lesson in this module is one principle in a different costume:

> **Untrusted input must be validated at the boundary, in deterministic code, before it can act.**

- SQL injection (L16) — a value became a command.
- Mass assignment (L15) — a field became a permission.
- Prompt injection (Module 5) — text became an instruction.
- Path traversal (L09) — a filename became a location.

All four are the same failure. The defence is always the same shape: **parameterise or allow-list,
never escape-and-hope**, and decide permissions in code the attacker cannot influence.

---

## 6. Re-run these before the assessment

Each takes under a minute:

```bash
python3 labs/m2/l03_collections.py        # set vs list, the crossover
python3 labs/m2/l04_control_flow.py       # generator memory, the four bugs
python3 labs/m2/l05_functions.py          # mutable defaults, validation
python3 labs/m2/l10_exceptions.py         # empty vs failed
python3 labs/m2/l16_sql.py                # a real SQL injection
bash     labs/m2/l17_git.sh               # a secret retrieved from history
python3 labs/m2/l19_secrets.py            # the repr leak
```

With the venv active:

```bash
python labs/m2/l08_pydantic.py            # nine LLM failure modes
python labs/m2/l13_async.py               # bounded beats unbounded
python labs/m2/l14_retries.py             # the thundering herd
python labs/m2/l15_fastapi.py             # authorization and filtering
```

---

## 7. What Module 2 was for

You can now build a service that validates its input, enforces permissions in code, persists data
safely, retries sensibly, logs without leaking, and is tested without a network.

**Module 5 adds a language model to exactly this structure.** Every control here is what makes that
safe — because a model is one more untrusted input source, and Module 2 is where you learned how to
treat those.

→ [Module 2 assessment](module-02-assessment.md)
