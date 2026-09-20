# Module 11 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple choice, a reason
each distractor fails.

> Module 11 quiz options are written to similar lengths with a balanced, unpatterned answer distribution, and carry no
> inline explanation of the correct choice. All rationale lives here.
>
> **Scope note.** Every lab in this module is a local simulator: no AWS account, no network, no spend. Where an answer
> cites a figure, it is the figure the lab computes. Where it cites AWS behaviour, the lesson's §14 records whether it was
> verified against documentation and when — quotas and prices change, so re-check before relying on a number in
> production.

| Lesson | Jump to |
|---|---|
| M11-L01 Cloud Computing and the Shared Responsibility Model | [↓](#m11-l01) |
| M11-L02 Regions, Availability Zones and Placement Decisions | [↓](#m11-l02) |
| M11-L03 Account Setup, Root User Protection and MFA | [↓](#m11-l03) |
| M11-L04 IAM: Identities, Policies, Roles and Least Privilege | [↓](#m11-l04) |
| M11-L05 Temporary Credentials, STS and the CLI | [↓](#m11-l05) |
| M11-L06 Billing, Budgets and Cost Allocation | [↓](#m11-l06) |
| M11-L07 VPCs, Subnets, Route Tables and Security Groups | [↓](#m11-l07) |
| M11-L08 Public vs Private Access, NAT and Endpoints | [↓](#m11-l08) |
| M11-L09 DNS, TLS and Load Balancing | [↓](#m11-l09) |
| M11-L10 S3: Buckets, Permissions, Encryption, Lifecycle | [↓](#m11-l10) |
| M11-L11 EC2 and the Compute Baseline | [↓](#m11-l11) |
| M11-L12 Containers on AWS: ECR, ECS and Fargate | [↓](#m11-l12) |
| M11-L13 Lambda and API Gateway | [↓](#m11-l13) |
| M11-L14 RDS and DynamoDB | [↓](#m11-l14) |
| M11-L15 SQS, SNS and EventBridge | [↓](#m11-l15) |
| M11-L16 CloudWatch and CloudTrail | [↓](#m11-l16) |
| M11-L17 KMS, Secrets Manager, Backups and Disaster Recovery | [↓](#m11-l17) |
| M11-L18 Infrastructure as Code, CI/CD and Rollback | [↓](#m11-l18) |

---

<a id="m11-l01"></a>
## M11-L01 — Cloud Computing and the Shared Responsibility Model

**Answers: B · D · A · C · A · D · C · B · D · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | AWS's own framing: security **of** the cloud (theirs) versus **in** the cloud (yours). **A**, **C** and **D** are invented splits. |
| 2 | **D** | 47% — see §7.2. **A** is EC2, **C** containers, **B** Lambda. |
| 3 | **A** | One of the six that never move. **B** moves at containers, **C** is the provider's, **D** is shared. |
| 4 | **C** | Toil falls, configuration surface grows. **A** is false — accountability never transfers; **B** is backwards; **D** is always yours. |
| 5 | **A** | Durability addresses media failure; a `DeleteObject` is not media failure. **B**, **C** and **D** misdescribe the guarantee. |
| 6 | **D** | The provider patches the runtime, not your `requirements.txt`. **A**, **B** and **C** invent mechanisms. |
| 7 | **C** | Physical controls, hypervisor isolation, and the service's own commitments. **A**, **B** and **D** contradict §7.5. |
| 8 | **B** | You cite their evidence instead of performing the control — and it still appears in your documentation, so **A** is wrong. **C** inverts it; **D** is a *shared* control, a different category. |
| 9 | **D** | It names a failure and an owner. **A**, **B** and **C** have answers that do not change any decision. |
| 10 | **A** | It is an egress decision made in code, usually unreviewed — the row that matters most for AI. **B** is incidental; **C** and **D** are false. |
| 11 | **B** | Failures move from "we did not patch" to "we misconfigured". **A**, **C** and **D** are reduced, not increased, by managed services. |
| 12 | **C** | Egress, endpoints, peering and permissive groups all exist (L08). **A** and **B** are false; **D** is not the relevant risk. |

**Q13 rubric (5 marks).** One mark each for: **what it removes** — model hosting, serving, scaling, and the host patching
beneath it (§5.2); **what it does not** — the six always-yours controls, especially IAM, data classification and *what you
send* (§5.3); **the new surface** — configuration and permissions become the failure mode (§5.2); **evidence** —
inherited versus implemented, and that their certification is an input not a substitute (§5.5); and **a concrete next
step**, e.g. building the per-control table with named owners. An answer that just says "it's still our data" scores 1.

---

<a id="m11-l02"></a>
## M11-L02 — Regions, Availability Zones and Placement Decisions

**Answers: C · A · D · B · D · C · A · B · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | One or more discrete data centres with independent power, cooling and networking. **A** understates it; **B** describes an organisational unit; **D** describes replication, not an AZ. |
| 2 | **A** | 88.5 ms. **B** is Frankfurt, **D** Ireland, **C** Sydney. |
| 3 | **D** | The floor is paid once per **sequential** round trip, so six hops pay it six times. **A**, **B** and **C** invent mechanisms. |
| 4 | **B** | 201.0 → 200.0 ppm: region failure now dominates. **A** overstates; **C** and **D** are unrelated. |
| 5 | **D** | The application's 2,000 ppm dwarfed the infrastructure term. **A** and **B** are not what the lab modelled; **C** is a §7.3 constraint, not the availability reason. |
| 6 | **C** | Residency is a gate applied first (M10-L06). **A** and **B** invert the order; **D** waits until it is too late. |
| 7 | **A** | Region parity for services, models and features. **B**, **C** and **D** are true but rarely block a design. |
| 8 | **B** | $960/year at $0.01/GB. **A** is same-AZ, **C** cross-region, **D** internet egress. |
| 9 | **A** | Chatty pairs should not cross an AZ boundary per request. **B** is cross-AZ *by design* — that is what you bought; **C** and **D** are not per-request traffic. |
| 10 | **D** | Multi-AZ (cheap, large), then the application (the dominant term), then multi-region. **A**, **B** and **C** invert or conflate the steps. |
| 11 | **B** | The same bug deploys to every region. **A**, **C** and **D** do not address the failure mode. |
| 12 | **C** | Moving later is a migration, so the reasoning must be reviewable. **A** and **B** are administrative; **D** misreads what recording a runner-up does. |

**Q13 rubric (5 marks).** One mark each for: **residency as a gate** — UK/EU data-protection questions answered before
architecture (§5.4); **region parity** — is the model available where the data must stay (§5.4); **latency arithmetic** —
88.5 ms × sequential hops from London (§5.2); **cost** — cross-region transfer and duplicated infrastructure (§5.5); and
**the decision record** — gates, the comparison, the runner-up, and that the choice is hard to reverse (§5.6). An answer
that argues only from latency scores 2.

---

<a id="m11-l03"></a>
## M11-L03 — Account Setup, Root User Protection and MFA

**Answers: B · C · D · A · D · B · C · D · A · A · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | The classic lockout: only root can restore an administrator's revoked permissions. **A**, **C** and **D** are all ordinary IAM tasks — **C** notably does *not* require root. |
| 2 | **C** | Nine of sixteen. **A**, **B** and **D** contradict §7.1. |
| 3 | **D** | Root is the account's own identity and the last-resort recovery path, so no policy constrains it. **A**, **B** and **C** invent mechanisms. |
| 4 | **A** | It changes the likelihood of theft and the credential's lifetime — not its reach, which is why **C** is wrong. **B** and **D** are unchanged. |
| 5 | **D** | 14.81%. **A** is a reused password, **B** TOTP, **C** phishing-resistant. |
| 6 | **B** | A one-time code can be relayed to a fake site in real time; an origin-bound credential cannot. **A**, **C** and **D** are addressed by the password or by other controls. |
| 7 | **C** | Cross-account access needs explicit grants on both sides, and no single policy edit removes the boundary. **A** is false; **B** is false; **D** is a consequence, not the reason. |
| 8 | **D** | 35%. **A** is single-account, **B** prod-separated. **C** is not a figure in §7.4. |
| 9 | **A** | SCPs set a **maximum**; they grant nothing, which is why **B** is wrong. **C** and **D** describe other mechanisms. |
| 10 | **A** | Nine of ten items produce no symptom until they matter. **B**, **C** and **D** are not why it must be a checklist. |
| 11 | **C** | Every use is an incident until proven otherwise. **A**, **B** and **D** are too slow or too weak. |
| 12 | **B** | With Organizations, member accounts can have **no root credentials at all**. **A** and **C** still leave a credential; **D** does not apply to root. |

**Q13 rubric (5 marks).** One mark each for: **root hygiene** — MFA, no access keys, monitored email, recovery contacts
(§5.5); **human access** — federation instead of IAM users, and a check for long-lived keys (§5.2, L05); **detection** —
CloudTrail in all regions to a separate account, plus budget alerts (§5.5); **blast radius** — account layout, SCPs, and
whether dev and prod share an account (§5.4); and **recovery** — is there a second administrator, and has break-glass been
rehearsed (§5.6). Listing only "check MFA" scores 1.

---

<a id="m11-l04"></a>
## M11-L04 — IAM: Identities, Policies, Roles and Least Privilege

**Answers: B · C · D · B · A · C · D · C · A · B · D · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Deny by default. **A** is false even in-account; **C** describes a step, not an outcome; **D** invents an exception. |
| 2 | **C** | An explicit `Deny` cannot be overridden. **A** and **B** misstate the model — order is irrelevant; **D** is wrong because deny wins over any allow. |
| 3 | **D** | Union: an allow in either suffices (AWS's documented rule). **A** describes boundaries and SCPs; **B** and **C** invent precedence. |
| 4 | **B** | It caps the maximum an identity policy can grant. **A** is backwards — boundaries never grant; **C** and **D** are false. |
| 5 | **A** | The SCP denied `iam:*` only, so S3 actions remained. **C** contradicts the output; **B** overstates; **D** understates — delete was allowed too. |
| 6 | **C** | `s3:*Object` matched 4 actions including `DeleteObject`. **A** and **B** matched no dangerous actions; **D** contradicts §7.3. |
| 7 | **D** | It is the permission to grant permissions, including publicly. **A** depends on the resource ARN; **B** and **C** are false. |
| 8 | **C** | As a ratio of granted to used actions. **A**, **B** and **D** are proxies that a policy can satisfy while remaining over-broad. |
| 9 | **A** | It lets the principal hand any role — including an administrator role — to a service it creates. **B**, **C** and **D** describe other actions. |
| 10 | **B** | It stops a trusted vendor being tricked into acting for another customer — the confused deputy. **A**, **C** and **D** are other controls. |
| 11 | **D** | Both sides must allow. **A** and **B** are each half; **C** confuses SCPs with the requirement. |
| 12 | **A** | `ListBucket` acts on the bucket ARN, `GetObject` on the object ARN. **B** concerns public access; **C** is false; **D** is a different action. |

**Q13 rubric (5 marks).** One mark each for: **expanding the wildcard** against the real action list and naming the
dangerous ones, especially `Put*Policy` / `Put*Acl` (§5.4); **resource scoping** — named ARNs rather than `*`;
**conditions** where tenancy or transport matters (§5.3); **the generate-from-usage loop** — start broad in a
non-production account, generate from CloudTrail, review the diff (§5.5); and **a concrete alternative** written out, not
just a refusal. "Tighten it later" without a mechanism scores 1 — the lesson's point is that later does not arrive.

---

<a id="m11-l05"></a>
## M11-L05 — Temporary Credentials, STS and the CLI

**Answers: B · C · D · A · D · B · C · B · D · A · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Access key id, secret, **and session token** — omitting the third causes signature errors. **A** is the long-lived pair; **C** and **D** describe other schemes. |
| 2 | **C** | The leak was found in 72 hours, far inside a 90-day window, so the exposure was identical. **A** contradicts the scenario; **B** and **D** are false. |
| 3 | **D** | 900 seconds. **A** and **B** are below the minimum; **C** is the default, not the minimum. |
| 4 | **A** | Role chaining caps the session at one hour. **B** is the API maximum without chaining; **C** is overridden by the chaining rule; **D** is the minimum. |
| 5 | **D** | The shared credentials file sits above IMDS in the chain. **A** is the common misconception; **B** and **C** are false. |
| 6 | **B** | `get-caller-identity` answers "which principal am I?" before any policy debugging. **A** is useful later; **C** is partial; **D** is for after the fact. |
| 7 | **C** | OIDC federation removes the stored key entirely. **A** and **D** store long-lived keys; **B** is never acceptable. |
| 8 | **B** | 66% of key-days came from the 38% of keys older than a year. **A** is the count share; **C** and **D** are other buckets. |
| 9 | **D** | The `PUT` for a session token is what a forged fetch cannot perform. **A**, **B** and **C** are not IMDSv2 mechanisms. |
| 10 | **A** | A hop limit of 1 stops a container on a bridge network reaching the host's IMDS. **B**, **C** and **D** are unrelated. |
| 11 | **C** | The session name appears in CloudTrail and is how an action is attributed to a person. **A**, **B** and **D** are false. |
| 12 | **A** | Lifetime limits the **window**, not the reach — which is L04's job, so **B** is wrong. **C** and **D** are unaffected. |

**Q13 rubric (5 marks).** One mark each for: **the arithmetic** — rotation does not shorten the window when detection is
faster than the period (§7.1); **replace rather than rotate** — roles on compute, OIDC for CI, Identity Center for people
(§5.4); **detection** — report keys by age and last use, alarm on IAM-user credentials where a role is expected (§5.4,
L16); **IMDSv2** as the related second path (§5.6); and **a migration plan** with a documented exception process for keys
that genuinely cannot be removed. Accepting the 60-day policy as the answer scores 1.

---

<a id="m11-l06"></a>
## M11-L06 — Billing, Budgets and Cost Allocation

**Answers: D · B · A · C · B · D · C · A · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | Billing data lags and budgets evaluate periodically, so the alert describes spend already incurred. **A** and **C** are false; **B** is not the mechanism. |
| 2 | **B** | $13,440 over 21 hours. **C** is after metering, **A** after the alert, **D** after someone read it. |
| 3 | **A** | A cap makes spending impossible by failing something. **B** is not generally true; **C** is one implementation; **D** describes routing. |
| 4 | **C** | In-application limits are cheapest, most precise and cause the least collateral damage. **A** is last and non-production only; **B** and **D** are account-wide blunt instruments. |
| 5 | **B** | It is a self-inflicted outage on a spend trigger. **A** is false; **C** is false; **D** misses that production is usually the largest spend. |
| 6 | **D** | $12,600. **C** is 30% coverage, **B** 60%, **A** 97%. |
| 7 | **C** | The untagged resources are precisely the ones whose owner has left. **A** is false; **B** is a real but secondary effect; **D** is a hygiene issue. |
| 8 | **A** | 86% — input plus output tokens. **B** and **C** are the two components separately; **D** is everything else. |
| 9 | **D** | The model dominates, so context, retrieval, caching and routing are the levers. **A**, **B** and **C** together are 14%. |
| 10 | **B** | Your own usage counter is near-real-time; billing data is not. **A**, **C** and **D** all inherit the billing lag. |
| 11 | **C** | They group spend by owner, environment and service in cost reports. **A** is a tag *policy* or SCP; **B** and **D** are other controls. |
| 12 | **A** | A spend anomaly is often the first visible sign of compromised credentials. **B**, **C** and **D** are true-ish but not the reason. |

**Q13 rubric (5 marks).** One mark each for: **what the alert does** — tells you after the fact, with a measurable lag
(§5.1); **what it does not** — stop anything, or attribute the spend (§5.1, §5.3); **in-application caps** — `max_tokens`,
step limits, per-run ceiling (§5.2, M8-L15); **a near-real-time signal** on your own counter with alerting to a rota, not
a mailbox (§5.1); and **tagging enforced at creation** so the spend has an owner (§5.3). Naming only "lower the threshold"
scores 1.

---

<a id="m11-l07"></a>
## M11-L07 — VPCs, Subnets, Route Tables and Security Groups

**Answers: B · C · D · C · A · D · B · C · D · A · A · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Five per subnet. **A**, **C** and **D** contradict the documented behaviour. |
| 2 | **C** | 16 addresses minus 5 reserved = 11. **A** is the total, **B** the classic non-AWS answer, **D** is invented. |
| 3 | **D** | A subnet is *defined* as being in exactly one AZ. **A**, **B** and **C** are false. |
| 4 | **C** | The ranges overlap, so peering requires re-addressing. **A**, **B** and **D** invent exceptions. |
| 5 | **A** | Longest prefix match: the `/22` beats the `/16`. **B** is the common misconception; **C** and **D** are false. |
| 6 | **D** | A route to an internet gateway — routing, not a setting. **A** is a consequence; **B** and **C** are filters, not routing. |
| 7 | **B** | Security groups are stateful. **A**, **C** and **D** misdescribe the mechanism. |
| 8 | **C** | The missing ephemeral return rule, because NACLs are stateless. **A**, **B** and **D** are real features, not the common bug. |
| 9 | **D** | Allow-only: anything not allowed is denied, so **A** is wrong. **B** is false for outbound and irrelevant; **C** is wrong — they attach to interfaces. |
| 10 | **A** | It grants access to a role, and membership updates itself. **B** is immaterial; **C** and **D** are false. |
| 11 | **A** | 263 hosts. **B** is the app-subnet rule, **C** is the SG reference, **D** is one component of the total. |
| 12 | **B** | Subnets cannot be resized, so growth needs contiguous free space. **A** is false; **C** is a real limit but not the reason; **D** is invented. |

**Q13 rubric (5 marks).** One mark each for: **a /16 with room left** — allocation from a central register, >50% spare
(§5.1–§5.2); **per-AZ subnets per tier**, with the app tier sized for the deployment peak, not steady state (§5.1, §6);
**public vs private by routing** — load balancer public, everything else private (§5.3); **database inbound rules using a
security-group reference**, not a CIDR (§5.6); and **restricted egress** for anything handling untrusted input (§5.4). An
answer with no numbers, or one that puts the database in a public subnet, scores 1.

---

<a id="m11-l08"></a>
## M11-L08 — Public vs Private Access, NAT and Endpoints

**Answers: A · B · D · C · D · B · C · D · B · A · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | A public IP with an internet gateway is the only inbound-capable path. **B**, **C** and **D** are outbound only. |
| 2 | **B** | NAT gateway or an egress proxy. **A** exposes it inbound; **C** makes the subnet public; **D** does not reach the internet. |
| 3 | **D** | Gateway endpoints have no hourly or per-GB charge. **A**, **B** and **C** describe interface endpoints or NAT. |
| 4 | **C** | $202/month. **B** is the full processing charge, **A** and **D** are hourly components. |
| 5 | **D** | An AZ failure must not remove egress, and cross-AZ traffic is charged. **A** is not the usual driver; **B** is false; **C** is false. |
| 6 | **B** | Another account's S3 bucket — reachable under every design. **A** and **C** are blocked once NAT is removed; **D** is blocked in the strictest design. |
| 7 | **C** | Your bucket and an attacker's are at the same service endpoint. **A**, **B** and **D** are false. |
| 8 | **D** | An endpoint policy naming the allowed resources. **A**, **B** and **C** operate on addresses, not resources. |
| 9 | **B** | It filters the path; the caller still needs an identity policy. **A** and **C** overstate it — an endpoint policy never grants; **D** is false. |
| 10 | **A** | That access arrives through a specific VPC endpoint. **B**, **C** and **D** are other condition keys. |
| 11 | **C** | Public IP, route to an internet gateway, security group, network ACL. **A**, **B** and **D** undercount. |
| 12 | **A** | Reachability depends on all four conditions. **B** is a fact but not the reason; **C** is true and irrelevant here; **D** is false. |

**Q13 rubric (5 marks).** One mark each for: **what it removes** — arbitrary internet destinations (§7.3); **what it does
not** — any resource behind the same service endpoint, notably another account's bucket (§5.4); **endpoint policies**
naming permitted resources (§5.5); **identity-side conditions** — `aws:SourceVpce`, `s3:ResourceAccount` (§5.4); and
**detection** — flow logs and CloudTrail alerting on writes outside the account (§5.4, L16). Accepting "no NAT = no
exfiltration" scores 0 on the second mark and cannot exceed 3.

---

<a id="m11-l09"></a>
## M11-L09 — DNS, TLS and Load Balancing

**Answers: A · C · D · B · C · B · C · D · A · D · A · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Days in advance, so caches already hold the short value. **B** is the common error; **C** changes nothing for caches already holding the old answer; **D** is false. |
| 2 | **C** | You do not control resolver caches. **A**, **B** and **D** are false. |
| 3 | **D** | ACM certificates validated by DNS, while the validation CNAME remains. **A** and **C** need a person; **B** overstates. |
| 4 | **B** | Someone deletes the validation CNAME during a tidy-up. **A**, **C** and **D** are not the usual cause. |
| 5 | **C** | 25.0% — round robin is indifferent to backend state, so **D** is wrong. **A** is the LOR share; **B** contradicts the output. |
| 6 | **B** | Share fell to 14.6% and p95 from 865 to 751 ms — better, not fixed. **A** is the health check's job; **C** and **D** contradict the output. |
| 7 | **C** | Health checks remove the dead one; nothing removes the slow one. **A** and **D** are incidental; **B** is backwards. |
| 8 | **D** | Interval × unhealthy threshold. **A**, **B** and **C** are wrong arithmetic. |
| 9 | **A** | One dependency failure would remove every target at once. **B**, **C** and **D** are secondary or false. |
| 10 | **D** | 21.03%. **B** is a delay of 0, **A** is 30 s, **C** is 60 s. |
| 11 | **A** | From p99, including the full streaming duration. **B** loses the tail; **C** and **D** are unrelated inputs. |
| 12 | **B** | Static IPs for partner allowlisting, or a non-HTTP protocol. **A**, **C** and **D** are ALB strengths. |

**Q13 rubric (5 marks).** One mark each for: **deregistration delay** against p99 stream duration (§5.6); **idle timeout**
at the load balancer or gateway (§5.3, L13); **graceful shutdown** in the application on `SIGTERM` (§5.6); **correlating
with deployments** — overlay deploy markers and look for clustering (§6, L16); and **a slice metric** for incomplete
streams rather than an aggregate error rate (M10-L08). Naming only "increase the timeout" scores 1.

---

<a id="m11-l10"></a>
## M11-L10 — S3: Buckets, Permissions, Encryption, Lifecycle

**Answers: A · D · C · A · C · B · C · B · D · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | `RestrictPublicBuckets` restricts a bucket with a public policy to the owner's account and AWS service principals. **B** prevents new public policies being set; **C** and **D** govern ACLs. |
| 2 | **D** | Only the ACL settings were on; the policy settings were off. **A**, **B** and **C** are false. |
| 3 | **C** | Four of eight. **A**, **B** and **D** contradict §7.1. |
| 4 | **A** | SSE-S3 is transparent to authorization: `s3:GetObject` is sufficient. **B**, **C** and **D** describe KMS-backed options. |
| 5 | **C** | A customer-managed key can be disabled or its policy edited. **A** has no key control; **B** is AWS-managed; **D** confuses rotation with revocation. |
| 6 | **B** | Objects deleted before the minimum are still billed for it. **A**, **C** and **D** invent restrictions. |
| 7 | **C** | 66% — $33,915 to $11,366. **A**, **B** and **D** contradict §7.3. |
| 8 | **B** | A per-GB retrieval charge on every full read. **A** is false for that class; **C** understates; **D** is invented. |
| 9 | **D** | A delete marker is added; versions remain and are billed. **A**, **B** and **C** describe other operations. |
| 10 | **B** | Expiring noncurrent versions. **A**, **C** and **D** are transitions people do remember. |
| 11 | **A** | Media failure — the only physical-storage mode in the list. **B**, **C** and **D** are permission or application failures. |
| 12 | **D** | A separate account, unreachable by the credentials that destroyed the original. **A**, **B** and **C** leave it reachable. |

**Q13 rubric (5 marks).** One mark each for: **Block Public Access — all four settings — plus Object Ownership** (§5.1);
**encryption with a customer-managed key** and a policy denying unencrypted PUTs (§5.2); **versioning with a noncurrent
expiry rule** and an abort rule for incomplete uploads (§5.4); **retention, deletion and data class** for customer
documents (M10-L06); and **a backup that is a backup** — replication to a separate account, with a tested restore (§5.5).
An answer that only mentions "make sure it's not public" scores 1.

---

<a id="m11-l11"></a>
## M11-L11 — EC2 and the Compute Baseline

**Answers: A · B · C · D · A · C · D · B · B · C · D · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Measured p95 plus a stated headroom factor. **C** loses the tail; **B** is not measurement; **D** over-provisions for a one-off. |
| 2 | **B** | Undersized: 3.8 × 1.4 = 5.3 vCPU needs the next size up. **A**, **C** and **D** contradict §7.1. |
| 3 | **C** | A level of spend per hour for the term. **A** is the older Reserved Instance model; **B** and **D** are false. |
| 4 | **D** | `(1 − 0.05)^24 ≈ 29%`. **A**, **B** and **C** overstate survival. |
| 5 | **A** | Work that checkpoints and can resume. **B**, **C** and **D** all put user-visible work on reclaimable capacity. |
| 6 | **C** | 330 seconds in total. **A**, **B** and **D** are individual stages. |
| 7 | **D** | It responds in minutes while a spike arrives in seconds. **A**, **B** and **C** are secondary or false. |
| 8 | **B** | In-flight requests or queue depth — the real bottleneck. **A** is the classic mistake; **C** and **D** are rarely binding. |
| 9 | **B** | 2.2%. **A** is the model wait, **C** vector search, **D** the concurrency multiplier. |
| 10 | **C** | Memory and connections. **A** is 2% busy; **B** and **D** are rarely the limit. |
| 11 | **D** | A hand-modified instance cannot be reproduced, and scale-out launches the image. **A**, **B** and **C** are false or incidental. |
| 12 | **A** | Credit exhaustion collapses performance in a way that resembles an application bug. **B**, **C** and **D** are false. |

**Q13 rubric (5 marks).** One mark each for: **the profile** — the request is ~2% CPU and mostly waiting (§5.4);
**the real bottleneck** — memory and concurrency, measured (§5.4, §6); **a load test** establishing capacity per instance
(M13-L11); **the autoscaling metric** — in-flight requests, not CPU (§5.4); and **a constructive alternative** — right-size
on the resource that binds, consider containers or a purchase-option change (§5.2, §5.6). Simply refusing scores 1.

---

<a id="m11-l12"></a>
## M11-L12 — Containers on AWS: ECR, ECS and Fargate

**Answers: C · D · B · D · A · A · C · B · A · C · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Least to most frequently changed, so the cache survives. **A**, **B** and **D** all invalidate the cache on every commit. |
| 2 | **D** | 146.4 seconds against 14.7. **A** is the good ordering; **B** and **C** are individual layer times. |
| 3 | **B** | It adds pull time to every scale-out, deployment and rollback. **A**, **C** and **D** are false. |
| 4 | **D** | The execution role: the agent could not pull the image or write logs. **A** would still produce logs; **B** and **C** are not the mechanism. |
| 5 | **A** | The task role covers the application's own AWS calls. **B** is the agent's; **C** and **D** are false. |
| 6 | **A** | Pulling the image, writing logs and fetching injected secrets. **B** is the task role's job; **C** and **D** are false. |
| 7 | **C** | It bounds every AWS action the agent can take (M9-L13). **A**, **B** and **D** are application concerns. |
| 8 | **B** | `0 / 100` — a legal configuration with a zero capacity floor. **A** keeps half; **C** and **D** keep full capacity. |
| 9 | **A** | Capacity may briefly double, and so does cost. **B**, **C** and **D** misread the setting. |
| 10 | **C** | Images acquire new findings while sitting untouched in the registry. **A**, **B** and **D** are invented. |
| 11 | **D** | The host — never the image you built. **A**, **B** and **C** remain yours (L01 §7.4). |
| 12 | **B** | Injected at runtime from a secret store. **A**, **C** and **D** all put the secret somewhere it cannot be rotated or audited (L17). |

**Q13 rubric (5 marks).** One mark each for: **measure first** — image size, layer cache hit rate, pull time, batch
duration (§7.1–§7.2); **layer order and multi-stage build**, with `.dockerignore` (§5.2); **removing what the runtime does
not need** — build tools, wrong base image, test suite (§6); **deployment configuration** — batch size, capacity floor,
circuit-breaker rollback (§5.5); and **rollback specifically** — a small image makes reverting fast, and the previous
image must still be deployable. Answers that only say "make the image smaller" score 2.

---

<a id="m11-l13"></a>
## M11-L13 — Lambda and API Gateway

**Answers: A · C · B · A · D · C · C · B · D · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Module scope, so initialisation is amortised across invocations. **B** repeats the work every request; **C** and **D** are not how the runtime behaves. |
| 2 | **C** | 100% — nothing stays warm between calls that far apart. **A** is one per minute, **D** one per ten seconds, **B** one per second. |
| 3 | **B** | If the warm floor covers most traffic, you have bought a server — use a container. **A** and **C** are good fits for it; **D** is not the criterion. |
| 4 | **A** | It guarantees a share **and** caps it. **B** is provisioned concurrency; **C** and **D** are false. |
| 5 | **D** | 140 × 2.5 = 350. **A**, **B** and **C** ignore the duration term. |
| 6 | **C** | The API Gateway integration timeout and a typical Lambda default. **A** and **B** understate; **D** overstates — the 15-minute maximum was not exceeded. |
| 7 | **C** | 15 minutes. **A** is the gateway default; **B** and **D** are invented. |
| 8 | **B** | The integration timeout is shorter than the function's duration — and the function keeps running and billing. **A**, **C** and **D** do not fit the evidence. |
| 9 | **D** | Duty cycle first, then the limits. **A**, **B** and **C** are secondary. |
| 10 | **B** | It scales per request, far faster than a database accepts connections (L14 §5.3). **A**, **C** and **D** are false. |
| 11 | **A** | Environments are reused, so per-request data at module scope can reach another user. **B** is marginal; **C** and **D** are false. |
| 12 | **D** | A streaming-capable path — a function URL, or a load balancer in front of a container. **A** does not address the gateway ceiling; **B** and **C** change the product to avoid the problem. |

**Q13 rubric (5 marks).** One mark each for: **the concurrency arithmetic** — 200k/day with 2.5 s responses, and the peak
concurrency it implies (§5.4); **the timeout ceilings** on the chosen path, and whether streaming works (§5.5); **cold
starts** at that rate — which are *not* the problem here, and saying so earns the mark; **cost comparison** against a
container at that duty cycle (§7.5); and **a recommendation with a condition** — e.g. containers for the synchronous API,
Lambda for the asynchronous paths. A flat yes or no without arithmetic scores 1.

---

<a id="m11-l14"></a>
## M11-L14 — RDS and DynamoDB

**Answers: B · C · D · A · D · A · C · B · C · D · B · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | It answers questions you did not anticipate. **A** is usually backwards; **C** is false; **D** is not a differentiator. |
| 2 | **C** | Three of five. **A**, **B** and **D** contradict §7.1. |
| 3 | **D** | Largely the instance's memory. **A**, **B** and **C** are false. |
| 4 | **A** | Compute scales with traffic; the limit scales with database memory. **B** and **D** are false; **C** overstates — pooling exists but is per-instance. |
| 5 | **D** | `ceil(6/1) × 400 = 2,400`. **A** ignores item size; **B** and **C** use the wrong divisor. |
| 6 | **A** | 1,000 WCU per partition. **B** is the read ceiling; **C** and **D** are false. |
| 7 | **C** | One partition is receiving a disproportionate share. **A** contradicts the 6% figure; **B** affects reads, not throttled writes; **D** is a reporting detail, not the cause. |
| 8 | **B** | It reduces items returned, not items read and billed. **A** and **D** are the common misconception; **C** is false. |
| 9 | **C** | About 33,000×. **A** and **B** understate; **D** is the item count, not the ratio. |
| 10 | **D** | Recovering from an accidental delete — replication copies the delete. **A**, **B** and **C** are exactly what replicas are for. |
| 11 | **B** | Nothing user-visible; it exists to fail over. **A** is the common confusion with read replicas; **C** and **D** are false. |
| 12 | **A** | Retry idempotently, because connections drop. **B** risks data loss; **C** does not address the dropped connection; **D** would send writes to a read-only endpoint. |

**Q13 rubric (5 marks).** One mark each for: **which parts fit DynamoDB** — session state, idempotency keys, job status
(§5.7); **which do not** — permissions, joins, evaluation runs, ad-hoc questions (§7.1); **the key-design requirement** —
access patterns written down first, and what happens when a new one appears (§5.2); **operational limits** — partition
ceilings, item size, scans (§5.4–§5.5); and **a split recommendation** rather than one store for everything. Choosing
either store for all of it, without qualification, scores 2.

---

<a id="m11-l15"></a>
## M11-L15 — SQS, SNS and EventBridge

**Answers: B · C · D · A · C · A · B · D · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | A latency problem — accepted work that waits, rather than rejected work. **A**, **C** and **D** are not the trade. |
| 2 | **C** | 55.6%. **A** is with the queue; **B** and **D** contradict §7.1. |
| 3 | **D** | It is redelivered and processed again, while the first worker is still running. **A**, **B** and **C** are false. |
| 4 | **A** | Above p99, or extended from the worker as it progresses. **B** duplicates the slow half; **C** is a default, not a decision; **D** is backwards. |
| 5 | **C** | Idempotent handlers. **A** changes the guarantee but not the requirement in standard queues; **B** loses work; **D** discards retries entirely. |
| 6 | **A** | Indexing by a stable id is idempotent by key. **B**, **C** and **D** all produce visible double effects. |
| 7 | **B** | It blocks every later message in its group. **A**, **C** and **D** are false. |
| 8 | **D** | Age of the oldest message. **A** and **B** are secondary; **C** can be near zero while nothing completes. |
| 9 | **A** | Messages in flight and failing repeatedly are not counted as available. **B**, **C** and **D** are false. |
| 10 | **D** | EventBridge — archive and replay. **A**, **B** and **C** have no replay facility. |
| 11 | **B** | A slow or broken consumer buffers its own backlog rather than losing messages. **A**, **C** and **D** are false. |
| 12 | **C** | It serialises the entire system, because order is preserved within a group. **A**, **B** and **D** are false. |

**Q13 rubric (5 marks).** One mark each for: **visibility timeout against p99 processing**, including the consumer's own
timeout (§5.3); **idempotency on a content-derived key**, with a conditional write and a TTL (§5.4); **DLQ configuration**
— small `maxReceiveCount`, alarm on depth (§5.5); **monitoring** — age of oldest message, not depth (§5.6); and **the
downstream consequence** — duplicate chunks degrade retrieval, so the index needs de-duplication too (M7-L05). Naming
only "add a check for duplicates" without the key design scores 2.

---

<a id="m11-l16"></a>
## M11-L16 — CloudWatch and CloudTrail

**Answers: B · A · C · D · B · C · D · A · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Metrics. **A**, **C** and **D** must first be turned into metrics (metric filters, embedded metric format) to be alarmed on. |
| 2 | **A** | 1.7% — $107 against $6,125. **B**, **C** and **D** overstate. |
| 3 | **C** | Keep all errors, sample successes. **A** increases cost; **B** is marginal; **D** loses searchability. |
| 4 | **D** | Only the p99, at 9,488 ms. **A**, **B** and **C** were all silent — which is the point. |
| 5 | **B** | A minority failure leaves the average silent. **A**, **C** and **D** are false. |
| 6 | **C** | Management events. **A** is opt-in; **B** and **D** are false. |
| 7 | **D** | Who read a specific object. **A**, **B** and **C** are management events. |
| 8 | **A** | Charged per event, at very large volume. **B**, **C** and **D** are false. |
| 9 | **C** | 2,102.40 per year. **A** is "2 out of 2", **D** "3 out of 3", **B** "3 out of 5". |
| 10 | **A** | It keeps firing through a flapping failure that a single healthy datapoint would reset. **B** is marginally false — it fires slightly more often; **C** is false; **D** is invented. |
| 11 | **D** | A runbook link and a named owner. **A**, **B** and **C** are design choices, not universal requirements. |
| 12 | **B** | Absent data usually means something worse than a breach. **A**, **C** and **D** are false. |

**Q13 rubric (5 marks).** One mark each for: **the statistic** — move from averages to p95/p99 (§5.3); **slices** —
per-tenant and per-route metrics, because the aggregate hides the affected population (M10-L08); **sampling with a
consistent key**, so slow requests' traces survive (§5.2); **tracing** to identify which dependency is slow (§7.1); and
**an alarm that would have caught it**, with a threshold and a datapoints rule. An answer that only adds more logging
scores 1.

---

<a id="m11-l17"></a>
## M11-L17 — KMS, Secrets Manager, Backups and Disaster Recovery

**Answers: C · B · A · B · C · D · A · B · D · A · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Both the key policy and the caller's IAM policy (absent a grant). **A** and **D** are each half; **B** is invented. |
| 2 | **B** | The key policy does not name them. **A**, **C** and **D** are false. |
| 3 | **A** | The data becomes unreadable by everyone, immediately — the revocation lever. **B**, **C** and **D** are false. |
| 4 | **B** | KMS encrypts a data key; the data key encrypts the data. **A** and **C** misdescribe it; **D** is false. |
| 5 | **C** | $0.11. **A** is one call per object, **B** Bucket Keys, **D** is not a figure in §7.2. |
| 6 | **D** | A larger blast radius if the cached key is exposed. **A** is backwards; **B** and **C** are false. |
| 7 | **A** | It cannot be rotated and there is no record of who read it. **B**, **C** and **D** are false — Parameter Store's plain `String` type is not encrypted, environment variables are not exposed over the network, and size is not the issue. |
| 8 | **B** | Not having a secret at all — a role or federated identity. **A**, **C** and **D** still leave one to protect. |
| 9 | **D** | 1,440 minutes × 1,400 = 2,016,000. **A** is a 5-minute RPO, **B** continuous replication, **C** a 6-hour RPO. |
| 10 | **A** | RPO is data lost; RTO is time down. **B**, **C** and **D** are false. |
| 11 | **C** | Pilot light. **A** has no standing infrastructure; **B** runs a small live copy; **D** runs both fully. |
| 12 | **D** | Whether it works, how long it takes, and what is missing. **A**, **B** and **C** are all checkable without restoring anything. |

**Q13 rubric (5 marks).** One mark each for: **stating the RPO** — up to 24 hours, translated into lost work (§5.5);
**stating the RTO** — unknown until measured, and dependent on restore time (§5.5); **the questions** — are keys available
in the recovery region, is the backup in a separate account, does the restore need permissions someone has (§5.1, §5.4,
§6); **the business framing** — is a day of lost work acceptable, and who accepted it (M10-L16); and **the one test** — a
timed restore into the recovery region, end to end, verifying the application serves traffic (§5.6). Accepting the plan as
stated scores 1.

---

<a id="m11-l18"></a>
## M11-L18 — Infrastructure as Code, CI/CD and Rollback

**Answers: B · C · D · C · A · D · D · B · A · C · A · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Remove write access so code is the only path — the source, not the symptom. **A** and **D** treat the symptom; **C** achieved 18% drift in the lab. |
| 2 | **C** | 45%. **B** is with the practice discouraged, **D** with monthly detection, **A** with a read-only console. |
| 3 | **D** | Destroy and create. **A**, **B** and **C** describe non-destructive operations. |
| 4 | **C** | A replacement: a new empty database, and the old one deleted. **A**, **B** and **D** contradict §7.2. |
| 5 | **A** | 54 of 71.2 minutes — about three-quarters. **B**, **C** and **D** understate. |
| 6 | **D** | It catches defects that otherwise reach production, at a fraction of the cost. **A** is false — it complements review; **B** and **C** are incidental. |
| 7 | **D** | A security group rule. **A**, **B** and **C** are state or effects, not configuration. |
| 8 | **B** | The reverse migration. **A**, **C** and **D** are all after the fact. |
| 9 | **A** | So routine deploys cannot destroy or replace the database. **B** is a side benefit; **C** and **D** are false. |
| 10 | **C** | Any branch — including one from a fork's pull request — can assume the deployment role. **A**, **B** and **D** are false. |
| 11 | **A** | Rebuilds are slow and may not reproduce the previous artefact (M10-L13). **B**, **C** and **D** are false or incidental. |
| 12 | **B** | CI, against the reviewed plan. **A** and **C** break the review-to-apply link; **D** ignores that the plan reviewed must be the plan applied. |

**Q13 rubric (5 marks).** One mark each for: **reading the plan for verbs** — every `replace` and `destroy`, not the
diff of the source (§5.2); **naming the stateful resources at risk** — databases, buckets, tables (§7.2); **the controls
you would require** — deletion protection, separate stacks, a policy check that fails on destroy in production (§5.2–§5.3);
**a refusal condition** — any unexplained replacement of a stateful resource, or a plan not posted for review; and **a safe
alternative** — rename in state (a move/import) rather than recreating the resource. Approving on the grounds that it is a
"tidy-up" scores 0.

---

*Module 11 answer key complete: all 18 lessons.*
