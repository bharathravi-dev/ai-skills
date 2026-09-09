# M2-L17 — Git, Branches and Dependency Management

| | |
|---|---|
| **Lesson ID** | M2-L17 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M2-L06](M2-L06-modules-packages.md) |

---

> You almost certainly know Git. This lesson is short on basics and concentrates on the parts that
> matter for **this course specifically**: reproducible environments, what must never be committed,
> and how prompts and datasets become versioned artefacts (M5-L12, M10-L13).

---

## 1. Learning objectives

1. **Use** the core Git workflow and **explain** what staging adds.
2. **Recover** from the three most common mistakes: wrong branch, committed secret, bad commit.
3. **Explain** why `.gitignore` is not a security control.
4. **Choose** between a pinned `requirements.txt`, a lockfile and `pyproject.toml`.
5. **Reproduce** an environment exactly on another machine.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Repository** | A project plus its complete history. |
| **Commit** | A snapshot with a message, author and parent. |
| **Staging area / index** | Where you assemble the next commit. |
| **Branch** | A movable pointer to a commit. |
| **HEAD** | The commit you currently have checked out. |
| **Merge** | Combining two branches, creating a merge commit. |
| **Rebase** | Replaying commits onto a new base, rewriting history. |
| **Remote** | Another copy of the repository, usually on a server. |
| **`.gitignore`** | Patterns for files Git should not track. |
| **Pin** | An exact version: `pydantic==2.13.5`. |
| **Lockfile** | Every package including transitive dependencies, pinned. |
| **`pyproject.toml`** | The standard project metadata and dependency file. |
| **Editable install** | `pip install -e .` — imports resolve to your working copy. |
| **Semantic versioning** | `MAJOR.MINOR.PATCH`. |

---

## 3. Plain-language explanation

Git stores snapshots. Each commit records the whole tree, plus a pointer to its parent.

```bash
git status                      # what has changed
git add path/to/file            # stage specific changes
git commit -m "message"         # snapshot the staged changes
git log --oneline -10           # recent history
git diff                        # unstaged changes
git diff --staged               # what you are about to commit
```

**The staging area is the part people skip and should not.** It lets you commit *part* of your
working changes — so a bug fix and an unrelated refactor become two commits with two messages, rather
than one commit called "stuff". `git add -p` walks you through hunks interactively and is worth
learning.

**Two habits that matter more than any command:**

1. **`git diff --staged` before every commit.** It is how you catch the API key you pasted into a
   config file for five minutes of testing.
2. **Commit messages say *why*, not *what*.** The diff already shows what changed. "Fix retry loop
   dropping the last error so failures were reported as successes" is worth writing; "fix bug" is
   not.

---

## 4. Analogy

**Git is a save system with named timelines.** Commits are saves, branches are separate timelines,
merging brings a timeline back into the main one.

### Where the analogy breaks

1. **Deleting a save frees the space. Git keeps everything.** A committed secret stays in history
   even after you delete the file in a later commit — which is why §5.4 exists.
2. **Saves are private. Once pushed, history is shared**, and rewriting it disrupts everyone else.
3. **A save captures the whole machine state. Git captures only tracked files** — not your `.venv`,
   not your `.env`, not the database. Reproducing a project needs Git *plus* a dependency
   specification.
4. **Games have one timeline. Git branches diverge and reconverge**, and conflicts are a genuine
   category of work with no analogue.

---

## 5. Detailed technical explanation

### 5.1 Branching

```bash
git switch -c feature/ticket-classifier    # create and switch
git switch main                            # switch back
git merge feature/ticket-classifier        # bring it in
git branch -d feature/ticket-classifier    # delete when merged
```

`git switch` and `git restore` replace the overloaded `git checkout`, which did both jobs and caused
real accidents (`git checkout .` silently discards uncommitted work).

**Merge versus rebase:**

| | Merge | Rebase |
|---|---|---|
| History | Preserved, with a merge commit | Linear, rewritten |
| Safe on shared branches | **Yes** | **No** |
| Use for | Integrating a finished branch | Tidying *your own* unpushed commits |

**The rule: never rebase commits you have pushed and others may have based work on.**

### 5.2 What must never be committed

| Never commit | Why | Instead |
|---|---|---|
| `.env`, API keys, tokens | Permanent in history, and readable by everyone with repo access | `.env.example` with blank values |
| `.venv/` | Large, machine-specific, rebuildable | `requirements.txt` |
| `__pycache__/`, `*.pyc` | Generated | `.gitignore` |
| Databases, `*.db` | Large, changing, often personal data | Migrations plus seed scripts |
| Large datasets, model weights | Bloats history permanently | Object storage; Git LFS |
| Customer or personal data | Legal and privacy exposure | Synthetic data (as this course uses) |

This course's `.gitignore` already covers these.

### 5.3 `.gitignore` is not a security control

`.gitignore` only prevents **untracked** files from being added. It does nothing about:

- A file already tracked before you added the pattern.
- Anything committed with `git add -f`.
- Secrets pasted into a file that *is* tracked — a config, a notebook, a test fixture.

**The real controls** are: never put a live secret in the working tree (M2-L19), and run automated
secret scanning in CI (`gitleaks`, `detect-secrets`, or your platform's push protection).

### 5.4 Recovering from mistakes

**Committed but not pushed — fix the last commit:**
```bash
git commit --amend                 # change the message or add staged files
```

**Undo the last commit, keep the changes:**
```bash
git reset --soft HEAD~1            # changes return to staging
git reset HEAD~1                   # changes return to the working tree
```

**Discard local changes to a file** (destructive):
```bash
git restore path/to/file
```

**Committed on the wrong branch:**
```bash
git switch correct-branch
git cherry-pick <commit-sha>
git switch wrong-branch && git reset --hard HEAD~1
```

**Committed a secret — the important one.**

Removing the file in a *new* commit is **not enough**. The secret remains in history and can be
retrieved from any clone. The correct response, in order:

1. **Rotate the credential immediately.** Assume it is compromised. Everything else is secondary, and
   this step alone resolves most of the risk.
2. If it was pushed to a shared remote, **treat it as public**. Anyone with read access, any CI log,
   any fork, and any cached mirror may hold it.
3. Only then consider rewriting history (`git filter-repo`, BFG), coordinating with everyone who has
   a clone.

**Rotation first. History rewriting is cleanup, not remediation.**

**Find what a commit changed:**
```bash
git show <sha>
git log -p path/to/file            # history of one file
git log -S "api_key"               # commits that added or removed that string
git blame path/to/file             # who last changed each line
```

`git log -S` is how you find when a secret entered the repository.

### 5.5 Dependency management

Three files, three jobs:

| File | Purpose | Pins transitive deps? |
|---|---|---|
| `pyproject.toml` | Project metadata + **direct** dependencies (ranges) | No |
| `requirements.txt` | Direct dependencies, usually pinned | No |
| `requirements.lock` (from `pip freeze`) | **Everything** installed, pinned | **Yes** |

```toml
[project]
name = "ticketapi"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.140,<1.0",
    "pydantic>=2.11,<3.0",
]

[project.optional-dependencies]
dev = ["pytest>=9.0", "mypy>=1.8"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

```bash
pip install -e ".[dev]"            # editable install with dev extras
pip freeze > requirements.lock     # exact snapshot including transitive deps
```

**Libraries specify ranges** so consumers can resolve compatible versions.
**Applications pin exactly** so deployments are reproducible.

**Full reproducibility needs three things**, and people usually record only the first:

1. The **lockfile** (`pip freeze`).
2. The **Python version** (`requires-python`, and the version in your Dockerfile).
3. The **platform** — some packages ship different wheels per OS and architecture.

Two of the three are why "it works in CI but not on the M-series laptop" happens.

### 5.6 What this course versions beyond code

This is the part that is specific to AI engineering, and it is easy to miss:

| Artefact | Why version it | Lesson |
|---|---|---|
| **Prompts** | A prompt is a hyperparameter (M1-L05). Changing it invalidates every prior evaluation | M5-L12 |
| **Evaluation datasets** | A score is meaningless without knowing which set produced it | M5-L18 |
| **Model IDs and settings** | `claude-sonnet-5` at temperature 0.2 is part of your system's behaviour | M10-L13 |
| **Chunking and retrieval config** | Chunk size and `k` change results as much as code | M7-L06 |

**A result should be reproducible from a commit SHA.** If your evaluation report does not record the
prompt version, the model ID, the dataset version and the configuration, it is not reproducible — and
M10-L13 makes this an auditability requirement, not a preference.

### 5.7 Assumptions and limitations

- Git tracks content, not intent. A clean history requires discipline, not tooling.
- `pip freeze` captures your platform's resolution; cross-platform reproducibility needs more
  (`uv`, `poetry`, or per-platform lockfiles).
- Git handles text well and binaries badly. Model weights belong in object storage.
- Rewriting shared history is disruptive; coordinate it.

---

## 6. Worked example — making a project reproducible

**Start:** a folder with `main.py`, a `.venv`, some scripts and a `.env` containing a real key.

**Step 1 — `.gitignore` *before* `git init`.** Order matters: create it first and nothing untracked
is ever offered for staging.

```
.venv/
__pycache__/
*.pyc
.env
*.db
.pytest_cache/
```

**Step 2 — initialise and check what Git *would* add.**

```bash
git init
git add -A
git status --short
```

**Read that list before committing.** If `.env` or `.venv/` appears, stop and fix `.gitignore`. This
one habit prevents most accidental commits.

**Step 3 — provide `.env.example`.**

```
ANTHROPIC_API_KEY=
LLM_MODEL=claude-sonnet-5
LOG_LEVEL=INFO
```

Committed, with **blank values**. It documents what is required without exposing anything, and it is
what a new contributor copies.

**Step 4 — pin dependencies.**

```bash
pip freeze > requirements.lock
```

Commit both `requirements.txt` (readable, direct) and `requirements.lock` (exact, complete).

**Step 5 — record the Python version** in `pyproject.toml` (`requires-python`) and in the Dockerfile
base image (M2-L20).

**Step 6 — a README that actually works.** The test is that a new person can go from clone to running
in four commands:

```bash
git clone <url> && cd project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env    # then fill in your key
```

**Step 7 — verify by doing it.** Clone into a fresh directory and follow your own README exactly. It
will fail the first time — an undocumented system package, a missing migration, a step you do
automatically without noticing. **The instructions are only correct once you have executed them
somewhere clean.**

---

## 7. Practical activity

**File:** [`labs/m2/l17_git.sh`](../../labs/m2/l17_git.sh)

```bash
bash labs/m2/l17_git.sh
```

Creates a throwaway repository in a temporary directory (**your own repositories are untouched**),
then demonstrates: `.gitignore` working and failing, a secret committed and why deleting it does not
help, `git log -S` finding it, branching and merging, and recovering from a commit on the wrong
branch.

### 7.1 Important lines

| Command | Why |
|---|---|
| `git status --short` | The list to read before every commit. |
| `git log -S "sk-live"` | Finds every commit that added or removed that string. |
| `git show <sha>:file` | Retrieves a file's content **from history**, proving deletion is not removal. |
| `git reset --hard HEAD~1` | Removes the last commit from a branch (destructive). |
| `git cherry-pick <sha>` | Copies a commit onto another branch. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with git 2.43.0. Commit SHAs and the temporary path will differ:

```
==========================================================================
GIT: IGNORING, SECRETS, HISTORY AND RECOVERY
==========================================================================
git version: git version 2.43.0
temporary repository: /tmp/tmp.02VBOLr8J3

--------------------------------------------------------------------------
1. .gitignore WORKS - for UNTRACKED files
--------------------------------------------------------------------------
  Files on disk:
    .env
    .gitignore
    main.py
    .venv

  What git would stage (git status --short):
    A  .gitignore
    A  main.py

  .env and .venv/ are absent from that list. Read this list before
  EVERY commit - it is how you catch a key you pasted in for testing.

--------------------------------------------------------------------------
2. .gitignore IS NOT SECURITY - forcing a tracked secret
--------------------------------------------------------------------------
  Someone runs 'git add -f .env' (or pastes a key into a tracked file):
    committed. .gitignore did not stop -f.

  Now they 'fix' it by deleting the file:
    .env no longer exists in the working tree:
      (file is gone)

  But the secret is STILL IN HISTORY. Finding it:
    $ git log -S 'sk-live' --oneline
      1e0134a Remove environment file (oops)
      d5f4c62 Add environment file

    $ git show d5f4c62:.env
      ANTHROPIC_API_KEY=sk-live-SECRET-do-not-share

  The live key is retrievable from any clone, any fork, and any CI
  cache. Deleting the file did nothing.

  CORRECT ORDER OF RESPONSE:
    1. ROTATE the credential now. Assume it is compromised.
    2. If pushed anywhere shared, treat it as public.
    3. Only then consider rewriting history (git filter-repo).
  Rotation is the remediation. History rewriting is cleanup.

--------------------------------------------------------------------------
3. AN ALREADY-TRACKED FILE IGNORES .gitignore
--------------------------------------------------------------------------
  config.json is listed in .gitignore, but was tracked first.
  Changing it still shows up:
     M config.json

  Fix - stop tracking it, keeping the local file:
    $ git rm --cached config.json
    (now genuinely ignored - no output above means clean)

--------------------------------------------------------------------------
4. BRANCHING AND MERGING
--------------------------------------------------------------------------
  History after merging a feature branch:
    *   a1d2a70 Merge branch 'feature/classifier'
    |\  
    | * eeaf1fd Add classifier
    * | 896b671 Add README
    |/  
    * b7c694e Stop tracking config.json
    * 7760383 Track config anyway
    * 89b4f9e Ignore config.json

--------------------------------------------------------------------------
5. RECOVERING FROM A COMMIT ON THE WRONG BRANCH
--------------------------------------------------------------------------
  Committed 'c612652 Urgent hotfix' onto main by mistake.
  main now:
    c612652 Urgent hotfix
    a1d2a70 Merge branch 'feature/classifier'

  Move it to a hotfix branch based on the commit BEFORE the mistake:
    $ git switch -c hotfix main~1
    $ git cherry-pick c612652
    hotfix branch:
      c612652 Urgent hotfix
      a1d2a70 Merge branch 'feature/classifier'

    $ git switch main && git reset --hard HEAD~1
    main after reset:
      a1d2a70 Merge branch 'feature/classifier'
      896b671 Add README

  The commit is on hotfix and gone from main. Note reset --hard is
  DESTRUCTIVE to uncommitted work - the commit survived only because
  cherry-pick had already copied it.

--------------------------------------------------------------------------
6. WHAT A CLEAN PROJECT COMMITS
--------------------------------------------------------------------------
  Tracked files in the final repository:
    .env.example
    .gitignore
    README.md
    classifier.py
    main.py
    requirements.txt

  Present: .env.example (BLANK values), pinned requirements, code.
  Absent from the working tree: .env, .venv/, __pycache__.
  Note .env still appears in HISTORY from step 2 - which is exactly
  why the rule is 'never let it in', not 'remove it later'.

==========================================================================
```

### 7.3 Reading the result

**Section 2 is the one to sit with.** Watch the sequence:

1. `.env` containing `sk-live-SECRET-do-not-share` is force-added and committed.
2. It is deleted and the deletion committed. The working tree is clean; the file is gone.
3. `git log -S 'sk-live'` finds **two** commits — the one that added it and the one that removed it.
4. `git show 760260b:.env` prints the key **in full**.

The file was deleted three commits ago and the secret is still one command away. It is in every
clone, every fork, every CI cache and every mirror. A pull request that "removes the credential"
closes nothing.

That is why the remediation order in §5.4 is what it is: **rotate first**. Rewriting history is
housekeeping you do afterwards, and only after you have assumed the key is public.

**Section 3 shows the other `.gitignore` limitation.** `config.json` is listed in `.gitignore`, yet
modifying it still appears in `git status`, because it was **tracked before** the rule existed.
`.gitignore` governs untracked files only. `git rm --cached` stops the tracking while keeping your
local copy.

**Section 5** demonstrates the recovery most people need at some point. The commit was copied to a
new branch with `cherry-pick`, *then* removed from `main` with `reset --hard`. Order matters
absolutely: `reset --hard` discards work, and the commit survived only because it had already been
copied. Doing those two steps in the opposite order loses it.

**Section 6 closes the loop.** The final repository tracks `.env.example` with **blank** values,
pinned `requirements.txt`, and the code — and nothing else. But note the closing line: `.env` is
still in the *history* from step 2. The working tree being clean is not the same as the repository
being clean, which is exactly why the rule is *never let it in* rather than *remove it later*.

**Verification:** confirm that `git show <sha>:.env` prints the key after the file has been deleted,
and that `git status --short` in section 1 lists neither `.env` nor `.venv/`.

---

## 8. Common mistakes and troubleshooting

1. **Committing `.env` or keys.** Rotate first, rewrite second.
2. **Committing `.venv/`.**
3. **Believing `.gitignore` protects an already-tracked file.**
4. **`git checkout .`** discarding uncommitted work. Prefer `git restore`.
5. **Rebasing pushed commits.**
6. **Unpinned dependencies** in an application.
7. **Not recording the Python version.**
8. **Commit messages describing *what* rather than *why*.**
9. **Not versioning prompts, eval sets and model configuration.**

| Symptom | Cause | Fix |
|---|---|---|
| Ignored file still tracked | It was tracked before the ignore rule | `git rm --cached path`, then commit |
| `.gitignore` seems ignored | Wrong location, or the file is already tracked | `git check-ignore -v path` |
| Merge conflict | Both branches changed the same lines | Edit markers, `git add`, `git commit` |
| Wrong branch | Committed before switching | `cherry-pick` then `reset --hard` |
| Works in CI, not locally | Different Python or unpinned deps | Compare `pip freeze`; pin |
| Secret found in history | Committed at some point | **Rotate now**; then consider `git filter-repo` |

---

## 9. Security, privacy, reliability and cost

- **Security.** A secret in Git history is compromised the moment it is pushed. **Rotate
  immediately**; history rewriting is cleanup. Enable push protection or a secret scanner in CI —
  human review does not reliably catch this.
- **Privacy.** Never commit customer data, even in a test fixture. History is permanent and clones
  spread. This course uses synthetic data throughout for exactly this reason.
- **Reliability.** Unpinned dependencies mean your build is a function of *when* it ran. A pinned
  lockfile plus a recorded Python version makes it a function of the commit.
- **Governance.** Reproducibility from a commit SHA — code, prompt, dataset, model ID, configuration
  — is an auditability requirement in M10-L13, not a nicety.
- **Cost.** Committed model weights or datasets bloat every clone permanently, and Git cannot forget
  them without rewriting history.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

In a throwaway directory:

1. `git init`, create three files, stage only two, and commit. Confirm with `git status` that the
   third is still uncommitted.
2. Modify a committed file. Show `git diff` and `git diff --staged` and explain the difference.
3. Write two commit messages for the same change: a poor one and a good one. State what makes the
   second better.

### Exercise 2 — Intermediate (~25 min)

1. Create a `.gitignore` with `.env`, then create `.env` and confirm `git status` does not show it.
2. Now `git add -f .env` and commit it. Delete the file and commit again.
3. Use `git log -S` to find the commit that added it, and `git show <sha>:.env` to retrieve its
   contents. **Explain in writing what this proves about deleting a secret.**
4. State the correct remediation order and why rotation comes first.
5. Create a branch, commit on it, merge it into main, and show the resulting `git log --graph`.

### Exercise 3 — Challenge (~25 min)

1. Take one of this course's labs and make it a reproducible mini-project: `pyproject.toml`,
   `requirements.lock`, `.env.example`, `.gitignore`, README.
2. Clone it into a **fresh** directory and follow your own README exactly. Record every step that
   failed or was missing.
3. Fix the README and repeat until a clean clone works first time.
4. Add a `scripts/check_secrets.sh` that greps the working tree for patterns like `sk-`,
   `AKIA`, `-----BEGIN` and `password =`, and exits non-zero on a match. Test it against a file
   containing a fake key.
5. Explain in three sentences why that script is a useful backstop and why it is **not** sufficient.

---

## 11. Quiz

**Q1.** What does the staging area let you do?

- A. Nothing useful; it is a formality.
- B. Assemble a commit from *part* of your working changes, so unrelated edits become separate
  commits.
- C. Store files remotely.
- D. Undo commits.

**Q2.** You committed a `.env` containing a live API key, then deleted the file in a later commit.
What is the state of the secret?

- A. Safe; it was deleted.
- B. Still present in history and retrievable from any clone — it must be treated as compromised and
  rotated.
- C. Removed once you push.
- D. Encrypted by Git.

**Q3.** What is the correct **first** action after committing a secret?

- A. Rewrite history with `git filter-repo`.
- B. Rotate the credential immediately.
- C. Delete the repository.
- D. Add it to `.gitignore`.

**Q4.** Why is `.gitignore` not a security control?

- A. It can be edited.
- B. It only stops untracked files being added; it does nothing about files already tracked,
  `git add -f`, or secrets pasted into tracked files.
- C. It is optional.
- D. It only works on some platforms.

**Q5.** When is rebase unsafe?

- A. Always.
- B. On commits already pushed and possibly used as a base by others, because it rewrites history.
- C. On your own local branches.
- D. Never.

**Q6.** For an application, how should dependencies be specified?

- A. Unpinned, for the newest fixes.
- B. Pinned exactly, with a lockfile capturing transitive dependencies, plus a recorded Python
  version.
- C. Ranges only.
- D. Installed manually and documented in a wiki.

**Q7.** Which command finds the commit that introduced a particular string?

- A. `git blame`  B. `git log -S "string"`  C. `git diff`  D. `git show`

**Q8.** Besides code, what else must be versioned in an AI project?

- A. Nothing else.
- B. Prompts, evaluation datasets, model IDs and settings, and retrieval configuration — all of them
  change behaviour and invalidate previous results.
- C. Only the model weights.
- D. Only the README.

**Q9.** Beyond a lockfile, what else is needed for a reproducible environment?

- A. Nothing.
- B. The Python version and the platform, since some packages ship different wheels per OS and
  architecture.
- C. A faster machine.
- D. The Git version.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why the README's setup instructions
must be tested from a clean clone rather than reviewed.

---

## 12. Revision notes

- `status` → `add` → `commit`. **The staging area lets you split unrelated changes.**
  **`git diff --staged` before every commit.**
- Commit messages explain **why**.
- `git switch` / `git restore` instead of the overloaded `git checkout`.
- **Merge for shared branches; rebase only for your own unpushed commits.**
- **Never commit:** `.env`, keys, `.venv/`, databases, datasets, model weights, customer data.
- **`.gitignore` is not security.** It does not cover tracked files, `add -f`, or secrets pasted into
  tracked files. Use a secret scanner.
- **Committed a secret → ROTATE FIRST.** History rewriting is cleanup, not remediation. `git log -S`
  finds when it entered.
- Applications **pin exactly** + lockfile; libraries use **ranges**.
- **Reproducibility = lockfile + Python version + platform.**
- **Version prompts, eval datasets, model IDs and retrieval config** — a result must be reproducible
  from a commit SHA (M10-L13).
- **Test your README from a clean clone.** It will fail the first time.

---

## 13. Completion checklist

- [ ] I use the staging area to split unrelated changes.
- [ ] I read `git diff --staged` before committing.
- [ ] I proved a deleted secret is still retrievable from history.
- [ ] I can state the remediation order, rotation first.
- [ ] My project has `.gitignore`, `.env.example`, `pyproject.toml` and a lockfile.
- [ ] I tested my README from a fresh clone and fixed what broke.
- [ ] I know which non-code artefacts this course versions.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Pro Git (free). <https://git-scm.com/book/en/v2> `[UNVERIFIED]`
- Python Packaging User Guide.
  <https://packaging.python.org/en/latest/> `[UNVERIFIED]`
- `git filter-repo`. <https://github.com/newren/git-filter-repo> `[UNVERIFIED]`
- git 2.43.0 `[VERIFIED 2026-09-08]` — the version used for this lesson's lab.

---

## 15. Next lesson

→ [M2-L18 — Logging and Automated Testing with pytest](M2-L18-logging-testing.md)

Your code is versioned and reproducible. Next: knowing whether it works, and knowing what it did in
production — the two things you cannot add later.
