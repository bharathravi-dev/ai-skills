# M11-L01 — Cloud Computing and the Shared Responsibility Model

| | |
|---|---|
| **Lesson ID** | M11-L01 |
| **Difficulty** | 1 (Beginner) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | None (M10-L07 and M10-L16 give useful context) |

> **Nothing in this module requires an AWS account.** Every lab is a local simulator of the decision logic AWS applies, so
> you can learn the rules without spending money or risking a live account. Where a lesson describes console or CLI steps,
> they are marked and optional.

---

## 1. Learning objectives

1. **State** the shared responsibility model as a boundary per control, not as a slogan.
2. **Compute** how much responsibility each deployment model actually removes — and how much it never does.
3. **Name** the controls that are yours at every level of abstraction.
4. **Challenge** the common assumptions that create gaps nobody owns.
5. **Explain** what a provider's certification transfers to you and what it does not.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Cloud computing** | Renting compute, storage and services on demand, paying for use, with the provider operating the layers below your code. |
| **Shared responsibility model** | AWS's division of duties: AWS is responsible for security **of** the cloud; you are responsible for security **in** the cloud. |
| **IaaS** | Infrastructure as a service — you get a virtual machine (EC2) and own everything above the hypervisor. |
| **Managed service** | The provider operates the software; you configure and use it (RDS, Lambda, Bedrock). |
| **Serverless** | No servers for you to manage or patch; you pay per request or per unit of work. |
| **Control** | A specific thing that must be done to prevent a specific failure. |
| **Responsibility gap** | A control both parties assume the other handles. |
| **Inherited control** | A control the provider operates that you rely on and cite, but do not perform. |

---

## 3. Plain-language explanation

### 3.1 The model is a table, not a sentence

"AWS secures the cloud, you secure what's in it" is memorable and too vague to act on. §7.1 turns it into 18 controls ×
5 deployment models, and every cell is a different answer. That table is the useful form: for any given control, you can
point at who does it.

### 3.2 Moving up the stack removes about half

§7.2 computes the customer's share: **100%** on-premises, **78%** on EC2, **72%** for containers, **61%** for Lambda,
**47%** for a managed AI service. Going all the way from a data centre you own to a fully managed service removes **53%**
of the controls — real, and less than most people assume. The half that remains is the half Module 10 was about.

### 3.3 Six controls are yours no matter what you buy

§7.3: application code, application dependencies, identity and access policy, data classification, **what data you send
the service**, and monitoring your own failures. No purchasing decision moves any of them.

### 3.4 The gap is made of reasonable-sounding sentences

§7.4 tests eight beliefs: **5 are flatly wrong** and **3 are partly wrong**. "S3 is durable so our data is backed up",
"the provider is certified so we are compliant", "multi-AZ by default", "deleting the resource deletes the data". Each has
been said in a design review by someone competent.

### 3.5 Certification transfers three things

§7.5: of nine claims, **3 transfer** — physical controls, hypervisor isolation, the service's own availability
commitments. Your IAM policies, your bucket permissions, your classification, your retention, your authorization logic and
your evidence do not.

---

## 4. Analogy

**Renting a flat in a managed building.** The freeholder maintains the roof, the lifts, the fire alarm in the common parts
and the door to the street. You are responsible for locking your own door, what you keep inside, who you give keys to, and
whether you noticed the tap was running. A building with excellent security does not compensate for a key under the mat —
and "the building is secure" is not an answer to "who has your keys?".

### Where the analogy breaks

- **Your flat has one door; a cloud account has thousands**, created by anyone with permission, in seconds, from a script.
  That is why identity policy (L04) is the control that matters most (§5.3).
- **A landlord cannot see inside your flat; your provider can see your API calls** and, for some services, your data. What
  you *send* is therefore a control in its own right (§5.3, M10-L11).

---

## 5. Detailed technical explanation

### 5.1 Security "of" vs "in" the cloud

AWS states the boundary as: AWS is responsible for **security of the cloud** — hardware, the global infrastructure,
facilities, and the software of managed services; the customer is responsible for **security in the cloud** — data,
identity and access management, operating-system and network configuration where applicable, and encryption choices
`[STABLE — AWS's own framing]`.

The boundary **moves per service**. For EC2, you patch the guest OS; for RDS, AWS patches the database engine on a
schedule you choose; for Lambda, there is no OS for you to see; for Bedrock, you do not operate the model at all. Read the
specific service's documentation rather than generalising from another service.

### 5.2 Deployment models and what they remove

`[REAL, computed]` §7.2 — 100% / 78% / 72% / 61% / 47% customer share.

| Model | You stop doing | You still do |
|---|---|---|
| **EC2 / IaaS** | Racking, power, hardware, hypervisor | Guest OS patching, AMI hygiene, network config, everything above |
| **Containers (ECS/Fargate)** | Host OS patching, capacity management | Base image currency, image scanning, task role permissions |
| **Lambda** | Base image, runtime patching, scaling | Dependencies, code, permissions, concurrency and cost limits |
| **Managed AI (Bedrock)** | Model hosting, serving, scaling | Prompt and data handling, IAM, guardrails, evaluation, what you send |

Each step up removes operational toil and adds a **configuration surface**. The failures move from "we did not patch" to
"we misconfigured" — which is why the rest of this module is mostly about configuration.

### 5.3 The six that never move

`[REAL, computed]` §7.3.

| Always yours | Because |
|---|---|
| Application code | Nobody else wrote it |
| Application dependencies | The provider patches its runtime, not your `requirements.txt` (M2-L17) |
| Identity and access policy | Only you know who should do what (L04, M10-L07) |
| Data classification | Only you know what the data is (M10-L06) |
| **What data you send the service** | Every managed service is an egress decision (M9-L12, M10-L11) |
| Monitoring your own failures | The provider watches its platform; your errors are invisible to it (L16) |

The fifth deserves emphasis in an AI course: choosing to send a customer's transcript to a hosted model is a data-transfer
decision made in code, usually without a review. It is exactly the kind of control that nothing in the platform will make
for you.

### 5.4 Closing the gap

`[REAL, classified]` §7.4 — 5 wrong, 3 partly wrong.

| Belief | The specific correction |
|---|---|
| "S3 is durable, so we have backups" | Durability protects against media failure. A `DeleteObject` or an overwrite is not media failure — you need versioning, lifecycle rules and a tested restore (L10, L17) |
| "Encrypted at rest, so we are covered" | Encryption is only as strong as the key policy: who can decrypt, and is that logged? (L17) |
| "Managed, so patching is handled" | The runtime, yes. Your dependencies, no (M2-L17) |
| "They are certified, so we are compliant" | Their certification covers their layer (§5.5) |
| "Multi-AZ by default" | True for some services, a paid choice for most (L02, L14) |
| "They monitor our application" | They monitor their platform (L16) |
| "Deleting the resource deletes the data" | Snapshots, backups, replicas and logs may survive (M10-L06, M10-L13) |
| "Private subnet means unreachable" | Egress, VPC endpoints, peering and permissive security groups all exist (L07, L08) |

The diagnostic question: **which specific failure does the provider prevent, and which do I?** "Is it managed?" does not
have an actionable answer.

### 5.5 What a certification transfers

`[REAL, classified]` §7.5 — 3 of 9.

Providers publish audit reports (on AWS, through **AWS Artifact**) covering their controls. Those reports are an **input**
to your evidence: you *inherit* physical security, hypervisor isolation and the service's operational controls, and you
cite them. Everything configured by you — permissions, public access, classification, retention, application
authorization — remains yours to implement and to evidence (M10-L11, M10-L16).

The practical consequence for a design review: separate **inherited** controls (cite the provider) from **implemented**
controls (show your configuration and a test) in the same document. Reviewers who cannot see which is which tend to
assume the wrong one.

### 5.6 Why cloud at all

Not as advocacy — as the trade-off you are accepting:

| Gain | Cost |
|---|---|
| Elastic capacity; no capital purchase | Variable spend that can run away (L06, M8-L15) |
| Managed operations for common software | Configuration surface, and provider-specific coupling (M10-L11) |
| Global footprint and redundancy on request | Redundancy is a paid choice, not a default (L02) |
| Fast provisioning | Fast provisioning of mistakes, by anyone with permission (L04) |

### 5.7 Assumptions and limitations

- The 18-control table is a teaching simplification; real boundaries are per service and are documented per service.
- The percentages depend entirely on which controls you list. They are a way of thinking, not a benchmark.
- This lesson covers the model, not AWS's services; those start in L02.

---

## 6. Worked example — the bucket nobody owned

**The situation.** A team moved a document pipeline to AWS. The design review asked about security; the answer was "it's
all managed — S3 and Lambda, nothing to patch". That was true and irrelevant.

**What happened.**

1. An S3 bucket was created by a script with a permissive policy so that a partner integration "just worked". Nobody
   owned bucket policy as a control (§5.3 — identity and access policy is always yours).
2. Documents were classified "internal" in a spreadsheet and never mapped to the bucket, so lifecycle rules were never
   applied (§5.3 — classification).
3. A Lambda's `requirements.txt` pinned a library from two years earlier. "Serverless, so patching is handled" (§5.4).
4. A quarterly review cited the provider's certification as the security evidence for the whole pipeline (§5.5).
5. The gap was found by a customer's security questionnaire, which asked who could read the bucket and what the retention
   period was. Neither question had an owner.

| # | Assumed handled | Actually yours | Lesson |
|---|---|---|---|
| 1 | Bucket permissions | Yours, always | L04, L10 |
| 2 | Data classification and retention | Yours, always | M10-L06 |
| 3 | Dependency patching | Yours, always | M2-L17 |
| 4 | Compliance evidence | Inherited ≠ implemented | §5.5, M10-L16 |
| 5 | Noticing any of it | Yours, always | L16 |

**The general rule.** **A managed service removes work, never accountability. Ask per control, not per service.**

---

## 7. Practical activity

**File:** [`labs/m11/l01_shared_responsibility.py`](../../labs/m11/l01_shared_responsibility.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l01_shared_responsibility.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. WHO IS RESPONSIBLE FOR WHAT?
============================================================================
  control                                   on-prem     EC2/IaaS   containers       Lambda   managed AI
  physical data-centre security                   C            P            P            P            P
  hardware and network fabric                     C            P            P            P            P
  hypervisor / isolation                          C            P            P            P            P
  host OS patching                                C            C            P            P            P
  container base image patching                   C            C            C            P            P
  runtime / language patching                     C            C            C            S            P
  application code                                C            C            C            C            C
  application dependencies                        C            C            C            C            C
  network segmentation (VPC, SGs)                 C            C            C            C            S
  encryption in transit                           C            S            S            S            P
  encryption at rest (key policy)                 C            S            S            S            S
  identity and access policy (IAM)                C            C            C            C            C
  data classification                             C            C            C            C            C
  what data you send the service                  C            C            C            C            C
  retention and deletion                          C            C            C            C            S
  backup and restore testing                      C            C            C            C            S
  availability design (multi-AZ)                  C            C            C            S            S
  monitoring your own failures                    C            C            C            C            C

  P = provider   C = customer   S = shared (each has a distinct part)

============================================================================
2. HOW MUCH IS STILL YOURS?
============================================================================
  model           provider   shared  customer   your share
  on-prem                0        0        18        100%
  EC2/IaaS               3        2        13         78%
  containers             4        2        12         72%
  Lambda                 5        4         9         61%
  managed AI             7        5         6         47%

  moving from on-prem to a managed AI service removes 53% of the controls from
  your plate. It does not remove the rest, and the rest is where the incidents
  in Module 10 came from.

============================================================================
3. WHAT IS ALWAYS YOURS?
============================================================================
  yours in EVERY model (6):
    - application code
    - application dependencies
    - identity and access policy (IAM)
    - data classification
    - what data you send the service
    - monitoring your own failures

  the provider's in every cloud model (3):
    - physical data-centre security
    - hardware and network fabric
    - hypervisor / isolation

  The first list is the one to memorise. Access policy, data classification,
  what you send, your own code and whether you noticed it break are yours at
  every level of abstraction you will ever buy (M10-L07, M10-L14).

============================================================================
4. THE ASSUMPTION GAP
============================================================================
  common belief                                          true?   what is actually the case
  'S3 is durable, so our data is backed up'                 no   durability is not versioning; a delete or overwrite still destroys it
  'The provider encrypts at rest, so we are covered'    partly   who holds the key, and who can decrypt, is your key policy (M11-L17)
  'Managed service, so patching is handled'             partly   the runtime is; your dependencies are not (M2-L17)
  'The provider is certified, so we are compliant'          no   their certification covers their layer only (section 5)
  'Multi-AZ by default'                                     no   for some services; for most it is a choice you make and pay for
  'The provider monitors our application'                   no   they monitor their platform; your errors are yours (M11-L16)
  'Deleting the resource deletes the data'                  no   backups, snapshots, logs and replicas may survive (M10-L06)
  'Private subnet means unreachable'                    partly   egress, peering, endpoints and misconfigured SGs all exist (M11-L08)

  flatly wrong: 5/8   partly wrong: 3/8
  Every one of these is a sentence somebody has said in a design review. The
  test is not 'is it managed?' but 'which specific failure does the provider
  prevent, and which do I?'

============================================================================
5. WHAT A PROVIDER'S CERTIFICATION TRANSFERS
============================================================================
  claim                                           transfers to you?
  the data centre's physical controls                           yes
  the hypervisor's tenant isolation                             yes
  the service's own availability commitments                    yes
  your IAM policies being least-privilege                        NO
  your bucket not being public                                   NO
  your data classification being correct                         NO
  your retention actually deleting things                        NO
  your application's authorization logic                         NO
  your evidence that any of the above works                      NO

  transfers: 3/9
  A provider's audit report is an input to YOUR evidence, not a substitute for
  it (M10-L11, M10-L16). You inherit their controls at their layer and you
  still have to demonstrate yours.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every share, count and classification above is computed from the
  responsibility table encoded in this script.

  ILLUSTRATIVE: the table is a teaching simplification. Real boundaries are
  per service and are stated in the provider's own shared-responsibility
  documentation -- read it for the services you actually use.

  NOT SHOWN: contractual terms, audit report scopes, and the specific
  responsibility boundaries of individual AWS services (M11-L10 onwards).

Done.
```

### 7.3 Reading the result

**Section 2's last column is the surprise for most readers**: a fully managed AI service still leaves you **47%** of the
controls.

**Section 3's six-item list** is worth memorising; it is the answer to "but it's managed".

**Section 4** is a design-review script. Ask these eight questions and you will find at least one gap.

---

## 8. Common mistakes and troubleshooting

1. **Treating the model as a slogan.** §5.1 — make it a table with a name against each row.
2. **Generalising one service's boundary to another.** EC2 and Lambda differ completely.
3. **Assuming durability means backup.** §5.4 — a delete is not a media failure.
4. **Assuming encryption means confidentiality.** The key policy decides who can read it (L17).
5. **Citing a provider certification as your own evidence.** §5.5 — inherited ≠ implemented.
6. **Forgetting that "what we send" is a control.** §5.3 — especially for hosted models (M10-L11).
7. **No owner for configuration controls.** Managed services fail by misconfiguration, and misconfiguration needs an owner.

| Symptom | Likely cause | Fix |
|---|---|---|
| Security questions in a customer review have no owner | Controls never enumerated per service | Build the §7.1 table for your stack, with names |
| Data lost despite a durable store | Backup confused with durability | Versioning, lifecycle, tested restore (L10, L17) |
| Outdated libraries in a serverless app | "Managed means patched" | Dependency policy and scanning in CI (M2-L17, L18) |
| Outage nobody noticed | Provider monitoring assumed | Your own alarms on your own metrics (L16) |
| Compliance evidence is a vendor PDF | Inherited/implemented not separated | Split the evidence table in two columns (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Misconfiguration is the dominant cloud failure mode; the controls that prevent it are all in the customer
  column (L04, L07, L10).
- **Privacy.** "What data you send" is yours at every level — the single most important row for an AI system (M10-L06).
- **Reliability.** Availability is a design choice you pay for, not a property of the cloud (L02, L14).
- **Cost.** Elasticity means spend responds to bugs as readily as to demand; budgets and alarms are part of the
  responsibility you keep (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name the six controls that are yours in every model.
2. What is the customer's share for Lambda in §7.2, and why is it not lower?
3. Which of the eight beliefs in §7.4 have you heard said aloud?
4. Why does "the provider is certified" not make you compliant?
5. Give one control that is *shared* and say what each party's part is.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add three controls specific to an AI system (guardrail config, evaluation, prompt storage) and recompute.
2. Add a "SaaS" column where you own only data, access and what you send; compute the share.
3. Write your own stack's responsibility table with an owner's name in each customer cell.
4. For each `S` row, write the two sentences describing each party's part.
5. Take one belief from §7.4 and find out whether it is true for a service you actually use.

### Exercise 3 — Challenge (~60 min)

1. Produce the inherited-vs-implemented evidence table for one system, with a citation or a test per row.
2. Find one responsibility gap in a system you work on, and assign it an owner.
3. Write the design-review question list from §5.4 and use it on the next design.
4. Estimate what moving one component from EC2 to a managed service would remove, and what it would add.
5. Map the six always-yours controls to Module 10 lessons and identify your weakest.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l01).)*

**Q1.** How does AWS state the shared responsibility boundary?

- A. Security of applications versus security of data
- B. Security *of* the cloud versus security *in* the cloud
- C. Security of infrastructure versus security of compliance
- D. Security of the account versus security of the region

**Q2.** In §7.2, what was the customer's share of controls for a managed AI service?

- A. 78%
- B. 61%
- C. 72%
- D. 47%

**Q3.** Which control is yours in every deployment model?

- A. What data you send the service
- B. Host operating-system patching
- C. Hypervisor isolation
- D. Encryption in transit

**Q4.** What changes as you move up the stack?

- A. Accountability transfers to the provider
- B. Configuration surface disappears
- C. Operational toil falls and configuration surface grows
- D. Data classification becomes the provider's responsibility

**Q5.** Why is "S3 is durable, so our data is backed up" wrong?

- A. Durability protects against media failure, not deletion or overwriting
- B. Durability applies only to versioned buckets
- C. Durability guarantees are excluded from the service agreement
- D. Durability is measured per region, not per object

**Q6.** Why is "managed service, so patching is handled" only partly true?

- A. Managed services are patched on a delayed schedule
- B. Patching requires a maintenance window you must approve
- C. Only security patches are applied automatically
- D. The runtime is patched; your dependencies are not

**Q7.** In §7.5, how many of the nine claims transferred to you from a provider's certification?

- A. All nine
- B. Six
- C. Three
- D. None

**Q8.** What does inheriting a control mean in a design review?

- A. The control no longer needs to appear in your documentation
- B. You cite the provider's evidence rather than performing the control
- C. You perform the control and the provider verifies it
- D. The control is shared equally between both parties

**Q9.** Which question is actionable in a design review?

- A. Is this service managed?
- B. Is the provider certified?
- C. Does this service have an SLA?
- D. Which specific failure does the provider prevent, and which do I?

**Q10.** Why is "what data you send the service" called out as a control?

- A. It is a data-transfer decision made in code, usually without review
- B. Providers charge per byte transferred
- C. It determines which region processes the request
- D. It is the only control that applies to serverless systems

**Q11.** What replaces patching failures as you adopt managed services?

- A. Capacity failures
- B. Misconfiguration failures
- C. Hardware failures
- D. Dependency conflicts

**Q12.** A private subnet is *not* a guarantee of unreachability because —

- A. subnets are shared between accounts by default
- B. private subnets still receive public IP addresses
- C. egress, endpoints, peering and permissive security groups exist
- D. the provider retains administrative network access

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team proposes replacing a self-hosted model with a managed
AI service, arguing it removes the security work. Explain what it actually removes and what it does not.

---

## 12. Revision notes

- **The model is a table**: 18 controls × 5 models, one answer per cell.
- **Customer share**: on-prem **100%**, EC2 **78%**, containers **72%**, Lambda **61%**, managed AI **47%** — a **53%**
  reduction end to end, not 100%.
- **Six controls never move**: code, dependencies, IAM policy, data classification, what you send, your own monitoring.
- **Eight common beliefs**: **5 flatly wrong**, **3 partly wrong** — durability ≠ backup, certified ≠ compliant, managed
  ≠ patched, private ≠ unreachable.
- **Certification transfers 3 of 9**: physical, hypervisor, the service's own commitments. Yours stay yours.
- **The diagnostic question**: which specific failure does the provider prevent, and which do I?

---

## 13. Completion checklist

- [ ] I can state the boundary as a per-control table rather than a slogan.
- [ ] I can name the six controls that are mine in every model.
- [ ] I can correct all eight beliefs in §7.4 with a specific mechanism.
- [ ] I separate inherited from implemented controls in evidence.
- [ ] I ask "which failure does the provider prevent?" in design reviews.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS Shared Responsibility Model — "security *of* the cloud" vs "security *in* the cloud"; AWS Artifact for audit
  reports — <https://aws.amazon.com/compliance/shared-responsibility-model/> `[STABLE]`
- M10-L07 (access control as a governance control) and M10-L16 (inherited vs implemented evidence) `[STABLE]`
- M10-L06 (data classification, retention, deletion) and M10-L11 (supplier assessment) `[STABLE]`
- M2-L17 (dependency management) and M2-L20 (containers) — the parts that stay yours `[STABLE]`

---

## 15. Next lesson

→ [M11-L02 — Regions, Availability Zones and Placement Decisions](M11-L02-regions-availability-zones.md) takes the first
control in the customer column — where your data and compute physically live — and turns it into a decision with latency,
cost, resilience and legal consequences.
