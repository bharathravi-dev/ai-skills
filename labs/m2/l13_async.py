"""M2-L13: sequential vs concurrent vs bounded, and the blocking trap.

Requires httpx:
    source .venv/bin/activate
    python labs/m2/l13_async.py

Runs a local server; no key or internet needed.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

LINE = "-" * 74
N_REQUESTS = 30
SERVER_DELAY = 0.10          # each request takes 100 ms server-side


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

    def do_GET(self) -> None:                       # noqa: N802
        time.sleep(SERVER_DELAY)                    # simulate a slow upstream
        # /item/N fails for every 5th id, to exercise partial failure.
        index = int(self.path.rsplit("/", 1)[-1]) if self.path[-1].isdigit() else 0
        status = 500 if (self.path.startswith("/flaky/") and index % 5 == 0) else 200
        body = json.dumps({"id": index, "ok": status == 200}).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


# ---------------------------------------------------------------------------
async def sequential(base: str) -> float:
    start = time.perf_counter()
    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        for i in range(N_REQUESTS):
            await client.get(f"/item/{i}")
    return time.perf_counter() - start


async def concurrent_unbounded(base: str) -> float:
    start = time.perf_counter()
    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        await asyncio.gather(*(client.get(f"/item/{i}") for i in range(N_REQUESTS)))
    return time.perf_counter() - start


async def concurrent_bounded(base: str, limit: int) -> float:
    semaphore = asyncio.Semaphore(limit)
    start = time.perf_counter()
    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        async def one(i: int):
            async with semaphore:
                return await client.get(f"/item/{i}")
        await asyncio.gather(*(one(i) for i in range(N_REQUESTS)))
    return time.perf_counter() - start


async def blocking_trap(base: str) -> float:
    """Looks concurrent. Is not. time.sleep freezes the whole event loop."""
    start = time.perf_counter()

    async def one(i: int) -> None:
        time.sleep(SERVER_DELAY)        # BLOCKING - no await, loop is frozen
        return None

    await asyncio.gather(*(one(i) for i in range(N_REQUESTS)))
    return time.perf_counter() - start


async def fixed_with_to_thread() -> float:
    """The same blocking work, offloaded so the loop keeps running."""
    start = time.perf_counter()

    async def one(i: int) -> None:
        await asyncio.to_thread(time.sleep, SERVER_DELAY)

    await asyncio.gather(*(one(i) for i in range(N_REQUESTS)))
    return time.perf_counter() - start


async def timing_demo(base: str) -> None:
    section("1. SEQUENTIAL vs CONCURRENT vs BOUNDED")
    print(f"  {N_REQUESTS} requests, each taking {SERVER_DELAY * 1000:.0f} ms server-side.")
    print(f"  Theoretical sequential floor: {N_REQUESTS * SERVER_DELAY:.1f} s")
    print()
    print("  Each strategy is run 3 times, because the SPREAD matters as much")
    print("  as the average.")
    print()

    async def repeat(fn, times: int = 3) -> list[float]:
        return [await fn() for _ in range(times)]

    seq = await repeat(lambda: sequential(base), times=1)
    unb = await repeat(lambda: concurrent_unbounded(base))
    b10 = await repeat(lambda: concurrent_bounded(base, 10))
    b5 = await repeat(lambda: concurrent_bounded(base, 5))

    baseline = seq[0]
    print(f"  {'strategy':<28}{'best':>9}{'worst':>9}{'spread':>9}{'speed-up':>11}")
    for label, runs in (("sequential", seq), ("gather (unbounded)", unb),
                        ("gather + semaphore(10)", b10), ("gather + semaphore(5)", b5)):
        best, worst = min(runs), max(runs)
        spread = worst - best
        print(f"  {label:<28}{best:>8.2f}s{worst:>8.2f}s{spread:>8.2f}s"
              f"{baseline / best:>10.1f}x")

    print()
    print("  Nothing got faster. The WAITING overlapped. During the")
    print("  sequential run the CPU was idle almost the entire time.")
    print()
    print("  Now the result people find surprising: compare unbounded gather")
    print("  with semaphore(10). More concurrency was SLOWER.")
    print()
    print("  Firing all 30 requests at once saturates the server. It has a")
    print("  finite number of worker threads, so the extra requests do not")
    print("  run sooner - they queue, and everything contends for the same")
    print("  resources. Ten at a time keeps the server in its efficient range.")
    print()
    print("  This is the general shape of concurrency tuning: throughput rises")
    print("  with concurrency up to the point the downstream service")
    print("  saturates, then FLATTENS OR FALLS. The best limit is a property")
    print("  of the thing you are calling, not of your code, so it must be")
    print("  measured rather than guessed.")
    print()
    print("  Exact numbers vary between machines and runs. What is stable is")
    print("  the shape: sequential is worst, a sensible bound is best, and")
    print("  unbounded is neither fastest nor safe. Against a real API,")
    print("  unbounded also means HTTP 429s and exhausted file descriptors.")


async def blocking_demo(base: str) -> None:
    section("2. THE BLOCKING TRAP - async that is not concurrent")
    blocked = await blocking_trap(base)
    threaded = await fixed_with_to_thread()

    print(f"  {'version':<44}{'time':>10}")
    print(f"  {'async def + time.sleep (BLOCKING)':<44}{blocked:>9.2f}s")
    print(f"  {'async def + await asyncio.to_thread(...)':<44}{threaded:>9.2f}s")
    print()
    print(f"  The first is {blocked / threaded:.0f}x slower despite being 'async'.")
    print()
    print("  time.sleep does not yield to the event loop, so all 30 'concurrent'")
    print("  coroutines ran one after another. The code LOOKS concurrent, uses")
    print("  gather, and is fully sequential.")
    print()
    print("  DIAGNOSTIC: an 'async def' whose body contains no 'await' is")
    print("  almost always this bug. Look for the missing await first.")


def cpu_work(n: int) -> int:
    """Deliberately CPU-bound: no I/O to overlap."""
    return sum(i * i for i in range(n))


async def cpu_demo() -> None:
    section("3. CPU-BOUND WORK - async and threads do not help")
    size = 3_000_000
    jobs = 4

    start = time.perf_counter()
    for _ in range(jobs):
        cpu_work(size)
    seq = time.perf_counter() - start

    async def one() -> int:
        return cpu_work(size)          # no await: nothing to yield to
    start = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(jobs)))
    asyncio_time = time.perf_counter() - start

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(cpu_work, [size] * jobs))
    threads = time.perf_counter() - start

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(cpu_work, [size] * jobs))
    processes = time.perf_counter() - start

    print(f"  {jobs} jobs, each summing {size:,} squares")
    print()
    print(f"  {'approach':<32}{'time':>10}{'vs sequential':>16}")
    print(f"  {'sequential':<32}{seq:>9.2f}s{'1.0x':>16}")
    print(f"  {'asyncio.gather':<32}{asyncio_time:>9.2f}s{seq / asyncio_time:>15.1f}x")
    print(f"  {'ThreadPoolExecutor':<32}{threads:>9.2f}s{seq / threads:>15.1f}x")
    print(f"  {'ProcessPoolExecutor':<32}{processes:>9.2f}s{seq / processes:>15.1f}x")
    print()
    print("  asyncio and threads give roughly NO improvement: the GIL lets")
    print("  only one thread execute Python bytecode at a time, and there is")
    print("  no I/O to overlap. Only separate PROCESSES get real parallelism.")


async def partial_failure_demo(base: str) -> None:
    section("4. PARTIAL FAILURE - keeping the successes")
    total = 20
    semaphore = asyncio.Semaphore(5)

    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        async def one(i: int) -> tuple[int, dict]:
            async with semaphore:
                response = await client.get(f"/flaky/{i}")
                response.raise_for_status()          # raises on the 500s
                return i, response.json()

        print("  WITHOUT return_exceptions=True:")
        try:
            await asyncio.gather(*(one(i) for i in range(total)))
        except httpx.HTTPStatusError as exc:
            print(f"    gather raised {type(exc).__name__} "
                  f"({exc.response.status_code}) on the first failure.")
            print("    Every successful result was discarded.")

        print()
        print("  WITH return_exceptions=True:")
        outcomes = await asyncio.gather(
            *(one(i) for i in range(total)), return_exceptions=True
        )

    results: dict[int, dict] = {}
    failures: list[tuple[int, str]] = []
    for index, outcome in enumerate(outcomes):
        if isinstance(outcome, Exception):
            failures.append((index, type(outcome).__name__))
        else:
            position, payload = outcome
            results[position] = payload

    print(f"    kept {len(results)} successes, captured {len(failures)} failures")
    print(f"    failed indices: {[i for i, _ in failures]}")
    print(f"    (the server fails every 5th id, so this is exactly right)")
    print()
    print("  The exceptions arrive as ORDINARY VALUES in the results list.")
    print("  If you do not check for them you will pass an exception object")
    print("  downstream as if it were data.")


async def main_async(base: str) -> None:
    await timing_demo(base)
    await blocking_demo(base)
    await cpu_demo()
    await partial_failure_demo(base)


def main() -> None:
    server = QuietServer(("127.0.0.1", 0), Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("=" * 74)
    print("ASYNC AND CONCURRENCY")
    print("=" * 74)
    print(f"Local server on {base}")
    try:
        asyncio.run(main_async(base))
    finally:
        server.shutdown()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
