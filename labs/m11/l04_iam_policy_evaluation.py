"""M11-L04 lab -- a working IAM policy evaluator, plus least privilege measured.
This lab implements AWS's documented evaluation rules and uses them to compute:

  1. deny-by-default and explicit deny, over eight requests,
  2. identity + resource policy (UNION) vs identity + boundary (INTERSECTION)
     vs identity + SCP (INTERSECTION),
  3. what a wildcard actually grants, counted against a small action catalogue,
  4. least privilege measured: actions granted vs actions used in 30 days,
  5. a cross-account trust policy, with and without an external ID.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l04_iam_policy_evaluation.py
"""

from __future__ import annotations

import fnmatch
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# --------------------------------------------------------------------------- engine
def matches(patterns, value: str) -> bool:
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatchcase(value, p) for p in patterns)


def evaluate(policy: dict | None, action: str, resource: str) -> str:
    """Return 'Deny', 'Allow' or 'none' for one policy document."""
    if not policy:
        return "none"
    verdict = "none"
    for stmt in policy["Statement"]:
        if matches(stmt["Action"], action) and matches(stmt["Resource"], resource):
            if stmt["Effect"] == "Deny":
                return "Deny"                      # explicit deny short-circuits
            verdict = "Allow"
    return verdict


def authorize(action: str, resource: str, *, identity=None, resource_policy=None,
              boundary=None, scp=None, same_account: bool = True) -> tuple[bool, str]:
    """AWS's documented rules, in order."""
    results = {
        "identity": evaluate(identity, action, resource),
        "resource": evaluate(resource_policy, action, resource),
        "boundary": evaluate(boundary, action, resource),
        "scp": evaluate(scp, action, resource),
    }
    # 1. an explicit Deny anywhere wins
    for where, r in results.items():
        if r == "Deny":
            return False, f"explicit Deny in the {where} policy"
    # 2. an SCP, if present, must Allow (intersection)
    if scp is not None and results["scp"] != "Allow":
        return False, "no Allow in the SCP (implicit deny)"
    # 3. a permissions boundary, if present, must Allow (intersection)
    if boundary is not None and results["boundary"] != "Allow":
        return False, "no Allow in the permissions boundary (implicit deny)"
    # 4. same account: identity OR resource policy may Allow (union)
    if same_account and (results["identity"] == "Allow" or results["resource"] == "Allow"):
        src = "identity policy" if results["identity"] == "Allow" else "resource policy"
        return True, f"Allow from the {src}"
    if not same_account and results["identity"] == "Allow" and results["resource"] == "Allow":
        return True, "Allow from BOTH sides (cross-account)"
    return False, "no Allow anywhere (deny by default)"


# --------------------------------------------------------------------------- policies
READ_BUCKET = {"Statement": [
    {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"],
     "Resource": ["arn:aws:s3:::reports", "arn:aws:s3:::reports/*"]}]}
ADMIN = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}
DENY_DELETE = {"Statement": [
    {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
    {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"}]}
BUCKET_POLICY = {"Statement": [
    {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::public-docs/*"}]}
BOUNDARY_READONLY = {"Statement": [
    {"Effect": "Allow", "Action": ["s3:Get*", "s3:List*"], "Resource": "*"}]}
SCP_NO_IAM = {"Statement": [
    {"Effect": "Allow", "Action": "*", "Resource": "*"},
    {"Effect": "Deny", "Action": "iam:*", "Resource": "*"}]}

# ============================================================ 1
rule("1. DENY BY DEFAULT, AND EXPLICIT DENY")

REQUESTS = [
    ("s3:GetObject",    "arn:aws:s3:::reports/q3.csv",     READ_BUCKET, None),
    ("s3:PutObject",    "arn:aws:s3:::reports/q3.csv",     READ_BUCKET, None),
    ("s3:GetObject",    "arn:aws:s3:::payroll/staff.csv",  READ_BUCKET, None),
    ("s3:DeleteObject", "arn:aws:s3:::reports/q3.csv",     DENY_DELETE, None),
    ("s3:PutObject",    "arn:aws:s3:::reports/q3.csv",     DENY_DELETE, None),
    ("s3:GetObject",    "arn:aws:s3:::public-docs/a.pdf",  None,        BUCKET_POLICY),
    ("s3:PutObject",    "arn:aws:s3:::public-docs/a.pdf",  None,        BUCKET_POLICY),
    ("iam:CreateUser",  "*",                               ADMIN,       None),
]
print(f"  {'action':<17}{'resource':<34}{'verdict':>9}   why")
for action, resource, ident, rp in REQUESTS:
    ok, why = authorize(action, resource, identity=ident, resource_policy=rp)
    print(f"  {action:<17}{resource:<34}{('ALLOW' if ok else 'deny'):>9}   {why}")
print("\n  Nothing is permitted unless something permits it, and an explicit Deny")
print("  cannot be outvoted. Row 4 is the pattern to recognise: a policy that allows")
print("  's3:*' and denies one action still denies that action.")


# ============================================================ 2
rule("2. UNION, INTERSECTION, INTERSECTION")

CASES = [
    ("identity only",                     dict(identity=READ_BUCKET)),
    ("resource policy only (same acct)",  dict(resource_policy=BUCKET_POLICY)),
    ("identity + resource policy",        dict(identity=READ_BUCKET, resource_policy=BUCKET_POLICY)),
    ("admin identity + read-only boundary", dict(identity=ADMIN, boundary=BOUNDARY_READONLY)),
    ("admin identity + SCP denying IAM",  dict(identity=ADMIN, scp=SCP_NO_IAM)),
]
PROBES = [("Get reports", "s3:GetObject", "arn:aws:s3:::reports/q3.csv"),
          ("Get public", "s3:GetObject", "arn:aws:s3:::public-docs/a.pdf"),
          ("Delete", "s3:DeleteObject", "arn:aws:s3:::reports/q3.csv"),
          ("CreateUser", "iam:CreateUser", "*")]
print(f"  {'configuration':<38}" + "".join(f"{label:>13}" for label, _, _ in PROBES))
for label, kwargs in CASES:
    row = ""
    for _, action, resource in PROBES:
        ok, _ = authorize(action, resource, **kwargs)
        row += f"{('ALLOW' if ok else 'deny'):>13}"
    print(f"  {label:<38}{row}")
print("\n  identity + resource policy = UNION: either one can grant it.")
print("  identity + permissions boundary = INTERSECTION: the boundary caps an")
print("  administrator down to read-only without editing their policy.")
print("  identity + SCP = INTERSECTION: the SCP's Deny on iam:* wins over 'Action: *'.")


# ============================================================ 3
rule("3. WHAT DOES A WILDCARD ACTUALLY GRANT?")

CATALOGUE = [
    "s3:GetObject", "s3:GetObjectVersion", "s3:ListBucket", "s3:PutObject", "s3:DeleteObject",
    "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:PutBucketAcl", "s3:GetBucketPolicy",
    "s3:PutBucketVersioning", "s3:PutObjectAcl", "s3:RestoreObject",
]
DANGEROUS = {"s3:DeleteObject", "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:PutBucketAcl",
             "s3:PutObjectAcl", "s3:PutBucketVersioning"}
GRANTS = ["s3:*", "s3:Get*", "s3:*Object", "s3:*Bucket*",
          "s3:GetObject", "s3:GetObject|s3:ListBucket|s3:PutObject"]
print(f"  action catalogue: {len(CATALOGUE)} actions, of which {len(DANGEROUS)} can change access or destroy data\n")
print(f"  {'grant':<42}{'actions':>9}{'dangerous':>12}   which dangerous ones")
for g in GRANTS:
    pats = g.split("|")
    hit = [a for a in CATALOGUE if matches(pats, a)]
    bad = [a for a in hit if a in DANGEROUS]
    names = ", ".join(b.split(":")[1] for b in bad) or "none"
    print(f"  {g:<42}{len(hit):>9}{len(bad):>12}   {names[:40]}")
print("\n  's3:Get*' looks careful and grants no destructive action. 's3:*Object' looks")
print("  narrower than 's3:*' and still grants Delete and PutObjectAcl. Read a")
print("  wildcard by EXPANDING it against the real action list, never by eye.")


# ============================================================ 4
rule("4. LEAST PRIVILEGE, MEASURED")

ROLES = {
    #                        granted actions,                       used in 30 days
    "app runtime role":      (["s3:*", "dynamodb:*", "sqs:*", "kms:*"],
                              ["s3:GetObject", "s3:PutObject", "dynamodb:GetItem",
                               "dynamodb:PutItem", "kms:Decrypt"]),
    "data science role":     (["s3:*", "athena:*", "glue:*"],
                              ["s3:GetObject", "s3:ListBucket", "athena:StartQueryExecution"]),
    "deployment role":       (["*"], ["cloudformation:*", "s3:PutObject", "iam:PassRole",
                                      "ecs:UpdateService", "logs:CreateLogGroup"]),
}
EXPANSION = {"s3:*": 40, "dynamodb:*": 35, "sqs:*": 20, "kms:*": 30, "athena:*": 25,
             "glue:*": 60, "cloudformation:*": 45, "*": 18000}
print(f"  {'role':<22}{'granted (approx actions)':>26}{'used in 30d':>13}{'over-permission':>17}")
for name, (granted, used) in ROLES.items():
    approx = sum(EXPANSION.get(g, 1) for g in granted)
    ratio = approx / max(1, len(used))
    print(f"  {name:<22}{approx:>26,}{len(used):>13}{ratio:>16,.0f}x")
print("\n  'Least privilege' is not a feeling; it is this ratio. Generate the next")
print("  version of each policy FROM the 30-day usage, review the diff, and repeat")
print("  (AWS calls this access-analyzer policy generation). The deployment role")
print("  shows the other half of the problem: iam:PassRole is one action and it is")
print("  how a narrow role becomes an administrator (M11-L05).")


# ============================================================ 5
rule("5. A CROSS-ACCOUNT ROLE, AND THE CONFUSED DEPUTY")

TRUST_WEAK = {"Statement": [
    {"Effect": "Allow", "Action": "sts:AssumeRole", "Resource": "arn:aws:iam::*:role/VendorAccess"}]}
TRUST_STRONG = {"Statement": [
    {"Effect": "Allow", "Action": "sts:AssumeRole", "Resource": "arn:aws:iam::999:role/VendorAccess",
     "Condition": "sts:ExternalId == 'a7f3-customer-42'"}]}
ATTEMPTS = [
    ("the vendor, acting for us",        "arn:aws:iam::999:role/VendorAccess", "a7f3-customer-42"),
    ("the vendor, acting for a DIFFERENT customer", "arn:aws:iam::999:role/VendorAccess", "b2c9-customer-77"),
    ("an unrelated account",             "arn:aws:iam::555:role/VendorAccess", "a7f3-customer-42"),
]
print(f"  {'who is asking':<46}{'weak trust':>13}{'with external ID':>19}")
for who, principal, ext in ATTEMPTS:
    weak, _ = authorize("sts:AssumeRole", principal, resource_policy=TRUST_WEAK)
    strong_stmt = TRUST_STRONG["Statement"][0]
    strong = (matches(strong_stmt["Resource"], principal)
              and ext == "a7f3-customer-42")
    print(f"  {who:<46}{('ALLOW' if weak else 'deny'):>13}{('ALLOW' if strong else 'deny'):>19}")
print("\n  The weak trust policy trusts a role NAME in ANY account, and trusts the")
print("  vendor to remember which customer it is acting for. The external ID makes")
print("  the vendor prove it -- which is the whole point of the confused-deputy")
print("  control (M9-L11, M10-L10).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: the evaluator implements AWS's documented rules -- deny by default,")
print("  explicit deny wins, identity/resource = union, boundary and SCP = intersection")
print("  -- and every verdict, count and ratio above comes from running it.")
print("\n  SIMPLIFIED: real IAM has condition keys, session policies, RCPs, service-linked")
print("  roles, ABAC tags and per-service quirks. The action-count expansions in")
print("  section 4 are approximations, not the real catalogue sizes.")
print("\n  NOT SHOWN: the IAM console, Access Analyzer itself, and the policy language's")
print("  full grammar (M11-L05, M12-L08).")
print("\nDone.")
