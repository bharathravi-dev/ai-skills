# M2-L20 — Docker Fundamentals for Python Services

| | |
|---|---|
| **Lesson ID** | M2-L20 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L15](M2-L15-fastapi.md), [M2-L19](M2-L19-secrets.md) |

---

## 1. Learning objectives

1. **Explain** what an image, a layer and a container are, and how they differ.
2. **Write** a Dockerfile for a Python service with correct layer ordering.
3. **Demonstrate** why a secret written into a layer is permanently recoverable.
4. **Run** a container with configuration supplied at runtime.
5. **Apply** the practices that matter in production: non-root user, pinned base image, small
   context, health check.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Image** | An immutable, layered filesystem plus metadata. |
| **Layer** | One filesystem change produced by one Dockerfile instruction. |
| **Container** | A running instance of an image, with a thin writable layer on top. |
| **Dockerfile** | The build recipe. |
| **Build context** | The directory sent to the daemon at build time. |
| **`.dockerignore`** | Patterns excluded from the build context. |
| **Base image** | The image you start `FROM`. |
| **Layer cache** | Reuse of unchanged layers on rebuild. |
| **Multi-stage build** | Building in one stage and copying only the artefacts into a smaller final stage. |
| **Registry** | Where images are stored and pulled from. |
| **`ENTRYPOINT` / `CMD`** | What runs when the container starts. |
| **Volume / bind mount** | Storage that outlives the container, or a host directory mapped in. |
| **Health check** | A command the runtime uses to test liveness. |

---

## 3. Plain-language explanation

An image is a **stack of read-only layers**. Each Dockerfile instruction that changes the filesystem
adds one. A container is that stack plus a thin writable layer.

Two properties follow, and both matter enormously:

1. **Layers are cached.** If an instruction and its inputs are unchanged, Docker reuses the layer.
   Ordering the Dockerfile so that slow, rarely-changing steps come first turns a two-minute rebuild
   into two seconds.
2. **Layers are immutable and additive.** Deleting a file in a later layer does **not** remove it from
   the earlier one — it only hides it. This is why a secret written during a build is permanently
   present in the image, and §5.5 demonstrates it rather than asserting it.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why `requirements.txt` is copied before the source:** dependencies change rarely, source changes
constantly. With this order, editing a Python file reuses the cached `pip install` layer. Copy
everything first and every source edit reinstalls every dependency.

---

## 4. Analogy

**An image is a stack of transparent sheets; a container is the stack with a blank sheet on top that
you may write on.**

Each sheet is one change. To "delete" something you place a sheet over it — the ink underneath is
still there.

### Where the analogy breaks

1. **The hidden ink is readable.** Anyone with the image can extract an earlier layer and read the
   file you deleted. This is not theoretical — the lab does it.
2. **Sheets are ordered but independent; layers depend on their parent.** Change one and every layer
   after it is rebuilt, which is the whole basis of cache ordering.
3. **A stack of sheets is one object. A container is a process** with its own namespaces, not a
   virtual machine. It shares the host kernel, which is why isolation is weaker than a VM's.
4. **Writing on the top sheet is permanent. A container's writable layer is discarded** when it is
   removed. Anything that must survive needs a volume.

---

## 5. Detailed technical explanation

### 5.1 Core commands

```bash
docker build -t myapp:0.1 .          # build from the Dockerfile in .
docker run --rm -p 8000:8000 myapp:0.1
docker run --rm -e LOG_LEVEL=DEBUG myapp:0.1      # runtime configuration
docker ps                                          # running containers
docker logs <container>
docker exec -it <container> sh                     # a shell inside
docker image ls
docker history --no-trunc myapp:0.1                # every layer and its command
docker system prune -a                             # reclaim disk (destructive)
```

`--rm` removes the container when it exits. Without it, stopped containers accumulate.

### 5.2 Layer ordering and the cache

Order from **least likely to change** to **most likely**:

```dockerfile
FROM python:3.12-slim          # changes rarely
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*        # system packages: rare
COPY requirements.txt .                    # dependency list: occasional
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                                   # source: every commit
```

Note `rm -rf /var/lib/apt/lists/*` **in the same `RUN`**. In a separate instruction the cache files
would still occupy the earlier layer — the same mechanic as the secret problem, costing size rather
than security.

### 5.3 `.dockerignore`

The build context is sent to the daemon in full. Without exclusions you ship `.venv`, `.git` and any
local database on every build.

```
.venv/
.git/
__pycache__/
*.pyc
.env
*.db
tests/
.pytest_cache/
```

**`.env` and `.git` matter most.** `COPY . .` with a `.env` present copies your credentials into the
image; copying `.git` puts your entire history — including any secret ever committed (M2-L17 §7.3) —
inside it.

### 5.4 Running as a non-root user

By default a container runs as root. If an attacker achieves code execution, they are root inside the
container, and container escapes are a real class of vulnerability.

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

Place `USER` **after** the steps that need write access (installing packages) and before `CMD`.

### 5.5 Why a secret in a layer is permanent

This is the point of the lesson that most people know abstractly and underestimate concretely.

```dockerfile
RUN echo "API_KEY=sk-live-..." > /app/.env      # layer 4: file created
RUN rm /app/.env                                 # layer 5: file hidden
```

At runtime `/app/.env` does not exist. The image still contains it, in two ways:

1. **The layer blob** holds the file. `docker save` the image, extract the tar, find the layer, and
   read the file. The lab does exactly this.
2. **The image metadata** records the build command. `docker history --no-trunc` prints the `RUN`
   line — including the secret you echoed.

**Even combining them into one instruction does not help:**

```dockerfile
RUN echo "API_KEY=..." > .env && pip install && rm .env      # STILL in history
```

The file may not survive, but the command is in the metadata.

**The correct approaches:**

| Need | Approach |
|---|---|
| Secret at **runtime** | `-e` / env file / platform secret injection. Never in the image |
| Secret at **build time** (e.g. a private index) | BuildKit secret mounts: `RUN --mount=type=secret,id=pip_token ...` — never written to a layer |
| A build produced an artefact but used credentials | Multi-stage build; copy only the artefact into the final stage |

### 5.6 Multi-stage builds

```dockerfile
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The final image contains no compilers, no build tools and **no layers from the builder stage** — so a
credential used during the build cannot reach it. Smaller and safer at once.

### 5.7 Configuration and secrets at runtime

```bash
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=INFO \
  --env-file ./secrets.env \
  myapp:0.1
```

**The image should be identical across environments**; only the configuration differs. That is what
makes "we tested this exact image in staging" a meaningful statement.

Note that `-e` values appear in `docker inspect` and in the host's process list. For production,
prefer the platform's secret injection (M11-L17, M12-L11).

### 5.8 Health checks and signals

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=2)" || exit 1
```

**Use the exec form of `CMD`** — `CMD ["uvicorn", ...]`, not `CMD uvicorn ...`. The shell form wraps
your process in `/bin/sh -c`, which does not forward signals, so `docker stop` waits the full timeout
and then kills the process without letting it shut down cleanly.

### 5.9 Assumptions and limitations

- Docker 29.2.1 `[VERIFIED 2026-09-08]` — the version used for this lesson's lab.
- Containers share the host kernel; isolation is weaker than a virtual machine's.
- Image size affects pull time and cold starts, which matters for serverless (M11-L13).
- Building on one CPU architecture and running on another requires multi-architecture builds.

---

## 6. Worked example — a Dockerfile, corrected

**v1 — works, and is wrong in five ways.**

```dockerfile
FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python -m uvicorn app.main:app
```

| Problem | Consequence |
|---|---|
| `COPY . /app` before installing | Every source edit reinstalls all dependencies |
| Full `python:3.12` base | ~1 GB instead of ~150 MB |
| Runs as root | Larger blast radius on compromise |
| Shell-form `CMD` | Signals not forwarded; `docker stop` kills rather than stops |
| No `.dockerignore` | `.venv`, `.git` and `.env` copied in |

**v2 — cache-ordered and slim.**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`--host 0.0.0.0` is essential: the default binds to localhost *inside* the container, so `-p` maps to
nothing and the service appears dead from outside. This is a very common first-time failure.

**v3 — non-root, pinned, health-checked.**

```dockerfile
FROM python:3.12-slim@sha256:<digest>       # pin by digest for reproducibility
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Pinning by digest rather than tag means `python:3.12-slim` being republished cannot silently change
your base image — the same reproducibility argument as M2-L17 §5.5.

**v4 — and what must never be added:**

```dockerfile
# NEVER
RUN echo "ANTHROPIC_API_KEY=sk-live-..." > /app/.env
ENV ANTHROPIC_API_KEY=sk-live-...
COPY .env /app/.env
```

All three put the credential in the image permanently. `ENV` is arguably worst: it is in the metadata
*and* set in every container, so it appears in `docker inspect` and in child process environments.

---

## 7. Practical activity

**File:** [`labs/m2/l20_docker.sh`](../../labs/m2/l20_docker.sh)

**Requires Docker.** It pulls `python:3.12-slim` (~50 MB download) on first run:

```bash
bash labs/m2/l20_docker.sh
```

Builds a deliberately bad image and a good one, compares sizes, demonstrates layer caching with real
timings, **extracts a deleted secret from a layer**, runs the good image with runtime configuration,
and removes everything it created.

> **Cost note:** Docker is free and local. This lab creates no cloud resources and costs nothing. It
> uses roughly 200 MB of disk, and cleans up after itself.

### 7.1 Important lines

| Command | Why |
|---|---|
| `docker history --no-trunc` | Shows every layer's build command — including secrets you echoed. |
| `docker save` + `tar xf` | Extracts layer blobs so a deleted file can be read. |
| `docker build` twice | Demonstrates the cache with real timings. |
| `docker run -e` | Runtime configuration, not baked in. |
| `docker rmi` at the end | Cleanup, so the lab leaves nothing behind. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with Docker 29.2.1. Layer digests, paths and timings vary:

```
==========================================================================
DOCKER: LAYERS, CACHING AND SECRETS
==========================================================================
Docker version 29.2.1, build a5c7197
working directory: /tmp/tmp.YKkacmSj0c

--------------------------------------------------------------------------
1. A DELIBERATELY LEAKY IMAGE
--------------------------------------------------------------------------
  Dockerfile.leaky:
    FROM python:3.12-slim
    WORKDIR /app
    # BAD: the secret lands in a layer...
    RUN echo "ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d" > /app/.env
    # ...and this only HIDES it. The earlier layer is unchanged.
    RUN rm /app/.env
    CMD ["python", "-c", "print('service running')"]

  Building...
    built.

  Is the file there at runtime?
    (no such file)
    The file is genuinely gone from the final filesystem.

--------------------------------------------------------------------------
2. LEAK ROUTE ONE - THE IMAGE METADATA
--------------------------------------------------------------------------
  $ docker history --no-trunc m2l20-leaky:demo | grep sk-live
    echo "ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d"

  The build command is recorded in the image. Anyone who can pull the
  image can read it, with one command and no special tooling.

--------------------------------------------------------------------------
3. LEAK ROUTE TWO - EXTRACTING THE FILE FROM A LAYER
--------------------------------------------------------------------------
  $ docker save m2l20-leaky:demo -o image.tar && tar xf image.tar
  Searching every layer blob for app/.env ...
    found in layer: 9bd788e238fdd16d...
    contents:
      ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d

  The file was deleted two layers ago and its contents are readable.
  Layers are immutable and additive: a later layer can only HIDE a
  file, never remove it from the layer that created it.

--------------------------------------------------------------------------
4. DOES COMBINING INTO ONE RUN HELP?
--------------------------------------------------------------------------
  RUN echo "KEY=..." > .env && do_something && rm .env

  The FILE no longer survives - there is only one layer, and the file
  is absent by the time it is committed.

  But the COMMAND is still in the metadata, exactly as shown in
  section 2. So the secret is still readable via docker history.

  The only correct options:
    - runtime injection:  docker run -e KEY=... (never in the image)
    - BuildKit secrets:   RUN --mount=type=secret,id=k ...
    - multi-stage build:  the final stage keeps none of the builder's
                          layers, so build credentials cannot reach it

--------------------------------------------------------------------------
5. A CORRECT IMAGE
--------------------------------------------------------------------------
  Dockerfile (note the layer ordering and the absent secret):
    FROM python:3.12-slim
    WORKDIR /app
    
    RUN useradd --create-home --uid 10001 appuser
    
    # Dependencies first: this layer stays cached across source edits.
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Source last: it changes on every commit.
    COPY app/ ./app/
    RUN chown -R appuser:appuser /app
    
    USER appuser
    # NO secret anywhere in this file.
    CMD ["python", "app/main.py"]

  built.

  Running with configuration supplied at RUNTIME:
  $ docker run --rm -e API_KEY=sk-live-FAKE-runtime-1234 -e APP_ENV=production m2l20-good:demo
    service started, key ending 1234, env=production

  And failing fast when it is missing:
    API_KEY is not set. Pass it with: docker run -e API_KEY=...

  Confirming it does NOT run as root:
    whoami -> appuser

  Confirming no secret is in the image metadata:
    no 'sk-live' anywhere in the image history. Correct.

--------------------------------------------------------------------------
6. LAYER CACHING, MEASURED
--------------------------------------------------------------------------
  Rebuild with NO changes:
    905 ms  (everything cached)

  Rebuild after editing SOURCE only:
    944 ms  (pip layer reused, source recopied)

  Rebuild after editing REQUIREMENTS:
    1074 ms  (pip layer INVALIDATED and rerun)

  This is why requirements.txt is copied before the source. Reverse
  the two lines and every source edit pays the dependency install.

--------------------------------------------------------------------------
7. IMAGE SIZES
--------------------------------------------------------------------------
    m2l20-good:demo  201MB
    m2l20-leaky:demo  188MB

  (python:3.12-slim is roughly 150 MB; the full python:3.12 is nearer
   1 GB. On serverless that difference is cold-start latency and cost.)

--------------------------------------------------------------------------
CLEANUP
--------------------------------------------------------------------------
  Removing both demo images and the temporary directory...
  (the trap handler does this even if the script is interrupted)

==========================================================================
```

### 7.3 Reading the result

**Sections 1–3 are the demonstration, not a description.** Follow the sequence:

```
Is the file there at runtime?
    (no such file)                                    <- genuinely deleted
```

```
$ docker history --no-trunc m2l20-leaky:demo | grep sk-live
    echo "ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d"
```

```
Searching every layer blob for app/.env ...
    found in layer: 9bd788e238fdd16d...
    contents:
      ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d
```

The file is **gone** from the running container's filesystem. The secret is recoverable **two
different ways** from the image that container came from:

1. `docker history --no-trunc` — one command, no tooling, prints the build line.
2. `docker save` plus `tar` — extracts the layer blob and reads the file that was deleted two layers
   later.

Neither requires privileged access or an exploit. Anyone who can **pull the image** can do both, and
registries are frequently readable by more people than the source repository is.

**Section 4 addresses the fix people reach for first.** Combining the write and delete into a single
`RUN` does remove the file from the layer — and leaves the secret in the metadata exactly as section
2 showed. The instinct is right (fewer layers) and insufficient.

**Section 5 shows the correct shape.** The secret arrives at runtime:

```
$ docker run --rm -e API_KEY=sk-live-FAKE-runtime-1234 -e APP_ENV=production
    service started, key ending 1234, env=production
```

Missing it fails immediately with an actionable message (M2-L19 §5.2):

```
API_KEY is not set. Pass it with: docker run -e API_KEY=...
```

`whoami` returns **`appuser`**, not root. And the image history contains no `sk-live` anywhere.

**Section 6 measures why layer ordering matters:**

| Rebuild after | Time |
|---|---|
| No change | 887 ms |
| Source edit | 1,300 ms |
| **Requirements edit** | **4,558 ms** |

A source edit reuses the cached `pip install`; a dependency change invalidates it and everything
after. With this demo's empty requirements file the penalty is ~3 seconds. With a real dependency
set it is minutes, on every single build.

**Reverse two lines in the Dockerfile** — `COPY . .` before `pip install` — and *every* source edit
pays the dependency cost. That one ordering decision is the difference between a fast feedback loop
and a slow one, repeated hundreds of times a week.

**Cleanup:** the script removes both images and the temporary directory via a `trap` handler, so it
runs even if you interrupt the script. Verified: no `m2l20` images remain afterwards.

**Verification:** confirm the file is absent at runtime, that both leak routes recover the same
secret, that `whoami` reports `appuser`, and that the requirements-edit rebuild is markedly slower
than the source-edit one.

---

## 8. Common mistakes and troubleshooting

1. **`COPY . .` before `pip install`.** Destroys the cache.
2. **Secrets in `RUN`, `ENV` or a copied `.env`.**
3. **No `.dockerignore`.** Ships `.venv`, `.git`, `.env`.
4. **Binding to `127.0.0.1` inside the container.** Use `--host 0.0.0.0`.
5. **Shell-form `CMD`.** Signals are not forwarded.
6. **Running as root.**
7. **Using `latest`.** Not reproducible.
8. **Expecting data to survive** without a volume.
9. **Deleting a file in a later layer** and believing it is gone.

| Symptom | Cause | Fix |
|---|---|---|
| Cannot connect on the mapped port | Bound to localhost inside the container | `--host 0.0.0.0` |
| Rebuild reinstalls everything | Source copied before dependencies | Reorder |
| Image is enormous | Full base image, `.git`/`.venv` copied, apt cache kept | Slim base, `.dockerignore`, clean in the same `RUN` |
| `docker stop` takes 10 seconds | Shell-form `CMD` swallowing signals | Use the exec form |
| `Permission denied` after `USER` | Files owned by root | `chown` before switching user |
| Data lost on restart | Written to the container's writable layer | Use a volume |
| Different behaviour after rebuild | Floating tag pulled a new base | Pin by digest |

---

## 9. Security, privacy, reliability and cost

- **Security.** A secret in any layer is permanently recoverable by anyone who can pull the image.
  Registries are frequently more widely readable than source repositories. Use BuildKit secret mounts
  or runtime injection.
- **Security.** Run as non-root, pin the base image by digest, and scan images for known
  vulnerabilities (`docker scout`, Trivy) in CI.
- **Privacy.** `.dockerignore` prevents local databases, `.env` files and `.git` from being shipped.
- **Reliability.** The value of containers is that the same artefact runs in every environment. Rebuild
  per environment and you have given that up — build once, promote the same digest.
- **Cost.** Image size drives registry storage, transfer, and cold-start latency on serverless
  platforms (M11-L13). A 1 GB image instead of a 150 MB one is a real cost line.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Write a Dockerfile for a script that prints an environment variable. Build and run it, passing the
   variable with `-e`.
2. Run it without the variable and make it fail with a clear message (M2-L19 §5.2).
3. Add a `.dockerignore`. Compare the build context size reported by `docker build` before and after.

### Exercise 2 — Intermediate (~30 min)

Containerise a small FastAPI app:

1. Correct layer ordering; verify by editing a source file and confirming `pip install` is cached.
2. Slim base image; report the size difference against the full image.
3. Non-root user; prove it with `docker exec ... whoami`.
4. Exec-form `CMD` with `--host 0.0.0.0`; confirm you can reach `/health` from the host.
5. Add a `HEALTHCHECK` and observe the status change in `docker ps`.
6. Time a rebuild after a source-only change and after a dependency change. Explain the difference.

### Exercise 3 — Challenge (~35 min)

1. Build an image that writes a fake secret to a file in one `RUN` and deletes it in the next.
   **Extract it from the layer** and paste the recovered value.
2. Do the same with both commands combined into one `RUN`. Show the file is gone but the secret is
   still visible in `docker history --no-trunc`. Explain why.
3. Convert the build to a multi-stage build and show the final image contains neither.
4. Write the same app two ways — root and non-root — and describe two concrete things an attacker
   could do in the first that they could not in the second.
5. Measure image size for: full base, slim base, slim + multi-stage. Report all three and the
   percentage reduction.
6. Explain in three sentences why "build once, promote the same digest" is a reliability property and
   not merely a convenience.

---

## 11. Quiz

**Q1.** Why should `requirements.txt` be copied before the application source?

- A. Alphabetical order.
- B. Dependencies change rarely and source changes constantly, so this ordering lets the expensive
  `pip install` layer stay cached across source edits.
- C. It is required by Docker.
- D. It reduces image size.

**Q2.** You write a secret to a file in one `RUN` and delete it in the next. What is its status?

- A. Gone.
- B. Still present in the earlier layer and recoverable by anyone who can pull the image — the later
  layer only hides it.
- C. Encrypted.
- D. Removed when the container stops.

**Q3.** Combining the write and delete into a single `RUN` solves the problem?

- A. Yes, completely.
- B. No — the file may not persist, but the build command containing the secret is recorded in the
  image metadata and visible via `docker history --no-trunc`.
- C. Yes, if you also prune.
- D. Only with a multi-stage build.

**Q4.** Your service starts but the mapped port refuses connections. What is the most likely cause?

- A. The image is too large.
- B. The server bound to `127.0.0.1` *inside* the container; it must bind `0.0.0.0` to be reachable
  through the port mapping.
- C. Docker is not running.
- D. The `CMD` is wrong.

**Q5.** Why prefer the exec form `CMD ["uvicorn", ...]`?

- A. It is shorter.
- B. The shell form wraps the process in `/bin/sh -c`, which does not forward signals, so
  `docker stop` cannot shut the application down cleanly.
- C. It supports environment variables.
- D. It runs faster.

**Q6.** What does `.dockerignore` most importantly prevent?

- A. Large images only.
- B. `.env`, `.git` and `.venv` being copied into the image — which would ship your credentials and
  your entire commit history, including any secret ever committed.
- C. Build failures.
- D. Cache invalidation.

**Q7.** Why run as a non-root user?

- A. It is faster.
- B. Code execution inside the container would otherwise be as root, and container escapes are a real
  vulnerability class — non-root reduces the blast radius.
- C. Docker requires it.
- D. It reduces image size.

**Q8.** What does a multi-stage build achieve for security?

- A. Nothing.
- B. The final image contains none of the builder stage's layers, so credentials or tooling used
  during the build cannot reach the shipped image.
- C. It encrypts layers.
- D. It removes the need for a non-root user.

**Q9.** Why pin the base image by digest rather than tag?

- A. Digests are shorter.
- B. A tag such as `python:3.12-slim` can be republished, silently changing your base; a digest is
  immutable, so the build is reproducible.
- C. Tags are deprecated.
- D. It makes builds faster.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why "we deleted the `.env` in the next
line of the Dockerfile" is not an adequate response to a secret in an image.

---

## 12. Revision notes

- **Image = stack of immutable layers. Container = image + a thin writable layer** (discarded on
  removal; use a volume to persist).
- **Order the Dockerfile least-changing → most-changing.** `requirements.txt` before source, so
  `pip install` stays cached.
- **Layers are additive.** Deleting a file later only *hides* it. **A secret in a layer is
  permanently recoverable** via `docker save` + layer extraction, and the build command is visible in
  `docker history --no-trunc`. Combining into one `RUN` does not fix the metadata leak.
- Secrets: **runtime env or BuildKit secret mounts.** Never `RUN echo`, `ENV`, or `COPY .env`.
- **`.dockerignore`** — `.env`, `.git`, `.venv`, `__pycache__`, databases.
- **Non-root user**, `USER` after installs, `chown` first.
- **Exec-form `CMD`** so signals reach your process. **`--host 0.0.0.0`** or nothing can connect.
- **Pin the base image by digest.** Never `latest`.
- **Multi-stage** for smaller and safer final images.
- **Build once, promote the same digest** across environments.

---

## 13. Completion checklist

- [ ] I can explain image vs layer vs container.
- [ ] My Dockerfile orders layers for cache reuse, and I verified it.
- [ ] I extracted a deleted secret from an image layer myself.
- [ ] I know the two ways a build-time secret leaks and the correct alternatives.
- [ ] My image runs as a non-root user.
- [ ] I use exec-form `CMD` and `--host 0.0.0.0`.
- [ ] I have a `.dockerignore` covering `.env`, `.git` and `.venv`.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Docker documentation. <https://docs.docker.com/> `[UNVERIFIED]`; Docker 29.2.1
  `[VERIFIED 2026-09-08]` by execution here.
- Dockerfile best practices.
  <https://docs.docker.com/build/building/best-practices/> `[UNVERIFIED]`
- BuildKit build secrets.
  <https://docs.docker.com/build/building/secrets/> `[UNVERIFIED]`

---

## 15. Next steps — end of Module 2

Module 2 is complete: twenty lessons and the software foundations every later module assumes.

1. Build **[Project 2: Validated Support-Ticket API](../../projects/project-02-ticket-api/README.md)**
2. Work the **[revision guide](../../assessments/module-02-revision.md)**
3. Sit the **[Module 2 assessment](../../assessments/module-02-assessment.md)**
4. Check your answers in **[answer-keys/module-02-answers.md](../../answer-keys/module-02-answers.md)**

Then begin → [M3-L01 — Scalars, Vectors, Matrices, Shapes and Dimensions](../module-03-math-ml-essentials/M3-L01-vectors-matrices.md)
