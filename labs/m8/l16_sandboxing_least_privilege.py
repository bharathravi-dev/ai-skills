"""M8-L16 lab -- M5-L08's blast-radius principle and M8-L11's read-only vs
state-changing distinction both point at the same underlying question this
lesson makes explicit: what is a tool actually CAPABLE of doing, structurally,
regardless of what it was designed for? A tool granted broad access "just in
case" carries the blast radius of everything it COULD do, not just what it's
intended to do. This lesson demonstrates least privilege (a narrow-scope
tool structurally cannot leak fields it was never given access to) and
sandboxing (a restricted execution environment structurally cannot reach
outside its intended scope, even when asked to).

Deterministic. No API key, no network, no third-party dependencies. Section
2's "escape" demonstration only calls harmless, read-only functions
(os.getcwd()) to illustrate the concept safely -- it does not execute,
modify, or read anything sensitive.
Run:  python labs/m8/l16_sandboxing_least_privilege.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. LEAST PRIVILEGE: A NARROW-SCOPE TOOL CANNOT LEAK WHAT IT NEVER HAS")

CUSTOMER_RECORD = {
    "name": "Dana Kim",
    "order_history": ["O-1001", "O-1002"],
    "ssn": "123-45-6789",
    "payment_method": "Visa ending 4242",
}


def get_customer_info_broad(field: str) -> str:
    """[REAL, deliberately over-privileged] Has access to the ENTIRE
    customer record -- including fields no ordinary support task ever
    needs -- because it was built to be 'flexible.'"""
    return str(CUSTOMER_RECORD.get(field, f"no such field: {field!r}"))


def get_customer_info_narrow(field: str) -> str:
    """[REAL, least privilege] Only knows about the two fields an ordinary
    support task actually needs -- ssn and payment_method are not merely
    hidden, they are absent from this function's own data entirely,
    exactly M5-L08's absent-parameter defense, applied to READ scope."""
    allowed = {"name": CUSTOMER_RECORD["name"], "order_history": CUSTOMER_RECORD["order_history"]}
    return str(allowed.get(field, f"no such field: {field!r}"))


print("  A request that only needs the customer's name behaves identically")
print("  on both versions:")
print(f"    broad:  get_customer_info_broad('name') -> {get_customer_info_broad('name')!r}")
print(f"    narrow: get_customer_info_narrow('name') -> {get_customer_info_narrow('name')!r}")

print("\n  A request -- crafted, mistaken, or from a manipulated agent step --")
print("  asking for a field no legitimate support task ever needs:")
print(f"    broad:  get_customer_info_broad('ssn') -> {get_customer_info_broad('ssn')!r}")
print(f"    narrow: get_customer_info_narrow('ssn') -> {get_customer_info_narrow('ssn')!r}")

print("\n  The broad tool genuinely returns the SSN -- it has that data and no")
print("  scope restriction stops it. The narrow tool cannot leak it, not")
print("  because of a value check that happened to catch this specific")
print("  field name, but because the SSN was never part of its own data at")
print("  all. Removing a capability is a stronger defense than checking")
print("  whether a capability was misused.")


# ============================================================ 2
rule("2. SANDBOXING: A RESTRICTED EXECUTION ENVIRONMENT CANNOT REACH OUTSIDE ITSELF")

import os


def calculate_unsafe(expression: str):
    """[REAL, deliberately dangerous] Full Python eval() with the complete
    standard builtins available -- genuinely capable of far more than
    arithmetic."""
    return eval(expression)


def calculate_sandboxed(expression: str):
    """[REAL] Restricts eval()'s builtins to an empty dict and its
    namespace to a small, explicit allow-list of math functions -- nothing
    else is reachable from inside this expression, structurally, not by
    convention."""
    safe_names = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow, "sum": sum}
    try:
        return eval(expression, {"__builtins__": {}}, safe_names)
    except NameError as exc:
        return f"BLOCKED: {exc}"


print("  A genuine arithmetic request behaves identically on both versions:")
print(f"    unsafe:     calculate_unsafe('2 + 2 * 3') -> {calculate_unsafe('2 + 2 * 3')!r}")
print(f"    sandboxed:  calculate_sandboxed('2 + 2 * 3') -> {calculate_sandboxed('2 + 2 * 3')!r}")

escape_attempt = "__import__('os').getcwd()"
print(f"\n  An expression reaching for something no calculator needs:")
print(f"    {escape_attempt!r}")
print(f"    unsafe:     calculate_unsafe(...) -> {calculate_unsafe(escape_attempt)!r}")
print(f"    sandboxed:  calculate_sandboxed(...) -> {calculate_sandboxed(escape_attempt)!r}")

print("\n  The unsafe version genuinely executed a real OS call -- reading the")
print("  current directory, deliberately chosen here because it is harmless")
print("  to actually run, standing in for what could just as easily have")
print("  been a file read or a system command. The sandboxed version could")
print("  not even NAME __import__, because its builtins were never made")
print("  available in the first place -- the same removal-over-restriction")
print("  principle as section 1, applied to code execution instead of data.")


# ============================================================ 3
rule("3. A FRAMEWORK: DOES THIS TOOL'S ACTUAL SCOPE MATCH WHAT IT NEEDS")


def assess_privilege(capability_needed: set[str], capability_granted: set[str]) -> str:
    """[REAL] The excess is exactly what a manipulated or buggy call could
    reach that a legitimate one never would -- a real, checkable set
    difference, not a subjective judgment."""
    excess = capability_granted - capability_needed
    if not excess:
        return "LEAST PRIVILEGE: granted scope matches what is actually needed"
    return f"OVER-PRIVILEGED: granted access to {sorted(excess)} beyond what any legitimate call needs"


print("  Applying a real set-difference check to both this lab's tools:\n")
print(f"    get_customer_info_narrow: "
      f"{assess_privilege({'name', 'order_history'}, {'name', 'order_history'})}")
print(f"    get_customer_info_broad:  "
      f"{assess_privilege({'name', 'order_history'}, {'name', 'order_history', 'ssn', 'payment_method'})}")
print(f"    calculate_sandboxed:      "
      f"{assess_privilege({'arithmetic'}, {'arithmetic'})}")
print(f"    calculate_unsafe:         "
      f"{assess_privilege({'arithmetic'}, {'arithmetic', 'filesystem', 'os', 'network', 'imports'})}")

print("\n  This connects directly to M8-L11's own classification and M5-L08's")
print("  blast-radius principle: a state-changing, over-privileged tool is")
print("  the highest-risk combination this course has built toward -- not")
print("  because it is more LIKELY to be misused than a narrowly-scoped")
print("  one, but because the CONSEQUENCE of any misuse, accidental or")
print("  adversarial, is structurally larger.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: both customer-info functions genuinely differ in what data")
print("  they can return, verified directly above; both calculate functions")
print("  genuinely differ in what they can execute, including a real,")
print("  harmless OS call the sandboxed version genuinely cannot reach.")
print("\n  ILLUSTRATIVE: CUSTOMER_RECORD is a small, hand-built example, not a")
print("  claim about real customer data models. The sandboxed eval() shown")
print("  here blocks ONE real class of escape (builtin access) -- a")
print("  production-grade sandbox for arbitrary code execution needs much")
print("  more (resource limits, real process isolation), which this lab")
print("  does not attempt to build.")
print("\n  NOT SHOWN: how a real system enforces least privilege at the")
print("  infrastructure level (database row-level security, IAM roles, OS")
print("  containers) rather than inside a single Python function; and a")
print("  complete, hardened code-execution sandbox, which is a substantial")
print("  engineering effort beyond this lesson's own scope.")

print("\nDone.")
