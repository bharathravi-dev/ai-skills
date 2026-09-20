# M11-L10 — S3: Buckets, Permissions, Encryption, Lifecycle

| | |
|---|---|
| **Lesson ID** | M11-L10 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M11-L04](M11-L04-iam-policies-roles.md), [M11-L08](M11-L08-public-private-nat-endpoints.md) |

---

## 1. Learning objectives

1. **Evaluate** whether a bucket is public using all four Block Public Access settings, not by eye.
2. **Choose** an encryption option from *who can decrypt* and *can you revoke*, not from a checkbox.
3. **Compute** lifecycle savings, and avoid the minimum-duration and retrieval-cost traps.
4. **Explain** what a `DELETE` does with versioning on, and bound the cost of old versions.
5. **Separate** durability from backup, and name the control for each real loss mode.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Bucket policy** | A resource-based policy on a bucket (L04). |
| **ACL** | The older per-object/per-bucket grant mechanism; disabled by default on new buckets. |
| **Block Public Access (BPA)** | Four settings that prevent or neutralise public grants, at organisation, account and bucket level. |
| **SSE-S3** | Server-side encryption with keys AWS manages entirely. |
| **SSE-KMS** | Server-side encryption with a KMS key — AWS-managed or customer-managed. |
| **S3 Bucket Keys** | A feature that reduces KMS request charges for SSE-KMS. |
| **Storage class** | The price/latency/retrieval tier an object is stored in. |
| **Minimum billable duration** | The minimum period an object in a tier is charged for, even if deleted sooner. |
| **Versioning** | Keeping every version of an object; a `DELETE` adds a delete marker. |
| **Object Lock** | Write-once-read-many retention preventing deletion for a period. |

---

## 3. Plain-language explanation

### 3.1 "Public" has four switches, and only one governs policies

§7.1 evaluates eight configurations; **4 are public**. The instructive one is row 6: BPA looks "mostly on" —
`BlockPublicAcls` and `IgnorePublicAcls` are enabled — and the bucket is **still public**, because
`RestrictPublicBuckets` is the setting that governs *policies*.

Two settings prevent public grants being **made** (`BlockPublicAcls`, `BlockPublicPolicy`); two **neutralise** grants
already there (`IgnorePublicAcls`, `RestrictPublicBuckets`). You need all four.

### 3.2 Encryption's real question is "can you revoke it?"

§7.2: with **SSE-S3**, anyone with `s3:GetObject` reads the data — the encryption is invisible to authorization. With a
**customer-managed KMS key**, the reader needs `s3:GetObject` **and** the key policy to permit them, and you can make
every object unreadable by disabling one key. Only that option gives a separate key-level audit trail.

The cost: at 40M reads/month, SSE-KMS adds **$120/month** in KMS request charges (illustrative), which S3 Bucket Keys
reduce substantially.

### 3.3 Lifecycle saves two-thirds, with two traps

§7.3: a 40 TB corpus costs **$33,915** over 36 months in Standard, or **$11,366** under a
Standard → Standard-IA → Glacier Instant Retrieval policy — **66% cheaper**.

The traps: **minimum billable duration** (an object moved to Standard-IA and deleted after 10 days is billed for 30, so
lifecycle rules on short-lived objects can *increase* the bill), and **retrieval cost** — re-indexing the whole corpus
from Glacier Instant Retrieval costs **$1,229 each time** (M7-L16).

### 3.4 A delete with versioning on deletes nothing

§7.4: `DELETE` adds a **delete marker**. `GET` then returns 404, the old versions are still billed, and deleting the
marker restores the object. Without an expiry rule for **noncurrent** versions, a corpus re-ingested four times a year
stores four copies — **$883/year** of versions nobody reads, in the lab's figures.

### 3.5 Durability is about disks; loss is about permissions

§7.5 lists seven ways data is actually lost. **None is a media failure.** Overwrites, deletes, compromised credentials,
bucket deletion, a bad ingestion, a region outage, ransomware — each needs a different control, and none is covered by
durability.

---

## 4. Analogy

**A shared document library.** Whether the public can walk in depends on the front door, the notice on the door, the
receptionist's instructions *and* the standing policy — and three of four being right still leaves it open. Locking the
cabinets helps only if you control who holds the key; a lock whose key is handed out with the building pass is decoration.
Moving old files to off-site storage is cheaper per month and costs money and time to get anything back. And "our shelves
are very sturdy" is not an answer to "what if someone throws the files away?".

### Where the analogy breaks

- **A library's shelves are visible; a bucket's permissions are four settings in three places** (organisation, account,
  bucket), and the effective answer needs all of them (§5.1).
- **Paper files are copied deliberately; S3 versions accumulate silently** and are billed until a rule removes them
  (§5.4).

---

## 5. Detailed technical explanation

### 5.1 Public access, precisely

`[VERIFIED 2026-09-17 — Amazon S3 User Guide, "Blocking public access to your Amazon S3 storage"]`

New buckets, access points and objects **do not allow public access by default**; users can still change policies and
permissions, which is what BPA overrides.

| Setting | Effect |
|---|---|
| `BlockPublicAcls` | Rejects `PutBucketAcl` / `PutObjectAcl` calls that specify a public ACL |
| `IgnorePublicAcls` | Ignores all public ACLs on the bucket and its objects (existing ones included) |
| `BlockPublicPolicy` | Rejects `PutBucketPolicy` calls whose policy allows public access |
| `RestrictPublicBuckets` | Restricts a bucket with a public policy to AWS service principals and users in the owner's account — blocking cross-account access |

Apply them at the **organisation** level (via AWS Organizations) and the **account** level, so an individual bucket cannot
opt out. Also set **Object Ownership** to bucket-owner-enforced, which disables ACLs entirely and removes a whole class of
mistake.

Then use **IAM Access Analyzer for S3** to review which buckets are reachable from outside the account (L04 §5.5).

### 5.2 Encryption options

`[REAL, compared — ILLUSTRATIVE rates]` §7.2.

| Option | Who can decrypt | Revoke by | Audit | Cost |
|---|---|---|---|---|
| SSE-S3 | Anyone with `s3:GetObject` | Removing S3 permission | S3 data events only | None |
| SSE-KMS, AWS-managed key | `s3:GetObject` + `kms:Decrypt` | Not directly — AWS owns the key policy | CloudTrail on the key | Per request |
| **SSE-KMS, customer-managed key** | `s3:GetObject` **and** the key policy | **Editing or disabling the key** | CloudTrail on the key | Per request + key/month |
| Client-side | Whoever holds your key | Your mechanism | Your mechanism | Engineering |

For anything sensitive, use a **customer-managed key**, enable **S3 Bucket Keys** to cut request charges, and treat the
key policy as a second, independent authorization layer (L17). Enforce encryption with a bucket policy that denies
`s3:PutObject` without the expected `s3:x-amz-server-side-encryption` header and key id.

Encryption in transit is separate: deny requests where `aws:SecureTransport` is false.

### 5.3 Lifecycle and storage classes

`[REAL, computed — ILLUSTRATIVE rates]` §7.3 — $33,915 → $11,366, 66% cheaper.

| Class | Use for | Watch |
|---|---|---|
| Standard | Active data, frequent reads | Default; most expensive |
| Intelligent-Tiering | Unpredictable access patterns | A small per-object monitoring charge |
| Standard-IA | Infrequent but immediate access | 30-day minimum; retrieval charge |
| One Zone-IA | Reproducible data only | Single AZ — it is not durable against AZ loss |
| Glacier Instant Retrieval | Archives needing millisecond access | 90-day minimum; higher retrieval charge |
| Glacier Flexible / Deep Archive | Genuine archives | 90/180-day minimum; retrieval takes minutes to hours |

Two rules for RAG corpora specifically: source documents that will be **re-ingested** (M7-L16) should not sit in a class
with a high retrieval charge, and **derived artefacts** — chunk stores, embeddings caches — are reproducible, so decide
deliberately whether to store them at all.

### 5.4 Versioning

`[REAL, computed]` §7.4.

- A `DELETE` creates a **delete marker**; the object is still there and still billed.
- A `GET` returns 404 because the marker is the current version.
- Deleting the marker **restores** the object — this is the recovery path in most accidental-delete incidents.
- `DELETE` with a version id removes that version permanently.
- **MFA delete** can require MFA to remove versions, for the strictest buckets.

Always pair versioning with a lifecycle rule that **expires noncurrent versions** after a chosen period, and with a rule
that **aborts incomplete multipart uploads** — otherwise both grow unbounded and invisibly.

Versioning is also the mechanism that makes deletion for privacy harder: a deletion request must remove **all versions**
(M10-L06, M10-L13).

### 5.5 Durability is not backup

`[REAL, enumerated]` §7.5 — seven loss modes, none of them media failure.

| Loss | Control |
|---|---|
| Overwrite | Versioning with noncurrent retention |
| Accidental delete | Versioning; MFA delete for critical buckets |
| Credential compromise | Versioning + Object Lock + copies in a separate account |
| Bucket deletion | Object Lock, deny-delete policies, replication to another account |
| Bad ingestion overwriting good data | Versioning + a **tested** restore procedure |
| Region unavailable | Cross-region replication (L02) |
| Ransomware | Object Lock in compliance mode; versions in another account |

The recurring theme: **a separate account** is what makes a backup a backup. Copies reachable by the same credentials that
destroyed the original are not a recovery plan (L03 §5.4).

### 5.6 The bucket checklist

```text
[ ] BPA: all four settings, at organisation and account level
[ ] Object Ownership: bucket-owner-enforced (ACLs disabled)
[ ] Encryption: SSE-KMS with a customer-managed key; Bucket Keys on
[ ] Bucket policy: deny unencrypted PUTs; deny aws:SecureTransport = false
[ ] Access restricted to your VPC endpoint (aws:SourceVpce) where applicable (L08)
[ ] Versioning on; noncurrent expiry rule; abort incomplete multipart uploads
[ ] Lifecycle transitions matched to real access patterns and retrieval needs
[ ] Replication to a separate account for anything you cannot lose
[ ] Access logging / data events for sensitive buckets (L16)
[ ] Tags: owner, environment, service, cost-centre, data-class (L06)
```

### 5.7 Assumptions and limitations

- All rates and corpus sizes are invented; storage-class minimums are as documented but should be re-checked.
- The lab's evaluator models BPA's documented behaviour, not the full "meaning of public" evaluation AWS performs.
- Access points, Object Lock configuration, replication mechanics and request-rate design are out of scope.

---

## 6. Worked example — the corpus that cost more after the optimisation

**The situation.** A team's RAG corpus was 40 TB of source documents in S3 Standard. A cost review recommended a lifecycle
policy. They applied "transition to Standard-IA after 30 days, Glacier Instant Retrieval after 90".

**What happened.**

1. The bill went **up** for two months. The pipeline re-ingested and **overwrote** a large fraction of documents monthly;
   each overwrite created a new object that transitioned and was then superseded, incurring the **30-day minimum** charge
   (§5.3).
2. Transition requests themselves are charged per object; the corpus had millions of small files (§5.3).
3. A quarterly re-index read the whole corpus from Glacier Instant Retrieval: **$1,229** in retrieval charges per run,
   which nobody had modelled (§7.3).
4. Versioning was on with **no noncurrent expiry**, so every overwritten version stayed — and transitioned — and was
   billed (§7.4).
5. The eventual design: keep the working set in Standard, archive only documents untouched for a year, expire noncurrent
   versions after 30 days, and stop storing the derived chunk store at all.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Lifecycle applied to short-lived objects | Transition only what is genuinely cold |
| 2 | Per-object transition costs on millions of files | Aggregate small files; check request costs |
| 3 | Retrieval cost for re-indexing not modelled | Match the class to the re-index pattern (M7-L16) |
| 4 | No noncurrent version expiry | Lifecycle rule on noncurrent versions |
| 5 | Derived artefacts stored as if precious | Reproducible data gets a different policy |

**The general rule.** **Lifecycle rules are priced on access patterns, not on file age. Measure the pattern first.**

---

## 7. Practical activity

**File:** [`labs/m11/l10_s3_permissions_encryption_lifecycle.py`](../../labs/m11/l10_s3_permissions_encryption_lifecycle.py)

**No AWS account, no network, no third-party dependencies.** The Block Public Access evaluator implements the four
documented settings, so you can test a configuration before applying it.

```bash
source .venv/bin/activate
python labs/m11/l10_s3_permissions_encryption_lifecycle.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. IS THIS BUCKET PUBLIC?
============================================================================
  configuration                              public?   why
  new bucket, defaults                       private   nothing grants public access
  public policy, BPA all on                  private   public policy present but RESTRICTED to the account
  public policy, BPA all off                  PUBLIC   a public bucket policy is in effect
  public ACL, BPA all off                     PUBLIC   a public ACL is in effect
  public ACL, BPA all on                     private   public ACL present but IGNORED
  public policy, only ACL settings on         PUBLIC   a public bucket policy is in effect
  both public, BPA all off                    PUBLIC   a public ACL is in effect; a public bucket policy is in effect
  both public, BPA all on                    private   public ACL present but IGNORED; public policy present but RESTRICTED to the account

  public: 4/8
  Row 6 is the trap: three of the four settings look 'mostly on' and the
  bucket is still public, because RestrictPublicBuckets is the one that
  governs policies. Set all four, at the ACCOUNT level (and now at the
  organisation level), so a new bucket cannot opt out.
  BlockPublicAcls and BlockPublicPolicy prevent public settings being MADE;
  IgnorePublicAcls and RestrictPublicBuckets neutralise ones already there.

============================================================================
2. ENCRYPTION: WHO CAN ACTUALLY DECRYPT IT?
============================================================================
  option                            who can decrypt                   revoke access?          
  SSE-S3 (AES256, AWS-managed)      anyone with s3:GetObject          no -- remove S3 permission
  SSE-KMS (AWS-managed key)         s3:GetObject + kms:Decrypt        no -- AWS manages the policy
  SSE-KMS (customer-managed key)    s3:GetObject + the KEY POLICY     YES -- edit or disable the key
  client-side encryption            whoever holds your key            yours to build          

  at 40,000,000 object reads/month [ILLUSTRATIVE rate $0.03/10k KMS requests]:
    SSE-S3 (AES256, AWS-managed)      $        0/month in KMS request charges
    SSE-KMS (AWS-managed key)         $      120/month in KMS request charges
    SSE-KMS (customer-managed key)    $      120/month in KMS request charges
    client-side encryption            $        0/month in KMS request charges

  The row that matters for governance is 'revoke access?'. Only a
  CUSTOMER-MANAGED key lets you make data unreadable by changing one policy,
  without touching a single object -- and only it gives you a key-level audit
  trail separate from the data-level one (M11-L17, M10-L13).
  Use S3 Bucket Keys to cut the KMS request charge above substantially.

============================================================================
3. LIFECYCLE: 36 MONTHS OF A DOCUMENT CORPUS  [ILLUSTRATIVE RATES]
============================================================================
  40,960 GB corpus, 36 months

  storage class                    $/GB/mo  min days    36 months  retrieve all
  Standard                          0.0230         0       33,915             0
  Standard-IA                       0.0125        30       18,432           410
  Glacier Instant Retrieval         0.0040        90        5,898         1,229
  Glacier Flexible Retrieval        0.0036        90        5,308           410
  Glacier Deep Archive              0.0010       180        1,475           819

  a lifecycle policy of Standard 3mo -> Standard-IA 9mo -> Glacier Instant Retrieval 24mo:
    $11,366 over 36 months vs $33,915 all-Standard -- 66% cheaper
  Two traps. MINIMUM BILLABLE DURATION: an object moved to Standard-IA and
  deleted after 10 days is billed for 30, so lifecycle rules on short-lived
  objects can INCREASE the bill. And RETRIEVAL costs money: a RAG re-index
  that reads the whole corpus from Glacier Instant Retrieval costs
  $1,229 each time (M7-L16).

============================================================================
4. VERSIONING: WHAT DOES A DELETE ACTUALLY DO?
============================================================================
  event                             bucket state      result
  PUT report.pdf (v1, 10 MB)        versioning off    1 object,  10 MB billed
  PUT report.pdf (v2, 10 MB)        versioning off    1 object,  10 MB billed -- v1 is GONE
  PUT report.pdf (v1, 10 MB)        versioning ON     1 version, 10 MB billed
  PUT report.pdf (v2, 10 MB)        versioning ON     2 versions, 20 MB billed
  DELETE report.pdf                 versioning ON     2 versions + delete marker, 20 MB STILL billed
  GET report.pdf                    versioning ON     404 -- the delete marker is the current version
  DELETE the delete marker          versioning ON     v2 is current again -- the object is restored

  a 8,000 GB corpus re-ingested 4 times a year with versioning on and no
  expiry rule stores 4x the data: $6,624/year of old versions nobody reads.
  Versioning is the control that makes a delete or an overwrite recoverable
  (section 5). It is also unbounded growth unless a lifecycle rule expires
  NONCURRENT versions -- and that rule is the one teams forget (M10-L06).

============================================================================
5. ELEVEN NINES OF DURABILITY DOES NOT COVER THESE
============================================================================
  how data is actually lost                           what protects against it
  a user or script overwrites the object              versioning + noncurrent retention
  a user or script deletes the object                 versioning; MFA delete for the strictest cases
  credentials are compromised and data is wiped       versioning + Object Lock + a separate account
  the whole bucket is deleted                         Object Lock, deny-delete policy, replication to another account
  a bad ingestion overwrites good documents with bad onesversioning + a tested restore procedure
  the region is unavailable                           cross-region replication (M11-L02)
  ransomware encrypts objects in place                Object Lock in compliance mode; versions in another account

  none of the 7 rows above is a media failure, which is what durability
  measures. Durability is about the disks; every row here is about PERMISSIONS
  and TIME. Test the restore -- an untested backup is a belief (M10-L14).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the Block Public Access evaluator implements the four documented
  settings, and every cost, count and verdict above is computed by this script.

  VERIFIED 2026-09-17: the four Block Public Access settings and their
  behaviours follow the Amazon S3 User Guide; new buckets, access points and
  objects do not allow public access by default, and BPA can be managed at
  organisation, account and bucket level.

  ILLUSTRATIVE: all storage, retrieval and KMS rates are invented, as are the
  corpus sizes. Check current S3 pricing and minimum durations.

  NOT SHOWN: access points, Object Lock configuration in detail, replication
  mechanics, S3 Tables, and request-rate design (M11-L17, M12-L09).

Done.
```

### 7.3 Reading the result

**Section 1, row 6** is the configuration that passes a casual review and is public.

**Section 2's "revoke access?" column** is the reason to pay for a customer-managed key.

**Section 3's last three lines** are the two traps that make lifecycle rules backfire.

**Section 4, rows 5–7** are the delete-marker behaviour that saves you in an incident and costs you every month.

**Section 5** contains no media failures at all.

---

## 8. Common mistakes and troubleshooting

1. **Enabling three of the four BPA settings.** §7.1, row 6.
2. **Leaving ACLs enabled.** Set Object Ownership to bucket-owner-enforced.
3. **Treating SSE-S3 as an access control.** §5.2 — anyone with `s3:GetObject` reads it.
4. **Not enforcing encryption on PUT.** Objects arrive unencrypted and nobody notices.
5. **Lifecycle rules on short-lived objects.** §5.3 — minimum durations increase the bill.
6. **Ignoring retrieval costs for re-indexing.** §7.3 — $1,229 per full read.
7. **Versioning with no noncurrent expiry.** §7.4 — unbounded growth.
8. **No abort rule for incomplete multipart uploads.** Invisible, billed storage.
9. **Believing durability is backup.** §7.5 — and backups in the same account are not backups.

| Symptom | Likely cause | Fix |
|---|---|---|
| A bucket is public despite BPA | Only some settings enabled, or bucket-level override | All four, at account and organisation level |
| Storage bill rises after lifecycle rules | Minimum durations and transition requests | Transition only genuinely cold data |
| Deleted objects still billed | Versioning with no expiry rule | Expire noncurrent versions |
| `GET` returns 404 but data is "there" | Delete marker is the current version | Delete the marker to restore (§5.4) |
| Deletion request not fully satisfied | Old versions retained | Delete all versions; check replicas and logs (M10-L06) |

---

## 9. Security, privacy, reliability, cost

- **Security.** The four BPA settings plus a customer-managed key plus `aws:SourceVpce` is the practical exfiltration
  defence for stored data (L08, M10-L10).
- **Privacy.** Deletion means all versions, all replicas and all logs; versioning makes this harder and must be designed
  for (M10-L06, M10-L13).
- **Reliability.** Replication to a separate account is what converts durability into recoverability (§5.5).
- **Cost.** Lifecycle, noncurrent expiry and incomplete-upload cleanup are usually the three largest storage savings
  available (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which BPA setting governs public *policies*?
2. Why is row 6 in §7.1 public?
3. Which encryption option lets you revoke access by changing one thing?
4. What is the minimum billable duration for Standard-IA?
5. What does a `DELETE` do when versioning is on?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a configuration with only `RestrictPublicBuckets` enabled and explain the result.
2. Change the read volume in §7.2 and decide whether Bucket Keys are worth enabling.
3. Model your own corpus's lifecycle, including one full re-index per quarter.
4. Compute the cost of noncurrent versions for your own re-ingestion frequency.
5. Write the bucket policy that denies unencrypted PUTs and non-TLS requests.

### Exercise 3 — Challenge (~60 min)

1. Write the full bucket baseline from §5.6 as infrastructure code (L18).
2. Design the deletion procedure that satisfies a privacy request across versions, replicas and logs.
3. Design and **test** a restore for the "bad ingestion overwrote good documents" case.
4. Model the cost and the recovery-time objective of replication to a separate account.
5. Build a check that fails CI if any bucket lacks all four BPA settings or has ACLs enabled.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l10).)*

**Q1.** Which Block Public Access setting neutralises an existing public bucket policy?

- A. `RestrictPublicBuckets`
- B. `BlockPublicPolicy`
- C. `IgnorePublicAcls`
- D. `BlockPublicAcls`

**Q2.** In §7.1, why was "public policy, only ACL settings on" still public?

- A. The bucket had ACLs enabled
- B. `BlockPublicPolicy` only applies to new buckets
- C. The account-level settings were not applied
- D. The settings governing policies were off

**Q3.** How many of the eight configurations were public?

- A. Two
- B. Six
- C. Four
- D. Three

**Q4.** With SSE-S3, who can read an object?

- A. Anyone with `s3:GetObject`
- B. Only principals granted `kms:Decrypt`
- C. Only principals in the bucket owner's account
- D. Only principals allowed by the key policy

**Q5.** Which encryption option allows you to make objects unreadable by changing one policy?

- A. SSE-S3
- B. SSE-KMS with an AWS-managed key
- C. SSE-KMS with a customer-managed key
- D. Any server-side option, by rotating the key

**Q6.** What is the minimum billable duration trap?

- A. Objects cannot be deleted before the minimum period
- B. Objects deleted early are still billed for the minimum period
- C. Transitions are rejected before the minimum period
- D. Retrieval is unavailable during the minimum period

**Q7.** In §7.3, what did the three-tier lifecycle policy save over 36 months?

- A. 33%
- B. 50%
- C. 66%
- D. 90%

**Q8.** What cost does a full re-index from Glacier Instant Retrieval incur?

- A. None — retrieval is free for instant-access classes
- B. A per-GB retrieval charge each time
- C. Only the request charges
- D. A one-off restoration fee per bucket

**Q9.** With versioning on, what does `DELETE` without a version id do?

- A. Permanently removes the newest version
- B. Removes all versions of the object
- C. Fails unless MFA delete is satisfied
- D. Adds a delete marker; the versions remain and are billed

**Q10.** Which lifecycle rule do teams most often forget?

- A. Transitioning to Glacier Deep Archive
- B. Expiring noncurrent versions
- C. Transitioning after 30 days
- D. Enabling Intelligent-Tiering

**Q11.** Which loss mode does eleven nines of durability protect against?

- A. Media failure in the storage fleet
- B. Overwriting by a faulty ingestion job
- C. Deletion by a compromised credential
- D. Deletion of the entire bucket

**Q12.** What makes a copy of your data an actual backup?

- A. It is stored in a different storage class
- B. It is encrypted with a different key
- C. It is versioned
- D. It is in a separate account, not reachable by the credentials that destroyed the original

**Q13.** *(Written, rubric-graded.)* In under 150 words: you inherit a bucket holding a RAG corpus with customer
documents. List the settings you check first, and the two you would change immediately.

---

## 12. Revision notes

- **Four BPA settings**: `BlockPublicAcls` and `BlockPublicPolicy` prevent public grants being made; `IgnorePublicAcls`
  and `RestrictPublicBuckets` neutralise existing ones. **4 of 8** lab configurations were public; the trap is enabling
  only the ACL pair.
- **Defaults**: new buckets, access points and objects do not allow public access; disable ACLs with bucket-owner-enforced
  ownership.
- **Encryption**: only a **customer-managed KMS key** lets you revoke access by policy and gives a key-level audit trail.
  Bucket Keys cut request charges.
- **Lifecycle**: **66%** saving over 36 months, with **minimum billable durations** and **retrieval charges** as the two
  traps ($1,229 per full re-index in the lab).
- **Versioning**: `DELETE` adds a marker; old versions are still billed; always expire noncurrent versions and abort
  incomplete multipart uploads.
- **Durability ≠ backup**: none of the seven real loss modes is a media failure; a separate account is what makes a copy a
  backup.

---

## 13. Completion checklist

- [ ] All four BPA settings are enabled at organisation and account level; ACLs are disabled.
- [ ] Sensitive buckets use a customer-managed KMS key, with Bucket Keys enabled.
- [ ] Bucket policies deny unencrypted PUTs and non-TLS requests.
- [ ] Versioning is on, with noncurrent expiry and incomplete-upload cleanup.
- [ ] Lifecycle transitions match measured access patterns, including re-index reads.
- [ ] Anything I cannot lose is replicated to a separate account, and the restore has been tested.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon S3 User Guide — *Blocking public access to your Amazon S3 storage*: the four settings, defaults, and management
  at organisation, account and bucket level —
  <https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html> `[VERIFIED 2026-09-17]`
- Amazon S3 — storage classes and minimum billable durations; lifecycle configuration; versioning and delete markers;
  Object Lock; S3 Bucket Keys `[STABLE — check current pricing]`
- M11-L17 (KMS key policies and backups) and M11-L08 (`aws:SourceVpce`) `[STABLE]`
- M10-L06 (retention and deletion across versions and replicas) and M7-L16 (re-indexing and deletion propagation) `[STABLE]`

---

## 15. Next lesson

→ [M11-L11 — EC2 and the Compute Baseline](M11-L11-ec2-compute-baseline.md) turns to compute: instance families, what you
are actually paying for, and why the sizing question for AI workloads is different from the one for web servers.
