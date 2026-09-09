#!/usr/bin/env bash
# M2-L20: layers, caching, and why a deleted secret stays in an image.
#
#     bash labs/m2/l20_docker.sh
#
# Requires Docker. Pulls python:3.12-slim on first run (~50 MB).
# Creates a temporary directory and removes every image it builds.
# Costs nothing: everything is local.

set -u
LINE="--------------------------------------------------------------------------"
WORK="$(mktemp -d)"
BAD_TAG="m2l20-leaky:demo"
GOOD_TAG="m2l20-good:demo"

cleanup() {
  docker rmi -f "$BAD_TAG" "$GOOD_TAG" >/dev/null 2>&1
  rm -rf "$WORK"
}
trap cleanup EXIT

section() { echo; echo "$LINE"; echo "$1"; echo "$LINE"; }

echo "=========================================================================="
echo "DOCKER: LAYERS, CACHING AND SECRETS"
echo "=========================================================================="
docker --version
echo "working directory: $WORK"

cd "$WORK" || exit 1

# ---------------------------------------------------------------------------
section "1. A DELIBERATELY LEAKY IMAGE"
cat > Dockerfile.leaky <<'EOF'
FROM python:3.12-slim
WORKDIR /app
# BAD: the secret lands in a layer...
RUN echo "ANTHROPIC_API_KEY=sk-live-FAKE-LEAKED-IN-LAYER-9f8e7d" > /app/.env
# ...and this only HIDES it. The earlier layer is unchanged.
RUN rm /app/.env
CMD ["python", "-c", "print('service running')"]
EOF
echo "  Dockerfile.leaky:"
sed 's/^/    /' Dockerfile.leaky
echo
echo "  Building..."
docker build -q -f Dockerfile.leaky -t "$BAD_TAG" . >/dev/null 2>&1 && echo "    built."

echo
echo "  Is the file there at runtime?"
docker run --rm "$BAD_TAG" sh -c "cat /app/.env 2>/dev/null || echo '(no such file)'" \
  | sed 's/^/    /'
echo "    The file is genuinely gone from the final filesystem."

# ---------------------------------------------------------------------------
section "2. LEAK ROUTE ONE - THE IMAGE METADATA"
echo "  \$ docker history --no-trunc $BAD_TAG | grep sk-live"
docker history --no-trunc "$BAD_TAG" 2>/dev/null \
  | grep -o 'echo "ANTHROPIC_API_KEY=[^"]*"' | head -1 | sed 's/^/    /'
echo
echo "  The build command is recorded in the image. Anyone who can pull the"
echo "  image can read it, with one command and no special tooling."

# ---------------------------------------------------------------------------
section "3. LEAK ROUTE TWO - EXTRACTING THE FILE FROM A LAYER"
echo "  \$ docker save $BAD_TAG -o image.tar && tar xf image.tar"
docker save "$BAD_TAG" -o image.tar 2>/dev/null
mkdir -p extract && tar xf image.tar -C extract 2>/dev/null

echo "  Searching every layer blob for app/.env ..."
FOUND=""
for blob in $(find extract -type f 2>/dev/null); do
  if tar tf "$blob" 2>/dev/null | grep -q "^app/\.env$"; then
    FOUND="$blob"
    echo "    found in layer: $(basename "$blob" | cut -c1-16)..."
    echo "    contents:"
    tar xf "$blob" -O "app/.env" 2>/dev/null | sed 's/^/      /'
  fi
done
if [ -z "$FOUND" ]; then
  echo "    (layer format differs on this Docker version; the metadata leak"
  echo "     in section 2 still applies)"
fi
echo
echo "  The file was deleted two layers ago and its contents are readable."
echo "  Layers are immutable and additive: a later layer can only HIDE a"
echo "  file, never remove it from the layer that created it."

# ---------------------------------------------------------------------------
section "4. DOES COMBINING INTO ONE RUN HELP?"
echo "  RUN echo \"KEY=...\" > .env && do_something && rm .env"
echo
echo "  The FILE no longer survives - there is only one layer, and the file"
echo "  is absent by the time it is committed."
echo
echo "  But the COMMAND is still in the metadata, exactly as shown in"
echo "  section 2. So the secret is still readable via docker history."
echo
echo "  The only correct options:"
echo "    - runtime injection:  docker run -e KEY=... (never in the image)"
echo "    - BuildKit secrets:   RUN --mount=type=secret,id=k ..."
echo "    - multi-stage build:  the final stage keeps none of the builder's"
echo "                          layers, so build credentials cannot reach it"

# ---------------------------------------------------------------------------
section "5. A CORRECT IMAGE"
mkdir -p app
cat > app/main.py <<'EOF'
import os

key = os.getenv("API_KEY", "").strip()
if not key:
    raise SystemExit("API_KEY is not set. Pass it with: docker run -e API_KEY=...")
print(f"service started, key ending {key[-4:]}, env={os.getenv('APP_ENV', 'local')}")
EOF
cat > requirements.txt <<'EOF'
# no third-party dependencies for this demo
EOF
cat > .dockerignore <<'EOF'
.venv/
.git/
__pycache__/
*.pyc
.env
*.db
EOF
cat > Dockerfile <<'EOF'
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
EOF
echo "  Dockerfile (note the layer ordering and the absent secret):"
sed 's/^/    /' Dockerfile
echo
docker build -q -t "$GOOD_TAG" . >/dev/null 2>&1 && echo "  built."

echo
echo "  Running with configuration supplied at RUNTIME:"
echo "  \$ docker run --rm -e API_KEY=sk-live-FAKE-runtime-1234 -e APP_ENV=production $GOOD_TAG"
docker run --rm -e API_KEY=sk-live-FAKE-runtime-1234 -e APP_ENV=production \
  "$GOOD_TAG" 2>&1 | sed 's/^/    /'
echo
echo "  And failing fast when it is missing:"
docker run --rm "$GOOD_TAG" 2>&1 | sed 's/^/    /'
echo
echo "  Confirming it does NOT run as root:"
echo -n "    whoami -> "
docker run --rm "$GOOD_TAG" whoami 2>/dev/null || echo "(entrypoint override unsupported)"
echo
echo "  Confirming no secret is in the image metadata:"
if docker history --no-trunc "$GOOD_TAG" 2>/dev/null | grep -q "sk-live"; then
  echo "    FOUND A SECRET - this would be a bug"
else
  echo "    no 'sk-live' anywhere in the image history. Correct."
fi

# ---------------------------------------------------------------------------
section "6. LAYER CACHING, MEASURED"
echo "  Rebuild with NO changes:"
START=$(date +%s%N)
docker build -q -t "$GOOD_TAG" . >/dev/null 2>&1
END=$(date +%s%N)
echo "    $(( (END - START) / 1000000 )) ms  (everything cached)"

echo
echo "  Rebuild after editing SOURCE only:"
echo "# a comment" >> app/main.py
START=$(date +%s%N)
docker build -q -t "$GOOD_TAG" . >/dev/null 2>&1
END=$(date +%s%N)
echo "    $(( (END - START) / 1000000 )) ms  (pip layer reused, source recopied)"

echo
echo "  Rebuild after editing REQUIREMENTS:"
echo "# changed" >> requirements.txt
START=$(date +%s%N)
docker build -q -t "$GOOD_TAG" . >/dev/null 2>&1
END=$(date +%s%N)
echo "    $(( (END - START) / 1000000 )) ms  (pip layer INVALIDATED and rerun)"
echo
echo "  This is why requirements.txt is copied before the source. Reverse"
echo "  the two lines and every source edit pays the dependency install."

# ---------------------------------------------------------------------------
section "7. IMAGE SIZES"
docker image ls --format "{{.Repository}}:{{.Tag}}  {{.Size}}" \
  | grep -E "m2l20|^python" | head -5 | sed 's/^/    /' 
echo
echo "  (python:3.12-slim is roughly 150 MB; the full python:3.12 is nearer"
echo "   1 GB. On serverless that difference is cold-start latency and cost.)"

echo
echo "$LINE"
echo "CLEANUP"
echo "$LINE"
echo "  Removing both demo images and the temporary directory..."
echo "  (the trap handler does this even if the script is interrupted)"

echo
echo "=========================================================================="
