"""M2-L14: retry classification, backoff, jitter and the thundering herd.

Requires httpx:
    source .venv/bin/activate
    python labs/m2/l14_retries.py

Local server; no key or internet needed.
"""

from __future__ import annotations

import json
import random
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

LINE = "-" * 74
RETRYABLE = {408, 425, 429, 500, 502, 503, 504, 529}
NON_RETRYABLE = {400, 401, 403, 404, 409, 413, 422}

_ATTEMPTS: Counter[str] = Counter()


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True

    def log_message(self, *args) -> None:
        pass

    def _json(self, status: int, payload: dict, extra: dict | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:                    # noqa: N802
        route = self.path
        _ATTEMPTS[route] += 1

        if route == "/flaky":
            # Fails twice, then succeeds. Counter resets per demo.
            if _ATTEMPTS[route] <= 2:
                self._json(503, {"error": "temporarily unavailable"})
            else:
                self._json(200, {"ok": True, "attempts": _ATTEMPTS[route]})
        elif route == "/always-500":
            self._json(500, {"error": "internal"})
        elif route == "/bad-request":
            self._json(400, {"error": "max_tokens must be <= 8192"})
        elif route == "/rate-limited":
            self._json(429, {"error": "slow down"}, {"Retry-After": "3"})
        else:
            self._json(404, {"error": "not found"})


# ---------------------------------------------------------------------------
def full_jitter(attempt: int, *, base: float = 1.0, cap: float = 30.0) -> float:
    return random.uniform(0, min(cap, base * (2 ** attempt)))


def call_with_retry(
    client: httpx.Client,
    path: str,
    *,
    max_attempts: int = 4,
    base: float = 0.05,          # small so the lab runs quickly
    cap: float = 1.0,
    deadline: float | None = None,
    verbose: bool = True,
) -> tuple[dict, int]:
    """Return (payload, calls_made). Raises on permanent failure."""
    started = time.monotonic()
    last_exc: Exception | None = None
    calls = 0

    for attempt in range(max_attempts):
        elapsed = time.monotonic() - started
        if deadline is not None and elapsed > deadline:
            raise TimeoutError(
                f"deadline of {deadline}s exceeded after {attempt} attempts "
                f"({elapsed:.2f}s elapsed)"
            ) from last_exc

        try:
            calls += 1
            response = client.get(path)
            response.raise_for_status()
            if verbose:
                print(f"      attempt {attempt + 1}: {response.status_code} OK")
            return response.json(), calls

        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code
            if status in NON_RETRYABLE:
                if verbose:
                    print(f"      attempt {attempt + 1}: {status} -> NOT retryable, "
                          f"failing immediately")
                raise
            server_wait = exc.response.headers.get("Retry-After")
            if server_wait and server_wait.isdigit():
                delay = float(server_wait)
                source = f"Retry-After: {server_wait}s"
            else:
                delay = full_jitter(attempt, base=base, cap=cap)
                source = "full jitter"
            if verbose:
                print(f"      attempt {attempt + 1}: {status} -> retryable, "
                      f"waiting {delay:.3f}s ({source})")

        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            last_exc = exc
            delay = full_jitter(attempt, base=base, cap=cap)
            if verbose:
                print(f"      attempt {attempt + 1}: {type(exc).__name__} -> "
                      f"never reached server, waiting {delay:.3f}s")

        if attempt == max_attempts - 1:
            break

        # Check the deadline BEFORE sleeping, not after. Sleeping 3 seconds
        # only to discover the deadline passed 2.5 seconds ago wastes the one
        # resource the deadline exists to protect.
        if deadline is not None:
            elapsed = time.monotonic() - started
            if elapsed + delay > deadline:
                if verbose:
                    print(f"      would need {delay:.3f}s more, but only "
                          f"{deadline - elapsed:.3f}s of deadline remains "
                          f"-> stopping now")
                raise TimeoutError(
                    f"deadline of {deadline}s would be exceeded by waiting "
                    f"{delay:.3f}s after {attempt + 1} attempts"
                ) from last_exc

        time.sleep(delay)

    raise RuntimeError(f"failed after {max_attempts} attempts") from last_exc


def retry_demo(base_url: str) -> None:
    section("1. RETRY CLASSIFICATION IN ACTION")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:

        print("  /flaky  (503, 503, then 200)")
        _ATTEMPTS["/flaky"] = 0
        payload, calls = call_with_retry(client, "/flaky")
        print(f"      -> succeeded: {payload}, total calls: {calls}")
        print()

        print("  /bad-request  (400 - not retryable)")
        try:
            call_with_retry(client, "/bad-request")
        except httpx.HTTPStatusError as exc:
            print(f"      -> raised {exc.response.status_code} after 1 call")
            print("      Four attempts were allowed. Only ONE was used, because")
            print("      retrying a 400 cannot possibly succeed.")
        print()

        print("  /rate-limited  (429 with Retry-After: 3)")
        try:
            call_with_retry(client, "/rate-limited", max_attempts=2, deadline=0.5)
        except TimeoutError as exc:
            print(f"      -> TimeoutError: {exc}")
            print("      The server asked for 3s; our deadline was 0.5s. Stopping")
            print("      is correct - the caller will have given up long before.")
        print()

        print("  /always-500 with deadline=0.3s")
        try:
            call_with_retry(client, "/always-500", max_attempts=8,
                            base=0.1, cap=1.0, deadline=0.3)
        except (TimeoutError, RuntimeError) as exc:
            print(f"      -> {type(exc).__name__}: {exc}")


def herd_demo() -> None:
    section("2. THE THUNDERING HERD - why jitter is mandatory")
    clients = 500
    outage_ends = 5.0
    attempt = 3          # every client is on its 4th attempt when the outage ends

    fixed = [outage_ends + 1.0 * (2 ** attempt) for _ in range(clients)]
    jittered = [outage_ends + random.uniform(0, min(30.0, 1.0 * (2 ** attempt)))
                for _ in range(clients)]

    def histogram(times: list[float], label: str) -> int:
        buckets: Counter[int] = Counter()
        for t in times:
            buckets[int((t - outage_ends) * 2)] += 1      # 500 ms buckets
        peak = max(buckets.values())
        print(f"  {label}")
        for bucket in range(0, 18):
            count = buckets.get(bucket, 0)
            bar = "#" * int(count / clients * 60)
            if count or bucket < 17:
                print(f"    t+{bucket / 2:>4.1f}s |{bar:<60}| {count:>4}")
        print(f"    peak in any 500ms window: {peak} of {clients} clients")
        print()
        return peak

    peak_fixed = histogram(fixed, "FIXED exponential backoff (no jitter)")
    peak_jitter = histogram(jittered, "FULL JITTER")

    print(f"  Peak load reduced from {peak_fixed} to {peak_jitter} "
          f"({peak_fixed / max(peak_jitter, 1):.0f}x lower)")
    print()
    print("  Without jitter every client waits EXACTLY 8s, so all 500 retries")
    print("  land in the same instant. The service has just come back up and")
    print("  is immediately hit by its entire client base at once - which is")
    print("  how a recovering service falls over again.")
    print()
    print("  Backoff spreads retries in time PER CLIENT. Only jitter spreads")
    print("  them ACROSS clients. You need both.")


class TokenBucket:
    """Bounds RATE. A semaphore bounds CONCURRENCY. They are different limits."""

    def __init__(self, rate: float, capacity: float) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.updated = time.monotonic()

    def acquire(self) -> float:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        return (1 - self.tokens) / self.rate


def bucket_demo() -> None:
    section("3. TOKEN BUCKET - bounding RATE, not concurrency")
    bucket = TokenBucket(rate=2.0, capacity=5.0)     # 2/s sustained, burst of 5
    print("  rate=2/s, capacity=5 (so a burst of 5 is allowed immediately)")
    print()
    print(f"  {'request':<10}{'wait':>10}   note")
    started = time.monotonic()
    for i in range(1, 9):
        wait = bucket.acquire()
        note = "burst allowed" if wait == 0 and i <= 5 else (
            "throttled" if wait > 0 else "token refilled")
        print(f"  {i:<10}{wait:>9.2f}s   {note}")
        if wait:
            time.sleep(wait)
    print()
    print(f"  8 requests took {time.monotonic() - started:.2f}s")
    print("  The first 5 went straight through (the burst capacity), then the")
    print("  bucket enforced roughly 2 per second.")
    print()
    print("  A SEMAPHORE would not have helped here: 8 sequential requests are")
    print("  never concurrent. Rate limits and concurrency limits are")
    print("  different constraints and providers usually impose both.")


def amplification_demo() -> None:
    section("4. RETRY AMPLIFICATION - why you retry at ONE layer only")
    print(f"  {'layers retrying':<22}{'attempts each':<16}{'upstream calls'}")
    for layers in (1, 2, 3):
        print(f"  {layers:<22}{3:<16}{3 ** layers}")
    print()
    print("  One user request becomes 27 upstream calls when the client, the")
    print("  service and the gateway each retry three times. During a partial")
    print("  degradation that multiplies load by 27 at exactly the moment the")
    print("  dependency can least afford it.")
    print()
    print("  Rule: retry at exactly ONE layer - normally the lowest one that")
    print("  can classify the error correctly - and disable it everywhere else.")


def main() -> None:
    random.seed(42)
    server = QuietServer(("127.0.0.1", 0), Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("=" * 74)
    print("TIMEOUTS, RETRIES, BACKOFF AND RATE LIMITS")
    print("=" * 74)
    print(f"Local server on {base}")
    try:
        retry_demo(base)
        herd_demo()
        bucket_demo()
        amplification_demo()
    finally:
        server.shutdown()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
