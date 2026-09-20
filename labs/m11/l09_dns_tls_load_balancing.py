"""M11-L09 lab -- the public edge: names, certificates, balancing and health.
This lab computes:

  1. how long a DNS change takes to take effect, by TTL,
  2. a certificate fleet: days remaining, and which renew themselves,
  3. round robin vs least-outstanding-requests when backends are not identical,
  4. health-check detection time, and the false-positive cost of making it faster,
  5. deregistration delay: requests lost when an instance leaves the pool.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l09_dns_tls_load_balancing.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1109)

# ============================================================ 1
rule("1. HOW LONG DOES A DNS CHANGE TAKE?")

TTLS = [(60, "1 minute"), (300, "5 minutes"), (3600, "1 hour"), (86400, "1 day")]
CLIENTS = 5000
print(f"  {CLIENTS:,} clients hold a cached answer; you change the record at t=0\n")
print(f"  {'TTL':<12}{'50% moved':>12}{'99% moved':>12}{'worst case':>13}   failover usefulness")
for ttl, label in TTLS:
    # a client moves when its cached copy expires: uniform over [0, TTL) plus resolver caching
    ages = [rng.random() * ttl for _ in range(CLIENTS)]
    ages.sort()
    p50 = ages[CLIENTS // 2]
    p99 = ages[int(CLIENTS * 0.99)]
    use = "usable for failover" if ttl <= 60 else ("slow" if ttl <= 300 else "NOT a failover mechanism")
    print(f"  {label:<12}{p50 / 60:>10.1f} m{p99 / 60:>10.1f} m{ttl / 60:>11.0f} m   {use}")
print("\n  A record's TTL is a promise you made to every resolver on the internet, and")
print("  you cannot withdraw it. Lower the TTL BEFORE you need to change the record;")
print("  lowering it afterwards changes nothing for the caches already holding the")
print("  old answer. And note the last column: DNS is a poor failover mechanism")
print("  because you do not control the caches (M11-L02).")


# ============================================================ 2
rule("2. THE CERTIFICATE FLEET")

TODAY = 0
CERTS = [
    ("api.example.com",          "ACM, DNS-validated",     71,  True),
    ("www.example.com",          "ACM, DNS-validated",     44,  True),
    ("legacy.example.com",       "ACM, EMAIL-validated",   19,  False),
    ("partner-mtls.example.com", "uploaded to ACM",         9,  False),
    ("internal-ca.example.local", "private CA",            123, True),
    ("old-lb.example.com",       "uploaded to ACM",        -3,  False),
]
print(f"  {'name':<28}{'source':<24}{'days left':>11}{'auto-renew':>12}   status")
for name, source, days, auto in CERTS:
    if days < 0:
        status = "EXPIRED -- clients are failing now"
    elif days < 14:
        status = "URGENT" if not auto else "renewing"
    elif not auto:
        status = "manual renewal needed"
    else:
        status = "fine"
    print(f"  {name:<28}{source:<24}{days:>11}{('yes' if auto else 'NO'):>12}   {status}")
manual = [c for c in CERTS if not c[3]]
print(f"\n  certificates that will NOT renew themselves: {len(manual)}/{len(CERTS)}")
print("  ACM certificates validated by DNS renew automatically for as long as the")
print("  validation CNAME stays in the zone -- so the failure mode is someone tidying")
print("  up 'unused' DNS records. Email-validated and uploaded certificates renew")
print("  only when a person does it. Alarm on days-remaining, not on expiry.")


# ============================================================ 3
rule("3. ROUND ROBIN VS LEAST OUTSTANDING REQUESTS")

BACKENDS = {"fast-1": 90, "fast-2": 95, "fast-3": 100, "slow (cold cache)": 700}   # mean ms
REQUESTS = 3000
ARRIVAL_MS = 200.0        # 5 requests/second -- below total capacity, so queues stay finite


def simulate(policy: str, seed: int) -> tuple[float, float, dict[str, int]]:
    r = random.Random(seed)
    names = list(BACKENDS)
    busy_until = {b: 0.0 for b in names}
    completions = {b: [] for b in names}     # completion times of requests sent to b
    sent = {b: 0 for b in names}
    latencies = []
    clock = 0.0
    for i in range(REQUESTS):
        clock += ARRIVAL_MS
        if policy == "round robin":
            b = names[i % len(names)]
        else:
            # least outstanding: fewest requests still in flight, ties broken at random
            outstanding = {n: sum(1 for c in completions[n] if c > clock) for n in names}
            fewest = min(outstanding.values())
            b = r.choice([n for n in names if outstanding[n] == fewest])
        start = max(clock, busy_until[b])                 # one request at a time per backend
        service = BACKENDS[b] * (0.7 + 0.6 * r.random())
        finish = start + service
        busy_until[b] = finish
        completions[b].append(finish)
        sent[b] += 1
        latencies.append(finish - clock)                  # queueing + service
    latencies.sort()
    return latencies[len(latencies) // 2], latencies[int(len(latencies) * 0.95)], sent


print(f"  {len(BACKENDS)} backends, one of them {BACKENDS['slow (cold cache)'] // 95}x slower; "
      f"{REQUESTS:,} requests at {1000 / ARRIVAL_MS:.0f}/second\n")
print(f"  {'policy':<34}{'p50':>10}{'p95':>10}   share sent to the slow backend")
for policy in ("round robin", "least outstanding requests"):
    p50, p95, sent = simulate(policy, 909)
    slow_share = sent["slow (cold cache)"] / REQUESTS
    print(f"  {policy:<34}{p50:>8.0f} ms{p95:>8.0f} ms{slow_share:>26.1%}")
print("\n  Round robin sends exactly one quarter of the traffic to the slow backend")
print("  whatever happens to it, so requests queue behind it and the p95 is dominated")
print("  by it. Least-outstanding-requests skips a busy backend, so the slow one gets")
print("  traffic only while it is idle: its share falls from 25% to 15% and the p95")
print("  from 865 ms to 751 ms. That is an improvement, not a cure -- and it is the")
print("  honest result. A slow backend still serves real users slowly. Health checks")
print("  remove a DEAD backend (section 4); nothing removes a slow one, which is why")
print("  it does more damage (M13-L11).")


# ============================================================ 4
rule("4. HEALTH CHECKS: DETECTION TIME VS FALSE ALARMS")

FLAKE = 0.02       # probability a single check fails on a healthy target
CONFIGS = [(5, 2), (10, 2), (30, 2), (10, 3), (30, 5)]
print(f"  a healthy target fails a single check {FLAKE:.0%} of the time [ILLUSTRATIVE]\n")
print(f"  {'interval':>10}{'threshold':>11}{'detect (worst)':>16}{'false removals/day':>21}")
for interval, threshold in CONFIGS:
    detect = interval * threshold
    checks_per_day = 86400 / interval
    p_false = FLAKE ** threshold
    false_per_day = checks_per_day * p_false
    print(f"  {interval:>8} s{threshold:>11}{detect:>14} s{false_per_day:>21.2f}")
print("\n  Detection time is interval x threshold, and false removals scale with the")
print("  check RATE times the failure probability raised to the threshold. A 5-second")
print("  interval with a threshold of 2 detects in 10 s and removes a healthy target")
print("  several times a day; 30 s with a threshold of 5 essentially never does, and")
print("  takes 150 s to notice a real failure. Pick from your own flake rate.")


# ============================================================ 5
rule("5. DEREGISTRATION DELAY: WHAT HAPPENS TO IN-FLIGHT REQUESTS?")

RPS_PER_TARGET = 40
N = 20000
# a long-tailed mix: most requests are quick, streaming answers are not (M13-L11)
durations = sorted(min(600.0, abs(rng.lognormvariate(0.6, 1.25))) for _ in range(N))
p50, p95, p99 = durations[N // 2], durations[int(N * 0.95)], durations[int(N * 0.99)]
print(f"  request duration: p50 {p50:.1f} s, p95 {p95:.1f} s, p99 {p99:.1f} s "
      f"[ILLUSTRATIVE long-tailed mix]\n")
print(f"  {'deregistration delay':<24}{'requests cut':>14}{'share of in-flight':>21}")
for delay in (0, 5, 30, 60, 300):
    cut = sum(1 for d in durations if d > delay) / N
    print(f"  {delay:>19} s{RPS_PER_TARGET * cut * p50:>14.1f}{cut:>21.2%}")
print("\n  A delay of 0 cuts every in-flight request. The interesting rows are the")
print("  middle ones: a 30-second delay still cuts the requests that were always")
print("  going to be slow -- which, for an AI system, are the streaming answers a")
print("  user is actively watching. Set the delay from your p99, not from a default,")
print("  and accept that deployments and scale-in get slower (M13-L11, M13-L14).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every propagation figure, days-remaining calculation, latency")
print("  percentile, detection time and loss count above is computed by this script.")
print("\n  ILLUSTRATIVE: TTL client behaviour is modelled as uniform expiry, which")
print("  ignores resolver-side caching that makes real propagation SLOWER. Backend")
print("  latencies, flake rates and traffic figures are invented.")
print("\n  NOT SHOWN: TLS handshake mechanics and cipher selection, ALB vs NLB")
print("  selection in depth, Route 53 routing policies, and WAF (M11-L12, M12-L11).")
print("\nDone.")
