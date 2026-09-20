# M11-L12 — Containers on AWS: ECR, ECS and Fargate

| | |
|---|---|
| **Lesson ID** | M11-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M11-L11](M11-L11-ec2-compute-baseline.md), [M2-L20](../module-02-python-foundations/M2-L20-docker.md) |

---

## 1. Learning objectives

1. **Order** image layers from least to most frequently changed, and quantify what that saves.
2. **Treat image size** as scale-out latency rather than as tidiness.
3. **Distinguish** the execution role from the task role, and diagnose a failure to the right one.
4. **Choose** a rolling-deployment configuration from what capacity you can afford to lose.
5. **Scan and rebuild** base images on a schedule, because the host being managed does not patch your image.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **ECR** | Elastic Container Registry — where your images live, with scanning and lifecycle policies. |
| **ECS** | Elastic Container Service — AWS's container orchestrator. |
| **Fargate** | A launch type where AWS runs the containers; no instances for you to manage. |
| **Task definition** | The immutable spec of a task: image, resources, roles, environment, logging. |
| **Execution role** | The role the **container agent** uses: pull the image, write logs, fetch injected secrets. |
| **Task role** | The role **your application code** uses for its own AWS calls. |
| **Service** | A long-running set of tasks kept at a desired count, with deployment and health settings. |
| **minimumHealthyPercent / maximumPercent** | The capacity floor and ceiling during a rolling deployment. |
| **Multi-stage build** | Building in one image and copying only artefacts into a smaller runtime image. |

---

## 3. Plain-language explanation

### 3.1 Layer order is a build-time decision with a deploy-time cost

§7.1 compares two Dockerfile orderings. With code last, the average build is **14.7 s** and pushes **147 MB**. With code
first, **146.4 s** and **1,384 MB** — **10× slower**, on every commit, because a code change invalidates every layer after
it and dependencies get reinstalled.

The rule: order layers from **least** to **most** frequently changed. Code changes on 96 of 100 builds; dependencies on 8.

### 3.2 Image size is how fast you can respond to load

§7.2: at 250 MB/s, a slim image pulls in **1.7 s** and a kitchen-sink image in **24.4 s** — **23 seconds added to every
scale-out event and every deployment**, on top of the lag in L11 §7.3.

### 3.3 Two roles, and the symptom tells you which

§7.3 attributes seven failures: **4 to the execution role**, 3 to the task role. The diagnostic is simple — **no logs at
all** means the execution role (the agent could not pull, or could not write logs); **`AccessDenied` inside a log line**
means the task role (your code was refused).

The task role is also what bounds an agent's reach, so it is the one that matters for M9-L13 and M12-L08.

### 3.4 Deployment configuration is a statement about what you can lose

§7.4, at a desired count of 12: **50/100** keeps only **6 tasks** running and costs nothing extra; **100/150** keeps all
12 and adds 6; **100/200** keeps 12, adds 12, and finishes in **one batch**; **0/100** takes capacity to **zero**.

### 3.5 A managed host does not patch your image

§7.5: vulnerability counts grow roughly linearly with base-image age — from a handful at one day to hundreds at two
years. Nothing about a running container tells you which row you are on. Fargate patches the *host*; the image is yours
(L01 §7.4).

---

## 4. Analogy

**A pre-packed flight case for a touring band.** Pack the heavy, unchanging gear at the bottom and the set list on top,
and each night you only repack the top. Pack the set list first and you unpack everything every night. A lighter case
loads faster at every venue. The crew's pass (execution role) gets the case into the building; the band's pass (task role)
is what lets them into the studio afterwards — and a refusal at the door tells you which pass was wrong. And a case that
has not been opened since last year still contains last year's problems.

### Where the analogy breaks

- **A flight case is inspected when opened; container images accumulate vulnerabilities while sitting still** in the
  registry, with nobody touching them (§5.6).
- **One case serves one band; one image runs as many tasks as you scale to**, so image size multiplies across every
  scale-out event (§5.3).

---

## 5. Detailed technical explanation

### 5.1 Why containers rather than instances

Against L11's baseline, containers on Fargate remove the host OS from your responsibilities (L01 §7.1), make deployments
image-swaps rather than in-place changes (L11 §5.5), and give each task an identity through the **task role** rather than
an instance role shared by everything on the box.

What you take on: image currency, base-image vulnerabilities, task sizing, and a new set of failure modes at start-up.

Fargate against ECS on EC2: Fargate for almost everything (no capacity management, no host patching); EC2 launch type when
you need GPUs, specific instance types, very large task sizes, or per-host optimisations.

### 5.2 Building images well

`[REAL, computed]` §7.1 — 14.7 s / 147 MB versus 146.4 s / 1,384 MB.

```dockerfile
# stage 1: build
FROM python:3.12-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# stage 2: runtime -- no compilers, no caches
FROM python:3.12-slim
COPY --from=build /install /usr/local
COPY assets/ /app/assets/          # changes occasionally
COPY src/ /app/src/                # changes constantly -- LAST
USER 10001
CMD ["python", "-m", "src.server"]
```

Four practices: **multi-stage** builds so build tools never reach the runtime; **`requirements.txt` copied before the
source**, so dependency layers cache; **`.dockerignore`** so the build context is not the whole repository; and a
**non-root user**.

### 5.3 Image size

`[REAL, computed]` §7.2 — 1.7 s / 6.2 s / 24.4 s to pull.

Size costs you at every scale-out, every deployment, and every rollback — which is exactly when you are in a hurry
(M10-L14). Reduce it by removing build tooling, avoiding a CUDA base image when you are not using a GPU, and keeping
model assets out of the image where they can be loaded from S3 or a cache at start-up (weighing that against a longer
warm-up).

Set an **ECR lifecycle policy** to expire untagged and old images, or the registry grows forever.

### 5.4 The two roles

`[REAL, attributed]` §7.3 — 4 execution, 3 task.

| | Execution role | Task role |
|---|---|---|
| Used by | The ECS container agent | Your application code |
| Typical permissions | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `logs:CreateLogStream`, `logs:PutLogEvents`, `secretsmanager:GetSecretValue` for injected secrets | `s3:GetObject`, `bedrock:InvokeModel`, `dynamodb:*` on named tables — whatever the app does |
| Failure looks like | Task never starts; no logs; "unable to pull image"; "unable to retrieve secret" | `AccessDenied` in an application log line |
| Scope | Small, identical across services | **Least privilege per service** (L04) |

This separation is genuinely useful for AI systems: the task role **is** the agent's permission boundary. An agent that
can call `s3:DeleteObject` can do so because its task role says it can — not because of anything in the prompt (M9-L13).

### 5.5 Rolling deployments

`[REAL, computed]` §7.4.

| Config | Capacity floor | Extra cost | Use when |
|---|---|---|---|
| 50 / 100 | Half | None | Off-peak, tolerant workloads, dev |
| 100 / 150 | Full | +50% briefly | The usual default for production |
| 100 / 200 | Full | +100% briefly | Fast deploys, expensive but safest |
| 0 / 100 | **Zero** | None | Never, for anything users touch |

Pair with: **circuit-breaker rollback** so a failing deployment reverts itself; a deregistration delay set from p99
(L09 §5.6); graceful shutdown on `SIGTERM`; and a **canary** for anything risky (M13-L14).

Remember §7.4's duration column interacts with L11 §7.3's warm-up: a task that takes 95 seconds to be ready makes every
batch at least that long.

### 5.6 Image security and currency

`[REAL, modelled — ILLUSTRATIVE rates]` §7.5.

- **Scan on push and continuously.** Images already in the registry acquire new findings without being touched.
- **Rebuild on a schedule**, not only on code change; nightly or weekly base-image rebuilds keep the count near zero.
- **Fail the build** on critical findings, with a documented exception path.
- **Pin base images by digest** for reproducibility (M10-L13), and update the pin deliberately.
- **Sign images** and verify at deployment where the threat model warrants it.
- **No secrets in images.** Inject at runtime from Secrets Manager or Parameter Store (L17).

### 5.7 Task sizing

Fargate charges for the vCPU and memory you request, per second. L11 §5.4's point applies directly: AI workloads are
memory- and concurrency-bound, so request memory generously and CPU modestly, then verify with a load test (M13-L11).

Watch for the **ephemeral storage** limit if your workload writes temporary files — document parsing and embedding
pipelines do (M7-L03).

### 5.8 Assumptions and limitations

- Layer sizes, change frequencies, pull bandwidth, batch timings and CVE accumulation rates are invented.
- The deployment model is simplified; real ECS batching depends on placement and health-check timing.
- EKS, service discovery, sidecars, Fargate platform versions and image signing mechanics are out of scope.

---

## 6. Worked example — the deploy that took twenty minutes and then failed

**The situation.** A team's assistant service deployed from a single-stage Dockerfile that copied the whole repository at
the second instruction. Deploys took about twenty minutes and were done at the end of the day.

**What was happening.**

1. `COPY . .` before `pip install` meant **every commit invalidated the dependency layer** (§7.1): a full reinstall and a
   1.5 GB push, every time.
2. The image included build tools, a CUDA base for a workload that never used a GPU, and the test suite — **6.1 GB**
   (§7.2), adding ~24 s to every task start.
3. The service ran `minimumHealthyPercent: 100, maximumPercent: 200` with a desired count of 12, so each deploy briefly
   started 12 more tasks, each pulling 6.1 GB.
4. A failed deployment rolled back — by pulling the **previous** 6.1 GB image again, doubling the time to recover
   (M10-L14).
5. The base image had last been rebuilt fourteen months earlier; the first scan enabled reported dozens of high findings
   (§7.5).

**After:** multi-stage build, `.dockerignore`, no CUDA, assets loaded from S3. Image **480 MB**, deploys around three
minutes, rollback under two.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Source copied before dependencies | Copy `requirements.txt` first (§5.2) |
| 2 | Build tools and tests in the runtime image | Multi-stage build; `.dockerignore` |
| 3 | Wrong base image for the workload | Match the base to what the code actually uses |
| 4 | Rollback as slow as deployment | Small images make rollback fast |
| 5 | Base image never rebuilt | Scheduled rebuilds; scan on push and continuously |

**The general rule.** **Image size and layer order are reliability properties: they set how fast you can deploy, scale and
roll back.**

---

## 7. Practical activity

**File:** [`labs/m11/l12_containers_ecr_ecs_fargate.py`](../../labs/m11/l12_containers_ecr_ecs_fargate.py)

**No AWS account, no Docker, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l12_containers_ecr_ecs_fargate.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1112)`; run twice, output
identical.

```text

============================================================================
1. LAYER ORDER DECIDES YOUR BUILD TIME
============================================================================
  order                 avg build s  avg pushed MB   why
  good: code last              14.7            147   only the 6 MB code layer usually rebuilds
  bad: code first             146.4           1384   a code change invalidates EVERYTHING after it

  The rule is: order layers from least to most frequently changed. The code
  layer changes on 96 of 100 builds; the dependency layer on 8. Putting code
  first means every commit reinstalls dependencies and re-pushes ~1.5 GB.
  This is a CI cost, a deploy-latency cost, and an ECR storage cost.

============================================================================
2. IMAGE SIZE IS SCALE-OUT LATENCY
============================================================================
  slim, deps only                              420 MB   pull   1.7 s   scale-out  46.7 s including start
  typical (deps + assets)                    1,560 MB   pull   6.2 s   scale-out  51.2 s including start
  kitchen sink (build tools, CUDA, docs)     6,100 MB   pull  24.4 s   scale-out  69.4 s including start

  at 250 MB/s, the kitchen-sink image adds 23 s
  to every scale-out event and every deployment (M11-L11 section 3).
  Multi-stage builds, no build tools in the runtime layer, and .dockerignore
  are the three changes that recover most of it. Image size is not tidiness;
  it is how fast you can respond to load.

============================================================================
3. EXECUTION ROLE OR TASK ROLE?
============================================================================
  symptom                                                   which role
  the task cannot pull the image from ECR               execution role
  the task starts but cannot write logs                 execution role
  the task cannot read the secret at startup            execution role
  the app gets AccessDenied calling S3                       task role
  the app gets AccessDenied calling Bedrock                  task role
  the app cannot assume a cross-account role                 task role
  the task never starts and there is no log at all      execution role

  execution role: 4/7   task role: 3/7
  The EXECUTION role belongs to the container agent: it pulls the image,
  writes to the log group, and fetches secrets injected at startup. The TASK
  role belongs to YOUR CODE: every AWS call the application makes.
  The diagnostic: no logs at all -> execution role; AccessDenied inside a log
  line -> task role. And the task role is the one that bounds an agent's
  reach, so it is the one that matters for M9-L13 and M12-L08.

============================================================================
4. ROLLING DEPLOYMENT: CAPACITY AND DURATION
============================================================================
  desired count 12, 90 s per batch

  minHealthy / maxPercent           min capacity  extra tasks  batches   duration
  50 / 100  (in-place, cheap)                  6            0        2      180 s
  100 / 150 (one-and-a-half)                  12            6        2      180 s
  100 / 200 (blue/green-ish)                  12           12        1       90 s
  0 / 100   (stop everything)                  0            0        1       90 s

  '50/100' never exceeds the desired count, so it costs nothing extra and
  runs at half capacity during the deployment -- fine at 2am, an outage at
  peak. '100/200' keeps full capacity and briefly doubles the bill. The
  question is not which is 'best' but what you can afford to lose while
  deploying, and deployments are when most incidents start (M10-L14).

============================================================================
5. HOW OLD IS YOUR BASE IMAGE?
============================================================================
  base image policy                     age (days)  critical    high   total
  rebuilt nightly                                1         0       1       9
  rebuilt on every release                      12         0       3      11
  rebuilt when something breaks                190         4      14      43
  pinned two years ago                         730        14      43     171

  [ILLUSTRATIVE accumulation rates.] The shape is what matters: vulnerability
  count grows roughly linearly with base-image age, and nothing about a
  running container tells you which row you are on. Scan on push AND
  continuously (images already in the registry get new CVEs without being
  touched), rebuild on a schedule, and fail the build on critical findings.
  'Serverless containers, so patching is handled' covers the HOST, never the
  image you built (M11-L01 section 4).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every build time, push size, pull time, role attribution, deployment
  duration and capacity figure above is computed from the values here.

  ILLUSTRATIVE: layer sizes, change frequencies, pull bandwidth, batch timing
  and CVE accumulation rates are invented. Measure your own.

  NOT SHOWN: ECS vs EKS selection, service discovery, sidecars, Fargate
  platform versions, and image signing (M11-L18).

Done.
```

### 7.3 Reading the result

**Section 1's two rows** differ only in the order of four lines in a Dockerfile: 14.7 s versus 146.4 s.

**Section 2's third row** is 23 seconds added to every scale-out, on top of L11's 330-second lag.

**Section 3's diagnostic** — no logs versus `AccessDenied` in a log — saves an hour of debugging every time.

**Section 4's last row** shows what `0/100` means: zero capacity, and it is a legal configuration.

---

## 8. Common mistakes and troubleshooting

1. **`COPY . .` before installing dependencies.** §7.1 — 10× slower builds.
2. **Build tools in the runtime image.** §5.2 — use multi-stage.
3. **A GPU base image for a CPU workload.** §6 — gigabytes for nothing.
4. **Confusing the two roles.** §5.4 — the symptom tells you which.
5. **Over-broad task roles.** The task role *is* the agent's permission boundary (M9-L13).
6. **`0/100` or `50/100` deployments at peak.** §7.4.
7. **No deployment circuit breaker.** A failing deploy should revert itself.
8. **Never rebuilding the base image.** §7.5 — findings accumulate while nothing changes.
9. **Secrets baked into images.** Inject at runtime (L17).
10. **No ECR lifecycle policy.** The registry grows forever.

| Symptom | Likely cause | Fix |
|---|---|---|
| Task stops immediately, no logs | Execution role cannot pull or log | Check execution role and log group (§5.4) |
| `AccessDenied` in application logs | Task role too narrow | Add the specific action and resource (L04) |
| Deploys take many minutes | Large image, bad layer order | Multi-stage, reorder, `.dockerignore` |
| Capacity dips during deployment | `minimumHealthyPercent` below 100 | Raise it; accept the extra cost |
| Scan reports hundreds of findings | Base image never rebuilt | Scheduled rebuilds; fail on critical |
| Task runs out of disk | Ephemeral storage limit | Raise it, or stream to S3 (M7-L03) |

---

## 9. Security, privacy, reliability, cost

- **Security.** The task role is the enforcement point for everything an agent can do (M9-L13, M12-L08). Scan images, pin
  digests, run as non-root, and keep secrets out of images.
- **Privacy.** Container logs carry prompts and outputs unless you stop them; apply M10-L13's hash-and-store pattern.
- **Reliability.** Deployment configuration, circuit-breaker rollback and graceful shutdown decide whether deploys cause
  incidents (M10-L14).
- **Cost.** Fargate bills per vCPU-second and GB-second, so task sizing is billing; ECR storage and cross-AZ pull traffic
  are real lines too (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why does copying source before dependencies slow every build?
2. How much time does the kitchen-sink image add to a scale-out?
3. A task never starts and there are no logs. Which role?
4. Which deployment config keeps full capacity and finishes in one batch?
5. Why does a container image accumulate vulnerabilities while untouched?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the code layer's change frequency to 30 and re-read section 1.
2. Add a "model weights baked in (14 GB)" image to §7.2 and compute the scale-out cost.
3. Add two failures from your own experience to §7.3 and attribute them.
4. Add a `75/125` configuration to §7.4 and compute its capacity and duration.
5. Write the multi-stage Dockerfile for a service you run, and measure the size change.

### Exercise 3 — Challenge (~60 min)

1. Write the task role for an AI service with exactly the permissions it needs, and test it (L04).
2. Set up scan-on-push and a scheduled base-image rebuild in CI, failing on critical findings.
3. Measure your real image pull time and add it to your scale-out lag budget.
4. Configure a deployment circuit breaker and prove it rolls back a broken image.
5. Write the runbook step "how to tell which role caused this failure" for your on-call guide.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l12).)*

**Q1.** How should Dockerfile layers be ordered?

- A. Largest layers first, to maximise cache reuse
- B. Alphabetically, for reproducibility
- C. From least to most frequently changed
- D. Application code first, so failures surface early

**Q2.** In §7.1, what was the average build time with code copied first?

- A. 14.7 seconds
- B. 42 seconds
- C. 95 seconds
- D. 146.4 seconds

**Q3.** Why does image size matter beyond storage cost?

- A. Larger images consume more task memory at runtime
- B. It adds pull time to every scale-out, deployment and rollback
- C. ECR charges per pull above a size threshold
- D. Fargate rejects images above a fixed size

**Q4.** A task fails to start and produces no logs at all. Which role is implicated?

- A. The task role
- B. The instance profile
- C. The service-linked role
- D. The execution role

**Q5.** An application logs `AccessDenied` calling Bedrock. Which role?

- A. The task role
- B. The execution role
- C. Both roles equally
- D. The ECS service role

**Q6.** What is the execution role used for?

- A. Pulling the image, writing logs and fetching injected secrets
- B. Signing requests made by the application SDK
- C. Assuming cross-account roles on behalf of the task
- D. Granting the load balancer access to the task

**Q7.** Why does the task role matter for an AI agent?

- A. It determines the model the agent can select
- B. It caps the agent's token budget
- C. It is the boundary on every AWS action the agent can take
- D. It controls which prompts the agent may load

**Q8.** In §7.4, which configuration takes capacity to zero?

- A. 50 / 100
- B. 0 / 100
- C. 100 / 150
- D. 100 / 200

**Q9.** What does `maximumPercent: 200` mean during a deployment?

- A. Capacity may briefly double, so cost does too
- B. Deployments may take twice as long
- C. Twice as many health checks are performed
- D. Twice the memory is allocated per task

**Q10.** Why rebuild base images on a schedule?

- A. Registry lifecycle policies expire unrebuilt images
- B. Layer caches expire after a fixed period
- C. Images acquire new vulnerability findings without being touched
- D. Fargate requires images newer than 90 days

**Q11.** What does Fargate patch on your behalf?

- A. The container image's OS packages
- B. Your application's dependencies
- C. The base image you build from
- D. The underlying host, not your image

**Q12.** Where should secrets be provided to a container?

- A. Baked into the image at build time
- B. Injected at runtime from Secrets Manager or Parameter Store
- C. In the task definition's plain environment variables
- D. In a configuration file committed alongside the Dockerfile

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's container deploys take 18 minutes and rollbacks take
the same. Describe what you would measure and the three changes you would make first.

---

## 12. Revision notes

- **Layer order**: code last → **14.7 s / 147 MB** per build; code first → **146.4 s / 1,384 MB**. Order least- to
  most-frequently-changed.
- **Image size is latency**: **1.7 s / 6.2 s / 24.4 s** to pull — added to every scale-out, deploy and rollback.
- **Execution role** = the agent (pull, logs, injected secrets) → *no logs at all*. **Task role** = your code → *
  `AccessDenied` in a log line*. The task role is the agent's permission boundary.
- **Deployment configs** at desired 12: `50/100` → floor 6, no extra cost; `100/150` → floor 12, +6; `100/200` → floor 12,
  +12, one batch; `0/100` → floor **0**.
- **Findings grow with base-image age**; scan on push **and** continuously, rebuild on a schedule, fail on critical.
- **Fargate patches the host, never your image.**

---

## 13. Completion checklist

- [ ] My Dockerfiles are multi-stage, with dependencies before source and a `.dockerignore`.
- [ ] I know my image size and its contribution to scale-out and rollback time.
- [ ] Execution and task roles are separate, and the task role is least-privilege per service.
- [ ] Deployment configuration keeps the capacity I can afford to lose, with circuit-breaker rollback.
- [ ] Base images are rebuilt on a schedule and scanned continuously; builds fail on critical findings.
- [ ] No secrets are baked into images; ECR has a lifecycle policy.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon ECS Developer Guide — task definitions, execution role vs task role, service deployment configuration and
  circuit breaker `[STABLE]`
- Amazon ECR — image scanning (on push and continuous), lifecycle policies `[STABLE]`
- AWS Fargate — serverless container compute; the host is AWS's responsibility, the image is yours `[STABLE]`
- M2-L20 (Docker fundamentals) and M11-L01 (shared responsibility — what "managed" does not cover) `[STABLE]`
- M9-L13 (permission enforcement outside the model) and M12-L08 (IAM for AI services) `[STABLE]`

---

## 15. Next lesson

→ [M11-L13 — Lambda and API Gateway](M11-L13-lambda-api-gateway.md) removes even the container from your
responsibilities — and introduces cold starts, concurrency limits and timeouts, all of which behave badly for the long,
streaming requests an AI system makes.
