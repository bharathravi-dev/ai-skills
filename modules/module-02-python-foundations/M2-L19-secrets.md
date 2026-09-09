# M2-L19 — Secret Handling

| | |
|---|---|
| **Lesson ID** | M2-L19 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M2-L09](M2-L09-files-json-env.md), [M2-L17](M2-L17-git-dependencies.md) |

---

## 1. Learning objectives

1. **List** the places a secret must never appear, and **explain** why each leaks.
2. **Load** secrets safely and **fail fast** when one is missing.
3. **Redact** secrets from logs, errors and object representations.
4. **Rank** the storage options from worst to best, with the trade-off of each.
5. **Execute** the correct response to a leaked credential, in the right order.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Secret** | Any value that grants access: API key, token, password, private key, connection string. |
| **Credential** | A secret that identifies you to a system. |
| **Rotation** | Replacing a secret with a new one and revoking the old. |
| **Blast radius** | What an attacker can reach with one leaked secret. |
| **Least privilege** | Granting only the permissions actually needed. |
| **Secret manager** | A service storing secrets with access control and audit (AWS Secrets Manager, Vault). |
| **Environment variable** | A process-level key/value pair; the common delivery mechanism. |
| **`.env`** | A local development file holding environment variables. Never committed. |
| **Secret scanning** | Automated detection of credentials in code or history. |
| **Short-lived credential** | A token that expires in minutes or hours. |
| **Scope** | The set of operations a credential permits. |

---

## 3. Plain-language explanation

A secret is anything that lets someone act as you. The engineering problem is not choosing a clever
store — it is that secrets **spread**. One key, pasted once, ends up in a repository, a log, a
screenshot, a support ticket, a CI cache and three laptops.

**The places a secret must never appear:**

| Place | Why it leaks |
|---|---|
| Source code | Permanent in Git history (M2-L17 §7.3) |
| A committed config file | Same |
| Logs | Widely readable, long retention, often shipped to third parties |
| URLs / query strings | Recorded by proxies, browser history, server access logs |
| Error messages returned to users | Directly exposed |
| Screenshots and recordings | Shared casually, indexed |
| Chat messages and tickets | Long-lived and broadly readable |
| Container images | Every layer is inspectable, including deleted files (M2-L20) |
| Client-side code | Anything shipped to a browser is public |

**The single most important rule:** the moment a secret reaches a place it should not be, **rotate
it**. Deleting the file, the commit or the log line is cleanup. Rotation is the fix, because you
cannot prove nobody copied it.

---

## 4. Analogy

**A secret is a physical key to your office.** You would not tape it to the door, photograph it, or
post it in a group chat. If you lost it you would change the lock rather than hope.

### Where the analogy breaks

1. **Copying a physical key takes effort and leaves a trace. Copying a secret is free and
   invisible** — you can never know whether it was taken, which is why the response is always to
   assume it was.
2. **One key opens one door. One API key often opens everything** — which is what "blast radius"
   means and why scoping matters more than storage.
3. **Physical keys do not expire.** Short-lived credentials do, and that automatic expiry is the
   strongest control available.
4. **You notice a missing key.** A copied secret leaves the original in place; the only detection is
   audit logging of *use*.

---

## 5. Detailed technical explanation

### 5.1 Storage options, worst to best

| Approach | Security | Notes |
|---|---|---|
| Hard-coded in source | **Terrible** | Permanent in history; visible to everyone with repo access |
| Committed config file | **Terrible** | Identical problem |
| `.env` file, git-ignored | **Adequate for local dev only** | Plain text on disk; readable by any process as your user |
| Environment variables in the platform | **Good** | No file; scoped to the process. Visible to anything that can inspect the process |
| **Secret manager** (AWS Secrets Manager, Vault) | **Better** | Access-controlled, audited, rotatable, versioned |
| **Short-lived credentials from an identity provider** (IAM roles, OIDC) | **Best** | Nothing long-lived to leak; expires automatically |

The last row is the real goal. On AWS this means an **IAM role** rather than an access key
(M11-L05) — the credential is issued on demand, expires in hours, and there is no static value to
commit or log.

Note the ordering is about *exposure*, not effort. A `.env` file is fine for local development and
unacceptable in production; a secret manager without least-privilege scoping still has a large blast
radius.

### 5.2 Loading safely

```python
import os
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)       # excluded from __repr__
    model: str
    max_tokens: int

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("api_key must not be empty")

def load_settings() -> Settings:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Settings(
        api_key=api_key,
        model=os.getenv("LLM_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
    )
```

Three deliberate choices:

1. **`field(repr=False)`** — a dataclass `__repr__` prints every field (M2-L07 §9). Without this,
   `logger.info("settings: %s", settings)` emits your key. This one keyword is the difference between
   a safe object and a landmine.
2. **Fail at startup**, with an actionable message. A missing key should stop the process, not
   surface as a `401` on the first user request an hour later.
3. **Load once, pass the frozen object around.** Scattered `os.getenv` calls make failure modes
   unpredictable and configuration untestable.

### 5.3 Redaction

Redact in three places, because they leak independently:

```python
def mask(secret: str, *, keep: int = 4) -> str:
    """Show only the last few characters, enough to identify which key it is."""
    if not secret:
        return "(empty)"
    if len(secret) <= keep:
        return "*" * len(secret)
    return f"{'*' * (len(secret) - keep)}{secret[-keep:]}"
```

| Place | Control |
|---|---|
| Logs | A redacting filter (M2-L18 §7.2) plus never logging headers or bodies |
| Object repr | `field(repr=False)`, or a custom `__repr__` |
| Errors to users | Generic message + a request ID; details server-side only |

**Masking is a diagnostic aid, not protection.** `mask()` exists so you can tell *which* key is in
use, not so that printing keys becomes acceptable.

### 5.4 Scope and blast radius

Storage is secondary to **what the secret can do**.

| Question | Better answer |
|---|---|
| What can this key access? | One service, one environment |
| How long is it valid? | Hours, not forever |
| Is production separate from development? | Always separate keys |
| Can it be revoked independently? | One key per service, not one shared key |
| Is its use logged? | Yes, with an identity attached |

**A read-only key that expires in an hour and covers one service is safer than a permanent
all-access key in the finest vault available.** Reducing what a secret *permits* beats improving where
it is *stored*, and it is usually easier.

### 5.5 Detection

Humans do not reliably catch secrets in review. Automate it:

- **Pre-commit hooks** — `gitleaks`, `detect-secrets`. Fast, local, before the mistake exists.
- **CI scanning** — catches what bypassed the hook.
- **Platform push protection** — blocks the push entirely.
- **Provider-side alerts** — some providers scan public repositories and revoke automatically.

Layer them. Each catches what the previous one missed.

### 5.6 When a secret leaks

**In this order:**

1. **Rotate immediately.** Issue a new secret, update consumers, **revoke the old one**. Revocation
   is the step people forget; issuing a new key does nothing while the old one still works.
2. **Assess exposure.** Where did it appear, for how long, who could read it? A public repository is
   worst; assume it was scraped within minutes.
3. **Check for misuse.** Provider usage logs, billing anomalies, unfamiliar source addresses.
4. **Clean up** — history rewriting, log purging. **Cleanup is not remediation.**
5. **Fix the cause.** A hook, a scanner, a changed process. A leak that can recur will.

**Rotation first. Always.** Every minute spent rewriting Git history before rotating is a minute the
live credential is still valid.

### 5.7 Assumptions and limitations

- Environment variables are visible to anything that can inspect the process, and to child processes.
  Better than files; not a vault.
- A secret manager still delivers a plaintext value into your process memory.
- `.env` is plain text on disk. Acceptable locally; never in production.
- Rotation requires the system to tolerate it — if changing a key needs a coordinated outage, you
  will not rotate promptly, which is itself the vulnerability.

---

## 6. Worked example — hardening configuration

**v1 — hard-coded.**

```python
API_KEY = "sk-live-abc123"
```
Permanent in history. Visible to everyone with repo access. Shipped in the container image.

**v2 — environment variable, unchecked.**

```python
API_KEY = os.getenv("ANTHROPIC_API_KEY")
```
Better, but `None` when unset, so the failure is a confusing `TypeError` or a `401` far from the
cause.

**v3 — checked at startup.**

```python
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY is not set")
```
Fails fast. Still a module-level global, still repr-able, still easy to log.

**v4 — a settings object with `repr=False`.** As in §5.2. The key is no longer printable by accident.

**v5 — the remaining leaks.** Even v4 leaks through routes v4 does not cover:

```python
# Leaks in an exception message
raise RuntimeError(f"auth failed with key {api_key}")

# Leaks in a URL - recorded by proxies and access logs
httpx.get(f"https://api.example.com/v1?api_key={api_key}")

# Leaks in a log line
logger.info("request headers: %s", dict(request.headers))

# Leaks in a container image, even after deletion (M2-L20)
# RUN echo "KEY=sk-live-abc" > /app/.env && rm /app/.env
```

**Each needs its own control:** never interpolate secrets into messages; always use the
`Authorization` header rather than a query parameter; redact headers before logging (M2-L11 §7.3);
and use build secrets or runtime environment for containers, never a `RUN` layer.

**v6 — what production actually looks like.**

```python
def load_settings() -> Settings:
    if os.getenv("APP_ENV") == "local":
        load_dotenv()                      # .env, local development only
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Settings(api_key=api_key, ...)
```

In production the value arrives from the platform — a secret manager injected as an environment
variable, or better, a short-lived credential from an IAM role (M11-L05, M11-L17). `load_dotenv` runs
only locally, so a stray `.env` on a server cannot silently override a managed secret.

---

## 7. Practical activity

**File:** [`labs/m2/l19_secrets.py`](../../labs/m2/l19_secrets.py)

```bash
python3 labs/m2/l19_secrets.py
```

Standard library only. Shows a dataclass leaking a key through `__repr__` and the `repr=False` fix,
five distinct leak routes with their controls, a masking function, a working secret scanner run over
a synthetic file, and the leak-response checklist.

**All keys in the lab are obviously fake** (`sk-live-FAKE-...`) and no real credential is used.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `field(repr=False)` | Excludes a field from the generated `__repr__`. |
| `mask(secret)` | Shows the last 4 characters only — enough to identify, not to use. |
| `re.compile(r"sk-[A-Za-z0-9_\-]{8,}")` | A scanner pattern. Illustrative, not exhaustive. |
| `os.getenv(..., "").strip()` | Empty-safe; `.strip()` catches a trailing newline from a copy-paste. |
| `raise RuntimeError(...)` at startup | Fail fast with an actionable message. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08, Python 3.12.3:

```
==========================================================================
SECRET HANDLING
==========================================================================
All credentials shown below are fake and non-functional.

--------------------------------------------------------------------------
1. THE DATACLASS __repr__ LEAK
--------------------------------------------------------------------------
  @dataclass with no repr control:
    print(settings)      -> LeakySettings(api_key='sk-live-FAKE-4b8c1e77d2a9f30e', model='claude-sonnet-5')
    f-string in a log    -> settings: LeakySettings(api_key='sk-live-FAKE-4b8c1e77d2a9f30e', model='...

  @dataclass with field(repr=False) on api_key:
    print(settings)      -> SafeSettings(model='claude-sonnet-5')

  Same object, same key, one keyword different. The first version
  emits your credential from any print, log, f-string, traceback
  or debugger inspection. This is the M2-L07 warning made concrete.

  When you must identify a key: mask() -> *************************f30e
  short value                          -> ***
  empty value                          -> (empty)

--------------------------------------------------------------------------
2. FIVE LEAK ROUTES, AND THE CONTROL FOR EACH
--------------------------------------------------------------------------
  ROUTE 1 - interpolated into an exception message
    BAD : auth failed with key sk-live-FAKE-4b8c1e77d2a9f30e
    GOOD: auth failed (key *************************f30e, request req_7f3c)

  ROUTE 2 - a query parameter
    BAD : GET /v1/messages?api_key=sk-live-FAKE-4b8c1e77d2a9f30e
          -> written to proxy logs, server access logs, browser history
    GOOD: GET /v1/messages
          Authorization: Bearer <key>   (headers are not logged by default)

  ROUTE 3 - logging the header dict
    BAD : {'Authorization': 'Bearer sk-live-FAKE-4b8c1e77d2a9f30e', 'X-Api-K...
    GOOD: {'Authorization': '***REDACTED***', 'X-Api-Key': '***REDACTED***', 'Content-Type': 'application/json', 'User-Agent': 'course/1.0'}

  ROUTE 4 - a returned error message
    BAD : 500 {"error": "connection to db://user:hunter2@host failed"}
    GOOD: 500 {"error": "internal error", "request_id": "req_7f3c"}
          (full detail logged server-side against that request_id)

  ROUTE 5 - a container image layer
    BAD : RUN echo "KEY=sk-live-..." > .env && rm .env
          -> the file is in the layer FOREVER, even though it was
             deleted in the same command. Layers are immutable and
             anyone who can pull the image can extract it (M2-L20).
    GOOD: pass the value at RUNTIME via the environment, or use
          BuildKit build secrets which are never written to a layer.

--------------------------------------------------------------------------
3. LOADING - fail fast, with an actionable message
--------------------------------------------------------------------------
  environment                       result
  unset                             RuntimeError: DEMO_API_KEY is not set. Copy .env...
  empty string                      RuntimeError: DEMO_API_KEY is not set. Copy .env...
  whitespace only                   RuntimeError: DEMO_API_KEY is not set. Copy .env...
  newline from a copy-paste         ok -> key ending **f30e
  valid                             ok -> key ending **f30e

  Note the whitespace and newline rows. A key copied from a browser
  often carries a trailing newline; .strip() turns a baffling 401
  into either a correct load or a clear startup error.

--------------------------------------------------------------------------
4. SECRET SCANNING - and its false-positive trade-off
--------------------------------------------------------------------------
  Scanned config.py (13 lines)

   line  pattern               match
      5  anthropic-style       ***********************a9f30e
      6  aws access key        **************XAMPLE
      7  connection string     ***********************nter2@
      8  password assignment   ****************************ttery"
     11  anthropic-style       ******************alogue

  5 findings.

  Now the honest part. Line 11 is 'sk-2024-winter-catalogue' -
  a product code, not a key, and the scanner flagged it. Loosen
  the pattern and you catch more real secrets and more noise;
  tighten it and you miss credentials in unexpected formats.

  A noisy scanner gets disabled, which is worse than a strict
  one. Tune it, add an allow-list for known false positives,
  and treat it as ONE layer alongside a pre-commit hook, CI
  scanning and platform push protection.

--------------------------------------------------------------------------
5. THE LEAK RESPONSE - order matters
--------------------------------------------------------------------------
  1. ROTATE and REVOKE    (minutes)
      Issue a new secret, update consumers, REVOKE the old one.
      Revocation is the step people skip.
  2. Assess exposure      (minutes)
      Where did it appear, for how long, who could read it? Public
      repo = assume scraped within minutes.
  3. Check for misuse     (hours)
      Provider usage logs, billing anomalies, unfamiliar source IPs.
  4. Clean up             (days)
      Rewrite history, purge logs. This is CLEANUP, not remediation.
  5. Fix the cause        (days)
      Pre-commit hook, CI scan, changed process. A leak that can
      recur, will.

  Every minute spent on step 4 before step 1 is a minute the live
  credential still works. You cannot prove nobody copied it, so
  the only safe assumption is that somebody did.

==========================================================================
```

### 7.3 Reading the result

**Section 1 is one keyword's difference:**

```
LeakySettings(api_key='sk-live-FAKE-4b8c1e77d2a9f30e', model='claude-sonnet-5')
SafeSettings(model='claude-sonnet-5')
```

Same class shape, same key, and the first one emits your credential from **any** print, log line,
f-string, traceback or debugger inspection. You do not have to write `print(settings.api_key)` — you
only have to write `print(settings)`, or have an exception occur while that object is in scope.

`field(repr=False)` is the smallest security control in this course and one of the highest-value.

**Section 3's middle rows are worth noticing:**

```
whitespace only             RuntimeError: DEMO_API_KEY is not set...
newline from a copy-paste   ok -> key ending **f30e
```

A key copied from a browser or a chat message frequently carries a trailing newline. Without
`.strip()`, that key is sent to the provider with a `\n` on the end and you get a `401` that appears
to say your perfectly correct key is invalid. The whitespace-only case is caught as *missing* rather
than accepted as a value — both behaviours come from one `.strip()`.

**Section 4 is deliberately honest about scanning.** Five findings, and **one is wrong**: line 11's
`sk-2024-winter-catalogue` is a product code, not a credential. Meanwhile the scanner correctly found
the fake Anthropic key, the AWS key, the database connection string with an embedded password, and a
password assignment.

That false positive is the whole trade-off. Loosen the pattern to catch credentials in unusual
formats and you generate noise; tighten it and you miss real secrets. **The failure mode that matters
is a noisy scanner being disabled**, which leaves you with nothing. Tune the patterns, maintain an
allow-list, and treat scanning as one layer among four — pre-commit hook, CI scan, push protection,
provider alerts.

**Section 5's ordering is the operational point.** Rotation takes *minutes* and is step 1. History
rewriting takes *days* and is step 4. Teams routinely invert these because rewriting history feels
like fixing the problem — it produces a clean-looking repository while the leaked credential
continues to work.

**You cannot prove nobody copied a secret.** There is no log of reads, no missing original, no
evidence either way. That asymmetry is why the response is always to assume compromise rather than to
assess likelihood.

**Verification:** confirm `SafeSettings` prints without the key, the whitespace-only environment
raises while the trailing-newline one succeeds, and that the scanner produces exactly one false
positive.

---

## 8. Common mistakes and troubleshooting

1. **Hard-coding a key "just for testing".** It gets committed.
2. **Secrets in URLs.** Logged everywhere.
3. **Logging headers or whole config objects.**
4. **A dataclass or Pydantic model without `repr=False`** on secret fields.
5. **Deleting a leaked secret instead of rotating it.**
6. **Rotating without revoking the old value.**
7. **One shared key across all services and environments.**
8. **`.env` in production.**
9. **Secrets baked into a container image**, including in a deleted-file layer.
10. **Relying on review to catch secrets.**

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: expected str, got None` | Secret not set, unchecked | Fail fast at startup |
| Works locally, `401` deployed | `.env` not present in production | Configure the platform's secrets |
| Key visible in logs | Logged headers or a config object | Redacting filter; `repr=False` |
| Key in Git history | Committed at some point | **Rotate**, then consider rewriting |
| `401` after rotation | Consumers still using the old value | Update all consumers, then revoke |
| Secret in an image | Added in a `RUN` or `COPY` layer | Build secrets or runtime env (M2-L20) |

---

## 9. Security, privacy, reliability and cost

- **Security.** Blast radius beats storage. Scope keys per service and environment, prefer
  short-lived credentials, and ensure each can be revoked independently.
- **Privacy.** A leaked key often grants access to customer data, making a credential leak a data
  breach with notification obligations (M10-L06).
- **Reliability.** Rotation must be routine. If it requires an outage, you will delay it — and that
  delay is the actual risk.
- **Cost.** A leaked LLM API key is directly monetisable; stolen keys are used to resell inference.
  Set spending limits and alerts (M11-L06) so misuse is visible quickly.
- **Governance.** Which secrets exist, who can access them, and when they were last rotated belong in
  your inventory (M10-L03).

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Write a frozen dataclass holding an API key. Print it and confirm the key appears.
2. Add `field(repr=False)` and confirm it no longer does.
3. Write `load_settings()` raising a clear `RuntimeError` when the key is missing. Test with the
   variable unset, set to an empty string, and set to `"   "`.

### Exercise 2 — Intermediate (~25 min)

1. Write `mask(secret, keep=4)` handling empty, short and normal values. Test all three.
2. Write `redact_headers(headers)` masking `Authorization`, `Cookie` and anything whose name contains
   `key`, `token` or `secret`. Test with six header sets including odd casing.
3. Write a scanner that walks a directory and reports file, line number and pattern for anything
   resembling a credential. Run it against a file you create containing three fake keys and two
   false-positive lookalikes.
4. Report how many false positives your patterns produce and explain the trade-off between a strict
   and a loose pattern.

### Exercise 3 — Challenge (~25 min)

1. List every place a secret could leak in the Project 2 API you will build. Aim for at least eight,
   and give the control for each.
2. Write a pre-commit hook script that blocks a commit when a staged file matches a credential
   pattern. Test it: staging a file with a fake key must fail, and without must succeed.
3. Demonstrate the URL leak: make a request with the key as a query parameter to the M2-L11 lab
   server, and show it appearing in the server's access log. Then move it to a header and show it no
   longer appears.
4. Write the incident runbook for "an API key was committed to a public repository", as numbered
   steps with an owner and a target time for each. Put rotation first and justify the ordering in one
   sentence.
5. Explain in three sentences why a short-lived credential from an IAM role is safer than a permanent
   key in a secret manager.

---

## 11. Quiz

**Q1.** A secret has been committed to a repository. What is the **first** action?

- A. Delete the file and commit.  B. Rewrite history.  C. Rotate the credential and revoke the old
  one.**  D. Add it to `.gitignore`.

**Q2.** Why is a dataclass holding an API key dangerous by default?

- A. Dataclasses cannot hold strings.
- B. The generated `__repr__` prints every field, so logging or printing the object emits the key —
  use `field(repr=False)`.
- C. They are mutable.
- D. They cannot be frozen.

**Q3.** Why must a secret never appear in a URL?

- A. URLs have a length limit.
- B. URLs are recorded by proxies, server access logs and browser history, so the secret is written
  to many systems you do not control.
- C. It would be encrypted.
- D. It is fine if the URL uses HTTPS.

**Q4.** Which is the strongest control?

- A. A long random key in a secret manager.
- B. A `.env` file with restrictive permissions.
- C. Short-lived credentials issued by an identity provider, which expire automatically so there is
  no long-lived value to leak.
- D. Encrypting the key in source code.

**Q5.** Why is scope more important than storage?

- A. It is not; storage matters more.
- B. A read-only, single-service, short-lived credential limits what an attacker can do even if it
  leaks, whereas a permanent all-access key is catastrophic regardless of where it was kept.
- C. Scoping is easier to implement.
- D. Storage cannot be secured.

**Q6.** Rotating a key without revoking the old one achieves what?

- A. Full remediation.
- B. Nothing for security — the leaked credential still works.
- C. It invalidates the old key automatically.
- D. It rotates the blast radius.

**Q7.** What does `mask(secret)` showing the last four characters give you?

- A. Security.
- B. A diagnostic aid — you can identify *which* key is in use without exposing a usable value. It
  does not make printing keys acceptable.
- C. Encryption.
- D. Rotation.

**Q8.** Where is a `.env` file appropriate?

- A. Everywhere.  B. Local development only; production should use platform-managed secrets or
  short-lived credentials.  C. Production only.  D. Never.

**Q9.** Why should secret detection be automated rather than left to code review?

- A. Reviewers are careless.
- B. A secret is a few characters in a large diff and is reliably missed by humans, while the cost of
  missing it once is a compromised credential — layered automated scanning catches what review does
  not.
- C. Automation is faster to write.
- D. Review cannot see config files.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why "we deleted the commit" is not an
adequate response to a leaked API key.

---

## 12. Revision notes

- A secret is anything granting access. The engineering problem is that **secrets spread**.
- **Never in:** source, committed config, logs, URLs, user-facing errors, screenshots, chat, container
  images, client-side code.
- Storage, worst → best: hard-coded · committed config · **`.env` (local only)** · platform env vars ·
  **secret manager** · **short-lived credentials from an identity provider (best)**.
- **Scope beats storage.** A read-only, one-service, one-hour credential beats a permanent all-access
  key in any vault.
- Load once, **fail fast at startup** with an actionable message, pass a frozen settings object.
- **`field(repr=False)`** on every secret field — dataclass and Pydantic `__repr__` print everything.
- Redact in three places: logs, object repr, user-facing errors. **Masking is diagnostic, not
  protective.**
- Automate detection: pre-commit hook + CI scan + push protection + provider alerts.
- **Leak response, in order: ROTATE and revoke → assess exposure → check for misuse → clean up → fix
  the cause.** Cleanup is not remediation.
- **Rotation must be routine.** If it needs an outage, you will delay it, and the delay is the risk.

---

## 13. Completion checklist

- [ ] I can list eight places a secret must never appear.
- [ ] My settings object uses `field(repr=False)` and fails fast when a key is missing.
- [ ] I wrote and tested `mask` and `redact_headers`.
- [ ] I ran a secret scanner and understand its false-positive trade-off.
- [ ] I wrote a pre-commit hook that blocks a staged secret.
- [ ] I can state the leak-response order and why rotation is first.
- [ ] I can explain why scope beats storage.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- OWASP Secrets Management Cheat Sheet.
  <https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html> `[UNVERIFIED]`
- gitleaks. <https://github.com/gitleaks/gitleaks> `[UNVERIFIED]`
- AWS Secrets Manager and IAM roles are covered in M11-L17 and M11-L05.

---

## 15. Next lesson

→ [M2-L20 — Docker Fundamentals for Python Services](M2-L20-docker.md)

The final lesson of Module 2: packaging your application so it runs identically everywhere — and how
a secret ends up permanently inside an image even after you delete it.
