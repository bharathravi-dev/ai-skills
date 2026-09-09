# Project 2 — Validated Support-Ticket API

| | |
|---|---|
| **Module** | Module 2 — Python and Software Foundations |
| **Prerequisites** | M2-L01 … M2-L20 (all of them) |
| **Estimated time** | 5–8 hours |
| **Cost** | £0. Everything runs locally; no cloud, no API keys. |
| **Status** | `[EXECUTED]` 2026-09-08 — **41 tests pass**, and the server was smoke-tested with real HTTP requests |

---

## 1. What you are building

A support-ticket API that demonstrates, in one coherent application, every practice from Module 2:

- Validated request and response schemas (M2-L08)
- Authentication and authorization enforced in deterministic code (M2-L15)
- SQLite persistence with parameterised queries and transactions (M2-L16)
- Domain exceptions translated to HTTP at the boundary (M2-L10)
- Structured logging with a correlation ID, and no user content in logs (M2-L18)
- Secrets from the environment, never in code or the image (M2-L19, M2-L20)
- A test suite that runs with no network and no credentials

This is the reference shape for every service you build later in the course. Project 5, Project 7 and
the capstone all extend it.

---

## 2. Why this project exists

Every later module assumes you can build a service that validates its input, enforces permissions
outside the model, logs safely, and is tested. Module 5 adds an LLM to *this* structure. Module 7 adds
retrieval to it. If the foundation is shaky, those modules become guesswork.

The one idea to carry forward: **authorization is decided by code, before any business logic runs,
and never by a model.** It recurs in M7-L15, M8-L16 and M9-L13.

---

## 3. Quick start

```bash
cd projects/project-02-ticket-api

python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                          # REQUIRED: src/ layout (M2-L06)

cp .env.example .env                      # then read it

pytest -q                                 # expect 41 passed
uvicorn ticketapi.main:app --reload
```

Then open <http://localhost:8000/docs> for the generated interactive documentation.

> **`pip install -e .` is not optional.** The `src/` layout means tests import the *installed*
> package, which is how packaging errors get caught before release (M2-L06 §5.5). Skip it and you
> get `ModuleNotFoundError: No module named 'ticketapi'` — which is the layout working as designed.

### Try it

```bash
# health (no auth required)
curl -s localhost:8000/health

# create a ticket
curl -s -X POST localhost:8000/tickets \
  -H "Authorization: Bearer tok-alice" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Refund","text":"Please refund order 123","priority":2}'

# without a token
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/tickets

# admin-only endpoint as a non-admin
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/admin/stats \
  -H "Authorization: Bearer tok-alice"
```

`[EXECUTED]` — the create call returns:

```json
{"ticket_id":"T-ce750813ab","subject":"Refund","text":"Please refund order 123",
 "priority":2,"channel":"email","status":"open",
 "created_at":"2026-09-07T21:43:16.928187Z","updated_at":"2026-09-07T21:43:16.928187Z"}
```

**Look at what is absent:** no `owner_id`, no `internal_notes`. The handler returned a full `Ticket`
containing both; `response_model=TicketOut` filtered them out (M2-L15 §5.3).

---

## 4. Layout

```
project-02-ticket-api/
├── pyproject.toml           # metadata, dependencies, pytest config
├── requirements.txt         # pinned, verified versions
├── .env.example             # documented, BLANK values
├── .dockerignore            # keeps .env, .git, .venv out of the image
├── Dockerfile               # non-root, cache-ordered, no secrets
├── src/ticketapi/
│   ├── __init__.py          # public API
│   ├── config.py            # Settings, loaded once, tokens repr=False
│   ├── models.py            # TicketCreate / Ticket / TicketOut
│   ├── errors.py            # domain exceptions (no HTTPException here)
│   ├── db.py                # SQLite, parameterised, transactions
│   ├── services.py          # business logic + authorization
│   └── main.py              # FastAPI: routes, dependencies, handlers
└── tests/
    ├── conftest.py          # fixtures: client, alice, bob, admin, conn
    ├── test_models.py       # 10 tests - validation rules
    ├── test_services.py     # 10 tests - logic and authorization, no HTTP
    └── test_api.py          # 21 tests - end to end through TestClient
```

**Three separate ticket models is deliberate**, and it is the single most important design decision
here:

| Model | Direction | Why |
|---|---|---|
| `TicketCreate` | **In** | `extra="forbid"` blocks mass assignment. No `owner_id`, no `status` |
| `Ticket` | Internal | The full row, including `owner_id` and `internal_notes` |
| `TicketOut` | **Out** | `response_model` filters to exactly these fields |

One model for all three would mean a client could send `owner_id` and read `internal_notes`.

---

## 5. Authorization model

| Actor | May do |
|---|---|
| No token | `/health` only. Everything else is `401` |
| Invalid token | `401` |
| `agent` | Create tickets; read, list and update **their own** |
| `admin` | Everything, plus `internal_notes` and `/admin/stats` |

Three decisions worth understanding rather than copying:

1. **`owner_id` comes from the verified token, never the request body.** Otherwise any user could
   create tickets as anyone else.
2. **Another user's ticket returns `404`, not `403`.** A `403` confirms the ticket exists, letting an
   attacker enumerate IDs. Both "absent" and "not yours" return an identical response — and the real
   reason is logged server-side with the request ID.
3. **`/admin/stats` returns `403`**, not `404`. The endpoint's existence is not a secret; only the
   permission is.

`test_nonexistent_ticket_is_indistinguishable` asserts point 2 directly.

---

## 6. Acceptance criteria

The project is complete when **all** of these hold. Tick them honestly.

### Functional

- [ ] `pytest -q` reports **41 passed**, with no skips.
- [ ] `uvicorn ticketapi.main:app` starts and `/health` returns `{"status": "ok"}`.
- [ ] `/docs` shows all endpoints with your `Field` constraints visible.
- [ ] Creating a ticket returns `201` and a body **without** `owner_id` or `internal_notes`.
- [ ] Requests without a valid token return `401`.
- [ ] Reading another agent's ticket returns `404` with a body identical to a genuinely missing one.
- [ ] A non-admin PATCHing `internal_notes` receives `403`.
- [ ] `limit=0`, `limit=101` and `offset=-1` each return `422`.
- [ ] `?sort=priority; DROP TABLE tickets` returns `422` and the table survives.

### Quality

- [ ] No SQL is built by string-formatting a **value**; the one interpolated identifier is
      allow-listed and commented.
- [ ] No `HTTPException` appears in `services.py` or `db.py`.
- [ ] Every response carries an `X-Request-ID` header, and a caller-supplied one is echoed.
- [ ] Error bodies include `request_id`.
- [ ] `test_ticket_text_is_not_logged` passes — no ticket text reaches the logs.
- [ ] `Settings.tokens` uses `repr=False`; printing the settings object reveals no tokens.

### Packaging

- [ ] `pip install -e .` succeeds and tests import the installed package.
- [ ] `.env` is git-ignored; `.env.example` has blank values.
- [ ] `docker build -t ticketapi:0.1 .` succeeds.
- [ ] `docker history --no-trunc ticketapi:0.1 | grep -i token` finds nothing.
- [ ] The container runs as `appuser`, not root.

---

## 7. Running in Docker

```bash
docker build -t ticketapi:0.1 .

docker run --rm -p 8000:8000 \
  -e API_TOKENS="tok-alice:u-alice:agent,tok-admin:u-admin:admin" \
  -e DATABASE_PATH=/tmp/tickets.db \
  -e APP_ENV=production \
  ticketapi:0.1

# prove it is not root
docker run --rm ticketapi:0.1 whoami        # -> appuser

# prove no secret is baked in
docker history --no-trunc ticketapi:0.1 | grep -i "tok-" || echo "clean"
```

**Configuration arrives at runtime.** The image is identical in every environment, which is what
makes "we tested this exact image" meaningful (M2-L20 §5.7).

### Teardown

```bash
docker rmi ticketapi:0.1
rm -f tickets.db
```

---

## 8. Extension exercises

Ordered by difficulty. Each maps to a lesson.

1. **(M2-L16)** Add `GET /tickets/search?q=...` doing a `LIKE` search over `subject` and `text`,
   parameterised. Add an index and measure the difference with `EXPLAIN QUERY PLAN`.
2. **(M2-L08)** Add a `tags: list[str]` field with at most 5 tags, each 1–20 characters, lowercased
   by a validator. Store as JSON.
3. **(M2-L14)** Add a `POST /tickets/{id}/notify` that calls an external service, with retries,
   full jitter and a deadline. Use `MockTransport` in tests — no real network.
4. **(M2-L13)** Add `POST /tickets/bulk` accepting up to 50 tickets, inserting them concurrently
   with a bounded semaphore, returning per-item success and failure with indices preserved.
5. **(M2-L15)** Add rate limiting per token with a token bucket, returning `429` with `Retry-After`.
6. **(M2-L18)** Emit logs as JSON with a redacting filter, and assert in a test that a fake key in a
   subject line never reaches the log output.
7. **(M2-L12)** Replace SQLite with PostgreSQL. Note what changes and what does not — this is the
   preparation for pgvector in M6-L08.

---

## 9. Grading rubric

**Total 50 marks.** Pass ≥ 35.

| Area | Marks | Full credit requires |
|---|---|---|
| **Correctness** | 10 | All 41 tests pass; endpoints behave as specified |
| **Validation** | 8 | Three-model design; `extra="forbid"`; constraints on every field; whitespace normalised before length checks |
| **Authorization** | 10 | `owner_id` from the token; ownership enforced in the service layer; `404` for another user's ticket with a justification; admin-only paths return `403` |
| **Error handling** | 6 | Domain exceptions in services, translated at the boundary; no `HTTPException` below the web layer; `request_id` in every error body |
| **Data layer** | 6 | Parameterised values; allow-listed identifiers; transactions; indexes; `PRAGMA foreign_keys` |
| **Observability** | 5 | Correlation ID on every request and response; structured fields; **no ticket text in logs**, asserted by a test |
| **Packaging and secrets** | 5 | `src/` layout; editable install; pinned deps; `.env.example`; non-root Dockerfile with no secrets in any layer |

**Automatic fail** regardless of other marks:
- A real credential committed anywhere.
- Any SQL built by formatting a value into a query string.
- `owner_id` accepted from the request body.
- Ticket text or subject appearing in log output.

---

## 10. Common problems

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'ticketapi'` | Package not installed | `pip install -e .` (M2-L06) |
| `RuntimeError: API_TOKENS is not set` | No `.env`, or not loaded | `cp .env.example .env`; the app reads the environment |
| All tests fail on import | Wrong directory | Run from the project root |
| Cannot reach the API in Docker | Bound to localhost inside the container | `--host 0.0.0.0` (already in the Dockerfile) |
| `sqlite3.OperationalError: database is locked` | Concurrent writes to a file database | Expected for SQLite; use `:memory:` in tests, PostgreSQL for real concurrency |
| Tests pass but the server 500s | Different config in `.env` than in `conftest.py` | Compare the two |

---

## 11. What comes next

Module 3 is mathematics and machine-learning essentials. You will return to this project's shape in
**Project 5**, where the classification is done by a language model instead of by a rule — and every
control you built here (validation, authorization, logging, testing) is what makes that safe.

→ [Module 2 revision guide](../../assessments/module-02-revision.md)
→ [Module 2 assessment](../../assessments/module-02-assessment.md)
