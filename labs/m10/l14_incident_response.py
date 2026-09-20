"""M10-L14 lab -- an incident is a race between a regression and your ability to see it.
This lab measures:

  1. time to detect under three detection strategies,
  2. how many users are harmed, given a detection time and a rollout strategy,
  3. which changes are actually reversible, and which are one-way doors,
  4. a severity rule applied to eight events -- who gets woken, and when,
  5. attribution: how batching deploys multiplies the candidate causes.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l14_incident_response.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1014)

# ============================================================ 1
rule("1. HOW LONG BEFORE ANYONE KNOWS?")

REQ_PER_HOUR = 600
BASE_BAD = 0.02          # normal rate of bad answers
INCIDENT_BAD = 0.14      # rate after the regression starts
TRIALS = 500
REPORT_PROB = 0.004      # a user who gets a bad answer bothers to report it
TRIAGE_H = 8             # reports sit in a support queue before anyone correlates them
HORIZON = 336            # give up after two weeks


def detect_by_user_reports(bad_rate: float) -> int | None:
    """Three reports have to land AND be triaged before anyone looks."""
    reports = 0
    for h in range(HORIZON):
        bad = sum(1 for _ in range(REQ_PER_HOUR) if rng.random() < bad_rate)
        reports += sum(1 for _ in range(bad) if rng.random() < REPORT_PROB)
        if reports >= 3:
            return h + 1 + TRIAGE_H
    return None


def detect_by_hourly_alert(bad_rate: float, threshold: float = 0.05) -> int | None:
    """An automated check on the hourly bad-answer rate of a 200-request sample."""
    for h in range(HORIZON):
        sample = sum(1 for _ in range(200) if rng.random() < bad_rate) / 200
        if sample > threshold:
            return h + 1
    return None


def detect_by_canary(bad_rate: float, threshold: float = 0.05, min_n: int = 100) -> int | None:
    """Canary is 5% of traffic, so the same check waits for enough samples."""
    per_hour = int(REQ_PER_HOUR * 0.05)
    seen = bad = 0
    for h in range(HORIZON):
        for _ in range(per_hour):
            seen += 1
            bad += rng.random() < bad_rate
        if seen >= min_n and bad / seen > threshold:
            return h + 1
    return None


DETECTORS = {
    "waiting for user reports (3, then triage)": detect_by_user_reports,
    "hourly alert on a 200-request sample":      detect_by_hourly_alert,
    "canary at 5% of traffic, min n=100":        detect_by_canary,
}

print(f"  regression raises the bad-answer rate from {BASE_BAD:.0%} to {INCIDENT_BAD:.0%}, "
      f"{REQ_PER_HOUR} requests/hour\n")
print(f"  {'detection strategy':<44}{'mean':>9}{'p90':>8}   false alarms in a quiet fortnight")
means = {}
for name, fn in DETECTORS.items():
    times = [t for t in (fn(INCIDENT_BAD) for _ in range(TRIALS)) if t is not None]
    means[name] = sum(times) / len(times)
    p90 = sorted(times)[int(len(times) * 0.9)]
    # same detector, no incident: how often does it fire anyway?
    false_fires = sum(1 for _ in range(200) if fn(BASE_BAD) is not None)
    print(f"  {name:<44}{means[name]:>7.1f} h{p90:>6} h   {false_fires / 200:>5.0%} of quiet fortnights")
mean_reports, mean_alert, mean_canary = means.values()
print(f"\n  automated checking detects ~{mean_reports / mean_alert:.0f}x sooner than waiting to be told,")
print(f"  and the canary ~{mean_reports / mean_canary:.0f}x sooner while exposing 5% of users (section 2).")
print("  The false-alarm column is the cost: a detector nobody trusts is not a")
print("  detector. Tune the threshold and the sample size together (M13-L12).")


# ============================================================ 2
rule("2. HOW MANY PEOPLE ARE HARMED BEFORE IT STOPS?")

ROLLOUTS = {"big bang (100% at once)": 1.00, "50% rollout": 0.50,
            "canary 5% then full": 0.05, "canary 1% then full": 0.01}
ROLLBACK_H = 1.0
print(f"  bad answers delivered = requests x exposure x (incident rate - base rate)")
print(f"  rollback takes {ROLLBACK_H:.0f} h once the decision is made\n")
print(f"  {'rollout':<26}{'detect':>9}{'exposed':>10}{'bad answers':>14}")
for name, share in ROLLOUTS.items():
    detect_h = mean_alert if share >= 0.5 else mean_canary
    hours = detect_h + ROLLBACK_H
    bad = REQ_PER_HOUR * share * hours * (INCIDENT_BAD - BASE_BAD)
    print(f"  {name:<26}{detect_h:>7.1f} h{share:>9.0%}{bad:>14,.0f}")
print("\n  Two levers, and they multiply: detect sooner, and expose fewer people while")
print("  you do. A slow rollout is not caution for its own sake -- it is a cap on the")
print("  size of the mistake you have not found yet (M13-L14).")


# ============================================================ 3
rule("3. WHICH CHANGES CAN YOU ACTUALLY TAKE BACK?")

CHANGES = [
    ("prompt template edit",            True,  "redeploy previous hash"),
    ("model version bump",              True,  "repoint to the pinned previous version"),
    ("decoding parameter change",       True,  "config revert"),
    ("retrieval k / filter change",     True,  "config revert"),
    ("guardrail policy update",         True,  "policy version revert"),
    ("re-embedding the whole corpus",   False, "needs the old index kept, or a full rebuild (hours)"),
    ("schema migration on the store",   False, "needs a reverse migration written IN ADVANCE"),
    ("emails already sent by the agent", False, "cannot be unsent; only corrected (M8-L11)"),
    ("records deleted by a tool call",  False, "recoverable only from backups, if in scope"),
    ("customer-visible price quote",    False, "commercially binding; a correction is a new event"),
]
print(f"  {'change':<36}{'reversible':>12}   how")
for name, rev, how in CHANGES:
    print(f"  {name:<36}{('yes' if rev else 'NO'):>12}   {how}")
one_way = [c for c, r, _ in CHANGES if not r]
print(f"\n  one-way doors: {len(one_way)}/{len(CHANGES)}")
print("  'We can always roll back' is true of configuration and false of effects. Know")
print("  which of your changes are which BEFORE the incident, and write the reverse")
print("  migration at the same time as the forward one (M8-L11, M8-L12).")


# ============================================================ 4
rule("4. SEVERITY: WHAT IS THIS, AND WHO GETS WOKEN?")

EVENTS = [
    # name,                                    users,  data_exposed, safety, money, workaround
    ("answers slower than usual",              "many",  False, False, False, True),
    ("one tenant sees another tenant's docs",  "few",   True,  False, False, False),
    ("agent emailed 40 wrong invoices",        "few",   False, False, True,  False),
    ("assistant produced unsafe advice",       "few",   False, True,  False, False),
    ("citations broken on all answers",        "many",  False, False, False, True),
    ("cost per request tripled overnight",     "all",   False, False, True,  True),
    ("French answers regressed 9 points",      "few",   False, False, False, True),
    ("model provider outage, feature down",    "all",   False, False, False, False),
]


def severity(users, data_exposed, safety, money, workaround) -> str:
    if data_exposed or safety:
        return "SEV1"
    if money and not workaround:
        return "SEV1"
    if users == "all" and not workaround:
        return "SEV2"
    if money or users in ("all", "many"):
        return "SEV2"
    return "SEV3"


ACTION = {"SEV1": "page now, incident channel, exec comms path",
          "SEV2": "page in hours, incident channel",
          "SEV3": "ticket, next working day"}
print(f"  {'event':<42}{'severity':>10}   action")
for name, users, data, safety, money, wk in EVENTS:
    s = severity(users, data, safety, money, wk)
    print(f"  {name:<42}{s:>10}   {ACTION[s]}")
counts = {}
for name, users, data, safety, money, wk in EVENTS:
    s = severity(users, data, safety, money, wk)
    counts[s] = counts.get(s, 0) + 1
print(f"\n  {counts}")
print("  Note what does NOT depend on user count: one tenant seeing another's")
print("  documents affects 'few' users and is still the highest severity, because")
print("  severity is about the KIND of harm, not the volume (M10-L07).")


# ============================================================ 5
rule("5. ATTRIBUTION: WHICH CHANGE CAUSED IT?")

DEPLOYS_PER_WEEK = 21
for batch in (1, 4, 12):
    innocent, steps = [], []
    for _ in range(4000):
        guilty = rng.randrange(batch)          # which change in the deploy caused it
        innocent.append(batch - 1)             # reverting the deploy reverts the rest too
        # bisecting within the deploy to find the guilty one
        lo, hi, n = 0, batch, 0
        while hi - lo > 1:
            mid = (lo + hi) // 2
            n += 1
            if guilty < mid:
                hi = mid
            else:
                lo = mid
        steps.append(n)
    print(f"  {batch:>2} changes per deploy, {DEPLOYS_PER_WEEK} deploys/week -> "
          f"{batch * DEPLOYS_PER_WEEK:>3} changes/week,  {batch:>2} suspects, "
          f"{sum(innocent) / len(innocent):>4.1f} innocent changes reverted, "
          f"{sum(steps) / len(steps):>4.1f} bisect steps to isolate")
print("\n  Bisecting a batch of twelve means twelve suspects and, usually, a rollback of")
print("  eleven innocent changes. Small, independently revertible changes are an")
print("  incident-response control, not a style preference (M11-L18).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every detection time, exposure count, severity classification and")
print("  candidate-cause count above is computed by simulation or by the stated rule.")
print("\n  ILLUSTRATIVE: traffic volume, incident rate, report probability, rollback")
print("  duration and the severity rule itself are invented -- yours will differ.")
print("\n  NOT SHOWN: on-call rotas, customer communication templates, regulatory")
print("  breach notification, and the blameless review meeting itself (M10-L16).")
print("\nDone.")
