# M9-L12 — Credentials, Token Handling and Trust Boundaries

| | |
|---|---|
| **Lesson ID** | M9-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M9-L11](M9-L11-oauth-mcp-authorization.md), [M2-L19](../module-02-python-foundations/M2-L19-secrets.md) |

---

## 1. Learning objectives

1. **Draw** the trust boundaries in an MCP deployment and list which inputs each component must treat as untrusted.
2. **Explain and demonstrate** why token passthrough is forbidden, and design the alternative: audience validation plus
   a separate downstream credential.
3. **Limit** what a local stdio server can reach by controlling the environment it inherits.
4. **Keep** credentials out of logs, and explain why field allowlists beat pattern-based redaction.
5. **Validate** server-supplied URLs against SSRF, and store tokens with correct permissions.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Trust boundary** | A line across which data or control passes between parties with different privileges or intentions; everything crossing it must be validated. |
| **Token passthrough** | An MCP server accepting a client's token without validating it was issued for the server, and forwarding it to another API. Forbidden by the MCP spec. |
| **Confused deputy** | A privileged component tricked into using its authority on behalf of someone who should not have it. |
| **Token exchange** | Swapping one token for another with a different audience or reduced scope (e.g. RFC 8693), so each hop gets its own credential. |
| **SSRF** | Server-Side Request Forgery: making a component send requests to destinations its operator never intended, typically internal ones. |
| **Blast radius** | Everything an attacker can do with one compromised credential. |
| **Allowlist logging** | Emitting only fields known to be safe, instead of emitting everything and trying to remove secrets afterwards. |

---

## 3. Plain-language explanation

### 3.1 A token is a key, and keys get copied

M9-L11 ended with a client holding an access token. From then on, that string *is* the user's authority for whatever
it grants, for as long as it lasts. Anyone who copies it — from a log file, a crash report, a world-readable cache
file, or a server that forwards it somewhere it shouldn't — gets the same authority. This lesson is about the places
tokens and other credentials travel after they exist, and the boundaries they cross.

### 3.2 The MCP server must not be a pipe for tokens

A tempting design for an MCP server that wraps an existing API is to take the user's token and forward it: "the API
already checks tokens, so I don't need to". §7.1 shows why the spec forbids this. A token **stolen from a calendar
service** was presented to a passthrough MCP server wrapping a files API; it read the user's files, and the files API's
audit log recorded the user — with no trace that the MCP server was involved. A server that checked the token was
issued for *itself*, and used its *own* credential downstream, rejected the stolen token and left an honest audit trail.

### 3.3 Local servers inherit more than you think

A stdio server is a child process, and by default a child process inherits its parent's entire environment. §7.2 put
five fake credentials in a host's environment. A server launched the ordinary way could read **all five**; one launched
with an allowlist — as the official Python SDK does by default — could read only the **one** it was meant to have.

### 3.4 Logs, URLs and files

Three more measured leaks. A log redactor that only masks `Authorization: Bearer` headers left **200 of 240**
secret-bearing log lines leaking; a better pattern-based redactor got to 0 — and then leaked **40 of 40** lines in two
formats it had not been written for (§7.3). A naive URL check let **8** internal addresses through, including the cloud
metadata service written as a single integer (§7.4). And a token cache file created the normal way was readable by
every user on the machine (§7.5).

---

## 4. Analogy

**A building's master key and a locksmith.** A tenant gives a locksmith (the MCP server) a key to their flat so the
locksmith can fix the door. A careless locksmith who hands that same key to a subcontractor has made the tenant's key
usable by someone the tenant never met, and the building's log says only "tenant's key used". A careful locksmith checks
the key is actually for this flat, then uses the **building's own contractor key** — logged as "locksmith, on behalf of
flat 4B" — for the parts of the building they need. Meanwhile, a locksmith who pins every key they've handled to a board
in the shared lobby (logs, world-readable files) has undone all of that care.

### Where the analogy breaks

- **Physical keys can't be copied by reading them; tokens can.** Seeing a token in a log line is the same as holding it,
  which is why logs matter far more than a lobby board would.
- **A locksmith knows which building they are in; software can be told to "go fetch" any address.** An MCP client that
  follows URLs from a server's metadata may be steered into the building's plant room (SSRF, §5.5) — a risk with no
  equivalent in the analogy.

---

## 5. Detailed technical explanation

### 5.1 Trust boundaries in an MCP deployment

```text
 user ─── host application ─── model (provider API)
              │
         MCP client ══════ boundary ══════ MCP server ══════ boundary ══════ upstream API
              │                                 │
       authorization server             local OS / environment (stdio)
```

| Component | Must treat as untrusted | Lessons |
|---|---|---|
| **MCP server** | Tool arguments (chosen by a model), `_meta` and `clientInfo` (client-asserted), `requestState` (echoed through the client), tokens until validated | M9-L05, L07, L10, L13 |
| **MCP client / host** | Tool descriptions and annotations, tool results, resource contents, schemas and `$ref`s, **every URL** in discovery metadata, icons | M9-L07, L11, L15 |
| **Upstream API** | Anything the MCP server forwards that it did not mint itself | §5.2 |
| **Local stdio server** | Nothing is "inside" by default: it runs with the permissions and environment it is given | §5.3 |

A useful habit: for each value in a request or response, ask **who could have set it**. If the answer includes a model,
another user, or a remote server you don't control, validate it at the boundary where it enters.

### 5.2 Token passthrough and the confused deputy

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Authorization §Token Handling; Security Best Practices §Token Passthrough]`

- MCP servers **MUST** validate that access tokens were issued specifically for them (audience).
- MCP servers **MUST NOT** accept or transit any other tokens.
- If an MCP server calls an upstream API, it acts as an OAuth client there, and **the token it uses upstream is a
  separate token issued by the upstream authorization server**.

`[REAL, measured]` §7.1, three tokens against two server designs:

| Token | Passthrough server | Audience check + downstream token |
|---|---|---|
| `li`'s token for the files MCP server | files returned; audit log says caller `li` | files returned; audit log says caller `mcp-files` on behalf of `li` |
| `li`'s token **for the calendar API**, stolen | **li's files returned** | rejected at the MCP server |
| Attacker's own token for the files MCP server | attacker's own files | attacker's own files |

The spec lists why passthrough is dangerous: it **bypasses controls** the MCP server or upstream enforce by audience
(rate limits, validation); it **destroys accountability**, because upstream logs cannot distinguish direct calls from
calls through the MCP server; it **breaks trust boundaries**, since a token accepted by many services lets one
compromised service reach all of them; and it blocks adding security controls later.

**The confused deputy variant** is specific to MCP *proxy* servers that use a single static OAuth client id with a
third-party API. If the third-party authorization server remembers consent in a cookie, an attacker can dynamically
register a malicious client at the proxy and send the user a link; consent is skipped and the authorization code goes to
the attacker. The spec requires such proxies to keep **per-client consent**, shown on the proxy's own consent page
(client name, scopes, redirect URI), with exact redirect-URI matching, single-use `state` set only after consent, and
anti-clickjacking protection.

### 5.3 stdio servers and their environment

`[REAL, measured]` §7.2 launched a probe process from a parent environment containing five fake credentials
(`AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`, `CATALOG_READONLY_TOKEN`):

| Launch | Credentials readable by the server |
|---|---|
| `subprocess` with the inherited environment | **5** |
| Allowlist (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`) + one named credential | **1** |

`[VERIFIED 2026-09-16 — mcp 2.2.0 source, mcp/client/stdio.py]` The official Python SDK's `get_default_environment()`
passes exactly that POSIX allowlist (a Windows equivalent on Windows), and `StdioServerParameters.env` merges only the
variables you name. Hosts built on other stacks may inherit everything — check.

Since stdio servers take credentials from the environment (M9-L10), **the environment is the authorization boundary**:

- Give each server a credential scoped to what it needs (a read-only database role, a fine-grained token for one
  repository) — not your personal admin key.
- Pass it explicitly; don't rely on it happening to be in your shell.
- Remember the server runs **with your OS user's privileges** regardless of environment; sandboxing (containers,
  restricted file-system access) limits the rest (MCP Security Best Practices, *Local MCP Server Compromise*).

### 5.4 Credentials in logs

`[REAL, measured]` §7.3, 300 generated log lines (240 containing a secret in one of six formats, 60 benign):

| Approach | Secret-bearing lines still leaking | Benign lines altered |
|---|---|---|
| No redaction | 240/240 | 0 |
| Mask `Bearer …` only | **200/240** | 0 |
| Pattern-based (JWT shape + key names) | 0/240 | 0 |
| Same pattern-based redactor, **40 held-out lines** in two unseen formats | **40/40** | — |
| Structured logging with a field allowlist | nothing to leak | — |

The pattern-based redactor looks perfect only because its patterns were written while looking at the test formats — the
same **overfitting** M1-L08 warned about, applied to security tooling. An opaque API key in an `X-Api-Key` header and a
password in a connection URL went straight through.

Practical rules:

1. **Log events, not requests.** Emit an allowlisted set of fields (method, tool name, request id, principal, status,
   duration). Never log headers, raw bodies, tool arguments or tool results by default.
2. Treat **stderr of stdio servers** as logs — hosts store it (M9-L08).
3. Keep redaction as a *second* line of defence, and test it with formats it wasn't written for.
4. Never put tokens in URLs: OAuth 2.1 and the MCP spec forbid access tokens in query strings, and URLs end up in browser
   history, proxy logs and `Referer` headers.
5. Don't mark sensitive tool parameters with `x-mcp-header`: headers are logged by intermediaries (M9-L08).

### 5.5 SSRF from server-supplied URLs

During discovery (M9-L11), a client fetches `resource_metadata`, `authorization_servers`, and the endpoints in
authorization server metadata — **all chosen by the server**. Schemas' `$ref`s (M9-L07) and icon URLs are similar. A
malicious server can point them at internal addresses, making a client **deployed on a server** fetch cloud metadata
credentials or poke internal services.

`[REAL, measured]` §7.4 classified 11 URLs:

| URL | Naive check | Careful check |
|---|---|---|
| `http://[::ffff:169.254.169.254]/…` (IPv4-mapped IPv6) | allowed | blocked |
| `http://0xA9FEA9FE/…`, `http://2852039166/…`, `http://0251.0376.0251.0376/…` (hex, integer, octal) | allowed | blocked — all are 169.254.169.254 |
| `http://127.1:6379/` | allowed | blocked (127.0.0.1) |
| `https://auth.example.com@169.254.169.254/` (userinfo trick) | allowed | blocked |
| `https://10.20.30.40/…` | allowed ("it's https") | blocked |
| hostnames | allowed | "needs DNS: resolve once, re-check, pin" |

The naive check let **8 internal destinations** through. The careful one used the standard library's own parsers
(`urllib.parse`, `ipaddress`, `socket.inet_aton`), which is the point: the spec itself warns **not to hand-roll IP
validation**, because attackers exploit exactly these encodings. `[VERIFIED 2026-09-15 — MCP Security Best Practices,
SSRF]` Mitigations: require HTTPS (loopback exceptions only in development); block private, loopback, link-local and
private IPv6 ranges; apply the same checks to every redirect hop; beware DNS rebinding between check and use (pin the
resolved address); and, for server-side deployments, route discovery through an **egress proxy** that enforces this by
design.

### 5.6 Storing tokens

`[REAL, measured]` §7.5 with a `022` umask: `open(path, "w")` created a token cache with mode **0644 — readable by
every local user**; `os.open(path, O_CREAT | O_EXCL, 0o600)` created **0600**.

- Prefer the OS credential store (macOS Keychain, Windows Credential Manager, Linux Secret Service via `keyring`).
- If a file is unavoidable, create it with restrictive permissions **at creation**, not with a `chmod` afterwards
  (there is a window in between).
- Key stored client credentials and tokens by **authorization server issuer** (M9-L11) and by resource.
- Authorization servers SHOULD issue short-lived access tokens and MUST rotate refresh tokens for public clients; servers
  MUST store any tokens they hold securely — including in caches and logs.

### 5.7 Assumptions and limitations

- §7.1 uses plain dictionaries to show the flow; real tokens are signed and validated as in M9-L10/L11.
- No DNS resolution happens in §7.4; real validation must resolve, check, and pin, or use an egress proxy.
- §7.5 fixes the umask for repeatability; your system's default may differ.

---

## 6. Worked example — the internal wiki server that leaked through three doors

**The situation.** An engineering team built a Streamable HTTP MCP server wrapping the company wiki's REST API and ran it
on the internal Kubernetes cluster. To "keep it simple", the server forwarded each user's corporate SSO token to the wiki
API, which already accepted SSO tokens. Debug logging was enabled during rollout. A companion stdio version for laptops
read `WIKI_TOKEN` from the environment.

**The incident.** A security review of a separate, compromised internal dashboard found it had been harvesting SSO tokens
from its users. Tokens issued for the dashboard were replayed against the wiki MCP server — and worked. Investigators then
could not tell which wiki reads were legitimate, because the wiki's access log recorded only the user.

**Following the lesson through the deployment.**

1. **Passthrough (§5.2).** The MCP server skipped audience validation and forwarded tokens. The dashboard-issued tokens
   were valid SSO tokens, so the wiki accepted them — §7.1's middle row.
2. **Logs (§5.4).** Debug logs contained full request headers for two weeks, so every user's token was also in the log
   platform, readable by anyone with log access.
3. **Local variant (§5.3).** Engineers' laptop configs launched the stdio server from a shell where `AWS_*` credentials and
   a personal GitHub token were set. The wiki server didn't use them — but a later dependency compromise would have.
4. **Discovery (§5.5).** A pen-tester found that the host application followed `authorization_servers` URLs from any
   configured server with no address checks, from a pod with access to the cloud metadata endpoint.

| # | Defect | Fix |
|---|---|---|
| 1 | Token passthrough, no audience check | Validate `aud` = wiki MCP server; obtain a wiki-API token via token exchange with `act` = the MCP server |
| 2 | Headers in debug logs | Allowlist structured logging; purge and rotate; alert on `Authorization` strings in logs |
| 3 | Inherited laptop environment | Launch with an allowlisted environment and a read-only, wiki-scoped token |
| 4 | Unvalidated discovery URLs | Egress proxy blocking private and link-local ranges; HTTPS only |

**The general rule.** **Every credential should be usable only for the one hop it was issued for, visible only where it is
used, and present only in the process that needs it.**

---

## 7. Practical activity

**File:** [`labs/m9/l12_credentials_token_handling.py`](../../labs/m9/l12_credentials_token_handling.py)

**No API key, no network, no third-party dependencies.** All secrets are fake and generated locally.

```bash
source .venv/bin/activate
python labs/m9/l12_credentials_token_handling.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 on Linux (pure standard library). Run twice; output identical.

```text

============================================================================
1. TOKEN PASSTHROUGH VS AUDIENCE VALIDATION + A DOWNSTREAM TOKEN
============================================================================
  li's token for the files MCP server
    passthrough server : returned ['li-contract.pdf'] (audit log: caller=li, on behalf of li)
    correct server     : returned ['li-contract.pdf'] (audit log: caller=mcp-files, on behalf of li)
  li's token for the calendar API (stolen)
    passthrough server : returned ['li-contract.pdf'] (audit log: caller=li, on behalf of li)
    correct server     : rejected by the MCP server (wrong audience)
  attacker's own token for the files MCP server
    passthrough server : returned ['eve-notes.txt'] (audit log: caller=eve, on behalf of eve)
    correct server     : returned ['eve-notes.txt'] (audit log: caller=mcp-files, on behalf of eve)

  With passthrough, a token stolen from the CALENDAR API read li's files, and
  the files API's audit log cannot tell the MCP server was involved at all.

============================================================================
2. A STDIO SERVER INHERITS ITS HOST'S ENVIRONMENT
============================================================================
  subprocess with inherited environment         : server can read 5 planted credential(s): ['AWS_SECRET_ACCESS_KEY', 'CATALOG_READONLY_TOKEN', 'DATABASE_URL', 'GITHUB_TOKEN', 'OPENAI_API_KEY']
  SDK-style allowlist + one explicit credential : server can read 1 planted credential(s): ['CATALOG_READONLY_TOKEN']

  A local MCP server runs with whatever the launching process hands it. The
  official Python SDK passes only a short allowlist plus the variables you name.

============================================================================
3. SECRETS IN LOGS: HEADER REDACTION VS STRUCTURED LOGGING
============================================================================
  no redaction            : 240/240 secret-bearing lines still leak; benign lines altered: 0
  header-only redactor    : 200/240 secret-bearing lines still leak; benign lines altered: 0
  pattern-based redactor  :   0/240 secret-bearing lines still leak; benign lines altered: 0

  The pattern-based redactor was written while looking at these six formats.
  Held-out formats it has never seen:
  pattern-based redactor on 40 held-out lines: 40/40 still leak

  structured logging with an allowlist of fields, same request:
    {"event": "tools/call", "method": "tools/call", "tool": "search", "request_id": "req_1", "status": 200, "duration_ms": 42, "principal": "li"}
  Redaction chases formats; an allowlist never writes the secret in the first place.

============================================================================
4. SSRF: URLS A SERVER GIVES A CLIENT DURING DISCOVERY
============================================================================
  https://auth.example.com/.well-known/oauth-authorization-s naive: allow  careful: needs DNS: resolve once, re-check, pin
  http://169.254.169.254/latest/meta-data/iam/security-crede naive: block  careful: block (169.254.169.254)
  http://[::ffff:169.254.169.254]/latest/meta-data/          naive: allow  careful: block (169.254.169.254)
  http://0xA9FEA9FE/latest/meta-data/                        naive: allow  careful: block (169.254.169.254)
  http://2852039166/latest/meta-data/                        naive: allow  careful: block (169.254.169.254)
  http://0251.0376.0251.0376/latest/meta-data/               naive: allow  careful: block (169.254.169.254)
  http://127.1:6379/                                         naive: allow  careful: block (127.0.0.1)
  http://[::1]:8080/admin                                    naive: allow  careful: block (::1)
  https://auth.example.com@169.254.169.254/                  naive: allow  careful: block (169.254.169.254)
  https://10.20.30.40/.well-known/openid-configuration       naive: allow  careful: block (10.20.30.40)
  https://metadata.internal.example/token                    naive: allow  careful: needs DNS: resolve once, re-check, pin

  internal destinations the naive check let through: 8
  (the careful column ignores the http/https difference so it is judged on the
  address alone; in production also require https and use an egress proxy)

============================================================================
5. TOKEN CACHE FILE PERMISSIONS ON THIS MACHINE
============================================================================
  open(path, 'w')        -> mode 0o644  readable by other local users: True
  os.open(..., 0o600)    -> mode 0o600  readable by other local users: False

  Prefer the OS credential store (Keychain, Credential Manager, Secret Service)
  where available; if a file is unavoidable, create it 0600 from the start.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the child-process environment probe, the file modes, the redaction
  counts over 300 generated lines, and the address classification (using the
  standard library's ipaddress and inet_aton parsers).

  ILLUSTRATIVE: section 1's tokens are dicts, not signed tokens; the log corpus
  is synthetic; no DNS lookups are made, so hostnames are reported as needing one.

  NOT SHOWN: token exchange (RFC 8693) wire details, OS keychain APIs, and egress
  proxy configuration.

Done.
```

### 7.3 Reading the result

**Section 1's audit column matters as much as the access column.** Even for legitimate requests, passthrough makes the
MCP server invisible to the upstream API's logs.

**Section 3's held-out line is the most transferable result in the lesson.** Any filter tuned on examples you've seen will
miss the formats you haven't — design so the secret is never written.

**Section 4 shows four spellings of one address.** Validation must parse, not pattern-match.

---

## 8. Common mistakes and troubleshooting

1. **Forwarding the client's token to an upstream API.** §5.2 — forbidden; use a separate downstream credential.
2. **Accepting tokens without an audience check "because the signature is valid".** §5.2, M9-L10.
3. **Launching stdio servers with the full inherited environment** or personal admin credentials. §5.3.
4. **Logging headers, bodies, arguments or results**, and relying on redaction. §5.4.
5. **Putting tokens in URLs.** §5.4.
6. **Following server-supplied URLs without SSRF controls**, or hand-rolling IP checks. §5.5.
7. **Creating token files with default permissions**, then `chmod`-ing. §5.6.

| Symptom | Likely cause | Fix |
|---|---|---|
| Upstream logs show users but not the MCP server | Token passthrough | Token exchange / server credential with actor identity |
| Tokens for other internal services work on the MCP server | No audience validation | Reject `aud` ≠ this server |
| Secrets found in the log platform | Request/header logging | Allowlist fields; purge; rotate affected credentials |
| Security scan flags `~/.config/app/tokens.json` as world-readable | File created with default mode | Create 0600 or use the OS keychain |
| Outbound requests to 169.254.169.254 from the host | Discovery or `$ref` URLs followed unchecked | Address checks on every hop; egress proxy |

---

## 9. Security, privacy, reliability, cost

- **Security.** Audience validation plus per-hop credentials limits a stolen token to one service; minimal scopes (M9-L11)
  limit it within that service. Treat everything crossing a boundary in §5.1's table as untrusted.
- **Privacy.** Logs are the largest accidental store of personal data and credentials in most systems; allowlist them.
- **Reliability.** Separate downstream credentials can be rotated without disrupting users' tokens, and an honest audit
  trail shortens incident investigations (§6).
- **Cost.** Credential leaks force rotation, forensic work and disclosure; egress proxies and keychains are cheap by
  comparison.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List three untrusted inputs for an MCP server and three for an MCP client.
2. What two rules in the spec together forbid token passthrough?
3. Which environment variables does the `mcp` 2.2.0 SDK pass to a stdio server on Linux by default?
4. Why did the pattern-based redactor leak 40/40 held-out lines?
5. Give three different spellings of `169.254.169.254` from §7.4.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a third launch in §7.2 that passes `os.environ` filtered by a *denylist* of names containing `KEY`,
   `TOKEN` or `SECRET`. Which planted credential still gets through, and why?
2. Add two more held-out log formats of your own and measure the pattern-based redactor.
3. Extend `careful_check` to re-validate redirect targets given a list of hops.
4. Change §7.5 to write a token file, then `chmod` it to 0600, and explain the race window.
5. Draw §5.1's diagram for a system you know, marking where each credential lives.

### Exercise 3 — Challenge (~60 min)

1. Implement a token exchange endpoint (RFC 8693 shape) in §7.1's simulation that issues a downscoped, audience-bound token
   with an `act` claim, and show the upstream audit log.
2. Use the `keyring` package to store and retrieve a token on your machine; document where it is stored on your OS.
3. Build a log-scanning test that fails CI if any log line matches a high-entropy secret heuristic, and measure its false
   positives on the benign lines.
4. Implement DNS-pinned fetching: resolve once, validate every address, connect to the validated IP with the original Host
   header (TLS SNI preserved). Test against a hostname you control locally (e.g. via `/etc/hosts`).
5. Threat-model an MCP proxy server using a static third-party client id, and write the consent-page requirements from §5.2.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l12).)*

**Q1.** Which input should an MCP **client** treat as untrusted?

- A. The message the user typed into the host
- B. The issuer value it recorded before redirecting
- C. URLs in a server's resource metadata
- D. The PKCE verifier it generated for this flow

**Q2.** In §7.1, what did the stolen calendar-API token achieve against the passthrough server?

- A. It read li's files
- B. It was rejected for wrong audience
- C. It read the attacker's own files
- D. It crashed the files API

**Q3.** When an MCP server needs to call an upstream API on a user's behalf, which token should it use?

- A. The user's MCP access token, unchanged
- B. A separate token issued for the upstream API
- C. The token with the broadest available scope
- D. The client's refresh token

**Q4.** Besides access control, what did passthrough break in §7.1?

- A. TLS encryption between services
- B. PKCE verification at the token endpoint
- C. Response caching at the gateway
- D. The upstream audit trail

**Q5.** How many planted credentials could a stdio server read with an inherited environment in §7.2?

- A. 1
- B. 5
- C. 0
- D. 6

**Q6.** Why is the environment especially important for stdio servers?

- A. stdio servers cannot read configuration files
- B. Environment variables are encrypted by the OS
- C. Their credentials come from it, per the spec
- D. OAuth tokens are always passed as variables

**Q7.** What does §7.3's held-out result show about pattern-based redaction?

- A. It damages many benign log lines
- B. It is slower than structured logging
- C. It fails on JWTs
- D. It misses formats it was not written for

**Q8.** Which logging approach avoids secret leaks by construction?

- A. Emitting only allowlisted fields
- B. Masking every `Authorization` header
- C. Logging bodies at DEBUG level only
- D. Base64-encoding every log line

**Q9.** Why did `http://2852039166/` get past the naive URL check?

- A. The check did not parse query strings
- B. It uses HTTPS
- C. It is 169.254.169.254 written as one integer
- D. It is an IPv6 address

**Q10.** What does the MCP security guidance say about implementing IP address validation?

- A. Use one regular expression per blocked range
- B. Block only the IPv4 private address ranges
- C. It is unnecessary when every URL uses TLS
- D. Don't hand-roll it; attackers abuse encodings

**Q11.** What was wrong with creating the token cache with `open(path, "w")` in §7.5?

- A. Other local users could read it
- B. It was encrypted with a weak key
- C. It could not be read back
- D. It deleted existing tokens

**Q12.** In §6, why couldn't investigators tell legitimate wiki reads from replayed ones?

- A. The wiki API did not log requests
- B. Upstream logs showed only the user
- C. Tokens were stored in the OS keychain
- D. The MCP server used a downstream token

**Q13.** *(Written, rubric-graded.)* In under 150 words: you are reviewing a remote MCP server that wraps a SaaS API. List
the credential-handling checks you would make and what each prevents.

---

## 12. Revision notes

- **Boundaries:** ask "who could have set this value?" — model, client, other users and remote servers are untrusted.
- **No passthrough:** validate audience; use a separate upstream token (e.g. token exchange with actor identity). Measured:
  a stolen calendar token read files through a passthrough server, and the audit log showed only the user.
- **stdio environment:** inherited env exposed **5/5** planted credentials; SDK-style allowlist exposed **1**. Scope
  environment credentials tightly.
- **Logs:** header-only redaction leaked **200/240**; a tuned redactor leaked **40/40** held-out lines. Use allowlisted
  structured logs; no tokens in URLs.
- **SSRF:** naive checks passed **8** internal URLs (IPv4-mapped, hex, integer, octal, userinfo). Use real parsers, HTTPS,
  redirect checks, DNS pinning, egress proxies.
- **Storage:** OS keychain, or files created 0600 at creation.

---

## 13. Completion checklist

- [ ] I can draw the trust boundaries of an MCP deployment and list untrusted inputs per component.
- [ ] I can explain why passthrough is forbidden and design the alternative.
- [ ] I launch stdio servers with an allowlisted environment and scoped credentials.
- [ ] I log with an allowlist and never put tokens in URLs.
- [ ] I validate server-supplied URLs against SSRF and store tokens safely.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Authorization* (§Token Handling) and *Authorization Security Considerations* `[VERIFIED 2026-09-16]`
- MCP *Security Best Practices* (Confused Deputy, Token Passthrough, SSRF, Local MCP Server Compromise) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices> `[VERIFIED 2026-09-15]`
- MCP Python SDK `mcp` 2.2.0, `mcp/client/stdio.py` (`DEFAULT_INHERITED_ENV_VARS`, `get_default_environment`) `[VERIFIED 2026-09-16]`
- RFC 8693, *OAuth 2.0 Token Exchange* — <https://www.rfc-editor.org/rfc/rfc8693> `[STABLE]`
- RFC 9700, *Best Current Practice for OAuth 2.0 Security* — <https://www.rfc-editor.org/rfc/rfc9700> `[STABLE]`
- OWASP SSRF Prevention Cheat Sheet — <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html> `[STABLE]`

---

## 15. Next lesson

→ [M9-L13 — Permission Enforcement Outside the Model](M9-L13-permission-enforcement-outside-model.md) asks where the checks
live: why instructions to a model are not permissions, and how servers bind handles, requests and confirmations to the
principal who is actually allowed to use them.
