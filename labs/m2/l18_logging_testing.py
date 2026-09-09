"""M2-L18: logging levels, structure, redaction - then a real pytest run.

Requires pytest and pydantic:
    source .venv/bin/activate
    python labs/m2/l18_logging_testing.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
import tempfile
import time
from pathlib import Path

LINE = "-" * 74
logger = logging.getLogger("m2l18")


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
class RedactingFilter(logging.Filter):
    """Strips anything that looks like a credential from every record."""

    PATTERNS = [
        (re.compile(r"sk-[A-Za-z0-9_\-]{4,}"), "sk-***REDACTED***"),
        (re.compile(r"AKIA[0-9A-Z]{6,}"), "AKIA***REDACTED***"),
        (re.compile(r"(?i)(bearer)\s+\S+"), r"\1 ***REDACTED***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)
        record.msg = message
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line, including any `extra` fields."""

    STANDARD = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
        "asctime", "message", "taskName"
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self.STANDARD:
                payload[key] = value
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info).splitlines()[-1]
        return json.dumps(payload)


def levels_demo() -> None:
    section("1. LEVELS - what gets through")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("    %(levelname)-8s %(message)s"))
    logger.handlers = [handler]
    logger.propagate = False

    for level_name in ("WARNING", "DEBUG"):
        logger.setLevel(getattr(logging, level_name))
        print(f"  logger level = {level_name}")
        logger.debug("cache lookup took 2ms")
        logger.info("ticket classified")
        logger.warning("retrying after 429")
        logger.error("classification failed")
        print()

    print("  At WARNING, the debug and info calls produced nothing. The code")
    print("  ran; the records were discarded. That is the control you lose")
    print("  entirely by using print().")


def formatting_cost_demo() -> None:
    section("2. WHY %s AND NOT AN f-STRING")

    class Expensive:
        def __init__(self) -> None:
            self.renders = 0

        def __str__(self) -> str:
            self.renders += 1
            time.sleep(0.0002)          # pretend this is costly to serialise
            return "expensive-value"

    logger.setLevel(logging.WARNING)     # DEBUG is disabled

    lazy = Expensive()
    start = time.perf_counter()
    for _ in range(2000):
        logger.debug("value: %s", lazy)          # deferred
    lazy_ms = (time.perf_counter() - start) * 1000

    eager = Expensive()
    start = time.perf_counter()
    for _ in range(2000):
        logger.debug(f"value: {eager}")          # noqa: G004 - built every time
    eager_ms = (time.perf_counter() - start) * 1000

    print("  2000 logger.debug calls with DEBUG DISABLED:")
    print(f"    logger.debug('value: %s', obj)   {lazy_ms:>8.1f} ms   "
          f"__str__ called {lazy.renders} times")
    print(f"    logger.debug(f'value: {{obj}}')    {eager_ms:>8.1f} ms   "
          f"__str__ called {eager.renders} times")
    print()
    print("  The f-string version formatted every single record that was then")
    print("  thrown away. On a hot path this is real cost - and it can also")
    print("  touch an object you did not intend to serialise.")


def structured_demo() -> None:
    section("3. STRUCTURED LOGGING WITH A CORRELATION ID")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    request_id = "req_7f3c1e"
    print("  One request, four components, one correlation ID:")
    print()
    logger.info("request_received", extra={"request_id": request_id, "route": "/classify"})
    logger.info("retrieval_completed", extra={"request_id": request_id,
                                              "chunks": 5, "duration_ms": 42})
    logger.info("ticket_classified", extra={"request_id": request_id,
                                            "category": "billing", "confidence": 0.92,
                                            "duration_ms": 431, "chars": 128})
    logger.info("response_sent", extra={"request_id": request_id,
                                        "status": 200, "duration_ms": 495})
    print()
    print("  Every line is machine-parseable, and request_id=req_7f3c1e")
    print("  reconstructs the whole request from a stream of thousands.")
    print()
    print("  Note what is NOT there: the ticket text. Only chars=128.")


def redaction_demo() -> None:
    section("4. REDACTION - a backstop, not a substitute for discipline")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("    %(message)s"))
    handler.addFilter(RedactingFilter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    print("  Someone adds a 'helpful' debug line:")
    logger.info("calling provider with key sk-live-abc123XYZ and Bearer tok-9f8e7d")
    logger.info("aws credential AKIAIOSFODNN7EXAMPLE in config")
    print()
    print("  The filter caught all three. But note it is pattern-based: a")
    print("  credential in an unexpected format passes straight through.")
    print("  Redaction reduces damage; it does not remove the need to never")
    print("  log secrets in the first place.")


# ---------------------------------------------------------------------------
TEST_FILE = '''
import logging
import random
import pytest

from chunking import chunk_text, classify, FakeModel, ValidationError


def test_chunk_counts_basic():
    assert len(chunk_text("a" * 25, size=10, overlap=3)) == 4


@pytest.mark.parametrize("size,overlap,expected", [
    (10, 0, 3),
    (10, 3, 4),
    (25, 0, 1),
    (5, 2, 9),
])
def test_chunk_counts_parametrised(size, overlap, expected):
    assert len(chunk_text("a" * 25, size=size, overlap=overlap)) == expected


def test_rejects_overlap_not_less_than_size():
    with pytest.raises(ValueError, match="must be less than"):
        chunk_text("abc", size=10, overlap=10)


def test_empty_input_returns_empty_list():
    assert chunk_text("   ", size=10, overlap=2) == []


@pytest.fixture
def model():
    return FakeModel('{"category":"billing","confidence":0.9,"reason":"refund"}')


def test_classify_returns_validated_result(model):
    result = classify("I want a refund", model=model, request_id="req_1")
    assert result.category in {"billing", "technical", "account", "sales"}
    assert 0.0 <= result.confidence <= 1.0
    assert model.calls == ["I want a refund"]


def test_classify_rejects_invalid_output():
    bad = FakeModel('{"category":"nonsense","confidence":5}')
    with pytest.raises(ValidationError):
        classify("x", model=bad, request_id="req_2")


def test_classify_does_not_log_ticket_text(model, caplog):
    """The privacy property, asserted rather than hoped for."""
    with caplog.at_level(logging.INFO):
        classify("SECRET customer complaint about Jane Doe", model=model,
                 request_id="req_3")
    assert "SECRET" not in caplog.text
    assert "Jane Doe" not in caplog.text


def test_correlation_id_is_recorded(model, caplog):
    """NOTE: caplog.text renders only the MESSAGE, not `extra` fields.

    Asserting `"req_3" in caplog.text` fails even though the field was
    logged. Structured extras live on the record objects, so inspect
    caplog.records instead.
    """
    with caplog.at_level(logging.INFO):
        classify("hello", model=model, request_id="req_3")
    record = next(r for r in caplog.records if r.getMessage() == "ticket_classified")
    assert record.request_id == "req_3"
    assert record.category == "billing"
    assert record.chars == 5
    assert not hasattr(record, "text")        # the ticket body is never attached


def test_that_passes_but_proves_nothing(model):
    """Deliberately weak: asserts only that nothing raised."""
    classify("anything at all", model=model, request_id="req_4")


def test_deliberately_failing():
    """Included so you can read pytest's failure output."""
    assert len(chunk_text("a" * 25, size=10, overlap=3)) == 99
'''

MODULE_FILE = '''
import logging
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger("chunking")


def chunk_text(text, *, size=500, overlap=50, keep_empty=False):
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be less than size ({size})")
    if not text.strip():
        return []
    chunks = []
    step = size - overlap
    for start in range(0, len(text), step):
        piece = text[start:start + size]
        if keep_empty or piece.strip():
            chunks.append(piece)
    logger.info("text_chunked", extra={"chars": len(text), "chunks": len(chunks)})
    return chunks


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["billing", "technical", "account", "sales"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class FakeModel:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def complete(self, text):
        self.calls.append(text)
        return self.response


def classify(text, *, model, request_id):
    started = time.perf_counter()
    try:
        raw = model.complete(text)
        result = Classification.model_validate_json(raw)
    except ValidationError:
        logger.exception("classification_invalid_output",
                         extra={"request_id": request_id, "chars": len(text)})
        raise
    logger.info("ticket_classified", extra={
        "request_id": request_id,
        "category": result.category,
        "confidence": result.confidence,
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "chars": len(text),
    })
    return result
'''


def pytest_demo() -> None:
    section("5. A REAL PYTEST RUN")
    import pytest

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        (tmp / "chunking.py").write_text(MODULE_FILE)
        (tmp / "test_chunking.py").write_text(TEST_FILE)

        logger.handlers = []
        sys.path.insert(0, str(tmp))
        print("  Running: pytest -q (one test fails on purpose)")
        print()
        pytest.main([str(tmp), "-q", "--no-header", "-p", "no:cacheprovider"])
        sys.path.remove(str(tmp))

    print()
    print("  Read the failure block. pytest rewrote the assert to show the")
    print("  ACTUAL value (4) against the expected one (99). You did not have")
    print("  to write assertEqual or a message.")
    print()
    print("  Note three tests in that suite:")
    print("    test_classify_does_not_log_ticket_text - asserts a PRIVACY")
    print("      property. 'We do not log user content' becomes something CI")
    print("      enforces, and it fails the day someone adds a debug line.")
    print("    test_correlation_id_is_recorded - inspects caplog.RECORDS, not")
    print("      caplog.text. caplog.text renders only the message, so an")
    print("      assertion on an `extra` field fails there even though the")
    print("      field WAS logged. A real trap worth meeting once.")
    print("    test_that_passes_but_proves_nothing - passes, asserts nothing,")
    print("      and would still pass if classify() returned garbage.")


def main() -> None:
    print("=" * 74)
    print("LOGGING AND TESTING")
    print("=" * 74)
    levels_demo()
    formatting_cost_demo()
    structured_demo()
    redaction_demo()
    pytest_demo()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
