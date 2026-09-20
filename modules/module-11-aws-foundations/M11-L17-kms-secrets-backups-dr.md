# M11-L17 — KMS, Secrets Manager, Backups and Disaster Recovery

| | |
|---|---|
| **Lesson ID** | M11-L17 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M11-L10](M11-L10-s3-buckets-permissions-encryption.md), [M11-L04](M11-L04-iam-policies-roles.md) |

---

## 1. Learning objectives

1. **Explain** why a KMS key needs both a key policy and an IAM policy, and use that as a governance control.
2. **Use envelope encryption and data-key caching** to make encryption affordable at scale.
3. **Choose** where a secret lives from rotation and auditability, not only from encryption.
4. **State RPO and RTO** as tested promises, and translate a backup schedule into lost work.
5. **Select** a disaster-recovery strategy from the RPO and RTO the business actually needs.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **KMS key** | A managed key; access is governed by its **key policy** as well as by IAM. |
| **Key policy** | The resource policy on a KMS key; without it, no IAM policy grants access. |
| **Grant** | A narrow, temporary delegation of key use, often made by an AWS service. |
| **Envelope encryption** | KMS encrypts a **data key**; the data key encrypts the data. |
| **Data-key caching** | Reusing a decrypted data key for multiple operations, reducing KMS calls. |
| **RPO** | Recovery point objective — how much recent data you can afford to lose. |
| **RTO** | Recovery time objective — how long you can afford to be down. |
| **Pilot light / warm standby** | DR strategies with data replicated and compute off, or a small live copy. |
| **Restore test** | Actually recovering from a backup, which is the only thing that validates one. |

---

## 3. Plain-language explanation

### 3.1 A KMS key has two gates, and an administrator may pass neither

§7.1: an account administrator with `Action: *` **cannot decrypt** unless the **key policy** names them. That is unusual
in AWS and it is the point: "who can read this data" becomes a short, reviewable document rather than an emergent property
of a hundred IAM policies.

The same mechanism gives you revocation: **disabling the key makes the data unreadable by everyone, immediately** — the
lever M10-L06 asks for and L10 §5.2 identified as the reason to pay for a customer-managed key.

### 3.2 Envelope encryption makes it affordable

§7.2: 60 million operations a month at one KMS call each is **$180/month**; with S3 Bucket Keys, **$1.80**; with a
five-minute application data-key cache, **$0.11**. KMS encrypts a **data key**, and the data key encrypts the data — so
reuse collapses the call count.

The trade-off is blast radius: a cached data key protects more objects, so cache for minutes, not days, and never persist
a plaintext data key.

### 3.3 The question is rotation, not encryption

§7.3 compares six places a secret can live. **4 of 6 have no encryption at rest**. But the property that matters more is
that the first three — source, image, plain environment variable — **cannot be rotated** and leave **no record of who read
them**. A secret you cannot rotate is one you can never properly respond to a leak about.

### 3.4 A backup schedule is a promise about lost work

§7.4, at 1,400 writes a minute: a nightly snapshot means an RPO of 24 hours — **2,016,000 writes** at worst, and on
average half a day of work. Point-in-time recovery at five minutes: **7,000**. Continuous replication: **140**.

### 3.5 Four DR strategies, four prices

§7.5: backup and restore (**RTO hours**, cost **0.02×**), pilot light (**tens of minutes**, **0.15×**), warm standby
(**minutes**, **0.45×**), multi-site active/active (**near zero**, **1.00×**).

Remember L02 §7.2: if your own software contributes more unavailability than the infrastructure does, a multi-region
project buys almost nothing. The honest first step for most teams is **backup and restore, tested quarterly** — because an
untested backup has an unknown RTO and possibly an infinite one.

---

## 4. Analogy

**A safe deposit box with two keys.** The bank's key and yours must both turn — being the bank manager does not open your
box. If you destroy your key, nobody opens it, ever, including you. You do not carry the contents around; you take out one
day's documents (a data key) and put them back. And the spare key taped inside the lid of the box is not a spare key at
all: it is the same risk written twice.

### Where the analogy breaks

- **A safe deposit box holds one thing; a KMS key protects a corpus**, so disabling it is an outage as well as a control
  (§5.2).
- **The bank tests its vault; nobody tests your backups unless you schedule it** (§5.6).

---

## 5. Detailed technical explanation

### 5.1 KMS access

`[REAL, evaluated]` §7.1.

```text
allowed  ⟺  key policy permits the principal
        AND the principal's IAM policy permits the KMS action
        AND the key is enabled
        (or a grant covers the operation)
```

Consequences to design around:

- **Key policies are short and reviewable.** Keep them that way: name the roles that may `Decrypt`, the roles that may
  `Encrypt`, and the (few) administrators.
- **Separate the administrator from the user.** The person who can delete a key should not be the one who can read the
  data, and vice versa.
- **`kms:ViaService`** restricts use of the key to a particular service (e.g. only via S3 in a region), which prevents a
  stolen credential decrypting objects directly.
- **Key rotation** keeps the same key id with new backing material; it does not re-encrypt existing data, and it is not a
  substitute for revocation.

### 5.2 Envelope encryption

`[REAL, computed — ILLUSTRATIVE rate]` §7.2 — $180 → $1.80 → $0.11 per month.

```text
GenerateDataKey -> {plaintext data key, encrypted data key}
encrypt data with the plaintext key; store the encrypted key beside the data
to read: Decrypt(encrypted data key) -> plaintext key -> decrypt data
```

Enable **S3 Bucket Keys** for S3 workloads; use the AWS Encryption SDK's caching for application-side encryption, with a
short maximum age and a maximum number of messages per key.

### 5.3 Secrets

`[REAL, compared]` §7.3 — 4 of 6 unencrypted at rest.

| Where | Encrypted | Rotatable | Audited | Use |
|---|---|---|---|---|
| Source / image / plain env var | No | **No** | No | Never |
| SSM Parameter Store (String) | No | Manual | CloudTrail | Non-secret configuration |
| SSM Parameter Store (SecureString) | Yes (KMS) | Manual | CloudTrail + key log | Cheap secrets |
| Secrets Manager | Yes (KMS) | **Automatic rotation** | CloudTrail + key log | Database credentials, API keys |

Better than any of them: **no secret at all**. IAM roles for AWS services (L05), IAM database authentication, and OIDC
federation for CI (L18) remove the secret rather than protecting it. Reserve the secret store for credentials to systems
that cannot use a role.

Operational rules: fetch at start-up and cache in memory with a refresh, never at every request; never log a secret;
alarm on retrieval from unexpected principals; and rehearse rotation before you need it.

### 5.4 Backups

`[REAL, computed]` §7.4.

| Mechanism | Protects against |
|---|---|
| Automated snapshots / PITR | Deletion, corruption, bad migration |
| Cross-region copies | Region loss |
| **Cross-account** copies with a locked vault | Compromised credentials, ransomware |
| S3 versioning + Object Lock | Overwrite and delete (L10 §5.5) |

The rule from L10 bears repeating: **a backup reachable by the credentials that destroyed the original is not a backup**.
Use a separate account and a vault with a retention lock.

Use **AWS Backup** to centralise policy across services, so "is this database backed up?" has one answer rather than one
per team.

### 5.5 RPO and RTO

`[REAL, computed]` §7.4 — 2,016,000 / 504,000 / 7,000 / 140 writes at risk.

Both are **business decisions** and should be written down with the owner who accepted them (M10-L16 §5.4). Translate them
into the language of the business — "up to half a day of submitted claims" — rather than leaving them as acronyms in an
architecture document.

### 5.6 Disaster recovery and the restore test

`[REAL, compared — ILLUSTRATIVE costs]` §7.5.

| Strategy | RPO | RTO | Relative cost | Region 2 holds |
|---|---|---|---|---|
| Backup and restore | Hours to a day | Hours | 0.02× | Backups only |
| Pilot light | Minutes | Tens of minutes | 0.15× | Data replicated, compute off |
| Warm standby | Minutes | Minutes | 0.45× | A small live copy |
| Multi-site active/active | Near zero | Near zero | 1.00× | A full second deployment |

What a restore test finds that a backup policy never does:

- The backup did not include something you need — a configuration, a key, a schema migration.
- The restore requires a permission nobody currently has.
- The restore takes six hours, not the forty-five minutes on the slide.
- The restored data is missing the last N hours, because the mechanism was misunderstood.

Schedule it quarterly, time it, and record the measured RTO next to the promised one (M10-L14, M10-L15).

### 5.7 What this means for an AI system

| Asset | Protection |
|---|---|
| Source documents in S3 | Versioning, Object Lock, cross-account replication (L10) |
| Vector index | Usually **reproducible** from sources — but measure the rebuild time, because that is your real RTO (M7-L16) |
| Prompts and configuration | In version control; the run fingerprint identifies them (M10-L13) |
| Evaluation sets and results | Back up — they are hard to recreate and you need them to re-gate after recovery (M10-L12) |
| Conversation state and user data | Backed up, with retention and deletion honoured (M10-L06) |
| Model provider credentials | Secrets Manager with rotation; better, a role (§5.3) |

The reproducibility of the index is a genuine cost saving and a genuine trap: "we can rebuild it" is an RTO claim like any
other, and it needs timing.

### 5.8 Assumptions and limitations

- All prices, volumes, timings and relative costs are invented.
- Key rotation mechanics, multi-Region keys, CloudHSM and AWS Backup configuration are out of scope.
- DR strategy names follow AWS's common terminology; the boundaries between them are fuzzy in practice.

---

## 6. Worked example — the backup that restored everything except the key

**The situation.** A team ran quarterly "DR reviews" that confirmed snapshots existed and cross-region copies were
enabled. Every review passed.

**Then a bad migration corrupted a production table.**

1. The snapshot restored cleanly, in about 50 minutes — close to the promised RTO (§7.4).
2. The application could not read the restored data: several columns were encrypted with a **customer-managed KMS key**,
   and the restored instance was in a **second region** where that key did not exist (§5.1).
3. A multi-Region key had never been configured because the review checked backups, not decryptability (§5.6).
4. The role that could administer the key had been deleted in a tidy-up; the key policy named a principal that no longer
   existed, so nobody could modify the policy except via the account's root user (L03 §5.1).
5. Actual RTO: **eleven hours**, most of it spent on the key.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Backups tested, restores not | Quarterly **restore** test, timed end to end (§5.6) |
| 2 | Key not available in the recovery region | Multi-Region key, or a documented re-encrypt path |
| 3 | Key policy named a deleted principal | Review key policies; always name a role that exists |
| 4 | RTO claimed, never measured | Record measured RTO beside the promised one |
| 5 | DR review checked artefacts, not outcomes | Test the outcome: can the application serve traffic? |

**The general rule.** **A backup is not a backup until you have restored from it, in the place you would have to restore
it, with the keys you would actually have.**

---

## 7. Practical activity

**File:** [`labs/m11/l17_kms_secrets_backups_dr.py`](../../labs/m11/l17_kms_secrets_backups_dr.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l17_kms_secrets_backups_dr.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. A KMS KEY HAS TWO GATES
============================================================================
  scenario                                      decrypt?   why
  app role: key policy yes, IAM yes              ALLOWED   allowed by the key policy AND the caller's IAM policy
  app role: key policy yes, IAM no                denied   the caller's IAM policy does not permit kms:Decrypt
  app role: key policy NO, IAM yes (admin)        denied   the KEY POLICY does not permit this principal
  account administrator, no key policy entry      denied   the KEY POLICY does not permit this principal
  app role, but the key is disabled               denied   the key is disabled -- nothing can decrypt, including you

  Row 4 is the one that surprises people: an account administrator with
  'Action: *' CANNOT decrypt unless the KEY POLICY says so. A KMS key is the
  one resource where IAM alone is not enough, which is exactly what makes it
  a governance control: 'who can read this data' becomes a short, reviewable
  document rather than an emergent property of a hundred IAM policies.
  Row 5 is the other half: disabling the key makes the data unreadable by
  EVERYONE, immediately -- the revocation lever from M10-L06.

============================================================================
2. ENVELOPE ENCRYPTION AND DATA-KEY CACHING
============================================================================
  60,000,000 encrypt/decrypt operations per month

  strategy                                      KMS calls    $/month
  one KMS call per object                      60,000,000        180
  S3 Bucket Keys (shared data key)                600,000          2
  application data-key cache, 5 min                36,000          0
  application data-key cache, 1 hour                3,000          0

  [ILLUSTRATIVE rate.] Envelope encryption is why this works: KMS encrypts a
  DATA KEY, and the data key encrypts the data. Reuse the data key across many
  objects and the KMS calls collapse. The trade-off is blast radius: a cached
  data key in memory protects more objects, so cache for minutes, not days,
  and never persist a plaintext data key.

============================================================================
3. WHERE DOES THE SECRET LIVE, AND WHO CAN READ IT?
============================================================================
  where                                   encrypted    gated by   who can read it
  hard-coded in source                           NO        none   everyone with repo access, forever, including git history
  in the container image                         NO        none   anyone who can pull the image (M11-L12)
  plain environment variable                     NO        none   anyone who can describe the task or read a crash dump
  SSM Parameter Store (String)                   NO         IAM   anyone with ssm:GetParameter
  SSM Parameter Store (SecureString)            yes   IAM + KMS   IAM + the KMS key policy
  Secrets Manager                               yes   IAM + KMS   IAM + the KMS key policy, with rotation

  places offering no encryption at rest: 4/6
  The first three also share a property that matters more than encryption:
  there is no way to ROTATE them and no record of who read them. A secret you
  cannot rotate is a secret you can never respond to a leak about -- so the
  question at design time is not 'is it encrypted' but 'what do we do at 2am
  when it leaks' (M10-L14, M11-L05).

============================================================================
4. RPO AND RTO: WHAT THE BACKUP SCHEDULE ACTUALLY PROMISES
============================================================================
  the system takes 1,400 writes per minute

  strategy                                     RPO   writes lost      RTO   recovery action
  nightly snapshot                        1440 min     2,016,000     90 m   restore + re-point the app
  snapshot every 6 hours                   360 min       504,000     90 m   restore + re-point the app
  point-in-time recovery (5 min)             5 min         7,000     45 m   restore to a new instance
  continuous replication to standby            6 s           140      2 m   failover (M11-L14)

  RPO is how much data you lose; RTO is how long you are down. They are
  bought separately and they are both PROMISES YOU HAVE TESTED, or they are
  guesses. A nightly snapshot means an average half-day of lost work -- which
  is a business decision, not a default, and somebody should have been asked.

============================================================================
5. FOUR DISASTER-RECOVERY STRATEGIES
============================================================================
  strategy                    RPO               RTO            rel. cost   what exists in region 2
  backup and restore          hours to a day    hours               0.02   rebuild from backups in another region
  pilot light                 minutes           tens of min         0.15   data replicated; compute off until needed
  warm standby                minutes           minutes             0.45   a small live copy, scaled up on failover
  multi-site active/active    near zero         near zero           1.00   both regions serve traffic

  [Relative cost is the second region's share of the first's; ILLUSTRATIVE.]
  Choose from the RPO and RTO the business actually needs -- and remember
  M11-L02: if your own software contributes more unavailability than the
  infrastructure does, a multi-region project buys almost nothing. The
  honest first step for most teams is 'backup and restore, tested quarterly',
  because an untested backup has an unknown RTO and quite possibly an
  infinite one (M10-L14).

  Four things a restore test finds that a backup policy never does:
    - the backup did not include the thing you need (a config, a key)
    - the restore needs a permission nobody has
    - the restore takes 6 hours, not the 45 minutes on the slide
    - the restored data is missing the last N hours nobody accounted for

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every access verdict, KMS call count, cost, RPO/RTO figure and
  comparison above is computed from the values and rules in this script.

  DOCUMENTED BEHAVIOUR: a KMS key requires BOTH the key policy and the
  caller's IAM policy to permit the operation (unless a grant applies);
  disabling a key makes ciphertext undecryptable by everyone; envelope
  encryption lets one data key protect many objects.

  ILLUSTRATIVE: all prices, volumes, timings and relative costs are invented.

  NOT SHOWN: key rotation mechanics, multi-Region keys, CloudHSM, AWS Backup
  configuration, and cross-account backup vaults (M12-L11).

Done.
```

### 7.3 Reading the result

**Section 1, row 4** is the fact to remember: `Action: *` is not enough for a KMS key.

**Section 2's spread** — $180 to $0.11 — is why envelope encryption exists.

**Section 3's first three rows** are the ones that cannot be rotated, which matters more than the encryption column.

**Section 4's second column** converts a schedule into lost work, which is the form a business decision can be made in.

**Section 5's last block** is the list a restore test produces and a policy review never does.

---

## 8. Common mistakes and troubleshooting

1. **Assuming IAM alone grants KMS access.** §7.1.
2. **A key policy naming a deleted principal.** §6 — recoverable only via root.
3. **One KMS call per object.** §7.2 — enable Bucket Keys or caching.
4. **Caching data keys for hours or persisting them.** §5.2 — blast radius.
5. **Secrets in environment variables or images.** §7.3 — unrotatable and unaudited.
6. **Fetching a secret on every request.** Cache with a refresh.
7. **Backups in the same account as the data.** §5.4 — not a backup.
8. **RPO and RTO never translated into business terms.** §5.5.
9. **DR reviews that check artefacts rather than outcomes.** §6.
10. **Assuming the vector index "can just be rebuilt".** §5.7 — time it.

| Symptom | Likely cause | Fix |
|---|---|---|
| `AccessDenied` on decrypt with a permissive IAM policy | Key policy does not name the principal | Add it to the key policy (§5.1) |
| KMS charges larger than expected | One call per object | Bucket Keys; data-key caching |
| A leaked credential cannot be rotated | Secret in an image or env var | Move to Secrets Manager; prefer a role |
| Restore succeeds, application still fails | Keys or configuration missing in the recovery path | Test the outcome, not the artefact |
| Real RTO far exceeds the promise | Never measured | Timed restore test; record the measured value |

---

## 9. Security, privacy, reliability, cost

- **Security.** The key policy is a short, reviewable answer to "who can read this", and disabling a key is the fastest
  containment action available (M10-L14).
- **Privacy.** Deletion must reach backups and snapshots, or the deletion promise is false (M10-L06, L10).
- **Reliability.** RPO and RTO are the reliability targets that matter most in a disaster, and only a restore test
  validates them.
- **Cost.** Envelope encryption and Bucket Keys make encryption nearly free; DR cost scales steeply with RTO, so buy the
  RTO you need (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why can an account administrator be denied `kms:Decrypt`?
2. What does disabling a KMS key do?
3. How much did data-key caching save in §7.2?
4. Which three places in §7.3 cannot be rotated?
5. How many writes does a nightly snapshot put at risk in §7.4?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the operation count to 600 million and re-read section 2.
2. Add "IAM database authentication (no secret)" to §7.3 and describe its properties.
3. Change the write rate in §7.4 to your own and re-derive the lost-work figures.
4. Add a fifth DR strategy to §7.5 for your own system.
5. Write the key policy for a bucket key: who encrypts, who decrypts, who administers.

### Exercise 3 — Challenge (~60 min)

1. Write the RPO and RTO for one system in business terms, and get them accepted by name (M10-L16).
2. Run a timed restore test and record the measured RTO beside the promised one.
3. Time a full vector-index rebuild and treat it as an RTO component (M7-L16).
4. Migrate one secret from an environment variable to Secrets Manager with rotation, and rehearse the rotation.
5. Design the cross-account backup vault with a retention lock, and prove production credentials cannot delete from it.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l17).)*

**Q1.** What is required for a principal to decrypt with a KMS key?

- A. An IAM policy allowing `kms:Decrypt`
- B. Membership of the key's administrator group
- C. Both the key policy and the caller's IAM policy to permit it
- D. The key policy alone

**Q2.** An account administrator with `Action: *` cannot decrypt. Why?

- A. Administrators are excluded from KMS operations by default
- B. The key policy does not name them
- C. `Action: *` excludes KMS actions
- D. The key is in a different region

**Q3.** What happens when a KMS key is disabled?

- A. The data becomes unreadable by everyone, immediately
- B. Only new encryptions fail
- C. Access falls back to IAM policies alone
- D. Existing ciphertext is re-encrypted with a new key

**Q4.** What does envelope encryption do?

- A. Encrypts data twice for defence in depth
- B. Has KMS encrypt a data key, which then encrypts the data
- C. Stores the key alongside the data in the same object
- D. Replaces the key policy with an IAM policy

**Q5.** In §7.2, what did a five-minute data-key cache reduce the monthly KMS cost to?

- A. $180
- B. $1.80
- C. $0.11
- D. $18

**Q6.** What is the trade-off of caching data keys for longer?

- A. Higher KMS charges
- B. Slower decryption
- C. Loss of the audit trail entirely
- D. A larger blast radius if the cached key is exposed

**Q7.** Why is a secret in an environment variable worse than an unencrypted one in Parameter Store?

- A. It cannot be rotated and there is no record of who read it
- B. Parameter Store encrypts all values by default
- C. Environment variables are visible over the network
- D. Environment variables are limited in size

**Q8.** What is better than protecting a secret?

- A. Rotating it more frequently
- B. Not having one — use a role or federated identity
- C. Splitting it across two stores
- D. Encrypting it with a customer-managed key

**Q9.** At 1,400 writes a minute, how many writes does a 24-hour RPO put at risk?

- A. 7,000
- B. 140
- C. 504,000
- D. 2,016,000

**Q10.** What distinguishes RPO from RTO?

- A. RPO is how much data you lose; RTO is how long you are down
- B. RPO applies to databases; RTO applies to compute
- C. RPO is measured in minutes; RTO in hours
- D. RPO is a target; RTO is a measurement

**Q11.** Which DR strategy keeps data replicated but compute switched off?

- A. Backup and restore
- B. Warm standby
- C. Pilot light
- D. Multi-site active/active

**Q12.** What does a restore test find that a backup policy review does not?

- A. Whether snapshots were taken on schedule
- B. Whether cross-region copies are enabled
- C. Whether retention meets the policy
- D. Whether the restore actually works, how long it takes, and what is missing

**Q13.** *(Written, rubric-graded.)* In under 150 words: your DR plan is "nightly snapshots, copied cross-region". State
the RPO and RTO it implies, the questions you would ask before accepting it, and the one test you would run.

---

## 12. Revision notes

- **KMS has two gates**: key policy **and** IAM. An `Action: *` administrator is denied without a key-policy entry.
  Disabling the key revokes access to everyone instantly.
- **Envelope encryption**: $180 → **$1.80** (Bucket Keys) → **$0.11** (5-minute cache) per month for 60M operations.
  Cache for minutes, never persist a plaintext data key.
- **Secrets**: **4 of 6** locations unencrypted; the first three are also **unrotatable and unaudited**. Best is no secret
  — use a role.
- **RPO/RTO**: a nightly snapshot risks **2,016,000** writes at 1,400/minute; PITR at 5 minutes risks **7,000**.
- **DR strategies**: backup/restore **0.02×**, pilot light **0.15×**, warm standby **0.45×**, active/active **1.00×**.
- **A backup is not a backup until you have restored from it**, in the recovery region, with the keys you would have.

---

## 13. Completion checklist

- [ ] Sensitive data uses customer-managed keys with short, reviewed key policies.
- [ ] Key administrators and key users are different principals; `kms:ViaService` is used where it fits.
- [ ] Bucket Keys or data-key caching are enabled; no plaintext data key is persisted.
- [ ] No secret lives in source, an image or a plain environment variable; roles are used where possible.
- [ ] Backups exist in a separate account with a retention lock.
- [ ] RPO and RTO are written in business terms, accepted by name, and validated by a timed restore test.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS KMS Developer Guide — key policies as the primary access control, grants, `kms:ViaService`, envelope encryption,
  key rotation `[STABLE]`
- AWS Secrets Manager and SSM Parameter Store — encryption, rotation and access auditing `[STABLE]`
- AWS Backup; AWS disaster-recovery strategies: backup and restore, pilot light, warm standby, multi-site active/active `[STABLE]`
- M10-L06 (deletion reaching backups) and M10-L14 (containment and recovery) `[STABLE]`
- M11-L10 (S3 encryption and Object Lock) and M11-L02 (whether multi-region is the right investment) `[STABLE]`

---

## 15. Next lesson

→ [M11-L18 — Infrastructure as Code, CI/CD and Rollback](M11-L18-iac-cicd-rollback.md) closes the module by making
everything in it reproducible: the account baseline, the network, the permissions, the alarms and the keys, defined in
code, reviewed, and deployable — and revertible — without anyone opening a console.
