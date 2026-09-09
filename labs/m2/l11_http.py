"""M2-L11: a real HTTP server and client, no network or API key needed.

    python3 labs/m2/l11_http.py

Starts a local server on a random port that returns 200, 401, 403, 429 with
Retry-After, 500, a 200-with-error-in-body, and an SSE stream. The client then
calls each and classifies the result.

Standard library only.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LINE = "-" * 74

# The rule from section 6 of the lesson.
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504, 529}

# Headers whose values must never reach a log.
SENSITIVE = ("authorization", "cookie", "x-api-key")

# Idempotency store: key -> the result we already produced for it.
_IDEMPOTENCY: dict[str, str] = {}
_ORDER_COUNT = {"n": 0}


def is_retryable(status: int | None) -> bool:
    """None means a connection error: no response was received at all."""
    if status is None:
        return True
    return status in RETRYABLE_STATUS


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return a copy safe to log."""
    out = {}
    for name, value in headers.items():
        lowered = name.lower()
        if lowered in SENSITIVE or any(
            token in lowered for token in ("key", "token", "secret")
        ):
            out[name] = "***REDACTED***"
        else:
            out[name] = value
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args) -> None:      # silence per-request logging
        pass

    def _send(self, status: int, payload: dict, extra: dict[str, str] | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("request-id", f"req_{status}_{int(time.time() * 1000) % 100000}")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:                  # noqa: N802
        route = self.path

        if route == "/ok":
            self._send(200, {"result": "hello"},
                       {"anthropic-ratelimit-requests-remaining": "49"})

        elif route == "/unauthenticated":
            self._send(401, {"error": {"type": "authentication_error",
                                       "message": "invalid api key"}})

        elif route == "/forbidden":
            self._send(403, {"error": {"type": "permission_error",
                                       "message": "your account cannot access this model"}})

        elif route == "/ratelimited":
            self._send(429, {"error": {"type": "rate_limit_error"}},
                       {"Retry-After": "12"})

        elif route == "/server-error":
            self._send(500, {"error": {"type": "internal_error"}})

        elif route == "/bad-request":
            self._send(400, {"error": {"type": "invalid_request_error",
                                       "message": "max_tokens: must be <= 8192"}})

        elif route == "/ok-but-failed":
            # Some APIs really do this: HTTP 200 with an error inside.
            self._send(200, {"error": "quota exceeded", "result": None})

        elif route == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for i, piece in enumerate(["Hel", "lo, ", "Bha", "rath", "!"]):
                event = (
                    f"event: content_block_delta\n"
                    f'data: {{"type":"text_delta","text":{json.dumps(piece)}}}\n\n'
                )
                self.wfile.write(event.encode())
                self.wfile.flush()
                time.sleep(0.05)               # simulate generation time
            self.wfile.write(b"event: message_stop\ndata: {}\n\n")
            self.wfile.flush()

        elif route == "/truncated-stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            for piece in ["The refund ", "policy is "]:
                self.wfile.write(
                    f'event: content_block_delta\ndata: {{"text":{json.dumps(piece)}}}\n\n'
                    .encode()
                )
                self.wfile.flush()
                time.sleep(0.05)
            # Closes WITHOUT sending message_stop.

        else:
            self._send(404, {"error": {"type": "not_found"}})

    def do_POST(self) -> None:                 # noqa: N802
        if self.path == "/orders":
            key = self.headers.get("Idempotency-Key", "")
            if key and key in _IDEMPOTENCY:
                self._send(200, {"order_id": _IDEMPOTENCY[key], "duplicate": True})
                return
            _ORDER_COUNT["n"] += 1
            order_id = f"ord-{_ORDER_COUNT['n']:03d}"
            if key:
                _IDEMPOTENCY[key] = order_id
            self._send(201, {"order_id": order_id, "duplicate": False})
        else:
            self._send(404, {"error": {"type": "not_found"}})


def call(base: str, route: str) -> tuple[int | None, dict, dict]:
    """Return (status, headers, body). status is None on a connection error."""
    request = urllib.request.Request(
        base + route,
        headers={"Authorization": "Bearer sk-fake-key", "User-Agent": "m2l11/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), json.loads(exc.read() or b"{}")
    except urllib.error.URLError:
        return None, {}, {}


def status_demo(base: str) -> None:
    print(LINE)
    print("1. STATUS CODES AND RETRY CLASSIFICATION")
    print(LINE)
    print(f"  {'route':<20}{'status':<8}{'retry?':<9}{'Retry-After':<13}detail")
    routes = ["/ok", "/bad-request", "/unauthenticated", "/forbidden",
              "/ratelimited", "/server-error", "/ok-but-failed"]
    for route in routes:
        status, headers, body = call(base, route)
        retry = "RETRY" if is_retryable(status) else "no"
        after = headers.get("Retry-After", "-")
        detail = ""
        if isinstance(body.get("error"), dict):
            detail = body["error"].get("message", body["error"].get("type", ""))
        elif body.get("error"):
            detail = str(body["error"])
        print(f"  {route:<20}{status!s:<8}{retry:<9}{after:<13}{detail[:32]}")

    print()
    print("  Note /ok-but-failed: status 200, classified 'no retry', but the")
    print("  BODY says 'quota exceeded'. Status-only classification misses it.")
    print("  Always inspect the body as well as the code.")


def header_demo(base: str) -> None:
    print()
    print(LINE)
    print("2. HEADERS - what to log and what never to log")
    print(LINE)
    status, headers, _ = call(base, "/ok")
    print(f"  response status : {status}")
    print(f"  request-id      : {headers.get('request-id')}   <- ALWAYS log this")
    print(f"  ratelimit-left  : "
          f"{headers.get('anthropic-ratelimit-requests-remaining')}")
    print()
    sent = {"Authorization": "Bearer sk-live-abc123", "User-Agent": "m2l11/1.0",
            "X-Api-Key": "secret-value", "Content-Type": "application/json"}
    print("  Request headers we sent, as they must appear in a log:")
    for name, value in redact_headers(sent).items():
        print(f"    {name:<18}{value}")
    print()
    print("  A bearer token IS your identity. Anyone who reads it from a log")
    print("  can act as you until it is rotated.")


def stream_demo(base: str) -> None:
    print()
    print(LINE)
    print("3. STREAMING - 200 arrives before the work is done")
    print(LINE)

    for route, label in (("/stream", "complete stream"),
                         ("/truncated-stream", "TRUNCATED stream")):
        request = urllib.request.Request(
            base + route, headers={"Accept": "text/event-stream"}
        )
        started = time.perf_counter()
        first_byte: float | None = None
        pieces: list[str] = []
        saw_stop = False

        with urllib.request.urlopen(request, timeout=5) as response:
            status = response.status
            for raw in response:
                line = raw.decode().strip()
                if not line:
                    continue
                if first_byte is None:
                    first_byte = time.perf_counter() - started
                if line.startswith("event:") and "message_stop" in line:
                    saw_stop = True
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    if "text" in payload:
                        pieces.append(payload["text"])

        total = time.perf_counter() - started
        print(f"  {label}")
        print(f"    HTTP status         : {status}   <- said OK before anything was generated")
        print(f"    chunks received     : {len(pieces)}")
        print(f"    assembled text      : {''.join(pieces)!r}")
        print(f"    time to first chunk : {first_byte * 1000:.0f} ms")
        print(f"    total time          : {total * 1000:.0f} ms")
        print(f"    saw message_stop    : {saw_stop}"
              f"{'' if saw_stop else '   <-- INCOMPLETE, yet status was 200'}")
        print()

    print("  The truncated stream returned 200 and then simply stopped. The")
    print("  only way to know it was cut off is the ABSENCE of the terminal")
    print("  event. If you trust the status code you will show the user half")
    print("  a sentence and call it an answer.")


def idempotency_demo(base: str) -> None:
    print()
    print(LINE)
    print("4. IDEMPOTENCY KEYS - making a POST retry safe")
    print(LINE)

    def post(key: str | None) -> dict:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Idempotency-Key"] = key
        request = urllib.request.Request(
            base + "/orders", data=b"{}", headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())

    print("  Without a key - simulating a timeout then a retry:")
    print(f"    attempt 1 -> {post(None)}")
    print(f"    attempt 2 -> {post(None)}   <-- TWO orders created")
    print()
    print("  With the SAME key reused across the retry:")
    key = "7f3c1e88-1111-2222-3333-444455556666"
    print(f"    attempt 1 -> {post(key)}")
    print(f"    attempt 2 -> {post(key)}   <-- same order, duplicate flagged")
    print()
    print("  With a NEW key per attempt (the common mistake):")
    print(f"    attempt 1 -> {post('key-aaa')}")
    print(f"    attempt 2 -> {post('key-bbb')}   <-- duplicate again")
    print()
    print("  Generate the key ONCE, before the first attempt, and reuse it.")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("=" * 74)
    print("HTTP: STATUS CODES, HEADERS, STREAMING AND IDEMPOTENCY")
    print("=" * 74)
    print(f"Local test server running on {base}")
    print()

    try:
        status_demo(base)
        header_demo(base)
        stream_demo(base)
        idempotency_demo(base)
    finally:
        server.shutdown()

    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
