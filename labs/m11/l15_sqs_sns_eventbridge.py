"""M11-L15 lab -- a queue is a shock absorber with arithmetic you can do.
This lab computes:

  1. a traffic spike with and without a queue: what users experience,
  2. visibility timeout against processing time, and the duplicates it creates,
  3. at-least-once delivery: how often idempotency actually saves you,
  4. a poison message: how much good work it blocks before a DLQ catches it,
  5. SQS, SNS and EventBridge matched to six requirements.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l15_sqs_sns_eventbridge.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1115)

# ============================================================ 1
rule("1. A SPIKE, WITH AND WITHOUT A QUEUE")

CAPACITY = 60                 # requests/second the workers can process
ARRIVALS = [40] * 10 + [260] * 20 + [40] * 40      # 70 seconds, a 20-second spike
print(f"  worker capacity {CAPACITY}/s; arrivals peak at {max(ARRIVALS)}/s for 20 s\n")

# without a queue: anything above capacity is rejected
rejected = sum(max(0, a - CAPACITY) for a in ARRIVALS)
offered = sum(ARRIVALS)
print(f"  WITHOUT a queue (synchronous):")
print(f"    offered {offered:,} requests, rejected {rejected:,} ({rejected / offered:.1%}) with errors")
print(f"    users affected immediately; the spike is lost work")

# with a queue: everything is accepted, latency grows and drains
backlog = 0
max_backlog = 0
latencies = []
for t, a in enumerate(ARRIVALS):
    backlog += a
    done = min(backlog, CAPACITY)
    backlog -= done
    max_backlog = max(max_backlog, backlog)
    latencies.append(backlog / CAPACITY)
drain_t = next((t for t, l in enumerate(latencies) if t > 30 and l < 1), len(latencies))
print(f"\n  WITH a queue:")
print(f"    rejected 0; peak backlog {max_backlog:,} messages")
print(f"    worst wait {max(latencies):.1f} s; back to normal {drain_t - 30} s after the spike ended")
print(f"    total work done: {offered:,} -- nothing was lost")
print("\n  The queue converts an AVAILABILITY problem into a LATENCY problem. That is")
print("  a good trade for ingestion, embedding, indexing and notifications, and a")
print("  bad one for a user waiting for an answer. Use it where the work can be")
print("  asynchronous, and tell the user it is queued (M10-L09).")


# ============================================================ 2
rule("2. VISIBILITY TIMEOUT VS PROCESSING TIME")

PROCESSING = [("fast path", 4), ("typical", 22), ("slow: long model call", 95),
              ("stuck: downstream hang", 400)]
TIMEOUTS = [30, 60, 300, 900]
print(f"  a message is redelivered if not deleted within the visibility timeout\n")
print(f"  {'processing time':<30}" + "".join(f"{f'{t} s':>12}" for t in TIMEOUTS))
for label, secs in PROCESSING:
    row = ""
    for t in TIMEOUTS:
        row += f"{('ok' if secs < t else 'REDELIVERED'):>12}"
    print(f"  {label + f' ({secs} s)':<30}{row}")
print("\n  A message redelivered while still being processed is now being processed")
print("  TWICE -- and the first worker will finish and delete it, so the second copy")
print("  does the work again. With a 30 s timeout, any model call over 30 s")
print("  duplicates every single time. Set the timeout above your p99 processing")
print("  time, or extend it from the worker as it goes (M13-L11).")


# ============================================================ 3
rule("3. AT-LEAST-ONCE: HOW OFTEN DOES A DUPLICATE ARRIVE?")

N = 200_000
DUP_RATE = 0.001          # standard queues deliver a duplicate occasionally
RETRY_DUP = 0.02          # plus duplicates from timeouts and worker crashes
dups = sum(1 for _ in range(N) if rng.random() < DUP_RATE + RETRY_DUP)
print(f"  {N:,} messages processed\n")
print(f"  duplicates delivered: {dups:,} ({dups / N:.2%})")
EFFECTS = [
    ("append a row to an audit log",     "harmless duplicate row", False),
    ("index a chunk (same id)",          "idempotent by key",      False),
    ("charge a customer",                "CHARGED TWICE",          True),
    ("send a notification email",        "EMAILED TWICE",          True),
    ("increment a counter",              "COUNT IS WRONG",         True),
    ("call the model and store by hash", "idempotent by content",  False),
]
print(f"\n  {'what the handler does':<38}{'effect of a duplicate':<26}needs a key?")
for action, effect, needs in EFFECTS:
    print(f"  {action:<38}{effect:<26}{'YES' if needs else 'no'}")
harmful = sum(1 for _, _, n in EFFECTS if n)
print(f"\n  handlers that must be made idempotent: {harmful}/{len(EFFECTS)}")
print(f"  at {dups / N:.2%} duplication, {harmful} of {len(EFFECTS)} handlers would misbehave "
      f"~{int(dups * harmful / len(EFFECTS)):,} times")
print("  'At-least-once' is not a caveat in the documentation; it is a requirement")
print("  on your handler. Store an idempotency key, conditionally write it, and")
print("  make the second delivery a no-op (M8-L12).")


# ============================================================ 4
rule("4. A POISON MESSAGE, AND WHAT A DLQ SAVES")

MAX_RECEIVE = [1, 3, 5, 100]
POISON_PROCESS_S = 30
print(f"  one message always fails, taking {POISON_PROCESS_S} s of a worker each time\n")
print(f"  {'maxReceiveCount':>17}{'attempts':>11}{'worker-seconds wasted':>24}   {'then':<32}")
for m in MAX_RECEIVE:
    wasted = m * POISON_PROCESS_S
    then = "moved to the DLQ" if m < 100 else "retried until it expires (days)"
    print(f"  {m:>17}{m:>11}{wasted:>24}   {then:<32}")
print(f"\n  without a DLQ, the message is retried until the retention period expires:")
print(f"    at a 4-day default retention, that is up to "
      f"{4 * 86400 // POISON_PROCESS_S:,} attempts of {POISON_PROCESS_S} s each")
print("  In a STANDARD queue the poison message only wastes a worker. In a FIFO")
print("  queue it BLOCKS its message group entirely: every later message for that")
print("  group waits behind it. Set maxReceiveCount to a small number, alarm on")
print("  DLQ depth, and treat anything in the DLQ as an incident with a cause")
print("  (M10-L14).")


# ============================================================ 5
rule("5. SQS, SNS OR EVENTBRIDGE?")

NEEDS = [
    ("absorb a spike; one consumer; work must not be lost",   "SQS"),
    ("one event, five unrelated consumers, fan out",          "SNS or EventBridge"),
    ("route events by their CONTENT to different targets",    "EventBridge"),
    ("strict ordering per customer",                          "SQS FIFO"),
    ("react to an AWS service event (S3 object created)",     "EventBridge"),
    ("replay last week's events after fixing a bug",          "EventBridge (archive + replay)"),
]
print(f"  {'requirement':<56}{'fits':<24}")
for need, fit in NEEDS:
    print(f"  {need:<56}{fit:<24}")
print("\n  The short version: SQS is a BUFFER between a producer and a consumer that")
print("  may be slower. SNS is a FAN-OUT: one message, many subscribers, push")
print("  delivery. EventBridge is a ROUTER: rules match event content and send it")
print("  to targets, with schemas, archive and replay.")
print("  The common production pattern combines them: EventBridge or SNS for fan-out,")
print("  with an SQS queue in front of EACH consumer so that a slow or broken")
print("  consumer buffers its own backlog instead of losing messages.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every backlog figure, redelivery verdict, duplicate count, wasted")
print("  worker-second and routing match above is computed by this script.")
print("\n  DOCUMENTED BEHAVIOUR: standard SQS is at-least-once with best-effort")
print("  ordering; a message not deleted within the visibility timeout is")
print("  redelivered; maxReceiveCount moves a message to a dead-letter queue; FIFO")
print("  queues preserve order within a message group.")
print("\n  ILLUSTRATIVE: traffic figures, capacity, duplication rates and processing")
print("  times are invented. Default retention and visibility values change --")
print("  check current documentation.")
print("\n  NOT SHOWN: long polling, batching, message attributes, Step Functions, and")
print("  Kinesis/streaming (M12-L09).")
print("\nDone.")
