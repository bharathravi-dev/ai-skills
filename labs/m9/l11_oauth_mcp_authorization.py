"""M9-L11 lab -- the OAuth 2.1 flow the MCP authorization spec (2026-07-28)
requires for HTTP servers, simulated in one process with real cryptography:

  1. discovery: 401 + WWW-Authenticate -> Protected Resource Metadata (RFC 9728)
     -> authorization server metadata URLs in the mandated order (RFC 8414 / OIDC),
  2. client registration choice: pre-registration, Client ID Metadata Document,
     Dynamic Client Registration (deprecated),
  3. PKCE (RFC 7636): S256 checked against the RFC's own test vector; a stolen
     code with and without the verifier; why 'plain' is weaker; refusing an
     authorization server that does not advertise PKCE,
  4. resource indicators (RFC 8707): audience-bound tokens across two MCP servers,
  5. mix-up attack and issuer validation (RFC 9207),
  6. step-up authorization: replacing scopes vs taking the union.

No real authorization server, browser or network is involved; every "HTTP" step
is a function call. Deterministic. No API key, no network, no dependencies.
Run:  python labs/m9/l11_oauth_mcp_authorization.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sys
from urllib.parse import urlsplit

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


# ============================================================ 1
rule("1. DISCOVERY: FROM A 401 TO THE AUTHORIZATION SERVER'S ENDPOINTS")

MCP_URL = "https://mcp.example.com/catalog/mcp"
ISSUER = "https://auth.example.com/tenant1"

PRM = {"resource": MCP_URL, "authorization_servers": [ISSUER], "scopes_supported": ["catalog:read"]}


def mcp_request_without_token():
    return 401, {"WWW-Authenticate": 'Bearer resource_metadata="https://mcp.example.com/.well-known/'
                                     'oauth-protected-resource/catalog/mcp", scope="catalog:read"'}


def parse_www_authenticate(value: str) -> dict:
    scheme, _, rest = value.partition(" ")
    params = {}
    for part in rest.split(","):
        k, _, v = part.strip().partition("=")
        params[k] = v.strip('"')
    return {"scheme": scheme, **params}


def prm_well_known_candidates(mcp_url: str) -> list[str]:
    u = urlsplit(mcp_url)
    base = f"{u.scheme}://{u.netloc}"
    path = u.path.rstrip("/")
    return ([f"{base}/.well-known/oauth-protected-resource{path}"] if path else []) + \
           [f"{base}/.well-known/oauth-protected-resource"]


def as_metadata_candidates(issuer: str) -> list[str]:
    u = urlsplit(issuer)
    base, path = f"{u.scheme}://{u.netloc}", u.path.rstrip("/")
    if path:
        return [f"{base}/.well-known/oauth-authorization-server{path}",
                f"{base}/.well-known/openid-configuration{path}",
                f"{base}{path}/.well-known/openid-configuration"]
    return [f"{base}/.well-known/oauth-authorization-server", f"{base}/.well-known/openid-configuration"]


status, headers = mcp_request_without_token()
challenge = parse_www_authenticate(headers["WWW-Authenticate"])
print(f"  MCP request with no token -> HTTP {status}")
print(f"    resource_metadata = {challenge['resource_metadata']}")
print(f"    scope             = {challenge['scope']}   (use this first when requesting a token)")
print(f"  if the header had no resource_metadata, try in order:")
for url in prm_well_known_candidates(MCP_URL):
    print(f"    {url}")
print(f"  Protected Resource Metadata says authorization_servers = {PRM['authorization_servers']}")
print(f"  authorization server metadata URLs for issuer '{ISSUER}', in the required order:")
for url in as_metadata_candidates(ISSUER):
    print(f"    {url}")
print(f"  ...and for an issuer with no path ('https://auth.example.com'):")
for url in as_metadata_candidates("https://auth.example.com"):
    print(f"    {url}")


# ============================================================ 2
rule("2. CLIENT REGISTRATION: WHICH MECHANISM, IN WHAT ORDER")


def choose_registration(pre_registered: bool, as_meta: dict) -> str:
    if pre_registered:
        return "use pre-registered client_id (keyed by this issuer)"
    if as_meta.get("client_id_metadata_document_supported"):
        return "use a Client ID Metadata Document (HTTPS URL as client_id)"
    if as_meta.get("registration_endpoint"):
        return "Dynamic Client Registration (deprecated fallback)"
    return "ask the user to enter client details"


cases = [
    ("enterprise AS, client pre-registered", True, {}),
    ("AS advertises CIMD", False, {"client_id_metadata_document_supported": True, "registration_endpoint": "/register"}),
    ("older AS with DCR only", False, {"registration_endpoint": "/register"}),
    ("AS with neither", False, {}),
]
for label, pre, meta in cases:
    print(f"  {label:<38} -> {choose_registration(pre, meta)}")


# ============================================================ 3
rule("3. PKCE: S256, A STOLEN CODE, AND WHY 'plain' IS WEAKER")

rfc_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
rfc_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
computed = b64url(hashlib.sha256(rfc_verifier.encode()).digest())
print(f"  RFC 7636 Appendix B verifier : {rfc_verifier}")
print(f"  S256 challenge computed here : {computed}")
print(f"  matches the RFC's value      : {computed == rfc_challenge}")


class AuthorizationServer:
    def __init__(self, issuer: str, key: bytes, pkce_methods=("S256",)):
        self.issuer, self.key = issuer, key
        self.metadata = {"issuer": issuer, "authorization_endpoint": f"{issuer}/authorize",
                         "token_endpoint": f"{issuer}/token", "authorization_response_iss_parameter_supported": True}
        if pkce_methods:
            self.metadata["code_challenge_methods_supported"] = list(pkce_methods)
        self.codes: dict[str, dict] = {}
        self.counter = 0

    def authorize(self, client_id, redirect_uri, challenge, method, resource, scope, user="li"):
        self.counter += 1
        code = f"code-{self.issuer.rsplit('/', 1)[-1]}-{self.counter}"
        self.codes[code] = {"client_id": client_id, "redirect_uri": redirect_uri, "challenge": challenge,
                            "method": method, "resource": resource, "scope": scope, "sub": user}
        return {"code": code, "iss": self.issuer}

    def token(self, code, verifier, client_id, redirect_uri, resource):
        grant = self.codes.pop(code, None)                       # single use
        if grant is None or grant["client_id"] != client_id or grant["redirect_uri"] != redirect_uri:
            return None, "invalid_grant"
        if verifier is None:
            return None, "invalid_grant (no code_verifier)"
        expected = b64url(hashlib.sha256(verifier.encode()).digest()) if grant["method"] == "S256" else verifier
        if not hmac.compare_digest(expected, grant["challenge"]):
            return None, "invalid_grant (PKCE mismatch)"
        if resource != grant["resource"]:
            return None, "invalid_target"
        claims = {"iss": self.issuer, "sub": grant["sub"], "aud": resource, "scope": grant["scope"], "exp": 1_800_000_600}
        body = b64url(json.dumps(claims, sort_keys=True).encode())
        return body + "." + b64url(hmac.new(self.key, body.encode(), hashlib.sha256).digest()), "ok"


AS = AuthorizationServer(ISSUER, b"as-signing-key")
CLIENT_ID, REDIRECT = "https://app.example.com/oauth/client-metadata.json", "http://127.0.0.1:3000/callback"

# the legitimate flow
resp = AS.authorize(CLIENT_ID, REDIRECT, rfc_challenge, "S256", MCP_URL, "catalog:read")
token, why = AS.token(resp["code"], rfc_verifier, CLIENT_ID, REDIRECT, MCP_URL)
print(f"\n  legitimate client redeems its code with the verifier -> {why}")

# an attacker intercepts the redirect (e.g. another app on the same loopback port)
resp = AS.authorize(CLIENT_ID, REDIRECT, rfc_challenge, "S256", MCP_URL, "catalog:read")
_, why = AS.token(resp["code"], None, CLIENT_ID, REDIRECT, MCP_URL)
print(f"  attacker redeems an intercepted S256 code, no verifier -> {why}")

# 'plain': the challenge IS the verifier, so anyone who saw the authorization request can redeem
plain_verifier = "plain-verifier-visible-in-the-authorization-url-0123456789"
resp = AS.authorize(CLIENT_ID, REDIRECT, plain_verifier, "plain", MCP_URL, "catalog:read")
_, why = AS.token(resp["code"], plain_verifier, CLIENT_ID, REDIRECT, MCP_URL)
print(f"  attacker who saw a 'plain' challenge redeems the code  -> {why}")
_, why = AS.token(AS.authorize(CLIENT_ID, REDIRECT, rfc_challenge, "S256", MCP_URL, "catalog:read")["code"],
                  rfc_challenge, CLIENT_ID, REDIRECT, MCP_URL)
print(f"  attacker who saw an S256 challenge tries it as verifier -> {why}")

no_pkce_as = AuthorizationServer("https://legacy-auth.example.com", b"k", pkce_methods=())
proceed = "code_challenge_methods_supported" in no_pkce_as.metadata
print(f"\n  AS metadata without code_challenge_methods_supported -> client proceeds? {proceed} (MUST refuse)")


# ============================================================ 4
rule("4. RESOURCE INDICATORS: TOKENS BOUND TO ONE MCP SERVER")

BILLING_URL = "https://mcp.example.com/billing/mcp"


def mcp_server_accepts(server_url: str, token: str, check_audience: bool) -> bool:
    body, _, sig = token.partition(".")
    if not hmac.compare_digest(sig, b64url(hmac.new(b"as-signing-key", body.encode(), hashlib.sha256).digest())):
        return False
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    return (claims["aud"] == server_url) if check_audience else True


catalog_token, _ = AS.token(AS.authorize(CLIENT_ID, REDIRECT, rfc_challenge, "S256", MCP_URL, "catalog:read")["code"],
                            rfc_verifier, CLIENT_ID, REDIRECT, MCP_URL)
for server, url in (("catalog MCP server", MCP_URL), ("billing MCP server", BILLING_URL)):
    print(f"  catalog token presented to {server:<19} audience checked: "
          f"{mcp_server_accepts(url, catalog_token, True)!s:<5}  not checked: {mcp_server_accepts(url, catalog_token, False)}")
print("\n  Same authorization server, same signing key: only the audience claim, set")
print("  from the client's `resource` parameter, stops a catalog token working at billing.")


# ============================================================ 5
rule("5. MIX-UP ATTACK AND ISSUER VALIDATION (RFC 9207)")

HONEST = AS
ATTACKER = AuthorizationServer("https://auth.evil.example", b"evil-key")
leaked = {"without iss check": 0, "with iss check": 0}
for policy in leaked:
    for attempt in range(5):
        recorded_issuer = ATTACKER.issuer                     # user started "log in with evil.example"
        # the attacker's authorize endpoint bounces the browser to the HONEST server,
        # using this client's registration there; the honest server returns code + iss
        response = HONEST.authorize(CLIENT_ID, REDIRECT, rfc_challenge, "S256", MCP_URL, "catalog:read")
        if policy == "with iss check" and response["iss"] != recorded_issuer:
            continue                                          # reject before redeeming anything
        # client redeems at the token endpoint of the issuer it RECORDED -> the attacker's
        leaked[policy] += 1                                   # the attacker now holds an honest code + verifier
for policy, n in leaked.items():
    print(f"  {policy:<18}: honest authorization codes sent to the attacker's token endpoint = {n}/5")
print("\n  PKCE does not help here: the client itself hands the attacker the verifier.")


# ============================================================ 6
rule("6. STEP-UP AUTHORIZATION: REPLACE SCOPES OR TAKE THE UNION?")

NEEDS = {"search_courses": "catalog:read", "set_course_price": "catalog:write"}
operations = ["search_courses", "set_course_price", "search_courses", "set_course_price", "search_courses", "search_courses"]
for strategy in ("replace", "union"):
    granted, reauths, trace = {"catalog:read"}, 0, []
    for op in operations:
        if NEEDS[op] not in granted:                          # server: 403 insufficient_scope scope="<needed>"
            reauths += 1
            granted = {NEEDS[op]} if strategy == "replace" else granted | {NEEDS[op]}
            trace.append(f"{op}:403->reauth")
        else:
            trace.append(f"{op}:200")
    print(f"  {strategy:<7}: {reauths} extra authorizations for {len(operations)} operations; final scopes {sorted(granted)}")
print("\n  Replacing scopes drops read access every time write access is granted, so the")
print("  user is sent back to the consent screen on every switch. The spec says clients")
print("  SHOULD request the union of previously requested and newly challenged scopes.")


# ============================================================ 7
rule("7. WHAT THIS LAB IS AND IS NOT")
print("  REAL: the S256 transformation (checked against RFC 7636's test vector), HMAC")
print("  token signatures, single-use codes, audience checks, and every count above.")
print("\n  ILLUSTRATIVE: no browser, redirects, TLS or real endpoints; the 'attacker'")
print("  is a scripted sequence; tokens are HMAC-signed JSON, not JWTs with RS256.")
print("\n  NOT SHOWN: refresh-token rotation, Client ID Metadata Document fetching and")
print("  its SSRF risks, and token storage and passthrough (M9-L12).")
print("\nDone.")
