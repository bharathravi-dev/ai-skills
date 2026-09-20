"""M11-L13 lab -- serverless, and the four limits that decide whether it fits.
This lab computes:

  1. cold starts: what share of requests pay one, at different invocation rates,
  2. what provisioned concurrency buys, and what it costs,
  3. concurrency limits: throttling arithmetic under a spike,
  4. timeouts: an AI request's duration against each layer's ceiling,
  5. Lambda vs Fargate cost across four workload shapes.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l13_lambda_api_gateway.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1113)

# ============================================================ 1
rule("1. WHAT SHARE OF REQUESTS PAYS A COLD START?")

IDLE_TIMEOUT_S = 600      # roughly how long an idle execution environment survives
COLD_MS, WARM_MS = 2400, 40      # a Python function importing an SDK and a model client
DURATION_S = 2.5
RATES = [0.0005, 0.01, 0.1, 1.0, 10.0, 100.0]     # requests per second
print(f"  cold start {COLD_MS} ms (SDK + model client import), warm start {WARM_MS} ms, "
      f"request {DURATION_S} s\n")
print(f"  {'requests/second':>16}{'concurrency':>13}{'cold starts/hour':>19}{'% of requests cold':>20}")
for rps in RATES:
    concurrency = max(1, round(rps * DURATION_S))
    requests_per_hour = rps * 3600
    # an environment goes cold after IDLE_TIMEOUT_S without a request
    gap = 1 / rps if rps > 0 else 1e9
    if gap > IDLE_TIMEOUT_S:
        colds_per_hour = requests_per_hour          # every request is cold
    else:
        colds_per_hour = concurrency * 1.0          # roughly one per environment per hour (recycling)
    share = min(1.0, colds_per_hour / requests_per_hour)
    print(f"  {rps:>16.4f}{concurrency:>13}{colds_per_hour:>19.1f}{share:>20.2%}")
print("\n  The shape is what matters. A function called once every 30 minutes pays the")
print("  full 2.4 s on EVERY request, because nothing stays warm between calls. From")
print("  about one call per minute the cost amortises away entirely. The dangerous")
print("  case is a function busy in the day and idle at night: your p99 is fine at")
print("  2pm and terrible at 6am, which is exactly when nobody is looking.")


# ============================================================ 2
rule("2. WHAT DOES PROVISIONED CONCURRENCY BUY?")

GB = 1.5
PC_RATE_PER_GB_HOUR = 0.0000041667 * 3600     # [ILLUSTRATIVE]
for provisioned in (0, 5, 20, 50):
    monthly = provisioned * GB * PC_RATE_PER_GB_HOUR * 730
    cold = "every request when idle" if provisioned == 0 else f"only above {provisioned} concurrent"
    print(f"  provisioned concurrency {provisioned:>3} -> ${monthly:>8,.0f}/month   cold starts: {cold}")
print("\n  [ILLUSTRATIVE rate.] Provisioned concurrency keeps environments warm and")
print("  charges for them whether or not they are used -- which is a server, billed")
print("  by another name. If you need a lot of it, you have discovered that your")
print("  workload is a service, and a container (M11-L12) is usually cheaper and")
print("  simpler. Provisioned concurrency is for a known, bounded warm floor.")


# ============================================================ 3
rule("3. CONCURRENCY LIMITS AND THROTTLING")

ACCOUNT_LIMIT = 1000
FUNCTIONS = {
    "assistant API (reserved 200)":   (200, 2.5),
    "ingestion worker (reserved 300)": (300, 8.0),
    "webhook handler (unreserved)":   (None, 0.3),
}
print(f"  account concurrency limit: {ACCOUNT_LIMIT} [default, soft]\n")
reserved_total = sum(r for r, _ in FUNCTIONS.values() if r)
unreserved = ACCOUNT_LIMIT - reserved_total
print(f"  {'function':<34}{'reserved':>10}{'duration':>10}{'max rps':>10}   note")
for name, (reserved, dur) in FUNCTIONS.items():
    pool = reserved if reserved else unreserved
    max_rps = pool / dur
    note = "isolated from the others" if reserved else f"shares the remaining {unreserved}"
    print(f"  {name:<34}{str(reserved or '-'):>10}{dur:>9.1f}s{max_rps:>10.0f}   {note}")
print(f"\n  reserved in total: {reserved_total}; left for everything unreserved: {unreserved}")
SPIKE_RPS = 140
dur = FUNCTIONS["assistant API (reserved 200)"][1]
needed = SPIKE_RPS * dur
print(f"  a spike of {SPIKE_RPS} rps on the assistant API needs {needed:.0f} concurrent executions,")
print(f"  against a reservation of 200 -> {'THROTTLED' if needed > 200 else 'fits'}"
      f", {max(0, needed - 200):.0f} executions' worth rejected (429)")
print("\n  Reserved concurrency does two jobs: it GUARANTEES a function its share, and")
print("  it CAPS that function so a runaway cannot starve everything else (M11-L06).")
print("  Both matter. An unreserved function competing for the remainder is the one")
print("  that gets throttled first during someone else's incident.")


# ============================================================ 4
rule("4. TIMEOUTS: AN AI REQUEST AGAINST EACH CEILING")

REQUEST = [("retrieval", 0.4), ("rerank", 0.3), ("model generation (streamed)", 46.0),
           ("post-processing and logging", 0.2)]
total = sum(s for _, s in REQUEST)
CEILINGS = [
    ("API Gateway integration timeout (default)", 29, "raiseable on REST APIs by quota request"),
    ("Load balancer idle timeout (typical default)", 60, "configurable, up to minutes"),
    ("Lambda function timeout (maximum)", 900, "15 minutes, hard"),
    ("Lambda function timeout (typical default)", 3, "set it deliberately"),
]
print(f"  {'phase':<34}{'seconds':>9}")
for name, s in REQUEST:
    print(f"  {name:<34}{s:>9.1f}")
print(f"  {'TOTAL':<34}{total:>9.1f}\n")
print(f"  {'ceiling':<46}{'seconds':>9}{'fits?':>8}   note")
for name, secs, note in CEILINGS:
    print(f"  {name:<46}{secs:>9}{('yes' if total <= secs else 'NO'):>8}   {note}")
print(f"\n  a {total:.0f}-second streamed answer exceeds two of the four ceilings at their")
print("  defaults. This is the single most common serverless surprise in AI work:")
print("  the model is fine, the function is fine, and the API layer cuts the")
print("  connection at its default. Check every ceiling on the path, and prefer")
print("  streaming-capable paths (function URLs, ALB) for long answers (M5-L09).")
print("  [Quotas change -- verify the current numbers for your API type.]")


# ============================================================ 5
rule("5. LAMBDA OR A CONTAINER?")

LAMBDA_GB_SECOND = 0.0000166667
LAMBDA_PER_REQUEST = 0.0000002
FARGATE_VCPU_HOUR, FARGATE_GB_HOUR = 0.04048, 0.004445     # [ILLUSTRATIVE]
SHAPES = [
    ("webhook: 5k/day, 200 ms, 0.5 GB",      5_000, 0.2, 0.5),
    ("assistant API: 200k/day, 2.5 s, 1.5 GB", 200_000, 2.5, 1.5),
    ("batch embed: 2M/day, 0.8 s, 2 GB",   2_000_000, 0.8, 2.0),
    ("rare admin job: 30/day, 60 s, 1 GB",        30, 60.0, 1.0),
]
print(f"  {'workload':<42}{'Lambda $/mo':>13}{'Fargate $/mo':>14}   cheaper")
for label, per_day, dur, gb in SHAPES:
    monthly_req = per_day * 30
    lam = monthly_req * (dur * gb * LAMBDA_GB_SECOND + LAMBDA_PER_REQUEST)
    # Fargate: size the fleet for the offered load at 60% utilisation
    concurrency = max(1, (per_day / 86400) * dur / 0.6)
    tasks = max(1, round(concurrency))
    far = tasks * (FARGATE_VCPU_HOUR * (gb / 2) + FARGATE_GB_HOUR * gb) * 730
    print(f"  {label:<42}{lam:>13,.0f}{far:>14,.0f}   {'Lambda' if lam < far else 'Fargate'}")
print("\n  [ILLUSTRATIVE rates; the crossover point is what matters, not the numbers.]")
print("  Lambda wins on spiky, low-duty-cycle and rare work, where a container would")
print("  idle. A container wins once the function is effectively always running --")
print("  and that is also the point where cold starts, concurrency limits and the")
print("  15-minute ceiling stop being theoretical. Choose by duty cycle first, then")
print("  by the timeout table in section 4.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every share, cost, throttling figure and comparison above is computed")
print("  from the values in this script.")
print("\n  ILLUSTRATIVE: cold-start durations, idle-environment behaviour, all prices,")
print("  and the request profile are invented. The cold-start model is a")
print("  simplification: real recycling depends on traffic shape and platform")
print("  behaviour you do not control.")
print("\n  VERIFY BEFORE RELYING ON: Lambda's 15-minute maximum is stable, but account")
print("  concurrency defaults and API Gateway integration timeouts change -- check")
print("  the current quotas for your account and API type.")
print("\n  NOT SHOWN: Lambda response streaming setup, SnapStart, VPC-attached Lambda")
print("  networking, and API Gateway authorisers (M12-L11).")
print("\nDone.")
