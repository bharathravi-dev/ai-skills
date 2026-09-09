"""M2-L19: how secrets leak, and the control for each.

    python3 labs/m2/l19_secrets.py

Standard library only. Every key here is obviously fake.
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

LINE = "-" * 74
FAKE_KEY = "sk-live-FAKE-4b8c1e77d2a9f30e"      # not a real credential


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LeakySettings:
    """The default. Every field appears in __repr__."""

    api_key: str
    model: str


@dataclass(frozen=True)
class SafeSettings:
    """repr=False keeps the key out of every automatic string conversion."""

    api_key: str = field(repr=False)
    model: str = "claude-sonnet-5"

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("api_key must not be empty")


def mask(secret: str, *, keep: int = 4) -> str:
    """Show only the last few characters: enough to identify, not to use."""
    if not secret:
        return "(empty)"
    if len(secret) <= keep:
        return "*" * len(secret)
    return f"{'*' * (len(secret) - keep)}{secret[-keep:]}"


SENSITIVE_NAMES = ("authorization", "cookie", "x-api-key", "proxy-authorization")


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, value in headers.items():
        lowered = name.lower()
        if lowered in SENSITIVE_NAMES or any(
            token in lowered for token in ("key", "token", "secret", "password")
        ):
            out[name] = "***REDACTED***"
        else:
            out[name] = value
    return out


def repr_demo() -> None:
    section("1. THE DATACLASS __repr__ LEAK")
    leaky = LeakySettings(api_key=FAKE_KEY, model="claude-sonnet-5")
    safe = SafeSettings(api_key=FAKE_KEY)

    print("  @dataclass with no repr control:")
    print(f"    print(settings)      -> {leaky}")
    print(f"    f-string in a log    -> {f'settings: {leaky}'[:72]}...")
    print()
    print("  @dataclass with field(repr=False) on api_key:")
    print(f"    print(settings)      -> {safe}")
    print()
    print("  Same object, same key, one keyword different. The first version")
    print("  emits your credential from any print, log, f-string, traceback")
    print("  or debugger inspection. This is the M2-L07 warning made concrete.")
    print()
    print(f"  When you must identify a key: mask() -> {mask(FAKE_KEY)}")
    print(f"  short value                          -> {mask('abc')}")
    print(f"  empty value                          -> {mask('')}")


def leak_routes_demo() -> None:
    section("2. FIVE LEAK ROUTES, AND THE CONTROL FOR EACH")

    print("  ROUTE 1 - interpolated into an exception message")
    try:
        raise RuntimeError(f"auth failed with key {FAKE_KEY}")
    except RuntimeError as exc:
        print(f"    BAD : {exc}")
    try:
        raise RuntimeError(f"auth failed (key {mask(FAKE_KEY)}, request req_7f3c)")
    except RuntimeError as exc:
        print(f"    GOOD: {exc}")

    print()
    print("  ROUTE 2 - a query parameter")
    print(f"    BAD : GET /v1/messages?api_key={FAKE_KEY}")
    print("          -> written to proxy logs, server access logs, browser history")
    print("    GOOD: GET /v1/messages")
    print("          Authorization: Bearer <key>   (headers are not logged by default)")

    print()
    print("  ROUTE 3 - logging the header dict")
    headers = {
        "Authorization": f"Bearer {FAKE_KEY}",
        "X-Api-Key": FAKE_KEY,
        "Content-Type": "application/json",
        "User-Agent": "course/1.0",
    }
    print(f"    BAD : {headers}"[:76] + "...")
    print(f"    GOOD: {redact_headers(headers)}")

    print()
    print("  ROUTE 4 - a returned error message")
    print("    BAD : 500 {\"error\": \"connection to db://user:hunter2@host failed\"}")
    print("    GOOD: 500 {\"error\": \"internal error\", \"request_id\": \"req_7f3c\"}")
    print("          (full detail logged server-side against that request_id)")

    print()
    print("  ROUTE 5 - a container image layer")
    print("    BAD : RUN echo \"KEY=sk-live-...\" > .env && rm .env")
    print("          -> the file is in the layer FOREVER, even though it was")
    print("             deleted in the same command. Layers are immutable and")
    print("             anyone who can pull the image can extract it (M2-L20).")
    print("    GOOD: pass the value at RUNTIME via the environment, or use")
    print("          BuildKit build secrets which are never written to a layer.")


def loading_demo() -> None:
    section("3. LOADING - fail fast, with an actionable message")

    def load_settings() -> SafeSettings:
        api_key = os.getenv("DEMO_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "DEMO_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return SafeSettings(api_key=api_key)

    print(f"  {'environment':<34}{'result'}")
    for label, value in (
        ("unset", None),
        ("empty string", ""),
        ("whitespace only", "   "),
        ("newline from a copy-paste", f"{FAKE_KEY}\n"),
        ("valid", FAKE_KEY),
    ):
        if value is None:
            os.environ.pop("DEMO_API_KEY", None)
        else:
            os.environ["DEMO_API_KEY"] = value
        try:
            settings = load_settings()
            print(f"  {label:<34}ok -> key ending {mask(settings.api_key)[-6:]}")
        except RuntimeError as exc:
            print(f"  {label:<34}RuntimeError: {str(exc)[:34]}...")
    os.environ.pop("DEMO_API_KEY", None)

    print()
    print("  Note the whitespace and newline rows. A key copied from a browser")
    print("  often carries a trailing newline; .strip() turns a baffling 401")
    print("  into either a correct load or a clear startup error.")


SCANNER_PATTERNS = [
    ("anthropic-style", re.compile(r"sk-[A-Za-z0-9_\-]{8,}")),
    ("aws access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password assignment", re.compile(r"(?i)password\s*=\s*['\"][^'\"]{4,}['\"]")),
    ("connection string", re.compile(r"[a-z]+://[^:\s]+:[^@\s]+@")),
]

SAMPLE_FILE = '''
import os

# Three real-looking credentials (all fake) and two lookalikes.
API_KEY = "sk-live-FAKE-4b8c1e77d2a9f30e"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
DB_URL = "postgresql://appuser:hunter2@db.internal:5432/app"
password = "correct-horse-battery"

# Lookalikes that are NOT secrets:
SKU_CODE = "sk-2024-winter-catalogue"
EXAMPLE_URL = "https://docs.example.com/auth"
API_KEY_FROM_ENV = os.getenv("ANTHROPIC_API_KEY")
'''


def scanner_demo() -> None:
    section("4. SECRET SCANNING - and its false-positive trade-off")
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "config.py"
        path.write_text(SAMPLE_FILE)

        findings: list[tuple[int, str, str]] = []
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            for label, pattern in SCANNER_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append((number, label, match.group(0)[:38]))

        print(f"  Scanned {path.name} ({len(SAMPLE_FILE.splitlines())} lines)")
        print()
        print(f"  {'line':>5}  {'pattern':<22}match")
        for number, label, text in findings:
            print(f"  {number:>5}  {label:<22}{mask(text, keep=6)}")

        print()
        print(f"  {len(findings)} findings.")
        print()
        print("  Now the honest part. Line 11 is 'sk-2024-winter-catalogue' -")
        print("  a product code, not a key, and the scanner flagged it. Loosen")
        print("  the pattern and you catch more real secrets and more noise;")
        print("  tighten it and you miss credentials in unexpected formats.")
        print()
        print("  A noisy scanner gets disabled, which is worse than a strict")
        print("  one. Tune it, add an allow-list for known false positives,")
        print("  and treat it as ONE layer alongside a pre-commit hook, CI")
        print("  scanning and platform push protection.")


def response_demo() -> None:
    section("5. THE LEAK RESPONSE - order matters")
    steps = [
        ("1. ROTATE and REVOKE", "minutes",
         "Issue a new secret, update consumers, REVOKE the old one. "
         "Revocation is the step people skip."),
        ("2. Assess exposure", "minutes",
         "Where did it appear, for how long, who could read it? "
         "Public repo = assume scraped within minutes."),
        ("3. Check for misuse", "hours",
         "Provider usage logs, billing anomalies, unfamiliar source IPs."),
        ("4. Clean up", "days",
         "Rewrite history, purge logs. This is CLEANUP, not remediation."),
        ("5. Fix the cause", "days",
         "Pre-commit hook, CI scan, changed process. A leak that can "
         "recur, will."),
    ]
    for step, when, why in steps:
        print(f"  {step:<24}({when})")
        for chunk in textwrap.wrap(why, width=62):
            print(f"      {chunk}")
    print()
    print("  Every minute spent on step 4 before step 1 is a minute the live")
    print("  credential still works. You cannot prove nobody copied it, so")
    print("  the only safe assumption is that somebody did.")


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    print("=" * 74)
    print("SECRET HANDLING")
    print("=" * 74)
    print("All credentials shown below are fake and non-functional.")
    repr_demo()
    leak_routes_demo()
    loading_demo()
    scanner_demo()
    response_demo()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
