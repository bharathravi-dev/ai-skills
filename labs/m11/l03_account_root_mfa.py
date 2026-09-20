"""M11-L03 lab -- the account boundary, the root user, and why MFA is arithmetic.
This lab computes:

  1. the tasks that genuinely require root, against the tasks people use root for,
  2. blast radius by credential type: what one stolen credential reaches,
  3. MFA arithmetic: annual compromise probability under three authentication designs,
  4. account separation: the same breach in one account vs four,
  5. which baseline settings fail SILENTLY -- you only find out by checking.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l03_account_root_mfa.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. WHAT ACTUALLY REQUIRES ROOT?")

TASKS = [
    # task,                                                        needs_root, note
    ("change the account's root email, password or access keys",   True,  "standalone accounts"),
    ("close the account",                                          True,  "standalone accounts"),
    ("restore IAM permissions an admin revoked from themselves",   True,  "the classic lockout"),
    ("remove an S3 bucket policy that denies ALL principals",      True,  "self-inflicted deny"),
    ("delete an SQS resource policy that denies ALL principals",   True,  "same pattern"),
    ("activate IAM access to the Billing console",                  True,  "one-time setting"),
    ("register as a seller in the Reserved Instance Marketplace",  True,  "rare"),
    ("sign up for AWS GovCloud (US)",                              True,  "rare"),
    ("link an AWS account to an MTurk Requester account",          True,  "rare"),
    ("create an S3 bucket",                                        False, "any permitted IAM principal"),
    ("deploy the application",                                     False, "a deployment role"),
    ("read the bill",                                              False, "after the one-time activation above"),
    ("create IAM users and roles",                                 False, "an admin principal"),
    ("investigate an incident",                                    False, "a break-glass role, not root"),
    ("give a contractor temporary access",                         False, "a role with a short session"),
    ("change the account name or contact details",                 False, "not root, despite the name"),
]
need = [t for t, r, _ in TASKS if r]
dont = [t for t, r, _ in TASKS if not r]
print(f"  {'task':<56}{'root?':>8}   note")
for task, r, note in TASKS:
    print(f"  {task:<56}{('ROOT' if r else 'no'):>8}   {note}")
print(f"\n  require root: {len(need)}/{len(TASKS)}   do not: {len(dont)}/{len(TASKS)}")
print(f"  Of the {len(need)} that do, {sum(1 for t in ('register as a seller in the Reserved Instance Marketplace', 'sign up for AWS GovCloud (US)', 'link an AWS account to an MTurk Requester account') if t in need)}"
      " are rare one-offs and two are recovery from")
print("  mistakes you hope never to make. Root is a fire extinguisher: essential,")
print("  and not a tool you use to cook with.")


# ============================================================ 2
rule("2. BLAST RADIUS BY CREDENTIAL")

CAPABILITIES = ["read data", "write data", "create infra", "change IAM", "disable logging",
                "close account", "spend without limit", "reach prod"]
PRINCIPALS = {
    "root user":                    [1, 1, 1, 1, 1, 1, 1, 1],
    "IAM user with AdministratorAccess": [1, 1, 1, 1, 1, 0, 1, 1],
    "admin role, MFA + 1h session": [1, 1, 1, 1, 1, 0, 1, 1],
    "deployment role (prod)":       [1, 1, 1, 0, 0, 0, 1, 1],
    "read-only analyst role":       [1, 0, 0, 0, 0, 0, 0, 1],
    "app runtime role (least priv)": [1, 1, 0, 0, 0, 0, 0, 1],
}
print(f"  {'principal':<36}" + "".join(f"{c[:9]:>11}" for c in CAPABILITIES) + f"{'reach':>8}")
for name, caps in PRINCIPALS.items():
    print(f"  {name:<36}" + "".join(f"{('yes' if c else '-'):>11}" for c in caps)
          + f"{sum(caps)}/{len(caps):<3}".rjust(8))
print("\n  The rows differ by what a stolen credential BUYS an attacker, not by who")
print("  you trust. 'admin role, MFA + 1h session' has the same reach as the admin")
print("  user -- what it changes is how long the reach lasts and how it is obtained.")
print("  Reducing reach is a separate job from reducing the chance of theft (M11-L04).")


# ============================================================ 3
rule("3. MFA IS ARITHMETIC")

ATTEMPTS = 40            # credential-stuffing / phishing attempts against this identity per year
DESIGNS = {
    "password only, reused elsewhere":      0.020,
    "strong unique password, no MFA":       0.004,
    "password + TOTP app":                  0.0004,
    "password + phishing-resistant (FIDO2)": 0.00002,
}
print(f"  {ATTEMPTS} credible attempts per identity per year [ILLUSTRATIVE]\n")
print(f"  {'authentication design':<42}{'per attempt':>13}{'per year':>11}{'1 in':>10}")
for name, p in DESIGNS.items():
    annual = 1 - (1 - p) ** ATTEMPTS
    print(f"  {name:<42}{p:>13.5f}{annual:>11.2%}{1 / annual:>10,.0f}")
base = 1 - (1 - DESIGNS["strong unique password, no MFA"]) ** ATTEMPTS
totp = 1 - (1 - DESIGNS["password + TOTP app"]) ** ATTEMPTS
fido = 1 - (1 - DESIGNS["password + phishing-resistant (FIDO2)"]) ** ATTEMPTS
print(f"\n  adding TOTP cuts the annual figure {base / totp:.0f}x; phishing-resistant keys cut it {base / fido:.0f}x.")
print("  The difference between TOTP and FIDO2 is the phishing case: a one-time code")
print("  can be relayed to a fake site in real time, a bound credential cannot.")
print("  Now multiply by the row for 'root user' in section 2 (M11-L05).")


# ============================================================ 4
rule("4. ONE ACCOUNT OR FOUR?")

WORKLOADS = {"dev": 0.35, "test": 0.15, "staging": 0.10, "prod": 0.40}   # share of resources
PROD_DATA = "customer records, model access, production keys"
print(f"  a credential is compromised in the DEV environment\n")
print(f"  {'account layout':<34}{'reachable resources':>22}{'prod data reachable?':>24}")
print(f"  {'one account for everything':<34}{'100%':>22}{'YES':>24}")
non_prod = (1 - WORKLOADS["prod"]) * 100
dev_only = WORKLOADS["dev"] * 100
print(f"  {'separate prod account':<34}{f'{non_prod:.0f}%':>22}{'no':>24}")
print(f"  {'one account per environment':<34}{f'{dev_only:.0f}%':>22}{'no':>24}")
print(f"\n  the same mistake costs {1 / WORKLOADS['dev']:.1f}x less with per-environment accounts, and")
print(f"  cannot reach {PROD_DATA} at all.")
print("  Accounts are the strongest isolation boundary AWS offers -- stronger than")
print("  any IAM policy, because it is not a policy anyone can edit by accident")
print("  (M10-L07). Use AWS Organizations to manage them centrally.")


# ============================================================ 5
rule("5. WHICH BASELINE SETTINGS FAIL SILENTLY?")

BASELINE = [
    # setting,                                      noisy failure?,  how you find out if not
    ("MFA on the root user",                        False, "only by checking, or after a breach"),
    ("no root access keys",                         False, "only by checking"),
    ("root email is a monitored group",              False, "when the person leaves"),
    ("billing alerts configured",                   False, "when the bill arrives (M11-L06)"),
    ("CloudTrail enabled in all regions",           False, "when you need the logs and they are absent"),
    ("S3 Block Public Access at account level",     False, "when a bucket leaks"),
    ("IAM Identity Center instead of IAM users",    True,  "people notice they cannot log in"),
    ("password policy and session duration",        False, "only by checking"),
    ("contact and security-contact details current", False, "when AWS cannot reach you in an incident"),
    ("a second admin who can restore permissions",  False, "during the lockout itself"),
]
silent = [b for b, noisy, _ in BASELINE if not noisy]
print(f"  {'baseline setting':<44}{'fails loudly?':>15}   otherwise you find out...")
for name, noisy, how in BASELINE:
    print(f"  {name:<44}{('yes' if noisy else 'NO'):>15}   {how}")
print(f"\n  silent if missing: {len(silent)}/{len(BASELINE)}")
print("  Nine of ten produce no symptom at all until the day they matter. That is")
print("  what makes them a CHECKLIST rather than a habit: run it on every new")
print("  account, and re-run it on a schedule (M10-L15, M11-L18).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count, blast-radius figure, annual probability and ratio above")
print("  is computed from the values in this script.")
print("\n  VERIFIED 2026-09-16: the root-only task list in section 1 follows the AWS IAM")
print("  User Guide, 'Tasks that require root user credentials'.")
print("\n  ILLUSTRATIVE: the per-attempt compromise probabilities, attempt rate and")
print("  resource shares are invented to make the arithmetic visible.")
print("\n  NOT SHOWN: the console steps themselves, AWS Organizations SCPs (M11-L04),")
print("  and identity federation (M11-L05).")
print("\nDone.")
