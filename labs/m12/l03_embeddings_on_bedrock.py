"""M12-L03 lab -- embeddings, and why their version discipline is stricter.
This lab computes:

  1. what happens when two embedding models' vectors are compared,
  2. the cost and time to re-embed a corpus, at four sizes,
  3. batching: throughput and cost against one call per chunk,
  4. dimension choice: storage, search cost and quality trade-off,
  5. the metadata every stored vector needs, and what breaks without it.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m12/l03_embeddings_on_bedrock.py
"""

from __future__ import annotations

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1203)

DIM, LATENT = 64, 8

# A shared latent "meaning" per text, so semantically close texts are close in BOTH
# models -- and each model projects that latent space with its OWN random basis, so
# the two models' output vectors are not comparable. That is the real property.
LATENTS = {
    "refund policy for damaged goods":            [0.9, 0.8, 0.1, 0.0, 0.1, 0.0, 0.0, 0.0],
    "how to return a damaged item":               [0.9, 0.7, 0.2, 0.0, 0.0, 0.1, 0.0, 0.0],
    "office opening hours":                       [0.0, 0.0, 0.1, 0.9, 0.7, 0.0, 0.1, 0.0],
    "annual leave entitlement":                   [0.0, 0.1, 0.0, 0.2, 0.1, 0.9, 0.8, 0.0],
    "my item arrived broken, can I get money back": [0.9, 0.8, 0.2, 0.0, 0.0, 0.0, 0.0, 0.1],
}


def _basis(model_seed: int) -> list[list[float]]:
    r = random.Random(model_seed)
    return [[r.gauss(0, 1) for _ in range(LATENT)] for _ in range(DIM)]


BASES = {11: _basis(11), 22: _basis(22)}


def embed(text: str, model_seed: int) -> list[float]:
    """A stand-in embedding model: shared meaning, model-specific basis."""
    z = LATENTS[text]
    basis = BASES[model_seed]
    v = [sum(b[j] * z[j] for j in range(LATENT)) for b in basis]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ============================================================ 1
rule("1. TWO EMBEDDING MODELS DO NOT SHARE A SPACE")

DOCS = ["refund policy for damaged goods", "how to return a damaged item",
        "office opening hours", "annual leave entitlement"]
QUERY = "my item arrived broken, can I get money back"
MODEL_A, MODEL_B = 11, 22

print(f"  query: {QUERY!r}\n")
print(f"  {'document':<40}{'model A':>10}{'model B':>10}{'A-query vs B-doc':>19}")
for d in DOCS:
    qa, qb = embed(QUERY, MODEL_A), embed(QUERY, MODEL_B)
    da, db = embed(d, MODEL_A), embed(d, MODEL_B)
    print(f"  {d:<40}{cosine(qa, da):>10.3f}{cosine(qb, db):>10.3f}{cosine(qa, db):>19.3f}")
print("\n  The last column is the point. Comparing a vector from model A with a vector")
print("  from model B produces a number -- cosine similarity always produces a")
print("  number -- and it is meaningless. There is no error, no exception and no")
print("  warning: retrieval simply becomes random, and the symptom is 'the assistant")
print("  stopped finding things' with no deploy to blame (M10-L13 section 5.1).")
print("  This is why an embedding model change is a CORPUS MIGRATION, not a config")
print("  change. A generation model can be swapped in an afternoon; an embedding")
print("  model cannot.")


# ============================================================ 2
rule("2. WHAT DOES RE-EMBEDDING COST?")

# [ILLUSTRATIVE rates]
EMBED_PER_M_TOKENS = 0.10
TOKENS_PER_CHUNK = 420
CHUNKS_PER_SECOND = 900          # with batching and parallelism
print(f"  ${EMBED_PER_M_TOKENS}/M tokens, {TOKENS_PER_CHUNK} tokens/chunk, "
      f"{CHUNKS_PER_SECOND} chunks/s sustained [ILLUSTRATIVE]\n")
print(f"  {'corpus':<26}{'chunks':>12}{'embed cost':>13}{'wall time':>14}")
for label, chunks in [("small (10k docs)", 120_000), ("medium (100k docs)", 1_200_000),
                      ("large (1M docs)", 12_000_000), ("very large (10M docs)", 120_000_000)]:
    cost = chunks * TOKENS_PER_CHUNK / 1_000_000 * EMBED_PER_M_TOKENS
    secs = chunks / CHUNKS_PER_SECOND
    hrs = secs / 3600
    wall = f"{hrs:.1f} h" if hrs >= 1 else f"{secs / 60:.0f} min"
    print(f"  {label:<26}{chunks:>12,}{'$' + format(cost, ',.0f'):>13}{wall:>14}")
print("\n  The 'embed cost' column is usually small and the 'wall time' column is not.")
print("  That wall time is your real recovery-time objective for the index (M11-L17")
print("  section 5.7): if the index is lost or invalidated, this is how long you are")
print("  degraded. Keep the previous index until the new one is gated (M10-L14), and")
print("  budget the re-embed before choosing a model you may want to change.")


# ============================================================ 3
rule("3. BATCHING")

CHUNKS = 1_200_000
PER_CALL_MS = 90
STRATEGIES = [
    ("one chunk per call, serial",           1,   1),
    ("one chunk per call, 16 in parallel",   1,  16),
    ("batch of 64, 16 in parallel",         64,  16),
    ("batch of 256, 32 in parallel",       256,  32),
]
print(f"  {CHUNKS:,} chunks, {PER_CALL_MS} ms per call [ILLUSTRATIVE]\n")
print(f"  {'strategy':<36}{'calls':>13}{'wall time':>14}{'vs serial':>12}")
base = None
for label, batch, parallel in STRATEGIES:
    calls = math.ceil(CHUNKS / batch)
    secs = calls * PER_CALL_MS / 1000 / parallel
    base = base or secs
    hrs = secs / 3600
    t = f"{hrs:.1f} h" if hrs >= 1 else f"{secs / 60:.0f} min"
    print(f"  {label:<36}{calls:>13,}{t:>14}{base / secs:>11.0f}x")
print("\n  Batching reduces the number of round trips; parallelism hides the latency")
print("  of each. They multiply, and together they are the difference between a")
print("  re-index that takes a fortnight and one that takes an afternoon.")
print("  The limits are the API's maximum batch size and your throughput quota")
print("  (M12-L12) -- so measure the sustained rate, not the burst.")


# ============================================================ 4
rule("4. DIMENSION CHOICE")

VECTORS = 12_000_000
BYTES_PER_FLOAT = 4
DIMS = [256, 512, 1024, 1536]
print(f"  {VECTORS:,} vectors, {BYTES_PER_FLOAT} bytes per dimension\n")
print(f"  {'dimensions':>12}{'GB stored':>12}{'rel. search cost':>19}{'typical quality':>18}")
for d in DIMS:
    gb = VECTORS * d * BYTES_PER_FLOAT / 1024 ** 3
    print(f"  {d:>12}{gb:>12,.0f}{d / DIMS[0]:>18.1f}x{'higher with d' if d > 256 else 'baseline':>18}")
print("\n  Storage and search cost scale LINEARLY with dimension; quality does not --")
print("  it rises and then flattens, and where it flattens depends on your corpus")
print("  and your queries (M6-L02). Some models support reduced output dimensions,")
print("  which is worth measuring: if 512 retrieves as well as 1536 on YOUR")
print("  evaluation set, you have cut storage and search cost by two thirds for")
print("  nothing. Measure it; do not assume in either direction (M6-L13).")


# ============================================================ 5
rule("5. WHAT EVERY STORED VECTOR MUST CARRY")

METADATA = [
    ("embedding model id and version", "without it, you cannot tell which space a vector is in"),
    ("dimension",                      "a mismatch is the one error you DO get, loudly"),
    ("chunking config version",        "chunk boundaries changed -> different text was embedded"),
    ("source document id AND revision", "the document may have been edited (M10-L13)"),
    ("tenant / permission scope",      "filtering happens at query time (M7-L15, M10-L07)"),
    ("ingestion run id and timestamp",  "which batch produced this, and when"),
    ("text hash",                      "proves what was embedded, without storing it twice"),
]
print(f"  {'field':<36}why")
for field, why in METADATA:
    print(f"  {field:<36}{why}")
print(f"\n  {len(METADATA)} fields. The first is the one that prevents section 1's silent")
print("  failure: if every vector records its model, a mixed index is DETECTABLE")
print("  rather than merely wrong. Make it a hard filter at query time -- refuse to")
print("  compare vectors whose model id differs from the query's -- and the worst")
print("  case becomes an empty result set instead of nonsense (M7-L13).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: the vectors in section 1 are generated deterministically and the")
print("  cosine similarities are computed; every cost, time, ratio and storage")
print("  figure is computed from the values here.")
print("\n  SIMULATED: 'embed()' is a hash-seeded stand-in, not a real embedding model.")
print("  It reproduces the PROPERTY that matters -- same text and model give the")
print("  same vector, different models give unrelated ones -- and nothing else. The")
print("  within-model similarities in section 1 are therefore meaningless as")
print("  semantics; only the cross-model column carries the lesson.")
print("\n  ILLUSTRATIVE: all prices, rates, chunk counts and throughput figures.")
print("\n  NOT SHOWN: the actual embedding API, index construction (M12-L10), and")
print("  retrieval quality measurement (M6-L13).")
print("\nDone.")
