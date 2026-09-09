# Module 2 Assessment — Python and Software Foundations

| | |
|---|---|
| **Covers** | M2-L01 … M2-L20 |
| **Questions** | 20 (12 multiple choice, 8 short answer) + 1 practical assignment |
| **Total marks** | 60 |
| **Pass mark** | 42 (70%) |
| **Time** | ~2 hours (75 min for Sections A–B, 45 min for Section C) |
| **Answer key** | [`answer-keys/module-02-answers.md`](../answer-keys/module-02-answers.md#module-assessment) |

**Conditions.** Closed book, no editor for Sections A and B. Section C may use a machine.

---

## Section A — Recall and understanding (12 marks, 1 each)

**A1.** What does `-7 // 2` evaluate to?

- A. `-3`  B. `-3.5`  C. `-4`  D. `3`

**A2.** `def f(x, acc=[]): acc.append(x); return acc`. What does the third call return?

- A. `[3]`  B. `[1, 2, 3]`  C. `[]`  D. `None`

**A3.** You must test membership against the same 10,000-item collection inside a loop. What do you
do?

- A. Keep the list; conversion costs too much.
- B. Convert to a `set` once before the loop.
- C. Sort the list first.
- D. Use a `tuple`.

**A4.** A dataclass field is annotated `score: float`. You construct it with `score="high"`. What
happens?

- A. `TypeError` at construction.  B. Coerced to a float.
- C. Nothing — annotations are not enforced at runtime.  D. A warning is printed.

**A5.** `DEBUG=false` is set in the environment. What does `bool(os.getenv("DEBUG"))` return?

- A. `False`  B. `True`  C. `None`  D. It raises

**A6.** Which HTTP status should **never** be retried?

- A. `503`  B. `429`  C. `401`  D. `504`

**A7.** Which exception proves the request never reached the server?

- A. `httpx.ReadTimeout`  B. `httpx.ConnectError`  C. `httpx.HTTPStatusError`  D. `TimeoutError`

**A8.** An `async def` function contains no `await` anywhere. What does that indicate?

- A. It is correctly written.
- B. It cannot yield control, so it blocks the event loop and gains nothing from being a coroutine.
- C. It will not run.
- D. It runs in a thread pool.

**A9.** Why is jitter added to exponential backoff?

- A. To make retries faster.
- B. Backoff leaves clients synchronised with each other; jitter spreads retries across clients,
  preventing a thundering herd when an outage ends.
- C. It is required by HTTP.
- D. To reduce cost.

**A10.** In FastAPI, what does `response_model=TicketOut` do?

- A. Validates the request body.
- B. Filters the outgoing response to exactly those fields, stripping anything extra.
- C. Sets the status code.
- D. Generates tests.

**A11.** `WHERE resolved_at = NULL` returns zero rows although many are NULL. Why?

- A. A syntax error.  B. Comparison with `NULL` is never true; use `IS NULL`.
- C. The column is misspelled.  D. NULL is stored as an empty string.

**A12.** You wrote a secret to a file in one `RUN` instruction and deleted it in the next. What is
its status in the image?

- A. Removed.  B. Encrypted.
- C. Still present in the earlier layer and recoverable by anyone who can pull the image.
- D. Removed when the container stops.

---

## Section B — Short answers (24 marks, 3 each)

Answer in 3–5 sentences. Marks are for precision.

**B1.** Explain why `Decimal("0.1")` must be constructed from a string rather than from the float
`0.1`. *(3)*

**B2.** A colleague writes `if not percent: percent = DEFAULT` for an optional discount percentage.
State the bug and the fix. *(3)*

**B3.** Explain what makes `f"SELECT * FROM t WHERE id = '{value}'"` dangerous, why parameterisation
fixes it, and what to do for a dynamic **column** name. *(3)*

**B4.** A retrieval function catches `Exception` and returns `[]`. Describe the user-visible failure
this creates and why it is worse than raising. *(3)*

**B5.** Your service, its HTTP client and the API gateway each retry three times. State the total
upstream calls for one user request and why this is dangerous during a degradation. *(3)*

**B6.** In a FastAPI endpoint, why must `owner_id` come from the verified token rather than the
request body, and what does `extra="forbid"` add? *(3)*

**B7.** A secret was committed and pushed. Give the response steps in order and justify why the first
one is first. *(3)*

**B8.** Explain why `logger.debug("value: %s", obj)` is preferable to
`logger.debug(f"value: {obj}")`, referring to both cost and side effects. *(3)*

---

## Section C — Practical assignment (24 marks)

You may use a machine and the course materials.

### Scenario

You inherit this endpoint. It works, and it is wrong in many ways.

```python
import sqlite3
from fastapi import FastAPI

app = FastAPI()
conn = sqlite3.connect("app.db")
API_KEY = "sk-live-9f8e7d6c5b4a"

@app.post("/documents")
def create_document(payload: dict):
    owner = payload["owner_id"]
    title = payload["title"]
    body = payload["body"]
    conn.execute(
        f"INSERT INTO documents (owner_id, title, body) VALUES ('{owner}', '{title}', '{body}')"
    )
    conn.commit()
    row = conn.execute(f"SELECT * FROM documents WHERE title = '{title}'").fetchone()
    print(f"created document {row} for {owner}")
    return {"document": row}

@app.get("/documents")
def list_documents(sort: str = "created_at"):
    rows = conn.execute(f"SELECT * FROM documents ORDER BY {sort}").fetchall()
    results = []
    for r in rows:
        user = conn.execute(f"SELECT * FROM users WHERE id = '{r[1]}'").fetchone()
        results.append({"doc": r, "user": user})
    return results
```

### Deliverables

| # | Task | Marks |
|---|---|---|
| 1 | **Audit.** List every defect you can find, each with its severity (critical / major / minor) and the lesson it relates to. Aim for at least twelve. | 8 |
| 2 | **Rewrite** the module correctly: Pydantic request and response models, authorization, parameterised SQL, transactions, domain exceptions, structured logging, no secrets. | 10 |
| 3 | **Tests.** Write at least eight covering: successful creation, mass assignment blocked, validation failure, missing auth, another user's document, SQL injection in `sort`, the N+1 fix, and that no document body reaches the logs. | 4 |
| 4 | **Note.** In under 200 words, explain to the original author which single defect you would fix first and why. | 2 |

### Constraints

- No network calls in tests.
- No real credentials anywhere.
- Your rewrite must run and your tests must pass.

---

## Marking and next steps

| Score | Meaning | Action |
|---|---|---|
| 54–60 | Strong | Proceed to Module 3 |
| 42–53 | Pass | Proceed; review the sections named in the remediation table |
| 36–41 | Borderline | Redo the weak lessons and re-sit Sections A–B |
| < 36 | Not yet | Re-work Module 2 from L08 onward |

The remediation table is in the
[answer key](../answer-keys/module-02-answers.md#module-assessment).

**Before moving on**, Project 2 must also be complete with all 41 tests passing —
[`projects/project-02-ticket-api/README.md`](../projects/project-02-ticket-api/README.md) §6.
