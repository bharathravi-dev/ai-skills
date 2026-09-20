"""M9-L12 lab -- what happens to credentials after they exist. Measures:

  1. token passthrough vs audience validation + a separate downstream token,
     against a stolen token issued for a different service,
  2. credential leakage through a stdio server's inherited environment,
  3. secrets in logs: a header-only redactor vs structured, key-based logging,
  4. SSRF: validating URLs a server hands to a client during OAuth discovery,
  5. token cache file permissions on this machine.

Every secret in this lab is fake and generated locally.
Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m9/l12_credentials_token_handling.py
"""

from __future__ import annotations

import ipaddress
import json
import os
import random
import re
import socket
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. TOKEN PASSTHROUGH VS AUDIENCE VALIDATION + A DOWNSTREAM TOKEN")

TOKENS = {
    "li's token for the files MCP server": {"sub": "li", "aud": "mcp-files", "iss": "idp"},
    "li's token for the calendar API (stolen)": {"sub": "li", "aud": "calendar-api", "iss": "idp"},
    "attacker's own token for the files MCP server": {"sub": "eve", "aud": "mcp-files", "iss": "idp"},
}
FILES = {"li": ["li-contract.pdf"], "eve": ["eve-notes.txt"]}


def files_api(token: dict, strict_audience: bool) -> tuple[bool, str]:
    """The upstream API. Many internal APIs accept any token from the company IdP."""
    if token["iss"] != "idp" or (strict_audience and token["aud"] != "files-api"):
        return False, "rejected"
    actor = token.get("act", token["sub"])
    return True, f"returned {FILES[token['sub']]} (audit log: caller={actor}, on behalf of {token['sub']})"


def passthrough_server(token: dict):
    """[deliberately wrong] no audience check; forwards the caller's token unchanged."""
    return files_api(token, strict_audience=False)


def correct_server(token: dict):
    if token["aud"] != "mcp-files":
        return False, "rejected by the MCP server (wrong audience)"
    downstream = {"sub": token["sub"], "aud": "files-api", "iss": "idp", "act": "mcp-files"}  # e.g. token exchange
    return files_api(downstream, strict_audience=True)


for label, token in TOKENS.items():
    ok_p, out_p = passthrough_server(token)
    ok_c, out_c = correct_server(token)
    print(f"  {label}")
    print(f"    passthrough server : {out_p}")
    print(f"    correct server     : {out_c}")
print("\n  With passthrough, a token stolen from the CALENDAR API read li's files, and")
print("  the files API's audit log cannot tell the MCP server was involved at all.")


# ============================================================ 2
rule("2. A STDIO SERVER INHERITS ITS HOST'S ENVIRONMENT")

fake_parent_env = dict(os.environ)
fake_parent_env.update({
    "AWS_SECRET_ACCESS_KEY": "fake-aws-secret-0000", "GITHUB_TOKEN": "ghp_fake000000000000000000000000000000",
    "OPENAI_API_KEY": "sk-fake-000", "DATABASE_URL": "postgres://admin:fake@db.internal/prod",
    "CATALOG_READONLY_TOKEN": "fake-readonly-token",
})
probe = ("import os, re; names = sorted(k for k in os.environ if re.search(r'SECRET|TOKEN|KEY|PASSWORD|DATABASE_URL', k)); "
         "print(','.join(names))")
SDK_DEFAULT = ["HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER"]   # mcp 2.2.0 get_default_environment() on POSIX
launches = {
    "subprocess with inherited environment": fake_parent_env,
    "SDK-style allowlist + one explicit credential": {**{k: fake_parent_env[k] for k in SDK_DEFAULT if k in fake_parent_env},
                                                      "CATALOG_READONLY_TOKEN": "fake-readonly-token"},
}
for label, env in launches.items():
    seen = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True).stdout.strip()
    names = [n for n in seen.split(",") if n]
    lab_names = [n for n in names if n in fake_parent_env and fake_parent_env[n].startswith(("fake", "ghp_fake", "sk-fake", "postgres://admin:fake"))]
    print(f"  {label:<46}: server can read {len(lab_names)} planted credential(s): {lab_names}")
print("\n  A local MCP server runs with whatever the launching process hands it. The")
print("  official Python SDK passes only a short allowlist plus the variables you name.")


# ============================================================ 3
rule("3. SECRETS IN LOGS: HEADER REDACTION VS STRUCTURED LOGGING")

rng = random.Random(1212)


def fake_jwt() -> str:
    part = lambda n: "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(n))
    return f"eyJ{part(20)}.eyJ{part(40)}.{part(43)}"


TEMPLATES = [
    ("header", lambda t: f"POST /mcp headers={{'Authorization': 'Bearer {t}', 'Mcp-Method': 'tools/call'}}"),
    ("query", lambda t: f"GET /callback?code=abc&access_token={t}&state=xyz"),
    ("json body", lambda t: f'token response {{"access_token": "{t}", "refresh_token": "rt_{t[-20:]}"}}'),
    ("exception", lambda t: f"ValueError: signature verification failed for {t}"),
    ("tool args", lambda t: f"tools/call args={{'query': 'q3 report', 'api_key': 'sk-live-{t[-24:]}'}}"),
    ("cookie", lambda t: f"Set-Cookie: session={t}; HttpOnly; Secure"),
]
BENIGN = [lambda: f"request_id=req_{rng.getrandbits(64):016x} commit={rng.getrandbits(160):040x} took 42ms",
          lambda: "tools/list returned 12 tools in 3ms"]

lines, secrets = [], []
for i in range(300):
    if i % 5 == 4:
        lines.append(("benign", BENIGN[i % 2]()))
    else:
        kind, make = TEMPLATES[i % len(TEMPLATES)]
        tok = fake_jwt()
        lines.append((kind, make(tok)))
        secrets.append(tok)


def header_only(line: str) -> str:
    return re.sub(r"(Bearer\s+)[A-Za-z0-9._\-]+", r"\1[REDACTED]", line)


def pattern_based(line: str) -> str:
    line = re.sub(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "[JWT]", line)
    line = re.sub(r"((?:access_token|refresh_token|api_key|session|code)[\"']?\s*[:=]\s*[\"']?)[^\"'&;,\s}]+", r"\1[REDACTED]", line)
    return line


def leaks(redact) -> tuple[int, int, int]:
    leaked_lines, fragments, benign_damaged = 0, 0, 0
    for kind, line in lines:
        out = redact(line)
        if kind == "benign":
            benign_damaged += out != line
            continue
        found = [s for s in secrets if s in out or s[-20:] in out or s[-24:] in out]
        leaked_lines += bool(found)
    return leaked_lines, sum(1 for k, _ in lines if k != "benign"), benign_damaged


for name, fn in (("no redaction", lambda s: s), ("header-only redactor", header_only), ("pattern-based redactor", pattern_based)):
    leaked, total, damaged = leaks(fn)
    print(f"  {name:<24}: {leaked:>3}/{total} secret-bearing lines still leak; benign lines altered: {damaged}")


print("\n  The pattern-based redactor was written while looking at these six formats.")
print("  Held-out formats it has never seen:")
held_out = []
for i in range(40):
    opaque = "".join(rng.choice("0123456789abcdef") for _ in range(40))
    held_out.append((opaque, f"upstream call headers={{'X-Api-Key': '{opaque}'}}") if i % 2 == 0 else
                    (opaque[:16], f"connecting to https://svc:{opaque[:16]}@db.internal:5432/prod"))
still = sum(secret in pattern_based(line) for secret, line in held_out)
print(f"  pattern-based redactor on 40 held-out lines: {still}/40 still leak")


def structured_log(event: str, **fields) -> str:
    allowed = {"method", "tool", "request_id", "status", "duration_ms", "principal"}
    return json.dumps({"event": event, **{k: v for k, v in fields.items() if k in allowed}})


print(f"\n  structured logging with an allowlist of fields, same request:")
print(f"    {structured_log('tools/call', method='tools/call', tool='search', request_id='req_1', status=200, duration_ms=42, principal='li', authorization='Bearer ' + secrets[0], arguments={'api_key': 'sk-live-x'})}")
print("  Redaction chases formats; an allowlist never writes the secret in the first place.")


# ============================================================ 4
rule("4. SSRF: URLS A SERVER GIVES A CLIENT DURING DISCOVERY")

CANDIDATES = [
    "https://auth.example.com/.well-known/oauth-authorization-server",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://[::ffff:169.254.169.254]/latest/meta-data/",
    "http://0xA9FEA9FE/latest/meta-data/",
    "http://2852039166/latest/meta-data/",
    "http://0251.0376.0251.0376/latest/meta-data/",
    "http://127.1:6379/",
    "http://[::1]:8080/admin",
    "https://auth.example.com@169.254.169.254/",
    "https://10.20.30.40/.well-known/openid-configuration",
    "https://metadata.internal.example/token",
]


def naive_check(url: str) -> bool:
    host = url.split("/")[2].split(":")[0]
    blocked = ("localhost", "127.0.0.1", "169.254.169.254", "10.", "192.168.", "[::1]")
    return url.startswith("https://") or not host.startswith(blocked)


def careful_check(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https":
        return "block (not https)"
    host = parts.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            ip = ipaddress.ip_address(socket.inet_aton(host))   # legacy forms: 127.1, 0x..., octal, integer
        except OSError:
            return "needs DNS: resolve once, re-check, pin"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return f"block ({ip})"
    return "allow"


def careful_scheme_blind(url: str) -> str:
    return careful_check(url.replace("http://", "https://", 1))


naive_allowed_internal, careful_allowed_internal = 0, 0
for url in CANDIDATES:
    naive = "allow" if naive_check(url) else "block"
    careful = careful_scheme_blind(url)
    internal = careful.startswith("block")
    naive_allowed_internal += internal and naive == "allow"
    careful_allowed_internal += careful == "allow" and internal
    print(f"  {url[:58]:<58} naive: {naive:<5}  careful: {careful}")
print(f"\n  internal destinations the naive check let through: {naive_allowed_internal}")
print("  (the careful column ignores the http/https difference so it is judged on the")
print("  address alone; in production also require https and use an egress proxy)")


# ============================================================ 5
rule("5. TOKEN CACHE FILE PERMISSIONS ON THIS MACHINE")

old_umask = os.umask(0o022)                     # a common default, set explicitly for repeatability
try:
    with tempfile.TemporaryDirectory() as tmp:
        naive_path, safe_path = os.path.join(tmp, "tokens_naive.json"), os.path.join(tmp, "tokens_safe.json")
        with open(naive_path, "w") as fh:
            json.dump({"refresh_token": "rt_fake"}, fh)
        fd = os.open(safe_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump({"refresh_token": "rt_fake"}, fh)
        for label, path in (("open(path, 'w')", naive_path), ("os.open(..., 0o600)", safe_path)):
            mode = stat.S_IMODE(os.stat(path).st_mode)
            print(f"  {label:<22} -> mode {oct(mode)}  readable by other local users: {bool(mode & stat.S_IROTH)}")
finally:
    os.umask(old_umask)
print("\n  Prefer the OS credential store (Keychain, Credential Manager, Secret Service)")
print("  where available; if a file is unavoidable, create it 0600 from the start.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: the child-process environment probe, the file modes, the redaction")
print("  counts over 300 generated lines, and the address classification (using the")
print("  standard library's ipaddress and inet_aton parsers).")
print("\n  ILLUSTRATIVE: section 1's tokens are dicts, not signed tokens; the log corpus")
print("  is synthetic; no DNS lookups are made, so hostnames are reported as needing one.")
print("\n  NOT SHOWN: token exchange (RFC 8693) wire details, OS keychain APIs, and egress")
print("  proxy configuration.")
print("\nDone.")
