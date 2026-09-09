"""M2-L10: tracebacks, handling strategies, chaining, and the finally trap.

    python3 labs/m2/l10_exceptions.py

Standard library only.
"""

from __future__ import annotations

import json
import logging
import tempfile
import traceback
from pathlib import Path

LINE = "-" * 74
logging.basicConfig(level=logging.INFO, format="    [%(levelname)s] %(message)s")
logger = logging.getLogger("m2l10")


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
# 1. A real, multi-frame traceback
# ---------------------------------------------------------------------------
def read_rows() -> list[dict]:
    return [{"priority": "2"}, {"priority": "high"}]


def load_rows() -> list[int]:
    return [int(r["priority"]) for r in read_rows()]


def build_report() -> str:
    rows = load_rows()
    return f"{len(rows)} rows"


def traceback_demo() -> None:
    section("1. READING A TRACEBACK - bottom up")
    try:
        build_report()
    except ValueError:
        print(traceback.format_exc().rstrip())
    print()
    print("  Read it BOTTOM UP:")
    print("    last line     -> ValueError, and the bad value: 'high'")
    print("    frame above   -> load_rows(), the int() call. LOOK HERE FIRST.")
    print("    frames above  -> how you got there: build_report -> load_rows")
    print("    the ^^^^ marks the exact sub-expression that failed")


# ---------------------------------------------------------------------------
# 2. Three versions of the same loader
# ---------------------------------------------------------------------------
class ConfigError(Exception):
    """Configuration could not be loaded."""


def load_v1(path: Path) -> dict:
    """No handling: library errors leak out with no context."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_v2(path: Path) -> dict:
    """Over-caught: every failure becomes an empty dict. WORSE than v1."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_v3(path: Path) -> dict:
    """Correct: specific handlers, actionable messages, chained causes."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(
            f"Config file not found: {path.name}. "
            f"Copy config.example.json to {path.name}."
        ) from exc
    except PermissionError as exc:
        raise ConfigError(f"Cannot read {path.name}: permission denied.") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path.name} is not valid UTF-8 text.") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{path.name} is not valid JSON: {exc.msg} "
            f"at line {exc.lineno}, column {exc.colno}"
        ) from exc


def loader_demo(tmp: Path) -> None:
    section("2. THREE LOADERS, THREE OUTCOMES")
    good = tmp / "good.json"
    good.write_text('{"model": "claude-sonnet-5"}', encoding="utf-8")
    broken = tmp / "broken.json"
    broken.write_text('{"model": "claude"\n  "bad": true}', encoding="utf-8")
    missing = tmp / "missing.json"

    for label, path in (("valid file", good), ("malformed JSON", broken),
                        ("missing file", missing)):
        print(f"  {label}")
        for name, fn in (("v1 no handling", load_v1),
                         ("v2 catch-all  ", load_v2),
                         ("v3 correct    ", load_v3)):
            try:
                result = fn(path)
                print(f"    {name}: returned {result!r}")
            except ConfigError as exc:
                print(f"    {name}: ConfigError: {exc}")
            except Exception as exc:
                print(f"    {name}: {type(exc).__name__}: "
                      f"{str(exc)[:60]}")
        print()

    print("  Look at the 'missing file' block. v2 returned {} - exactly what")
    print("  it returns for a VALID but empty config. The application starts")
    print("  with silent defaults and misbehaves later, and nobody connects")
    print("  the symptom to a missing file. v2 is worse than no handling.")


# ---------------------------------------------------------------------------
# 3. Chaining
# ---------------------------------------------------------------------------
def chaining_demo(tmp: Path) -> None:
    section("3. raise X from exc  vs  plain raise X")
    broken = tmp / "broken.json"

    print("  WITH 'from exc':")
    try:
        load_v3(broken)
    except ConfigError as exc:
        print(f"    __cause__   = {type(exc.__cause__).__name__}")
        print(f"    __context__ = {type(exc.__context__).__name__}")
        tb = traceback.format_exc().rstrip().splitlines()
        for line in tb:
            if "direct cause" in line or line.startswith(("json.decoder", "ConfigError")):
                print(f"    {line}")

    print()
    print("  WITHOUT 'from' (plain raise):")
    try:
        try:
            json.loads("{bad")
        except json.JSONDecodeError:
            raise ConfigError("config is invalid")
    except ConfigError as exc:
        print(f"    __cause__   = {exc.__cause__}")
        print(f"    __context__ = {type(exc.__context__).__name__}")
        tb = traceback.format_exc().rstrip().splitlines()
        for line in tb:
            if "another exception occurred" in line:
                print(f"    {line}")
    print()
    print("  Both keep the original visible, but 'from' says DELIBERATE")
    print("  TRANSLATION ('direct cause'), while plain raise reads as an")
    print("  accident ('during handling ... another exception occurred').")


# ---------------------------------------------------------------------------
# 4. Custom exceptions with structured data
# ---------------------------------------------------------------------------
class IngestionError(Exception):
    """Base for all ingestion failures."""


class ChunkTooLargeError(IngestionError):
    def __init__(self, doc_id: str, size: int, limit: int) -> None:
        super().__init__(f"chunk from {doc_id} is {size} tokens, limit is {limit}")
        self.doc_id = doc_id
        self.size = size
        self.limit = limit


def custom_demo() -> None:
    section("4. CUSTOM EXCEPTIONS CARRY DATA, NOT JUST TEXT")
    try:
        raise ChunkTooLargeError("policy-2026.pdf", size=1800, limit=1024)
    except IngestionError as exc:                      # caught by the BASE class
        print(f"    message : {exc}")
        if isinstance(exc, ChunkTooLargeError):
            print(f"    doc_id  : {exc.doc_id}")
            print(f"    size    : {exc.size}")
            print(f"    limit   : {exc.limit}")
            suggested = exc.limit // 2
            print(f"    -> the handler can ACT: retry {exc.doc_id} with "
                  f"chunk size {suggested}")
    print()
    print("  Catching the base class (IngestionError) picks up every failure")
    print("  from this subsystem without catching unrelated ones. The")
    print("  attributes let the handler decide, instead of parsing English.")


# ---------------------------------------------------------------------------
# 5. try/except/else/finally order, and the finally trap
# ---------------------------------------------------------------------------
def four_blocks(fail: bool) -> str:
    order: list[str] = []
    try:
        order.append("try")
        if fail:
            raise ValueError("boom")
        order.append("try-end")
    except ValueError:
        order.append("except")
    else:
        order.append("else")
    finally:
        order.append("finally")
    return " -> ".join(order)


def swallows_exception() -> str:
    try:
        raise ValueError("this exception vanishes")
    finally:
        return "from finally"      # noqa: B012 - deliberately wrong


def flow_demo() -> None:
    section("5. try / except / else / finally")
    print(f"  success path : {four_blocks(fail=False)}")
    print(f"  failure path : {four_blocks(fail=True)}")
    print()
    print("  'else' runs only on success AND is not protected by the")
    print("  handlers - so an error in your success path is not caught by a")
    print("  handler meant for the risky call.")
    print()
    print("  THE finally TRAP:")
    result = swallows_exception()
    print(f"    a function that raises ValueError returned: {result!r}")
    print("    The exception was DESTROYED by 'return' inside finally.")
    print("    No traceback. No log. The caller sees a normal return value.")
    print("    Never put return (or break/continue) inside finally.")


# ---------------------------------------------------------------------------
# 6. Empty vs failed
# ---------------------------------------------------------------------------
class RetrievalError(Exception):
    """The retrieval backend could not be reached."""


def retrieve_bad(query: str, *, backend_up: bool) -> list[str]:
    try:
        if not backend_up:
            raise ConnectionError("vector store unreachable")
        return [] if query == "unknown topic" else ["chunk-1"]
    except Exception:
        return []                     # collapses two very different outcomes


def retrieve_good(query: str, *, backend_up: bool) -> list[str]:
    try:
        if not backend_up:
            raise ConnectionError("vector store unreachable")
    except ConnectionError as exc:
        raise RetrievalError(f"retrieval failed for {query!r}") from exc
    return [] if query == "unknown topic" else ["chunk-1"]


def empty_vs_failed() -> None:
    section("6. 'NO RESULTS' MUST NOT LOOK LIKE 'IT BROKE'")
    cases = [("refund policy", True), ("unknown topic", True), ("refund policy", False)]
    print(f"  {'query':<18}{'backend':<10}{'bad version':<16}good version")
    for query, up in cases:
        bad = repr(retrieve_bad(query, backend_up=up))
        try:
            good = repr(retrieve_good(query, backend_up=up))
        except RetrievalError as exc:
            good = f"raises {type(exc).__name__}"
        print(f"  {query:<18}{str(up):<10}{bad:<16}{good}")
    print()
    print("  In the bad version, rows 2 and 3 are IDENTICAL: []. One means")
    print("  'we have nothing on that topic', the other means 'the database")
    print("  is down'. The assistant says 'I could not find anything' in")
    print("  both cases, users believe it, and the outage is invisible")
    print("  until someone checks a dashboard. (M7-L13, M7-L20.)")


def main() -> None:
    print("=" * 74)
    print("EXCEPTIONS, TRACEBACKS AND DEBUGGING")
    print("=" * 74)
    traceback_demo()
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        loader_demo(tmp)
        chaining_demo(tmp)
    custom_demo()
    flow_demo()
    empty_vs_failed()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
