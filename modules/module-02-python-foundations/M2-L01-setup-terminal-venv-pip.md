# M2-L01 — Terminal, Python Install, Virtual Environments and pip

| | |
|---|---|
| **Lesson ID** | M2-L01 |
| **Module** | Module 2 — Python and Software Foundations |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | None for the content. You should have finished Module 1 for context. |

---

## A note before you start

You are an experienced engineer. Module 2 will feel slow in places, and you should let it. Its job
is not to teach you programming — it is to establish **the exact Python idioms, validation library,
project layout and error-handling patterns that every later module assumes**. Skipping it means
Module 5 onwards will contain code you can read but not confidently modify.

Where a concept maps onto something you already know from JavaScript or another language, I say so
explicitly and then say where the mapping breaks.

---

## 1. Learning objectives

1. **Verify** your Python installation and **explain** what `python3`, `pip` and `venv` each do.
2. **Create, activate and deactivate** a virtual environment, and **explain** what problem it solves.
3. **Install** pinned dependencies and **regenerate** a lockfile.
4. **Diagnose** the three most common environment failures from their error messages.
5. **State** why `pip install` without a virtual environment is a mistake, in terms of reproducibility.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Terminal / shell** | A text interface for running commands. On Linux/macOS usually `bash` or `zsh`; on Windows, PowerShell. |
| **Interpreter** | The program that runs Python code. `python3` is an interpreter binary. |
| **PATH** | An environment variable listing directories the shell searches for commands. |
| **Package** | Reusable code distributed for installation. Equivalent to an npm package. |
| **PyPI** | The Python Package Index — the public package registry. The npm registry equivalent. |
| **pip** | Python's package installer. Roughly `npm`. |
| **Virtual environment (venv)** | An isolated directory containing its own Python interpreter and packages. |
| **Activate** | Adjust your shell so `python` and `pip` refer to the venv's copies. |
| **`requirements.txt`** | A list of packages to install, optionally with pinned versions. |
| **Pinning** | Specifying an exact version (`==2.13.5`) rather than a range. |
| **Transitive dependency** | A package installed because another package needs it. |
| **Site-packages** | The directory where installed packages live. |
| **Module** | A single `.py` file. |
| **Standard library** | Packages bundled with Python, needing no installation. |

---

## 3. Plain-language explanation

Three tools, three jobs:

- **`python3`** runs your code.
- **`pip`** downloads and installs libraries.
- **`venv`** keeps each project's libraries separate from every other project's.

The third is the one that matters and the one beginners skip.

**The problem `venv` solves.** Suppose Project A needs `pydantic` version 1 and Project B needs
version 2. They are incompatible. If you install packages globally, installing one breaks the other.
Worse, your machine ends up with a pile of packages accumulated over years, so the code works for you
and fails for everyone else — including your own CI pipeline and your production server.

A virtual environment is a folder containing its own Python and its own packages. Activate it and
`pip install` writes into that folder. Delete the folder and the project's dependencies are gone,
with nothing else affected.

### If you know Node

| Node | Python | Difference that matters |
|---|---|---|
| `node` | `python3` | — |
| `npm` | `pip` | — |
| `package.json` dependencies | `requirements.txt` | `requirements.txt` is a flat list, not structured JSON |
| `package-lock.json` | `requirements.txt` with `==` pins, or `pip-tools`/`uv` output | **Python has no universally standard lockfile.** This is a real gap |
| `node_modules/` (per project, automatic) | `.venv/` (per project, **manual**) | **This is the key difference.** Node isolates by default; Python does not |
| `npx` | `python -m <module>` | — |

**The one thing to internalise:** in Node, isolation is the default and you have to work to break it.
In Python, isolation is opt-in and you have to remember to create it. Every "it works on my machine"
Python story starts with someone forgetting.

---

## 4. Analogy

**A venv is a project-specific toolbox.**

The global Python install is the shared workshop tools everyone uses. A venv is a labelled box you
keep for one job, containing exactly the tools that job needs, at the versions it needs. When the job
is finished you throw the box away and the workshop is untouched.

### Where the analogy breaks

1. **The venv is not fully self-contained.** By default it *links to* the system Python interpreter
   rather than copying it. Upgrade or remove the system Python and existing venvs can break. Recreate
   them rather than repairing them.
2. **A toolbox holds physical tools; a venv holds a resolved dependency graph.** Installing one
   package pulls in others (transitive dependencies), and those can conflict in ways two spanners
   cannot.
3. **You can have many toolboxes open at once; only one venv is active per shell.** Activation is
   per-terminal-session and does not persist across new terminals.
4. **The analogy implies venvs are heavyweight.** They are not — creating one takes about a second
   and a few megabytes. Create one per project, always, without deliberation.

---

## 5. Detailed technical explanation

### 5.1 What activation actually does

Activation is less magical than it looks. It:

1. Prepends the venv's `bin/` (Windows: `Scripts\`) directory to your `PATH`.
2. Sets `VIRTUAL_ENV` to the venv path.
3. Usually alters your shell prompt so you can see it is active.

That is all. So `python` now resolves to `.venv/bin/python` instead of `/usr/bin/python3`, and that
interpreter is configured to look in its own `site-packages`.

Two consequences worth knowing:

- **You do not strictly need to activate.** Running `.venv/bin/python script.py` works identically.
  This is what CI systems and Docker images usually do, since there is no interactive shell to
  activate in.
- **Activation is per-shell.** Open a new terminal tab and you must activate again. Forgetting is the
  single most common cause of `ModuleNotFoundError`.

### 5.2 The commands

**Check your Python.** `[VERIFIED 2026-09-07]` — this course was authored and tested on Python
3.12.3.

```bash
python3 --version          # expect 3.10 or newer; 3.12.x is what the course uses
which python3              # where it lives (Windows: where python)
```

**Create a venv.** Run this from the course root, once.

```bash
python3 -m venv .venv
```

`python3 -m venv` means "run the `venv` module as a script". `.venv` is the directory name — the
leading dot is a widely used convention and it is already in this course's `.gitignore`.

**Activate.**

| Shell | Command |
|---|---|
| bash / zsh (Linux, macOS) | `source .venv/bin/activate` |
| fish | `source .venv/bin/activate.fish` |
| PowerShell (Windows) | `.venv\Scripts\Activate.ps1` |
| cmd.exe (Windows) | `.venv\Scripts\activate.bat` |

Your prompt should now show `(.venv)`. Verify properly:

```bash
which python              # should point INSIDE .venv
python -c "import sys; print(sys.prefix)"
```

**Install dependencies.**

```bash
pip install -r requirements.txt
```

**Deactivate.**

```bash
deactivate
```

**Delete and recreate** — the correct fix for most environment problems:

```bash
deactivate ; rm -rf .venv ; python3 -m venv .venv
source .venv/bin/activate ; pip install -r requirements.txt
```

Never spend an hour repairing a venv. It is a cache. Rebuild it.

### 5.3 Pinning, and why this course pins

Three ways to specify a version:

| Form | Meaning | Use when |
|---|---|---|
| `pydantic` | Any version | Never in a project you will run twice |
| `pydantic>=2,<3` | A compatible range | Publishing a library others depend on |
| `pydantic==2.13.5` | Exactly this | **Applications.** Reproducible builds |

This course pins exactly, and the pins in `requirements.txt` are versions that were **actually
installed and imported successfully** in the authoring environment on 2026-09-07 `[EXECUTED]`.

The honest limitation: `requirements.txt` with `==` pins your *direct* dependencies but not
necessarily every transitive one. For full reproducibility you need `pip freeze > requirements.lock`
(which captures everything installed) or a tool such as `pip-tools` or `uv`. This course keeps a
readable `requirements.txt` and notes the gap rather than pretending it is a lockfile.

```bash
pip freeze > requirements.lock     # every package and version, including transitive
pip list                           # human-readable
pip show pydantic                  # details of one package, including what requires it
```

### 5.4 The three failures you will actually hit

**Failure 1 — `ModuleNotFoundError: No module named 'pydantic'`**

Cause, 90% of the time: the venv is not activated, or you activated it in a different terminal.

```bash
which python        # if this is /usr/bin/python3, you are not in the venv
```

Other causes: you installed into a different venv; the package name differs from the import name
(you install `python-dotenv` and import `dotenv`); or you never installed it.

**Failure 2 — `pip: command not found`, or pip installing into the wrong place**

Cause: `pip` on the PATH belongs to a different Python. The robust fix is to never call `pip`
directly:

```bash
python -m pip install -r requirements.txt
```

`python -m pip` guarantees you get the pip belonging to *this* interpreter. **Use this form
habitually** — it eliminates an entire class of confusion.

**Failure 3 — `error: externally-managed-environment`**

On Debian, Ubuntu and recent macOS, `pip install` outside a venv is blocked by design (PEP 668), to
stop you breaking system tools that depend on Python.

The correct response is **create a venv**. Do not use `--break-system-packages`, whose name is an
accurate description of what it does.

### 5.5 Alternatives you will encounter

You do not need these for the course, but you will meet them.

| Tool | What it is | Note |
|---|---|---|
| `uv` | A very fast installer and venv manager | Rapidly gaining adoption; `uv venv` and `uv pip install` mirror the commands here `[UNVERIFIED]` |
| `poetry` | Dependency management with a real lockfile | Heavier; good for libraries |
| `conda` | Environment manager handling non-Python deps too | Common in data science; heavier |
| `pipx` | Installs Python *applications* in isolation | For CLI tools, not project deps |
| `pyenv` | Manages multiple Python *versions* | Useful when projects need different Pythons |

Learn `venv` and `pip` first. They are always available, and every alternative is explained in terms
of them.

### 5.6 Assumptions and limitations

- Assumes Python 3.10+. Older versions lack syntax used throughout this course (`list[str]`,
  `X | None`).
- Windows paths and activation differ; both forms are given above.
- Corporate networks may require proxy configuration or an internal package index, which is outside
  this course's scope — ask your platform team for the `--index-url` they use.

---

## 6. Worked example — a clean setup, start to finish

Every command with its expected output. `[EXECUTED]` on 2026-09-07, Linux, Python 3.12.3.

**Step 1 — check the interpreter.**

```bash
$ python3 --version
Python 3.12.3
```

If this says 3.9 or lower, stop and install a newer Python before continuing.

**Step 2 — create the environment.**

```bash
$ cd /home/bharathr/self/Learning/claude/ai
$ python3 -m venv .venv
```

No output on success. Silence is good. Confirm the directory exists:

```bash
$ ls .venv
bin  include  lib  lib64  pyvenv.cfg
```

**Step 3 — activate, and verify it worked.**

```bash
$ source .venv/bin/activate
(.venv) $ which python
/home/bharathr/self/Learning/claude/ai/.venv/bin/python
```

The path must be inside `.venv`. If it says `/usr/bin/python3`, activation failed.

**Step 4 — see the empty environment.**

```bash
(.venv) $ python -m pip list
Package Version
------- -------
pip     24.0
```

A fresh venv contains almost nothing. That is the point: you now know exactly what your project
depends on, because you are about to install all of it explicitly.

**Step 5 — install the course dependencies.**

```bash
(.venv) $ python -m pip install -r requirements.txt
```

Expect several lines of `Collecting ...` and `Installing collected packages: ...`, ending with
`Successfully installed ...`. This downloads from PyPI, so it needs network access.

**Step 6 — verify the install with an actual import**, not just `pip list`. A package can appear
installed and still fail to import (wrong architecture, broken build):

```bash
(.venv) $ python -c "import pydantic, fastapi, numpy; print(pydantic.VERSION, fastapi.__version__, numpy.__version__)"
2.13.5 0.141.1 2.5.3
```

`[EXECUTED]` — these are the real versions installed and imported in the authoring environment.
Yours should match, because the versions are pinned.

**Step 7 — prove the isolation.** This is the step that makes the concept click:

```bash
(.venv) $ deactivate
$ python3 -c "import fastapi"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'fastapi'
```

The system Python cannot see the package. It is installed **only** inside `.venv`. That error is not
a problem — it is the isolation working correctly, and recognising it as such will save you time
later.

---

## 7. Practical activity

**File:** [`labs/m2/l01_doctor.py`](../../labs/m2/l01_doctor.py)

A diagnostic script that checks your environment and explains anything wrong in plain language.
Standard library only, so it runs whether or not your venv is working — which is precisely when you
need it.

```bash
python3 labs/m2/l01_doctor.py
```

### 7.1 Important lines

| Construct | Why |
|---|---|
| `sys.version_info` | A tuple like `(3, 12, 3, 'final', 0)`. Compare tuples directly: `>= (3, 10)`. |
| `sys.prefix != sys.base_prefix` | **The canonical venv detection.** In a venv, `prefix` points at the venv and `base_prefix` at the system Python. Outside one, they are equal. |
| `importlib.util.find_spec(name)` | Checks whether a module *can* be imported without importing it. Faster and safer than a `try: import`. |
| `shutil.which("python")` | What the shell would run for that command — the PATH question, answered from Python. |
| `os.environ.get("VIRTUAL_ENV")` | Set by activation. Its absence with a correct `sys.prefix` means you are using the venv without activating — fine, but worth knowing. |

### 7.2 Expected output

Two runs are shown: the "before" state and the "after" state. Getting from one to the other **is**
the exercise.

**Run 1 — outside a virtual environment.** `[EXECUTED]` 2026-09-07:

```
======================================================================
ENVIRONMENT DOCTOR
======================================================================

PYTHON
  version            : 3.12.3
  executable         : /usr/bin/python3
  OK: Python 3.12.3 meets the course minimum of 3.10.

VIRTUAL ENVIRONMENT
  sys.prefix         : /usr
  sys.base_prefix    : /usr
  VIRTUAL_ENV env var: (not set)
  PROBLEM: You are NOT in a virtual environment.
     sys.prefix equals sys.base_prefix, which means this interpreter is
     the system Python. Installing packages here can break system tools
     and makes your project unreproducible.
     Fix:
       python3 -m venv .venv
       source .venv/bin/activate        # Windows: .venv\Scripts\activate
       python -m pip install -r requirements.txt

WHAT THE SHELL RESOLVES
  python             : (not found)
  python3            : /usr/bin/python3
  pip                : /usr/bin/pip
  NOTE: 'python' is not on your PATH, only 'python3'.
     Inside an activated venv, 'python' will exist. Until then, use
     'python3'. Prefer 'python -m pip' over bare 'pip' always.

COURSE DEPENDENCIES
  numpy                          ok
  scikit-learn (sklearn)         MISSING
  pydantic                       MISSING
  fastapi                        MISSING
  uvicorn                        MISSING
  httpx                          MISSING
  pytest                         MISSING
  python-dotenv (dotenv)         MISSING
  tiktoken                       MISSING
  rank-bm25 (rank_bm25)          MISSING
  1 of 10 present.
  PROBLEM: dependencies are missing.
     Activate your venv, then:
       python -m pip install -r requirements.txt

======================================================================
SUMMARY: 2 problem(s) found. Work through them top to bottom.
======================================================================
```

Note `numpy` shows `ok` here only because this particular machine happens to have it installed
system-wide. That is exactly the situation a venv prevents: a dependency that works for you and
fails for everyone else, because it came from your machine rather than from `requirements.txt`.
Your own "before" output will differ, and that is fine.

**Run 2 — inside a virtual environment with dependencies installed.** `[EXECUTED]` 2026-09-07:

```
======================================================================
ENVIRONMENT DOCTOR
======================================================================

PYTHON
  version            : 3.12.3
  executable         : /home/bharathr/self/Learning/claude/ai/.venv/bin/python
  OK: Python 3.12.3 meets the course minimum of 3.10.

VIRTUAL ENVIRONMENT
  sys.prefix         : /home/bharathr/self/Learning/claude/ai/.venv
  sys.base_prefix    : /usr
  VIRTUAL_ENV env var: (not set)
  OK: You are inside a virtual environment.
  NOTE: VIRTUAL_ENV is not set, so you are using the venv's
     interpreter directly without activating. That works fine
     (it is what CI and Docker usually do), but 'pip' on your
     PATH may belong to a different Python. Use 'python -m pip'.

WHAT THE SHELL RESOLVES
  python             : (not found)
  python3            : /usr/bin/python3
  pip                : /usr/bin/pip
  NOTE: 'python' is not on your PATH, only 'python3'.
     Inside an activated venv, 'python' will exist. Until then, use
     'python3'. Prefer 'python -m pip' over bare 'pip' always.

COURSE DEPENDENCIES
  numpy                          ok
  scikit-learn (sklearn)         ok
  pydantic                       ok
  fastapi                        ok
  uvicorn                        ok
  httpx                          ok
  pytest                         ok
  python-dotenv (dotenv)         ok
  tiktoken                       ok
  rank-bm25 (rank_bm25)          ok
  10 of 10 present.
  OK: all course dependencies are importable.

======================================================================
SUMMARY: no problems found. Your environment is ready.
======================================================================
```

Three things changed, and each is worth understanding rather than just observing:

| Line | Before | After | Why |
|---|---|---|---|
| `sys.prefix` | `/usr` | inside `.venv` | The interpreter is now the venv's own |
| `sys.base_prefix` | `/usr` | `/usr` | **Unchanged** — it always points at the underlying system Python. The *difference* between the two is the venv signal |
| Dependencies | 1 of 10 | 10 of 10 | Installed into the venv, not the system |

The `VIRTUAL_ENV is not set` note appears because this run invoked `.venv/bin/python` directly
instead of activating first. That is a legitimate way to work — it is what Docker images and CI
pipelines do, since there is no interactive shell to activate in. If you activate normally, that note
disappears.

**Run 3 — the shadowing check.** Create a file called `json.py` in your working directory and re-run:

```
MODULE SHADOWING
  PROBLEM: ./json.py shadows the standard library module 'json'.
     Any 'import' of these will load YOUR file instead of the
     standard library, producing errors that make no sense.
     Fix: rename your file.
```

`[EXECUTED]` — this is Exercise 3 part 3, detected automatically. Python searches the current
directory before the standard library, so your `json.py` wins and every `json.dumps` call in your
project (and in your *dependencies*) breaks with an error that names a module you did not write.

**Verification:** after completing §6, your run should report `10 of 10 present` and
`SUMMARY: no problems found`.

---

## 8. Common mistakes and troubleshooting

1. **Forgetting to activate in a new terminal.** The commonest issue by far. `which python` first,
   always.
2. **Committing `.venv/` to git.** It is large and machine-specific. Already in this course's
   `.gitignore`.
3. **Using bare `pip`.** Use `python -m pip`.
4. **`--break-system-packages`.** Create a venv instead.
5. **Assuming install name = import name.** `python-dotenv` → `import dotenv`; `scikit-learn` →
   `import sklearn`; `rank-bm25` → `import rank_bm25`. The doctor script shows both.
6. **Repairing a broken venv.** Delete and recreate.
7. **Not pinning versions**, then wondering why CI differs from your laptop.

| Error message | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'X'` | Not activated, or not installed | `which python`; activate; `python -m pip install -r requirements.txt` |
| `error: externally-managed-environment` | pip outside a venv (PEP 668) | Create and activate a venv |
| `pip: command not found` | pip not on PATH | `python -m pip` |
| `Activate.ps1 cannot be loaded` (Windows) | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate |
| `SyntaxError` on `list[str]` or `X \| None` | Python < 3.10 | Install a newer Python |
| `No matching distribution found` | Version does not exist for your Python/platform | Check the pin; check your Python version |

---

## 9. Security, privacy, reliability and cost

- **Security.** `pip install` **runs code from the internet**. A package's build step executes on
  your machine with your permissions. Typosquatting (`reqeusts` for `requests`) is a real and active
  attack. Check names carefully, pin versions, and prefer well-known packages. In a work context,
  your organisation may run an internal index that vets packages — use it.
- **Reliability.** Unpinned dependencies mean your build is a function of *when* you ran it. Pin.
- **Reproducibility.** "Works on my machine" is almost always an environment difference. A venv plus
  pins plus a recorded Python version eliminates most of it. This becomes a governance requirement in
  M10-L13, where you must be able to reconstruct exactly what produced a result.
- **Cost.** Free — but a broken environment costs hours. The five minutes spent on the doctor script
  and a clean rebuild is the best-value time in this module.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Run `labs/m2/l01_doctor.py` with no venv active. Record what it reports.
2. Create and activate a venv, install `requirements.txt`, and re-run the doctor.
3. Paste both outputs into a note and write two sentences on what changed and why.

### Exercise 2 — Intermediate (~20 min)

1. With your venv active, run `python -m pip freeze | wc -l`. Compare that count with the number of
   lines in `requirements.txt`. Explain the difference in one sentence.
2. Run `python -m pip show fastapi`. Which packages does it require, and which packages require it?
3. Create a **second** venv called `.venv-test`, activate it, and install **only** `httpx`. Run the
   doctor. Which dependencies are missing, and what does this demonstrate?
4. Delete `.venv-test`. Confirm the original venv is unaffected.

### Exercise 3 — Challenge (~25 min)

Deliberately break things and fix them. For each, record the exact error and the fix:

1. Deactivate your venv and run `python3 -c "import fastapi"`. What error? Why is this correct
   behaviour rather than a bug?
2. With the venv active, run `python -m pip install pydantic==1.10.13` (downgrading). Then run
   `python -c "import pydantic; print(pydantic.VERSION)"`. Now re-run
   `python -m pip install -r requirements.txt`. What happened, and what does this tell you about how
   pip resolves pins?
3. Create a file called `json.py` in your working directory containing `print("hello")`. Then run
   `python -c "import json; print(json.dumps({}))"`. Explain what happened and why this is a nasty
   class of bug. Delete the file afterwards.
4. Write down the rule you would give a colleague to avoid the problem in part 3.

Part 3 is the most valuable. The answer key explains what shadowing is and why it produces
bewildering errors.

---

## 11. Quiz

**Q1.** What does activating a virtual environment actually do?

- A. Downloads a new copy of Python.
- B. Prepends the venv's `bin` directory to `PATH` and sets `VIRTUAL_ENV`, so `python` and `pip`
  resolve to the venv's copies.
- C. Permanently changes your system Python.
- D. Compiles your project.

**Q2.** How do you reliably detect from inside Python whether you are in a virtual environment?

- A. Check whether `.venv` exists in the current directory.
- B. Compare `sys.prefix` with `sys.base_prefix` — they differ inside a venv.
- C. Check whether `pip` is installed.
- D. Check `os.getcwd()`.

**Q3.** You see `error: externally-managed-environment`. What should you do?

- A. Re-run with `--break-system-packages`.
- B. Install as root with `sudo`.
- C. Create and activate a virtual environment, then install there.
- D. Uninstall the system Python.

**Q4.** Why does this course recommend `python -m pip install` over `pip install`?

- A. It is faster.
- B. It guarantees you get the pip belonging to the currently-running interpreter, eliminating a
  whole class of "installed but not found" confusion.
- C. `pip` is deprecated.
- D. It installs globally.

**Q5.** You installed `python-dotenv` but `import python_dotenv` fails. Why?

- A. The install failed silently.
- B. The distribution name and the import name differ; you import `dotenv`.
- C. The package requires activation.
- D. Hyphens are not allowed in Python.

**Q6.** What is the most important practical difference between Node's `node_modules` and Python's
`.venv`?

- A. `.venv` is smaller.
- B. Node isolates dependencies per project by default; Python isolation is opt-in and must be
  created deliberately, which is why global installs and "works on my machine" are common in Python.
- C. `node_modules` cannot be deleted.
- D. There is no meaningful difference.

**Q7.** Your `requirements.txt` pins `fastapi==0.141.1`. Does this guarantee a fully reproducible
install?

- A. Yes, completely.
- B. Not entirely — it pins your direct dependency but transitive dependencies may still float; a
  full `pip freeze` lockfile or a tool like pip-tools/uv is needed for that.
- C. No, pins are ignored by pip.
- D. Only on Linux.

**Q8.** After `deactivate`, `python3 -c "import fastapi"` raises `ModuleNotFoundError`. This means:

- A. The install was corrupted.
- B. The venv is working correctly — the package exists only inside it and the system Python cannot
  see it.
- C. You must reinstall globally.
- D. Python is misconfigured.

**Q9.** Your venv has become confusing and inconsistent. The best first action is:

- A. Debug `site-packages` by hand.
- B. Reinstall Python.
- C. Delete `.venv` and recreate it from `requirements.txt` — it is a rebuildable cache, not a source
  artefact.
- D. Edit `pyvenv.cfg`.

**Q10.** *(Written, rubric-graded.)* In under 70 words, explain to a colleague why `pip install`
without a virtual environment is a mistake. Give one concrete consequence.

---

## 12. Revision notes

- `python3` runs code · `pip` installs packages · `venv` isolates them per project.
- **Activation just edits `PATH`** and sets `VIRTUAL_ENV`. It is per-shell and does not persist.
- Detect a venv from Python with `sys.prefix != sys.base_prefix`.
- Always `python -m pip`, never bare `pip`.
- **Node isolates by default; Python does not.** That difference causes most Python environment pain.
- Pin exact versions in applications. `requirements.txt` pins direct deps; `pip freeze` captures
  transitive ones too.
- `externally-managed-environment` → create a venv. Never `--break-system-packages`.
- Install name ≠ import name: `python-dotenv`→`dotenv`, `scikit-learn`→`sklearn`,
  `rank-bm25`→`rank_bm25`.
- A broken venv is deleted and rebuilt, never repaired.
- `pip install` executes code from the internet. Pin, and check names for typosquatting.

---

## 13. Completion checklist

- [ ] `python3 --version` reports 3.10 or newer.
- [ ] I created `.venv` and activated it.
- [ ] `which python` points inside `.venv`.
- [ ] `pip install -r requirements.txt` completed successfully.
- [ ] The doctor script reports `10 of 10 present` and no problems.
- [ ] I ran the §6 step 7 isolation proof and understand why the error is correct.
- [ ] I completed Exercise 3 part 3 and can explain module shadowing.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python docs, `venv` — Creation of virtual environments.
  <https://docs.python.org/3/library/venv.html> `[UNVERIFIED]` link not re-checked 2026-09-07
- pip user guide. <https://pip.pypa.io/en/stable/user_guide/> `[UNVERIFIED]`
- PEP 668 — Externally managed environments (the §5.4 Failure 3 error).
  <https://peps.python.org/pep-0668/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L02 — Variables, Numbers, Strings and f-strings](M2-L02-variables-strings.md)

Your environment works. Next: the language itself, starting with the parts whose behaviour differs
from JavaScript in ways that cause real bugs.
