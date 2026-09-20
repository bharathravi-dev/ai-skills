# M9-L11 — OAuth Concepts and MCP's Authorization Requirements

| | |
|---|---|
| **Lesson ID** | M9-L11 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M9-L10](M9-L10-authentication-vs-authorization.md) |

---

## 1. Learning objectives

1. **Name** the three OAuth roles in MCP authorization and which component plays each.
2. **Trace** discovery from an MCP server's `401` response to the authorization server's endpoints, including the
   well-known URL fallbacks in their required order.
3. **Choose** a client registration mechanism in the order the 2026-07-28 spec sets out.
4. **Explain and demonstrate** PKCE with `S256`, resource indicators, and issuer validation — and the specific attack
   each one stops.
5. **Implement** step-up authorization correctly, taking the union of scopes.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **OAuth 2.1** | The consolidated OAuth authorization framework (an IETF draft) MCP builds on; it removes insecure flows and requires PKCE. |
| **Resource server** | The API that accepts access tokens — here, the **MCP server**. |
| **Authorization server (AS)** | The service that authenticates the user, obtains consent and issues tokens. |
| **Client** | The application requesting tokens on a user's behalf — here, the **MCP client** in the host. |
| **Authorization code flow** | The browser-based flow: the user approves at the AS, which redirects back with a short-lived *code* that the client exchanges for tokens. |
| **PKCE** | Proof Key for Code Exchange: the client proves at the token endpoint that it started the flow. |
| **Protected Resource Metadata (PRM)** | A JSON document (RFC 9728) in which an MCP server names its authorization server(s). |
| **Resource indicator** | The `resource` parameter (RFC 8707) naming which server a token is for; it becomes the token's audience. |
| **Issuer (`iss`)** | The identifier of the AS that produced a response (RFC 9207). |
| **Step-up authorization** | Obtaining a token with additional scopes when a server answers `403 insufficient_scope`. |

---

## 3. Plain-language explanation

### 3.1 Why OAuth, and why not API keys

A remote MCP server acts on a user's data: their files, tickets, calendars. The user should be able to grant a
specific client limited access, see what they granted, and revoke it — without handing that client their password,
and without the MCP server's operator issuing a permanent API key per user. **OAuth** is the industry's answer: the
user signs in at an **authorization server** they trust, approves a request for specific **scopes**, and the client
receives a short-lived **access token** that the **MCP server** can verify.

### 3.2 The unusual part: clients and servers that have never met

In a typical web app, the developer registers their client with one authorization server in advance. In MCP, a user
can paste any server URL into any host. The client doesn't know the server's authorization server; the authorization
server has never heard of the client. The MCP spec's answer is a chain of **discovery**: the MCP server's `401` points
to its metadata; that names the authorization server; the authorization server's metadata lists its endpoints and
features. §7.1 walks the chain.

### 3.3 Four protections, four attacks

Each protection in the spec answers a concrete attack, and §7 demonstrates each:

- **PKCE** stops someone who **steals the authorization code** from redeeming it (§7.3).
- **Resource indicators** stop a token for **one server** from working at **another** (§7.4).
- **Issuer validation** stops a malicious authorization server from **tricking the client** into sending it an honest
  server's code (§7.5).
- **Scope union on step-up** stops users being sent back to the consent screen over and over (§7.6) — a usability
  failure that trains people to click "approve" without reading.

### 3.4 What MCP adds to OAuth — and what it doesn't

The MCP authorization spec is mostly a **profile**: it chooses which OAuth pieces are mandatory so any client can talk to
any server. It applies to HTTP transports; stdio servers take credentials from the environment (M9-L10). How the
authorization server authenticates users, what scopes mean, and how the MCP server decides what each scope allows are
**outside** the spec — they are your design (M9-L13).

---

## 4. Analogy

**A hotel booking made through a travel agent.** You (the resource owner) want the agent (client) to book a room at a
hotel (resource server). The hotel says "bookings are verified by the Grand Hotels head office" (Protected Resource
Metadata). The head office (authorization server) asks *you* directly whether this agent may book one room for these
dates (consent and scopes), then gives the agent a voucher naming **this hotel** (audience). To collect the voucher, the
agent must show the half of a torn ticket it kept when it started the request (PKCE), so a courier who intercepts the
confirmation slip can't use it. And the agent checks the confirmation is stamped by the head office it actually
contacted (issuer validation), not a look-alike office that intercepted the process.

### Where the analogy breaks

- **Vouchers are paper; tokens are copyable strings.** Anyone who obtains a token can use it until it expires. That is why
  tokens are short-lived, audience-bound, sent only over HTTPS in headers, and never logged (M9-L12).
- **A travel agent is a known business; an MCP client may be software the authorization server has never seen.** Client
  registration (§5.3) is how an unknown client gets an identity at all — and it can be impersonated on `localhost`.

---

## 5. Detailed technical explanation

### 5.1 Roles and standards

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Authorization]`

| Role | MCP component | Must |
|---|---|---|
| Resource server | **MCP server** | Implement Protected Resource Metadata (RFC 9728); validate tokens incl. audience; reject any token not issued for it |
| Authorization server | Any OAuth 2.1 AS (may be co-hosted) | Implement OAuth 2.1; provide RFC 8414 or OpenID Connect discovery metadata; SHOULD support Client ID Metadata Documents |
| Client | **MCP client** | Use PRM for discovery; support both AS metadata formats; PKCE with `S256`; send `resource`; validate `iss` |

Authorization is **optional** in MCP. When a server on HTTP implements it, it SHOULD follow this profile.

### 5.2 Discovery

**Step 1 — the 401.** A request without a valid token receives:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource/catalog/mcp",
                         scope="catalog:read"
```

Servers MUST provide PRM via this header **or** a well-known URL; clients MUST support both, using the header when present.

**Step 2 — Protected Resource Metadata.** If the header lacks `resource_metadata`, the client tries, in order:

1. `https://<host>/.well-known/oauth-protected-resource<MCP endpoint path>` (path insertion)
2. `https://<host>/.well-known/oauth-protected-resource`

The document MUST contain `authorization_servers` with at least one entry. If several are listed, each is independent:
client credentials and tokens are kept **per authorization server** and never reused across them.

**Step 3 — authorization server metadata.** For an issuer with a path (`https://auth.example.com/tenant1`), clients MUST try:

1. `https://auth.example.com/.well-known/oauth-authorization-server/tenant1`
2. `https://auth.example.com/.well-known/openid-configuration/tenant1`
3. `https://auth.example.com/tenant1/.well-known/openid-configuration`

and for an issuer without a path, the first two without `/tenant1`. The retrieved metadata must then be validated (its
`issuer` must match).

`[REAL, measured]` §7.1 parsed a real `WWW-Authenticate` value and generated exactly these URL lists.

**Every URL in this chain comes from a server you may not trust.** A malicious MCP server can point `resource_metadata`
or `authorization_servers` at `http://169.254.169.254/` or an internal admin page, making the *client* issue the request.
Clients deployed on servers must treat discovery as an SSRF risk (M9-L12).

### 5.3 Client registration

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Client Registration]` A client supporting all options SHOULD use:

| Priority | Mechanism | When | Notes |
|---|---|---|---|
| 1 | **Pre-registration** | Client and AS already have a relationship | Credentials MUST be keyed by the AS's `issuer`; never reused with another AS |
| 2 | **Client ID Metadata Document (CIMD)** | AS metadata has `client_id_metadata_document_supported: true` | `client_id` is an HTTPS URL of a JSON document with `client_id`, `client_name`, `redirect_uris`; the AS fetches and validates it |
| 3 | **Dynamic Client Registration** (RFC 7591) | AS metadata has `registration_endpoint` | **Deprecated in 2026-07-28**; kept for older authorization servers; MUST send an appropriate `application_type` |
| 4 | Ask the user | None of the above | E.g. user pastes a client id they registered |

`[REAL, measured]` §7.2 applied this order to four authorization server configurations.

CIMD solves "clients and servers that have never met" without letting anyone create unlimited registrations, but it
cannot prove which local process is listening on a `localhost` redirect URI — authorization servers must show the
redirect hostname and warn on localhost-only clients.

### 5.4 The authorization code flow with PKCE

```text
client: code_verifier = 43-128 random URL-safe chars
        code_challenge = BASE64URL(SHA256(code_verifier))              method S256
browser → AS /authorize?response_type=code&client_id=…&redirect_uri=…
                       &code_challenge=…&code_challenge_method=S256
                       &resource=https%3A%2F%2Fmcp.example.com%2Fcatalog%2Fmcp
                       &scope=catalog:read&state=…
user signs in and consents
AS → browser → client redirect_uri?code=…&state=…&iss=https://auth.example.com/tenant1
client: check state; check iss == recorded issuer (§5.6)
client → AS /token  grant_type=authorization_code&code=…&code_verifier=…&redirect_uri=…&resource=…
AS: SHA256(code_verifier) == stored challenge?  →  access token (aud = resource) [+ refresh token]
client → MCP server   Authorization: Bearer <access token>     (every request)
```

`[REAL, measured]` §7.3:

| Scenario | Result |
|---|---|
| S256 of RFC 7636's example verifier | `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM` — **matches the RFC** |
| Legitimate client redeems code with verifier | ok |
| Attacker redeems intercepted S256 code, no verifier | `invalid_grant` |
| Attacker who saw a **`plain`** challenge redeems the code | **ok** |
| Attacker who saw an **S256** challenge tries it as the verifier | `invalid_grant (PKCE mismatch)` |
| AS metadata lacks `code_challenge_methods_supported` | client must **refuse to proceed** |

With `plain`, the challenge sent through the browser **is** the verifier, so anyone who can see the authorization request
and intercept the code can redeem it. S256 publishes only a hash. The MCP spec requires `S256` when technically capable,
and requires clients to confirm PKCE support from metadata — an absent `code_challenge_methods_supported` means "no PKCE",
and the client MUST NOT continue.

### 5.5 Resource indicators and audience

Clients MUST send `resource` — the MCP server's **canonical URI** — in both the authorization and token requests, even if
the authorization server ignores it. Canonical URIs are absolute `https` URIs without fragments, e.g.
`https://mcp.example.com/mcp`; clients should give the most specific URI and consistently omit a trailing slash.

`[REAL, measured]` §7.4: a token issued with `resource = …/catalog/mcp`, presented to the billing MCP server on the **same
authorization server and signing key**, was rejected when the audience was checked and **accepted when it wasn't**. The
signature proves the AS issued the token; only the audience proves it was issued *for you*.

### 5.6 Issuer validation and mix-up attacks

A client may use many authorization servers. In a **mix-up attack**, a malicious authorization server the user chose to
log in with bounces the browser to an honest one using this client's registration there. The honest server returns a
valid code to the client's callback; the client, believing the flow belongs to the malicious server, redeems the code —
and its PKCE verifier — at the **malicious** token endpoint.

`[VERIFIED 2026-09-15]` Since 2026-07-28, authorization servers SHOULD include `iss` in authorization responses (RFC 9207),
and clients MUST record the expected issuer before redirecting and compare a present `iss` exactly — no normalization — before
redeeming the code, rejecting responses without `iss` when the AS advertised support.

`[REAL, measured, scripted attack]` §7.5 ran the sequence five times: **5/5** honest codes reached the attacker's token
endpoint without the check, **0/5** with it. The count is fixed by construction; its point is where the check sits —
**before** the code leaves the client. PKCE cannot help, because the client itself sends the verifier.

### 5.7 Scopes and step-up authorization

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Scope Selection Strategy and Step-Up Authorization Flow]`

- **Initial scopes:** use the `scope` from the 401's `WWW-Authenticate`; otherwise use `scopes_supported` from PRM.
  Servers should keep `scopes_supported` to the minimum for basic functionality.
- **At runtime,** insufficient scope gets:

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope", scope="catalog:write",
                         resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource/catalog/mcp"
```

- The client re-authorizes with the **union** of previously requested scopes and the challenged scopes, retries a
  bounded number of times, and treats repeated failure as permanent.
- Servers SHOULD put **all** scopes an operation needs in one challenge, and must account for scope hierarchies.

`[REAL, measured]` §7.6, six operations alternating read and write: replacing scopes needed **4** extra authorizations
and ended without write access; taking the union needed **1**.

**Refresh tokens.** Clients must keep them confidential; authorization servers SHOULD issue short-lived access tokens and
MUST rotate refresh tokens for public clients. MCP servers SHOULD NOT include `offline_access` in their challenges or
`scopes_supported` — refresh is a client concern, not a resource requirement.

### 5.8 Assumptions and limitations

- The lab replaces browsers, redirects and HTTP with function calls, and uses HMAC-signed JSON instead of JWTs signed with
  the authorization server's asymmetric keys.
- OAuth 2.1 is still an IETF draft (MCP cites draft 13); details of the base framework may shift before publication.
- Use a maintained OAuth library in both clients and servers. The MCP Python SDK includes client OAuth support and server
  token verification hooks.

---

## 6. Worked example — the connector that asked for everything, twice a day

**The situation.** A company built a remote MCP server for its document system and an internal assistant as the client.
Users complained that the assistant "keeps asking me to log in", and the security team flagged tokens with `docs:*`
scope appearing in a debug log.

**Investigation.**

1. The server's PRM listed **every** scope in `scopes_supported` — `docs:read docs:write docs:share docs:admin` — and its
   `401` challenge carried no `scope`. Following §5.7's rule, the client requested all four up front. Users saw a consent
   screen asking to administer their documents, and many approved without reading.
2. Some users' organisations denied `docs:admin`, so the authorization server issued a reduced token. When a user then
   shared a document, the server returned `403 insufficient_scope scope="docs:share"`, and the client re-authorized with
   **only** `docs:share` — dropping `docs:read`. The next search returned 403, triggering another login. This is §7.6's
   "replace" behaviour: four prompts where one would do.
3. The client had been built against one authorization server in development and **skipped `iss` validation** and the
   PKCE-support check because "our AS supports both".

| # | Defect | Consequence | Fix |
|---|---|---|---|
| 1 | Full scope catalog in `scopes_supported`, no challenge scope | Over-broad tokens; blind consent | Minimal `scopes_supported`; precise `scope` in each challenge (§5.7) |
| 2 | Step-up replaced scopes | Repeated logins | Request the union (§5.7) |
| 3 | No `iss` check, no PKCE-support check | Vulnerable when pointed at any other AS | Record issuer; compare exactly; refuse if PKCE not advertised (§5.4, §5.6) |
| 4 | Broad token in debug log | A leaked `docs:*` token grants admin access | Minimal scopes limit blast radius; never log tokens (M9-L12) |

**The general rule.** **Least privilege in OAuth is a design property of the *server's* scope challenges and the *client's*
scope accumulation together.** Either side getting it wrong produces over-broad tokens or login loops — and login loops
produce users who approve anything.

---

## 7. Practical activity

**File:** [`labs/m9/l11_oauth_mcp_authorization.py`](../../labs/m9/l11_oauth_mcp_authorization.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l11_oauth_mcp_authorization.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. DISCOVERY: FROM A 401 TO THE AUTHORIZATION SERVER'S ENDPOINTS
============================================================================
  MCP request with no token -> HTTP 401
    resource_metadata = https://mcp.example.com/.well-known/oauth-protected-resource/catalog/mcp
    scope             = catalog:read   (use this first when requesting a token)
  if the header had no resource_metadata, try in order:
    https://mcp.example.com/.well-known/oauth-protected-resource/catalog/mcp
    https://mcp.example.com/.well-known/oauth-protected-resource
  Protected Resource Metadata says authorization_servers = ['https://auth.example.com/tenant1']
  authorization server metadata URLs for issuer 'https://auth.example.com/tenant1', in the required order:
    https://auth.example.com/.well-known/oauth-authorization-server/tenant1
    https://auth.example.com/.well-known/openid-configuration/tenant1
    https://auth.example.com/tenant1/.well-known/openid-configuration
  ...and for an issuer with no path ('https://auth.example.com'):
    https://auth.example.com/.well-known/oauth-authorization-server
    https://auth.example.com/.well-known/openid-configuration

============================================================================
2. CLIENT REGISTRATION: WHICH MECHANISM, IN WHAT ORDER
============================================================================
  enterprise AS, client pre-registered   -> use pre-registered client_id (keyed by this issuer)
  AS advertises CIMD                     -> use a Client ID Metadata Document (HTTPS URL as client_id)
  older AS with DCR only                 -> Dynamic Client Registration (deprecated fallback)
  AS with neither                        -> ask the user to enter client details

============================================================================
3. PKCE: S256, A STOLEN CODE, AND WHY 'plain' IS WEAKER
============================================================================
  RFC 7636 Appendix B verifier : dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
  S256 challenge computed here : E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  matches the RFC's value      : True

  legitimate client redeems its code with the verifier -> ok
  attacker redeems an intercepted S256 code, no verifier -> invalid_grant (no code_verifier)
  attacker who saw a 'plain' challenge redeems the code  -> ok
  attacker who saw an S256 challenge tries it as verifier -> invalid_grant (PKCE mismatch)

  AS metadata without code_challenge_methods_supported -> client proceeds? False (MUST refuse)

============================================================================
4. RESOURCE INDICATORS: TOKENS BOUND TO ONE MCP SERVER
============================================================================
  catalog token presented to catalog MCP server  audience checked: True   not checked: True
  catalog token presented to billing MCP server  audience checked: False  not checked: True

  Same authorization server, same signing key: only the audience claim, set
  from the client's `resource` parameter, stops a catalog token working at billing.

============================================================================
5. MIX-UP ATTACK AND ISSUER VALIDATION (RFC 9207)
============================================================================
  without iss check : honest authorization codes sent to the attacker's token endpoint = 5/5
  with iss check    : honest authorization codes sent to the attacker's token endpoint = 0/5

  PKCE does not help here: the client itself hands the attacker the verifier.

============================================================================
6. STEP-UP AUTHORIZATION: REPLACE SCOPES OR TAKE THE UNION?
============================================================================
  replace: 4 extra authorizations for 6 operations; final scopes ['catalog:read']
  union  : 1 extra authorizations for 6 operations; final scopes ['catalog:read', 'catalog:write']

  Replacing scopes drops read access every time write access is granted, so the
  user is sent back to the consent screen on every switch. The spec says clients
  SHOULD request the union of previously requested and newly challenged scopes.

============================================================================
7. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the S256 transformation (checked against RFC 7636's test vector), HMAC
  token signatures, single-use codes, audience checks, and every count above.

  ILLUSTRATIVE: no browser, redirects, TLS or real endpoints; the 'attacker'
  is a scripted sequence; tokens are HMAC-signed JSON, not JWTs with RS256.

  NOT SHOWN: refresh-token rotation, Client ID Metadata Document fetching and
  its SSRF risks, and token storage and passthrough (M9-L12).

Done.
```

### 7.3 Reading the result

**Section 3's first three lines anchor everything else.** The lab's S256 implementation reproduces the RFC's published
value, so the attack results that follow rest on a correct primitive.

**Section 4 is the one to remember when reviewing a server.** Signature valid, issuer valid, wrong service — accepted,
unless someone wrote the audience check.

**Section 6 is a user-experience bug with a security cost.** Every unnecessary consent screen teaches people to stop
reading consent screens.

---

## 8. Common mistakes and troubleshooting

1. **Skipping discovery and hard-coding one authorization server.** §5.2 — breaks for other servers and hides SSRF risk.
2. **Treating PKCE as optional, or using `plain`.** §5.4.
3. **Omitting `resource`, or servers not checking audience.** §5.5.
4. **Not validating `iss`.** §5.6.
5. **Replacing scopes on step-up.** §5.7.
6. **Publishing every scope in `scopes_supported`**, or emitting one missing scope per retry. §5.7, §6.
7. **Reusing client credentials across authorization servers.** §5.3.
8. **Using Dynamic Client Registration in new implementations** where CIMD is available. §5.3.

| Symptom | Likely cause | Fix |
|---|---|---|
| Users re-prompted for consent repeatedly | Step-up replaces scopes | Union of previous and challenged scopes |
| Token works at a different MCP server | Server skips audience validation | Validate `aud` equals the canonical server URI |
| `invalid_target` from token endpoint | `resource` differs between authorize and token requests | Send the identical canonical URI both times |
| Client refuses a new authorization server | Metadata lacks `code_challenge_methods_supported` | Correct behaviour; the AS must advertise PKCE |
| Registration rejected by an OIDC server | DCR without `application_type: "native"` for localhost redirects | Set `application_type` (or use CIMD) |
| Consent screen lists admin scopes for a read-only task | Full scope catalog requested | Minimal `scopes_supported`, precise challenges |

---

## 9. Security, privacy, reliability, cost

- **Security.** PKCE (`S256`), audience binding, `iss` validation, exact redirect URI matching and `state` checks are
  independent defences against different attacks; none substitutes for another.
- **Privacy.** Scopes are the user's consent in machine form. Over-broad scopes leak more data when tokens leak and make
  consent meaningless.
- **Reliability.** Discovery must handle both metadata formats and path-based issuers (§5.2); step-up must be bounded.
- **Cost.** Every avoidable re-authorization costs user time and support tickets (§6); a hosted authorization server is
  usually cheaper than building one.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. Map resource server, authorization server and client to MCP components.
2. List the well-known URLs a client tries for PRM of `https://api.example.com/tools/mcp` and for AS metadata of issuer
   `https://login.example.com/org7`.
3. What attack does PKCE prevent, and why is `S256` preferred to `plain`?
4. What does the `resource` parameter become in the issued token, and who checks it?
5. Why doesn't PKCE prevent a mix-up attack?

### Exercise 2 — Intermediate (~45 min)

1. Run the lab. Add a trailing slash to the resource sent at the token endpoint in §7.4 and observe the result. How should
   canonical URIs be handled?
2. Extend `choose_registration` so pre-registered credentials are ignored when their recorded issuer differs from the
   current AS, and surface an error instead.
3. Implement `state` checking in §7.3's flow and show a CSRF-style forged callback being rejected.
4. Change §7.6's server to challenge one missing scope at a time for an operation needing two scopes. Count prompts.
5. Write the PRM JSON and the 401/403 headers for a server with `tickets:read` and `tickets:write`.

### Exercise 3 — Challenge (~60 min)

1. Replace the HMAC tokens with RS256 JWTs using the `cryptography` or `PyJWT` package and a JWKS document; verify audience,
   issuer and expiry.
2. Implement the client side of discovery against a local HTTP server (M9-L08) that serves PRM and AS metadata, with the
   §5.2 fallback order.
3. Threat-model a Client ID Metadata Document flow with a localhost redirect URI. What can a malicious local app do, and
   what should the authorization server display?
4. Read the MCP Python SDK's `mcp/client/auth/oauth2.py` and list which of §5.2–§5.7's MUSTs it implements.
5. Design scopes for an MCP server exposing a CRM: which scopes, what `scopes_supported` contains, and which challenge each
   tool emits.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l11).)*

**Q1.** In MCP authorization, which OAuth role does the MCP server play?

- A. Resource server
- B. Authorization server
- C. Client
- D. Resource owner

**Q2.** How does an MCP client first learn which authorization server protects an MCP server?

- A. From the server's `tools/list` result
- B. From the `clientInfo` in `_meta`
- C. From Protected Resource Metadata, found via the 401 or a well-known URL
- D. From a list of providers hard-coded in the specification

**Q3.** For issuer `https://auth.example.com/tenant1`, which URL does the client try first?

- A. `https://auth.example.com/tenant1/.well-known/openid-configuration`
- B. `https://auth.example.com/.well-known/openid-configuration/tenant1`
- C. `https://auth.example.com/.well-known/oauth-authorization-server`
- D. `https://auth.example.com/.well-known/oauth-authorization-server/tenant1`

**Q4.** Which registration mechanism is deprecated in 2026-07-28?

- A. Pre-registration
- B. Dynamic Client Registration
- C. Client ID Metadata Documents
- D. Asking the user for client details

**Q5.** In §7.3, why could an attacker redeem a code issued with the `plain` method?

- A. The code was not single-use
- B. The token endpoint skipped client_id checks
- C. The `resource` parameter was missing
- D. The challenge they saw was the verifier itself

**Q6.** An authorization server's metadata lacks `code_challenge_methods_supported`. What must the client do?

- A. Refuse to proceed
- B. Use `plain` instead of `S256`
- C. Proceed without PKCE
- D. Retry discovery with OpenID Connect

**Q7.** What stopped the catalog token from working at the billing MCP server in §7.4?

- A. A different signing key
- B. A different authorization server issued it
- C. The audience check against the `resource` value
- D. PKCE verification

**Q8.** When must a client compare the `iss` parameter against the recorded issuer?

- A. After receiving the access token
- B. Before redeeming the authorization code
- C. Only when PKCE is not supported
- D. Only for OpenID Connect providers

**Q9.** A server returns `403` with `error="insufficient_scope", scope="catalog:write"` to a client holding
`catalog:read`. What should the client request?

- A. `catalog:write` only
- B. `catalog:read catalog:write`
- C. Every scope in `scopes_supported`
- D. The same token again after a delay

**Q10.** Why should a server's `scopes_supported` be minimal?

- A. Clients cannot parse long scope lists
- B. OAuth 2.1 limits a token to one scope
- C. Clients may request it all when no challenge scope is given
- D. Authorization servers reject scopes they do not know

**Q11.** Which transport should *not* use the MCP OAuth flow, per the spec?

- A. stdio
- B. Streamable HTTP
- C. The deprecated HTTP+SSE transport
- D. Any transport behind a reverse proxy

**Q12.** In §6, what caused users to be asked to log in repeatedly?

- A. Tokens expired every few minutes
- B. The server rotated signing keys
- C. PKCE verification failed intermittently
- D. The client replaced scopes on step-up

**Q13.** *(Written, rubric-graded.)* In under 150 words: describe what happens, step by step, from the moment an MCP client
sends its first request to a protected remote MCP server until it receives a successful response. Name at least three
security checks and what each prevents.

---

## 12. Revision notes

- **Roles:** MCP server = resource server; MCP client = OAuth client; separate or co-hosted authorization server.
- **Discovery:** 401 `WWW-Authenticate resource_metadata` (or well-known PRM: path insertion, then root) →
  `authorization_servers` → AS metadata (RFC 8414 path insertion → OIDC path insertion → OIDC path append).
- **Registration order:** pre-registered → CIMD → DCR (deprecated) → ask user; credentials keyed by issuer.
- **PKCE S256** (lab matched RFC 7636's vector): stolen code without verifier fails; `plain` leaks the verifier; refuse ASs
  without `code_challenge_methods_supported`.
- **`resource` → audience:** same AS and key, different server → only the audience check rejects it.
- **`iss` validation** before redeeming the code stops mix-up (5/5 → 0/5 in the scripted attack).
- **Step-up:** 403 `insufficient_scope`; request the **union** (4 vs 1 extra authorizations measured).

---

## 13. Completion checklist

- [ ] I can trace discovery from a 401 to token and authorization endpoints.
- [ ] I can choose a registration mechanism in the spec's order.
- [ ] I can explain PKCE, resource indicators and `iss` validation, and the attack each stops.
- [ ] I can implement step-up authorization with scope union.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Authorization* — <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Authorization Server Discovery* and *Client Registration* (fetched from the specification repository) `[VERIFIED 2026-09-16]`
- MCP 2026-07-28, *Authorization Security Considerations* `[VERIFIED 2026-09-16]`
- RFC 7636, *Proof Key for Code Exchange* (Appendix B test vector) — <https://www.rfc-editor.org/rfc/rfc7636> `[STABLE]`
- RFC 8414 (*Authorization Server Metadata*), RFC 8707 (*Resource Indicators*), RFC 9207 (*Issuer Identification*), RFC 9728
  (*Protected Resource Metadata*) — <https://www.rfc-editor.org/> `[STABLE]`
- OAuth 2.1, draft-ietf-oauth-v2-1-13 — <https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13> `[VERIFIED 2026-09-15 as the draft MCP cites]`

---

## 15. Next lesson

→ [M9-L12 — Credentials, Token Handling and Trust Boundaries](M9-L12-credentials-token-handling-trust-boundaries.md) follows
the token after issue: where it is stored, why an MCP server must never pass it through, how it leaks into logs, and where
the trust boundaries in an MCP deployment actually lie.
