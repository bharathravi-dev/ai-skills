# M2-L09 — Files, Paths, CSV, JSON and Environment Variables

| | |
|---|---|
| **Lesson ID** | M2-L09 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L05](M2-L05-functions-scope.md) |

---

## 1. Learning objectives

1. **Use** `pathlib` for all path handling and **explain** why string concatenation is wrong.
2. **Read and write** text files safely with explicit encoding and context managers.
3. **Parse** CSV and JSON, including the encoding and type pitfalls of each.
4. **Load** configuration from environment variables with defaults and type conversion.
5. **Stream** a large file without loading it into memory.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Path** | A location in a filesystem. |
| **`pathlib.Path`** | The object-oriented path API. Preferred over string manipulation. |
| **Absolute path** | From the filesystem root: `/home/user/data.csv`. |
| **Relative path** | From the current working directory: `data/tickets.csv`. |
| **CWD** | Current working directory — where the process was started, not where the file lives. |
| **Context manager** | The `with` statement; guarantees cleanup. |
| **Encoding** | How characters map to bytes. Always specify `utf-8`. |
| **Text vs binary mode** | `"r"` decodes to `str`; `"rb"` gives raw `bytes`. |
| **CSV** | Comma-separated values. Everything is a string. |
| **JSON** | JavaScript Object Notation. Has types, but a limited set. |
| **JSONL** | One JSON object per line. The standard for datasets and logs. |
| **Environment variable** | A key–value string pair from the process environment. |
| **`.env` file** | A local file of environment variables, loaded by `python-dotenv`. Never committed. |

---

## 3. Plain-language explanation

Four ways data gets into your program from outside, and each has one classic mistake.

| Source | The classic mistake |
|---|---|
| **Files** | Building paths with string concatenation; forgetting `encoding="utf-8"` |
| **CSV** | Forgetting that **every value is a string** |
| **JSON** | Assuming Python types survive the round trip |
| **Environment variables** | Forgetting they are **always strings**, and crashing when one is missing |

The unifying theme, which connects directly to M2-L08: **all four are untrusted input from outside
your program.** They deserve validation at the boundary.

### If you know Node

| Node | Python |
|---|---|
| `path.join(a, b)` | `Path(a) / b` |
| `fs.readFileSync(p, 'utf8')` | `Path(p).read_text(encoding="utf-8")` |
| `JSON.parse` / `JSON.stringify` | `json.loads` / `json.dumps` |
| `process.env.FOO` | `os.environ["FOO"]` or `os.getenv("FOO", default)` |
| `dotenv` | `python-dotenv` |
| `__dirname` | `Path(__file__).parent` |

`Path(a) / b` using the division operator is unusual at first and quickly becomes natural. It handles
separators, so the same code works on Windows.

---

## 4. Analogy

**A file path is a postal address; the CWD is "where you are standing".**

A relative path is "two streets over" — meaningless unless you know where the speaker is. An absolute
path is the full address, which works from anywhere.

### Where the analogy breaks

1. **You can move while a program runs.** The CWD is a property of the *process*, not of your code,
   and it is wherever the user happened to be when they typed the command. That is why
   `open("data.csv")` works in your terminal and fails in cron, in a container, or in a test runner.
2. **There are two "heres".** The CWD, and the directory containing your source file
   (`Path(__file__).parent`). They are frequently different, and confusing them is the most common
   file bug in Python.
3. **Addresses are stable; paths are not.** A file can be deleted between your check and your open —
   a race condition (§8).
4. **Postal addresses do not have encodings.** File contents do, and getting it wrong corrupts data
   silently rather than failing loudly.

---

## 5. Detailed technical explanation

### 5.1 `pathlib`

```python
from pathlib import Path

data_dir = Path("data")
csv_file = data_dir / "tickets.csv"        # the / operator joins

csv_file.exists()
csv_file.is_file()
csv_file.suffix          # '.csv'
csv_file.stem            # 'tickets'
csv_file.name            # 'tickets.csv'
csv_file.parent          # Path('data')
csv_file.absolute()
csv_file.stat().st_size  # bytes

data_dir.mkdir(parents=True, exist_ok=True)   # create, no error if present
list(data_dir.glob("*.csv"))                  # matching files
list(data_dir.rglob("*.json"))                # recursive
```

**Why not string concatenation?** `"data" + "/" + "tickets.csv"` breaks on Windows, produces
`data//tickets.csv` if a segment already ends in a slash, and cannot handle `..` normalisation.
`Path` handles all of it.

**The `__file__` pattern** — the fix for "works in my terminal, fails in cron":

```python
HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "tickets.csv"
```

This is relative to the *source file*, not to wherever the process was started. **Use it for any file
shipped alongside your code.** Use CWD-relative paths only for files the user supplies.

### 5.2 Reading and writing

```python
text = path.read_text(encoding="utf-8")
path.write_text(content, encoding="utf-8")

with open(path, "r", encoding="utf-8") as f:      # for larger files
    for line in f:
        process(line)
```

**Always pass `encoding="utf-8"`.** Without it Python uses a platform default which differs between
machines — so a file that reads correctly on your Linux laptop can raise `UnicodeDecodeError` on a
colleague's Windows machine, or worse, decode to subtly wrong characters. This is a real
cross-platform bug and the fix is one keyword argument.

**`with` guarantees the file is closed**, even if an exception is raised. Without it, a file left
open in a long-running server leaks a file descriptor, and eventually the process runs out.

Modes: `"r"` read · `"w"` write (**truncates**) · `"a"` append · `"x"` create-or-fail ·
`"rb"`/`"wb"` binary.

`"x"` is underused and useful: it fails if the file exists, preventing accidental overwrites.

### 5.3 CSV

```python
import csv

with open(path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        print(row["ticket_id"], row["priority"])
```

**`newline=""` is required**, not optional. Without it, the `csv` module's own line handling collides
with Python's universal newline translation, and rows containing embedded newlines in quoted fields
split incorrectly. It is in the standard library documentation for exactly this reason.

**Every CSV value is a string.** `row["priority"]` is `"3"`, not `3`. Convert explicitly, and be
ready for failure:

```python
priority = int(row["priority"])     # ValueError if it is "" or "high"
```

Writing:

```python
with open(path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["ticket_id", "priority"])
    writer.writeheader()
    writer.writerows(rows)
```

Do **not** write CSV by joining strings with commas. A field containing a comma, a quote or a newline
will silently corrupt the file. The `csv` module quotes and escapes correctly.

### 5.4 JSON

```python
import json

data = json.loads(text)              # from a string
data = json.load(file_object)        # from a file
text = json.dumps(data, indent=2)    # to a string
json.dump(data, file_object)         # to a file
```

**Type mapping:**

| Python | JSON | Round-trip |
|---|---|---|
| `dict` | object | ✅ |
| `list` | array | ✅ |
| `tuple` | array | ⚠️ **comes back as a list** |
| `str` | string | ✅ |
| `int`, `float` | number | ✅ |
| `True`/`False` | true/false | ✅ |
| `None` | null | ✅ |
| `set` | — | ❌ `TypeError` |
| `datetime` | — | ❌ `TypeError` |
| `Decimal` | — | ❌ `TypeError` |

The last three are the ones that bite. Convert explicitly: `list(my_set)`, `dt.isoformat()`,
`str(decimal)`. Or supply `default=str` to `dumps` — convenient, but it silently stringifies
*everything* unknown, so be deliberate.

Also note: **JSON object keys are always strings.** `json.loads(json.dumps({1: "a"}))` returns
`{"1": "a"}` — the integer key became a string, silently.

**JSONL** (one object per line) is the standard for datasets and logs, because it streams and appends
cleanly:

```python
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")
```

You will use JSONL for evaluation datasets in M5-L18 and for traces in M8-L17.

### 5.5 Environment variables

```python
import os

api_key = os.environ["ANTHROPIC_API_KEY"]        # KeyError if missing
log_level = os.getenv("LOG_LEVEL", "INFO")       # default
```

**Three rules:**

1. **Everything is a string.** `os.getenv("MAX_TOKENS")` gives `"1024"`. Convert explicitly.
2. **Booleans need care.** `bool("false")` is `True` — the string is non-empty. Compare explicitly:
   `os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}`.
3. **Fail loudly at startup for required values.** A missing API key should stop the process
   immediately with a clear message, not fail on the first request an hour later.

```python
from dotenv import load_dotenv
load_dotenv()          # reads .env into the environment; does NOT overwrite existing vars
```

`.env` is for local development only. In production, values come from the platform's secret
management (M11-L17). `.env` must never be committed — it is in this course's `.gitignore`, and
M2-L19 covers this properly.

**The config pattern used throughout this course:**

```python
@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    max_tokens: int
    debug: bool

def load_settings() -> Settings:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env.")
    return Settings(
        api_key=api_key,
        model=os.getenv("LLM_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
        debug=os.getenv("DEBUG", "").lower() in {"1", "true", "yes"},
    )
```

Load once at startup, validate immediately, pass the frozen object around. **Do not call
`os.getenv` scattered through your code** — it makes configuration untestable and its failure modes
unpredictable.

### 5.6 Streaming large files

```python
# Loads the ENTIRE file into memory
lines = path.read_text(encoding="utf-8").splitlines()

# Streams one line at a time - constant memory
with open(path, encoding="utf-8") as f:
    for line in f:
        process(line)
```

This is the M2-L04 generator lesson applied to files. A 2 GB log file will not fit in a 512 MB
container, and this is exactly how ingestion pipelines fail in Module 7.

### 5.7 Assumptions and limitations

- `pathlib` abstracts separators but not permissions, case-sensitivity or symlink behaviour, which
  still differ between platforms.
- `json` is not the fastest parser; `orjson` is faster for large payloads.
- Environment variables are visible to the process and often to anything that can inspect it. They
  are better than hard-coded secrets, not a secrets-management solution (M11-L17).

---

## 6. Worked example — a robust dataset loader

Load synthetic tickets from CSV, validate each row, write valid ones as JSONL, and report failures.
This is the shape of every ingestion script in Module 7.

**Attempt 1 — naive:**

```python
import csv
rows = list(csv.DictReader(open("tickets.csv")))
for row in rows:
    priority = int(row["priority"])
```

Five problems: the file is never closed; no encoding; no `newline=""`; a CWD-relative path; and one
bad row kills the whole load with a `ValueError` that does not say which row.

**Attempt 2 — robust:**

```python
from pathlib import Path
import csv, json
from pydantic import BaseModel, Field, ValidationError

HERE = Path(__file__).resolve().parent

class Ticket(BaseModel):
    ticket_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    priority: int = Field(ge=1, le=5)
    channel: str

def load(csv_path: Path) -> tuple[list[Ticket], list[dict]]:
    valid: list[Ticket] = []
    failures: list[dict] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):   # 2: header is line 1
            try:
                valid.append(Ticket.model_validate(row))
            except ValidationError as exc:
                failures.append({
                    "line": line_no,
                    "row": row,
                    "errors": [
                        {"field": ".".join(str(p) for p in e["loc"]), "msg": e["msg"]}
                        for e in exc.errors()
                    ],
                })
    return valid, failures
```

**The design decisions worth noting:**

1. **`start=2`** because the header is line 1, so reported line numbers match what the user sees in
   a spreadsheet. A small thing that saves real time.
2. **Collect failures, do not abort.** One bad row in ten thousand should not fail the load. Return
   both lists and let the caller decide the policy.
3. **Pydantic does the string conversion.** `priority` arrives as `"3"` and is coerced to `3` —
   exactly the CSV problem from §5.3, solved by the M2-L08 tool instead of a manual `int()` wrapped
   in `try`.
4. **Structured failure records**, not log strings, so they can be written to a file, counted, or
   displayed.

**Writing JSONL:**

```python
def write_jsonl(path: Path, tickets: list[Ticket]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for t in tickets:
            f.write(t.model_dump_json() + "\n")
```

`mkdir(parents=True, exist_ok=True)` means the output directory does not have to exist, and running
twice is not an error. **Idempotent by default** — a habit that matters for pipelines (M8-L12).

**Reporting:**

```
Loaded 12 valid tickets, 3 rejected.
  line 5: priority — Input should be less than or equal to 5 (got 9)
  line 8: text — String should have at least 1 character (got '')
  line 11: priority — Input should be a valid integer (got 'high')
```

A user can fix their spreadsheet from that. Compare with `ValueError: invalid literal for int()`.

---

## 7. Practical activity

**File:** [`labs/m2/l09_files.py`](../../labs/m2/l09_files.py)

**Requires the venv** (uses pydantic):

```bash
source .venv/bin/activate
python labs/m2/l09_files.py
```

Generates a synthetic CSV with deliberate defects in a temporary directory, runs the §6 loader,
writes JSONL, demonstrates the JSON type round-trip surprises, shows environment-variable typing
traps, and measures streaming against full-read memory.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `Path(__file__).resolve().parent` | Anchors paths to the source file, not the CWD. |
| `tempfile.TemporaryDirectory()` | The lab writes nothing into your repository. |
| `csv.DictReader(f)` with `newline=""` | Correct CSV line handling. |
| `enumerate(reader, start=2)` | Line numbers matching a spreadsheet. |
| `json.dumps(..., default=str)` | Handles unserialisable types — deliberately, not accidentally. |
| `tracemalloc` | Real memory measurement for the streaming comparison. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with pydantic 2.13.5, Python 3.12.3. Temporary paths and memory figures will
differ on your machine:

```
==========================================================================
FILES, CSV, JSON AND ENVIRONMENT VARIABLES
==========================================================================

--------------------------------------------------------------------------
1. PATHS - anchored to the file, not the working directory
--------------------------------------------------------------------------
  Path.cwd()                     : /home/bharathr/self/Learning/claude/ai
  Path(__file__).resolve().parent: /home/bharathr/self/Learning/claude/ai/labs/m2

  These are different right now, and they are different again when
  the script runs under cron, in a container, or from pytest.
  For files shipped WITH your code, always use the second one.

  HERE / 'data' / 'tickets.csv'  : ...rning/claude/ai/labs/m2/data/tickets.csv
    .name   = tickets.csv
    .stem   = tickets
    .suffix = .csv
    .parent = ...aude/ai/labs/m2/data

--------------------------------------------------------------------------
2. CSV - every value is a string, and quoting matters
--------------------------------------------------------------------------
  Wrote 7 rows.

  Raw file bytes for the two awkward rows:
    'T-006,"Order 12, item 3, wrong colour",4,email'
    'T-007,"Line one'
    'Line two",5,chat'
    ^ the csv module quoted the comma and the newline for us.

  Loaded 4 valid tickets, 3 rejected.
    line 4: priority - Input should be less than or equal to 5 (got '9')
    line 5: text - String should have at least 1 character (got '')
    line 6: priority - Input should be a valid integer, unable to parse string as an integer (got 'high')

  Every message names the line, the field and the value. A user
  can fix their spreadsheet from that. Compare with the bare
  'ValueError: invalid literal for int()' a naive loader gives.

  Note priority came in as the STRING '2' and is now:
    2 (int) - Pydantic did the conversion

--------------------------------------------------------------------------
3. JSONL - one object per line, for datasets and traces
--------------------------------------------------------------------------
  Wrote 4 lines to tickets.jsonl
  First line:
    {"ticket_id":"T-001","text":"Refund not received","priority":2,"channel":"email"}
  Read back 4 tickets. Round trip intact: True

--------------------------------------------------------------------------
4. JSON - which Python types survive the round trip
--------------------------------------------------------------------------
  key       before            after             same type?
  string    str               str               True
  int       int               int               True
  float     float             float             True
  bool      bool              bool              True
  none      NoneType          NoneType          True
  list      list              list              True
  tuple     tuple             list              False   <-- CHANGED
  nested    dict              dict              True

  Integer keys become strings, silently:
    json.loads(json.dumps({1: 'a'})) -> {'1': 'a'}

  And these raise outright:
    set        TypeError: Object of type set is not JSON serializable
    datetime   TypeError: Object of type datetime is not JSON serializable
    Decimal    TypeError: Object of type Decimal is not JSON serializable

  default=str handles them - but converts EVERYTHING unknown, so
  use it deliberately rather than as a reflex:
    {"d": "2026-01-01 00:00:00"}

--------------------------------------------------------------------------
5. ENVIRONMENT VARIABLES - always strings
--------------------------------------------------------------------------
  os.getenv('DEMO_MAX_TOKENS') = '2048' (str)
  int(raw)                     = 2048

  THE BOOLEAN TRAP - DEMO_DEBUG is the string 'false':
    bool(os.getenv('DEMO_DEBUG'))  = True   <-- WRONG
    parse_bool(os.getenv(...))     = False   <-- correct

  input       bool()    parse_bool()
  'true'      True      True
  'false'     True      False
  '1'         True      True
  '0'         True      False
  'yes'       True      True
  ''          False     False
  'no'        True      False

  Required values must fail AT STARTUP, not on first use:
    RuntimeError: DEMO_MISSING_KEY is not set. Copy .env.example to .env and fill it in.
    loaded once into a frozen dataclass: model='claude-sonnet-5' max_tokens=2048 debug=False

--------------------------------------------------------------------------
6. PATH TRAVERSAL - never trust a user-supplied filename
--------------------------------------------------------------------------
  'reports/q1.csv'       ALLOWED -> ...x_ss78v/uploads/reports/q1.csv
  '../../etc/passwd'     BLOCKED  (path escapes the base directory: '../../etc/passwd')
  '/etc/passwd'          BLOCKED  (path escapes the base directory: '/etc/passwd')
  'ok.txt'               ALLOWED -> ...tmp/tmpxx_ss78v/uploads/ok.txt

  Note '/etc/passwd' is blocked too: an ABSOLUTE path given to
  Path.__truediv__ discards the base entirely. Checking for '..'
  alone would have missed it.

--------------------------------------------------------------------------
7. STREAMING vs READING A WHOLE FILE
--------------------------------------------------------------------------
  Generated big.jsonl: 17.1 MB, 200,000 lines

  full read  : 200,000 lines, peak     43.8 MB
  streaming  : 200,000 lines, peak      0.0 MB
  ratio      : 2,009x less memory

  This file is small. Scale it to a 2 GB corpus in a 512 MB
  container and the full read is an OOM kill, not a slow function.

==========================================================================
```

### 7.3 Reading the result

**Section 2 shows the CSV module earning its place.** Look at the raw bytes it wrote:

```
'T-006,"Order 12, item 3, wrong colour",4,email'
'T-007,"Line one'
'Line two",5,chat'
```

A field containing commas was quoted; a field containing a newline was quoted and **spans two
physical lines in the file**. The reader reassembles it correctly. Any hand-rolled
`",".join(values)` writer produces a file that silently parses into the wrong number of columns —
and `newline=""` is what makes the reader handle that second case.

The failure report is the other half:

```
line 4: priority - Input should be less than or equal to 5 (got '9')
line 5: text - String should have at least 1 character (got '')
line 6: priority - Input should be a valid integer, unable to parse string as an integer (got 'high')
```

Line number, field name, rule violated, offending value. A non-technical user can fix their
spreadsheet from that without asking you anything. And note `priority` arrived as the *string* `'2'`
and came out as the *integer* `2` — the CSV type problem solved by the M2-L08 validator rather than
by a hand-written `int()` wrapped in `try`.

**Section 4 confirms the round-trip table.** Only `tuple` changed type (to `list`), integer keys
became strings silently, and `set`, `datetime` and `Decimal` all raised. That last group is the
one that catches people, because those are exactly the types you accumulate in real code — a set of
seen IDs, a timestamp, a monetary amount from M2-L02.

**Section 5's boolean table is the trap in full:**

| value | `bool()` | `parse_bool()` |
|---|---|---|
| `'true'` | True | True |
| `'false'` | **True** | False |
| `'0'` | **True** | False |
| `'no'` | **True** | False |
| `''` | False | False |

`bool()` returns `True` for **every non-empty string**, so `DEBUG=false` enables debug mode. This
is not hypothetical: it is how debug logging ends up on in production, printing request bodies into
logs.

**Section 6 contains the detail most path-traversal defences miss.** Both of these were blocked:

```
'../../etc/passwd'     BLOCKED
'/etc/passwd'          BLOCKED
```

The second is the interesting one. `Path("/srv/uploads") / "/etc/passwd"` evaluates to
`/etc/passwd` — an absolute right-hand operand **discards the base entirely**. A defence that only
scans for `..` would let it straight through. Resolving and checking `is_relative_to(base)` catches
both forms, which is why that is the correct pattern and why you will see it again in M9-L13.

**Section 7:** 43.8 MB against effectively nothing, a 2,009× difference, on a file of only 17 MB.
The full-read figure scales linearly with file size; the streaming figure does not move. That is the
difference between an ingestion job that survives a 2 GB corpus in a small container and one that is
OOM-killed.

**Verification:** confirm 4 valid / 3 rejected with those three line numbers, `tuple` as the only
changed type, `'false'` showing `True` under `bool()`, and both traversal attempts blocked.

---

## 8. Common mistakes and troubleshooting

1. **String concatenation for paths.**
2. **Omitting `encoding="utf-8"`.**
3. **Omitting `newline=""` for CSV.**
4. **Forgetting CSV values are strings.**
5. **`open()` without `with`.**
6. **CWD-relative paths for files shipped with your code.** Use `Path(__file__).parent`.
7. **`bool(os.getenv("DEBUG"))`** — `"false"` is truthy.
8. **Reading a whole large file** instead of streaming.
9. **Assuming `json.dumps`/`loads` round-trips every type.** Tuples become lists; integer keys become
   strings; sets, datetimes and Decimals raise.
10. **Check-then-open race:** `if path.exists(): open(path)`. Just open it and catch
    `FileNotFoundError` (M2-L10).

| Error | Cause | Fix |
|---|---|---|
| `FileNotFoundError` | Wrong CWD, or a relative path | Use `Path(__file__).parent`; print `Path.cwd()` |
| `UnicodeDecodeError` | Wrong or default encoding | `encoding="utf-8"`; try `errors="replace"` to inspect |
| `TypeError: Object of type set is not JSON serializable` | Unsupported type | Convert first, or pass `default=str` |
| CSV rows split oddly | Missing `newline=""` | Add it |
| `ValueError: invalid literal for int()` | CSV value is not numeric | Validate with Pydantic and report the row |
| `KeyError: 'ANTHROPIC_API_KEY'` | Variable not set | Fail at startup with a clear message |
| `PermissionError` | Wrong permissions or a directory | Check the path and its mode |
| `MemoryError` on a large file | Full read | Stream line by line |

---

## 9. Security, privacy, reliability and cost

- **Security — path traversal.** Never build a path from user input without constraining it. A
  filename of `../../etc/passwd` escapes your directory. Validate:

  ```python
  base = Path("/srv/uploads").resolve()
  target = (base / user_filename).resolve()
  if not target.is_relative_to(base):
      raise ValueError("path escapes the upload directory")
  ```

  This becomes essential in M7-L15 and M9-L13, where a tool exposes file access to a model.
- **Security — never log environment contents.** `print(os.environ)` dumps every secret into your
  logs. It happens in debugging and the log survives.
- **Privacy.** Files are copies. Deleting a record from your database does not delete it from the
  CSV export, the JSONL dataset, or the container image. Track every copy (M10-L06).
- **Reliability.** `"w"` truncates immediately — an interrupted write leaves an empty file. For
  important outputs, write to a temporary file then rename, since rename is atomic on the same
  filesystem.
- **Cost.** Reading a whole file into memory is the most common cause of container OOM kills in
  ingestion pipelines. Streaming is free to implement and prevents it.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Write a function returning the absolute path of a `data/` directory next to your script,
   regardless of the CWD. Prove it by running the script from two directories.
2. Write a dict containing a string, an int, a list, a tuple and `None` to JSON, read it back, and
   print the type of every value. Note which type changed.
3. Read an environment variable `MAX_ITEMS`, defaulting to 10, as an int. Handle the case where it is
   set to `"abc"` with a clear error.

### Exercise 2 — Intermediate (~25 min)

Build the §6 loader yourself:

1. Create a CSV with 10 rows, of which 3 are invalid (out-of-range priority, blank text,
   non-numeric priority).
2. Load with `csv.DictReader` and validate each row with a Pydantic model.
3. Report valid and failed counts, with line numbers matching the spreadsheet.
4. Write the valid rows to JSONL and read them back, confirming the count matches.
5. Add a field containing a comma and a field containing a newline. Confirm the `csv` module handles
   both, then try building the same file by joining strings with commas and observe what breaks.

### Exercise 3 — Challenge (~25 min)

1. Write `load_settings()` returning a frozen dataclass from environment variables, with: a required
   string that raises a clear error if absent; an int with a default; a bool parsed correctly from
   `"true"`, `"1"`, `"yes"`, `"false"`, `"0"`, `""`; and a `Literal`-style choice validated against a
   set of options.
2. Write six tests using `monkeypatch.setenv` (or by setting `os.environ` directly) covering: all
   defaults, all set, missing required, invalid int, each boolean form, invalid choice.
3. Demonstrate the `bool("false")` trap explicitly and show your fix.
4. Write `safe_join(base, user_path)` that raises if the result escapes `base`. Test it with
   `../../etc/passwd`, an absolute path `/etc/passwd`, and a legitimate `reports/q1.csv`.
5. Measure peak memory reading a 50 MB generated file fully versus streaming it. Report both.

---

## 11. Quiz

**Q1.** Why use `Path("data") / "file.csv"` rather than `"data" + "/" + "file.csv"`?

- A. It is faster.
- B. It handles platform separators, duplicate slashes and normalisation correctly, so the same code
  works on Windows and Linux.
- C. Strings cannot be used as paths.
- D. It validates that the file exists.

**Q2.** What is wrong with `open("data.csv")` in a script run by cron?

- A. cron cannot read files.
- B. The path is relative to the process's current working directory, which under cron is not your
  project directory — use `Path(__file__).resolve().parent` for files shipped with your code.
- C. `open` requires an absolute path.
- D. Nothing.

**Q3.** Why must you pass `newline=""` when opening a CSV file?

- A. To remove blank lines.
- B. Because the `csv` module handles line endings itself, and Python's universal newline
  translation on top of that mis-splits rows whose quoted fields contain newlines.
- C. It is optional.
- D. To set the encoding.

**Q4.** `row["priority"]` from `csv.DictReader` where the file contains `3`. What is its type?

- A. `int`  B. `str` — every CSV value is a string  C. `float`  D. Depends on the column

**Q5.** Which does **not** survive a `json.dumps` → `json.loads` round trip unchanged?

- A. `dict`  B. `list`  C. `tuple` — it comes back as a list  D. `str`

**Q6.** `DEBUG=false` in the environment. What does `bool(os.getenv("DEBUG"))` return?

- A. `False`  B. `True` — the string `"false"` is non-empty and therefore truthy
- C. `None`  D. Raises

**Q7.** Why should a missing required environment variable fail at startup?

- A. It is faster.
- B. Otherwise the process starts successfully and fails later on the first request that needs it,
  turning a configuration error into an intermittent runtime error.
- C. Python requires it.
- D. It does not matter.

**Q8.** What does `path.write_text(...)` with mode `"w"` do to an existing file?

- A. Appends.  B. Raises.  C. Truncates it immediately, so an interrupted write leaves it empty.
- D. Creates a backup.

**Q9.** A user supplies the filename `../../etc/passwd`. What is the correct defence?

- A. Reject filenames containing dots.
- B. Resolve the joined path and confirm it is still inside the intended base directory, rejecting it
  otherwise.
- C. Use `os.path.join`, which is safe.
- D. Run as a non-root user, which is sufficient.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why the §6 loader collects failures
instead of raising on the first bad row, and when that would be the wrong choice.

---

## 12. Revision notes

- **`pathlib` everywhere.** `Path(a) / b`. Never concatenate strings.
- **`Path(__file__).resolve().parent`** for files shipped with your code; CWD-relative only for
  user-supplied paths.
- **Always `encoding="utf-8"`.** Always `with`. `"w"` truncates; `"x"` refuses to overwrite.
- **CSV: `newline=""`, and every value is a string.** Never hand-join commas — use the `csv` module.
- **JSON:** tuples → lists, integer keys → strings; sets, datetimes and Decimals raise. **JSONL** for
  datasets, logs and traces.
- **Env vars are always strings.** `bool("false")` is `True`. Convert explicitly and fail loudly at
  startup for required values.
- **Load config once into a frozen dataclass.** No scattered `os.getenv`.
- **Stream large files**; a full read is how containers get OOM-killed.
- **Path traversal:** resolve and check `is_relative_to(base)`.
- **Never log `os.environ`.**
- Collect row failures with line numbers rather than aborting the whole load.

---

## 13. Completion checklist

- [ ] I use `pathlib` and `Path(__file__).parent` by default.
- [ ] I always pass `encoding="utf-8"` and `newline=""`.
- [ ] I built the CSV → validate → JSONL loader with line-numbered failures.
- [ ] I saw which JSON types do not round-trip.
- [ ] I demonstrated the `bool("false")` trap and fixed it.
- [ ] I wrote and tested `safe_join` against traversal attempts.
- [ ] I measured streaming versus full-read memory.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python docs, `pathlib`. <https://docs.python.org/3/library/pathlib.html> `[UNVERIFIED]`
- Python docs, `csv` — including the `newline=""` requirement.
  <https://docs.python.org/3/library/csv.html> `[UNVERIFIED]`
- Python docs, `json`. <https://docs.python.org/3/library/json.html> `[UNVERIFIED]`
- python-dotenv. <https://pypi.org/project/python-dotenv/> `[UNVERIFIED]`
- OWASP, Path Traversal. <https://owasp.org/www-community/attacks/Path_Traversal> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L10 — Exceptions, Tracebacks and Debugging](M2-L10-exceptions-debugging.md)

Every section of this lesson mentioned an exception. Next: how to raise, catch and read them
properly — and how to debug when the traceback is not enough.
