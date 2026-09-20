"""M11-L17 lab -- keys, secrets, and backups that have actually been restored.
This lab computes:

  1. the TWO gates on a KMS key: the key policy and the caller's IAM policy,
  2. envelope encryption and data-key caching: KMS request cost at scale,
  3. where a secret lives, and who can read it there,
  4. RPO and RTO arithmetic: what backup frequency and restore time really mean,
  5. four disaster-recovery strategies priced against their RTO and RPO.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l17_kms_secrets_backups_dr.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. A KMS KEY HAS TWO GATES")


def can_decrypt(key_policy_allows: bool, iam_allows: bool, key_enabled: bool,
                grant: bool = False) -> tuple[bool, str]:
    if not key_enabled:
        return False, "the key is disabled -- nothing can decrypt, including you"
    if key_policy_allows and iam_allows:
        return True, "allowed by the key policy AND the caller's IAM policy"
    if grant and key_policy_allows:
        return True, "allowed by a grant"
    if not key_policy_allows:
        return False, "the KEY POLICY does not permit this principal"
    return False, "the caller's IAM policy does not permit kms:Decrypt"


CASES = [
    ("app role: key policy yes, IAM yes",       True,  True,  True),
    ("app role: key policy yes, IAM no",        True,  False, True),
    ("app role: key policy NO, IAM yes (admin)", False, True,  True),
    ("account administrator, no key policy entry", False, True, True),
    ("app role, but the key is disabled",       True,  True,  False),
]
print(f"  {'scenario':<44}{'decrypt?':>10}   why")
for label, kp, iam, enabled in CASES:
    ok, why = can_decrypt(kp, iam, enabled)
    print(f"  {label:<44}{('ALLOWED' if ok else 'denied'):>10}   {why}")
print("\n  Row 4 is the one that surprises people: an account administrator with")
print("  'Action: *' CANNOT decrypt unless the KEY POLICY says so. A KMS key is the")
print("  one resource where IAM alone is not enough, which is exactly what makes it")
print("  a governance control: 'who can read this data' becomes a short, reviewable")
print("  document rather than an emergent property of a hundred IAM policies.")
print("  Row 5 is the other half: disabling the key makes the data unreadable by")
print("  EVERYONE, immediately -- the revocation lever from M10-L06.")


# ============================================================ 2
rule("2. ENVELOPE ENCRYPTION AND DATA-KEY CACHING")

OBJECTS_PER_MONTH = 60_000_000
KMS_PER_10K = 0.03      # [ILLUSTRATIVE]
STRATEGIES = [
    ("one KMS call per object",              1.0),
    ("S3 Bucket Keys (shared data key)",     0.01),
    ("application data-key cache, 5 min",    0.0006),
    ("application data-key cache, 1 hour",   0.00005),
]
print(f"  {OBJECTS_PER_MONTH:,} encrypt/decrypt operations per month\n")
print(f"  {'strategy':<40}{'KMS calls':>15}{'$/month':>11}")
for label, frac in STRATEGIES:
    calls = OBJECTS_PER_MONTH * frac
    print(f"  {label:<40}{calls:>15,.0f}{calls / 10_000 * KMS_PER_10K:>11,.0f}")
print("\n  [ILLUSTRATIVE rate.] Envelope encryption is why this works: KMS encrypts a")
print("  DATA KEY, and the data key encrypts the data. Reuse the data key across many")
print("  objects and the KMS calls collapse. The trade-off is blast radius: a cached")
print("  data key in memory protects more objects, so cache for minutes, not days,")
print("  and never persist a plaintext data key.")


# ============================================================ 3
rule("3. WHERE DOES THE SECRET LIVE, AND WHO CAN READ IT?")

PLACES = [
    ("hard-coded in source",           "everyone with repo access, forever, including git history", False, "none"),
    ("in the container image",         "anyone who can pull the image (M11-L12)",                   False, "none"),
    ("plain environment variable",     "anyone who can describe the task or read a crash dump",     False, "none"),
    ("SSM Parameter Store (String)",   "anyone with ssm:GetParameter",                              False, "IAM"),
    ("SSM Parameter Store (SecureString)", "IAM + the KMS key policy",                              True,  "IAM + KMS"),
    ("Secrets Manager",                "IAM + the KMS key policy, with rotation",                   True,  "IAM + KMS"),
]
print(f"  {'where':<38}{'encrypted':>11}{'gated by':>12}   who can read it")
for place, who, enc, gate in PLACES:
    print(f"  {place:<38}{('yes' if enc else 'NO'):>11}{gate:>12}   {who}")
bad = sum(1 for _, _, e, _ in PLACES if not e)
print(f"\n  places offering no encryption at rest: {bad}/{len(PLACES)}")
print("  The first three also share a property that matters more than encryption:")
print("  there is no way to ROTATE them and no record of who read them. A secret you")
print("  cannot rotate is a secret you can never respond to a leak about -- so the")
print("  question at design time is not 'is it encrypted' but 'what do we do at 2am")
print("  when it leaks' (M10-L14, M11-L05).")


# ============================================================ 4
rule("4. RPO AND RTO: WHAT THE BACKUP SCHEDULE ACTUALLY PROMISES")

SCHEDULES = [
    ("nightly snapshot",                 24 * 60, 90,  "restore + re-point the app"),
    ("snapshot every 6 hours",           6 * 60,  90,  "restore + re-point the app"),
    ("point-in-time recovery (5 min)",   5,       45,  "restore to a new instance"),
    ("continuous replication to standby", 0.1,    2,   "failover (M11-L14)"),
]
WRITES_PER_MINUTE = 1400
print(f"  the system takes {WRITES_PER_MINUTE:,} writes per minute\n")
print(f"  {'strategy':<38}{'RPO':>10}{'writes lost':>14}{'RTO':>9}   recovery action")
for label, rpo_min, rto_min, action in SCHEDULES:
    lost = rpo_min * WRITES_PER_MINUTE
    rpo = f"{rpo_min:.0f} min" if rpo_min >= 1 else f"{rpo_min * 60:.0f} s"
    print(f"  {label:<38}{rpo:>10}{lost:>14,.0f}{rto_min:>7.0f} m   {action}")
print("\n  RPO is how much data you lose; RTO is how long you are down. They are")
print("  bought separately and they are both PROMISES YOU HAVE TESTED, or they are")
print("  guesses. A nightly snapshot means an average half-day of lost work -- which")
print("  is a business decision, not a default, and somebody should have been asked.")


# ============================================================ 5
rule("5. FOUR DISASTER-RECOVERY STRATEGIES")

STRATEGIES_DR = [
    ("backup and restore",      "hours to a day", "hours",      0.02, "rebuild from backups in another region"),
    ("pilot light",             "minutes",        "tens of min", 0.15, "data replicated; compute off until needed"),
    ("warm standby",            "minutes",        "minutes",     0.45, "a small live copy, scaled up on failover"),
    ("multi-site active/active", "near zero",     "near zero",   1.00, "both regions serve traffic"),
]
print(f"  {'strategy':<28}{'RPO':<18}{'RTO':<14}{'rel. cost':>10}   what exists in region 2")
for name, rpo, rto, cost, note in STRATEGIES_DR:
    print(f"  {name:<28}{rpo:<18}{rto:<14}{cost:>10.2f}   {note}")
print("\n  [Relative cost is the second region's share of the first's; ILLUSTRATIVE.]")
print("  Choose from the RPO and RTO the business actually needs -- and remember")
print("  M11-L02: if your own software contributes more unavailability than the")
print("  infrastructure does, a multi-region project buys almost nothing. The")
print("  honest first step for most teams is 'backup and restore, tested quarterly',")
print("  because an untested backup has an unknown RTO and quite possibly an")
print("  infinite one (M10-L14).")
print("\n  Four things a restore test finds that a backup policy never does:")
for item in ("the backup did not include the thing you need (a config, a key)",
             "the restore needs a permission nobody has",
             "the restore takes 6 hours, not the 45 minutes on the slide",
             "the restored data is missing the last N hours nobody accounted for"):
    print(f"    - {item}")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every access verdict, KMS call count, cost, RPO/RTO figure and")
print("  comparison above is computed from the values and rules in this script.")
print("\n  DOCUMENTED BEHAVIOUR: a KMS key requires BOTH the key policy and the")
print("  caller's IAM policy to permit the operation (unless a grant applies);")
print("  disabling a key makes ciphertext undecryptable by everyone; envelope")
print("  encryption lets one data key protect many objects.")
print("\n  ILLUSTRATIVE: all prices, volumes, timings and relative costs are invented.")
print("\n  NOT SHOWN: key rotation mechanics, multi-Region keys, CloudHSM, AWS Backup")
print("  configuration, and cross-account backup vaults (M12-L11).")
print("\nDone.")
