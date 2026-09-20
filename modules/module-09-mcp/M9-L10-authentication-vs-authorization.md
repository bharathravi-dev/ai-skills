# M9-L10 — Authentication vs Authorization in MCP

| | |
|---|---|
| **Lesson ID** | M9-L10 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L11](../module-02-python-foundations/M2-L11-http-rest.md), [M9-L08](M9-L08-transports-stdio-streamable-http.md) |

---

## 1. Learning objectives

1. **Separate** authentication (verifying a caller's identity and token) from authorization (deciding what that
   caller may do), and name the checks that belong to each.
2. **Measure** how many forbidden requests get through servers that stop at authentication, at tool-level scopes,
   and at object-level checks.
3. **Explain** why self-reported identity (`clientInfo`) and filtered tool lists are not access controls.
4. **Return** 401 and 403 correctly, and predict what a client does after each.
5. **Describe** where credentials come from on each MCP transport: the environment for stdio, OAuth access tokens for
   Streamable HTTP.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Authentication (AuthN)** | Establishing *who* is calling — for an MCP HTTP server, validating that an access token is genuine, current and issued for this server. |
| **Authorization (AuthZ)** | Deciding *whether this caller may do this* — this tool, this resource, this record. |
| **Principal** | The authenticated identity a request acts on behalf of (a user, or a service). |
| **Scope** | A named permission carried by an OAuth access token, e.g. `catalog:read`. |
| **Audience** | The service a token was issued for. A token for another service must be rejected. |
| **Object-level authorization** | Checking access to the *specific* record requested (learner `raj`'s progress), not just the operation type. |
| **401 Unauthorized** | "I don't know who you are": missing, invalid or expired credentials. |
| **403 Forbidden** | "I know who you are, and you may not do this": insufficient permission. |

---

## 3. Plain-language explanation

### 3.1 Two questions, always in this order

Every protected request has to answer two questions. **"Who are you?"** — is this a genuine token, still valid, and
meant for this server? That is **authentication**. **"Are you allowed to do *this*?"** — may this person call this
tool, on this record, right now? That is **authorization**. The names sound alike, the checks often live in the same
middleware, and treating them as one check is one of the most common security defects in APIs.

### 3.2 Measured: where each design leaks

§7.2 ran 8 callers against 4 operations — 32 requests — through five server designs. A server that treated "valid
token" as "allowed" let **5 forbidden requests** through, including a learner changing course prices. Adding
tool-level scopes cut that to **2**, both of them a learner reading *another learner's* progress. Only the design that
also checked **which record** was requested got to **0**. Then a fourth design added an "admin console bypass" keyed
on the client's self-reported name, and a learner who simply claimed to be `admin-console` reopened **2** holes.

### 3.3 Things that look like access control but are not

- **Filtered tool lists.** Showing a learner only the tools they may use is good user experience. It is not a
  control: §7.3's learner called the hidden `set_course_price` anyway, and a server that relied on hiding returned
  **200**.
- **Self-reported identity.** `clientInfo` and capabilities are statements the client makes about itself (M9-L05).
  Anyone can send `{"name": "admin-console"}`.
- **Instructions to the model.** "Only call this tool for the current user" in a description is a request, not a rule
  (M9-L13).

### 3.4 Where credentials come from depends on the transport

For **Streamable HTTP**, the MCP authorization spec makes the server an **OAuth 2.1 resource server**: every request
carries an access token in an `Authorization: Bearer` header, and the server validates it (M9-L11). For **stdio**, the
spec says implementations **should not** use that flow and should take credentials **from the environment** — the
server runs as a subprocess of a host the user already trusts, and it uses whatever API keys or database credentials
the user configured for it. Authorization still matters on stdio: the question becomes what those environment
credentials let the server do (M9-L12).

---

## 4. Analogy

**A hospital visitor badge.** At reception, a guard checks your photo ID against your face and prints a badge with
today's date: **authentication**. The badge says "Visitor — Ward 3". Whether you may enter the pharmacy, or read a
patient's chart in Ward 3, is **authorization** — and the chart question depends on *which patient*, not just which
ward (object-level). A ward door that opens for any valid badge is design A. A door that checks "Ward 3" but lets any
Ward 3 visitor read every chart is design B. A sticker you wrote yourself saying "DOCTOR" is `clientInfo`. And taking
the pharmacy off the visitor map (a filtered list) does not lock its door.

### Where the analogy breaks

- **Hospital badges are checked by people who can use judgement; servers check the same rules every time.** That is
  a strength (consistency) and a weakness (a rule you forgot to write simply does not exist) — which is why §7.2
  compares designs against an explicit policy table.
- **A badge is issued once for the day; MCP HTTP requests each carry a token that can expire mid-conversation.**
  Authentication happens on every request, so status codes that tell the client *what to do next* matter (§5.5).

---

## 5. Detailed technical explanation

### 5.1 What authentication checks

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Authorization §Access Token Usage and §Token Handling]`

For an MCP server on HTTP, authentication means validating the access token on **every request**:

| Check | Fails as | Why |
|---|---|---|
| Present, in `Authorization: Bearer <token>` (never in the query string) | 401 | No identity at all |
| Signature / introspection valid, issued by the expected authorization server | 401 | Forged or unrelated tokens |
| Not expired | 401 | Stolen tokens should age out |
| **Audience is this server** (RFC 8707) | 401 | A token for another service must not work here |

`[REAL, measured]` §7.1 classified 8 callers: no token, a token signed with the wrong key, an expired token, and a
token whose audience was a different server were all rejected; four genuine callers were accepted.

The audience check is the one most often skipped. Without it, any token your authorization server issues for **any**
service — a billing API, an internal dashboard — also works against your MCP server. The spec states it as a MUST:
servers must only accept tokens issued specifically for them, and must not accept or transit any other tokens
(M9-L12 covers the passthrough half).

### 5.2 What authorization checks

Authorization runs **after** authentication and uses the principal and scopes it produced:

1. **Operation-level:** may this principal call `set_course_price` at all? (Scope `catalog:admin`.)
2. **Object-level:** may this principal read progress for **learner `raj`**? (Own record, own team, or all.)
3. **Context-level** (where relevant): amount limits, time windows, data residency, tenant boundaries.

`[REAL, measured]` §7.2, 32 requests, compared against a hand-written policy:

| Design | Forbidden requests allowed | Other wrong status codes |
|---|---|---|
| A — valid token = allowed | **5/32** | 0 |
| B — tool-level scopes | **2/32** | 0 |
| C — scopes + object-level checks | **0/32** | 0 |
| D — C plus trust in `clientInfo.name == "admin-console"` | **2/32** | 0 |
| E — C's decisions, but 403 for every refusal | 0/32 | **16** |

Design B's two leaks are both `get_progress(raj)` called by learner `li` — the classic **broken object-level
authorization** pattern (BOLA, the top entry in the OWASP API Security Top 10). The operation was allowed; the object
was not. MCP makes this easy to miss because tools take arguments chosen by a model: the model can put *any* learner
id in the call, whether or not the user asked for it.

### 5.3 Self-reported identity is not identity

`[REAL, measured]` Design D added a convenience: "requests from our admin console skip checks". Learner `li` sent the
same valid token with `clientInfo: {"name": "admin-console"}` and got **200** on both `get_progress(raj)` and
`set_course_price`.

The 2026-07-28 spec is explicit that `clientInfo` and `serverInfo` are self-reported, not verified, and SHOULD NOT be
used for security decisions. The same applies to anything else the client asserts about itself — capabilities,
user-agent strings, custom headers — unless it is bound into a credential the server verifies.

### 5.4 Filtered lists and per-call enforcement

The spec allows `tools/list` to vary by the authorization presented on the request — returning only the tools the
caller's scopes permit. That is worth doing: a model offered only usable tools makes fewer failed calls. It is **not**
enforcement.

`[REAL, measured]` §7.3: learner `li`'s list showed `search_courses` and `get_progress`; `li` then called
`set_course_price` by name. A server that relied on the list returned **200**; design C returned **403**. Tool names
leak through documentation, logs, error messages and other users. And if a filtered list is cached, it must be
`cacheScope: "private"` (M9-L06).

### 5.5 401 versus 403

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Authorization §Error Handling]`

| Status | Meaning | MCP server includes | A correct client then… |
|---|---|---|---|
| **401** | Authorization required, or token invalid/expired | `WWW-Authenticate: Bearer resource_metadata="…"`, optionally `scope="…"` | Discovers the authorization server and obtains or refreshes a token (M9-L11) |
| **403** | Valid token, insufficient scope or permission | `WWW-Authenticate: Bearer error="insufficient_scope", scope="…"` | Stops, or requests the additional scope (step-up authorization, M9-L11) |
| **400** | Malformed authorization request | — | Fixes the request |

`[REAL, measured]` Design E made the same allow/deny decisions as C but answered **403** for everything, producing
**16 wrong status codes** out of 32 — every anonymous, forged, expired and wrong-audience request. A client told "403"
for an expired token will not refresh it; a client told "401" for a missing permission will send the user round a
login loop that can never succeed.

**Tool execution errors are different.** A caller authorised to use `plan_study_time` who passes a bad argument still
gets a normal `isError` result (M9-L09). HTTP 401/403 are for "who you are" and "what you may do", decided before a tool
runs.

### 5.6 stdio: credentials from the environment

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Authorization §Protocol Requirements]` Authorization is optional in MCP. When
implemented: HTTP transports SHOULD follow the OAuth-based specification; **stdio transports SHOULD NOT**, and should
retrieve credentials from the environment; other transports must follow their own established security practices.

This changes the shape of the problem rather than removing it:

| | Streamable HTTP server | stdio server |
|---|---|---|
| Who authenticates the user | Authorization server → access token → MCP server validates | The host/OS: whoever launched the process |
| Principal the server sees | The token's subject and scopes | Effectively "the local user" |
| What limits damage | Scopes, object checks, audience | The **permissions of the environment credentials** the server holds, plus sandboxing |
| Typical failure | Missing object-level checks (§5.2) | A broad personal API key or admin database URL in the server's environment |

A stdio server given `DATABASE_URL` for an admin account can do anything that account can, whatever the model asks.
Least-privilege credentials for stdio servers are the subject of M9-L12.

### 5.7 Assumptions and limitations

- The lab's tokens are HMAC-signed JSON with a shared key. Real MCP servers validate OAuth access tokens — typically JWTs
  signed with the authorization server's private key and verified with its published public keys, or opaque tokens
  checked by introspection.
- The policy table is deliberately small. Real policies are usually expressed in a policy engine or a central
  authorization service and tested with the same matrix approach.
- Authorization in multi-tenant systems adds tenant isolation (M7-L15, M10-L07).

---

## 6. Worked example — the tutoring assistant that showed every student's grades

**The situation.** A university deployed an MCP server over Streamable HTTP that exposed `get_student_record(student_id)`
to a tutoring assistant. It used the university's single sign-on: requests without a valid token got 401, and the
security review signed off on "SSO-protected". Tokens carried a `role` claim (`student`, `tutor`, `registrar`), and the
tool checked `role in {"student", "tutor", "registrar"}`.

**The incident.** A student asked the assistant, "How did the top students in my cohort do on the midterm?" The model
listed the cohort, then called `get_student_record` for each classmate. Every call returned 200.

**Analysis using this lesson.**

1. **Authentication was correct.** Tokens were genuine, current and — after review — audience-checked (§5.1).
2. **Authorization stopped at the operation.** Every role could call the tool, and nothing checked *whose* record was
   requested. This is design B in §5.2, the BOLA pattern, and the model's freedom to choose arguments is what triggered
   it at scale.
3. **Two other shortcuts were found in review.** The registrar's web portal sent a custom header `X-Client: registrar-portal`
   that bypassed per-record checks (design D, §5.3), and the tool had been "hidden" from the student UI's tool list,
   which the team had counted as a control (§5.4).

| # | Defect | Fix |
|---|---|---|
| 1 | No object-level check | Students: own record only. Tutors: assigned students only. Registrar: all, with audit logging |
| 2 | Header-based bypass | Remove; if the portal needs broad access, give it a service principal with its own scoped token |
| 3 | Hidden tool treated as a control | Keep the filtered list for usability; enforce on every call |
| 4 | Denials returned 401 | Return 403 with `error="insufficient_scope"` or a plain 403 for object-level denials |

**Verification.** The team wrote the §7.2-style matrix as a test: every role × {own record, assigned student, other
student} × {read, update}, with the expected status code in each cell. It failed 11 cells before the fix and 0 after.

**The general rule.** **"Protected by SSO" describes authentication. Before approving a tool, write down who may call it
on *which* objects, and test that table.**

---

## 7. Practical activity

**File:** [`labs/m9/l10_authentication_vs_authorization.py`](../../labs/m9/l10_authentication_vs_authorization.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l10_authentication_vs_authorization.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. AUTHENTICATION: IS THIS A GENUINE, CURRENT TOKEN FOR THIS SERVER?
============================================================================
  anonymous                       -> no token        
  forged                          -> bad signature   
  expired                         -> expired         
  other-audience                  -> wrong audience  
  learner li                      -> ok              sub=li, scope='catalog:read progress:self'
  learner li (spoofs clientInfo)  -> ok              sub=li, scope='catalog:read progress:self'
  instructor ana                  -> ok              sub=ana, scope='catalog:read progress:team'
  admin sam                       -> ok              sub=sam, scope='catalog:read catalog:admin progress:all'

  Authentication ends here. It says nothing yet about WHICH operations
  learner li may perform -- that is authorization.

============================================================================
2. THE SAME REQUEST MATRIX AGAINST FOUR SERVER DESIGNS
============================================================================
  caller / operation                                   policy    A    B    C    D    E
  anonymous                       search_courses          401  401  401  401  401  403~
  anonymous                       get_progress(li)        401  401  401  401  401  403~
  anonymous                       get_progress(raj)       401  401  401  401  401  403~
  anonymous                       set_course_price        401  401  401  401  401  403~
  forged                          search_courses          401  401  401  401  401  403~
  forged                          get_progress(li)        401  401  401  401  401  403~
  forged                          get_progress(raj)       401  401  401  401  401  403~
  forged                          set_course_price        401  401  401  401  401  403~
  expired                         search_courses          401  401  401  401  401  403~
  expired                         get_progress(li)        401  401  401  401  401  403~
  expired                         get_progress(raj)       401  401  401  401  401  403~
  expired                         set_course_price        401  401  401  401  401  403~
  other-audience                  search_courses          401  401  401  401  401  403~
  other-audience                  get_progress(li)        401  401  401  401  401  403~
  other-audience                  get_progress(raj)       401  401  401  401  401  403~
  other-audience                  set_course_price        401  401  401  401  401  403~
  learner li                      search_courses          200  200  200  200  200  200 
  learner li                      get_progress(li)        200  200  200  200  200  200 
  learner li                      get_progress(raj)       403  200! 200! 403  403  403 
  learner li                      set_course_price        403  200! 403  403  403  403 
  learner li (spoofs clientInfo)  search_courses          200  200  200  200  200  200 
  learner li (spoofs clientInfo)  get_progress(li)        200  200  200  200  200  200 
  learner li (spoofs clientInfo)  get_progress(raj)       403  200! 200! 403  200! 403 
  learner li (spoofs clientInfo)  set_course_price        403  200! 403  403  200! 403 
  instructor ana                  search_courses          200  200  200  200  200  200 
  instructor ana                  get_progress(li)        200  200  200  200  200  200 
  instructor ana                  get_progress(raj)       200  200  200  200  200  200 
  instructor ana                  set_course_price        403  200! 403  403  403  403 
  admin sam                       search_courses          200  200  200  200  200  200 
  admin sam                       get_progress(li)        200  200  200  200  200  200 
  admin sam                       get_progress(raj)       200  200  200  200  200  200 
  admin sam                       set_course_price        200  200  200  200  200  200 

  ! = allowed something the policy forbids   ~ = wrong status code
  design A auth only               :  5/32 forbidden requests allowed,  0 other wrong codes
  design B tool scopes             :  2/32 forbidden requests allowed,  0 other wrong codes
  design C scopes+objects          :  0/32 forbidden requests allowed,  0 other wrong codes
  design D C+clientInfo trust      :  2/32 forbidden requests allowed,  0 other wrong codes
  design E C, 403 for all refusals :  0/32 forbidden requests allowed, 16 other wrong codes

============================================================================
3. HIDING A TOOL FROM tools/list IS NOT ENFORCING IT
============================================================================
  tools/list for learner li shows: ['search_courses', 'get_progress']
  li calls set_course_price anyway (a name seen in docs, logs or another
  user's screenshot): list-filtering server -> HTTP 200, design C -> HTTP 403

  A filtered tools/list is a usability feature. Every tools/call must be
  authorized on its own, because clients can send any name they like.

============================================================================
4. 401 VS 403: WHAT THE CLIENT DOES NEXT DEPENDS ON THE CODE
============================================================================
  anonymous        search_courses     -> 401: authenticate (again): get or refresh a token
  expired          search_courses     -> 401: authenticate (again): get or refresh a token
  other-audience   search_courses     -> 401: authenticate (again): get or refresh a token
  learner li       set_course_price   -> 403: stop, or request more scope (step-up), do NOT re-login blindly

  A server that answers 401 for 'insufficient permission' sends clients into
  a login loop; one that answers 403 for an expired token stops them from
  refreshing. The status code is part of the contract.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every status code in section 2 is computed by running each design
  against every caller and operation; the violation counts are those runs.

  ILLUSTRATIVE: tokens are HMAC-signed JSON with a hard-coded key, not OAuth
  access tokens; the policy table is a small hand-written example.

  NOT SHOWN: obtaining tokens (M9-L11), token storage and passthrough
  (M9-L12), and enforcement patterns such as handle binding (M9-L13).

Done.
```

### 7.3 Reading the result

**Section 2's table is the method, not just the result.** Writing the intended status for every caller × operation
before implementing anything turns authorization from an opinion into a test.

**Rows marked `!` for designs B and D are all about *objects* and *claims*,** not about tokens. Authentication was
identical across all five designs.

**Design E never allowed anything forbidden and was still wrong 16 times** — correctness of the *code* is part of the
contract with clients.

---

## 8. Common mistakes and troubleshooting

1. **Treating a valid token as permission.** §5.2 design A.
2. **Checking the operation but not the object.** §5.2 design B, §6 — especially dangerous when a model chooses ids.
3. **Skipping the audience check.** §5.1 — tokens for other services start working on yours.
4. **Trusting `clientInfo`, user-agent or custom headers for access decisions.** §5.3.
5. **Relying on a filtered `tools/list`.** §5.4.
6. **Returning 403 for expired tokens or 401 for missing permissions.** §5.5.
7. **Giving stdio servers broad personal or admin credentials "because it's local".** §5.6.

| Symptom | Likely cause | Fix |
|---|---|---|
| Users can read other users' data through a tool | No object-level authorization | Check the requested object against the principal on every call |
| Client loops through login repeatedly | 401 returned for insufficient permission | Return 403, with `insufficient_scope` when more scope would help |
| Client never refreshes an expired token | 403 returned for expired tokens | Return 401 with `WWW-Authenticate` |
| Tokens from another internal service work | No audience validation | Reject tokens whose audience is not this server |
| A "hidden" tool is being called | List filtering without call enforcement | Authorize every `tools/call` |

---

## 9. Security, privacy, reliability, cost

- **Security.** Authentication and authorization must both run on every request. Object-level checks matter most for
  tools, because a model picks the identifiers. Never grant access based on client self-description.
- **Privacy.** BOLA defects are privacy incidents by definition (§6). Log denials with principal, tool and object id so
  that probing is visible.
- **Reliability.** Correct 401/403 semantics let clients recover automatically instead of failing or looping (§5.5).
- **Cost.** A policy-matrix test is cheap to write and catches whole classes of defects; retrofitting object checks after
  an incident is expensive and public.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Classify each as authentication or authorization: token signature; `catalog:admin` scope; audience claim; learner id
   matches the token's subject; token expiry.
2. What status code and header should an MCP server return for an expired token? For a valid token without
   `catalog:admin`?
3. Why were design B's two leaks both `get_progress(raj)`?
4. Why is `clientInfo` unsuitable for access decisions?
5. Where should a stdio MCP server get its credentials, per the spec?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a caller `instructor ana (expired)` and predict every design's row before running.
2. Add an operation `set_progress(li)` that only the learner themself and admins may perform, and extend `policy()` and
   `design_c()`.
3. Implement design F: per-object checks, but `progress:team` treats the team list as "everyone except admins". Measure it.
4. Change `authenticate` to skip the audience check and re-run section 2. Which rows change?
5. Write the `WWW-Authenticate` header values each §7.4 example should carry.

### Exercise 3 — Challenge (~50 min)

1. Convert §7.2's matrix into a `pytest` parametrised test that any server implementation can be run against.
2. Design object-level authorization for a tool `search_learners(query)` that returns many records. Where do you filter,
   and how do you prevent leaking counts of records the caller cannot see?
3. A stdio MCP server needs read-only access to one table in a shared database. Specify the credential, its permissions,
   where it is stored, and how the host passes it to the server.
4. Compare authorization implemented inside each tool handler with a central policy layer that runs before dispatch. What
   does each make easy to forget?
5. Read OWASP API Security Top 10 entries for BOLA and broken function-level authorization and map each to a design in §7.2.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l10).)*

**Q1.** Which check is part of authentication for an MCP HTTP server?

- A. The caller has the `catalog:admin` scope
- B. The requested learner id matches the caller
- C. The tool appears in the caller's `tools/list`
- D. The token's audience is this server

**Q2.** In §7.2, how many forbidden requests did the authentication-only design allow?

- A. 0
- B. 5
- C. 2
- D. 16

**Q3.** What kind of defect produced design B's remaining leaks?

- A. Missing object-level authorization
- B. Missing signature validation
- C. Missing audience validation
- D. Wrong status codes

**Q4.** Why did design D allow learner `li` to set course prices?

- A. `li`'s token contained `catalog:admin`
- B. The token was expired
- C. It trusted self-reported `clientInfo`
- D. The tool was missing from `tools/list`

**Q5.** A server hides `set_course_price` from a learner's `tools/list`. What does that achieve?

- A. It enforces the permission for all transports
- B. It removes the need for scope checks
- C. It improves usability but enforces nothing
- D. It prevents the model from ever calling the tool

**Q6.** A request arrives with an expired token. What should the server return?

- A. 401 with `WWW-Authenticate`
- B. 403 with `insufficient_scope`
- C. 400 Bad Request
- D. 200 with `isError: true`

**Q7.** A valid token lacks the scope for an operation. What should the server return?

- A. 401 with a `resource_metadata` challenge
- B. 403, optionally with `error="insufficient_scope"`
- C. 404 Not Found
- D. A JSON-RPC `-32601` method-not-found error

**Q8.** What did design E demonstrate?

- A. Returning 403 everywhere is safer
- B. Status codes do not affect clients
- C. Object checks are unnecessary with 403
- D. Correct decisions can still carry wrong codes

**Q9.** Per the spec, how should a stdio MCP server obtain credentials?

- A. From its environment
- B. Through the OAuth authorization code flow
- C. From `clientInfo` in each request
- D. From the host's `tools/list` cache

**Q10.** Why is object-level authorization especially important for MCP tools?

- A. MCP forbids scope-based authorization
- B. Tools cannot read token claims
- C. Resources never carry identifiers
- D. A model chooses the identifiers in calls

**Q11.** In §6, what did "SSO-protected" actually guarantee?

- A. That students could only see their own records
- B. That callers were authenticated
- C. That tokens could not be stolen
- D. That tutors were limited to assigned students

**Q12.** Which statement about `tools/list` and authorization is correct under 2026-07-28?

- A. The list must be identical for all callers
- B. The list must be public and cacheable
- C. The list may vary by the caller's authorization
- D. The list replaces per-call authorization

**Q13.** *(Written, rubric-graded.)* In under 150 words: a teammate says "our MCP server validates tokens, so it's
secure." Explain what is missing, using an example tool of your choice, and describe how you would test it.

---

## 12. Revision notes

- **AuthN:** token present (Bearer header), genuine, unexpired, **audience = this server** → otherwise 401.
- **AuthZ:** operation-level (scopes) **and** object-level (which record) **and** context → otherwise 403.
- **Measured (32 requests):** auth-only **5** leaks; tool scopes **2** (both BOLA); scopes + objects **0**; plus
  `clientInfo` trust **2**; correct decisions with 403-for-all → **16 wrong codes**.
- **Not controls:** `clientInfo`, filtered tool lists, instructions to the model.
- **401 vs 403** tells the client whether to (re)authenticate or stop/step up.
- **stdio:** credentials from the environment; limit what those credentials can do.

---

## 13. Completion checklist

- [ ] I can list the authentication checks and the authorization checks separately.
- [ ] I can explain each design's leaks in §7.2.
- [ ] I never use self-reported client data or list filtering as access control.
- [ ] I return 401 and 403 correctly with the right headers.
- [ ] I can explain how authorization differs for stdio and HTTP servers.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Authorization* (roles, token usage, audience validation, error handling) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Base Protocol* (`clientInfo` not for security decisions; stdio credentials from environment) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic> `[VERIFIED 2026-09-15]`
- RFC 6750, *OAuth 2.0 Bearer Token Usage* (401/403 and `WWW-Authenticate` errors) — <https://www.rfc-editor.org/rfc/rfc6750> `[STABLE]`
- RFC 8707, *Resource Indicators for OAuth 2.0* — <https://www.rfc-editor.org/rfc/rfc8707> `[STABLE]`
- OWASP API Security Top 10 (2023): API1 Broken Object Level Authorization, API5 Broken Function Level Authorization —
  <https://owasp.org/API-Security/> `[STABLE]`

---

## 15. Next lesson

→ [M9-L11 — OAuth Concepts and MCP's Authorization Requirements](M9-L11-oauth-mcp-authorization.md) explains where the
access tokens in this lesson come from: discovery, client registration, PKCE, resource indicators and step-up scopes.
