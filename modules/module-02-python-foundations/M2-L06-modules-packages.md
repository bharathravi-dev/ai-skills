# M2-L06 — Modules, Packages and Project Layout

| | |
|---|---|
| **Lesson ID** | M2-L06 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M2-L05](M2-L05-functions-scope.md) |

---

## 1. Learning objectives

1. **Explain** how Python resolves an import, and **debug** `ModuleNotFoundError` from first
   principles.
2. **Structure** a project as a package with a clear public API.
3. **Choose** between absolute and relative imports and justify the choice.
4. **Explain** what `__init__.py`, `__all__` and `if __name__ == "__main__"` each do.
5. **Avoid** circular imports and module shadowing.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Module** | A single `.py` file. Its name is the filename without the extension. |
| **Package** | A directory of modules, normally containing `__init__.py`. |
| **`__init__.py`** | Runs when the package is first imported. Defines the package's public surface. |
| **`sys.path`** | The ordered list of directories Python searches for imports. |
| **Absolute import** | `from myapp.services import retrieve` — the full path from a `sys.path` root. |
| **Relative import** | `from .services import retrieve` — relative to the current package. |
| **`__all__`** | A list of names exported by `from package import *`, and a statement of intent. |
| **`__name__`** | The module's name; `"__main__"` when run directly. |
| **Circular import** | Two modules importing each other. |
| **Shadowing** | A local file with the same name as a standard-library module. |
| **Entry point** | The script or function that starts your program. |
| **Editable install** | Installing your own package so imports resolve from anywhere. |

---

## 3. Plain-language explanation

Every `.py` file is a **module**. A directory of modules is a **package**. That is the whole model.

The part that causes trouble is *how Python finds them*. When you write `import ticketkit`, Python
walks `sys.path` in order and takes the first match:

1. The directory of the script you ran (or the current directory, in the REPL).
2. Directories in the `PYTHONPATH` environment variable.
3. The installed packages of the active interpreter (`site-packages`).

Two consequences explain almost every import error you will hit:

- **Where you run the script from changes what it can import.** `python3 run_demo.py` from inside a
  directory works; running the same file from one level up fails. Nothing about the code changed.
- **Your own file can shadow a real module.** A `json.py` in your directory is found *before* the
  standard library's, because step 1 comes before step 3. The M2-L01 doctor script checks for this.

### If you know Node

| Node | Python |
|---|---|
| `require('./utils')` | `from . import utils` or `from myapp import utils` |
| `module.exports = {...}` | Everything top-level is exported; `__all__` documents the intended surface |
| `node_modules` resolution walks up directories | `sys.path` is a **flat list**, searched in order |
| `index.js` | `__init__.py` |
| `if (require.main === module)` | `if __name__ == "__main__":` |

The key difference: **Node's resolver walks up the directory tree; Python's does not.** Python looks
in a fixed list of roots. That is why "it works when I run it from this folder" is such a common
Python problem and a rare Node one.

---

## 4. Analogy

**A package is a library building; `__init__.py` is the front desk.**

Callers ask the front desk for what they want. The desk knows which room holds it. Rearrange the
rooms and callers never notice, because they always go through the desk.

### Where the analogy breaks

1. **The desk can be bypassed.** Nothing stops someone writing
   `from ticketkit._rules import URGENT_WORDS`. The leading underscore is a *sign*, not a lock.
   Python has no `private`.
2. **The front desk does work on arrival.** `__init__.py` *executes* on first import. Put slow code
   or side effects there and every importer pays for it — a real cause of slow CLI startup.
3. **Two front desks can deadlock.** If A's `__init__` imports B and B's imports A, you get a
   circular import — a failure mode with no analogue in a real building.
4. **The building has one address; a module can be loaded twice** under different names
   (`ticketkit.models` and `models`), producing two distinct classes that fail `isinstance` checks
   against each other. Rare, deeply confusing, and always caused by inconsistent import style.

---

## 5. Detailed technical explanation

### 5.1 Import forms

```python
import json                          # whole module; use as json.dumps(...)
import numpy as np                   # aliased
from pathlib import Path             # one name from a module
from ticketkit.models import Ticket  # one name from a package module
from . import models                 # relative: same package
from .models import Ticket           # relative: specific name
from ticketkit import *              # avoid - unclear origin, shadowing risk
```

**Prefer `from x import y` for names you use often, and `import x` when the module name adds clarity
at the call site.** `json.dumps(...)` reads better than a bare `dumps(...)`.

**Never use `import *`** outside a REPL. It makes the origin of every name invisible and can
silently overwrite a name you already had.

### 5.2 Absolute versus relative

```python
# absolute - works anywhere the package is importable
from ticketkit.models import Ticket

# relative - only inside a package, resolved from the current module
from .models import Ticket
from ..shared import config          # one level up
```

| | Absolute | Relative |
|---|---|---|
| Readability | Explicit, greppable | Shorter, shows locality |
| Moving the package | Must update every path | Keeps working |
| Running a module directly | Works | **Fails** with `ImportError: attempted relative import with no known parent package` |
| Recommendation | **Default to this** | Fine within a cohesive package |

**This course uses absolute imports throughout**, because they are unambiguous and because relative
imports break the moment someone runs a module as a script — which happens constantly while
debugging.

### 5.3 `__init__.py` and the public API

```python
# ticketkit/__init__.py
from ticketkit.classify import classify_ticket
from ticketkit.models import Ticket

__all__ = ["Ticket", "classify_ticket"]
__version__ = "0.1.0"
```

This lets callers write:

```python
from ticketkit import Ticket, classify_ticket        # stable public API
```

rather than reaching into `ticketkit.classify`. **You can then reorganise the internals freely** —
split `classify.py` into three files, rename `_rules.py` — and no caller breaks. That is the real
value, and it is worth doing from the first day of a project.

`__all__` controls `import *` and, more usefully, documents intent to readers and linters.

**Keep `__init__.py` cheap.** It runs on first import. Loading a model, opening a database connection
or reading a file there makes every import slow and every test harder.

**Namespace packages** (a directory *without* `__init__.py`) are valid since Python 3.3 but are for
splitting one package across distributions. For ordinary projects, include `__init__.py`.

### 5.4 `if __name__ == "__main__":`

```python
def main() -> None:
    ...

if __name__ == "__main__":
    main()
```

When a file is **run** (`python3 script.py`), `__name__` is `"__main__"`. When it is **imported**,
`__name__` is the module's name. So the guard means *"only do this when run directly"*.

Without it, importing a module would execute its demo code — including in test collection, where
pytest imports every test file's dependencies.

### 5.5 Project layout

The layout this course uses, and which you should copy for Project 2:

```
project/
├── pyproject.toml          # project metadata and dependencies
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── ticketapi/
│       ├── __init__.py     # public API
│       ├── main.py         # FastAPI app (M2-L15)
│       ├── models.py       # Pydantic schemas (M2-L08)
│       ├── services.py     # business logic
│       ├── db.py           # database access (M2-L16)
│       └── config.py       # settings from env vars (M2-L09)
└── tests/
    ├── test_models.py
    └── test_services.py
```

**Why `src/`?** It is not decoration. Without it, running tests from the project root puts the root
on `sys.path`, so `import ticketapi` finds your *source directory* whether or not the package is
correctly installed. With `src/`, the only way tests can import your package is if it is genuinely
installed — so your tests exercise the same import path your users will. This catches missing
`__init__.py` files and packaging mistakes before release rather than after.

**Making your package importable during development:**

```bash
pip install -e .          # editable install: changes take effect immediately
```

This is the correct fix for `ModuleNotFoundError: No module named 'ticketapi'`. Manipulating
`sys.path` inside your code, or setting `PYTHONPATH`, are workarounds that will confuse the next
person.

A minimal `pyproject.toml`:

```toml
[project]
name = "ticketapi"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["fastapi==0.141.1", "pydantic==2.13.5"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

### 5.6 Circular imports

```python
# a.py
from b import helper          # imports b
def thing(): ...

# b.py
from a import thing           # imports a -- which is still executing
def helper(): ...
```

Result: `ImportError: cannot import name 'thing' from partially initialized module 'a'`.

Python executes a module top to bottom on first import. If A is halfway through and asks for B, and B
asks for A, the names A has not yet defined do not exist.

**Fixes, best first:**

1. **Extract the shared thing** into a third module both can import. Usually the circularity is
   telling you the design is wrong — two modules that need each other are often one module, or are
   missing a shared one.
2. **Import inside the function** rather than at module level, deferring it to call time.
3. **`if TYPE_CHECKING:`** — for imports needed only for type hints (M2-L08).

### 5.7 Assumptions and limitations

- `sys.path` manipulation at runtime works but is fragile and hides real packaging problems.
- Import time is startup time. A package importing heavy libraries at module level makes every CLI
  invocation slow.
- Module-level code runs **once per process**, and its state is shared by every importer — the
  M2-L05 mutable-default problem at module scale.

---

## 6. Worked example — a small package, built up

The package is real and runnable: [`labs/m2/l06_demo/`](../../labs/m2/l06_demo/).

```
labs/m2/l06_demo/
├── run_demo.py             # entry point
└── ticketkit/
    ├── __init__.py         # public API: Ticket, classify_ticket
    ├── models.py           # the Ticket dataclass
    ├── _rules.py           # internal word lists (underscore = private)
    └── classify.py         # the classifier
```

**Step 1 — `models.py` defines the data shape.**

```python
@dataclass
class Ticket:
    ticket_id: str
    text: str
    channel: str = "email"
    tags: list[str] = field(default_factory=list)
```

Note `default_factory=list`. A bare `tags: list[str] = []` would be **the M2-L05 mutable default
bug**, shared by every `Ticket` instance. Dataclasses actually raise a `ValueError` if you try it —
one of the few places Python protects you from this. Classes are M2-L07; the point here is that the
bug follows you.

**Step 2 — `_rules.py` holds internals.** The leading underscore says "not public". Nothing enforces
it.

**Step 3 — `classify.py` uses absolute imports:**

```python
from ticketkit._rules import BILLING_WORDS, URGENT_WORDS, contains_any
from ticketkit.models import Ticket
```

Explicit and greppable. You can find every user of `_rules` with one search.

**Step 4 — `__init__.py` defines the public surface:**

```python
from ticketkit.classify import classify_ticket
from ticketkit.models import Ticket

__all__ = ["Ticket", "classify_ticket"]
__version__ = "0.1.0"
```

**Step 5 — the caller stays simple:**

```python
from ticketkit import Ticket, classify_ticket
```

The caller does not know that `classify_ticket` lives in `classify.py`, or that `_rules.py` exists at
all. **Split `classify.py` into five files tomorrow and this line still works.**

---

## 7. Practical activity

```bash
cd labs/m2/l06_demo
python3 run_demo.py
```

Then, from the **course root**, run it again to see the import fail — that contrast is the lesson.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `from ticketkit.classify import classify_ticket` in `__init__.py` | Re-export: gives callers a stable API independent of internal layout. |
| `__all__ = [...]` | Declares the public surface. |
| `field(default_factory=list)` | Fresh list per instance — the M2-L05 fix, in dataclass form. |
| `sys.path[0]` | Printed by the demo so you can see *why* the import resolved. |
| `if __name__ == "__main__":` | The demo runs only when executed directly. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, run from inside `labs/m2/l06_demo`:

```
======================================================================
PACKAGE IMPORTS
======================================================================

  ticketkit.__version__ : 0.1.0
  ticketkit.__all__     : ['Ticket', 'classify_ticket']
  ticketkit.__file__    : .../ticketkit/__init__.py

  sys.path[0] (where Python looks first):
    /home/bharathr/self/Learning/claude/ai/labs/m2/l06_demo

  id    urgent   billing   words  text
  ----------------------------------------------------------------
  T-1   True     False     7      Our checkout is down, this is 
  T-2   False    True      6      Question about the invoice fro
  T-3   False    False     6      How do I change my avatar?

  Note what the caller did NOT have to know:
    - that classify_ticket lives in ticketkit/classify.py
    - that the word lists live in ticketkit/_rules.py
  __init__.py re-exported them, so the internal layout can change
  without breaking any caller.

  The dataclass default_factory in action (M2-L05's bug, avoided):
    a.tags = ['escalated']
    b.tags = []   <-- separate lists, thanks to default_factory
======================================================================
```

### 7.3 Now break it deliberately

From the **course root** instead:

```bash
python3 labs/m2/l06_demo/run_demo.py
```

`[EXECUTED]` — this succeeds, because `sys.path[0]` is the *script's own directory*, not your
current directory. Look at the `sys.path[0]` line: it still points at `l06_demo`.

Now try the form that genuinely fails:

```bash
python3 -c "import ticketkit"
```

```
ModuleNotFoundError: No module named 'ticketkit'
```

Here `sys.path[0]` is the current directory (the course root), which contains no `ticketkit`. **The
code is identical; only the entry point changed.** This is the mechanism behind almost every import
error you will hit, and the permanent fix is `pip install -e .` (§5.5) rather than moving files
around until it works.

### 7.4 And now shadowing, deliberately

Create a file `labs/m2/l06_demo/pathlib.py` containing one line, `VALUE = 1`, then run the demo
again. `[EXECUTED]`:

```
Traceback (most recent call last):
  File ".../labs/m2/l06_demo/run_demo.py", line 9, in <module>
    from pathlib import Path
ImportError: cannot import name 'Path' from 'pathlib' (.../labs/m2/l06_demo/pathlib.py)
```

Your one-line file replaced the standard library's `pathlib` for the entire program, because the
script's own directory is searched first.

**Read the last line of that traceback closely.** Python tells you exactly which file it loaded:
`(.../labs/m2/l06_demo/pathlib.py)`. That parenthesised path is the whole diagnosis. Engineers lose
an hour to this bug precisely because they read "cannot import name 'Path' from 'pathlib'", conclude
their Python installation is broken, and never reach the end of the line.

Now try the same with `json.py` instead: **nothing breaks**, because `run_demo.py` never imports
`json`. The bug is latent — it will appear the moment any file in the project, or any *dependency*,
imports `json`. That delayed, action-at-a-distance quality is what makes shadowing so unpleasant, and
it is why the M2-L01 doctor script checks for it proactively.

Delete the file afterwards, **and** delete `__pycache__` — a stale compiled copy of your shadowing
module can keep the failure alive after the source is gone.

---

## 8. Common mistakes and troubleshooting

1. **Naming a file after a standard-library module** (`json.py`, `types.py`, `logging.py`).
2. **`import *`.**
3. **Expensive work in `__init__.py`.**
4. **Relative imports in a module you also run as a script.**
5. **Circular imports** — usually a design signal.
6. **`sys.path.append(...)` hacks** instead of an editable install.
7. **Forgetting `__init__.py`**, giving a namespace package that behaves subtly differently.
8. **Mixing import styles** so one module is loaded twice under two names.

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'X'` | `X` not on `sys.path` | `pip install -e .`; check where you ran from |
| `ImportError: attempted relative import with no known parent package` | Ran a module with relative imports directly | Use absolute imports, or `python -m package.module` |
| `ImportError: cannot import name 'Y' from partially initialized module` | Circular import | Extract shared code to a third module |
| `AttributeError: module 'json' has no attribute 'dumps'` | Local `json.py` shadowing | Rename your file; delete `__pycache__` |
| Class fails `isinstance` against itself | Module imported twice under two names | Use one consistent import style |
| Imports work in the IDE, fail on the command line | IDE adds the project root to `sys.path` | Install the package properly |

---

## 9. Security, privacy, reliability and cost

- **Security.** Import order is a supply-chain surface. A malicious or typosquatted package earlier on
  `sys.path` can shadow a real one, and module-level code executes on import. Pin versions (M2-L01)
  and never add untrusted directories to `sys.path`.
- **Reliability.** Module-level state is shared per process. A module-level cache or client is
  effectively a global, with the concurrency implications of M2-L13.
- **Cost.** Import time is cold-start time. On AWS Lambda (M11-L13) a package importing heavy
  libraries at module level directly increases cold-start latency and therefore billed duration.
  Import expensive things lazily inside functions where it matters.
- **Privacy.** Do not put credentials in `__init__.py` or any module-level constant. M2-L19.

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

1. Run `run_demo.py` from inside `labs/m2/l06_demo`. Record `sys.path[0]`.
2. Run it from the course root. Record `sys.path[0]` again and explain why it still works.
3. Run `python3 -c "import ticketkit"` from the course root. Record the error and explain the
   difference from step 2.

### Exercise 2 — Intermediate (~25 min)

Extend `ticketkit`:

1. Add `ticketkit/priority.py` with `score_priority(ticket) -> int` returning 3 for urgent, 2 for
   billing, else 1.
2. Export it from `__init__.py` and add it to `__all__`.
3. Update `run_demo.py` to use it via `from ticketkit import score_priority`.
4. Now **move** `_rules.py` to `ticketkit/internal/rules.py` (with an `__init__.py`). Update only the
   internal imports. Confirm `run_demo.py` still works **unchanged**. Explain what made that possible.

### Exercise 3 — Challenge (~25 min)

1. Deliberately create a circular import: make `models.py` import from `classify.py`. Record the exact
   error, including which name it says is unavailable.
2. Fix it three different ways (shared third module, function-level import, `TYPE_CHECKING`). State
   the trade-off of each.
3. Create `labs/m2/l06_demo/pathlib.py` containing `VALUE = 1`, then run `run_demo.py`. Record the
   exact error. Note that it names the file responsible — read that line carefully, because it is
   the clue that turns a bewildering failure into a five-second fix.
   Then try the same with `json.py` instead. Nothing breaks. Explain why the two differ.
   Finally delete the file **and** `__pycache__`, and explain why the second step matters.
4. Convert `l06_demo` into a proper installable package with a `pyproject.toml` and `src/` layout,
   then `pip install -e .` into your venv and import it from a different directory. Report what
   changed about `sys.path`.

---

## 11. Quiz

**Q1.** What makes a directory a package?

- A. Any directory of `.py` files.  B. The presence of `__init__.py` (for a regular package).
- C. A `pyproject.toml`.  D. Being listed in `sys.path`.

**Q2.** Where does Python look first when resolving `import X`?

- A. `site-packages`.  B. The directory of the script being run (or the current directory in a REPL).
- C. Alphabetically through all directories.  D. `PYTHONPATH` only.

**Q3.** Why does a local file named `json.py` break your program?

- A. `json` is a reserved word.
- B. The script's directory is searched before the standard library, so your file is imported instead
  of the real `json` module.
- C. Python forbids duplicate module names.
- D. It does not break anything.

**Q4.** What is the main practical benefit of re-exporting names in `__init__.py`?

- A. Faster imports.
- B. Callers depend on a stable public API rather than internal file paths, so you can reorganise the
  internals without breaking them.
- C. It makes names private.
- D. It is required by Python.

**Q5.** `ImportError: attempted relative import with no known parent package` means:

- A. The file is missing.
- B. A module using relative imports was run directly as a script rather than imported as part of its
  package.
- C. `__init__.py` is missing.
- D. The package is not installed.

**Q6.** Why does the course recommend a `src/` layout?

- A. It looks tidier.
- B. Without it, the project root is on `sys.path` during testing, so imports succeed whether or not
  the package is correctly installed — hiding packaging errors until release.
- C. It is required by pytest.
- D. It makes imports faster.

**Q7.** What is the best first fix for a circular import?

- A. Add `sys.path` entries.
- B. Extract the shared code into a third module that both import — the circularity usually indicates
  a design problem.
- C. Rename one of the files.
- D. Use `import *`.

**Q8.** What does `if __name__ == "__main__":` protect against?

- A. Syntax errors.
- B. Module-level demo or script code running when the module is merely imported, for example during
  test collection.
- C. Circular imports.
- D. Shadowing.

**Q9.** Why should `__init__.py` avoid expensive work?

- A. It cannot contain function calls.
- B. It executes on first import, so every importer — including tests and CLI startup — pays that
  cost, which on serverless directly increases billed cold-start time.
- C. It runs on every function call.
- D. Python limits its size.

**Q10.** *(Written, rubric-graded.)* In under 70 words, explain to a colleague why
`sys.path.append("../..")` at the top of a file is a bad fix for an import error, and what to do
instead.

---

## 12. Revision notes

- Module = one `.py` file. Package = a directory with `__init__.py`.
- **Import resolution:** script's own directory → `PYTHONPATH` → `site-packages`. **First match
  wins**, which is why local files can shadow the standard library.
- **Node walks up directories; Python searches a flat `sys.path` list.** That difference explains
  most Python import confusion.
- **Default to absolute imports.** Relative imports break when a module is run directly.
- **Never `import *`.**
- `__init__.py` defines the **public API** by re-exporting; `__all__` documents it. Keep it cheap —
  it runs on import, and import time is cold-start time.
- `if __name__ == "__main__":` = "only when run directly".
- **`src/` layout** forces tests to use the installed package, catching packaging errors early.
- `pip install -e .` is the correct fix for `ModuleNotFoundError` on your own package. Never
  `sys.path.append`.
- **Circular imports are a design signal.** Extract a third module first.

---

## 13. Completion checklist

- [ ] I ran the demo from two locations and can explain both `sys.path[0]` values.
- [ ] I made `python3 -c "import ticketkit"` fail and can explain why.
- [ ] I extended the package and moved `_rules.py` without breaking the caller.
- [ ] I created and fixed a circular import three ways.
- [ ] I reproduced the shadowing bug and know why `__pycache__` must also be cleared.
- [ ] I can explain the `src/` layout rationale.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python tutorial, "Modules". <https://docs.python.org/3/tutorial/modules.html> `[UNVERIFIED]`
- Python reference, "The import system".
  <https://docs.python.org/3/reference/import.html> `[UNVERIFIED]`
- Python Packaging User Guide, "Packaging Python Projects".
  <https://packaging.python.org/en/latest/tutorials/packaging-projects/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L07 — Classes, Dataclasses and Composition over Inheritance](M2-L07-classes-dataclasses.md)

You saw a `@dataclass` in this lesson's package. Next: what it actually generates, when to use a
class at all, and why composition beats inheritance in the kind of code you will write in this
course.
