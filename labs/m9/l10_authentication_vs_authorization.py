"""M9-L10 lab -- authentication (who is calling?) and authorization (what may
they do?) are different checks, and an MCP server needs both. This lab builds a
small signed-token scheme with the standard library, then runs the SAME matrix of
callers x operations against four server designs and counts policy violations:

  A. "valid token = allowed"                  (authentication only)
  B. tool-level scopes                        (coarse authorization)
  C. scopes + object-level checks             (fine authorization)
  D. design C, but trusting self-reported clientInfo for an admin bypass

It also measures two common shortcuts: hiding tools from tools/list instead of
enforcing on tools/call, and returning 401 where 403 is correct (and vice versa).

Tokens here are HMAC-signed JSON, not real JWTs or OAuth -- M9-L11 covers where
real tokens come from. Deterministic. No API key, no network, no dependencies.
Run:  python labs/m9/l10_authentication_vs_authorization.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


ISSUER_KEY = b"lab-issuer-signing-key"          # never hard-code keys in real code
THIS_SERVER = "https://catalog.example.com/mcp"
NOW = 1_800_000_000


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def mint(claims: dict, key: bytes = ISSUER_KEY) -> str:
    body = b64(json.dumps(claims, sort_keys=True).encode())
    return body + "." + b64(hmac.new(key, body.encode(), hashlib.sha256).digest())


def authenticate(token: str | None) -> tuple[dict | None, str]:
    """[REAL] Authentication: is this a genuine, current token meant for THIS server?"""
    if not token:
        return None, "no token"
    body, _, sig = token.partition(".")
    good = b64(hmac.new(ISSUER_KEY, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, good):
        return None, "bad signature"
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    if claims["exp"] <= NOW:
        return None, "expired"
    if claims["aud"] != THIS_SERVER:
        return None, "wrong audience"
    return claims, "ok"


# ------------------------------------------------------------------ callers
CALLERS = {
    "anonymous": (None, {}),
    "forged": (mint({"sub": "eve", "scope": "catalog:admin", "aud": THIS_SERVER, "exp": NOW + 600},
                    key=b"attacker-key"), {}),
    "expired": (mint({"sub": "li", "scope": "catalog:read progress:self", "aud": THIS_SERVER, "exp": NOW - 5}), {}),
    "other-audience": (mint({"sub": "li", "scope": "catalog:admin", "aud": "https://billing.example.com/mcp",
                             "exp": NOW + 600}), {}),
    "learner li": (mint({"sub": "li", "scope": "catalog:read progress:self", "aud": THIS_SERVER, "exp": NOW + 600}), {}),
    "learner li (spoofs clientInfo)": (mint({"sub": "li", "scope": "catalog:read progress:self", "aud": THIS_SERVER,
                                             "exp": NOW + 600}), {"name": "admin-console"}),
    "instructor ana": (mint({"sub": "ana", "scope": "catalog:read progress:team", "aud": THIS_SERVER,
                             "exp": NOW + 600, "team": ["li", "raj"]}), {}),
    "admin sam": (mint({"sub": "sam", "scope": "catalog:read catalog:admin progress:all", "aud": THIS_SERVER,
                        "exp": NOW + 600}), {}),
}

# operation -> (required scope, object-level rule)
OPERATIONS = {
    "search_courses": ("catalog:read", None),
    "get_progress(li)": ("progress:self", ("li",)),
    "get_progress(raj)": ("progress:self", ("raj",)),
    "set_course_price": ("catalog:admin", None),
}


def policy(caller: str, op: str) -> int:
    """The INTENDED outcome, written out by hand: 200, 401 or 403."""
    token, _ = CALLERS[caller]
    claims, why = authenticate(token)
    if claims is None:
        return 401
    scopes = set(claims["scope"].split())
    if op == "search_courses":
        return 200 if "catalog:read" in scopes else 403
    if op == "set_course_price":
        return 200 if "catalog:admin" in scopes else 403
    target = op[op.index("(") + 1:-1]
    if "progress:all" in scopes:
        return 200
    if "progress:team" in scopes and target in claims.get("team", []):
        return 200
    if "progress:self" in scopes and target == claims["sub"]:
        return 200
    return 403


def design_a(token, client_info, op):
    claims, _ = authenticate(token)
    return 401 if claims is None else 200


def design_b(token, client_info, op):
    claims, _ = authenticate(token)
    if claims is None:
        return 401
    scopes = set(claims["scope"].split())
    needed = OPERATIONS[op][0]
    if needed.startswith("progress:"):
        return 200 if scopes & {"progress:self", "progress:team", "progress:all"} else 403
    return 200 if needed in scopes else 403


def design_c(token, client_info, op):
    claims, _ = authenticate(token)
    if claims is None:
        return 401
    scopes = set(claims["scope"].split())
    if not op.startswith("get_progress"):
        return 200 if OPERATIONS[op][0] in scopes else 403
    target = op[op.index("(") + 1:-1]
    allowed = ("progress:all" in scopes or ("progress:team" in scopes and target in claims.get("team", []))
               or ("progress:self" in scopes and target == claims["sub"]))
    return 200 if allowed else 403


def design_d(token, client_info, op):
    if client_info.get("name") == "admin-console":         # "our admin UI is trusted"
        claims, _ = authenticate(token)
        return 401 if claims is None else 200
    return design_c(token, client_info, op)


def design_e(token, client_info, op):
    """Design C's decisions, but 403 for every refusal -- a very common shortcut."""
    return 403 if design_c(token, client_info, op) != 200 else 200


# ============================================================ 1
rule("1. AUTHENTICATION: IS THIS A GENUINE, CURRENT TOKEN FOR THIS SERVER?")
for caller, (token, _) in CALLERS.items():
    claims, why = authenticate(token)
    who = f"sub={claims['sub']}, scope='{claims['scope']}'" if claims else ""
    print(f"  {caller:<31} -> {why:<15} {who}")
print("\n  Authentication ends here. It says nothing yet about WHICH operations")
print("  learner li may perform -- that is authorization.")


# ============================================================ 2
rule("2. THE SAME REQUEST MATRIX AGAINST FOUR SERVER DESIGNS")

designs = {"A auth only": design_a, "B tool scopes": design_b, "C scopes+objects": design_c,
           "D C+clientInfo trust": design_d, "E C, 403 for all refusals": design_e}
header = "  caller / operation".ljust(55) + "policy  " + "  ".join(f"{k[:1]:>3}" for k in designs)
print(header)
totals = {k: {"too_permissive": 0, "wrong_code": 0} for k in designs}
for caller, (token, info) in CALLERS.items():
    for op in OPERATIONS:
        want = policy(caller, op)
        row = f"  {caller:<31} {op:<21} {want:>5}  "
        cells = []
        for name, fn in designs.items():
            got = fn(token, info, op)
            if got == 200 and want != 200:
                totals[name]["too_permissive"] += 1
                mark = "!"
            elif got != want:
                totals[name]["wrong_code"] += 1
                mark = "~"
            else:
                mark = " "
            cells.append(f"{got}{mark}")
        print(row + " ".join(cells))
print("\n  ! = allowed something the policy forbids   ~ = wrong status code")
n = len(CALLERS) * len(OPERATIONS)
for name, t in totals.items():
    print(f"  design {name:<26}: {t['too_permissive']:>2}/{n} forbidden requests allowed, "
          f"{t['wrong_code']:>2} other wrong codes")


# ============================================================ 3
rule("3. HIDING A TOOL FROM tools/list IS NOT ENFORCING IT")


TOOL_SCOPES = {"search_courses": {"catalog:read"},
               "get_progress": {"progress:self", "progress:team", "progress:all"},
               "set_course_price": {"catalog:admin"}}


def tools_list_for(token):
    claims, _ = authenticate(token)
    scopes = set(claims["scope"].split()) if claims else set()
    return [name for name, needs in TOOL_SCOPES.items() if scopes & needs]


def call_without_enforcement(token, op):
    claims, _ = authenticate(token)
    return 401 if claims is None else 200          # "they can't see it, so they won't call it"


li_token = CALLERS["learner li"][0]
listed = tools_list_for(li_token)
print(f"  tools/list for learner li shows: {listed}")
print(f"  li calls set_course_price anyway (a name seen in docs, logs or another")
print(f"  user's screenshot): list-filtering server -> HTTP {call_without_enforcement(li_token, 'set_course_price')}, "
      f"design C -> HTTP {design_c(li_token, {}, 'set_course_price')}")
print("\n  A filtered tools/list is a usability feature. Every tools/call must be")
print("  authorized on its own, because clients can send any name they like.")


# ============================================================ 4
rule("4. 401 VS 403: WHAT THE CLIENT DOES NEXT DEPENDS ON THE CODE")
examples = [("anonymous", "search_courses"), ("expired", "search_courses"),
            ("other-audience", "search_courses"), ("learner li", "set_course_price")]
for caller, op in examples:
    code = design_c(CALLERS[caller][0], {}, op)
    meaning = ("authenticate (again): get or refresh a token" if code == 401
               else "stop, or request more scope (step-up), do NOT re-login blindly")
    print(f"  {caller:<16} {op:<18} -> {code}: {meaning}")
print("\n  A server that answers 401 for 'insufficient permission' sends clients into")
print("  a login loop; one that answers 403 for an expired token stops them from")
print("  refreshing. The status code is part of the contract.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every status code in section 2 is computed by running each design")
print("  against every caller and operation; the violation counts are those runs.")
print("\n  ILLUSTRATIVE: tokens are HMAC-signed JSON with a hard-coded key, not OAuth")
print("  access tokens; the policy table is a small hand-written example.")
print("\n  NOT SHOWN: obtaining tokens (M9-L11), token storage and passthrough")
print("  (M9-L12), and enforcement patterns such as handle binding (M9-L13).")
print("\nDone.")
