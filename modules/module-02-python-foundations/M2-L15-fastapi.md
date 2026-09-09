# M2-L15 — FastAPI: Routes, Request/Response Schemas, Dependencies

| | |
|---|---|
| **Lesson ID** | M2-L15 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M2-L08](M2-L08-type-hints-pydantic.md), [M2-L12](M2-L12-api-clients-httpx.md) |

---

## 1. Learning objectives

1. **Build** a FastAPI application with typed request and response models.
2. **Use** path, query and body parameters, and **choose** correct status codes.
3. **Handle** errors so clients receive useful, safe messages.
4. **Use** dependency injection for shared resources and for testable authorization.
5. **Test** an API with `TestClient`, without running a server.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **FastAPI** | A Python web framework using type hints for validation and documentation. |
| **ASGI** | Asynchronous Server Gateway Interface — the async successor to WSGI. |
| **Uvicorn** | An ASGI server that runs FastAPI apps. |
| **Route / path operation** | A URL path plus method, bound to a function. |
| **Path parameter** | A value in the URL path: `/tickets/{ticket_id}`. |
| **Query parameter** | A value after `?`: `/tickets?limit=10`. |
| **Request body** | JSON sent with POST/PUT/PATCH. |
| **`response_model`** | The schema FastAPI uses to serialise and filter the response. |
| **Dependency injection** | Declaring what a route needs; FastAPI supplies it. |
| **`Depends`** | The marker declaring a dependency. |
| **`HTTPException`** | Raise to return an HTTP error. |
| **Lifespan** | Startup/shutdown hooks for shared resources. |
| **`TestClient`** | Calls your app in-process, without a network. |
| **OpenAPI** | The machine-readable API description FastAPI generates. |

---

## 3. Plain-language explanation

FastAPI turns type hints into behaviour. You declare what a route accepts and returns; the framework
validates, serialises, documents and reports errors.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TicketIn(BaseModel):
    text: str
    priority: int = 3

class TicketOut(BaseModel):
    ticket_id: str
    text: str
    priority: int

@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketIn) -> TicketOut:
    return TicketOut(ticket_id="T-001", text=payload.text, priority=payload.priority)
```

From those annotations FastAPI derives: JSON parsing, validation with a structured `422` on failure,
response serialisation and filtering, and interactive documentation at `/docs`.

**This is M2-L08 applied at the network boundary** — the place where untrusted input actually
arrives.

### If you know Express

| Express | FastAPI |
|---|---|
| `app.get('/x', handler)` | `@app.get("/x")` |
| `req.params.id` | `def f(id: str)` in the path |
| `req.query.limit` | `def f(limit: int = 10)` |
| `req.body` | `def f(payload: TicketIn)` |
| Manual validation (Joi/Zod) | **Automatic** from the type hint |
| `res.status(404).json(...)` | `raise HTTPException(404, ...)` |
| Swagger via a plugin | **Generated automatically** |
| Middleware | Middleware **and** dependencies |

The two rows in bold are the reason to use it: validation and documentation are derived from the code
rather than maintained alongside it, so they cannot drift.

---

## 4. Analogy

**A route is a form on a counter.** The schema is the form's fields; FastAPI is the clerk who checks
it is filled in correctly before it reaches you. Anything malformed is handed back with the errors
marked.

### Where the analogy breaks

1. **The clerk checks the *shape*, not the truth.** `priority: 3` is valid whether or not it is the
   right priority. Validation is necessary, never sufficient (M2-L08 §6).
2. **A clerk checks identity too. FastAPI does not** unless you build it. Authentication and
   authorization are dependencies you write (§5.5).
3. **A form is filled once. A route serves thousands concurrently**, so anything shared between
   requests is shared *state* with all the concurrency hazards of M2-L13.
4. **The analogy implies a queue.** FastAPI is async: a `def` route runs in a threadpool, an
   `async def` route runs on the event loop, and choosing wrongly is a real performance bug (§5.7).

---

## 5. Detailed technical explanation

### 5.1 Parameters

```python
@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: str,                                   # path (name matches)
    include_history: bool = False,                    # query (has a default)
    limit: int = Query(default=10, ge=1, le=100),     # query with constraints
) -> TicketOut: ...

@app.post("/tickets")
def create(payload: TicketIn) -> TicketOut: ...       # body (a BaseModel)
```

FastAPI decides by rule: **name in the path → path parameter; a Pydantic model → body; anything else
→ query.** No configuration.

### 5.2 Status codes and errors

```python
@app.post("/tickets", status_code=201)               # success code for this route
def create(payload: TicketIn) -> TicketOut: ...

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> TicketOut:
    ticket = repository.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"ticket {ticket_id} not found")
    return ticket
```

**Validation failures return `422` automatically**, with a body naming every invalid field — the
`exc.errors()` structure from M2-L08, rendered as JSON. You write nothing.

**Custom handlers** map your domain exceptions to responses in one place:

```python
@app.exception_handler(TicketNotFound)
def handle_not_found(request: Request, exc: TicketNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

This keeps `HTTPException` out of your business logic — services raise domain errors, the web layer
translates them. That separation is what lets the same service be used from a CLI or a worker.

### 5.3 `response_model` and accidental data leaks

```python
class UserOut(BaseModel):
    id: str
    email: str
    # note: no password_hash, no internal_notes

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str):
    return db.get_user(user_id)          # may contain many more fields
```

**`response_model` filters the response**, so extra fields on the returned object are stripped. This
is a genuine security control: it is how you avoid returning a password hash because someone added a
column.

**Return the model, do not just annotate it.** With a bare `-> dict` return annotation and no
`response_model`, nothing is filtered.

### 5.4 Dependency injection

```python
def get_db() -> Iterator[Connection]:
    conn = connect()
    try:
        yield conn                       # code after yield runs at teardown
    finally:
        conn.close()

@app.get("/tickets")
def list_tickets(db: Connection = Depends(get_db)) -> list[TicketOut]: ...
```

Dependencies can depend on other dependencies, are cached within a request, and — the important part
— **can be overridden in tests**:

```python
app.dependency_overrides[get_db] = lambda: fake_connection
```

No patching, no mocking library. This is M2-L07's composition argument, applied by the framework.

### 5.5 Authentication and authorization as dependencies

```python
def current_user(authorization: str = Header(default="")) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    user = verify_token(authorization[7:])
    if user is None:
        raise HTTPException(401, "invalid token")
    return user

def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "admin required")     # 403, not 401 (M2-L11)
    return user

@app.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: str, user: User = Depends(require_admin)) -> None: ...
```

Note the composition: `require_admin` depends on `current_user`. And note the status codes — `401`
for "who are you", `403` for "not permitted" (M2-L11 §5.4).

**The principle that carries into Modules 7–9:** authorization is enforced here, in deterministic
code, **before** any model or business logic runs. Never by a prompt, never by a model's judgement
(M7-L15, M9-L13).

### 5.6 Shared resources with lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=30.0)     # startup
    yield
    await app.state.http.aclose()                        # shutdown

app = FastAPI(lifespan=lifespan)
```

**Create expensive resources once.** An `httpx.AsyncClient` per request destroys connection pooling
(M2-L12) — a real and common performance bug.

### 5.7 `def` versus `async def` routes

| Route type | Runs on | Use when |
|---|---|---|
| `async def` | The event loop | Your I/O is async (`httpx.AsyncClient`, async DB drivers) |
| `def` | A threadpool | You call **blocking** libraries |

**The trap:** a blocking call inside an `async def` route freezes the event loop for *every* request
(M2-L13 §5.5). Under load that turns a fast API into a queue.

**If you are unsure, use `def`.** FastAPI runs it in a threadpool where blocking is safe. Use
`async def` only when everything inside it is genuinely awaitable.

### 5.8 Testing

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_ticket():
    response = client.post("/tickets", json={"text": "help", "priority": 2})
    assert response.status_code == 201
    assert response.json()["priority"] == 2

def test_validation_error():
    response = client.post("/tickets", json={"text": "help", "priority": 99})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "priority"]
```

`TestClient` calls the app **in-process** — no server, no port, no network, fast enough to run on
every save. Combined with `dependency_overrides`, you can test authorization logic without real
tokens.

### 5.9 Assumptions and limitations

- FastAPI 0.141.1 and Pydantic 2.13.5 `[VERIFIED 2026-09-08]` by installation and execution here.
- Generated docs describe the schema, not behaviour or rate limits.
- Validation protects shape, not semantics or authorization.
- Long-running work does not belong in a request handler — LLM calls of 30+ seconds usually want a
  job queue (M11-L15).

---

## 6. Worked example — a ticket endpoint, hardened

**v1 — works, and is unsafe.**

```python
@app.post("/tickets")
def create(payload: dict):
    ticket = db.insert(payload)
    return ticket
```

No validation (any JSON accepted), no response filtering (internal fields leak), no status code
(returns 200 for a creation), no authorization, and no error handling.

**v2 — validated.**

```python
class TicketIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=5000)
    priority: int = Field(default=3, ge=1, le=5)
    channel: Literal["email", "chat", "phone"] = "email"
```

`extra="forbid"` blocks **mass assignment** — a client posting `{"text": "...", "is_admin": true}`
now gets a `422` instead of silently setting a field you never intended to expose.

**v3 — response filtered and status code set.**

```python
class TicketOut(BaseModel):
    ticket_id: str
    text: str
    priority: int
    created_at: datetime
    # deliberately absent: internal_notes, assigned_agent_cost, raw_email_headers

@app.post("/tickets", response_model=TicketOut, status_code=201)
```

**v4 — authorization and shared resources.**

```python
@app.post("/tickets", response_model=TicketOut, status_code=201)
def create(
    payload: TicketIn,
    user: User = Depends(current_user),
    db: Connection = Depends(get_db),
) -> TicketOut:
    ticket = service.create_ticket(db, payload, owner_id=user.id)
    return TicketOut.model_validate(ticket)
```

**`owner_id` comes from the verified token, never from the request body.** If the client supplied it,
any user could create tickets as anyone else. This is the single most common authorization bug in web
APIs, and `extra="forbid"` plus taking identity from the token is the fix.

**v5 — error handling.**

```python
@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, user: User = Depends(current_user),
               db: Connection = Depends(get_db)) -> TicketOut:
    ticket = service.get_ticket(db, ticket_id)
    if ticket is None or ticket.owner_id != user.id:
        raise HTTPException(404, "ticket not found")      # note: 404, not 403
    return TicketOut.model_validate(ticket)
```

**Returning `404` rather than `403` for a ticket belonging to someone else is deliberate.** A `403`
confirms the ticket exists, which leaks information: an attacker enumerating IDs learns which are
real. Returning `404` for both "does not exist" and "not yours" reveals nothing.

That trade-off — security against debuggability — should be a conscious decision, and you should log
the real reason server-side with the request ID so your own team can still diagnose it.

---

## 7. Practical activity

**File:** [`labs/m2/l15_fastapi.py`](../../labs/m2/l15_fastapi.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m2/l15_fastapi.py
```

A complete API with validation, authorization, error handling and dependency overrides — exercised
entirely through `TestClient`, so **no server and no port are needed**. It prints each request and
response, including the `422` bodies and the authorization outcomes.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `response_model=TicketOut` | Filters the response; strips fields not in the model. |
| `ConfigDict(extra="forbid")` | Blocks mass assignment. |
| `Depends(current_user)` | Authorization in deterministic code, before any logic. |
| `app.dependency_overrides[...]` | Swap a dependency in tests with no patching. |
| `TestClient(app)` | In-process calls, no network. |
| `raise HTTPException(404)` for another user's ticket | Avoids leaking existence. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with fastapi 0.141.1, pydantic 2.13.5, Python 3.12.3:

```
/tmp/claude-1001/-home-bharathr-self-Learning-claude-ai/9c4512c5-c9dc-4273-a0a7-c085ab932aab/scratchpad/venvtest/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
==========================================================================
FASTAPI: VALIDATION, AUTHORIZATION AND TESTING
==========================================================================

--------------------------------------------------------------------------
1. VALIDATION - what the framework rejects for you
--------------------------------------------------------------------------
  valid ticket
    -> 201  {"ticket_id": "T-003", "text": "Printer on fire", "priority": 1, "channel": "email", "created_at": "2026-09-07...
  priority out of range (99)
    -> 422  {"detail": [{"type": "less_than_equal", "loc": ["body", "priority"], "msg": "Input should be less than or equa...
  empty text
    -> 422  {"detail": [{"type": "string_too_short", "loc": ["body", "text"], "msg": "String should have at least 1 charac...
  invalid channel
    -> 422  {"detail": [{"type": "literal_error", "loc": ["body", "channel"], "msg": "Input should be 'email', 'chat' or '...

  MASS ASSIGNMENT ATTEMPT - client tries to own someone else's data:
    posts owner_id and is_admin
    -> 422  {"detail": [{"type": "extra_forbidden", "loc": ["body", "owner_id"], "msg": "Extra inputs are not permitted", ...
    extra='forbid' rejected both fields by name. Without it they
    would have been silently ignored - or worse, honoured.

  The 422 body is structured, not prose:
    loc=['body', 'text']  msg=String should have at least 1 character
    loc=['body', 'priority']  msg=Input should be less than or equal to 5

--------------------------------------------------------------------------
2. AUTHORIZATION - enforced before any handler logic runs
--------------------------------------------------------------------------
  request                                         status
  no Authorization header                            401
  invalid token                                      401
  alice reads her own ticket                         200
  alice reads BOB's ticket                           404
  alice reads a ticket that does not exist           404
  admin reads bob's ticket                           200

  Note rows 4 and 5 BOTH return 404.
  Bob's ticket exists; the non-existent one does not. Returning 403
  for the first would confirm its existence, letting an attacker
  enumerate valid ticket IDs. Identical responses reveal nothing.

  admin-only delete                               status
  alice tries to delete                              403
  admin deletes                                      204
    403 for alice: authenticated, but not permitted (M2-L11).

--------------------------------------------------------------------------
3. response_model - a real data-leak control
--------------------------------------------------------------------------
  Fields stored in the row  : ['channel', 'created_at', 'handling_cost', 'internal_notes', 'owner_id', 'priority', 'text', 'ticket_id']
  Fields returned to client : ['channel', 'created_at', 'priority', 'text', 'ticket_id']

  STRIPPED by response_model: ['handling_cost', 'internal_notes', 'owner_id']

  The handler returned the whole row. FastAPI filtered it down to
  TicketOut. 'internal_notes' contained 'VIP customer, escalate
  fast' and 'handling_cost' was 12.5 - neither reached the client.

  Add a column to the table tomorrow and it is NOT exposed unless
  someone deliberately adds it to TicketOut. That default is the
  security property.

--------------------------------------------------------------------------
4. DEPENDENCY OVERRIDES - testing auth with no real tokens
--------------------------------------------------------------------------
  Run the SAME endpoint as three different users, no tokens needed:
    as u-alice    (admin=False) -> sees ['T-001', 'T-003']
    as u-bob      (admin=False) -> sees ['T-002']
    as u-admin    (admin=True ) -> sees ['T-001', 'T-003', 'T-002']

  No patching, no mocking library, no fake HTTP server. The real
  route code ran - real validation, real response_model filtering -
  with one dependency swapped. This is M2-L07 composition, applied
  by the framework.

--------------------------------------------------------------------------
5. THE GENERATED SCHEMA
--------------------------------------------------------------------------
  Your Field() constraints appear in the OpenAPI document:
    text        {'maxLength': 5000, 'minLength': 1}
    priority    {'maximum': 5.0, 'minimum': 1.0, 'default': 3}
    channel     {'enum': ['email', 'chat', 'phone'], 'default': 'email'}

  Paths documented: ['/health', '/tickets', '/tickets/{ticket_id}']
  This is generated from the code, so it cannot drift from it.

==========================================================================
```

**Note the first line.** With these versions, `starlette.testclient` emits
`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2
instead.` `[VERIFIED 2026-09-08]` It is harmless here, and it is a good example of why every version
in this course is pinned and dated: this warning did not exist a year ago and the recommended fix
will change again.

### 7.3 Reading the result

**Section 1's mass-assignment test is the security headline:**

```
posts {"text": "x", "owner_id": "u-bob", "is_admin": true}
-> 422  {"type": "extra_forbidden", "loc": ["body", "owner_id"], ...}
```

A client attempted to create a ticket owned by a *different user* and to grant itself admin. Both
fields were rejected **by name**. Without `extra="forbid"` the default is `ignore` — the fields would
have been silently dropped, which sounds safe until someone later writes
`Ticket(**payload.model_dump())` and the smuggled fields start being honoured.

The `422` bodies are structured, and multiple errors are reported at once — the `exc.errors()`
structure from M2-L08, delivered to the client as JSON with no code from you.

**Section 2 contains the deliberate design decision:**

```
alice reads BOB's ticket                         404
alice reads a ticket that does not exist         404
```

Bob's ticket **exists**. The other does not. Both return `404`, and that is the point: a `403` on the
first would confirm the ID is real, letting an attacker enumerate valid ticket IDs by watching which
responses differ. Identical responses leak nothing.

Contrast with the delete endpoint, where alice correctly gets **`403`** — there the *resource path*
is not secret, only the *operation* is restricted, so distinguishing "not permitted" from "not found"
costs nothing. Choosing between `403` and `404` is a judgement about what the status code reveals.

**Section 3 shows `response_model` earning its place as a security control:**

| | Fields |
|---|---|
| Stored in the row | `channel, created_at, handling_cost, internal_notes, owner_id, priority, text, ticket_id` |
| Returned to the client | `channel, created_at, priority, text, ticket_id` |
| **Stripped** | **`handling_cost, internal_notes, owner_id`** |

The handler returned the **entire row**. FastAPI filtered it. `internal_notes` held *"VIP customer,
escalate fast"* and `handling_cost` was `12.5` — neither reached the client.

The property that matters is the **default**: add a column to that table tomorrow and it is *not*
exposed unless somebody deliberately adds it to `TicketOut`. A hand-written serialiser that does
`return dict(row)` has the opposite default, and that is how internal notes end up in a public API
response.

**Section 4** ran the same endpoint as three different users with **one line each** and no tokens,
no patching and no mocking library:

```
as u-alice (admin=False) -> sees ['T-001', 'T-003']
as u-bob   (admin=False) -> sees ['T-002']
as u-admin (admin=True ) -> sees ['T-001', 'T-003', 'T-002']
```

The real route code ran — real validation, real filtering, real authorization logic. Only the
dependency was swapped. This is exactly the M2-L07 composition argument, provided by the framework.

**Section 5** confirms the constraints you wrote appear in the generated OpenAPI document
(`minLength`, `maximum`, `enum`). Because it is derived from the code, the documentation cannot drift
from the behaviour — a class of bug that hand-maintained API docs never escape.

**Verification:** confirm the mass-assignment attempt returns `422` naming `owner_id`, that both
alice-reads-bob and alice-reads-missing return `404`, and that `internal_notes` appears in the stored
row but not in the response.

---

## 8. Common mistakes and troubleshooting

1. **No `response_model`.** Internal fields leak.
2. **Trusting an ID from the request body** instead of the token.
3. **Omitting `extra="forbid"`** — mass assignment.
4. **Blocking calls in `async def` routes.**
5. **Creating an HTTP client or DB connection per request.**
6. **Returning `403` where `404` avoids leaking existence.**
7. **Returning raw exception text to clients** — leaks internals (M2-L10 §9).
8. **Business logic in route functions**, making it untestable outside HTTP.
9. **Long LLM calls in a request handler**; use a job queue.

| Error | Cause | Fix |
|---|---|---|
| `422` with `loc: ["body", "x"]` | Request failed validation | Read `detail`; it names the field |
| `422` for a field you did send | `extra="forbid"` and a typo, or wrong nesting | Compare against `/docs` |
| Response missing fields | Not declared in `response_model` | Add them deliberately |
| Slow under load, fast alone | Blocking call in an `async def` route | Use `def`, or make the call async |
| `RuntimeError: Event loop is closed` | Sync client used in async context | Use `AsyncClient` in `async def` |
| Tests hit the real database | Dependency not overridden | `app.dependency_overrides[get_db] = ...` |

---

## 9. Security, privacy, reliability and cost

- **Security.** `response_model` and `extra="forbid"` are real controls against data leakage and mass
  assignment. **Identity always comes from the verified token, never the body.**
- **Security.** Authorization is a dependency running before your handler — deterministic,
  auditable, testable. This is the pattern M7-L15 and M9-L13 build on: **permissions are enforced
  outside the model.**
- **Privacy.** Do not log request bodies wholesale. Log the request ID, route, status and duration.
- **Reliability.** Shared resources belong in `lifespan`. Blocking calls in `async def` routes are a
  latency cliff under load.
- **Cost.** A synchronous LLM call inside a request handler ties up a worker for 30+ seconds. At
  modest concurrency that exhausts your workers and every other request queues.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Build an API with:

1. `GET /health` returning `{"status": "ok"}`.
2. `GET /items/{item_id}` with a path parameter, returning `404` when unknown.
3. `GET /items` with `limit` (1–100, default 10) and `offset` (≥ 0, default 0) query parameters.
4. `POST /items` with a validated body and a `201` status.

Test each with `TestClient`, including one invalid request per endpoint.

### Exercise 2 — Intermediate (~30 min)

Extend it:

1. Add `current_user` reading a bearer token, returning `401` if missing or invalid.
2. Add ownership: users see only their own items. Return `404` for someone else's, and explain in a
   comment why not `403`.
3. Add a `response_model` that excludes an `internal_cost` field. **Prove** it is excluded by
   returning an object that has it.
4. Override `current_user` in tests to run as three different users without real tokens.
5. Write eight tests: success, unauthenticated, wrong user, validation failure, not found, mass
   assignment blocked, response filtering, and pagination bounds.

### Exercise 3 — Challenge (~35 min)

1. Add a dependency that rejects requests whose body exceeds 10 KB, returning `413`.
2. Add a custom exception handler mapping a domain `TicketNotFound` to `404`, with no
   `HTTPException` in your service layer.
3. Add `lifespan` creating one `httpx.AsyncClient`. Prove it is created once by counting.
4. Add both a `def` and an `async def` route that each sleep 0.5 s using `time.sleep`. Fire 10
   concurrent requests at each and compare total time. Explain the difference precisely.
5. Add a middleware logging method, path, status and duration with a per-request ID — and confirm no
   request body is logged.
6. Generate the OpenAPI schema and confirm your constraints appear in it.

---

## 11. Quiz

**Q1.** How does FastAPI decide whether a parameter is path, query or body?

- A. By declaration order.
- B. Name matching the path → path; a Pydantic model → body; otherwise → query.
- C. You must annotate each explicitly.
- D. All parameters are query parameters.

**Q2.** What status code does FastAPI return for a request failing validation?

- A. `400`  B. `422`  C. `500`  D. `404`

**Q3.** What does `response_model` do that a return annotation alone does not?

- A. Nothing.
- B. It filters the outgoing response to exactly the declared fields, stripping anything extra — a
  real control against leaking internal data.
- C. It validates the request.
- D. It sets the status code.

**Q4.** Why must `owner_id` come from the verified token rather than the request body?

- A. It is faster.
- B. Otherwise any client could set it to another user's ID and create or read data as them.
- C. Bodies cannot contain IDs.
- D. It does not matter.

**Q5.** What does `extra="forbid"` prevent?

- A. Missing fields.
- B. Mass assignment — a client sending fields you never intended to accept, such as `is_admin`.
- C. Large payloads.
- D. Duplicate requests.

**Q6.** A route calls a blocking library. Should it be `def` or `async def`?

- A. `async def`, always.
- B. `def` — FastAPI runs it in a threadpool where blocking is safe; a blocking call in an
  `async def` freezes the event loop for every request.
- C. Either; no difference.
- D. Neither; use middleware.

**Q7.** What is the main benefit of `app.dependency_overrides` in tests?

- A. Faster tests only.
- B. You can substitute databases, HTTP clients and the authenticated user with no patching or
  mocking library, so tests exercise the real route code.
- C. It disables validation.
- D. It generates test data.

**Q8.** Why return `404` rather than `403` for a resource belonging to another user?

- A. `403` is deprecated.
- B. `403` confirms the resource exists, letting an attacker enumerate valid IDs; `404` for both
  "absent" and "not yours" reveals nothing.
- C. `404` is faster.
- D. FastAPI cannot return `403`.

**Q9.** Where should an `httpx.AsyncClient` be created in a FastAPI app?

- A. Inside each route function.
- B. Once at startup via `lifespan`, so connection pooling works across requests.
- C. At import time in every module.
- D. In middleware, per request.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why validation at the API boundary is
a security control and not merely a convenience.

---

## 12. Revision notes

- FastAPI derives **validation, serialisation, filtering and documentation** from type hints.
- Parameter rule: **path name → path · Pydantic model → body · otherwise → query.**
- Validation failure → automatic **`422`** with per-field detail. Set success codes explicitly
  (`status_code=201`).
- **`response_model` filters the response** — a leak control. **`extra="forbid"`** blocks mass
  assignment.
- **Identity comes from the verified token, never the request body.**
- **Authorization is a dependency**, running in deterministic code before any handler or model.
- `Depends` composes, caches per request, and is **overridable in tests** — no patching.
- **Shared resources in `lifespan`**, created once. A client per request kills pooling.
- **`def` for blocking code** (threadpool), `async def` only when everything inside is awaitable.
- **`404` not `403`** for another user's resource, to avoid leaking existence — and log the real
  reason server-side.
- `TestClient` runs the app in-process: no server, no port, no network.

---

## 13. Completion checklist

- [ ] I built routes with path, query and body parameters.
- [ ] I used `response_model` and proved a field was filtered out.
- [ ] I used `extra="forbid"` and saw mass assignment rejected.
- [ ] I implemented authorization as a dependency and overrode it in tests.
- [ ] I can explain the `def` vs `async def` choice.
- [ ] I returned `404` for another user's resource and can justify it.
- [ ] I wrote at least eight `TestClient` tests.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- FastAPI documentation. <https://fastapi.tiangolo.com/> `[UNVERIFIED]` link not re-checked;
  version 0.141.1 `[VERIFIED 2026-09-08]` by installation and execution here.
- FastAPI, Dependencies. <https://fastapi.tiangolo.com/tutorial/dependencies/> `[UNVERIFIED]`
- OWASP API Security Top 10 — mass assignment and broken object-level authorization.
  <https://owasp.org/API-Security/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L16 — SQL Fundamentals and Database Access from Python](M2-L16-sql-databases.md)

Your API needs somewhere to keep data. Next: SQL from first principles, parameterised queries, and
the foundations you need before pgvector in Module 6.
