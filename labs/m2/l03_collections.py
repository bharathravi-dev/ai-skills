"""M2-L03: the four containers, the performance difference, and the copy bugs.

    python3 labs/m2/l03_collections.py

Standard library only.
"""

from __future__ import annotations

import copy
import time
from collections import Counter, defaultdict

LINE = "-" * 70


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def show(expression: str, value: object, note: str = "") -> None:
    print(f"  {expression:<38} = {value!r:<22} {note}")


def containers() -> None:
    section("1. THE FOUR CONTAINERS")
    show("[1, 2, 3] + [4]", [1, 2, 3] + [4], "concatenation")
    show("[1, 2] * 2", [1, 2] * 2, "repetition")
    show('{"a": 1} | {"a": 2, "b": 3}', {"a": 1} | {"a": 2, "b": 3}, "right wins")
    show("{1,2,3} & {2,3,4}", {1, 2, 3} & {2, 3, 4}, "intersection")
    show("{1,2,3} | {2,3,4}", {1, 2, 3} | {2, 3, 4}, "union")
    show("{1,2,3} - {2,3,4}", {1, 2, 3} - {2, 3, 4}, "difference")
    show("len({1,1,1,2})", len({1, 1, 1, 2}), "sets deduplicate")
    show('("x")', ("x"), "<-- NOT a tuple, just a string")
    show('("x",)', ("x",), "<-- the comma makes it a tuple")
    show("type({})", type({}).__name__, "<-- empty DICT, not set")
    show("type(set())", type(set()).__name__, "empty set")

    print()
    print("  Mutating methods return None:")
    result = [3, 1, 2].sort()
    show("[3,1,2].sort()", result, "<-- sorts IN PLACE, returns None")
    show("sorted([3,1,2])", sorted([3, 1, 2]), "returns a NEW list")

    print()
    print("  Safe dict access:")
    user = {"name": "Bharath", "role": "lead"}
    show('user.get("missing")', user.get("missing"), "no exception")
    show('user.get("missing", "n/a")', user.get("missing", "n/a"), "with a default")
    try:
        user["missing"]
    except KeyError as exc:
        show('user["missing"]', f"KeyError({exc})", "<-- raises, unlike JavaScript")

    print()
    print("  Counter and defaultdict:")
    words = ["a", "b", "a", "c", "a", "b"]
    show("Counter(words)", Counter(words))
    show("Counter(words).most_common(2)", Counter(words).most_common(2))

    groups: defaultdict[str, list[str]] = defaultdict(list)
    for w in ["apple", "avocado", "banana", "blueberry", "cherry"]:
        groups[w[0]].append(w)          # no existence check needed
    show("defaultdict(list) grouping", dict(groups))

    print()
    print("  Order-preserving deduplication:")
    items = [3, 1, 3, 2, 1]
    show("list(set(items))", list(set(items)), "order LOST")
    show("list(dict.fromkeys(items))", list(dict.fromkeys(items)), "order KEPT")


def performance() -> None:
    section("2. LIST vs SET MEMBERSHIP - the difference that matters")
    print("  1000 membership tests for a value NOT present (worst case).")
    print()
    print(f"  {'n':>10}{'list (ms)':>14}{'set (ms)':>12}{'ratio':>12}")

    trials = 1000
    for n in (100, 1_000, 10_000, 100_000):
        data_list = list(range(n))
        data_set = set(data_list)
        missing = -1                      # forces a full scan of the list

        start = time.perf_counter()
        for _ in range(trials):
            missing in data_list
        list_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        for _ in range(trials):
            missing in data_set
        set_ms = (time.perf_counter() - start) * 1000

        ratio = list_ms / set_ms if set_ms else float("inf")
        print(f"  {n:>10}{list_ms:>14.2f}{set_ms:>12.2f}{ratio:>11.0f}x")

    print()
    print("  The set time is FLAT - it does not care how big the collection is.")
    print("  The list time grows linearly. That is O(1) versus O(n).")

    print()
    print("  Why it matters: membership testing INSIDE a loop.")
    n = 5_000
    existing = list(range(n))
    new_items = list(range(n // 2, n + n // 2))

    start = time.perf_counter()
    dupes_slow = [x for x in new_items if x in existing]
    slow_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    existing_set = set(existing)
    dupes_fast = [x for x in new_items if x in existing_set]
    fast_ms = (time.perf_counter() - start) * 1000

    print(f"    finding duplicates among {len(new_items)} items vs {n} existing")
    print(f"    against a list : {slow_ms:8.2f} ms")
    print(f"    against a set  : {fast_ms:8.2f} ms   ({slow_ms / fast_ms:.0f}x faster)")
    print(f"    same result?     {dupes_slow == dupes_fast}")
    print()
    print("  The list version is O(n*m). Building the set once costs O(n),")
    print("  then every test is O(1). This is the M7-L05 deduplication step.")

    # ---------------------------------------------------------------------
    # The honest counter-question: building a set is not free. When does it
    # actually pay for itself?
    # ---------------------------------------------------------------------
    print()
    print("  BUT building a set costs O(n) too. How many lookups justify it?")
    print()
    size = 1000
    data_list = list(range(size))
    print(f"    {size} existing items:")
    print(f"    {'lookups':>9}{'list (us)':>12}{'build+set (us)':>16}{'winner':>10}")
    for k in (1, 2, 3, 5, 10, 50):
        reps = max(200, 20_000 // k)

        start = time.perf_counter()
        for _ in range(reps):
            for i in range(k):
                (-1 - i) in data_list
        list_us = (time.perf_counter() - start) / reps * 1e6

        start = time.perf_counter()
        for _ in range(reps):
            lookup_set = set(data_list)          # rebuilt each time
            for i in range(k):
                (-1 - i) in lookup_set
        set_us = (time.perf_counter() - start) / reps * 1e6

        winner = "list" if list_us < set_us else "set"
        print(f"    {k:>9}{list_us:>12.2f}{set_us:>16.2f}{winner:>10}")

    print()
    print("  The crossover is at TWO lookups. For a single membership test a")
    print("  set is never worth building - constructing it is itself O(n), so")
    print("  you have done the scan anyway plus allocation overhead.")
    print("  Rule: convert to a set when you will test membership MORE THAN")
    print("  ONCE against the same collection. Which, inside a loop, is always.")


def copying() -> None:
    section("3. ALIASING AND COPYING - three real bugs")

    print("  BUG 1: assignment does not copy")
    a = [1, 2, 3]
    b = a
    b.append(4)
    show("a after b.append(4)", a, "<-- b was never a copy")
    print(f"    id(a)={id(a)}  id(b)={id(b)}  same object: {a is b}")

    print()
    print("  Fixed with an explicit copy:")
    a2 = [1, 2, 3]
    b2 = a2.copy()
    b2.append(4)
    show("a2 after b2.append(4)", a2, "unchanged")

    print()
    print("  BUG 2: copy() is SHALLOW")
    rows = [[1, 2], [3, 4]]
    shallow = rows.copy()
    shallow[0].append(99)
    show("rows after shallow[0].append(99)", rows, "<-- inner lists are shared")

    deep_rows = [[1, 2], [3, 4]]
    deep = copy.deepcopy(deep_rows)
    deep[0].append(99)
    show("with copy.deepcopy", deep_rows, "genuinely independent")

    print()
    print("  BUG 3: [[]] * 3 makes three references to ONE list")
    grid = [[]] * 3
    grid[0].append("x")
    show('[[]] * 3 then grid[0].append("x")', grid, "<-- all three changed")

    grid2 = [[] for _ in range(3)]
    grid2[0].append("x")
    show("[[] for _ in range(3)]", grid2, "correct")


def ranking() -> None:
    section("4. SORTING WITH A TUPLE KEY - and why the tie-break matters")
    scores = {"doc-c": 0.9, "doc-a": 0.9, "doc-b": 0.5, "doc-d": 0.9}

    no_tiebreak = sorted(scores.items(), key=lambda kv: -kv[1])
    with_tiebreak = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    print("  Four documents, three tied on 0.9.")
    print(f"    sorted by score only : {[k for k, _ in no_tiebreak]}")
    print(f"    score then doc id    : {[k for k, _ in with_tiebreak]}")
    print()
    print("  Python's sort is stable, so the first version preserves whatever")
    print("  order the dict happened to have. Change the insertion order, or")
    print("  rebuild the dict from a set, and the tied results reshuffle -")
    print("  while every score stays identical.")
    print()
    print("  That is enough to make an evaluation run non-reproducible")
    print("  (M3-L14). ALWAYS give a sort a deterministic tie-break.")


def main() -> None:
    print("=" * 70)
    print("PYTHON COLLECTIONS")
    print("=" * 70)
    containers()
    performance()
    copying()
    ranking()
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
