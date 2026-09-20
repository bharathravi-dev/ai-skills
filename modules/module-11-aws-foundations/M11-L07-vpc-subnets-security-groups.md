# M11-L07 — VPCs, Subnets, Route Tables and Security Groups

| | |
|---|---|
| **Lesson ID** | M11-L07 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M11-L02](M11-L02-regions-availability-zones.md), [M2-L11](../module-02-python-foundations/M2-L11-http-rest.md) |

---

## 1. Learning objectives

1. **Plan** a VPC address space that survives growth, counting AWS's reserved addresses and alignment waste.
2. **Avoid** the CIDR overlaps that make peering impossible without re-addressing.
3. **Resolve** a route table by longest prefix match, and predict what a new route changes.
4. **Explain** stateful security groups against stateless network ACLs, including the ephemeral-port bug.
5. **Prefer** security-group references to CIDR rules, and say how much reach that removes.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **VPC** | A logically isolated virtual network in one region, with a CIDR block you choose. |
| **CIDR block** | An address range written as `10.20.0.0/16`; the prefix length says how many addresses. |
| **Subnet** | A slice of the VPC's range, bound to exactly one Availability Zone. |
| **Route table** | Rules mapping destination prefixes to targets; associated with subnets. |
| **Longest prefix match** | The most specific matching route wins. |
| **Internet gateway** | The VPC attachment that makes public addressing possible. |
| **Security group** | A **stateful**, allow-only firewall attached to an elastic network interface. |
| **Network ACL** | A **stateless**, numbered, allow-and-deny filter at the subnet boundary. |
| **Ephemeral port** | The high-numbered source port a client picks for an outbound connection. |
| **SG reference** | A security-group rule whose source is another security group, not a CIDR. |

---

## 3. Plain-language explanation

### 3.1 Addresses disappear before you launch anything

§7.1 plans a `/16` into nine subnets. AWS reserves **5 addresses in every subnet**, so nine subnets lose **45 addresses**
before anything starts. Alignment costs another **256** — a `/22` must begin on a `/22` boundary. The plan uses **7%** of
the VPC, which is the point: leave room.

A `/28` subnet has **11 usable addresses**. That is why `/28` subnets fail during a rolling deployment, when old and new
tasks exist at once, rather than at steady state.

### 3.2 Overlapping CIDRs cannot be connected

§7.2: of four counterparties, two overlap. The instructive one is **"our own second region" at `10.20.128.0/17`** — carved
from inside the first VPC's own range. Address space is the one decision you cannot change without rebuilding.

### 3.3 The most specific route wins

§7.3 resolves six destinations. `10.20.17.9` matches both `10.20.0.0/16` (local) and `10.20.16.0/22` (an endpoint) and
goes to the **`/22`**. Adding a more specific route silently reroutes a subset of traffic — which is how a change that
"did not touch the network" stops a service reaching a dependency.

### 3.4 Stateful versus stateless is one table

§7.4 sends a request to tcp/443 and a response back to ephemeral port **49512**. The **security group allows the response
with no matching outbound rule**, because it remembers the request. The network ACL **drops it**, because it remembers
nothing — until an explicit rule for **1024–65535** is added.

### 3.5 A CIDR rule grants access to an address range, not to a role

§7.5: allowing the whole VPC to reach the database exposes it to **263 hosts**; the app subnet, **258**; a **security-group
reference, 12** — and that set updates itself as instances come and go.

---

## 4. Analogy

**An office building's floor plan and door policy.** The floor plan (address space) is poured in concrete: you can
repurpose a room, but you cannot move a wall without a rebuild, and you cannot merge with the building next door if both
numbered their rooms 1–100. The door policy comes in two kinds: a badge reader that remembers you came in and lets you out
(stateful), and a guard with a list who checks every crossing in both directions independently (stateless) — and who will
stop you leaving unless "leaving" is also on the list.

### Where the analogy breaks

- **Rooms do not appear overnight; instances do.** A CIDR rule admits whatever gets an address in the range, including
  things that do not exist yet (§5.6).
- **Buildings have one entrance policy; a VPC has several layers** — NACL, security group, host firewall, and the
  application's own authorization (M10-L07).

---

## 5. Detailed technical explanation

### 5.1 Address planning

`[REAL, computed]` §7.1 — 45 addresses to reservations, 256 to alignment, 7% of the VPC used.

| Rule | Detail |
|---|---|
| VPC CIDR size | `/16` down to `/28` |
| Reserved per subnet | **5**: network address, VPC router, DNS, future use, broadcast |
| Subnet scope | Exactly one AZ; a subnet never spans AZs |
| Alignment | A subnet must start on a boundary of its own size |

A workable plan:

```text
central allocation (whole organisation):  10.0.0.0/8
  per region+environment:                 a /16   (e.g. 10.20.0.0/16 = eu-west-2 prod)
    per tier, per AZ:
      public         /24 each   (load balancers, NAT)
      private-app    /22 each   (containers, tasks — the ones that scale)
      private-data   /24 each   (databases, caches)
    leave >50% of the /16 unallocated
```

Size the **app tier** generously: container platforms consume an address per task, and a rolling deployment needs old and
new at once. Size the data tier small. Keep the spare space contiguous.

### 5.2 Never overlap

`[REAL, computed]` §7.2 — 2 of 4 overlap.

Overlapping CIDRs cannot be peered, cannot be joined by Transit Gateway, and cannot be reached over a VPN without network
address translation that nobody wants to own. The failures arrive late, at a merger, a partner integration or a
multi-region rollout.

The discipline is boring and cheap: a central register of allocated ranges, an allocation per region and environment, and
a default template that does **not** use `10.0.0.0/16` (everyone's default, and therefore everyone's collision).

### 5.3 Route tables

`[REAL, computed]` §7.3.

- Routes map a **destination prefix** to a **target**: `local`, internet gateway, NAT gateway, VPC endpoint, peering
  connection, transit gateway.
- The **local** route for the VPC's own CIDR always exists and cannot be removed.
- **Longest prefix match** decides; `0.0.0.0/0` is the last resort.
- Route tables associate with **subnets**, which is what makes a subnet "public" (a route to an internet gateway) or
  "private" (no such route) — the terms describe routing, not a setting.

`169.254.169.254` is link-local: it is never routed, which is why the instance metadata service is reachable from the
instance and from nowhere else (L05 §5.6).

### 5.4 Security groups

- **Stateful**: a response to an allowed request is allowed automatically.
- **Allow-only**: there is no deny rule. Everything not allowed is denied.
- Attached to **network interfaces**, not to subnets; one interface can have several.
- Rules can reference **another security group**, a CIDR, or a prefix list.
- Evaluated as the **union** of all attached groups.

Default posture: inbound allows exactly what is needed, from SG references where possible; outbound restricted for
anything handling untrusted input or sensitive data — an unrestricted egress rule is the exfiltration path in M9-L12 and
M10-L10.

### 5.5 Network ACLs

`[REAL, computed]` §7.4.

- **Stateless**: request and response are evaluated independently.
- **Numbered**: rules are evaluated in ascending order; the first match wins; there is an implicit deny at the end.
- **Allow and deny**: the only place in the VPC you can express "deny this range".

Because they are stateless, **every allowed flow needs a return rule**, normally the ephemeral range **1024–65535**. This
is the classic bug in §7.4: the connection establishes and then hangs.

Use NACLs as a **coarse second layer** — a blunt deny for a range, a guard on a sensitive subnet — and do the precise work
in security groups. A NACL as your primary firewall is a source of subtle outages.

### 5.6 SG references over CIDR rules

`[REAL, computed]` §7.5 — 263 / 258 / 12 reachable hosts.

A CIDR rule grants access to **whatever holds an address in that range, now or later**. A security-group reference grants
access to **membership of a role**, and membership changes as instances are created and destroyed. Inside a VPC, prefer
references; reserve CIDR rules for genuinely external sources, and keep those as narrow as you can.

### 5.7 Assumptions and limitations

- The CIDR plan, fleet sizes and rules are invented; the arithmetic and firewall semantics are real.
- IPv6, Transit Gateway, PrivateLink, AWS Network Firewall and flow-log analysis are out of scope (L08, L16).
- Some managed services place network interfaces in your subnets and consume addresses — count them in the plan.

---

## 6. Worked example — the deployment that ran out of addresses

**The situation.** A container platform ran in three `/26` private subnets, one per AZ — 59 usable addresses each,
comfortable for a steady state of about 40 tasks.

**What happened.**

1. A rolling deployment started new tasks before stopping old ones, briefly doubling the count (§5.1 — the deployment
   peak, not the steady state, sizes the subnet).
2. New tasks failed to launch with an address-exhaustion error. The deployment stalled half-migrated.
3. Growing the subnet was impossible: the adjacent space had already been allocated to another tier, and a subnet's CIDR
   cannot be resized (§5.1).
4. The workaround was new subnets in unallocated space, which required new route-table associations and new NACL rules —
   during an incident (M10-L14).
5. The root cause was a `/26` chosen to "keep the plan tidy" in a VPC using **7%** of its range.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Subnet sized for steady state | Size for the deployment peak, plus growth |
| 2 | No spare adjacent space | Leave >50% of the VPC unallocated and contiguous |
| 3 | Reserved and alignment addresses not counted | 5 per subnet; alignment waste (§5.1) |
| 4 | Managed-service interfaces not counted | Include them in the address budget |
| 5 | Address plan not reviewed against growth | Review when task counts change materially |

**The general rule.** **Address space is free until you need more of it, at which point it is a rebuild. Over-allocate.**

---

## 7. Practical activity

**File:** [`labs/m11/l07_vpc_subnets_security_groups.py`](../../labs/m11/l07_vpc_subnets_security_groups.py)

**No AWS account, no network, no third-party dependencies.** Uses Python's `ipaddress` module for real addressing
arithmetic, so you can plan a VPC offline and check it before building anything.

```bash
source .venv/bin/activate
python labs/m11/l07_vpc_subnets_security_groups.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. A CIDR PLAN, WITH AWS'S RESERVED ADDRESSES COUNTED
============================================================================
  VPC 10.20.0.0/16 -> 65,536 addresses

  subnet                    CIDR                   total   usable
  public-a                  10.20.0.0/24             256      251
  public-b                  10.20.1.0/24             256      251
  public-c                  10.20.2.0/24             256      251
  private-app-a             10.20.4.0/22           1,024    1,019
  private-app-b             10.20.8.0/22           1,024    1,019
  private-app-c             10.20.12.0/22          1,024    1,019
  private-data-a            10.20.16.0/24            256      251
  private-data-b            10.20.17.0/24            256      251
  private-data-c            10.20.18.0/24            256      251

  allocated 4,864/65,536 addresses (7%), 4,563 usable after reservations
  lost to ALIGNMENT (a /22 must start on a /22 boundary): 256 addresses
  AWS reserves 5 addresses in EVERY subnet, so 9 subnets lose 45 addresses
  before you launch anything. A /28 has 11 usable addresses, which is why /28
  subnets run out during a rolling deployment rather than at steady state.

============================================================================
2. WHY THESE TWO VPCs CANNOT BE PEERED
============================================================================
  our VPC: 10.20.0.0/16

  the other side                  their CIDR          overlaps?   consequence
  partner A (default template)    10.0.0.0/16                no   peering fine
  acquired company                10.20.0.0/16              YES   peering impossible without re-addressing
  our own second region           10.20.128.0/17            YES   peering impossible without re-addressing
  well-planned partner B          10.60.0.0/16               no   peering fine

  Row 3 is the one teams inflict on themselves: a second environment carved
  from inside the first VPC's range. Address space is the one decision you
  cannot change without rebuilding, so allocate from a central plan with room
  for regions, environments and companies you have not acquired yet.

============================================================================
3. ROUTE TABLES RESOLVE BY LONGEST PREFIX MATCH
============================================================================
  route             target
  10.20.0.0/16      local
  10.20.16.0/22     vpc-endpoint (S3 gateway)
  10.60.0.0/16      pcx-partner-b (peering)
  0.0.0.0/0         nat-gateway

  destination         matched route     target                            prefix
  10.20.3.14          10.20.0.0/16      local                             /16
  10.20.17.9          10.20.16.0/22     vpc-endpoint (S3 gateway)         /22
  10.60.2.200         10.60.0.0/16      pcx-partner-b (peering)           /16
  52.95.110.1         0.0.0.0/0         nat-gateway                       /0
  10.99.0.5           0.0.0.0/0         nat-gateway                       /0
  169.254.169.254     (link-local)      instance metadata, never routed   --

  The most specific route wins, always. Adding a /22 for an endpoint silently
  changes where a subset of traffic goes -- which is how a 'no change to the
  network' deploy stops reaching a service (M11-L08).

============================================================================
4. STATEFUL SECURITY GROUP VS STATELESS NETWORK ACL
============================================================================
  a client at 10.20.3.14 calls an instance on tcp/443; the response returns
  from the instance to the client's EPHEMERAL port 49512

  flow                       port       security group   NACL (broken)   NACL (fixed)
  inbound request             443              allowed         allowed        allowed
  outbound response         49512   allowed (stateful)         DROPPED        allowed

  The security group remembers the request, so the response is allowed without
  any outbound rule matching port 49512. A network ACL remembers NOTHING, so
  the response needs its OWN rule for the ephemeral range 1024-65535.
  This is the single most common NACL bug: connections that open and hang.
  Security groups also have NO deny rules -- everything not allowed is denied.

============================================================================
5. SG-REFERENCING VS CIDR RULES: WHAT CAN REACH THE DATABASE?
============================================================================
  database inbound rule                         reachable hosts   who
  source = 10.20.0.0/16 (the whole VPC)                     263   app servers, batch workers, bastio
  source = 10.20.16.0/22 (the app subnet)                   258   app servers, batch workers, anythi
  source = sg-app (security group reference)                 12   app servers

  A CIDR rule grants access to an ADDRESS RANGE, which means to anything that
  ever gets an address in it -- including the instance someone launches next
  month. A security-group reference grants access to a ROLE, and the set
  updates itself. Prefer SG references inside the VPC (M10-L07).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every subnet calculation, overlap test, longest-prefix match, firewall
  verdict and host count above is computed by this script, using Python's
  ipaddress module for the addressing arithmetic.

  VERIFIED BEHAVIOUR: AWS reserves 5 addresses per subnet; routes resolve by
  longest prefix match; security groups are stateful and allow-only; network
  ACLs are stateless, numbered, and evaluated in order with allow and deny.

  ILLUSTRATIVE: the CIDR plan, fleet sizes and rule sets are invented.

  NOT SHOWN: Transit Gateway, IPv6, PrivateLink, Network Firewall and
  flow-log analysis (M11-L08, M11-L16).

Done.
```

### 7.3 Reading the result

**Section 1's last two lines** are the numbers people omit from a plan: 45 addresses reserved, 256 lost to alignment.

**Section 2, row 3** is self-inflicted and extremely common.

**Section 3, row 2** shows a more specific route taking traffic away from `local`.

**Section 4's second row** is the ephemeral-port bug in one line: the security group allows it, the NACL drops it.

**Section 5** is 263 hosts versus 12, for the same intent.

---

## 8. Common mistakes and troubleshooting

1. **Using `10.0.0.0/16`** because it is the default. §5.2 — it is everyone's default.
2. **Sizing subnets for steady state.** §6 — size for the deployment peak.
3. **Forgetting the 5 reserved addresses.** §5.1 — a `/28` has 11 usable.
4. **Allocating the whole VPC immediately.** Leave contiguous space for growth.
5. **Carving a second environment out of an existing VPC's range.** §7.2, row 3.
6. **Using NACLs as the primary firewall.** §5.5 — stateless, subtle, and it will hang connections.
7. **Omitting the ephemeral return rule.** §7.4.
8. **CIDR rules where an SG reference would do.** §7.5 — 263 hosts versus 12.
9. **Unrestricted egress everywhere.** The exfiltration path (M9-L12, L08).

| Symptom | Likely cause | Fix |
|---|---|---|
| Tasks fail to launch during deploys | Subnet too small for the peak | Larger subnets; deployment-aware sizing |
| Connection opens then hangs | NACL missing the ephemeral return rule | Allow 1024–65535 outbound (§5.5) |
| Traffic goes somewhere unexpected | A more specific route was added | Check longest prefix match (§5.3) |
| Cannot peer with a partner | Overlapping CIDRs | Central address register; re-address one side |
| A new instance can unexpectedly reach the database | CIDR-based rule | Switch to an SG reference (§5.6) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Egress control is the network half of M10-L10: an assistant that can reach arbitrary destinations can
  exfiltrate (L08 covers endpoints and NAT).
- **Privacy.** Data-tier subnets with no route to the internet are a concrete residency and exposure control (M10-L06).
- **Reliability.** Subnets per AZ are what make multi-AZ possible (L02); address exhaustion is an outage with no quick fix.
- **Cost.** Cross-AZ traffic and NAT data processing are network design decisions with monthly bills (L02, L06, L08).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. How many usable addresses are in a `/28`? A `/24`?
2. Why can `10.20.128.0/17` not be peered with `10.20.0.0/16`?
3. Which route does `10.20.17.9` take in §7.3, and why?
4. Why does the security group allow the response in §7.4?
5. How many hosts can reach the database under each of the three rules in §7.5?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the VPC to a `/18` and see which tiers still fit.
2. Add a fourth AZ to the layout and recompute the allocation.
3. Add a route `10.20.17.0/24 -> pcx-partner-b` and re-resolve the destinations.
4. Add a NACL rule set of your own and test a flow on port 5432.
5. Write the security-group rules for a three-tier application using only SG references.

### Exercise 3 — Challenge (~60 min)

1. Produce a full address plan for three regions × three environments from a single `/8`, with the register.
2. Extend the lab's firewall evaluator to handle multiple security groups attached to one interface.
3. Model your own VPC's subnets and compute the deployment-peak headroom.
4. Design the egress restriction for a subnet that must reach only AWS services and one partner API.
5. Write the test that fails CI if any security group allows `0.0.0.0/0` inbound on a non-load-balancer interface.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l07).)*

**Q1.** How many addresses does AWS reserve in each subnet?

- A. Two
- B. Five
- C. None
- D. One per Availability Zone

**Q2.** How many usable addresses does a `/28` subnet provide?

- A. 16
- B. 14
- C. 11
- D. 8

**Q3.** Why can a subnet not span two Availability Zones?

- A. Route tables associate with a single AZ
- B. Security groups are AZ-scoped
- C. CIDR blocks cannot be split across AZs
- D. A subnet is defined as existing in exactly one AZ

**Q4.** Two VPCs use `10.20.0.0/16` and `10.20.128.0/17`. What is the consequence?

- A. They can peer, since one is more specific
- B. They can peer if the route tables exclude the overlap
- C. They cannot be peered without re-addressing one side
- D. They can peer, but only within one region

**Q5.** A route table has `10.20.0.0/16 -> local` and `10.20.16.0/22 -> endpoint`. Where does `10.20.17.9` go?

- A. To the endpoint — the longest prefix wins
- B. To local — the VPC route always takes precedence
- C. To whichever route was created first
- D. The traffic is dropped as ambiguous

**Q6.** What makes a subnet "public"?

- A. It has public IP addresses assigned
- B. Its network ACL allows inbound traffic from the internet
- C. Its security groups permit `0.0.0.0/0`
- D. Its route table has a route to an internet gateway

**Q7.** Why does a security group allow a response on an ephemeral port with no matching rule?

- A. Ephemeral ports are exempt from filtering
- B. It is stateful and remembers the request
- C. Outbound rules default to allow-all
- D. Responses are evaluated by the network ACL instead

**Q8.** What is the most common network ACL bug?

- A. Rules evaluated in the wrong numeric order
- B. The implicit deny at the end of the list
- C. Missing the return rule for ephemeral ports 1024–65535
- D. Associating the ACL with the wrong route table

**Q9.** Which statement about security groups is true?

- A. They support deny rules for specific CIDRs
- B. They are evaluated before network ACLs on inbound traffic
- C. They attach to subnets rather than interfaces
- D. They are allow-only; anything not allowed is denied

**Q10.** Why prefer a security-group reference to a CIDR rule inside a VPC?

- A. It grants access to a role, and membership updates itself
- B. It evaluates faster than a CIDR comparison
- C. It is required for cross-AZ traffic
- D. It avoids the need for a route table entry

**Q11.** In §7.5, how many hosts could reach the database when the rule allowed the whole VPC?

- A. 263
- B. 258
- C. 12
- D. 240

**Q12.** Why should more than half the VPC range be left unallocated?

- A. AWS charges for allocated address space
- B. Subnets cannot be resized, so growth needs contiguous free space
- C. Route tables have a limit on the number of entries
- D. Unallocated space improves longest-prefix matching

**Q13.** *(Written, rubric-graded.)* In under 150 words: you are designing a VPC for an AI application with a container
platform, a database and a load balancer, across three AZs. Describe your address plan and your inbound rules for the
database.

---

## 12. Revision notes

- **Reserved and alignment**: **5 addresses per subnet** (9 subnets → 45), plus alignment waste (**256** in the lab). A
  `/28` has **11** usable.
- **Size for the deployment peak**, not steady state; leave **>50%** of the VPC free and contiguous.
- **Never overlap CIDRs** — peering, transit and VPN all break; the self-inflicted case is carving an environment out of
  an existing range.
- **Longest prefix match wins**; a subnet is public because of a route to an internet gateway, not a setting.
- **Security groups**: stateful, allow-only, attached to interfaces, evaluated as a union, can reference other groups.
- **Network ACLs**: stateless, numbered, allow and deny — every flow needs its **ephemeral return rule (1024–65535)**.
- **SG references beat CIDR rules**: **12** reachable hosts versus **263** for the same intent.

---

## 13. Completion checklist

- [ ] My address plan counts reserved addresses, alignment, and the deployment peak.
- [ ] Ranges come from a central register and do not overlap anything we may need to connect.
- [ ] I can resolve a route table by longest prefix match and predict what a new route changes.
- [ ] I can explain stateful versus stateless, and I know where the ephemeral return rule goes.
- [ ] Inbound rules inside the VPC use security-group references, not CIDRs.
- [ ] Egress is restricted for anything handling untrusted input.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon VPC User Guide — VPC and subnet sizing, the five reserved addresses per subnet, route tables and longest prefix
  match, security groups (stateful) and network ACLs (stateless) `[STABLE]`
- M11-L02 (AZs and cross-AZ transfer costs) and M11-L08 (NAT, endpoints, public vs private) `[STABLE]`
- M10-L10 (exfiltration paths) and M9-L12 (egress allowlists and SSRF) `[STABLE]`
- M10-L07 (network controls as one layer of tenant isolation) `[STABLE]`

---

## 15. Next lesson

→ [M11-L08 — Public vs Private Access, NAT and Endpoints](M11-L08-public-private-nat-endpoints.md) takes the routing
you can now read and turns it into the egress decision: how private workloads reach AWS services and the internet, what
each path costs, and which one is an exfiltration channel.
