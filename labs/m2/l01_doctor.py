"""M2-L01: environment doctor. Diagnoses your Python setup in plain language.

    python3 labs/m2/l01_doctor.py

Standard library only, and deliberately so: this script must run even when
your environment is broken, which is exactly when you need it.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys

MIN_VERSION = (3, 10)

# (distribution name as you pip install it, module name as you import it)
COURSE_DEPENDENCIES: list[tuple[str, str]] = [
    ("numpy", "numpy"),
    ("scikit-learn", "sklearn"),
    ("pydantic", "pydantic"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("httpx", "httpx"),
    ("pytest", "pytest"),
    ("python-dotenv", "dotenv"),
    ("tiktoken", "tiktoken"),
    ("rank-bm25", "rank_bm25"),
]

ACTIVATE_HINT = (
    "       python3 -m venv .venv\n"
    "       source .venv/bin/activate        # Windows: .venv\\Scripts\\activate\n"
    "       python -m pip install -r requirements.txt"
)


def check_python(problems: list[str]) -> None:
    print("PYTHON")
    version = ".".join(str(p) for p in sys.version_info[:3])
    print(f"  version            : {version}")
    print(f"  executable         : {sys.executable}")

    if sys.version_info[:2] >= MIN_VERSION:
        print(f"  OK: Python {version} meets the course minimum of "
              f"{MIN_VERSION[0]}.{MIN_VERSION[1]}.")
    else:
        problems.append("python-version")
        print(f"  PROBLEM: Python {version} is older than the required "
              f"{MIN_VERSION[0]}.{MIN_VERSION[1]}.")
        print("     This course uses syntax such as list[str] and 'X | None'")
        print("     that older versions cannot parse. Install a newer Python.")
    print()


def check_venv(problems: list[str]) -> None:
    print("VIRTUAL ENVIRONMENT")
    # THE canonical check: inside a venv these two differ.
    in_venv = sys.prefix != sys.base_prefix
    print(f"  sys.prefix         : {sys.prefix}")
    print(f"  sys.base_prefix    : {sys.base_prefix}")
    print(f"  VIRTUAL_ENV env var: {os.environ.get('VIRTUAL_ENV', '(not set)')}")

    if in_venv:
        print("  OK: You are inside a virtual environment.")
        if not os.environ.get("VIRTUAL_ENV"):
            print("  NOTE: VIRTUAL_ENV is not set, so you are using the venv's")
            print("     interpreter directly without activating. That works fine")
            print("     (it is what CI and Docker usually do), but 'pip' on your")
            print("     PATH may belong to a different Python. Use 'python -m pip'.")
    else:
        problems.append("no-venv")
        print("  PROBLEM: You are NOT in a virtual environment.")
        print("     sys.prefix equals sys.base_prefix, which means this interpreter is")
        print("     the system Python. Installing packages here can break system tools")
        print("     and makes your project unreproducible.")
        print("     Fix:")
        print(ACTIVATE_HINT)
    print()


def check_path(problems: list[str]) -> None:
    print("WHAT THE SHELL RESOLVES")
    found: dict[str, str | None] = {}
    for command in ("python", "python3", "pip"):
        location = shutil.which(command)
        found[command] = location
        print(f"  {command:<19}: {location or '(not found)'}")

    if found["python"] is None:
        print("  NOTE: 'python' is not on your PATH, only 'python3'.")
        print("     Inside an activated venv, 'python' will exist. Until then, use")
        print("     'python3'. Prefer 'python -m pip' over bare 'pip' always.")
    elif found["pip"] and found["python"]:
        # If pip and python live in different directories, that is a classic trap.
        if os.path.dirname(found["pip"]) != os.path.dirname(found["python"]):
            problems.append("pip-mismatch")
            print("  PROBLEM: 'pip' and 'python' come from DIFFERENT directories.")
            print("     Packages you install with 'pip' may be invisible to 'python'.")
            print("     Fix: always use 'python -m pip install ...' instead.")
    print()


def check_dependencies(problems: list[str]) -> None:
    print("COURSE DEPENDENCIES")
    present = 0
    for dist_name, module_name in COURSE_DEPENDENCIES:
        # find_spec checks importability WITHOUT importing - faster and avoids
        # side effects from a package's __init__.
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, ValueError):
            spec = None

        label = dist_name if dist_name == module_name else f"{dist_name} ({module_name})"
        if spec is not None:
            present += 1
            print(f"  {label:<30} ok")
        else:
            print(f"  {label:<30} MISSING")

    print(f"  {present} of {len(COURSE_DEPENDENCIES)} present.")
    if present < len(COURSE_DEPENDENCIES):
        problems.append("missing-deps")
        print("  PROBLEM: dependencies are missing.")
        print("     Activate your venv, then:")
        print("       python -m pip install -r requirements.txt")
    else:
        print("  OK: all course dependencies are importable.")
    print()


def check_shadowing(problems: list[str]) -> None:
    """Detect local files that shadow standard library modules.

    A file called json.py in your working directory silently replaces the
    standard library's json module. The resulting errors are bewildering.
    """
    risky = {
        "json", "types", "string", "random", "logging", "email", "csv",
        "time", "select", "code", "token", "copy", "queue", "typing",
        "test", "abc", "io", "operator", "secrets", "statistics",
    }
    cwd = os.getcwd()
    try:
        local_modules = {
            f[:-3] for f in os.listdir(cwd)
            if f.endswith(".py") and not f.startswith("_")
        }
    except OSError:
        return

    clashes = sorted(local_modules & risky)
    if clashes:
        problems.append("shadowing")
        print("MODULE SHADOWING")
        for name in clashes:
            print(f"  PROBLEM: ./{name}.py shadows the standard library module "
                  f"'{name}'.")
        print("     Any 'import' of these will load YOUR file instead of the")
        print("     standard library, producing errors that make no sense.")
        print("     Fix: rename your file.")
        print()


def main() -> None:
    print("=" * 70)
    print("ENVIRONMENT DOCTOR")
    print("=" * 70)
    print()

    problems: list[str] = []
    check_python(problems)
    check_venv(problems)
    check_path(problems)
    check_dependencies(problems)
    check_shadowing(problems)

    print("=" * 70)
    if problems:
        print(f"SUMMARY: {len(problems)} problem(s) found. Work through them top to bottom.")
    else:
        print("SUMMARY: no problems found. Your environment is ready.")
    print("=" * 70)


if __name__ == "__main__":
    main()
