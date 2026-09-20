"""M11-L10 lab -- S3: who can read it, who can decrypt it, and what it costs over time.
This lab computes:

  1. a Block Public Access evaluator over eight bucket configurations,
  2. four encryption options compared on who can decrypt, what is logged and cost,
  3. lifecycle arithmetic: 36 months of a document corpus across storage classes,
  4. versioning: what a DELETE actually does, and what the versions cost,
  5. durability is not backup -- the four ways data is lost that 11 nines do not cover.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l10_s3_permissions_encryption_lifecycle.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. IS THIS BUCKET PUBLIC?")


def is_public(public_acl: bool, public_policy: bool, bpa: dict) -> tuple[bool, str]:
    """AWS's four Block Public Access settings, applied to one bucket."""
    reasons = []
    acl_grants = public_acl and not bpa["IgnorePublicAcls"]
    policy_grants = public_policy and not bpa["RestrictPublicBuckets"]
    if acl_grants:
        reasons.append("a public ACL is in effect")
    if policy_grants:
        reasons.append("a public bucket policy is in effect")
    if public_acl and bpa["IgnorePublicAcls"]:
        reasons.append("public ACL present but IGNORED")
    if public_policy and bpa["RestrictPublicBuckets"]:
        reasons.append("public policy present but RESTRICTED to the account")
    return (acl_grants or policy_grants), "; ".join(reasons) or "nothing grants public access"


ALL_ON = {"BlockPublicAcls": True, "IgnorePublicAcls": True,
          "BlockPublicPolicy": True, "RestrictPublicBuckets": True}
ALL_OFF = {k: False for k in ALL_ON}
PARTIAL = {"BlockPublicAcls": True, "IgnorePublicAcls": True,
           "BlockPublicPolicy": False, "RestrictPublicBuckets": False}

CONFIGS = [
    ("new bucket, defaults",              False, False, ALL_ON),
    ("public policy, BPA all on",         False, True,  ALL_ON),
    ("public policy, BPA all off",        False, True,  ALL_OFF),
    ("public ACL, BPA all off",           True,  False, ALL_OFF),
    ("public ACL, BPA all on",            True,  False, ALL_ON),
    ("public policy, only ACL settings on", False, True, PARTIAL),
    ("both public, BPA all off",          True,  True,  ALL_OFF),
    ("both public, BPA all on",           True,  True,  ALL_ON),
]
print(f"  {'configuration':<40}{'public?':>10}   why")
public_count = 0
for label, acl, policy, bpa in CONFIGS:
    pub, why = is_public(acl, policy, bpa)
    public_count += pub
    print(f"  {label:<40}{('PUBLIC' if pub else 'private'):>10}   {why}")
print(f"\n  public: {public_count}/{len(CONFIGS)}")
print("  Row 6 is the trap: three of the four settings look 'mostly on' and the")
print("  bucket is still public, because RestrictPublicBuckets is the one that")
print("  governs policies. Set all four, at the ACCOUNT level (and now at the")
print("  organisation level), so a new bucket cannot opt out.")
print("  BlockPublicAcls and BlockPublicPolicy prevent public settings being MADE;")
print("  IgnorePublicAcls and RestrictPublicBuckets neutralise ones already there.")


# ============================================================ 2
rule("2. ENCRYPTION: WHO CAN ACTUALLY DECRYPT IT?")

OPTIONS = {
    "SSE-S3 (AES256, AWS-managed)": {
        "decrypt": "anyone with s3:GetObject", "key_audit": "no separate key log",
        "revoke": "no -- remove S3 permission", "cost": "none", "kms_calls": 0},
    "SSE-KMS (AWS-managed key)": {
        "decrypt": "s3:GetObject + kms:Decrypt", "key_audit": "CloudTrail on the key",
        "revoke": "no -- AWS manages the policy", "cost": "per request", "kms_calls": 1},
    "SSE-KMS (customer-managed key)": {
        "decrypt": "s3:GetObject + the KEY POLICY", "key_audit": "CloudTrail on the key",
        "revoke": "YES -- edit or disable the key", "cost": "per request + key/month", "kms_calls": 1},
    "client-side encryption": {
        "decrypt": "whoever holds your key", "key_audit": "yours to build",
        "revoke": "yours to build", "cost": "engineering", "kms_calls": 0},
}
print(f"  {'option':<34}{'who can decrypt':<34}{'revoke access?':<24}")
for name, o in OPTIONS.items():
    print(f"  {name:<34}{o['decrypt']:<34}{o['revoke']:<24}")
REQUESTS_PER_MONTH = 40_000_000
KMS_PER_10K = 0.03
print(f"\n  at {REQUESTS_PER_MONTH:,} object reads/month [ILLUSTRATIVE rate ${KMS_PER_10K}/10k KMS requests]:")
for name, o in OPTIONS.items():
    monthly = REQUESTS_PER_MONTH * o["kms_calls"] / 10_000 * KMS_PER_10K
    print(f"    {name:<34}${monthly:>9,.0f}/month in KMS request charges")
print("\n  The row that matters for governance is 'revoke access?'. Only a")
print("  CUSTOMER-MANAGED key lets you make data unreadable by changing one policy,")
print("  without touching a single object -- and only it gives you a key-level audit")
print("  trail separate from the data-level one (M11-L17, M10-L13).")
print("  Use S3 Bucket Keys to cut the KMS request charge above substantially.")


# ============================================================ 3
rule("3. LIFECYCLE: 36 MONTHS OF A DOCUMENT CORPUS  [ILLUSTRATIVE RATES]")

TB = 40
GB = TB * 1024
CLASSES = {                    # $/GB/month, minimum billable days, retrieval $/GB
    "Standard":                     (0.0230, 0,   0.000),
    "Standard-IA":                  (0.0125, 30,  0.010),
    "Glacier Instant Retrieval":    (0.0040, 90,  0.030),
    "Glacier Flexible Retrieval":   (0.0036, 90,  0.010),
    "Glacier Deep Archive":         (0.0010, 180, 0.020),
}
print(f"  {GB:,} GB corpus, 36 months\n")
print(f"  {'storage class':<30}{'$/GB/mo':>10}{'min days':>10}{'36 months':>13}{'retrieve all':>14}")
for name, (rate, mindays, retr) in CLASSES.items():
    print(f"  {name:<30}{rate:>10.4f}{mindays:>10}{rate * GB * 36:>13,.0f}{retr * GB:>14,.0f}")
POLICY = [("Standard", 3), ("Standard-IA", 9), ("Glacier Instant Retrieval", 24)]
tiered = sum(CLASSES[c][0] * GB * m for c, m in POLICY)
flat = CLASSES["Standard"][0] * GB * 36
print(f"\n  a lifecycle policy of {' -> '.join(f'{c} {m}mo' for c, m in POLICY)}:")
print(f"    ${tiered:,.0f} over 36 months vs ${flat:,.0f} all-Standard "
      f"-- {1 - tiered / flat:.0%} cheaper")
print("  Two traps. MINIMUM BILLABLE DURATION: an object moved to Standard-IA and")
print("  deleted after 10 days is billed for 30, so lifecycle rules on short-lived")
print("  objects can INCREASE the bill. And RETRIEVAL costs money: a RAG re-index")
print("  that reads the whole corpus from Glacier Instant Retrieval costs")
print(f"  ${CLASSES['Glacier Instant Retrieval'][2] * GB:,.0f} each time (M7-L16).")


# ============================================================ 4
rule("4. VERSIONING: WHAT DOES A DELETE ACTUALLY DO?")

EVENTS = [
    ("PUT report.pdf (v1, 10 MB)",     "versioning off", "1 object,  10 MB billed"),
    ("PUT report.pdf (v2, 10 MB)",     "versioning off", "1 object,  10 MB billed -- v1 is GONE"),
    ("PUT report.pdf (v1, 10 MB)",     "versioning ON",  "1 version, 10 MB billed"),
    ("PUT report.pdf (v2, 10 MB)",     "versioning ON",  "2 versions, 20 MB billed"),
    ("DELETE report.pdf",              "versioning ON",  "2 versions + delete marker, 20 MB STILL billed"),
    ("GET report.pdf",                 "versioning ON",  "404 -- the delete marker is the current version"),
    ("DELETE the delete marker",       "versioning ON",  "v2 is current again -- the object is restored"),
]
print(f"  {'event':<34}{'bucket state':<18}result")
for event, state, result in EVENTS:
    print(f"  {event:<34}{state:<18}{result}")
CORPUS_GB, REVISIONS, MONTHS = 8_000, 4, 12
extra = CORPUS_GB * (REVISIONS - 1) * CLASSES["Standard"][0] * MONTHS
print(f"\n  a {CORPUS_GB:,} GB corpus re-ingested {REVISIONS} times a year with versioning on and no")
print(f"  expiry rule stores {REVISIONS}x the data: ${extra:,.0f}/year of old versions nobody reads.")
print("  Versioning is the control that makes a delete or an overwrite recoverable")
print("  (section 5). It is also unbounded growth unless a lifecycle rule expires")
print("  NONCURRENT versions -- and that rule is the one teams forget (M10-L06).")


# ============================================================ 5
rule("5. ELEVEN NINES OF DURABILITY DOES NOT COVER THESE")

LOSSES = [
    ("a user or script overwrites the object",  "versioning + noncurrent retention"),
    ("a user or script deletes the object",     "versioning; MFA delete for the strictest cases"),
    ("credentials are compromised and data is wiped", "versioning + Object Lock + a separate account"),
    ("the whole bucket is deleted",             "Object Lock, deny-delete policy, replication to another account"),
    ("a bad ingestion overwrites good documents with bad ones", "versioning + a tested restore procedure"),
    ("the region is unavailable",               "cross-region replication (M11-L02)"),
    ("ransomware encrypts objects in place",    "Object Lock in compliance mode; versions in another account"),
]
print(f"  {'how data is actually lost':<52}what protects against it")
for loss, control in LOSSES:
    print(f"  {loss:<52}{control}")
print(f"\n  none of the {len(LOSSES)} rows above is a media failure, which is what durability")
print("  measures. Durability is about the disks; every row here is about PERMISSIONS")
print("  and TIME. Test the restore -- an untested backup is a belief (M10-L14).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: the Block Public Access evaluator implements the four documented")
print("  settings, and every cost, count and verdict above is computed by this script.")
print("\n  VERIFIED 2026-09-17: the four Block Public Access settings and their")
print("  behaviours follow the Amazon S3 User Guide; new buckets, access points and")
print("  objects do not allow public access by default, and BPA can be managed at")
print("  organisation, account and bucket level.")
print("\n  ILLUSTRATIVE: all storage, retrieval and KMS rates are invented, as are the")
print("  corpus sizes. Check current S3 pricing and minimum durations.")
print("\n  NOT SHOWN: access points, Object Lock configuration in detail, replication")
print("  mechanics, S3 Tables, and request-rate design (M11-L17, M12-L09).")
print("\nDone.")
