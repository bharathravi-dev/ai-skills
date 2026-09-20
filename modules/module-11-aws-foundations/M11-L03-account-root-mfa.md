# M11-L03 — Account Setup, Root User Protection and MFA

| | |
|---|---|
| **Lesson ID** | M11-L03 |
| **Difficulty** | 1 (Beginner) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M11-L01](M11-L01-cloud-shared-responsibility.md) |

---

## 1. Learning objectives

1. **Name** the small set of tasks that genuinely require the root user, and stop using it for anything else.
2. **Compare** credentials by blast radius rather than by who holds them.
3. **Quantify** what MFA buys, and why phishing-resistant factors differ from one-time codes.
4. **Use the account boundary** as the strongest isolation available, and say why it beats a policy.
5. **Run a baseline checklist**, because nine of its ten items fail silently.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **AWS account** | The billing and isolation boundary; every resource belongs to exactly one. |
| **Root user** | The identity created with the account, authenticating with the account's email address; it cannot be restricted by IAM policy. |
| **AWS Organizations** | Central management of many accounts, with policies applied across them. |
| **MFA** | Multi-factor authentication — something you know plus something you have. |
| **TOTP** | A time-based one-time code from an app; relayable to an attacker in real time. |
| **Phishing-resistant MFA** | A credential bound to the site's origin (FIDO2 / WebAuthn security keys or passkeys), so a relay attack fails. |
| **Break-glass** | A deliberately restricted, heavily audited path for emergency access. |
| **Blast radius** | What one compromised credential can reach. |

---

## 3. Plain-language explanation

### 3.1 Root has a short, strange job list

§7.1 lists sixteen tasks. **9 require root**, and of those, **3 are rare one-offs** (GovCloud sign-up, Reserved Instance
Marketplace seller registration, MTurk linking) and two are **recovery from your own mistakes** — restoring IAM
permissions an administrator revoked from themselves, and removing an S3 bucket policy or SQS resource policy that denies
every principal.

The seven that do **not** need root are the ones people habitually use it for: creating buckets, deploying, reading the
bill, creating users, investigating incidents, granting contractor access, changing the account name.

### 3.2 Compare credentials by what theft buys

§7.2 scores six principals across eight capabilities. Root reaches **8 of 8** — including closing the account. An admin
role with MFA and a one-hour session reaches **7 of 8**, the same as a long-lived admin user. What the role changes is how
long the reach lasts and how it is obtained, not how far it goes. Reducing reach and reducing the chance of theft are two
separate jobs.

### 3.3 MFA is arithmetic, not hygiene

§7.3, at 40 credible attempts per identity per year: a reused password gives a **55.43%** chance of compromise in a year.
A strong unique password alone, **14.81%**. Adding TOTP takes it to **1.59%** — **9× better**. A phishing-resistant key:
**0.08%** — **185× better** than the password alone.

TOTP and FIDO2 differ on exactly one case, and it is the common one: a one-time code can be relayed to a fake site in real
time; a credential bound to the real origin cannot.

### 3.4 Accounts beat policies

§7.4: a credential compromised in dev reaches **100%** of resources in a single-account layout, **60%** with a separate
production account, and **35%** with one account per environment — and in the last two cases it cannot reach production
data at all.

### 3.5 Nine of ten baseline settings fail silently

§7.5: of ten baseline items, **9 produce no symptom** until the day they matter. Missing root MFA, root access keys left
in place, no billing alerts, CloudTrail off in some regions, account-level public access not blocked. Only one — using
identity federation instead of IAM users — announces itself.

---

## 4. Analogy

**The master key to a building.** It exists, it opens everything, and the correct number of people carrying it around
daily is zero. It lives in a sealed box with a log, and it is used for two things: the annual inspection nobody else can
do, and the day a lock jams and no other key works. Anyone who says "I just used the master, it was quicker" has told you
about a control failure, not a shortcut.

### Where the analogy breaks

- **A master key opens doors one at a time; root can delete everything at once**, from a script, in seconds (§5.2).
- **A building has one master key; an organisation has one per account** — which is why the account count and the
  Organizations structure matter as much as the key discipline (§5.4).

---

## 5. Detailed technical explanation

### 5.1 The root user, precisely

`[VERIFIED 2026-09-16 — AWS IAM User Guide, "Tasks that require root user credentials"]`

Root is the identity created with the account. It cannot be restricted by an IAM policy, which is why it is both the
recovery path and the largest risk. Tasks that require it include:

| Category | Task |
|---|---|
| Account | Change the root email address, root password or root access keys (standalone accounts); close the account (standalone accounts) |
| Recovery | Restore IAM permissions when the only administrator has revoked their own; remove an S3 bucket policy or SQS resource policy that denies **all** principals |
| Billing | Activate IAM access to the Billing and Cost Management console; a few billing tasks and certain tax invoices |
| Rare | Sign up for AWS GovCloud (US); register as a seller in the Reserved Instance Marketplace; link an account to an MTurk Requester account; KMS key recovery via Support |

Notably **not** root tasks: changing the account name, contact information, alternate contacts or enabled Regions.

`[VERIFIED 2026-09-16]` Two current behaviours worth knowing:

- **MFA is enforced for root by default**, but adding it requires customer action during account creation or at sign-in.
- With **AWS Organizations** and centralised root access, you can **remove root credentials from member accounts**
  entirely; new accounts created in the organisation have **no root credentials by default**, and privileged tasks
  (including the deny-all bucket-policy fix) are performed from the management or delegated administrator account.

That last point is the modern answer to root hygiene: not "protect root carefully" but "member accounts do not have one".

### 5.2 Blast radius, not trust

`[REAL, computed]` §7.2 — 8/8 for root down to 3/8 for a least-privilege runtime role.

Two independent questions, often confused:

| Question | Controlled by |
|---|---|
| How likely is this credential to be stolen? | MFA strength, session lifetime, where it is stored, whether it is long-lived (L05) |
| What does it reach if it is? | Permissions, account boundary, resource policies, guardrails (L04) |

An admin role with MFA answers the first well and the second not at all. A least-privilege runtime role answers the second
well. You need both, and they are different pieces of work.

### 5.3 What MFA buys

`[REAL, computed — ILLUSTRATIVE probabilities]` §7.3 — 55.43% / 14.81% / 1.59% / 0.08% per year.

```text
annual = 1 − (1 − p_per_attempt)^attempts
```

Practical guidance:

- **Root**: phishing-resistant MFA, a hardware key, stored physically, with a documented recovery process — and, in an
  Organizations member account, no root credentials at all (§5.1).
- **Humans**: federated sign-in with phishing-resistant MFA, short sessions, no long-lived access keys (L05).
- **Machines**: no MFA — machines get **roles**, not users, and therefore short-lived credentials by construction (L05).

Multiply §7.3 by §7.2: a 14.81% annual compromise chance on a credential with 8/8 reach is a different sentence from the
same number on a read-only role.

### 5.4 The account boundary

`[REAL, computed]` §7.4 — 100% / 60% / 35% reachable.

An AWS account is the strongest isolation AWS offers: cross-account access requires an explicit grant on **both** sides,
and it is not something a single mistaken policy edit can remove. Compare that with separating environments by IAM policy
inside one account, where one over-broad policy or one wildcard resource ARN collapses the boundary.

A common structure:

```text
Organization
├── management account            (billing, Organizations; no workloads)
├── security / log-archive        (CloudTrail destination, immutable)
├── shared services               (CI/CD, artefact registry)
└── workloads
    ├── dev      ├── test      ├── staging      └── prod
```

With **Service Control Policies** (L04) applied at the organisational-unit level as guardrails: deny disabling CloudTrail,
deny leaving the organisation, deny regions you do not use, deny deleting log buckets. SCPs set a **maximum**; they grant
nothing.

### 5.5 The baseline checklist

`[REAL, classified]` §7.5 — 9 of 10 silent.

For every new account:

```text
[ ] root: phishing-resistant MFA registered (or no root credentials, via Organizations)
[ ] root: no access keys exist
[ ] root: email is a monitored distribution list, not an individual
[ ] root: recovery phone and security contact are current and reachable
[ ] humans: federated via IAM Identity Center; no long-lived IAM users
[ ] a second administrator exists who could restore permissions
[ ] CloudTrail enabled in all regions, delivering to a separate log-archive account
[ ] S3 Block Public Access enabled at the account level
[ ] budget and billing alerts configured (L06)
[ ] the account is in the organisation, under the right OU, with SCPs applied
```

Because these fail silently, they belong in **code** (L18) and in a scheduled check, not in a wiki page someone read once.

### 5.6 Break-glass

You still need an emergency path for the lockout case. Design it deliberately:

- A dedicated break-glass role or credential, not root, wherever the task permits.
- Credentials split or stored physically, with a documented, rehearsed retrieval procedure.
- **Alerting on use** — every use is an incident until proven otherwise (M10-L14).
- Rehearsed at least annually. An untested recovery procedure is a belief, not a control.

### 5.7 Assumptions and limitations

- The compromise probabilities, attempt rate and resource shares in the lab are invented; the arithmetic is real.
- Root-task lists and Organizations capabilities change; the list here was verified on 2026-09-16 and should be re-checked.
- Console procedures are deliberately out of scope; this lesson is about which decisions to make.

---

## 6. Worked example — the account that cost £41,000 in a weekend

**The situation.** A team ran a proof of concept in a personal-style AWS account. Root had a password, no MFA, and a pair
of access keys created "for the setup script" two months earlier. The keys ended up in a public repository inside a
notebook.

**What happened.**

1. The keys were found by automated scanners within minutes and used to launch expensive compute across **many regions**
   (§7.2 — root reaches everything, everywhere).
2. CloudTrail was on in one region only, so the early activity in other regions was invisible (§5.5).
3. No budget alert existed; the first signal was the invoice (L06).
4. The credentials could not simply be revoked by an administrator — they were **root** keys, so containment required root
   sign-in, which required the recovery email, which pointed at someone on leave (§5.5).
5. Because dev, test and production shared one account, the containment steps risked the production workload too (§7.4).

| # | What was missing | Fix |
|---|---|---|
| 1 | Root access keys existed at all | Delete them; root never has access keys (§5.5) |
| 2 | No MFA on root | Phishing-resistant MFA, or no root credentials via Organizations (§5.1) |
| 3 | CloudTrail in one region | All regions, delivered to a separate log-archive account (L16) |
| 4 | No budget alert | Budget and anomaly alerts from day one (L06) |
| 5 | Root email was an individual | A monitored distribution list |
| 6 | One account for everything | Per-environment accounts under an organisation (§5.4) |

**The general rule.** **Every item on that list is free, takes minutes, and is invisible until the weekend it is not.**

---

## 7. Practical activity

**File:** [`labs/m11/l03_account_root_mfa.py`](../../labs/m11/l03_account_root_mfa.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic. Nothing here touches a real account — the
lab computes the consequences of the settings so you can reason about them before you configure anything.

```bash
source .venv/bin/activate
python labs/m11/l03_account_root_mfa.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. WHAT ACTUALLY REQUIRES ROOT?
============================================================================
  task                                                       root?   note
  change the account's root email, password or access keys    ROOT   standalone accounts
  close the account                                           ROOT   standalone accounts
  restore IAM permissions an admin revoked from themselves    ROOT   the classic lockout
  remove an S3 bucket policy that denies ALL principals       ROOT   self-inflicted deny
  delete an SQS resource policy that denies ALL principals    ROOT   same pattern
  activate IAM access to the Billing console                  ROOT   one-time setting
  register as a seller in the Reserved Instance Marketplace    ROOT   rare
  sign up for AWS GovCloud (US)                               ROOT   rare
  link an AWS account to an MTurk Requester account           ROOT   rare
  create an S3 bucket                                           no   any permitted IAM principal
  deploy the application                                        no   a deployment role
  read the bill                                                 no   after the one-time activation above
  create IAM users and roles                                    no   an admin principal
  investigate an incident                                       no   a break-glass role, not root
  give a contractor temporary access                            no   a role with a short session
  change the account name or contact details                    no   not root, despite the name

  require root: 9/16   do not: 7/16
  Of the 9 that do, 3 are rare one-offs and two are recovery from
  mistakes you hope never to make. Root is a fire extinguisher: essential,
  and not a tool you use to cook with.

============================================================================
2. BLAST RADIUS BY CREDENTIAL
============================================================================
  principal                             read data  write dat  create in  change IA  disable l  close acc  spend wit  reach pro   reach
  root user                                   yes        yes        yes        yes        yes        yes        yes        yes   8/8  
  IAM user with AdministratorAccess           yes        yes        yes        yes        yes          -        yes        yes   7/8  
  admin role, MFA + 1h session                yes        yes        yes        yes        yes          -        yes        yes   7/8  
  deployment role (prod)                      yes        yes        yes          -          -          -        yes        yes   5/8  
  read-only analyst role                      yes          -          -          -          -          -          -        yes   2/8  
  app runtime role (least priv)               yes        yes          -          -          -          -          -        yes   3/8  

  The rows differ by what a stolen credential BUYS an attacker, not by who
  you trust. 'admin role, MFA + 1h session' has the same reach as the admin
  user -- what it changes is how long the reach lasts and how it is obtained.
  Reducing reach is a separate job from reducing the chance of theft (M11-L04).

============================================================================
3. MFA IS ARITHMETIC
============================================================================
  40 credible attempts per identity per year [ILLUSTRATIVE]

  authentication design                       per attempt   per year      1 in
  password only, reused elsewhere                 0.02000     55.43%         2
  strong unique password, no MFA                  0.00400     14.81%         7
  password + TOTP app                             0.00040      1.59%        63
  password + phishing-resistant (FIDO2)           0.00002      0.08%     1,250

  adding TOTP cuts the annual figure 9x; phishing-resistant keys cut it 185x.
  The difference between TOTP and FIDO2 is the phishing case: a one-time code
  can be relayed to a fake site in real time, a bound credential cannot.
  Now multiply by the row for 'root user' in section 2 (M11-L05).

============================================================================
4. ONE ACCOUNT OR FOUR?
============================================================================
  a credential is compromised in the DEV environment

  account layout                       reachable resources    prod data reachable?
  one account for everything                          100%                     YES
  separate prod account                                60%                      no
  one account per environment                          35%                      no

  the same mistake costs 2.9x less with per-environment accounts, and
  cannot reach customer records, model access, production keys at all.
  Accounts are the strongest isolation boundary AWS offers -- stronger than
  any IAM policy, because it is not a policy anyone can edit by accident
  (M10-L07). Use AWS Organizations to manage them centrally.

============================================================================
5. WHICH BASELINE SETTINGS FAIL SILENTLY?
============================================================================
  baseline setting                              fails loudly?   otherwise you find out...
  MFA on the root user                                     NO   only by checking, or after a breach
  no root access keys                                      NO   only by checking
  root email is a monitored group                          NO   when the person leaves
  billing alerts configured                                NO   when the bill arrives (M11-L06)
  CloudTrail enabled in all regions                        NO   when you need the logs and they are absent
  S3 Block Public Access at account level                  NO   when a bucket leaks
  IAM Identity Center instead of IAM users                yes   people notice they cannot log in
  password policy and session duration                     NO   only by checking
  contact and security-contact details current             NO   when AWS cannot reach you in an incident
  a second admin who can restore permissions               NO   during the lockout itself

  silent if missing: 9/10
  Nine of ten produce no symptom at all until the day they matter. That is
  what makes them a CHECKLIST rather than a habit: run it on every new
  account, and re-run it on a schedule (M10-L15, M11-L18).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count, blast-radius figure, annual probability and ratio above
  is computed from the values in this script.

  VERIFIED 2026-09-16: the root-only task list in section 1 follows the AWS IAM
  User Guide, 'Tasks that require root user credentials'.

  ILLUSTRATIVE: the per-attempt compromise probabilities, attempt rate and
  resource shares are invented to make the arithmetic visible.

  NOT SHOWN: the console steps themselves, AWS Organizations SCPs (M11-L04),
  and identity federation (M11-L05).

Done.
```

### 7.3 Reading the result

**Section 1's bottom seven rows** are the tasks people actually sign in as root to do. None of them needs it.

**Section 2's third row** is the important subtlety: a short-lived admin role has the same *reach* as an admin user. MFA
and session limits reduce the chance of theft, not the consequences.

**Section 3's last two rows** are the argument for hardware keys on anything privileged: 1.59% versus 0.08%.

**Section 5 is why this is a checklist.** Nine of ten items give you no feedback at all until they matter.

---

## 8. Common mistakes and troubleshooting

1. **Using root for daily work.** §7.1 — 7 of 16 common tasks need a role, not root.
2. **Root access keys.** §6 — there is no legitimate reason for them to exist.
3. **Root email owned by an individual.** Use a monitored distribution list.
4. **No second administrator.** The lockout case is one of the few genuine root tasks (§5.1).
5. **Treating MFA as a checkbox.** §5.3 — TOTP and phishing-resistant factors differ by 20× in the lab.
6. **Long-lived IAM users for humans.** Federate instead (L05).
7. **One account for every environment.** §5.4 — the account is the strongest boundary you have.
8. **CloudTrail in one region.** Attackers use the regions you do not watch.
9. **An untested break-glass procedure.** §5.6 — rehearse it.

| Symptom | Likely cause | Fix |
|---|---|---|
| Nobody can log in as administrator | Admin revoked their own permissions | Root recovery — one of the few real root tasks (§5.1) |
| A bucket policy locked everyone out | Deny-all resource policy | Root, or the Organizations privileged task (§5.1) |
| Unexpected activity in an unused region | CloudTrail not global | Enable in all regions, deliver to log archive (L16) |
| Surprise bill | No budget alert | Budgets and anomaly detection (L06) |
| A dev mistake reached production | Single-account layout | Per-environment accounts with SCPs (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Security.** This lesson is the account-level half of M10-L07; the application half is L04 and L10.
- **Privacy.** Account separation is also a data boundary: production data stays in the production account (M10-L06).
- **Reliability.** The lockout scenarios in §5.1 are availability incidents; the second administrator and the rehearsed
  break-glass path are the controls (M10-L14).
- **Cost.** Stolen credentials cost money immediately and continuously; budget alerts are a security control as much as a
  finance one (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List the root-only tasks from §7.1 that are recoveries from your own mistakes.
2. Which four tasks in §7.1 do people commonly use root for that do not need it?
3. What is the annual compromise probability for a strong password with no MFA in §7.3?
4. How much does a phishing-resistant factor improve on that?
5. Why does an admin role with MFA have the same blast radius as an admin user?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change `ATTEMPTS` to 400 and re-read the table; which designs still hold up?
2. Add a "contractor role, 15-minute session" row to §7.2 with its capabilities.
3. Add three baseline items your organisation requires and classify them silent or loud.
4. Draw your current account layout and mark where a dev compromise would stop.
5. Write the break-glass procedure for your account, including who is alerted on use.

### Exercise 3 — Challenge (~60 min)

1. Write the baseline checklist as a script that reports pass/fail per item (as a dry-run design, no account needed).
2. Design the organisation structure for a team of ten with dev, staging and production, and list the SCPs.
3. Write the runbook for "the only administrator has locked themselves out".
4. Rehearse the break-glass retrieval end to end, and record how long it took.
5. Propose the migration path from IAM users to federated access for an existing account.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l03).)*

**Q1.** Which of these genuinely requires the root user?

- A. Creating IAM users and roles
- B. Restoring IAM permissions an administrator revoked from themselves
- C. Changing the account name and contact details
- D. Reading the monthly bill

**Q2.** In §7.1, how many of the sixteen listed tasks required root?

- A. Sixteen
- B. Four
- C. Nine
- D. Seven

**Q3.** Why can root not be restricted by an IAM policy?

- A. IAM policies apply only to federated identities
- B. Root operates outside the region where policies are evaluated
- C. Root policies are managed by AWS Organizations instead
- D. It is the account's own identity, and the recovery path of last resort

**Q4.** What does an admin role with MFA and a one-hour session change, compared with an admin IAM user?

- A. How likely theft is, and how long the credential lasts
- B. The permissions granted to the principal
- C. The reach of the credential if stolen
- D. Which resources the account can create

**Q5.** In §7.3, what annual compromise probability did a strong unique password with no MFA produce?

- A. 55.43%
- B. 1.59%
- C. 0.08%
- D. 14.81%

**Q6.** What does phishing-resistant MFA prevent that TOTP does not?

- A. Brute-force attacks against the password
- B. Real-time relay of the second factor to a fake site
- C. Credential reuse across unrelated services
- D. Session hijacking after successful sign-in

**Q7.** Why is an AWS account a stronger boundary than an IAM policy?

- A. Accounts are physically isolated in separate data centres
- B. IAM policies are evaluated only at sign-in
- C. Cross-account access needs explicit grants on both sides, and no single policy edit removes it
- D. Accounts have separate CloudTrail trails by default

**Q8.** In §7.4, what share of resources did a dev compromise reach under one account per environment?

- A. 100%
- B. 60%
- C. 40%
- D. 35%

**Q9.** What do Service Control Policies do?

- A. They set a maximum on what accounts in scope may do
- B. They grant permissions to organisational units
- C. They replace IAM roles for cross-account access
- D. They apply MFA requirements to federated users

**Q10.** Why are the baseline items called a checklist rather than a habit?

- A. Nine of ten produce no symptom until the day they matter
- B. They must be certified annually by an auditor
- C. They change too frequently to memorise
- D. They apply only to newly created accounts

**Q11.** What should happen when the break-glass credential is used?

- A. It should be rotated at the next scheduled maintenance window
- B. The session should be limited to read-only actions
- C. It should trigger an alert and be treated as an incident until proven otherwise
- D. The usage should be recorded in the following month's review

**Q12.** What is the modern answer to protecting root in a member account?

- A. Rotate the root password on a fixed schedule
- B. Use Organizations so the member account has no root credentials at all
- C. Store root access keys in a secrets manager
- D. Restrict root with a permissions boundary

**Q13.** *(Written, rubric-graded.)* In under 150 words: you have inherited an AWS account running a production workload,
created two years ago by someone who has left. List the first six things you check, and why each matters.

---

## 12. Revision notes

- **Root task list is short**: **9 of 16** lab tasks; **3** are rare one-offs, **2** are recovery from your own mistakes.
  Changing the account name is *not* one of them.
- **Root reaches 8/8 capabilities**; a least-privilege runtime role reaches 3/8. Theft likelihood and blast radius are
  separate problems.
- **MFA arithmetic** at 40 attempts/year: **55.43%** (reused password) → **14.81%** (strong password) → **1.59%** (TOTP,
  9×) → **0.08%** (phishing-resistant, 185×).
- **Accounts beat policies**: a dev compromise reaches **100% / 60% / 35%** under one account, prod-separated, and
  per-environment layouts.
- **Nine of ten baseline items fail silently** — put them in code and check them on a schedule.
- **Modern root hygiene**: Organizations member accounts can have **no root credentials at all**.

---

## 13. Completion checklist

- [ ] I can list the tasks that genuinely require root, and I use a role for everything else.
- [ ] Root has phishing-resistant MFA, no access keys, and a monitored email address.
- [ ] Humans are federated with short sessions; machines use roles, not users.
- [ ] Environments are separated by account, under an organisation with SCPs.
- [ ] The baseline checklist is automated, and break-glass has been rehearsed.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS IAM User Guide — *AWS account root user* and *Tasks that require root user credentials*; centralised root access via
  AWS Organizations — <https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-tasks.html> `[VERIFIED 2026-09-16]`
- AWS Organizations — Service Control Policies as maximum-permission guardrails `[STABLE]`
- M10-L07 (access control as a governance control) and M10-L14 (incident response, break-glass) `[STABLE]`
- M11-L04 (IAM policies and least privilege) and M11-L05 (temporary credentials) — the next two layers `[STABLE]`
- M11-L06 (budgets and alerts) and M11-L16 (CloudTrail) — the detection half of this lesson `[STABLE]`

---

## 15. Next lesson

→ [M11-L04 — IAM: Identities, Policies, Roles and Least Privilege](M11-L04-iam-policies-roles.md) moves inside the
account: how AWS actually decides whether a request is allowed, in what order, and why "least privilege" is a measurable
property rather than an aspiration.
