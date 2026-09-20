# M11-L09 — DNS, TLS and Load Balancing

| | |
|---|---|
| **Lesson ID** | M11-L09 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M11-L08](M11-L08-public-private-nat-endpoints.md), [M2-L11](../module-02-python-foundations/M2-L11-http-rest.md) |

---

## 1. Learning objectives

1. **Plan** DNS TTLs in advance, and explain why DNS is a poor failover mechanism.
2. **Track** certificates by days remaining and by whether they renew themselves.
3. **Choose** a load-balancing algorithm knowing what it does and does not fix.
4. **Set** health-check interval and threshold from your own flake rate.
5. **Set** deregistration delay from your p99 request duration, not from a default.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **TTL** | How long resolvers may cache a DNS answer. |
| **Alias record** | A Route 53 record pointing at an AWS resource, resolving to its current addresses. |
| **ACM** | AWS Certificate Manager — issues and, for DNS-validated certificates, renews TLS certificates. |
| **DNS validation** | Proving domain control with a CNAME record; enables automatic renewal while the record remains. |
| **ALB** | Application Load Balancer — layer 7; routes on host, path and headers; terminates TLS. |
| **NLB** | Network Load Balancer — layer 4; preserves the source address; static IPs; very high throughput. |
| **Target group** | The set of backends a load balancer sends to, with its own health check. |
| **Least outstanding requests** | Sending each request to the target with the fewest in flight. |
| **Deregistration delay** | How long a target keeps serving in-flight requests after being removed. |

---

## 3. Plain-language explanation

### 3.1 A TTL is a promise you cannot withdraw

§7.1: with a 1-hour TTL, half of clients move within **~30 minutes** and 99% within **~59** — and the worst case is the
full hour. Lowering the TTL **after** you need to change a record does nothing for caches already holding the old answer.
Lower it days in advance, or design so you do not need a DNS change: an **alias record to a load balancer** changes
backends without changing DNS at all.

### 3.2 Certificates fail on a date, silently, until they don't

§7.2 tracks six certificates. **3 of 6 will not renew themselves** — email-validated and uploaded ones. One is already
**3 days expired**. ACM certificates validated by DNS renew automatically *for as long as the validation CNAME stays in
the zone*, so the real failure mode is someone tidying up "unused" DNS records.

### 3.3 Load balancing helps with a slow backend; it does not fix one

§7.3: one backend 7× slower than the others. Round robin sends it **25.0%** of traffic regardless, and the fleet p95 is
**865 ms**. Least-outstanding-requests reduces its share to **14.6%** and the p95 to **751 ms** — an improvement, not a
cure. Health checks remove a *dead* backend; nothing removes a *slow* one, which is why slow is worse.

### 3.4 Health checks trade detection time against false removals

§7.4, at a 2% per-check flake rate: a 5-second interval with a threshold of 2 detects in **10 s** and falsely removes a
healthy target **6.91 times a day**. A 30-second interval with a threshold of 5 falsely removes essentially never — and
takes **150 s** to notice a real failure.

### 3.5 Deregistration delay is set by your slowest requests

§7.5, with a long-tailed mix (p50 **1.8 s**, p95 **14.0 s**, p99 **35.0 s**): a delay of 0 cuts **100%** of in-flight
requests; 5 seconds still cuts **21.03%**; 30 seconds cuts **1.41%**. The requests cut are the slow ones — for an AI
system, the streaming answers someone is actively reading.

---

## 4. Analogy

**A shop's phone number, its opening hours sign, and its queue.** The number in the printed directory (DNS with a long
TTL) cannot be corrected until the next printing, however loudly you announce the change. The certificate is the licence
in the window with a date on it — nobody notices until an inspector does, and then you are closed. The queue policy
matters: sending every fourth customer to the slow till keeps that queue growing, and moving people to the shortest queue
helps without making the slow till fast. And if you shut a till with people still at it, they lose their place.

### Where the analogy breaks

- **A directory is reprinted on a schedule; DNS caches expire independently everywhere**, so there is no moment when the
  change is complete (§5.1).
- **A till can be watched; a slow backend looks healthy to a health check** that only asks whether it answers (§5.4).

---

## 5. Detailed technical explanation

### 5.1 DNS

`[REAL, computed]` §7.1.

| Decision | Guidance |
|---|---|
| TTL for records you may need to change | 60 s, set **days before** the change |
| TTL for stable records | 3,600 s+ — fewer queries, lower cost |
| Pointing at an AWS load balancer | Use an **alias** record; the balancer's addresses change and the alias follows |
| Failover | Prefer a load balancer or a health-checked routing policy; DNS alone is slow and cache-dependent |
| Apex domain (`example.com`) | Alias records work where a CNAME is not permitted |

Route 53 routing policies — weighted, latency, failover, geolocation — are useful, but every one of them inherits the
cache problem. For fast failover, keep a single stable name and move what is *behind* it.

### 5.2 TLS and certificate lifecycle

`[REAL, computed]` §7.2 — 3 of 6 need a human; 1 already expired.

- **ACM, DNS-validated**: renews automatically while the validation CNAME remains in the zone. This is the default you
  want.
- **ACM, email-validated**: requires a person to act on an email, at an address that may no longer be monitored.
- **Uploaded certificates**: renew only when you replace them.
- **Private CA / internal certificates**: your own lifecycle, your own automation.

Controls: **alarm on days-remaining** (30 and 14 days), not on expiry; protect validation CNAMEs from "cleanup"; list
certificates with their sources in the inventory (M10-L03); and remember that certificates on *clients* — mutual TLS,
partner integrations — expire too, and their expiry is someone else's calendar.

Terminate TLS at the load balancer for ALB workloads; re-encrypt to the backend where the traffic is sensitive or a
compliance requirement says so. Keep the minimum TLS version and cipher policy current.

### 5.3 ALB or NLB

| | ALB (layer 7) | NLB (layer 4) |
|---|---|---|
| Routes on | Host, path, headers, query, method | Address and port |
| TLS | Terminates; can re-encrypt | Passthrough or terminate |
| Source IP | In `X-Forwarded-For` | Preserved |
| Static IPs | No | Yes (one per AZ) |
| Good for | HTTP APIs, web apps, path-based routing to services | Very high throughput, non-HTTP protocols, IP allowlisting by partners |

For most AI applications an **ALB** is right: HTTP, path routing to several services, TLS termination, and
least-outstanding-requests. Choose an NLB when a partner must allowlist your addresses, or when the protocol is not HTTP.

Two AI-specific details: **long streaming responses** need an idle timeout set above your p99 (the default is typically
far too short for a streamed answer), and **request/response buffering** behaviour differs between balancer types —
verify streaming works end to end rather than assuming.

### 5.4 Balancing algorithms

`[REAL, simulated]` §7.3 — 25.0% → 14.6% share, 865 ms → 751 ms p95.

- **Round robin** ignores backend state entirely. It is fine when backends are identical and requests are uniform —
  neither of which is true of AI workloads, where one request may take 50× another.
- **Least outstanding requests** responds to actual load, which matters when request cost varies widely.

Neither fixes a slow backend. The real controls are: making slowness visible (p95 per target, not per fleet), health
checks that fail on latency as well as on errors where the platform supports it, and automatic replacement of
persistently slow targets.

### 5.5 Health checks

`[REAL, computed]` §7.4.

```text
detection time (worst case) = interval × unhealthy_threshold
false removals per day      ≈ (86400 / interval) × flake_rate ^ threshold
```

Design notes:

- The health endpoint should check **what the target needs to serve** — can it reach its database, is the model client
  configured — and nothing more. A health check that calls a shared dependency turns one dependency failure into a
  fleet-wide removal.
- Make it **cheap**, because it runs constantly from every balancer node.
- Separate **liveness** ("restart me") from **readiness** ("do not send traffic yet"), especially for workloads with a
  long warm-up such as a model client or a loaded index.
- Measure your flake rate before choosing the interval and threshold.

### 5.6 Deregistration delay and draining

`[REAL, computed]` §7.5 — 100% / 21.03% / 1.41% / 0.30% / 0% of in-flight requests cut at 0 / 5 / 30 / 60 / 300 seconds.

Set the delay from your **p99 request duration**, and accept the cost: deployments and scale-in take at least that long.
For streaming responses, the duration is the *whole stream*, not the time to first token — a 300-second answer needs a
300-second delay or the user loses a partially-read response (M13-L11).

Pair it with graceful shutdown in the application: stop accepting new work, finish what is in flight, then exit.

### 5.7 Assumptions and limitations

- TTL propagation is modelled as uniform expiry; real propagation is **slower** because resolvers cache independently and
  some ignore short TTLs.
- Backend latencies, flake rates, request durations and certificate dates are invented.
- Idle timeouts, WAF, CDN behaviour and Route 53 routing policies are out of scope.

---

## 6. Worked example — the streaming answers that vanished at every deploy

**The situation.** An assistant streamed answers over HTTP. Deployments were routine and automated. Support reported
occasional complaints that answers "stopped halfway", clustered without an obvious pattern.

**What was happening.**

1. The target group's deregistration delay was the default, far below the p99 answer duration (§7.5).
2. Every deployment cut in-flight streams. At roughly six deploys a week and 40 requests per second per target, the
   affected count was small per deploy and invisible in aggregate metrics.
3. The clustering was by **time of day** — the deployment window — which nobody had plotted (M10-L14 §5.1).
4. The load balancer's **idle timeout** was also below the p99, so the slowest answers were cut even without a deploy
   (§5.3).
5. The application had no graceful shutdown: on `SIGTERM` it exited immediately (§5.6).

| # | What went wrong | Fix |
|---|---|---|
| 1 | Deregistration delay below p99 | Set from p99 stream duration (§5.6) |
| 2 | Idle timeout below p99 | Raise above the longest expected stream |
| 3 | No graceful shutdown | Drain on `SIGTERM`, then exit |
| 4 | Failures invisible in aggregates | Track incomplete-stream rate as a slice metric (M10-L08, M10-L12) |
| 5 | Not correlated with deploys | Overlay deployment markers on error charts (L16) |

**The general rule.** **Every timeout and delay at the edge must be set from your p99, and AI p99s are measured in
minutes, not milliseconds.**

---

## 7. Practical activity

**File:** [`labs/m11/l09_dns_tls_load_balancing.py`](../../labs/m11/l09_dns_tls_load_balancing.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l09_dns_tls_load_balancing.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1109)`; run twice, output
identical.

```text

============================================================================
1. HOW LONG DOES A DNS CHANGE TAKE?
============================================================================
  5,000 clients hold a cached answer; you change the record at t=0

  TTL            50% moved   99% moved   worst case   failover usefulness
  1 minute           0.5 m       1.0 m          1 m   usable for failover
  5 minutes          2.5 m       4.9 m          5 m   slow
  1 hour            30.5 m      59.5 m         60 m   NOT a failover mechanism
  1 day            707.2 m    1422.1 m       1440 m   NOT a failover mechanism

  A record's TTL is a promise you made to every resolver on the internet, and
  you cannot withdraw it. Lower the TTL BEFORE you need to change the record;
  lowering it afterwards changes nothing for the caches already holding the
  old answer. And note the last column: DNS is a poor failover mechanism
  because you do not control the caches (M11-L02).

============================================================================
2. THE CERTIFICATE FLEET
============================================================================
  name                        source                    days left  auto-renew   status
  api.example.com             ACM, DNS-validated               71         yes   fine
  www.example.com             ACM, DNS-validated               44         yes   fine
  legacy.example.com          ACM, EMAIL-validated             19          NO   manual renewal needed
  partner-mtls.example.com    uploaded to ACM                   9          NO   URGENT
  internal-ca.example.local   private CA                      123         yes   fine
  old-lb.example.com          uploaded to ACM                  -3          NO   EXPIRED -- clients are failing now

  certificates that will NOT renew themselves: 3/6
  ACM certificates validated by DNS renew automatically for as long as the
  validation CNAME stays in the zone -- so the failure mode is someone tidying
  up 'unused' DNS records. Email-validated and uploaded certificates renew
  only when a person does it. Alarm on days-remaining, not on expiry.

============================================================================
3. ROUND ROBIN VS LEAST OUTSTANDING REQUESTS
============================================================================
  4 backends, one of them 7x slower; 3,000 requests at 5/second

  policy                                   p50       p95   share sent to the slow backend
  round robin                            104 ms     865 ms                     25.0%
  least outstanding requests             100 ms     751 ms                     14.6%

  Round robin sends exactly one quarter of the traffic to the slow backend
  whatever happens to it, so requests queue behind it and the p95 is dominated
  by it. Least-outstanding-requests skips a busy backend, so the slow one gets
  traffic only while it is idle: its share falls from 25% to 15% and the p95
  from 865 ms to 751 ms. That is an improvement, not a cure -- and it is the
  honest result. A slow backend still serves real users slowly. Health checks
  remove a DEAD backend (section 4); nothing removes a slow one, which is why
  it does more damage (M13-L11).

============================================================================
4. HEALTH CHECKS: DETECTION TIME VS FALSE ALARMS
============================================================================
  a healthy target fails a single check 2% of the time [ILLUSTRATIVE]

    interval  threshold  detect (worst)   false removals/day
         5 s          2            10 s                 6.91
        10 s          2            20 s                 3.46
        30 s          2            60 s                 1.15
        10 s          3            30 s                 0.07
        30 s          5           150 s                 0.00

  Detection time is interval x threshold, and false removals scale with the
  check RATE times the failure probability raised to the threshold. A 5-second
  interval with a threshold of 2 detects in 10 s and removes a healthy target
  several times a day; 30 s with a threshold of 5 essentially never does, and
  takes 150 s to notice a real failure. Pick from your own flake rate.

============================================================================
5. DEREGISTRATION DELAY: WHAT HAPPENS TO IN-FLIGHT REQUESTS?
============================================================================
  request duration: p50 1.8 s, p95 14.0 s, p99 35.0 s [ILLUSTRATIVE long-tailed mix]

  deregistration delay      requests cut   share of in-flight
                    0 s          72.9              100.00%
                    5 s          15.3               21.03%
                   30 s           1.0                1.41%
                   60 s           0.2                0.30%
                  300 s           0.0                0.00%

  A delay of 0 cuts every in-flight request. The interesting rows are the
  middle ones: a 30-second delay still cuts the requests that were always
  going to be slow -- which, for an AI system, are the streaming answers a
  user is actively watching. Set the delay from your p99, not from a default,
  and accept that deployments and scale-in get slower (M13-L11, M13-L14).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every propagation figure, days-remaining calculation, latency
  percentile, detection time and loss count above is computed by this script.

  ILLUSTRATIVE: TTL client behaviour is modelled as uniform expiry, which
  ignores resolver-side caching that makes real propagation SLOWER. Backend
  latencies, flake rates and traffic figures are invented.

  NOT SHOWN: TLS handshake mechanics and cipher selection, ALB vs NLB
  selection in depth, Route 53 routing policies, and WAF (M11-L12, M12-L11).

Done.
```

### 7.3 Reading the result

**Section 1's last column** is the conclusion: above a 60-second TTL, DNS is not a failover mechanism.

**Section 2's count** — 3 of 6 needing a human — is the normal state of a certificate estate.

**Section 3 is deliberately unflattering to load balancing**: the p95 improves from 865 ms to 751 ms and the slow backend
is still serving users slowly.

**Section 5's middle rows** are the ones to take to a design discussion.

---

## 8. Common mistakes and troubleshooting

1. **Lowering a TTL at the moment you need the change.** §5.1 — lower it days earlier.
2. **Using DNS for failover.** §5.1 — move what is behind a stable name.
3. **Deleting "unused" DNS records.** §5.2 — that CNAME is what renews your certificate.
4. **Alarming on certificate expiry rather than days remaining.** §5.2.
5. **Assuming a load balancer fixes a slow backend.** §5.4 — 25% → 15% is not a fix.
6. **Health checks that call shared dependencies.** §5.5 — one failure removes the whole fleet.
7. **Health-check interval chosen without measuring flake.** §7.4 — 6.91 false removals a day.
8. **Default deregistration delay and idle timeout for streaming workloads.** §7.5, §6.
9. **No graceful shutdown.** The delay achieves nothing if the process exits immediately.

| Symptom | Likely cause | Fix |
|---|---|---|
| Some clients still hit the old endpoint | TTL not lowered in advance | Plan TTL changes days ahead; use aliases |
| TLS failures on a fixed date | Certificate not auto-renewing | ACM DNS validation; alarm on days remaining |
| p95 much worse than p50 | One slow target taking its share | Per-target latency; replace persistently slow targets |
| Targets flap in and out | Interval and threshold too aggressive | Raise threshold; measure flake rate first |
| Streams truncate during deploys | Deregistration delay below p99 | Set from p99; add graceful shutdown |

---

## 9. Security, privacy, reliability, cost

- **Security.** TLS everywhere, current minimum versions, and mutual TLS where partners require it; the load balancer is
  also where WAF attaches (L10).
- **Privacy.** Logs at the edge contain addresses and paths — personal data with a retention rule (M10-L06, M10-L13).
- **Reliability.** Health checks, deregistration delay and idle timeouts are the three settings that most often cause
  self-inflicted user-visible errors.
- **Cost.** Load balancer hourly and capacity-unit charges, and DNS query charges at high TTL-miss rates, are both real
  lines (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. With a 1-hour TTL, when have 99% of clients moved?
2. Which certificate types in §7.2 renew themselves?
3. What share of traffic did round robin send to the slow backend?
4. What is the detection time for a 30-second interval with threshold 5?
5. What share of in-flight requests is cut by a 5-second deregistration delay?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a 30-second TTL and compare it with 60.
2. Add two certificates of your own to §7.2 with real dates.
3. Change the slow backend to 2× and see how much of the p95 gap closes.
4. Change the flake rate to 0.5% and re-choose an interval and threshold.
5. Compute the deregistration delay you need from your own p99.

### Exercise 3 — Challenge (~60 min)

1. Write the runbook for changing a production DNS record, with the TTL timeline.
2. Build the certificate inventory with source, expiry, auto-renewal and owner (M10-L03).
3. Design health endpoints for a service with a slow-loading index: liveness and readiness separately.
4. Measure the incomplete-stream rate for a streaming endpoint and set the edge timeouts from it.
5. Add deployment markers to your latency dashboards and look for the pattern in §6.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l09).)*

**Q1.** When should a TTL be lowered before a planned DNS change?

- A. Days in advance, so caches hold the short TTL
- B. At the moment the record is changed
- C. Immediately after the change, to speed up propagation
- D. TTL does not affect how quickly a change takes effect

**Q2.** Why is DNS a poor failover mechanism?

- A. Route 53 health checks are evaluated only hourly
- B. Records cannot be changed programmatically
- C. You do not control resolver caches, so old answers persist
- D. Alias records cannot point at load balancers

**Q3.** Which certificates renew automatically?

- A. Certificates uploaded to ACM
- B. All ACM certificates regardless of validation method
- C. Email-validated ACM certificates
- D. ACM certificates validated by DNS, while the validation CNAME remains

**Q4.** What is the common failure mode for automatic renewal?

- A. The certificate authority rotating its root
- B. Someone deleting the validation CNAME as an unused record
- C. The load balancer caching the old certificate
- D. Renewal requiring a maintenance window

**Q5.** In §7.3, what share of traffic did round robin send to the slow backend?

- A. 14.6%
- B. 0%
- C. 25.0%
- D. It varied with the backend's queue depth

**Q6.** What did least-outstanding-requests achieve there?

- A. It removed the slow backend from the pool
- B. It reduced the slow backend's share and improved p95, without fixing slowness
- C. It eliminated the p95 gap entirely
- D. It made no measurable difference

**Q7.** Why is a slow backend worse than a dead one?

- A. Slow backends consume more of the load balancer's capacity units
- B. Dead backends trigger an incident, slow ones do not
- C. Health checks remove the dead one; nothing removes the slow one
- D. Slow backends fail health checks intermittently, causing flapping

**Q8.** How is worst-case health-check detection time calculated?

- A. Interval plus threshold
- B. Interval divided by threshold
- C. Threshold multiplied by the flake rate
- D. Interval multiplied by the unhealthy threshold

**Q9.** Why should a health endpoint avoid calling shared dependencies?

- A. One dependency failure would remove every target at once
- B. It would make the check too slow to complete in the interval
- C. Load balancers cannot follow redirects from health endpoints
- D. Shared dependencies are not reachable from the balancer's subnets

**Q10.** In §7.5, what share of in-flight requests did a 5-second deregistration delay cut?

- A. 1.41%
- B. 100%
- C. 0.30%
- D. 21.03%

**Q11.** How should deregistration delay be chosen?

- A. From the p99 request duration, including full streaming time
- B. From the mean request duration
- C. From the deployment frequency
- D. From the health-check interval

**Q12.** When is an NLB the better choice than an ALB?

- A. When routing by URL path to several services
- B. When a partner must allowlist static IP addresses, or the protocol is not HTTP
- C. When TLS must be terminated at the load balancer
- D. When least-outstanding-requests balancing is needed

**Q13.** *(Written, rubric-graded.)* In under 150 words: users report that streamed answers occasionally stop halfway.
Describe the edge settings you would check and what you would set each of them from.

---

## 12. Revision notes

- **TTL is a promise**: at 1 hour, 99% of clients move in **~59 minutes**. Lower TTLs days in advance; prefer alias
  records; DNS is not failover.
- **Certificates**: **3 of 6** in the lab need a human; ACM **DNS-validated** renews itself while the CNAME remains. Alarm
  on days remaining.
- **Balancing**: round robin sent **25.0%** to a 7× slow backend (p95 **865 ms**); least-outstanding **14.6%**
  (p95 **751 ms**) — better, not fixed.
- **Health checks**: detect = interval × threshold; false removals ≈ rate × flake^threshold. 5 s/2 → **10 s** detect,
  **6.91** false removals/day; 30 s/5 → **150 s**, ~0.
- **Deregistration delay** from p99: 0 s cuts **100%**, 5 s cuts **21.03%**, 30 s cuts **1.41%** of in-flight requests.
- **Streaming changes every timeout**: idle timeout and drain must exceed the whole stream duration.

---

## 13. Completion checklist

- [ ] TTLs are planned ahead of changes; public names are alias records to load balancers.
- [ ] Every certificate is inventoried with source, expiry, auto-renewal status and owner.
- [ ] Alarms fire on days-remaining, and validation CNAMEs are protected from cleanup.
- [ ] Health checks are cheap, local, and tuned from a measured flake rate.
- [ ] Deregistration delay and idle timeout are set from p99, and the app shuts down gracefully.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon Route 53 — alias records, TTLs, routing policies and health checks `[STABLE]`
- AWS Certificate Manager — DNS validation and automatic renewal; managed renewal requires the validation record to remain `[STABLE]`
- Elastic Load Balancing — ALB vs NLB, target groups, health checks, deregistration delay, idle timeout `[STABLE]`
- M13-L11 (latency percentiles and load testing) and M13-L14 (canary releases) `[STABLE]`
- M11-L08 (what sits behind the public edge) and M11-L16 (edge logs and alarms) `[STABLE]`

---

## 15. Next lesson

→ [M11-L10 — S3: Buckets, Permissions, Encryption, Lifecycle](M11-L10-s3-buckets-permissions-encryption.md) moves to
storage, where most AI systems keep their documents — and where the best-known cloud failure mode, the accidentally public
bucket, still happens.
