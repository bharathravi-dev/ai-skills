# M11-L04 — IAM: Identities, Policies, Roles and Least Privilege

| | |
|---|---|
| **Lesson ID** | M11-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M11-L03](M11-L03-account-root-mfa.md), [M10-L07](../module-10-governance-security/M10-L07-access-control-tenant-isolation.md) |

---

## 1. Learning objectives

1. **Apply** AWS's evaluation rules in order: deny by default, explicit deny wins, then the combination rules.
2. **Distinguish** union (identity + resource policy) from intersection (permissions boundary, SCP).
3. **Expand** a wildcard against the real action list instead of judging it by eye.
4. **Measure** least privilege as a ratio of granted to used actions, and shrink it iteratively.
5. **Write** a cross-account trust policy that is not vulnerable to the confused-deputy problem.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Principal** | The entity making a request: an IAM user, a role session, a service, or the root user. |
| **Identity-based policy** | A policy attached to a user, group or role. |
| **Resource-based policy** | A policy attached to a resource (bucket policy, queue policy, role trust policy). |
| **Role** | An identity with permissions that principals *assume* to get temporary credentials. |
| **Trust policy** | A role's resource-based policy: who is allowed to assume it. |
| **Permissions boundary** | A policy that caps the maximum permissions an identity policy can grant. |
| **SCP / RCP** | Organizations policies that cap permissions for accounts (SCP) or access to resources (RCP). |
| **Implicit deny** | The default: no matching Allow means denied. |
| **Explicit deny** | A matching `Deny` statement; it cannot be overridden by any Allow. |
| **`iam:PassRole`** | The permission to hand a role to a service — the action that turns a narrow role into a broad one. |
| **Confused deputy** | A trusted intermediary tricked into using its access on someone else's behalf. |

---

## 3. Plain-language explanation

### 3.1 Nothing is allowed until something allows it

§7.1 runs eight requests through a working evaluator. Requests with no matching Allow are denied — "deny by default". The
row to internalise is the fourth: a policy that allows `s3:*` **and** denies `s3:DeleteObject` denies the delete. An
explicit deny cannot be outvoted by any number of allows.

### 3.2 Three combination rules, and they are not the same

§7.2 runs one set of probes through five configurations:

- **Identity + resource policy is a union.** Either can grant it. The read-only identity plus the bucket policy allows
  both reads.
- **Identity + permissions boundary is an intersection.** An `Action: *` administrator plus a read-only boundary can read
  and cannot delete or create users — **without editing the administrator's policy**.
- **Identity + SCP is an intersection.** The same administrator under an SCP that denies `iam:*` can still delete objects
  but cannot create a user.

### 3.3 Wildcards do not mean what they look like

§7.3 expands five grants against a 12-action catalogue where **6 actions** can change access or destroy data.
`s3:Get*` matches **3 actions, 0 dangerous** — genuinely careful. `s3:*Object` *looks* narrower than `s3:*` and still
matches **4 actions including DeleteObject**. `s3:*Bucket*` matches **6, of which 4 are dangerous**, including
`PutBucketPolicy` — the permission to grant yourself everything else.

### 3.4 Least privilege is a ratio you can compute

§7.4: an app runtime role granted roughly **125** actions used **5** — **25×** over-permissioned. A data science role,
**42×**. A deployment role with `Action: *` — roughly **18,000** actions for **5** used: **3,600×**.

### 3.5 A trust policy that trusts too much

§7.5: a trust policy naming a role *name* in **any** account allows all three attempts, including an unrelated account and
the vendor acting for a different customer. Adding an **external ID** condition reduces that to the one legitimate case.

---

## 4. Analogy

**Keys, and the rules for using them.** A key card (identity policy) opens certain doors. Some doors also have their own
list at reception (resource policy) — being on either list gets you in. Your employment contract may cap what you can ever
be given (permissions boundary), so a generous manager still cannot grant you the server-room key. And the building's
landlord can ban a whole category of access for every tenant (SCP), whatever the tenants' own lists say. A "no entry" sign
beats every list.

### Where the analogy breaks

- **Doors are visible; `s3:*` is 40 doors you never enumerated** (§5.4). The wildcard is the hard part of IAM, not the
  concept.
- **A key card cannot mint new key cards; `iam:PassRole` and `iam:*` can** (§5.6). Some permissions are permissions to
  grant permissions, and they need separate treatment.

---

## 5. Detailed technical explanation

### 5.1 The evaluation rules

`[VERIFIED 2026-09-17 — AWS IAM User Guide, "Policy evaluation logic"]`

1. **Deny by default.** A request with no applicable Allow is denied.
2. **An explicit `Deny` in any policy overrides every Allow.**
3. **Identity-based and resource-based policies in the same account combine as a union**: an Allow in either is sufficient,
   and an explicit Deny in either overrides.
4. **Identity policy and permissions boundary combine as an intersection**: the effective permissions are the overlap; an
   explicit Deny in either overrides.
5. **Identity policy, SCPs and RCPs combine as an intersection**: for a resource without a resource-based policy, the
   action must be allowed by all of them; an explicit Deny in any overrides.

The lab's `authorize()` is a direct implementation. Read it — a hundred lines of Python is a faster route to intuition
than a flow chart.

**Cross-account** access is the exception worth remembering: the trusting account's resource policy (or role trust policy)
**and** the calling principal's identity policy must both allow it.

### 5.2 Users, roles, and which to use

| Use | Identity | Why |
|---|---|---|
| A person | Federated identity (IAM Identity Center) assuming roles | Short-lived credentials, central lifecycle, MFA (L05) |
| An application on EC2/ECS/Lambda | An IAM **role** attached to the compute | Credentials are delivered and rotated automatically; nothing to leak |
| A CI/CD pipeline | A role assumed via OIDC federation | No long-lived keys in the pipeline (L18) |
| A partner or vendor | A role with a trust policy and an external ID | §5.7 |
| Anything at all | **Not** an IAM user with long-lived access keys | Long-lived keys are the credential most often found in repositories |

The design rule: **roles, not users; short sessions, not stored keys**. An IAM user with access keys should be a
documented exception with a rotation owner.

### 5.3 Policy structure

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "ReadReportsOnly",
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::reports", "arn:aws:s3:::reports/*"],
    "Condition": {"StringEquals": {"aws:PrincipalTag/team": "finance"},
                  "Bool": {"aws:SecureTransport": "true"}}
  }]
}
```

Two details that cause real bugs:

- **Bucket-level and object-level ARNs are different resources.** `ListBucket` acts on `arn:aws:s3:::reports`;
  `GetObject` acts on `arn:aws:s3:::reports/*`. Omitting one breaks listing or reading, confusingly.
- **Conditions are where tenancy lives.** `aws:PrincipalTag`, `aws:ResourceTag`, `aws:SourceVpce`, `aws:SecureTransport`,
  `s3:prefix` — these turn a coarse policy into a per-tenant one (M10-L07).

### 5.4 Reading wildcards

`[REAL, computed]` §7.3 — 12 / 3 / 4 / 6 / 1 / 3 actions matched; 6 / 0 / 1 / 4 / 0 / 0 dangerous.

The method: **expand the pattern against the service's actual action list** and look at what comes back. Pay particular
attention to actions that grant *access* rather than use it:

| Action pattern | Why it is worse than it looks |
|---|---|
| `s3:PutBucketPolicy`, `s3:PutBucketAcl`, `s3:PutObjectAcl` | Grants the ability to grant — including to the public |
| `iam:*`, `iam:PutRolePolicy`, `iam:AttachRolePolicy` | Privilege escalation to administrator |
| `iam:PassRole` with `Resource: *` | Hand any role to any service: escalation by proxy (§5.6) |
| `kms:*` | Decrypt everything, or make data permanently unreadable (L17) |
| `logs:DeleteLogGroup`, `cloudtrail:StopLogging` | Destroy the evidence (L16, M10-L13) |

### 5.5 Measuring least privilege

`[REAL, computed — ILLUSTRATIVE action counts]` §7.4 — 25× / 42× / 3,600×.

The workflow that actually converges:

1. Start broad enough to work in a **non-production** account.
2. Run the real workload for a period; collect the actions actually used (CloudTrail — L16).
3. **Generate** the next policy version from that usage (IAM Access Analyzer offers policy generation from CloudTrail).
4. Review the diff, apply in staging, watch for denials.
5. Repeat. Report the ratio as a metric, not as a claim.

Also use **Access Analyzer findings** to detect resources shared outside the account or organisation — the same tool,
answering "who outside can reach this?".

### 5.6 The permissions that grant permissions

`iam:PassRole` deserves its own paragraph. A deployment role that can pass **any** role to a service can pass the
administrator role to a Lambda it creates, and then run as an administrator. The fix is a resource constraint and a
condition:

```json
{"Effect": "Allow", "Action": "iam:PassRole",
 "Resource": "arn:aws:iam::123456789012:role/app-runtime-*",
 "Condition": {"StringEquals": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}}}
```

The same logic applies to `iam:CreateRole` / `AttachRolePolicy` (bound by a **permissions boundary** condition, so newly
created roles cannot exceed it), and to `lambda:UpdateFunctionCode` on a function whose role is powerful.

### 5.7 Trust policies and the confused deputy

`[REAL, computed]` §7.5 — weak trust allows 3 of 3 attempts; with an external ID, 1 of 3.

A role's trust policy answers "who may assume me". Get three things right:

- **Name the account, not just a role name.** `arn:aws:iam::999:role/VendorAccess`, not a wildcard account.
- **Require an external ID** for third parties: a value you generate, unique per customer, that the vendor must supply.
  This stops the vendor being tricked into using its access to your account on another customer's behalf.
- **Add conditions** where possible: source account, source ARN, source VPC endpoint, MFA present
  (`aws:MultiFactorAuthPresent`).

This is the same control MCP calls out for OAuth clients (M9-L11) and the same class of failure as the confused deputy in
M10-L10.

### 5.8 Assumptions and limitations

- The lab's evaluator is a faithful implementation of the documented ordering, but **simplified**: no condition-key
  evaluation, no session policies, no RCPs, no service-specific exceptions.
- Action-count expansions in §7.4 are approximations for illustrating the ratio.
- Real IAM behaviour varies per service (some services do not support resource policies; some support ABAC differently).
  Check the service's own documentation.

---

## 6. Worked example — the read-only role that could delete the bucket

**The situation.** An analytics team asked for read access to a data bucket. The policy granted `s3:*Bucket*` and
`s3:Get*` on the analytics buckets, reviewed and approved as "read-mostly".

**What happened.**

1. `s3:*Bucket*` expanded to include `s3:DeleteBucket`, `s3:PutBucketPolicy`, `s3:PutBucketAcl` and
   `s3:PutBucketVersioning` (§7.3 — 4 of 6 dangerous actions).
2. A cleanup script ran `DeleteBucket` against an empty-looking bucket that held a month of lifecycle-transitioned
   objects.
3. Versioning had been turned **off** by an earlier script using the same permission, so there was nothing to restore
   (M10-L14 §5.4 — a one-way door).
4. The bucket policy could also have been rewritten to grant public access; nobody had checked whether it had.
5. The review had read the policy **by eye**. Nobody had expanded the wildcard.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Wildcard judged visually | Expand against the action list; automate it in review (§5.4) |
| 2 | Access-granting actions bundled with read | Separate `Put*Policy`/`Put*Acl` into an explicit deny |
| 3 | Versioning could be disabled by the same role | Deny `s3:PutBucketVersioning` at the SCP level |
| 4 | No measurement of granted vs used | Generate the policy from 30 days of CloudTrail (§5.5) |
| 5 | No account-level guardrail | SCP denying destructive S3 actions outside a break-glass role |

**The general rule.** **A wildcard is a claim about a list you have not read. Print the list.**

---

## 7. Practical activity

**File:** [`labs/m11/l04_iam_policy_evaluation.py`](../../labs/m11/l04_iam_policy_evaluation.py)

**No AWS account, no network, no third-party dependencies.** The lab *implements* the evaluation rules, so you can test
your own policies against them offline.

```bash
source .venv/bin/activate
python labs/m11/l04_iam_policy_evaluation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. DENY BY DEFAULT, AND EXPLICIT DENY
============================================================================
  action           resource                            verdict   why
  s3:GetObject     arn:aws:s3:::reports/q3.csv           ALLOW   Allow from the identity policy
  s3:PutObject     arn:aws:s3:::reports/q3.csv            deny   no Allow anywhere (deny by default)
  s3:GetObject     arn:aws:s3:::payroll/staff.csv         deny   no Allow anywhere (deny by default)
  s3:DeleteObject  arn:aws:s3:::reports/q3.csv            deny   explicit Deny in the identity policy
  s3:PutObject     arn:aws:s3:::reports/q3.csv           ALLOW   Allow from the identity policy
  s3:GetObject     arn:aws:s3:::public-docs/a.pdf        ALLOW   Allow from the resource policy
  s3:PutObject     arn:aws:s3:::public-docs/a.pdf         deny   no Allow anywhere (deny by default)
  iam:CreateUser   *                                     ALLOW   Allow from the identity policy

  Nothing is permitted unless something permits it, and an explicit Deny
  cannot be outvoted. Row 4 is the pattern to recognise: a policy that allows
  's3:*' and denies one action still denies that action.

============================================================================
2. UNION, INTERSECTION, INTERSECTION
============================================================================
  configuration                           Get reports   Get public       Delete   CreateUser
  identity only                                 ALLOW         deny         deny         deny
  resource policy only (same acct)               deny        ALLOW         deny         deny
  identity + resource policy                    ALLOW        ALLOW         deny         deny
  admin identity + read-only boundary           ALLOW        ALLOW         deny         deny
  admin identity + SCP denying IAM              ALLOW        ALLOW        ALLOW         deny

  identity + resource policy = UNION: either one can grant it.
  identity + permissions boundary = INTERSECTION: the boundary caps an
  administrator down to read-only without editing their policy.
  identity + SCP = INTERSECTION: the SCP's Deny on iam:* wins over 'Action: *'.

============================================================================
3. WHAT DOES A WILDCARD ACTUALLY GRANT?
============================================================================
  action catalogue: 12 actions, of which 6 can change access or destroy data

  grant                                       actions   dangerous   which dangerous ones
  s3:*                                             12           6   DeleteObject, DeleteBucket, PutBucketPol
  s3:Get*                                           3           0   none
  s3:*Object                                        4           1   DeleteObject
  s3:*Bucket*                                       6           4   DeleteBucket, PutBucketPolicy, PutBucket
  s3:GetObject                                      1           0   none
  s3:GetObject|s3:ListBucket|s3:PutObject           3           0   none

  's3:Get*' looks careful and grants no destructive action. 's3:*Object' looks
  narrower than 's3:*' and still grants Delete and PutObjectAcl. Read a
  wildcard by EXPANDING it against the real action list, never by eye.

============================================================================
4. LEAST PRIVILEGE, MEASURED
============================================================================
  role                    granted (approx actions)  used in 30d  over-permission
  app runtime role                             125            5              25x
  data science role                            125            3              42x
  deployment role                           18,000            5           3,600x

  'Least privilege' is not a feeling; it is this ratio. Generate the next
  version of each policy FROM the 30-day usage, review the diff, and repeat
  (AWS calls this access-analyzer policy generation). The deployment role
  shows the other half of the problem: iam:PassRole is one action and it is
  how a narrow role becomes an administrator (M11-L05).

============================================================================
5. A CROSS-ACCOUNT ROLE, AND THE CONFUSED DEPUTY
============================================================================
  who is asking                                    weak trust   with external ID
  the vendor, acting for us                             ALLOW              ALLOW
  the vendor, acting for a DIFFERENT customer           ALLOW               deny
  an unrelated account                                  ALLOW               deny

  The weak trust policy trusts a role NAME in ANY account, and trusts the
  vendor to remember which customer it is acting for. The external ID makes
  the vendor prove it -- which is the whole point of the confused-deputy
  control (M9-L11, M10-L10).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the evaluator implements AWS's documented rules -- deny by default,
  explicit deny wins, identity/resource = union, boundary and SCP = intersection
  -- and every verdict, count and ratio above comes from running it.

  SIMPLIFIED: real IAM has condition keys, session policies, RCPs, service-linked
  roles, ABAC tags and per-service quirks. The action-count expansions in
  section 4 are approximations, not the real catalogue sizes.

  NOT SHOWN: the IAM console, Access Analyzer itself, and the policy language's
  full grammar (M11-L05, M12-L08).

Done.
```

### 7.3 Reading the result

**Section 1, row 4** is the rule that surprises people: `Allow s3:*` plus `Deny s3:DeleteObject` denies the delete.

**Section 2 is three different combination rules in one table.** The boundary row shows an administrator capped to
read-only without their policy changing.

**Section 3, row 3** (`s3:*Object`) is the wildcard that looks careful and is not.

**Section 5's middle row** is the confused deputy: the *right* vendor, acting for the *wrong* customer, allowed by a
trust policy that only checks a name.

---

## 8. Common mistakes and troubleshooting

1. **Judging a wildcard by eye.** §5.4 — expand it.
2. **Assuming a boundary grants.** It only caps; you still need an identity policy that allows (§5.1).
3. **Forgetting bucket-level ARNs for `ListBucket`.** §5.3.
4. **`iam:PassRole` with `Resource: *`.** §5.6 — escalation by proxy.
5. **Trust policies naming a role name in any account.** §5.7.
6. **Long-lived IAM user keys for applications.** Use a role on the compute (§5.2).
7. **Granting `s3:PutBucketPolicy` alongside read access.** It is the permission to grant permissions.
8. **Treating least privilege as a claim.** §5.5 — it is a ratio you can print.
9. **Debugging a denial by adding permissions.** Find *which* policy denied it first — SCP, boundary, resource or identity.

| Symptom | Likely cause | Fix |
|---|---|---|
| Access denied despite an Allow | Explicit Deny, or an SCP/boundary intersection | Check SCPs and boundaries before editing the identity policy |
| `ListBucket` fails but `GetObject` works | Bucket ARN missing from the policy | Add both bucket and object ARNs (§5.3) |
| A narrow role can do administrator things | Unconstrained `iam:PassRole` or `iam:*` | Constrain resources and add `iam:PassedToService` (§5.6) |
| A vendor can reach the wrong customer's data | Trust policy without an external ID | Add a per-customer external ID condition (§5.7) |
| Permissions keep growing | No measurement or review loop | Generate from usage; report the granted/used ratio (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Security.** This is where M10-L07's "enforcement outside the model" becomes concrete: an agent's tool permissions are
  the role's permissions (M9-L13, M12-L08).
- **Privacy.** Conditions on tags and prefixes are how tenant isolation is enforced rather than hoped for (M10-L07).
- **Reliability.** Over-broad permissions cause outages as often as breaches — a script with `s3:*` deletes a bucket.
- **Cost.** Permissions to create expensive resources are a cost control; SCPs restricting instance types and regions are
  a standard guardrail (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why is request 4 in §7.1 denied despite `s3:*` being allowed?
2. What is the difference between a union and an intersection here?
3. How many dangerous actions does `s3:*Object` grant in §7.3?
4. What is the over-permission ratio of the deployment role?
5. What does an external ID prevent?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a policy of your own and test it against the probes.
2. Add a `Condition` field to the evaluator for `aws:SecureTransport` and make one request fail on it.
3. Extend the action catalogue in §7.3 and re-expand the grants.
4. Write the `iam:PassRole` statement for a deployment role that may pass only `app-runtime-*` roles to ECS.
5. Write a trust policy for a vendor, with an external ID and a source-account condition.

### Exercise 3 — Challenge (~60 min)

1. Implement condition-key evaluation in the lab's engine for `StringEquals` and `Bool`.
2. Take a real policy you use and compute its granted/used ratio from a month of usage.
3. Write an SCP for a workload OU: deny leaving the organisation, deny disabling CloudTrail, deny unused regions.
4. Design the permissions-boundary strategy that lets developers create roles safely.
5. Build a test suite of "must be allowed" and "must be denied" requests for one system, and run it in CI.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l04).)*

**Q1.** What happens to a request that matches no policy statement?

- A. It is allowed if the principal is in the same account
- B. It is denied — deny by default
- C. It is referred to the resource policy
- D. It is allowed for read-only actions

**Q2.** A policy allows `s3:*` and denies `s3:DeleteObject`. What happens to a delete?

- A. It is allowed, because the allow is broader
- B. It depends on statement order in the document
- C. It is denied — an explicit deny cannot be overridden
- D. It is allowed if a resource policy also allows it

**Q3.** How do an identity policy and a resource policy combine in the same account?

- A. As an intersection — both must allow
- B. The resource policy takes precedence
- C. The identity policy takes precedence
- D. As a union — an allow in either is sufficient

**Q4.** What does a permissions boundary do?

- A. It grants permissions that identity policies cannot
- B. It caps the maximum an identity policy can grant
- C. It applies only to roles assumed cross-account
- D. It replaces the identity policy during a session

**Q5.** In §7.2, an administrator identity with an SCP denying `iam:*` could still —

- A. read and delete S3 objects
- B. do nothing at all
- C. create IAM users
- D. only read S3 objects

**Q6.** Which wildcard in §7.3 granted destructive actions despite looking narrow?

- A. `s3:Get*`
- B. `s3:GetObject`
- C. `s3:*Object`
- D. None of them

**Q7.** Why is `s3:PutBucketPolicy` more dangerous than `s3:PutObject`?

- A. It applies to every bucket in the account
- B. It bypasses encryption requirements
- C. It cannot be logged by CloudTrail
- D. It is the permission to grant permissions, including publicly

**Q8.** How should least privilege be measured?

- A. By counting the statements in each policy
- B. By the number of roles per account
- C. As a ratio of actions granted to actions actually used
- D. By whether any wildcard appears in the policy

**Q9.** What makes `iam:PassRole` with `Resource: *` dangerous?

- A. It allows the principal to hand any role, including an administrator role, to a service
- B. It permits role creation without a boundary
- C. It exposes role names to unauthenticated callers
- D. It disables the trust policy check

**Q10.** What does an external ID in a trust policy prevent?

- A. Credentials being reused after a session expires
- B. A trusted vendor being tricked into acting for another customer
- C. Role assumption from outside the organisation
- D. Access from accounts without MFA enabled

**Q11.** Cross-account access requires —

- A. an allow in the resource policy only
- B. an allow in the calling principal's identity policy only
- C. an SCP permitting the action in both accounts
- D. an allow on both sides: the trust/resource policy and the caller's identity policy

**Q12.** A `ListBucket` call fails while `GetObject` succeeds. What is the likely cause?

- A. The bucket-level ARN is missing from the policy
- B. The bucket has Block Public Access enabled
- C. `ListBucket` requires a resource policy
- D. The principal lacks `s3:ListAllMyBuckets`

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague's pull request adds a role with
`"Action": "s3:*", "Resource": "*"` and says it will be tightened later. Give your review comment, with what you would ask
for instead.

---

## 12. Revision notes

- **Order**: deny by default → explicit Deny wins → then combine.
- **Union**: identity + resource policy (same account). **Intersection**: identity + boundary; identity + SCP/RCP.
- **Cross-account**: both sides must allow.
- **Wildcards**: `s3:Get*` = 3 actions, 0 dangerous; `s3:*Object` = 4 actions, 1 dangerous; `s3:*Bucket*` = 6 actions,
  **4 dangerous**. Expand, never eyeball.
- **Least privilege is a ratio**: **25× / 42× / 3,600×** in the lab. Generate the next policy from 30 days of usage.
- **Permissions that grant permissions**: `iam:*`, `iam:PassRole`, `s3:Put*Policy`, `s3:Put*Acl`, `kms:*` — constrain them
  by resource and condition.
- **Trust policies**: name the account, require an external ID for third parties, add conditions. Weak trust allowed
  **3/3** attempts; the external ID allowed **1/3**.

---

## 13. Completion checklist

- [ ] I can predict the verdict for a request given identity, resource, boundary and SCP policies.
- [ ] I expand every wildcard against the action list before approving a policy.
- [ ] Applications use roles on the compute, not IAM users with access keys.
- [ ] `iam:PassRole` is constrained by resource and `iam:PassedToService`.
- [ ] Third-party trust policies name the account and require an external ID.
- [ ] I can state the granted/used ratio for at least one of my roles.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS IAM User Guide — *Policy evaluation logic*: deny by default, explicit deny, union with resource policies,
  intersection with boundaries and SCPs/RCPs —
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html> `[VERIFIED 2026-09-17]`
- IAM Access Analyzer — policy generation from CloudTrail; external-access findings `[STABLE]`
- M10-L07 (access control and tenant isolation) and M9-L13 (enforcement outside the model) `[STABLE]`
- M9-L11 (OAuth, confused deputy) and M10-L10 (threat model) — the same failure class `[STABLE]`
- M11-L05 (temporary credentials and STS) and M12-L08 (IAM for AI services) `[STABLE]`

---

## 15. Next lesson

→ [M11-L05 — Temporary Credentials, STS and the CLI](M11-L05-sts-temporary-credentials-cli.md) takes the policies you can
now read and asks how a principal actually obtains credentials, for how long, and why every long-lived access key in your
estate is a finding.
