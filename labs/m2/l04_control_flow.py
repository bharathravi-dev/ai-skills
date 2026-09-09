"""M2-L04: comprehensions, generators, and the four classic loop bugs.

    python3 labs/m2/l04_control_flow.py

Standard library only.
"""

from __future__ import annotations

import tracemalloc

LINE = "-" * 70

RESULTS = [
    {"id": "doc-001", "score": 0.91, "source": "policy", "text": "Refunds within 5 days."},
    {"id": "doc-002", "score": 0.44, "source": "blog",   "text": "Our shipping story."},
    {"id": "doc-003", "score": 0.78, "source": "policy", "text": "Returns need a receipt."},
    {"id": "doc-004", "score": 0.12, "source": "policy", "text": "Office opening hours."},
]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def pipeline() -> None:
    section("1. THE SEARCH-RESULT PIPELINE")

    relevant = [r for r in RESULTS if r["score"] >= 0.5]
    print(f"  filtered (score >= 0.5)   : {[r['id'] for r in relevant]}")

    policy_only = [r for r in RESULTS if r["score"] >= 0.5 and r["source"] == "policy"]
    print(f"  + source == 'policy'      : {[r['id'] for r in policy_only]}")

    ranked = sorted(relevant, key=lambda r: (-r["score"], r["id"]))
    print(f"  ranked (score desc, id)   : {[r['id'] for r in ranked]}")

    print()
    print("  formatted with enumerate(start=1):")
    lines = [
        f"    {i}. [{r['score']:.2f}] {r['id']}: {r['text'][:40]}"
        for i, r in enumerate(ranked, start=1)
    ]
    for line in lines:
        print(line)

    print()
    print("  aggregates WITHOUT building intermediate lists:")
    print(f"    sum of scores  = {sum(r['score'] for r in ranked):.2f}")
    print(f"    any below 0.6  = {any(r['score'] < 0.6 for r in ranked)}")
    print(f"    all are policy = {all(r['source'] == 'policy' for r in ranked)}")

    print()
    print("  The token-budget loop - which CANNOT be a comprehension:")
    budget, used, selected = 60, 0, []
    for r in ranked:
        cost = len(r["text"])
        if used + cost > budget:
            print(f"    stopping at {r['id']}: {used} + {cost} would exceed {budget}")
            break
        selected.append(r["id"])
        used += cost
        print(f"    took {r['id']:<9} cost={cost:<3} used={used}")
    print(f"    selected: {selected}")
    print("    Each decision depends on state accumulated so far, and it must")
    print("    stop early. Comprehensions do neither.")


def bug_mutation() -> None:
    section("2. BUG 1 - mutating a list while iterating it")
    items = [2, 4, 6, 8]
    print(f"  start: {items}   removing EVERY even number with .remove()")
    print("  correct answer: []")
    print()
    for x in items:
        if x % 2 == 0:
            items.remove(x)
            print(f"    sees {x}, removes it -> list is now {items}")
        else:
            print(f"    sees {x}, keeps it")
    print(f"  result: {items}   <-- 4 and 8 SURVIVED. Every one should have gone.")
    print()
    print("  Why: the iterator walks POSITIONS 0, 1, 2, ... through a list whose")
    print("  length is shrinking underneath it.")
    print("    position 0 -> 2, removed. List becomes [4, 6, 8]; everything")
    print("                  shifted left, so 4 is now at position 0 - already")
    print("                  passed. It is skipped.")
    print("    position 1 -> 6, removed. List becomes [4, 8].")
    print("    position 2 -> past the end (len is 2). Loop stops.")
    print("  Half the list was never examined.")
    print()
    fixed = [x for x in [2, 4, 6, 8] if x % 2 != 0]
    print(f"  fix - build a NEW list instead of mutating: {fixed}")
    print()
    print("  NOTE how easily this hides. With [1,2,3,4] the same bug returns")
    print("  [1,3] - which is the RIGHT answer, purely because the skipped")
    print("  element happened not to need removing. The bug is present and")
    print("  invisible. That is why the rule is absolute: never mutate a list")
    print("  you are iterating.")


def bug_late_binding() -> None:
    section("3. BUG 2 - late binding in closures")
    funcs = [lambda: i for i in range(3)]
    print(f"  [lambda: i for i in range(3)] -> {[f() for f in funcs]}   <-- not [0,1,2]")
    print()
    print("  Each lambda captured the VARIABLE i, not its value. When they are")
    print("  finally called, the loop has finished and i is 2.")
    print()
    fixed1 = [lambda i=i: i for i in range(3)]
    print(f"  fix A - default argument binds NOW : {[f() for f in fixed1]}")

    def make(value: int):
        return lambda: value
    fixed2 = [make(i) for i in range(3)]
    print(f"  fix B - a factory gives each its own scope: {[f() for f in fixed2]}")


def bug_zip() -> None:
    section("4. BUG 3 - zip() truncating silently")
    features = [[1.0], [2.0], [3.0]]      # 3 examples
    labels = [1, 0]                       # only 2 labels - a data bug

    pairs = list(zip(features, labels))
    print(f"  features: {len(features)} rows, labels: {len(labels)} rows")
    print(f"  zip() gave {len(pairs)} pairs - the third example vanished SILENTLY")
    print("  No error. No warning. Your training set just lost a row.")
    print()
    try:
        list(zip(features, labels, strict=True))
    except ValueError as exc:
        print(f"  with strict=True -> ValueError: {exc}")
    print()
    print("  This is the M1-L04 X/y alignment bug in Python form. Make")
    print("  strict=True your default whenever the lengths ought to match.")


def bug_memory() -> None:
    section("5. BUG 4 - building a list you do not need")
    n = 2_000_000

    tracemalloc.start()
    total_list = sum([x * x for x in range(n)])
    _, peak_list = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    total_gen = sum(x * x for x in range(n))
    _, peak_gen = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  sum over {n:,} squares")
    print(f"    list comprehension   peak memory: {peak_list:>12,} bytes "
          f"({peak_list / 1_000_000:.1f} MB)")
    print(f"    generator expression peak memory: {peak_gen:>12,} bytes "
          f"({peak_gen / 1000:.1f} KB)")
    print(f"    ratio: {peak_list / max(peak_gen, 1):,.0f}x less memory")
    print(f"    same answer? {total_list == total_gen}")
    print()
    print("  The list version materialises 2 million integers to add them up")
    print("  and throw them away. The generator holds one at a time.")
    print("  In Module 7 the items are document chunks, not integers.")


def generators_exhaust() -> None:
    section("6. GENERATORS ARE CONSUMED ONCE")
    gen = (x for x in range(3))
    print(f"  first  list(gen) -> {list(gen)}")
    print(f"  second list(gen) -> {list(gen)}   <-- empty, and NO error")
    print()
    print("  This is why a function returning a generator can work the first")
    print("  time a caller uses it and silently return nothing the second.")


def main() -> None:
    print("=" * 70)
    print("CONTROL FLOW, COMPREHENSIONS AND GENERATORS")
    print("=" * 70)
    pipeline()
    bug_mutation()
    bug_late_binding()
    bug_zip()
    bug_memory()
    generators_exhaust()
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
