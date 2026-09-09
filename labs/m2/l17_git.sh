#!/usr/bin/env bash
# M2-L17: git behaviour demonstrated in a THROWAWAY repository.
#
#     bash labs/m2/l17_git.sh
#
# Creates a temporary directory. Your own repositories are never touched.

set -u
LINE="--------------------------------------------------------------------------"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

section() { echo; echo "$LINE"; echo "$1"; echo "$LINE"; }

echo "=========================================================================="
echo "GIT: IGNORING, SECRETS, HISTORY AND RECOVERY"
echo "=========================================================================="
echo "git version: $(git --version)"
echo "temporary repository: $WORK"

cd "$WORK" || exit 1
git init --quiet -b main
git config user.email "learner@example.invalid"
git config user.name "Course Learner"

# ---------------------------------------------------------------------------
section "1. .gitignore WORKS - for UNTRACKED files"
cat > .gitignore <<'EOF'
.venv/
__pycache__/
*.pyc
.env
*.db
EOF
echo "print('hello')" > main.py
echo "ANTHROPIC_API_KEY=sk-live-SECRET-do-not-share" > .env
mkdir -p .venv && echo "binary" > .venv/python

echo "  Files on disk:"
ls -a | grep -v '^\.$\|^\.\.$\|^\.git$' | sed 's/^/    /'
echo
echo "  What git would stage (git status --short):"
git add -A
git status --short | sed 's/^/    /'
echo
echo "  .env and .venv/ are absent from that list. Read this list before"
echo "  EVERY commit - it is how you catch a key you pasted in for testing."
git commit --quiet -m "Add main script and ignore rules"

# ---------------------------------------------------------------------------
section "2. .gitignore IS NOT SECURITY - forcing a tracked secret"
echo "  Someone runs 'git add -f .env' (or pastes a key into a tracked file):"
git add -f .env
git commit --quiet -m "Add environment file"
echo "    committed. .gitignore did not stop -f."
echo
echo "  Now they 'fix' it by deleting the file:"
git rm --quiet .env
git commit --quiet -m "Remove environment file (oops)"
echo "    .env no longer exists in the working tree:"
ls .env 2>/dev/null || echo "      (file is gone)"
echo
echo "  But the secret is STILL IN HISTORY. Finding it:"
echo "    \$ git log -S 'sk-live' --oneline"
git log -S 'sk-live' --oneline | sed 's/^/      /'
echo
BAD_SHA="$(git log -S 'sk-live' --format=%H | tail -1)"
echo "    \$ git show ${BAD_SHA:0:7}:.env"
git show "${BAD_SHA}:.env" | sed 's/^/      /'
echo
echo "  The live key is retrievable from any clone, any fork, and any CI"
echo "  cache. Deleting the file did nothing."
echo
echo "  CORRECT ORDER OF RESPONSE:"
echo "    1. ROTATE the credential now. Assume it is compromised."
echo "    2. If pushed anywhere shared, treat it as public."
echo "    3. Only then consider rewriting history (git filter-repo)."
echo "  Rotation is the remediation. History rewriting is cleanup."

# ---------------------------------------------------------------------------
section "3. AN ALREADY-TRACKED FILE IGNORES .gitignore"
echo "config.json" >> .gitignore
git add .gitignore && git commit --quiet -m "Ignore config.json"
echo '{"debug": true}' > config.json
git add -f config.json && git commit --quiet -m "Track config anyway"
echo '{"debug": false}' > config.json
echo "  config.json is listed in .gitignore, but was tracked first."
echo "  Changing it still shows up:"
git status --short | sed 's/^/    /'
echo
echo "  Fix - stop tracking it, keeping the local file:"
echo "    \$ git rm --cached config.json"
git rm --cached --quiet config.json
git commit --quiet -m "Stop tracking config.json"
echo '{"debug": true}' > config.json
git status --short | sed 's/^/    /'
echo "    (now genuinely ignored - no output above means clean)"

# ---------------------------------------------------------------------------
section "4. BRANCHING AND MERGING"
git switch --quiet -c feature/classifier
echo "def classify(t): return 'billing'" > classifier.py
git add classifier.py && git commit --quiet -m "Add classifier"
git switch --quiet main
echo "# Ticket API" > README.md
git add README.md && git commit --quiet -m "Add README"
git merge --quiet --no-edit feature/classifier
echo "  History after merging a feature branch:"
git log --oneline --graph -6 | sed 's/^/    /'

# ---------------------------------------------------------------------------
section "5. RECOVERING FROM A COMMIT ON THE WRONG BRANCH"
echo "print('urgent hotfix')" > hotfix.py
git add hotfix.py && git commit --quiet -m "Urgent hotfix"
WRONG_SHA="$(git rev-parse --short HEAD)"
echo "  Committed '$WRONG_SHA Urgent hotfix' onto main by mistake."
echo "  main now:"
git log --oneline -2 | sed 's/^/    /'
echo
echo "  Move it to a hotfix branch based on the commit BEFORE the mistake:"
echo "    \$ git switch -c hotfix main~1"
echo "    \$ git cherry-pick $WRONG_SHA"
git switch --quiet -c hotfix main~1
git cherry-pick "$WRONG_SHA" >/dev/null 2>&1
echo "    hotfix branch:"
git log --oneline -2 | sed 's/^/      /'
echo
echo "    \$ git switch main && git reset --hard HEAD~1"
git switch --quiet main
git reset --hard --quiet HEAD~1
echo "    main after reset:"
git log --oneline -2 | sed 's/^/      /'
echo
echo "  The commit is on hotfix and gone from main. Note reset --hard is"
echo "  DESTRUCTIVE to uncommitted work - the commit survived only because"
echo "  cherry-pick had already copied it."

# ---------------------------------------------------------------------------
section "6. WHAT A CLEAN PROJECT COMMITS"
cat > .env.example <<'EOF'
ANTHROPIC_API_KEY=
LLM_MODEL=claude-sonnet-5
LOG_LEVEL=INFO
EOF
cat > requirements.txt <<'EOF'
fastapi==0.141.1
pydantic==2.13.5
EOF
git add .env.example requirements.txt
git commit --quiet -m "Add example env and pinned requirements"
echo "  Tracked files in the final repository:"
git ls-files | sed 's/^/    /'
echo
echo "  Present: .env.example (BLANK values), pinned requirements, code."
echo "  Absent from the working tree: .env, .venv/, __pycache__."
echo "  Note .env still appears in HISTORY from step 2 - which is exactly"
echo "  why the rule is 'never let it in', not 'remove it later'."

echo
echo "=========================================================================="
