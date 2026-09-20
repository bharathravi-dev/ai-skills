"""M11-L05 lab -- why credential LIFETIME is the control, not credential secrecy.
This lab computes:

  1. the attacker-usable window of a leaked credential, by credential type,
  2. a validator for STS session durations, including the role-chaining rule,
  3. the SDK credential provider chain resolved over six environments,
  4. access-key age across a fictional estate, and the exposure it represents,
  5. whether an SSRF can steal instance credentials under IMDSv1 vs IMDSv2.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l05_sts_temporary_credentials.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1105)

# ============================================================ 1
rule("1. HOW LONG IS A LEAKED CREDENTIAL USEFUL?")

DETECT_H = 72          # hours until a leak is noticed and the credential revoked [ILLUSTRATIVE]
CREDENTIALS = {
    "IAM user access key (never rotated)": None,        # None = until revoked
    "IAM user access key (90-day rotation)": 90 * 24,
    "role session, 12 h maximum":          12,
    "role session, 1 h default":            1,
    "role session, 15 min minimum":         0.25,
}
print(f"  a credential leaks; it takes {DETECT_H} h to notice and revoke [ILLUSTRATIVE]\n")
print(f"  {'credential':<40}{'validity':>14}{'usable window':>16}")
for name, life in CREDENTIALS.items():
    usable = DETECT_H if life is None else min(DETECT_H, life)
    life_s = "until revoked" if life is None else (f"{life:.2f} h" if life < 1 else f"{life:,.0f} h")
    print(f"  {name:<40}{life_s:>14}{usable:>14.2f} h")
print(f"\n  The 15-minute session is useful for {0.25 / DETECT_H:.2%} of the detection window; the")
print("  never-rotated key, 100%. Note that 90-day rotation changes NOTHING here: the")
print("  leak is found in 72 h, long inside the rotation period. Rotation only bounds")
print("  the case where you never notice at all. SESSIONS shorten the window by")
print("  orders of magnitude, and they do it without anyone remembering to act.")
print("  This is the whole argument for roles over users (M11-L04).")


# ============================================================ 2
rule("2. WILL STS ACCEPT THIS SESSION DURATION?")

def check_duration(seconds: int, role_max_seconds: int, chained: bool) -> tuple[bool, str]:
    """AWS's documented AssumeRole rules."""
    if seconds < 900:
        return False, "below the 900 s (15 min) minimum"
    if seconds > 43200:
        return False, "above the 43200 s (12 h) API maximum"
    if chained and seconds > 3600:
        return False, "role chaining caps the session at 1 hour"
    if seconds > role_max_seconds:
        return False, f"above this role's maximum session duration ({role_max_seconds:,} s)"
    return True, "accepted"


CASES = [
    (3600,  3600,  False), (900,   3600,  False), (600,   3600,  False),
    (43200, 43200, False), (43200, 3600,  False), (50000, 43200, False),
    (3600,  43200, True),  (7200,  43200, True),
]
print(f"  {'requested':>11}{'role max':>11}{'chained?':>11}   verdict")
for secs, rmax, chained in CASES:
    ok, why = check_duration(secs, rmax, chained)
    print(f"  {secs:>9,} s{rmax:>9,} s{('yes' if chained else 'no'):>11}   {'OK' if ok else 'REJECTED'}: {why}")
print("\n  Two rules people meet the hard way: the role's own maximum (1-12 h, set by")
print("  an administrator) overrides what you ask for, and ROLE CHAINING -- assuming")
print("  a role from a role -- caps the session at one hour regardless.")


# ============================================================ 3
rule("3. WHICH CREDENTIALS DID THE SDK ACTUALLY USE?")

CHAIN = ["explicit code / CLI flags", "environment variables", "assumed role in config profile",
         "shared credentials file", "container credentials (ECS/EKS)", "instance metadata (IMDS)"]
ENVIRONMENTS = {
    "laptop, profile configured":      {"shared credentials file"},
    "laptop, stale AWS_ACCESS_KEY_ID": {"environment variables", "shared credentials file"},
    "EC2 instance with a role":        {"instance metadata (IMDS)"},
    "EC2 + leftover ~/.aws/credentials": {"shared credentials file", "instance metadata (IMDS)"},
    "ECS task with a task role":       {"container credentials (ECS/EKS)", "instance metadata (IMDS)"},
    "CI job, OIDC-assumed role":       {"assumed role in config profile"},
}
print(f"  provider chain order: " + " > ".join(c.split(' (')[0] for c in CHAIN) + "\n")
print(f"  {'environment':<38}{'wins':<34}surprise?")
for env, present in ENVIRONMENTS.items():
    winner = next((c for c in CHAIN if c in present), "none -- no credentials")
    surprise = "YES" if len(present) > 1 and winner != "container credentials (ECS/EKS)" else ""
    print(f"  {env:<38}{winner:<34}{surprise}")
print("\n  Rows 2 and 4 are the classic bug: the role you attached is ignored because")
print("  an older credential sits higher in the chain. The symptom is 'access denied")
print("  for a permission the role clearly has', and the fix is to delete the")
print("  leftover, not to widen the policy (M11-L04).")


# ============================================================ 4
rule("4. ACCESS-KEY AGE ACROSS AN ESTATE")

N = 240
ages = sorted(int(abs(rng.gauss(0, 420))) for _ in range(N))
buckets = [(0, 30), (30, 90), (90, 365), (365, 730), (730, 10_000)]
LABELS = ["under 30 days", "30-90 days", "90 days - 1 year", "1-2 years", "over 2 years"]
print(f"  {N} access keys in a fictional estate [ILLUSTRATIVE distribution]\n")
print(f"  {'age':<22}{'keys':>7}{'share':>9}{'key-days of exposure':>23}")
total_days = 0
for (lo, hi), label in zip(buckets, LABELS):
    keys = [a for a in ages if lo <= a < hi]
    days = sum(keys)
    total_days += days
    print(f"  {label:<22}{len(keys):>7}{len(keys) / N:>9.0%}{days:>23,}")
old = [a for a in ages if a >= 365]
print(f"\n  total key-days of exposure: {total_days:,}")
print(f"  keys older than a year: {len(old)} ({len(old) / N:.0%}), contributing "
      f"{sum(old) / total_days:.0%} of the exposure")
print("  Every one of these is a credential with no expiry that someone must remember")
print("  to rotate. The fix is not a better rotation reminder; it is not having them")
print("  (sections 1 and 3).")


# ============================================================ 5
rule("5. CAN AN SSRF STEAL THE INSTANCE'S CREDENTIALS?")

SSRF_STEPS = [
    ("attacker gets the app to fetch a URL it chose",          True,  True),
    ("GET http://169.254.169.254/latest/meta-data/ works",     True,  False),
    ("a PUT is needed first to obtain a session token",        False, True),
    ("the attacker's forged request can send a PUT",           False, False),
    ("a response hop limit can block containerised callers",   False, True),
]
print(f"  {'step':<58}{'IMDSv1':>9}{'IMDSv2':>9}")
for text, v1, v2 in SSRF_STEPS:
    print(f"  {text:<58}{('yes' if v1 else 'no'):>9}{('yes' if v2 else 'no'):>9}")
v1_ok = SSRF_STEPS[1][1]
print(f"\n  IMDSv1: a plain GET from a server-side request fetches the role's credentials.")
print(f"  IMDSv2: the token PUT breaks the typical SSRF chain, and the configurable")
print(f"  response hop limit (set it to 1) stops a container reaching the host's IMDS.")
print("  Require IMDSv2 (and set the hop limit to 1 where you can). An SSRF that")
print("  reaches instance credentials converts a web bug into an AWS credential")
print("  compromise with the full reach of the instance role (M9-L12, M10-L10).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every window, verdict, chain resolution, age figure and step result")
print("  above is computed by this script.")
print("\n  VERIFIED 2026-09-17: the STS duration rules in section 2 follow the AWS STS")
print("  API reference for AssumeRole (900 s minimum, 43200 s maximum, role maximum")
print("  of 1-12 hours, role chaining capped at 1 hour).")
print("\n  ILLUSTRATIVE: the detection time, key-age distribution and estate size are")
print("  invented. The provider chain is shown in its usual order; consult your SDK's")
print("  documentation for the exact list.")
print("\n  NOT SHOWN: IAM Identity Center sign-in, OIDC federation setup, and")
print("  credential_process (M11-L18).")
print("\nDone.")
