"""M5-L14 lab -- refusal detection, retry-worthiness, and circuit breakers.

Section 1 is REAL: a heuristic refusal detector run against constructed
sample outputs, including legitimate domain text that happens to contain
refusal-shaped words. Sections 2 and 3 are real arithmetic on stated
(mock) rates and parameters -- no LLM involved anywhere in this lab.

Deterministic. No API key, no network.
Run:  python labs/m5/l14_refusals_fallback.py
"""

from __future__ import annotations


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. REFUSAL DETECTION: A HEURISTIC THAT MISFIRES BOTH WAYS")

REFUSAL_MARKERS = [
    "i can't", "i cannot", "i won't", "i'm not able", "i am not able",
    "unable to", "as an ai", "i'm sorry, but",
]


def naive_refusal_detector(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in REFUSAL_MARKERS)


SAMPLES = [
    ("genuine_refusal_1",
     "I'm sorry, but I can't help with that request.", "refusal"),
    ("genuine_refusal_2",
     "I won't be able to assist with this, as it violates our usage "
     "policies.", "refusal"),
    ("genuine_refusal_3",
     "As an AI, I cannot provide medical diagnoses.", "refusal"),
    ("capability_limit",
     "I don't have the ability to browse the internet or access "
     "real-time data.", "refusal"),
    ("legit_domain_1",
     "Unable to find a matching record for that order number in our "
     "system. Please check the number and try again.", "legitimate"),
    ("legit_domain_2",
     "Under section 4.2, the tenant cannot sublet the property without "
     "written consent from the landlord.", "legitimate"),
    ("legit_domain_3",
     "Employees are unable to expense meals over $50 without prior "
     "manager approval.", "legitimate"),
    ("empty_response", "", "empty"),
    ("error_shaped",
     "Error: rate limit exceeded. Please try again later.", "infra_error"),
]

print("  Nine sample outputs. Ground truth: is this actually a model")
print("  REFUSING, or something else entirely?\n")
print(f"  {'sample':<20}{'true class':<14}{'detector says':<16}{'correct?'}")
false_pos = false_neg = 0
for name, text, true_class in SAMPLES:
    flagged = naive_refusal_detector(text)
    detector_says = "refusal" if flagged else "not-refusal"
    if true_class == "refusal":
        correct = flagged
        false_neg += not correct
    elif true_class == "legitimate":
        correct = not flagged
        false_pos += flagged
    else:
        correct = None   # empty / infra_error: not this detector's job at all
    mark = "n/a (wrong tool)" if correct is None else ("yes" if correct else "NO")
    print(f"  {name:<20}{true_class:<14}{detector_says:<16}{mark}")

n_refusals = sum(1 for _, _, c in SAMPLES if c == "refusal")
n_legit = sum(1 for _, _, c in SAMPLES if c == "legitimate")
print(f"\n  False negatives: {false_neg}/{n_refusals} genuine refusals missed.")
print(f"  False positives: {false_pos}/{n_legit} legitimate answers wrongly "
      f"flagged as refusals.")
print("\n  Read the two 'legit_domain' rows the detector got wrong: they")
print("  contain the exact words a refusal detector looks for, because the")
print("  DOMAIN CONTENT is about things that can't or cannot be done. And")
print("  read the last two rows: an empty response and an infrastructure")
print("  error are not refusals at all -- they are two entirely separate")
print("  failure classes a real system must detect with DIFFERENT checks,")
print("  not folded into 'the model said no.'")


# ============================================================ 2
rule("2. RETRYING AN INFRA ERROR VS RETRYING A REFUSAL")

INFRA_RETRY_SUCCESS_P = 0.60    # per-attempt success once the cause is transient
REFUSAL_RETRY_SUCCESS_P = 0.03  # per-attempt success on an identical re-ask

print("  Per-attempt success probability, cumulative over repeated retries")
print(f"  of the SAME request. Infra error (transient, per M2-L14): "
      f"{INFRA_RETRY_SUCCESS_P:.0%}/attempt.")
print(f"  Safety/policy refusal, identical re-ask: "
      f"{REFUSAL_RETRY_SUCCESS_P:.0%}/attempt.\n")
print(f"  {'attempts':>9}{'infra: cumulative success':>27}"
      f"{'refusal: cumulative success':>29}")
for k in (1, 2, 3, 5, 8):
    infra_cum = 1 - (1 - INFRA_RETRY_SUCCESS_P) ** k
    refusal_cum = 1 - (1 - REFUSAL_RETRY_SUCCESS_P) ** k
    print(f"  {k:>9}{infra_cum:>27.0%}{refusal_cum:>29.0%}")

print("\n  By 5 attempts, retrying a transient infra error succeeds nearly")
print("  99% of the time -- exactly why M2-L14's retry-with-backoff exists.")
print("  Retrying an identical prompt after a policy refusal barely moves: "
      f"just {1 - (1 - REFUSAL_RETRY_SUCCESS_P) ** 5:.0%} after those same 5")
print("  attempts, for the same cost. The refusal is not noise around a")
print("  right answer the way a timeout is -- it is closer to the model's")
print("  actual, repeatable answer. Retrying it blindly with M2-L14's")
print("  machinery burns budget for almost nothing; the right response is a")
print("  DIFFERENT strategy -- rephrase with more context, offer an")
print("  alternative capability, or escalate to a person (M5-L07's")
print("  degrade/escalate/fail choice, applied to a different failure class).")


# ============================================================ 3
rule("3. THE CIRCUIT BREAKER: BOUNDING COST DURING AN OUTAGE")

REQ_PER_SEC = 50
OUTAGE_SECONDS = 120
RETRIES_PER_REQUEST = 3         # 1 try + 2 retries, each doomed during outage
BREAKER_TRIP_AFTER = 5          # consecutive failures before the breaker opens
PROBE_INTERVAL_SECONDS = 30     # how often an open breaker tests upstream

total_requests = REQ_PER_SEC * OUTAGE_SECONDS
print(f"  An upstream dependency is down for {OUTAGE_SECONDS}s. Traffic: "
      f"{REQ_PER_SEC} req/s -> {total_requests:,} requests arrive during "
      f"the outage.\n")

no_breaker_attempts = total_requests * RETRIES_PER_REQUEST
print(f"  WITHOUT a circuit breaker: every request retries up to "
      f"{RETRIES_PER_REQUEST}x (M2-L14's backoff, applied blindly).")
print(f"    wasted upstream attempts: {total_requests:,} x "
      f"{RETRIES_PER_REQUEST} = {no_breaker_attempts:,}")

remaining_seconds = OUTAGE_SECONDS - BREAKER_TRIP_AFTER
probes = remaining_seconds // PROBE_INTERVAL_SECONDS
breaker_attempts = BREAKER_TRIP_AFTER + probes
print(f"\n  WITH a circuit breaker: opens after {BREAKER_TRIP_AFTER} "
      f"consecutive failures, then short-circuits new requests locally")
print(f"  (an instant fallback response, no upstream call) and probes "
      f"upstream once every {PROBE_INTERVAL_SECONDS}s to test recovery.")
print(f"    trip cost:   {BREAKER_TRIP_AFTER} attempts")
print(f"    probe cost:  {remaining_seconds}s remaining / "
      f"{PROBE_INTERVAL_SECONDS}s = {probes} probe attempts")
print(f"    total wasted upstream attempts: "
      f"{BREAKER_TRIP_AFTER} + {probes} = {breaker_attempts}")

reduction = 1 - breaker_attempts / no_breaker_attempts
print(f"\n  Reduction in wasted upstream attempts: {reduction:.2%} "
      f"({no_breaker_attempts:,} -> {breaker_attempts}).")
print(f"\n  Every one of the {total_requests:,} users still gets a response")
print("  in both cases -- the difference is WHERE it comes from. Without a")
print("  breaker, each of them waits through a full retry cycle against a")
print("  dependency that cannot answer. With a breaker, everyone after the")
print("  trip gets an immediate, honest fallback, and the dead dependency")
print("  is bothered only a handful of times instead of tens of thousands.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1's detector and its results on the stated samples,")
print("  and sections 2-3's arithmetic, given the stated rates and")
print("  parameters -- all exact and reproducible.")
print("\n  ILLUSTRATIVE: the specific per-attempt success rates in section 2")
print("  and the traffic/timing parameters in section 3. The SHAPE is the")
print("  point -- transient failures respond to retrying, refusals mostly")
print("  don't, and a breaker's saving grows with outage length and")
print("  traffic. Measure your own rates before setting real thresholds.")
print("\n  NOT SHOWN: a real model's actual refusal phrasing, which varies by")
print("  provider, version and system prompt, and a production-grade")
print("  refusal classifier, which typically needs more than a keyword list")
print("  -- see M5-L13's same lesson about pattern-matching's limits,")
print("  applied here to refusals instead of injected instructions.")

print("\nDone.")
