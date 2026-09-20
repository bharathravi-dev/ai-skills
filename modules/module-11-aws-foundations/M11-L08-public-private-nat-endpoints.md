# M11-L08 — Public vs Private Access, NAT and Endpoints

| | |
|---|---|
| **Lesson ID** | M11-L08 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M11-L07](M11-L07-vpc-subnets-security-groups.md) |

---

## 1. Learning objectives

1. **Choose** an egress path deliberately, knowing its cost, exposure and what can restrict it.
2. **Compute** NAT gateway cost, and the saving from moving service traffic to a gateway endpoint.
3. **Show** that blocking the internet does not block exfiltration to another account's bucket.
4. **Write** an endpoint policy that distinguishes your resources from an attacker's at the same service.
5. **Audit** inbound exposure against all four conditions, not just security groups.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Internet gateway** | The VPC attachment that lets resources with public addresses send and receive internet traffic. |
| **NAT gateway** | A managed device letting private resources make **outbound** connections; no inbound. |
| **Gateway endpoint** | A route-table entry giving private access to S3 or DynamoDB without leaving the AWS network; no hourly or per-GB charge. |
| **Interface endpoint (PrivateLink)** | An elastic network interface in your subnet providing private access to a service; charged hourly and per GB. |
| **Endpoint policy** | A resource policy on an endpoint restricting which resources may be reached through it. |
| **`aws:SourceVpce`** | A condition key letting a resource policy require that access arrive via a specific endpoint. |
| **Egress allowlist** | A restriction on where a workload may send traffic. |

---

## 3. Plain-language explanation

### 3.1 Four ways out, and only one lets anything in

§7.1 compares them. A **public IP is the only path that permits inbound connections** — so "it needs internet access" is
never a reason to assign a public address; that is what a NAT gateway is for. And only the **endpoint** rows can be
restricted by a *policy* rather than by an address range.

### 3.2 NAT costs hours plus gigabytes

§7.2: at 6,000 GB/month, one NAT gateway costs **$303/month**, three (one per AZ) **$369**. Moving **75%** of that traffic
to an S3 **gateway endpoint** — which has no hourly or per-GB charge — saves **$202/month** and keeps the traffic off the
public internet entirely.

Multi-AZ NAT is bought for **availability**, not throughput: one per AZ so an AZ failure does not take egress with it, and
so traffic does not cross an AZ boundary and get charged again (L02).

### 3.3 "We blocked the internet" does not block exfiltration

§7.3 is the important table. With endpoints and no NAT, **3 of 6** destinations are blocked — but **another account's S3
bucket is still reachable**, because it lives at the same service endpoint as yours. Network design alone cannot tell your
bucket from an attacker's.

### 3.4 An endpoint policy can

§7.4: an S3 gateway-endpoint policy allowing only `acme-prod-docs` **denies 2 of 4** attempts, including
`attacker-exfil-bucket`. It is the only mechanism in this lesson that distinguishes resources at the same endpoint.

### 3.5 Exposure has four conditions

§7.5: a public IP, a route to an internet gateway, a permitting security group, **and** a permitting network ACL. All four
must hold. Auditing only security groups both over-reports and under-reports.

---

## 4. Analogy

**A building's post room.** Staff can send post out without the building having a public letterbox (NAT). A letterbox on
the street is the only thing that lets post *in* (public IP). Internal mail to the company's other offices never leaves
the building's own courier network (endpoints). And a rule saying "no post to competitors" cannot be enforced by the
courier — it needs someone reading the address (endpoint policy).

### Where the analogy breaks

- **Post rooms see one destination per item; S3 requests to your bucket and to an attacker's look identical at the network
  layer** — same endpoint, same protocol (§5.4).
- **Couriers are cheap by the item; NAT charges by the gigabyte**, so the cost model rewards architecture rather than
  volume discipline (§5.3).

---

## 5. Detailed technical explanation

### 5.1 Public and private, precisely

A subnet is **public** if its route table has a route to an internet gateway (L07 §5.3). A resource is reachable from the
internet only if **all four** of §7.5's conditions hold.

| Need | Use | Not |
|---|---|---|
| Accept inbound traffic from users | A load balancer in a public subnet (L09) | A public IP on the workload |
| Make outbound calls to the internet | NAT gateway, or an egress proxy | A public IP |
| Reach S3 or DynamoDB | Gateway endpoint | NAT |
| Reach other AWS services privately | Interface endpoint (PrivateLink) | NAT |
| Reach a partner API | NAT with an egress control, or PrivateLink if the partner offers it | Open egress |

The default posture for an AI workload: **private subnets, no public addresses, endpoints for AWS services, and a narrow,
audited path for anything else**.

### 5.2 Gateway versus interface endpoints

| | Gateway endpoint | Interface endpoint |
|---|---|---|
| Services | S3, DynamoDB | Most AWS services, including Bedrock and Secrets Manager |
| Mechanism | A route-table entry with a prefix list | An ENI with a private IP in your subnet |
| Charges | None | Hourly per endpoint per AZ, plus per GB |
| Restrictable by | Endpoint policy | Endpoint policy **and** security group |
| DNS | Prefix-list routing | Private DNS overrides the public name |

Use gateway endpoints wherever they exist — free, and they remove the largest NAT line. Use interface endpoints for the
services that matter (model APIs, secrets, logging), and weigh the hourly cost against NAT processing at your volume.

### 5.3 NAT cost

`[REAL, computed — ILLUSTRATIVE rates]` §7.2 — $303 / $336 / $369 per month for one, two and three AZs; $202/month saved
by a gateway endpoint.

```text
NAT monthly ≈ (hourly_rate × 730 × number_of_AZs) + (per_GB_rate × GB_processed)
```

Both terms matter, and at high volume the per-GB term dominates. Check what is actually flowing through NAT before
optimising: container image pulls, package installs, log shipping and S3 traffic are the usual four, and three of them
have endpoint or caching alternatives.

### 5.4 The exfiltration path that survives

`[REAL, computed]` §7.3 — 0 / 0 / 2 / 3 of 6 destinations blocked.

This is the lesson's central point. Removing NAT blocks arbitrary internet destinations. It does **not** block:

- Writing to **another account's** S3 bucket, if that bucket permits it.
- Reading from an attacker-controlled bucket.
- Any other service reachable through the same endpoint.

The controls that do work, layered:

1. **Endpoint policy** on the gateway or interface endpoint, naming the resources reachable through it (§7.4).
2. **Identity policy conditions**: `aws:SourceVpce`, `aws:SourceVpc`, `s3:ResourceAccount` — so credentials only work from
   your network and only against your account's resources (L04, L10).
3. **Resource policies** with `aws:SourceVpce` on your own buckets, so they are reachable only through your endpoint.
4. **Application-level egress allowlists** for anything the model or an agent can cause to be fetched (M9-L12).
5. **Flow logs and CloudTrail** to detect what actually happened (L16, M10-L13).

### 5.5 Endpoint policies

```json
{
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::acme-prod-docs", "arn:aws:s3:::acme-prod-docs/*"]
  }]
}
```

An endpoint policy grants nothing on its own — the caller still needs an identity policy that allows the action (L04). It
acts as a **filter on the path**: requests for anything else do not leave the VPC.

The complementary condition on the bucket side:

```json
{"Effect": "Deny", "Principal": "*", "Action": "s3:*",
 "Resource": ["arn:aws:s3:::acme-prod-docs", "arn:aws:s3:::acme-prod-docs/*"],
 "Condition": {"StringNotEquals": {"aws:SourceVpce": "vpce-0abc123"}}}
```

Together: your workload can only reach your bucket, and your bucket can only be reached by your workload.

### 5.6 Auditing exposure

`[REAL, computed]` §7.5 — 1 of 5 scenarios reachable.

Audit all four conditions together. A tool that reports only "security group allows 0.0.0.0/0" will flag instances that
are unreachable and miss the instance whose group is narrow today. Better questions:

- Which resources have public addresses, and why?
- Which subnets have a route to an internet gateway, and what is in them?
- Which security groups allow `0.0.0.0/0` inbound, and are they on load balancers?
- What egress is permitted, and to where?

### 5.7 Assumptions and limitations

- All rates are invented; check current AWS pricing, which differs by region and direction.
- AWS Network Firewall, egress proxies with domain allowlists and Transit Gateway designs are out of scope.
- Interface endpoints are not available for every service in every region — check parity (L02).

---

## 6. Worked example — the private subnet that leaked anyway

**The situation.** After a security review, a team moved an assistant's workload into private subnets with no public
addresses and **no NAT gateway**. The review recorded "no internet egress" as the control against exfiltration.

**What happened.**

1. The workload still needed S3, so an S3 **gateway endpoint** was added — correctly, and with **no endpoint policy**
   (§7.4).
2. A prompt-injection payload in an ingested document instructed the assistant to summarise a customer list and write it
   to a bucket named in the payload (M5-L13, M9-L15).
3. The workload's role allowed `s3:PutObject` on `*` — a leftover from development (L04 §5.5).
4. The object was written to an attacker's bucket **through the endpoint**, without any internet access (§7.3, row 2).
5. Flow logs showed only traffic to the S3 prefix list. CloudTrail showed the `PutObject` — but nobody was looking at
   cross-account destinations (L16).

| # | What was missing | Fix |
|---|---|---|
| 1 | Endpoint policy | Restrict the endpoint to your buckets (§5.5) |
| 2 | Identity policy scope | `s3:PutObject` on named resources only (L04) |
| 3 | `s3:ResourceAccount` condition | Deny access to buckets outside your account |
| 4 | Bucket-side `aws:SourceVpce` | Your bucket reachable only via your endpoint |
| 5 | Detection | Alert on writes to buckets outside the account (L16) |

**The general rule.** **"No internet access" is not "no egress". The endpoint is the egress, and only a policy can tell
whose resource is on the other side.**

---

## 7. Practical activity

**File:** [`labs/m11/l08_public_private_nat_endpoints.py`](../../labs/m11/l08_public_private_nat_endpoints.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l08_public_private_nat_endpoints.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. FOUR WAYS OUT, COMPARED
============================================================================
  path                              reaches               inbound?    $/GB   $/hour   restrictable by
  public IP + internet gateway      the internet               YES   0.000    0.000   security group only
  NAT gateway                       the internet                no   0.045    0.045   security group only
  gateway endpoint (S3, DynamoDB)   that service only           no   0.000    0.000   ENDPOINT POLICY (per bucket/table)
  interface endpoint (PrivateLink)  that service only           no   0.010    0.011   ENDPOINT POLICY + security group

  [ILLUSTRATIVE rates.] Two things to notice. A public IP is the only row that
  allows INBOUND connections -- 'it needs internet access' is not a reason to
  give something a public address. And only the endpoint rows can be
  restricted by a POLICY rather than by an address range (section 4).

============================================================================
2. WHAT DOES NAT ACTUALLY COST?
============================================================================
  6,000 GB/month of egress, 730 hours [ILLUSTRATIVE rates]

  design                                       hourly   processing    total/mo    total/yr
  1 NAT gateway (1 AZ)                             33          270         303       3,634
  2 NAT gateways (2 AZs)                           66          270         336       4,028
  3 NAT gateways (3 AZs)                           99          270         369       4,423

  if 75% of that traffic is S3 and moves to a GATEWAY endpoint:
    processing charges fall by $202/month ($2,430/year) and the traffic
    never leaves the AWS network.
  Multi-AZ NAT is bought for availability, not throughput: one NAT per AZ so
  an AZ failure does not take egress with it -- and so that traffic does not
  cross AZs to reach it, which would be charged again (M11-L02).

============================================================================
3. WHAT CAN A COMPROMISED WORKLOAD REACH?
============================================================================
  destination                                 public IP          NAT   endpts+NAT  endpts only
  our S3 bucket (intended)                        reach        reach        reach        reach
  ANOTHER ACCOUNT'S S3 bucket                     reach        reach        reach        reach
  Bedrock / the model API                         reach        reach        reach        reach
  an approved partner API                         reach        reach        reach      BLOCKED
  pastebin.example / attacker endpoint            reach        reach      BLOCKED      BLOCKED
  a crypto-mining pool                            reach        reach      BLOCKED      BLOCKED

  public IP, open egress          blocks 0/6 destinations
  NAT gateway, open egress        blocks 0/6 destinations
  endpoints + NAT for partner     blocks 2/6 destinations
  endpoints only, no NAT          blocks 3/6 destinations

  Note row 2: every design that reaches S3 at all still reaches SOMEONE ELSE'S
  S3 bucket. Network design alone cannot tell your bucket from theirs --
  that needs an endpoint policy (section 4). This is the exfiltration path
  that survives 'we blocked the internet' (M9-L12, M10-L10).

============================================================================
4. AN ENDPOINT POLICY THAT KNOWS WHOSE BUCKET IT IS
============================================================================
  endpoint policy allows only: arn:aws:s3:::acme-prod-docs, arn:aws:s3:::acme-prod-docs/*

  attempt                                              verdict
  PutObject to acme-prod-docs/report.pdf               allowed
  GetObject from acme-prod-docs/policy.pdf             allowed
  PutObject to attacker-exfil-bucket/dump.zip           DENIED
  PutObject to acme-dev-scratch/dump.zip                DENIED

  denied: 2/4
  An endpoint policy is a resource-level control on a NETWORK path. It is the
  only mechanism in this lesson that can distinguish your bucket from an
  attacker's, because both live at the same service endpoint. Pair it with an
  identity policy condition on aws:SourceVpce (M11-L04, M11-L10).

============================================================================
5. CAN ANYTHING ACTUALLY REACH THIS INSTANCE?
============================================================================
  scenario                                    public       route    security     network   reachable?
  public subnet, SG open on 443                  yes         yes         yes         yes   YES
  public subnet, SG closed                       yes         yes          no         yes   no
  private subnet, SG open                         no          no         yes         yes   no
  public subnet, no public IP                     no         yes         yes         yes   no
  public subnet, NACL denies inbound             yes         yes         yes          no   no

  All four must hold. That is why 'is it exposed?' has four answers, and why
  auditing only security groups misses instances that are unreachable anyway
  -- and, worse, reports as safe an instance whose SG is closed today and
  will be opened by someone next week (M10-L07).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every cost, block count, policy verdict and reachability result above
  is computed from the values and rules in this script.

  ILLUSTRATIVE: all per-GB and hourly rates are invented; check current AWS
  pricing. Traffic volumes and the destination list are invented too.

  NOT SHOWN: AWS Network Firewall, egress proxies with domain allowlists,
  Transit Gateway designs, and PrivateLink for your own services (M11-L09).

Done.
```

### 7.3 Reading the result

**Section 1's "inbound?" column** has one `YES`. That is the whole argument against public addresses on workloads.

**Section 2's last paragraph** is usually the largest easy saving in a network bill.

**Section 3, row 2** is the finding: every design reaches another account's bucket.

**Section 4** is the fix, and **section 5** is how to audit whether any of it is exposed.

---

## 8. Common mistakes and troubleshooting

1. **Giving a workload a public IP so it can make outbound calls.** §5.1 — use NAT or endpoints.
2. **One NAT gateway for three AZs.** Availability risk plus cross-AZ charges (L02).
3. **Routing S3 traffic through NAT.** §7.2 — a gateway endpoint is free.
4. **Endpoints without endpoint policies.** §6 — the exfiltration path stays open.
5. **Treating "no NAT" as an exfiltration control.** §7.3.
6. **No `aws:SourceVpce` condition on sensitive buckets.** Credentials work from anywhere without it.
7. **Auditing security groups alone.** §7.5 — four conditions.
8. **Assuming interface endpoints exist everywhere.** Check region parity (L02).

| Symptom | Likely cause | Fix |
|---|---|---|
| Large NAT processing charges | S3 or image-pull traffic through NAT | Gateway endpoint; registry cache |
| Egress works in one AZ, fails in another | Single NAT, or missing route association | One NAT per AZ; check route tables |
| Data reached an external bucket | Endpoint without a policy | Endpoint policy plus `s3:ResourceAccount` |
| Service unreachable after adding an endpoint | Private DNS overriding the public name | Check endpoint DNS and security group |
| Exposure audit disagrees with reality | Only one of four conditions checked | Audit all four (§5.6) |

---

## 9. Security, privacy, reliability, cost

- **Security.** This lesson supplies the network half of M10-L10's exfiltration controls; the identity half is L04.
- **Privacy.** Endpoints keep traffic off the public internet, which is a real residency and interception argument
  (M10-L06).
- **Reliability.** NAT per AZ, and endpoint availability per AZ, are both availability decisions (L02).
- **Cost.** Gateway endpoints are free and usually the single largest network saving available (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which egress path allows inbound connections?
2. What does a gateway endpoint cost per GB?
3. Why does "endpoints only, no NAT" still reach another account's bucket?
4. What did the endpoint policy in §7.4 deny?
5. Name the four conditions for inbound reachability.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Raise the traffic to 60,000 GB/month and re-read the NAT arithmetic.
2. Add an "interface endpoint for Bedrock" design to §7.3 and score it.
3. Write the endpoint policy for two buckets and a DynamoDB table.
4. Add the `s3:ResourceAccount` condition to the §7.4 check and re-run the attempts.
5. Audit one workload you run against the four conditions in §7.5.

### Exercise 3 — Challenge (~60 min)

1. Design the full egress posture for an AI workload: endpoints, policies, conditions, detection.
2. Write the bucket policy that denies access not arriving via your endpoint.
3. Estimate your own NAT bill and the saving from a gateway endpoint.
4. Build the detection for "wrote to a bucket outside our account" (L16).
5. Write the exposure audit as a checklist a reviewer can run in ten minutes.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l08).)*

**Q1.** Which egress path permits inbound connections from the internet?

- A. A public IP with an internet gateway
- B. A gateway endpoint
- C. A NAT gateway
- D. An interface endpoint

**Q2.** What is the correct way for a private workload to make outbound internet calls?

- A. Assign it a public IP address
- B. Route through a NAT gateway or an egress proxy
- C. Attach an internet gateway to its subnet
- D. Use a gateway endpoint with a wildcard policy

**Q3.** What does a gateway endpoint for S3 charge?

- A. An hourly rate per AZ
- B. A per-GB processing rate
- C. An hourly rate plus per GB
- D. Nothing

**Q4.** In §7.2, what did moving 75% of traffic to a gateway endpoint save per month?

- A. $33
- B. $270
- C. $202
- D. $369

**Q5.** Why is one NAT gateway per AZ recommended?

- A. To increase total throughput beyond one gateway's limit
- B. Because endpoints require a NAT in the same AZ
- C. To reduce the per-GB processing rate
- D. So an AZ failure does not remove egress, and traffic does not cross AZs

**Q6.** In §7.3, which destination remained reachable under every design?

- A. A crypto-mining pool
- B. Another account's S3 bucket
- C. An attacker endpoint on the public internet
- D. An approved partner API

**Q7.** Why can network design not block that destination?

- A. S3 traffic is encrypted and cannot be inspected
- B. Endpoints bypass route tables entirely
- C. It is reached through the same service endpoint as your own bucket
- D. Cross-account traffic uses a different protocol

**Q8.** What mechanism can distinguish your bucket from an attacker's on the same endpoint?

- A. A network ACL rule on the endpoint's prefix list
- B. A security group attached to the gateway endpoint
- C. A route table entry for the bucket's prefix
- D. An endpoint policy naming the allowed resources

**Q9.** Does an endpoint policy grant permissions?

- A. Yes, it grants the actions it lists to any principal in the VPC
- B. No — it filters the path; the caller still needs an identity policy
- C. Yes, but only for gateway endpoints
- D. No — it only affects DNS resolution

**Q10.** What does `aws:SourceVpce` let a bucket policy require?

- A. That access arrives through a specific VPC endpoint
- B. That the caller's credentials were issued by STS
- C. That the request originated in a specific Availability Zone
- D. That the bucket is encrypted with a customer-managed key

**Q11.** How many conditions must hold for an instance to be reachable from the internet?

- A. Two
- B. Three
- C. Four
- D. One — a public IP address

**Q12.** Why is auditing security groups alone insufficient?

- A. Reachability also depends on public addressing, routing and the network ACL
- B. Security groups are evaluated after network ACLs
- C. Security groups cannot express deny rules
- D. Security group rules are not visible in configuration exports

**Q13.** *(Written, rubric-graded.)* In under 150 words: a review concludes that moving a workload to private subnets with
no NAT "removes the exfiltration risk". Explain what it does remove, what it does not, and the controls you would add.

---

## 12. Revision notes

- **Only a public IP allows inbound.** Outbound-only needs are met by NAT or endpoints.
- **NAT costs hours + gigabytes**: **$303 / $336 / $369** per month for 1/2/3 AZs at 6,000 GB; a **gateway endpoint is
  free** and saved **$202/month** for 75% of that traffic.
- **Multi-AZ NAT is for availability**, and avoids cross-AZ charges.
- **Blocking the internet does not block exfiltration**: another account's bucket is reachable under **every** design.
- **Endpoint policies** are the only control here that distinguishes resources at the same endpoint — pair with
  `aws:SourceVpce` and `s3:ResourceAccount`.
- **Exposure has four conditions**: public IP, IGW route, security group, network ACL. Audit all four.

---

## 13. Completion checklist

- [ ] No workload has a public IP address; inbound arrives via a load balancer.
- [ ] S3 and DynamoDB traffic uses gateway endpoints, not NAT.
- [ ] Every endpoint has an endpoint policy naming permitted resources.
- [ ] Sensitive buckets require `aws:SourceVpce`; roles carry `s3:ResourceAccount` conditions.
- [ ] Exposure audits check all four reachability conditions.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon VPC User Guide — NAT gateways, gateway endpoints (S3, DynamoDB), interface endpoints (AWS PrivateLink), endpoint
  policies `[STABLE]`
- IAM condition keys `aws:SourceVpce`, `aws:SourceVpc`, `s3:ResourceAccount` `[STABLE]`
- M9-L12 (egress allowlists, SSRF, trust boundaries) and M10-L10 (exfiltration channels) `[STABLE]`
- M11-L07 (routing and security groups) and M11-L10 (S3 permissions and Block Public Access) `[STABLE]`
- M11-L16 (flow logs and CloudTrail — detecting what actually left) `[STABLE]`

---

## 15. Next lesson

→ [M11-L09 — DNS, TLS and Load Balancing](M11-L09-dns-tls-load-balancing.md) covers how users reach the public edge of
your system: name resolution, certificates that expire at inconvenient times, and the load balancer that stands between
the internet and everything you just made private.
