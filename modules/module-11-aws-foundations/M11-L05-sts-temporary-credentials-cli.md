# M11-L05 — Temporary Credentials, STS and the CLI

| | |
|---|---|
| **Lesson ID** | M11-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M11-L04](M11-L04-iam-policies-roles.md) |

---

## 1. Learning objectives

1. **Argue** for short-lived credentials from the exposure window, not from principle.
2. **Apply** STS session-duration rules, including the role-chaining cap.
3. **Resolve** the SDK credential provider chain and debug the "wrong credentials won" failure.
4. **Quantify** the exposure a long-lived access key estate represents.
5. **Require IMDSv2** and explain which link of an SSRF chain it breaks.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **STS** | AWS Security Token Service — issues temporary credentials. |
| **`AssumeRole`** | The STS call that exchanges one identity for a role session. |
| **Role session** | Temporary credentials (access key id, secret, **session token**) that expire. |
| **Role chaining** | Assuming a role *from* a role session; capped at one hour. |
| **Provider chain** | The ordered list of places an SDK looks for credentials. |
| **IMDS** | Instance Metadata Service at `169.254.169.254`, where EC2 delivers role credentials. |
| **IMDSv2** | Session-oriented IMDS: a `PUT` obtains a token, required on subsequent requests. |
| **Hop limit** | How many network hops an IMDSv2 response may traverse; set to 1 to keep containers out. |
| **OIDC federation** | Exchanging an identity provider's token (e.g. a CI system's) for a role session — no stored keys. |

---

## 3. Plain-language explanation

### 3.1 Lifetime, not secrecy, is the control you can actually set

§7.1: a leak takes **72 hours** to notice. A never-rotated access key is useful to an attacker for all **72**. A key on a
**90-day rotation** is *also* useful for 72 — rotation changes nothing when detection is faster than the rotation period.
A 12-hour role session: **12 hours**. A one-hour session: **1**. A 15-minute session: **0.25 h — 0.35%** of the window.

Sessions shorten exposure by orders of magnitude **and require nobody to remember anything**. That is the argument for
roles over users, stated as arithmetic.

### 3.2 STS has rules you will meet the hard way

§7.2 validates eight duration requests. Below **900 seconds** is rejected; above **43,200** is rejected; above the
**role's own maximum** (an administrator setting between 1 and 12 hours) is rejected; and **role chaining caps the session
at one hour** regardless of what you ask for.

### 3.3 The chain decides, and it is not what you attached

§7.3 resolves six environments. On an EC2 instance with a role **and** a leftover `~/.aws/credentials`, the leftover
**wins** — it sits higher in the chain. The symptom is "access denied for a permission the role obviously has", and the
fix is deleting the stale credential, not widening the policy.

### 3.4 An access-key estate is a pile of exposure

§7.4: 240 keys, **38% older than a year**, contributing **66%** of **75,722 key-days** of exposure. Each is a credential
with no expiry that someone must remember to rotate.

### 3.5 IMDSv2 breaks the SSRF chain

§7.5: under IMDSv1, a plain `GET` from a server-side request retrieves the role's credentials — a web bug becomes an AWS
credential compromise. IMDSv2 requires a `PUT` first, which a forged fetch typically cannot send, and a response hop limit
of 1 keeps containers from reaching the host's IMDS.

---

## 4. Analogy

**Hotel key cards versus a cut brass key.** The card stops working at checkout whether or not anyone remembers to collect
it. The brass key works until someone changes the lock — and "we change the locks every 90 days" does not help if the key
was copied on day two. Reception can also issue a card for the gym only, for two hours, without reissuing anything else.

### Where the analogy breaks

- **A lost card is one room; a leaked AWS credential is whatever the role reaches** (L04 §7.2). Lifetime limits the
  window, not the blast radius — you still need both.
- **Hotel cards are handed over; cloud credentials are delivered invisibly** by the metadata service, which is why §5.6
  matters at all.

---

## 5. Detailed technical explanation

### 5.1 What STS issues

An STS response contains an access key id, a secret access key, a **session token** and an **expiry**. All three parts
must be sent; requests without the session token fail with a signature error, which is the usual first symptom of code
that copies only two of the three fields.

Common calls:

| Call | Used for |
|---|---|
| `AssumeRole` | Cross-account access, elevated roles, application roles |
| `AssumeRoleWithWebIdentity` | OIDC federation — CI systems, Kubernetes service accounts, mobile apps |
| `AssumeRoleWithSAML` | Enterprise SAML identity providers |
| `GetSessionToken` | MFA-protected temporary credentials for an IAM user |
| `GetCallerIdentity` | "Who am I?" — the first command to run when debugging anything |

### 5.2 Session durations

`[VERIFIED 2026-09-17 — AWS STS API Reference, `AssumeRole`]`

- `DurationSeconds` ranges from **900** (15 minutes) to **43,200** (12 hours).
- The role's **maximum session duration** is an administrator setting from **1 hour to 12 hours**; a request above it
  fails.
- The default is **3,600** seconds.
- **Role chaining limits a CLI or API role session to a maximum of one hour**, and a larger `DurationSeconds` makes the
  call fail.

Choose the duration from the work: a CI deployment needs minutes; an interactive session, an hour; a long batch job is a
reason to re-assume periodically rather than to request twelve hours.

### 5.3 The credential provider chain

`[REAL, resolved]` §7.3. The usual order for the AWS CLI and SDKs:

```text
1. explicit parameters in code / CLI flags
2. environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
3. assumed role / SSO / web identity configured in the profile
4. shared credentials file (~/.aws/credentials)
5. container credentials (ECS/EKS task role endpoint)
6. instance metadata (IMDS)
```

Debugging recipe, in order:

```bash
aws sts get-caller-identity            # who am I actually?
env | grep AWS_                        # is something set that should not be?
aws configure list                     # which profile and source is in play?
```

`get-caller-identity` answers in one line the question that policy debugging usually gets wrong. If the ARN is not what
you expected, no amount of policy editing will help.

### 5.4 Getting rid of long-lived keys

`[REAL, computed — ILLUSTRATIVE distribution]` §7.4 — 75,722 key-days, 66% of it from keys over a year old.

| Instead of an access key | Use |
|---|---|
| Developer laptop | IAM Identity Center sign-in; `aws sso login`; short sessions |
| Application on EC2/ECS/Lambda | The compute's role (delivered via IMDS or the task-role endpoint) |
| CI/CD pipeline | OIDC federation: the pipeline's own token exchanged for a role session (L18) |
| On-premises or third-party system | IAM Roles Anywhere, or a role assumed via an identity provider |
| Genuinely unavoidable key | Documented exception, owner, rotation schedule, scoped role, alarms on use |

Detect them: report access keys by age, keys never used, and keys used from unexpected regions or addresses (L16).

### 5.5 Cross-account and chaining in practice

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::222222222222:role/DataReader \
  --role-session-name alice-analysis \
  --external-id a7f3-customer-42 \
  --duration-seconds 3600
```

Two practical notes: give the session a **meaningful name** — it appears in CloudTrail and is how an investigator
attributes an action to a person (M10-L13); and prefer configuring the role in a **profile** (`role_arn` +
`source_profile`) so the SDK refreshes the session automatically instead of your code juggling expiry.

### 5.6 IMDS and SSRF

`[REAL, stepped]` §7.5.

IMDSv1 answers a plain `GET` to `169.254.169.254`. Any server-side request forgery in your application — a URL-fetching
feature, an image loader, a webhook tester, a model asked to fetch a link (M9-L12) — can retrieve the instance role's
credentials and use them with that role's full reach.

IMDSv2 requires a `PUT` to `/latest/api/token` with a TTL header, and subsequent `GET`s must carry the token. A forged
fetch typically cannot issue the `PUT` or set headers, which breaks the chain. Configure:

- `HttpTokens: required` (IMDSv2 only) on every instance and launch template.
- `HttpPutResponseHopLimit: 1` so containers on a bridge network cannot reach the host's IMDS.
- Detect any remaining IMDSv1 usage before enforcing, so you do not break a working workload.

### 5.7 Assumptions and limitations

- Detection time, key-age distribution and estate size are invented; the duration rules are verified.
- The provider chain's exact order and members vary slightly between SDKs and versions — check your SDK's documentation.
- Short sessions do not reduce blast radius; that is L04's job. You need both.

---

## 6. Worked example — the key that was rotated every 90 days

**The situation.** A team met an audit requirement by rotating IAM user access keys every 90 days, on a calendar reminder.
The keys were used by a data pipeline running on EC2.

**What happened.**

1. A key was committed to a private repository, which was later made public during a migration.
2. It was used within minutes. The 90-day rotation was **irrelevant**: the key was 31 days old, and the leak was detected
   after 72 hours (§7.1 — identical exposure to a never-rotated key).
3. The EC2 instances already had an instance role with the same permissions. The key existed because the original
   developer had configured `~/.aws/credentials` on the host and the pipeline had worked, so nobody looked further
   (§7.3, row 4).
4. IMDSv1 was enabled, so the same permissions were reachable through an SSRF in a separate internal tool (§7.5) — a
   second path that had never been noticed.
5. Remediation took one afternoon: delete the file, delete the key, enforce IMDSv2. The role was already there.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Long-lived key where a role existed | Delete the credentials file; rely on the instance role |
| 2 | Rotation treated as the control | Sessions, not rotation (§7.1) |
| 3 | Chain precedence hid the role | `aws sts get-caller-identity` in the pipeline's startup logs |
| 4 | IMDSv1 enabled | `HttpTokens: required`, hop limit 1 (§5.6) |
| 5 | No alarm on key usage | Alert on IAM-user credential use where a role is expected (L16) |

**The general rule.** **If a role could do this job, the access key is not a credential — it is an unclosed incident.**

---

## 7. Practical activity

**File:** [`labs/m11/l05_sts_temporary_credentials.py`](../../labs/m11/l05_sts_temporary_credentials.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l05_sts_temporary_credentials.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1105)`; run twice, output
identical.

```text

============================================================================
1. HOW LONG IS A LEAKED CREDENTIAL USEFUL?
============================================================================
  a credential leaks; it takes 72 h to notice and revoke [ILLUSTRATIVE]

  credential                                    validity   usable window
  IAM user access key (never rotated)      until revoked         72.00 h
  IAM user access key (90-day rotation)          2,160 h         72.00 h
  role session, 12 h maximum                        12 h         12.00 h
  role session, 1 h default                          1 h          1.00 h
  role session, 15 min minimum                    0.25 h          0.25 h

  The 15-minute session is useful for 0.35% of the detection window; the
  never-rotated key, 100%. Note that 90-day rotation changes NOTHING here: the
  leak is found in 72 h, long inside the rotation period. Rotation only bounds
  the case where you never notice at all. SESSIONS shorten the window by
  orders of magnitude, and they do it without anyone remembering to act.
  This is the whole argument for roles over users (M11-L04).

============================================================================
2. WILL STS ACCEPT THIS SESSION DURATION?
============================================================================
    requested   role max   chained?   verdict
      3,600 s    3,600 s         no   OK: accepted
        900 s    3,600 s         no   OK: accepted
        600 s    3,600 s         no   REJECTED: below the 900 s (15 min) minimum
     43,200 s   43,200 s         no   OK: accepted
     43,200 s    3,600 s         no   REJECTED: above this role's maximum session duration (3,600 s)
     50,000 s   43,200 s         no   REJECTED: above the 43200 s (12 h) API maximum
      3,600 s   43,200 s        yes   OK: accepted
      7,200 s   43,200 s        yes   REJECTED: role chaining caps the session at 1 hour

  Two rules people meet the hard way: the role's own maximum (1-12 h, set by
  an administrator) overrides what you ask for, and ROLE CHAINING -- assuming
  a role from a role -- caps the session at one hour regardless.

============================================================================
3. WHICH CREDENTIALS DID THE SDK ACTUALLY USE?
============================================================================
  provider chain order: explicit code / CLI flags > environment variables > assumed role in config profile > shared credentials file > container credentials > instance metadata

  environment                           wins                              surprise?
  laptop, profile configured            shared credentials file           
  laptop, stale AWS_ACCESS_KEY_ID       environment variables             YES
  EC2 instance with a role              instance metadata (IMDS)          
  EC2 + leftover ~/.aws/credentials     shared credentials file           YES
  ECS task with a task role             container credentials (ECS/EKS)   
  CI job, OIDC-assumed role             assumed role in config profile    

  Rows 2 and 4 are the classic bug: the role you attached is ignored because
  an older credential sits higher in the chain. The symptom is 'access denied
  for a permission the role clearly has', and the fix is to delete the
  leftover, not to widen the policy (M11-L04).

============================================================================
4. ACCESS-KEY AGE ACROSS AN ESTATE
============================================================================
  240 access keys in a fictional estate [ILLUSTRATIVE distribution]

  age                      keys    share   key-days of exposure
  under 30 days              15       6%                    243
  30-90 days                 25      10%                  1,553
  90 days - 1 year          109      45%                 23,648
  1-2 years                  77      32%                 38,612
  over 2 years               14       6%                 11,666

  total key-days of exposure: 75,722
  keys older than a year: 91 (38%), contributing 66% of the exposure
  Every one of these is a credential with no expiry that someone must remember
  to rotate. The fix is not a better rotation reminder; it is not having them
  (sections 1 and 3).

============================================================================
5. CAN AN SSRF STEAL THE INSTANCE'S CREDENTIALS?
============================================================================
  step                                                         IMDSv1   IMDSv2
  attacker gets the app to fetch a URL it chose                   yes      yes
  GET http://169.254.169.254/latest/meta-data/ works              yes       no
  a PUT is needed first to obtain a session token                  no      yes
  the attacker's forged request can send a PUT                     no       no
  a response hop limit can block containerised callers             no      yes

  IMDSv1: a plain GET from a server-side request fetches the role's credentials.
  IMDSv2: the token PUT breaks the typical SSRF chain, and the configurable
  response hop limit (set it to 1) stops a container reaching the host's IMDS.
  Require IMDSv2 (and set the hop limit to 1 where you can). An SSRF that
  reaches instance credentials converts a web bug into an AWS credential
  compromise with the full reach of the instance role (M9-L12, M10-L10).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every window, verdict, chain resolution, age figure and step result
  above is computed by this script.

  VERIFIED 2026-09-17: the STS duration rules in section 2 follow the AWS STS
  API reference for AssumeRole (900 s minimum, 43200 s maximum, role maximum
  of 1-12 hours, role chaining capped at 1 hour).

  ILLUSTRATIVE: the detection time, key-age distribution and estate size are
  invented. The provider chain is shown in its usual order; consult your SDK's
  documentation for the exact list.

  NOT SHOWN: IAM Identity Center sign-in, OIDC federation setup, and
  credential_process (M11-L18).

Done.
```

### 7.3 Reading the result

**Section 1, rows 1 and 2** make the point that rotation is not the control people think it is.

**Section 2's last row** is the rule that breaks CI pipelines: chained assumption, one hour, no exceptions.

**Section 3's rows 2 and 4** explain most "but the role has that permission!" tickets.

**Section 5** is why `HttpTokens: required` belongs in every launch template you own.

---

## 8. Common mistakes and troubleshooting

1. **Treating rotation as equivalent to expiry.** §7.1.
2. **Copying only the key id and secret, omitting the session token.** Signature errors follow.
3. **Requesting 12 hours on a chained role.** §7.2 — capped at one.
4. **Debugging permissions before checking identity.** Run `aws sts get-caller-identity` first.
5. **Leaving `~/.aws/credentials` on instances that have roles.** §7.3.
6. **Generic session names.** CloudTrail attribution becomes guesswork (M10-L13).
7. **IMDSv1 left enabled.** §7.5.
8. **Long-lived keys in CI.** Use OIDC federation (L18).

| Symptom | Likely cause | Fix |
|---|---|---|
| Access denied despite a correct policy | Wrong principal — another credential won the chain | `aws sts get-caller-identity`; remove the stale source |
| Signature does not match | Session token missing | Send all three fields |
| `AssumeRole` fails with a duration error | Role maximum, or role chaining | Reduce to ≤ the role max; ≤ 1 h when chained (§5.2) |
| Credentials expire mid-job | Fixed session, long job | Configure the role in a profile so the SDK refreshes |
| SSRF reached AWS credentials | IMDSv1 enabled | `HttpTokens: required`, hop limit 1 (§5.6) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Lifetime and blast radius are orthogonal controls; this lesson covers lifetime, L04 covers reach.
- **Privacy.** Meaningful session names are what make an audit record attribute an action to a person (M10-L13).
- **Reliability.** Credentials expiring mid-job is a routine outage; solve it with automatic refresh, not longer sessions.
- **Cost.** Stolen credentials cost money from the first minute; short sessions cap the damage as well as the access
  (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why does 90-day rotation not help in §7.1?
2. What is the minimum and maximum `DurationSeconds` for `AssumeRole`?
3. What is the role-chaining cap?
4. In §7.3, why does the instance role lose on row 4?
5. Which IMDSv2 requirement breaks a typical SSRF?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change `DETECT_H` to 2 hours and re-read section 1's argument.
2. Add two more cases to the duration validator, including a chained 900-second request.
3. Add an environment to §7.3 where the credential chain finds nothing, and say what the error would look like.
4. Compute the key-days of exposure for your own estate's key ages.
5. Write the `~/.aws/config` profile that assumes a role with a source profile and a session name.

### Exercise 3 — Challenge (~60 min)

1. Write a script that lists access keys by age and flags those a role could replace.
2. Design the OIDC federation for your CI system so no long-lived key exists (L18).
3. Write the detection query for "IAM user credentials used where a role was expected" (L16).
4. Plan an IMDSv2 enforcement rollout: detect v1 usage, fix callers, enforce, verify.
5. Build a test that fails CI if any committed file matches an AWS access-key pattern.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l05).)*

**Q1.** What does a temporary credential consist of?

- A. An access key id and a secret access key
- B. An access key id, a secret access key and a session token
- C. A signed request and an expiry timestamp
- D. A bearer token issued by the identity provider

**Q2.** In §7.1, why did 90-day rotation give the same exposure as no rotation?

- A. The key was replaced before the leak occurred
- B. Rotation applies only to console passwords
- C. The leak was detected in 72 hours, far inside the rotation period
- D. Rotation does not invalidate the previous key

**Q3.** What is the minimum session duration `AssumeRole` accepts?

- A. 60 seconds
- B. 300 seconds
- C. 3,600 seconds
- D. 900 seconds

**Q4.** What is the maximum session duration when role chaining?

- A. One hour
- B. Twelve hours
- C. The role's configured maximum
- D. Fifteen minutes

**Q5.** An EC2 instance has a role and a leftover `~/.aws/credentials`. Which wins?

- A. The instance role, because IMDS is authoritative
- B. Whichever was configured most recently
- C. Neither — the SDK raises an ambiguity error
- D. The credentials file, because it sits higher in the chain

**Q6.** What is the first command to run when debugging an unexpected access denial?

- A. `aws iam simulate-principal-policy`
- B. `aws sts get-caller-identity`
- C. `aws configure list-profiles`
- D. `aws cloudtrail lookup-events`

**Q7.** How should a CI/CD pipeline obtain AWS credentials?

- A. A dedicated IAM user with keys stored as CI secrets
- B. The account's root access keys, scoped by an SCP
- C. OIDC federation, exchanging the pipeline's token for a role session
- D. A shared credentials file baked into the runner image

**Q8.** In §7.4, what share of exposure came from keys older than a year?

- A. 38%
- B. 66%
- C. 45%
- D. 6%

**Q9.** Which IMDSv2 mechanism breaks a typical SSRF chain?

- A. TLS is required for all metadata requests
- B. Credentials are encrypted with a per-instance key
- C. The metadata address is randomised per instance
- D. A `PUT` is required first to obtain a session token

**Q10.** What does a response hop limit of 1 prevent?

- A. Containers on a bridge network reaching the host's IMDS
- B. Credentials being cached by the SDK
- C. Metadata requests from outside the VPC
- D. Role sessions being chained more than once

**Q11.** Why should role sessions have meaningful names?

- A. The name is used to scope the session's permissions
- B. Session names must be unique within the account
- C. The name appears in CloudTrail and enables attribution
- D. Names shorter than 16 characters are rejected

**Q12.** Short-lived credentials reduce —

- A. the window in which a leaked credential is usable
- B. the actions a compromised principal can perform
- C. the number of policies that must be evaluated
- D. the cost of API calls made by the session

**Q13.** *(Written, rubric-graded.)* In under 150 words: an audit finds 40 IAM users with access keys, most over a year
old. The proposed remediation is a 60-day rotation policy. Explain what you would propose instead and why.

---

## 12. Revision notes

- **Exposure window**: never-rotated key **72 h**; 90-day rotation **72 h** (no help); 12 h session **12 h**; 1 h session
  **1 h**; 15 min session **0.25 h** = **0.35%** of the window.
- **STS durations**: **900 s** min, **43,200 s** max, role maximum **1–12 h**, default **3,600 s**, **role chaining
  capped at 1 hour**.
- **Provider chain**: explicit → env → profile/assumed role → credentials file → container → IMDS. A stale source higher
  in the chain beats the role you attached.
- **`aws sts get-caller-identity` first**, always.
- **Key estate**: **38%** of keys over a year old carried **66%** of **75,722 key-days** of exposure.
- **IMDSv2**: require it (`HttpTokens: required`) and set the hop limit to **1**; it breaks the SSRF-to-credentials chain.

---

## 13. Completion checklist

- [ ] Applications and pipelines use roles or federation; no long-lived keys without a documented exception.
- [ ] I can predict whether STS will accept a given session duration.
- [ ] I debug identity before policy, with `get-caller-identity`.
- [ ] No stale credential files exist on hosts that have roles.
- [ ] IMDSv2 is required, with a hop limit of 1.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS STS API Reference — `AssumeRole`: `DurationSeconds` 900–43,200 s, role maximum 1–12 h, default 3,600 s, role
  chaining capped at one hour — <https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html>
  `[VERIFIED 2026-09-17]`
- EC2 Instance Metadata Service v2 — token requirement and `HttpPutResponseHopLimit` `[STABLE]`
- AWS SDK and CLI credential provider chain — order varies slightly by SDK; check yours `[STABLE]`
- M11-L04 (what the credential reaches) and M11-L16 (detecting credential misuse) `[STABLE]`
- M9-L12 (SSRF and trust boundaries) and M10-L10 (threat model) `[STABLE]`

---

## 15. Next lesson

→ [M11-L06 — Billing, Budgets, Cost Allocation — and why alerts are not caps](M11-L06-billing-budgets-cost-allocation.md)
covers the control that most often surprises teams building AI systems: spend responds to bugs as readily as to demand,
and an alert is not a brake.
