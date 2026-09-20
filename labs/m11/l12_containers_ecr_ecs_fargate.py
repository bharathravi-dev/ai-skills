"""M11-L12 lab -- images, roles and rolling deployments, computed.
This lab computes:

  1. how Dockerfile layer ORDER changes rebuild and push times,
  2. image size against pull time and scale-out lag,
  3. execution role vs task role: which one a failure actually implicates,
  4. rolling deployment capacity and duration under four ECS configurations,
  5. base-image age against the vulnerabilities a scan will report.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l12_containers_ecr_ecs_fargate.py
"""

from __future__ import annotations

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1112)

# ============================================================ 1
rule("1. LAYER ORDER DECIDES YOUR BUILD TIME")

# layer, MB, seconds to build, how often the layer's inputs change per 100 builds
LAYERS = {
    "base image (python:3.12-slim)": (120,  0,  0),
    "OS packages (apt-get)":         (180, 42,  2),
    "python dependencies (pip)":     (840, 95,  8),
    "model/tokeniser assets":        (410, 12,  4),
    "application code":              (  6,  3, 96),
}
ORDERS = {
    "good: code last":  ["base image (python:3.12-slim)", "OS packages (apt-get)",
                         "python dependencies (pip)", "model/tokeniser assets", "application code"],
    "bad: code first":  ["base image (python:3.12-slim)", "application code",
                         "OS packages (apt-get)", "python dependencies (pip)", "model/tokeniser assets"],
}
print(f"  {'order':<20}{'avg build s':>13}{'avg pushed MB':>15}   why")
for label, order in ORDERS.items():
    build_s = pushed_mb = 0.0
    for i, layer in enumerate(order):
        # a layer rebuilds if it changes OR any earlier layer changed
        p_changed = 1 - math.prod(1 - LAYERS[l][2] / 100 for l in order[:i + 1])
        build_s += LAYERS[layer][1] * p_changed
        pushed_mb += LAYERS[layer][0] * p_changed
    why = "only the 6 MB code layer usually rebuilds" if "good" in label \
        else "a code change invalidates EVERYTHING after it"
    print(f"  {label:<20}{build_s:>13.1f}{pushed_mb:>15.0f}   {why}")
print("\n  The rule is: order layers from least to most frequently changed. The code")
print("  layer changes on 96 of 100 builds; the dependency layer on 8. Putting code")
print("  first means every commit reinstalls dependencies and re-pushes ~1.5 GB.")
print("  This is a CI cost, a deploy-latency cost, and an ECR storage cost.")


# ============================================================ 2
rule("2. IMAGE SIZE IS SCALE-OUT LATENCY")

PULL_MBPS = 250.0
IMAGES = {"slim, deps only": 420, "typical (deps + assets)": 1560,
          "kitchen sink (build tools, CUDA, docs)": 6100}
for name, mb in IMAGES.items():
    pull_s = mb / PULL_MBPS
    print(f"  {name:<42}{mb:>6,} MB   pull {pull_s:>5.1f} s   "
          f"scale-out {pull_s + 45:>5.1f} s including start")
print(f"\n  at {PULL_MBPS:.0f} MB/s, the kitchen-sink image adds "
      f"{(IMAGES['kitchen sink (build tools, CUDA, docs)'] - IMAGES['slim, deps only']) / PULL_MBPS:.0f} s")
print("  to every scale-out event and every deployment (M11-L11 section 3).")
print("  Multi-stage builds, no build tools in the runtime layer, and .dockerignore")
print("  are the three changes that recover most of it. Image size is not tidiness;")
print("  it is how fast you can respond to load.")


# ============================================================ 3
rule("3. EXECUTION ROLE OR TASK ROLE?")

FAILURES = [
    ("the task cannot pull the image from ECR",         "execution role"),
    ("the task starts but cannot write logs",           "execution role"),
    ("the task cannot read the secret at startup",      "execution role"),
    ("the app gets AccessDenied calling S3",            "task role"),
    ("the app gets AccessDenied calling Bedrock",       "task role"),
    ("the app cannot assume a cross-account role",      "task role"),
    ("the task never starts and there is no log at all", "execution role"),
]
print(f"  {'symptom':<52}{'which role':>16}")
for symptom, role in FAILURES:
    print(f"  {symptom:<52}{role:>16}")
exec_n = sum(1 for _, r in FAILURES if r == "execution role")
print(f"\n  execution role: {exec_n}/{len(FAILURES)}   task role: {len(FAILURES) - exec_n}/{len(FAILURES)}")
print("  The EXECUTION role belongs to the container agent: it pulls the image,")
print("  writes to the log group, and fetches secrets injected at startup. The TASK")
print("  role belongs to YOUR CODE: every AWS call the application makes.")
print("  The diagnostic: no logs at all -> execution role; AccessDenied inside a log")
print("  line -> task role. And the task role is the one that bounds an agent's")
print("  reach, so it is the one that matters for M9-L13 and M12-L08.")


# ============================================================ 4
rule("4. ROLLING DEPLOYMENT: CAPACITY AND DURATION")

DESIRED = 12
BATCH_S = 90         # time for one batch to start, warm up and pass health checks
CONFIGS = [
    ("50 / 100  (in-place, cheap)",   50, 100),
    ("100 / 150 (one-and-a-half)",   100, 150),
    ("100 / 200 (blue/green-ish)",   100, 200),
    ("0 / 100   (stop everything)",    0, 100),
]
print(f"  desired count {DESIRED}, {BATCH_S} s per batch\n")
print(f"  {'minHealthy / maxPercent':<32}{'min capacity':>14}{'extra tasks':>13}"
      f"{'batches':>9}{'duration':>11}")
for label, min_pct, max_pct in CONFIGS:
    min_cap = DESIRED * min_pct // 100
    headroom = DESIRED * max_pct // 100 - DESIRED
    batch = max(1, headroom if headroom else DESIRED - min_cap)
    batches = math.ceil(DESIRED / batch)
    print(f"  {label:<32}{min_cap:>14}{headroom:>13}{batches:>9}{batches * BATCH_S:>9} s")
print("\n  '50/100' never exceeds the desired count, so it costs nothing extra and")
print("  runs at half capacity during the deployment -- fine at 2am, an outage at")
print("  peak. '100/200' keeps full capacity and briefly doubles the bill. The")
print("  question is not which is 'best' but what you can afford to lose while")
print("  deploying, and deployments are when most incidents start (M10-L14).")


# ============================================================ 5
rule("5. HOW OLD IS YOUR BASE IMAGE?")

IMAGES_AGE = [("rebuilt nightly", 1), ("rebuilt on every release", 12),
              ("rebuilt when something breaks", 190), ("pinned two years ago", 730)]
print(f"  {'base image policy':<36}{'age (days)':>12}{'critical':>10}{'high':>8}{'total':>8}")
for label, age in IMAGES_AGE:
    critical = int(age * 0.018 + rng.random() * 2)
    high = int(age * 0.055 + rng.random() * 4)
    total = int(age * 0.22 + rng.random() * 12)
    print(f"  {label:<36}{age:>12}{critical:>10}{high:>8}{total:>8}")
print("\n  [ILLUSTRATIVE accumulation rates.] The shape is what matters: vulnerability")
print("  count grows roughly linearly with base-image age, and nothing about a")
print("  running container tells you which row you are on. Scan on push AND")
print("  continuously (images already in the registry get new CVEs without being")
print("  touched), rebuild on a schedule, and fail the build on critical findings.")
print("  'Serverless containers, so patching is handled' covers the HOST, never the")
print("  image you built (M11-L01 section 4).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every build time, push size, pull time, role attribution, deployment")
print("  duration and capacity figure above is computed from the values here.")
print("\n  ILLUSTRATIVE: layer sizes, change frequencies, pull bandwidth, batch timing")
print("  and CVE accumulation rates are invented. Measure your own.")
print("\n  NOT SHOWN: ECS vs EKS selection, service discovery, sidecars, Fargate")
print("  platform versions, and image signing (M11-L18).")
print("\nDone.")
