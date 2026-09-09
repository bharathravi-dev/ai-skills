"""M2-L09: files, CSV, JSON, env vars - and the traps in each.

Requires pydantic:
    source .venv/bin/activate
    python labs/m2/l09_files.py

Writes only into a temporary directory; your repository is untouched.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

LINE = "-" * 74
HERE = Path(__file__).resolve().parent      # anchored to THIS FILE, not the CWD


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
class Ticket(BaseModel):
    ticket_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    priority: int = Field(ge=1, le=5)
    channel: str = Field(min_length=1)


# Synthetic rows. Three are deliberately broken, plus two awkward-but-legal
# fields (an embedded comma and an embedded newline) to prove the csv module
# handles what naive string joining cannot.
CSV_ROWS = [
    ["ticket_id", "text", "priority", "channel"],
    ["T-001", "Refund not received", "2", "email"],
    ["T-002", "Cannot log in", "1", "chat"],
    ["T-003", "Charged twice, need help", "9", "email"],        # priority out of range
    ["T-004", "", "3", "email"],                                # blank text
    ["T-005", "Invoice query", "high", "phone"],                # priority not an int
    ["T-006", "Order 12, item 3, wrong colour", "4", "email"],  # commas in the field
    ["T-007", "Line one\nLine two", "5", "chat"],               # newline in the field
]


def paths_demo() -> None:
    section("1. PATHS - anchored to the file, not the working directory")
    print(f"  Path.cwd()                     : {Path.cwd()}")
    print(f"  Path(__file__).resolve().parent: {HERE}")
    print()
    print("  These are different right now, and they are different again when")
    print("  the script runs under cron, in a container, or from pytest.")
    print("  For files shipped WITH your code, always use the second one.")
    print()
    p = HERE / "data" / "tickets.csv"
    print(f"  HERE / 'data' / 'tickets.csv'  : ...{str(p)[-40:]}")
    print(f"    .name   = {p.name}")
    print(f"    .stem   = {p.stem}")
    print(f"    .suffix = {p.suffix}")
    print(f"    .parent = ...{str(p.parent)[-20:]}")


def load(csv_path: Path) -> tuple[list[Ticket], list[dict]]:
    """Validate every row; collect failures rather than aborting."""
    valid: list[Ticket] = []
    failures: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        # start=2 because the header occupies line 1, so numbers match a
        # spreadsheet and the user can find the row.
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                valid.append(Ticket.model_validate(row))
            except ValidationError as exc:
                failures.append({
                    "line": line_no,
                    "errors": [
                        {"field": ".".join(str(p) for p in e["loc"]),
                         "msg": e["msg"],
                         "got": e.get("input")}
                        for e in exc.errors()
                    ],
                })
    return valid, failures


def csv_demo(tmp: Path) -> tuple[list[Ticket], Path]:
    section("2. CSV - every value is a string, and quoting matters")
    csv_path = tmp / "tickets.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(CSV_ROWS)

    print(f"  Wrote {len(CSV_ROWS) - 1} rows.")
    print()
    print("  Raw file bytes for the two awkward rows:")
    raw = csv_path.read_text(encoding="utf-8").splitlines()
    for line in raw[-3:]:
        print(f"    {line!r}")
    print("    ^ the csv module quoted the comma and the newline for us.")
    print()

    valid, failures = load(csv_path)
    print(f"  Loaded {len(valid)} valid tickets, {len(failures)} rejected.")
    for failure in failures:
        for err in failure["errors"]:
            print(f"    line {failure['line']}: {err['field']} - {err['msg']} "
                  f"(got {err['got']!r})")
    print()
    print("  Every message names the line, the field and the value. A user")
    print("  can fix their spreadsheet from that. Compare with the bare")
    print("  'ValueError: invalid literal for int()' a naive loader gives.")
    print()
    print("  Note priority came in as the STRING '2' and is now:")
    print(f"    {valid[0].priority!r} ({type(valid[0].priority).__name__}) "
          f"- Pydantic did the conversion")
    return valid, csv_path


def jsonl_demo(tmp: Path, tickets: list[Ticket]) -> None:
    section("3. JSONL - one object per line, for datasets and traces")
    out = tmp / "out" / "tickets.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)     # idempotent
    with open(out, "w", encoding="utf-8") as f:
        for t in tickets:
            f.write(t.model_dump_json() + "\n")

    print(f"  Wrote {len(tickets)} lines to {out.name}")
    print("  First line:")
    print(f"    {out.read_text(encoding='utf-8').splitlines()[0]}")

    reloaded = [Ticket.model_validate_json(line)
                for line in out.read_text(encoding="utf-8").splitlines()]
    print(f"  Read back {len(reloaded)} tickets. Round trip intact: "
          f"{reloaded == tickets}")


def json_types() -> None:
    section("4. JSON - which Python types survive the round trip")
    original = {
        "string": "hello",
        "int": 5,
        "float": 1.5,
        "bool": True,
        "none": None,
        "list": [1, 2],
        "tuple": (1, 2),
        "nested": {"a": 1},
    }
    restored = json.loads(json.dumps(original))

    print(f"  {'key':<10}{'before':<18}{'after':<18}same type?")
    for key in original:
        before = type(original[key]).__name__
        after = type(restored[key]).__name__
        flag = "" if before == after else "   <-- CHANGED"
        print(f"  {key:<10}{before:<18}{after:<18}{before == after}{flag}")

    print()
    print("  Integer keys become strings, silently:")
    print(f"    json.loads(json.dumps({{1: 'a'}})) -> {json.loads(json.dumps({1: 'a'}))}")
    print()
    print("  And these raise outright:")
    for value in ({"s": {1, 2}}, {"d": datetime(2026, 1, 1)}, {"m": Decimal("1.5")}):
        name = type(list(value.values())[0]).__name__
        try:
            json.dumps(value)
        except TypeError as exc:
            print(f"    {name:<10} TypeError: {exc}")
    print()
    print("  default=str handles them - but converts EVERYTHING unknown, so")
    print("  use it deliberately rather than as a reflex:")
    print(f"    {json.dumps({'d': datetime(2026, 1, 1)}, default=str)}")


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    max_tokens: int
    debug: bool


def parse_bool(raw: str | None) -> bool:
    """The correct way. bool('false') is True, which is almost never wanted."""
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def env_demo() -> None:
    section("5. ENVIRONMENT VARIABLES - always strings")
    os.environ["DEMO_MAX_TOKENS"] = "2048"
    os.environ["DEMO_DEBUG"] = "false"

    raw = os.getenv("DEMO_MAX_TOKENS")
    print(f"  os.getenv('DEMO_MAX_TOKENS') = {raw!r} ({type(raw).__name__})")
    print(f"  int(raw)                     = {int(raw or 0)}")
    print()
    print("  THE BOOLEAN TRAP - DEMO_DEBUG is the string 'false':")
    print(f"    bool(os.getenv('DEMO_DEBUG'))  = {bool(os.getenv('DEMO_DEBUG'))}   <-- WRONG")
    print(f"    parse_bool(os.getenv(...))     = {parse_bool(os.getenv('DEMO_DEBUG'))}   <-- correct")
    print()
    print(f"  {'input':<12}{'bool()':<10}parse_bool()")
    for value in ("true", "false", "1", "0", "yes", "", "no"):
        print(f"  {value!r:<12}{str(bool(value)):<10}{parse_bool(value)}")
    print()

    print("  Required values must fail AT STARTUP, not on first use:")
    try:
        key = os.getenv("DEMO_MISSING_KEY", "")
        if not key:
            raise RuntimeError(
                "DEMO_MISSING_KEY is not set. Copy .env.example to .env and fill it in."
            )
    except RuntimeError as exc:
        print(f"    RuntimeError: {exc}")

    settings = Settings(
        api_key="sk-fake-not-a-real-key",
        model=os.getenv("DEMO_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.getenv("DEMO_MAX_TOKENS", "1024")),
        debug=parse_bool(os.getenv("DEMO_DEBUG")),
    )
    print(f"    loaded once into a frozen dataclass: model={settings.model!r} "
          f"max_tokens={settings.max_tokens} debug={settings.debug}")

    for key in ("DEMO_MAX_TOKENS", "DEMO_DEBUG"):
        os.environ.pop(key, None)


def safe_join(base: Path, user_path: str) -> Path:
    """Reject any path that escapes `base`."""
    base = base.resolve()
    target = (base / user_path).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"path escapes the base directory: {user_path!r}")
    return target


def traversal_demo(tmp: Path) -> None:
    section("6. PATH TRAVERSAL - never trust a user-supplied filename")
    base = tmp / "uploads"
    base.mkdir(exist_ok=True)
    for candidate in ("reports/q1.csv", "../../etc/passwd", "/etc/passwd", "ok.txt"):
        try:
            resolved = safe_join(base, candidate)
            print(f"  {candidate!r:<22} ALLOWED -> ...{str(resolved)[-30:]}")
        except ValueError as exc:
            print(f"  {candidate!r:<22} BLOCKED  ({exc})")
    print()
    print("  Note '/etc/passwd' is blocked too: an ABSOLUTE path given to")
    print("  Path.__truediv__ discards the base entirely. Checking for '..'")
    print("  alone would have missed it.")


def streaming_demo(tmp: Path) -> None:
    section("7. STREAMING vs READING A WHOLE FILE")
    big = tmp / "big.jsonl"
    with open(big, "w", encoding="utf-8") as f:
        for i in range(200_000):
            f.write(json.dumps({"i": i, "text": "x" * 60}) + "\n")
    size_mb = big.stat().st_size / 1_000_000
    print(f"  Generated {big.name}: {size_mb:.1f} MB, 200,000 lines")
    print()

    tracemalloc.start()
    lines = big.read_text(encoding="utf-8").splitlines()
    count_full = len(lines)
    _, peak_full = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del lines

    tracemalloc.start()
    count_stream = 0
    with open(big, encoding="utf-8") as f:
        for _ in f:
            count_stream += 1
    _, peak_stream = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  full read  : {count_full:,} lines, peak {peak_full / 1_000_000:>8.1f} MB")
    print(f"  streaming  : {count_stream:,} lines, peak {peak_stream / 1_000_000:>8.1f} MB")
    print(f"  ratio      : {peak_full / max(peak_stream, 1):,.0f}x less memory")
    print()
    print("  This file is small. Scale it to a 2 GB corpus in a 512 MB")
    print("  container and the full read is an OOM kill, not a slow function.")


def main() -> None:
    print("=" * 74)
    print("FILES, CSV, JSON AND ENVIRONMENT VARIABLES")
    print("=" * 74)
    paths_demo()
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        tickets, _ = csv_demo(tmp)
        jsonl_demo(tmp, tickets)
        json_types()
        env_demo()
        traversal_demo(tmp)
        streaming_demo(tmp)
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
