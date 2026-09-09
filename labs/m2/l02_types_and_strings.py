"""M2-L02: every numeric, string and truthiness trap, demonstrated.

    python3 labs/m2/l02_types_and_strings.py

Standard library only.
"""

from __future__ import annotations

import math
from decimal import Decimal

LINE = "-" * 70


def show(expression: str, value: object, note: str = "") -> None:
    """Print an expression, its value, and an optional note."""
    # !r calls repr(), so strings show their quotes and you can see whitespace.
    print(f"  {expression:<30} = {value!r:<26} {note}")


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def numbers() -> None:
    section("1. NUMBERS - division and rounding")
    show("7 / 2", 7 / 2, "/ ALWAYS returns float")
    show("4 / 2", 4 / 2, "even when it divides evenly")
    show("7 // 2", 7 // 2, "// floors")
    show("-7 // 2", -7 // 2, "<-- FLOORS toward -inf, not toward zero")
    show("int(-7 / 2)", int(-7 / 2), "int() truncates toward zero - different!")
    show("7 % 2", 7 % 2)
    show("-7 % 2", -7 % 2, "sign follows the divisor, unlike C/Java")
    show("2 ** 10", 2 ** 10, "** is power; ^ is bitwise XOR")
    show("7 ^ 2", 7 ^ 2, "<-- XOR, not power. A classic slip.")

    print()
    print("  Integers are UNBOUNDED - no overflow:")
    show("2 ** 100", 2 ** 100)
    print("  (JavaScript's Number.MAX_SAFE_INTEGER is about 9.0e15.)")


def floats() -> None:
    section("2. FLOATS - why 0.1 + 0.2 is not 0.3")
    show("0.1 + 0.2", 0.1 + 0.2, "<-- not 0.3")
    show("0.1 + 0.2 == 0.3", 0.1 + 0.2 == 0.3)
    show("math.isclose(0.1+0.2, 0.3)", math.isclose(0.1 + 0.2, 0.3), "the correct test")

    print()
    print("  Why: 0.1 has no exact binary representation.")
    print(f"  0.1 to 20 decimal places = {0.1:.20f}")
    print(f"  0.2 to 20 decimal places = {0.2:.20f}")
    print(f"  0.3 to 20 decimal places = {0.3:.20f}")

    print()
    print("  MONEY: accumulate 0.003 one thousand times")
    total = 0.0
    for _ in range(1000):
        total += 0.003
    show("float accumulation", total, "wrong in the 13th decimal")
    show("float multiplication", 0.003 * 1000, "better, still not exact")

    exact = Decimal("0.003") * 1000
    show('Decimal("0.003") * 1000', exact, "EXACT")
    show('== Decimal("3")', exact == Decimal("3"))

    print()
    print("  And the trap inside the fix:")
    show('Decimal("0.1")', Decimal("0.1"), "from a string: exact")
    show("Decimal(0.1)", Decimal(0.1), "<-- from a float: inherits the error")


def strings() -> None:
    section("3. STRINGS - immutability and slicing")
    name = "bharath"
    show("name", name)
    show("name.upper()", name.upper(), "returns a NEW string")
    show("name (after .upper())", name, "<-- unchanged: strings are immutable")

    s = "abcdefgh"
    print()
    show("s", s)
    show("s[0]", s[0])
    show("s[-1]", s[-1], "negative counts from the end")
    show("s[1:4]", s[1:4], "start inclusive, stop exclusive")
    show("s[:3]", s[:3])
    show("s[3:]", s[3:])
    show("s[::2]", s[::2], "every 2nd character")
    show("s[::-1]", s[::-1], "reversed")
    show("s[10:20]", s[10:20], "<-- slices NEVER raise; indexing does")

    print()
    print("  Building strings: use join, not += in a loop")
    parts = ["alpha", "beta", "gamma"]
    show('", ".join(parts)', ", ".join(parts))


def fstrings() -> None:
    section("4. F-STRINGS - the formatting you will use constantly")
    name = "Bharath"
    score = 0.8734
    count = 1234567

    show('f"{score:.2f}"', f"{score:.2f}", "2 decimal places")
    show('f"{score:.1%}"', f"{score:.1%}", "as a percentage")
    show('f"{count:,}"', f"{count:,}", "thousands separator")
    show('f"{name:>12}|"', f"{name:>12}|", "right-align in 12")
    show('f"{name:<12}|"', f"{name:<12}|", "left-align")
    show('f"{name:^12}|"', f"{name:^12}|", "centre")
    show('f"{score=}"', f"{score=}", "<-- debugging form: name AND value")
    show('f"{count * 2}"', f"{count * 2}", "any expression works")

    print()
    print("  The table pattern used throughout this course:")
    print('    f"{label:<22}{value:>10.3f}"')
    for label, value in (("precision", 0.8734), ("recall", 0.6512), ("f1", 0.7472)):
        print(f"    {label:<22}{value:>10.3f}")


def identity() -> None:
    section("5. == vs is")
    a = [1, 2, 3]
    b = [1, 2, 3]
    c = a

    show("a == b", a == b, "same VALUE")
    show("a is b", a is b, "<-- different OBJECTS")
    show("a is c", a is c, "c is another name for the same list")
    print(f"  id(a)={id(a)}  id(b)={id(b)}  id(c)={id(c)}")

    print()
    print("  Mutating through one name is visible through the other:")
    c.append(4)
    show("a (after c.append(4))", a, "<-- a changed too")

    print()
    print("  None must be tested with 'is':")
    value = None
    show("value is None", value is None, "CORRECT")

    print()
    print("  The small-integer cache - an implementation detail, NEVER rely on it:")
    x1, x2 = 256, 256
    y1, y2 = 257, 257
    show("256 is 256 (literals)", x1 is x2, "cached by CPython")
    show("257 is 257 (literals)", y1 is y2, "<-- also True, but NOT the cache")

    print()
    print("  Why is the second one True? Because both 257 literals sit in the")
    print("  SAME compiled function, and CPython stores one shared constant for")
    print("  them. That is constant interning, not the small-int cache.")
    print("  Build the numbers at runtime instead and the two effects separate:")

    a_small = int("256")          # built at runtime, not a literal constant
    b_small = int("256")
    a_big = int("257")
    b_big = int("257")
    show('int("256") is int("256")', a_small is b_small, "True: small-int cache")
    show('int("257") is int("257")', a_big is b_big, "<-- False: outside the cache")
    show('int("257") == int("257")', a_big == b_big, "but EQUAL, which is what matters")

    print()
    print("  Two separate implementation details produced the same misleading")
    print("  result. That is exactly why 'is' must never be used to compare")
    print("  numbers or strings - only None, True and False.")


def truthiness() -> None:
    section("6. TRUTHINESS - and the bug it causes")
    values = [False, None, 0, 0.0, "", [], {}, set(), (),
              "0", "False", [0], {"a": 1}, -1, 0.1]
    print(f"  {'value':<16}{'bool()':<10}note")
    for v in values:
        note = ""
        if isinstance(v, (list, dict)) and not v:
            note = "<-- TRUTHY in JavaScript!"
        print(f"  {v!r:<16}{bool(v)!s:<10}{note}")

    print()
    print("  THE BUG: 'not value' vs 'value is None'")
    print()
    print(f"  {'input':<12}{'not value':<14}{'value is None':<16}outcome")
    for candidate in (None, 0, "", 0.0, 5, "x"):
        naive = "default" if not candidate else repr(candidate)
        correct = "default" if candidate is None else repr(candidate)
        flag = "  <-- WRONG" if naive != correct else ""
        print(f"  {candidate!r:<12}{str(not candidate):<14}"
              f"{str(candidate is None):<16}{naive} / {correct}{flag}")

    print()
    print("  A discount of 0 percent, an empty search string and a score of")
    print("  0.0 are all VALID values that 'if not value' silently replaces")
    print("  with a default. Use truthiness for collections, 'is None' for")
    print("  optional values.")


def main() -> None:
    print("=" * 70)
    print("PYTHON TYPES, STRINGS AND TRUTHINESS")
    print("=" * 70)
    numbers()
    floats()
    strings()
    fstrings()
    identity()
    truthiness()
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
