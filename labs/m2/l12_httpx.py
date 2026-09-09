"""M2-L12: httpx clients, timeouts, streaming, typed wrappers, MockTransport.

Requires httpx and pydantic:
    source .venv/bin/activate
    python labs/m2/l12_httpx.py

Runs a local server, so no API key and no internet access are needed.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
from pydantic import BaseModel, ValidationError

LINE = "-" * 74
RETRYABLE = {408, 425, 429, 500, 502, 503, 504, 529}


class QuietServer(ThreadingHTTPServer):
    """Suppresses the BrokenPipeError traceback the timeout demo provokes.

    When the client gives up on /slow it closes the socket while the server is
    still writing. That is exactly the behaviour being demonstrated, so the
    traceback is noise rather than a fault.
    """

    def handle_error(self, request, client_address) -> None:
        pass


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # Without TCP_NODELAY, Nagle's algorithm interacts with delayed ACKs and
    # adds ~40 ms to every request on loopback. That artefact is larger than
    # everything this lab measures, so it would drown the real result.
    disable_nagle_algorithm = True

    def log_message(self, *args) -> None:
        pass

    def _json(self, status: int, payload: dict, extra: dict | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("request-id", "req_abc123")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:                            # noqa: N802
        if self.path.startswith("/items/"):
            self._json(200, {"id": self.path.rsplit("/", 1)[-1], "name": "widget"})
        elif self.path == "/slow":
            time.sleep(1.0)
            try:
                self._json(200, {"ok": True})
            except (BrokenPipeError, ConnectionResetError):
                pass          # the client timed out and left; that is the point
        elif self.path == "/server-error":
            self._json(500, {"error": {"message": "internal error"}})
        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            for piece in ["Refunds ", "take ", "five ", "business ", "days."]:
                self.wfile.write(
                    f'data: {json.dumps({"text": piece})}\n\n'.encode()
                )
                self.wfile.flush()
                time.sleep(0.05)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self._json(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:                           # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/messages":
            self._json(200, {"id": "msg_1", "text": payload.get("text", ""),
                             "tokens": len(payload.get("text", "").split())})
        elif self.path == "/messages-malformed":
            self._json(200, {"id": "msg_2"})              # missing required fields
        else:
            self._json(404, {"error": {"message": "not found"}})


# ---------------------------------------------------------------------------
# The typed client from section 5.5
# ---------------------------------------------------------------------------
class Message(BaseModel):
    id: str
    text: str
    tokens: int


class ApiError(Exception):
    def __init__(self, status: int, message: str, request_id: str | None) -> None:
        super().__init__(f"{status}: {message} (request_id={request_id})")
        self.status = status
        self.message = message
        self.request_id = request_id
        self.retryable = status in RETRYABLE


class MessagesClient:
    def __init__(self, base_url: str, api_key: str, *,
                 transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
            transport=transport,
        )

    def create(self, text: str, *, path: str = "/messages") -> Message:
        response = self._client.post(path, json={"text": text})
        request_id = response.headers.get("request-id")
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            raise ApiError(
                response.status_code,
                body.get("error", {}).get("message", "unknown"),
                request_id,
            )
        return Message.model_validate(response.json())

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MessagesClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()


def pooling_demo(base: str) -> None:
    section("1. CONNECTION POOLING - reuse one client")
    n = 50

    start = time.perf_counter()
    for i in range(n):
        httpx.get(f"{base}/items/{i}", timeout=10.0)
    unpooled = time.perf_counter() - start

    with httpx.Client(base_url=base, timeout=10.0) as client:
        start = time.perf_counter()
        for i in range(n):
            client.get(f"/items/{i}")
        pooled = time.perf_counter() - start

    print(f"  {n} requests, new connection each time : {unpooled * 1000:7.1f} ms")
    print(f"  {n} requests, one pooled client        : {pooled * 1000:7.1f} ms")
    print(f"  speed-up                               : {unpooled / pooled:.1f}x")
    print()
    print("  What you are seeing is the cost of CONNECTION SETUP, repeated 50")
    print("  times versus paid once. Even on loopback - no DNS, no network")
    print("  latency, no TLS - it dominates.")
    print()
    print("  Against a real HTTPS provider the gap is LARGER still, because")
    print("  each new connection also pays for a DNS lookup, a network")
    print("  round trip, and a TLS handshake (typically 50-200 ms on its own).")
    print("  None of those appear in this local measurement.")


def timeout_demo(base: str) -> None:
    section("2. TIMEOUTS AND THE EXCEPTION HIERARCHY")
    print(f"  {'scenario':<34}{'exception':<24}reached server?")

    # Read timeout: server sleeps 1s, we allow 0.2s
    try:
        httpx.get(f"{base}/slow",
                  timeout=httpx.Timeout(5.0, read=0.2))
    except httpx.HTTPError as exc:
        print(f"  {'read timeout (server too slow)':<34}{type(exc).__name__:<24}unknown")

    # Connect error: nothing listening on this port
    try:
        httpx.get("http://127.0.0.1:9/items/1", timeout=2.0)
    except httpx.HTTPError as exc:
        print(f"  {'connect error (port closed)':<34}{type(exc).__name__:<24}NO - safe to retry")

    # Status error, only if you ask for it
    response = httpx.get(f"{base}/server-error", timeout=5.0)
    print(f"  {'500 without raise_for_status':<34}{'(no exception)':<24}yes")
    print(f"    -> status_code={response.status_code}, "
          f"body flows on as data: {response.json()}")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"  {'500 with raise_for_status':<34}{type(exc).__name__:<24}yes")
        print(f"    -> retryable? {exc.response.status_code in RETRYABLE}")

    print()
    print("  The exception TYPE answers the retry question:")
    print("    ConnectError      -> never reached the server. Always safe.")
    print("    TimeoutException  -> UNKNOWN. May have been processed. For a")
    print("                         write, retry only with an idempotency key.")
    print("    HTTPStatusError   -> reached it; decide from the status code.")


def streaming_demo(base: str) -> None:
    section("3. STREAMING")
    timeout = httpx.Timeout(5.0, read=5.0)      # 5.0 is the default for the rest
    with httpx.Client(base_url=base, timeout=timeout) as client:
        started = time.perf_counter()
        first: float | None = None
        pieces: list[str] = []
        with client.stream("GET", "/stream") as response:
            response.raise_for_status()
            print(f"  status {response.status_code} received after "
                  f"{(time.perf_counter() - started) * 1000:.0f} ms "
                  f"(before ANY text was generated)")
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                if first is None:
                    first = time.perf_counter() - started
                pieces.append(json.loads(payload)["text"])
        total = time.perf_counter() - started

    print(f"  chunks              : {len(pieces)}")
    print(f"  text                : {''.join(pieces)!r}")
    print(f"  time to first chunk : {first * 1000:.0f} ms")
    print(f"  total time          : {total * 1000:.0f} ms")
    print(f"  perceived wait is the FIRST number, not the second.")


def typed_client_demo(base: str) -> None:
    section("4. A TYPED CLIENT")
    with MessagesClient(base, api_key="sk-fake") as client:
        message = client.create("Refund my order please")
        print(f"  create() -> {message!r}")
        print(f"    type    : {type(message).__name__} (validated, not a raw dict)")
        print(f"    tokens  : {message.tokens} ({type(message.tokens).__name__})")

        print()
        print("  A malformed response is caught at the boundary:")
        try:
            client.create("hello", path="/messages-malformed")
        except ValidationError as exc:
            for err in exc.errors():
                print(f"    {err['loc']}: {err['msg']}")
        print("    The server returned HTTP 200. Only validation caught it.")


def mock_transport_demo() -> None:
    section("5. MockTransport - testing the real client with no network")

    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/messages":
            return httpx.Response(
                200,
                json={"id": "msg_mock", "text": "mocked", "tokens": 1},
                headers={"request-id": "req_mock"},
            )
        return httpx.Response(429, json={"error": {"message": "slow down"}},
                              headers={"request-id": "req_mock_429",
                                       "Retry-After": "12"})

    client = MessagesClient("https://api.example.test", "sk-fake",
                            transport=httpx.MockTransport(handler))

    message = client.create("hello")
    print(f"  success path -> {message!r}")

    try:
        client.create("hello", path="/other")
    except ApiError as exc:
        print(f"  429 path     -> ApiError status={exc.status} "
              f"retryable={exc.retryable} request_id={exc.request_id}")

    print()
    print(f"  requests actually made: {len(calls)}")
    for request in calls:
        auth = request.headers.get("authorization", "")
        redacted = "***REDACTED***" if auth else "(none)"
        print(f"    {request.method} {request.url.path}  Authorization={redacted}")
    print()
    print("  The real client ran unchanged: same headers, same timeouts, same")
    print("  error handling, same Pydantic validation. No network, no key, no")
    print("  flakiness - and a 429 was trivial to simulate.")
    client.close()


def main() -> None:
    server = QuietServer(("127.0.0.1", 0), Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("=" * 74)
    print("HTTP CLIENTS WITH httpx")
    print("=" * 74)
    print(f"httpx version {httpx.__version__}; local server on {base}")
    try:
        pooling_demo(base)
        timeout_demo(base)
        streaming_demo(base)
        typed_client_demo(base)
        mock_transport_demo()
    finally:
        server.shutdown()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
