"""M11-L16 lab -- what to record, what it costs, and what each signal can answer.
This lab computes:

  1. which incident questions metrics, logs and traces can each answer,
  2. what log volume costs, and what sampling actually saves,
  3. why the STATISTIC you alarm on decides whether you see the problem,
  4. management events vs data events in CloudTrail, and their cost,
  5. alarm noise: single-threshold vs multi-datapoint vs composite.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l16_cloudwatch_cloudtrail.py
"""

from __future__ import annotations

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1116)

# ============================================================ 1
rule("1. WHICH SIGNAL ANSWERS WHICH QUESTION?")

QUESTIONS = [
    ("is the system broken right now?",                 True,  False, False),
    ("how broken, and since when?",                     True,  False, False),
    ("which user was affected?",                        False, True,  True),
    ("what exactly did we send the model?",             False, True,  False),
    ("which of the eight services was slow?",           False, False, True),
    ("did the retrieval step or the model take 4 s?",   False, False, True),
    ("who changed the bucket policy, and when?",        False, True,  False),
    ("is the French slice regressing?",                 True,  False, False),
    ("why did THIS request fail?",                      False, True,  True),
]
print(f"  {'question':<48}{'metrics':>9}{'logs':>7}{'traces':>9}")
for q, m, l, t in QUESTIONS:
    print(f"  {q:<48}{('yes' if m else '-'):>9}{('yes' if l else '-'):>7}{('yes' if t else '-'):>9}")
for name, idx in (("metrics", 1), ("logs", 2), ("traces", 3)):
    n = sum(1 for q in QUESTIONS if q[idx])
    print(f"\n  {name:<8} answers {n}/{len(QUESTIONS)}", end="")
print("\n\n  Metrics tell you THAT something is wrong, cheaply and fast, and they are")
print("  what an alarm can fire on. Logs and traces tell you WHY, expensively and")
print("  after the fact. You need all three, and you should pay very different")
print("  amounts for each (M10-L13).")


# ============================================================ 2
rule("2. WHAT DOES LOGGING COST, AND WHAT DOES SAMPLING SAVE?")

RPS = 300
LOG_KB_PER_REQUEST = 14
INGEST_PER_GB = 0.50        # [ILLUSTRATIVE]
STORE_PER_GB_MONTH = 0.03
gb_month = RPS * 86400 * 30 * LOG_KB_PER_REQUEST / 1024 / 1024
print(f"  {RPS} requests/s, {LOG_KB_PER_REQUEST} KB of logs each -> {gb_month:,.0f} GB/month\n")
print(f"  {'policy':<44}{'GB/mo':>9}{'ingest $':>11}{'store $':>10}{'total $':>10}")
POLICIES = [
    ("everything, 90-day retention",       1.00, 3),
    ("everything, 14-day retention",       1.00, 0.47),
    ("errors + 5% of successes, 14 days",  0.10, 0.47),
    ("errors + 1% of successes, 14 days",  0.06, 0.47),
    ("structured metrics + errors only",   0.02, 0.47),
]
totals = []
for label, frac, months in POLICIES:
    gb = gb_month * frac
    ingest = gb * INGEST_PER_GB
    store = gb * STORE_PER_GB_MONTH * months
    total = ingest + store
    totals.append(total)
    print(f"  {label:<44}{gb:>9,.0f}{ingest:>11,.0f}{store:>10,.0f}{total:>10,.0f}")
print(f"\n  the strictest policy costs {totals[-1] / totals[0]:.1%} of the loosest "
      f"(${totals[0] - totals[-1]:,.0f}/month saved).")
print("  Sampling successes and keeping ALL errors is the highest-value change most")
print("  teams can make: you keep every failure you will investigate and drop the")
print("  99% of successful requests nobody ever reads. Emit the numbers you need as")
print("  METRICS (cheap, aggregated, alarmable) rather than parsing them out of logs")
print("  later (embedded metric format).")


# ============================================================ 3
rule("3. THE STATISTIC DECIDES WHETHER YOU SEE IT")

N = 6000
# 97% of requests are fast; 3% hit a broken dependency and take ~9 s
lat = sorted([rng.gauss(420, 90) for _ in range(int(N * 0.97))]
             + [rng.gauss(9000, 1200) for _ in range(int(N * 0.03))])
def pct(p): return lat[int(len(lat) * p)]
mean = sum(lat) / len(lat)
print(f"  3% of requests hit a broken dependency and take about 9 s\n")
print(f"  {'statistic':<22}{'value':>12}   alarm at 1500 ms?")
for label, value in (("Average", mean), ("p50", pct(0.50)), ("p90", pct(0.90)),
                     ("p95", pct(0.95)), ("p99", pct(0.99)), ("Maximum", lat[-1])):
    print(f"  {label:<22}{value:>9.0f} ms   {'FIRES' if value > 1500 else 'silent'}")
print("\n  Read that again: 3% of users are waiting NINE SECONDS, and the Average,")
print("  p50, p90 and p95 are all SILENT. Only the p99 fires. Averaging is how a")
print("  real, user-visible, dependency-shaped failure hides inside a green")
print("  dashboard. Alarm on a high percentile, and keep the average away from any")
print("  dashboard people make decisions from (M13-L11, M10-L08).")


# ============================================================ 4
rule("4. CLOUDTRAIL: MANAGEMENT EVENTS AND DATA EVENTS")

EVENTS = [
    ("someone changed a bucket policy",       "management", True),
    ("someone assumed a role",                "management", True),
    ("an instance was launched",              "management", True),
    ("CloudTrail logging was stopped",        "management", True),
    ("an object was READ from a bucket",      "data",       False),
    ("an object was WRITTEN to a bucket",     "data",       False),
    ("a Lambda function was INVOKED",         "data",       False),
    ("a DynamoDB item was read",              "data",       False),
]
print(f"  {'event':<44}{'type':<14}{'recorded by default?':>22}")
for name, kind, default in EVENTS:
    print(f"  {name:<44}{kind:<14}{('yes' if default else 'NO -- opt in'):>22}")
mgmt = sum(1 for _, k, _ in EVENTS if k == "management")
print(f"\n  management events: {mgmt}/{len(EVENTS)} (recorded by default)")
print(f"  data events:       {len(EVENTS) - mgmt}/{len(EVENTS)} (opt-in, charged per event)")
OBJECT_READS_PER_MONTH = 120_000_000
DATA_EVENT_PER_100K = 0.10        # [ILLUSTRATIVE]
print(f"\n  at {OBJECT_READS_PER_MONTH:,} object reads/month, S3 data events would cost "
      f"${OBJECT_READS_PER_MONTH / 100_000 * DATA_EVENT_PER_100K:,.0f}/month")
print("  Management events answer 'who changed the configuration' -- the question in")
print("  most security investigations -- and are on by default. Data events answer")
print("  'who read this object', which is what you need for a data-access")
print("  investigation, and are off and expensive. Enable them SELECTIVELY: on the")
print("  buckets holding sensitive data, not on the one holding container images")
print("  (M10-L13, M11-L10).")


# ============================================================ 5
rule("5. ALARM NOISE: FOUR CONFIGURATIONS")

HOURS = 24 * 30
FLAP_PROB = 0.004          # probability a single 1-minute period breaches for no real reason
REAL_INCIDENTS = 3
CONFIGS = [
    ("1 datapoint out of 1",           1, 1),
    ("2 out of 2",                     2, 2),
    ("3 out of 3",                     3, 3),
    ("3 out of 5 (tolerates a blip)",  3, 5),
]


def at_least_m_of_n(m: int, n: int, p: float) -> float:
    """Binomial: probability of at least m breaches in n periods."""
    return sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(m, n + 1))


print(f"  a healthy system breaches the threshold in {FLAP_PROB:.1%} of 1-minute periods\n")
print(f"  {'configuration':<34}{'false alarms/year':>19}{'detect delay':>15}   "
      f"{'survives a good blip?':<32}")
periods_per_year = 365 * 24 * 60
for label, m, n in CONFIGS:
    p_false = at_least_m_of_n(m, n, FLAP_PROB)
    per_year = periods_per_year / n * p_false
    tolerant = "yes" if n > m else "no -- one good minute resets it"
    print(f"  {label:<34}{per_year:>19,.2f}{n:>13} min   {tolerant:<32}")
one_of_one = periods_per_year / 1 * at_least_m_of_n(1, 1, FLAP_PROB) / 12
print(f"\n  '1 out of 1' produces about {one_of_one:,.0f} false alarms a month against "
      f"{REAL_INCIDENTS} real incidents:")
print(f"  {one_of_one / REAL_INCIDENTS:,.0f} false alarms for every real one. That alarm is muted within a")
print("  fortnight, and then the real incident goes undetected (M10-L14).")
print("  Note the last column. '3 out of 3' is quiet but a single healthy minute in")
print("  the middle of a real incident resets the count; '3 out of 5' is almost as")
print("  quiet and keeps firing through a flapping failure. Combine signals with a")
print("  COMPOSITE alarm -- 'latency high AND error rate up' -- so one noisy metric")
print("  cannot page anyone on its own.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every coverage count, cost figure, statistic, event classification")
print("  and false-alarm rate above is computed from the values in this script.")
print("\n  DOCUMENTED BEHAVIOUR: CloudTrail records management events by default and")
print("  requires data events to be enabled explicitly and charged; CloudWatch alarms")
print("  evaluate N datapoints out of M periods.")
print("\n  ILLUSTRATIVE: all prices, traffic volumes, latency distributions and flap")
print("  probabilities are invented. Measure your own flap rate before choosing an")
print("  alarm configuration.")
print("\n  NOT SHOWN: Logs Insights queries, X-Ray/OpenTelemetry setup, metric filters,")
print("  anomaly detection, and cross-account log aggregation (M12-L13, M13-L12).")
print("\nDone.")
