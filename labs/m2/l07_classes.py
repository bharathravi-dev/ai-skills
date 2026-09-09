"""M2-L07: what dataclasses generate, what they do not, and composition.

    python3 labs/m2/l07_classes.py

Standard library only.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Protocol

LINE = "-" * 70


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Chunk:
    """A retrieved chunk. Frozen, so it is immutable AND hashable."""

    chunk_id: str
    text: str
    doc_id: str
    score: float = 0.0

    @property
    def preview(self) -> str:
        return self.text[:40] + ("..." if len(self.text) > 40 else "")


@dataclass
class Basket:
    """Mutable defaults REQUIRE default_factory."""

    owner: str
    items: list[str] = field(default_factory=list)


def what_dataclass_generates() -> None:
    section("1. WHAT @dataclass ACTUALLY GENERATES")
    c = Chunk("c1", "Refunds are processed within 5 business days.", "d1", 0.91)

    print(f"  __repr__ : {c!r}")
    print(f"  __eq__   : {c == Chunk('c1', 'Refunds are processed within 5 business days.', 'd1', 0.91)}")
    print(f"  property : {c.preview!r}")
    print()
    print("  Fields discovered by introspection:")
    for f in dataclasses.fields(Chunk):
        default = "(required)" if f.default is dataclasses.MISSING else repr(f.default)
        print(f"    {f.name:<12}{str(f.type):<10}default={default}")
    print()
    print("  Generated methods present on the class:")
    for name in ("__init__", "__repr__", "__eq__", "__hash__"):
        print(f"    {name:<12}{hasattr(Chunk, name)}")


def mutable_defaults() -> None:
    section("2. DATACLASSES BLOCK THE MUTABLE DEFAULT BUG")
    print("  Trying to define:  items: list[str] = []")
    try:
        @dataclass
        class Broken:
            items: list[str] = []      # type: ignore[assignment]
    except ValueError as exc:
        print(f"    ValueError: {exc}")
    print()
    print("  This is one of the very few places Python protects you from the")
    print("  M2-L05 bug, and for exactly the same reason: one list would be")
    print("  shared by every instance.")
    print()
    a, b = Basket("alice"), Basket("bob")
    a.items.append("book")
    print(f"  With default_factory:  a.items={a.items}  b.items={b.items}")


def not_enforced() -> None:
    section("3. WHAT @dataclass DOES *NOT* DO - no runtime validation")
    bad = Chunk(chunk_id="c2", text="x", doc_id="d1", score="high")  # type: ignore[arg-type]
    print(f"  Chunk(..., score='high') constructed with NO error: {bad!r}")
    print(f"  type(bad.score) = {type(bad.score).__name__}")
    print()
    print("  The annotation said float. Nothing checked it. Now watch where")
    print("  it actually fails - a long way from the cause:")
    try:
        sorted([bad, Chunk("c3", "y", "d1", 0.5)], key=lambda c: -c.score)
    except TypeError as exc:
        print(f"    TypeError: {exc}")
    print()
    print("  Read that message. It says 'bad operand type for unary -'.")
    print("  It does not mention Chunk. It does not mention chunk_id 'c2'.")
    print("  It does not mention the field name 'score', or the annotation")
    print("  that was ignored, or where the bad value came from. In a real")
    print("  pipeline that value may have been built in another module")
    print("  minutes earlier, and you now debug a sort function that is")
    print("  entirely innocent. THIS is the gap Pydantic closes (M2-L08).")


def frozen_and_sets() -> None:
    section("4. frozen=True MAKES DEDUPLICATION POSSIBLE")
    chunks = [
        Chunk("c1", "Refund policy", "d1", 0.9),
        Chunk("c2", "Shipping policy", "d2", 0.7),
        Chunk("c1", "Refund policy", "d1", 0.9),      # exact duplicate
    ]
    unique = set(chunks)
    print(f"  {len(chunks)} chunks in, {len(unique)} unique out (set-based dedup)")
    print(f"  ranked: {[c.chunk_id for c in sorted(unique, key=lambda c: (-c.score, c.chunk_id))]}")
    print()
    try:
        chunks[0].score = 0.1            # type: ignore[misc]
    except dataclasses.FrozenInstanceError as exc:
        print(f"  Mutation blocked: FrozenInstanceError: {exc}")
    print()
    replaced = dataclasses.replace(chunks[0], score=0.1)
    print(f"  To 'change' one, build a new one: {replaced!r}")
    print()
    print("  Without frozen=True, Chunk would be unhashable and set() would")
    print("  raise TypeError. Immutability is what buys deduplication.")


class Leaky:
    """WRONG: a mutable CLASS attribute is shared by every instance."""

    cache: dict[str, int] = {}

    def add(self, key: str, value: int) -> None:
        self.cache[key] = value


class Correct:
    """RIGHT: per-instance state created in __init__."""

    def __init__(self) -> None:
        self.cache: dict[str, int] = {}

    def add(self, key: str, value: int) -> None:
        self.cache[key] = value


def class_attribute_leak() -> None:
    section("5. THE SHARED CLASS-ATTRIBUTE LEAK")
    user_a, user_b = Leaky(), Leaky()
    user_a.add("account_number", 12345)
    print("  class Leaky:  cache = {}        # class attribute")
    print(f"    user_a.add('account_number', 12345)")
    print(f"    user_b.cache -> {user_b.cache}   <-- user B can read user A's data")
    print(f"    same object? {user_a.cache is user_b.cache}")
    print()
    ok_a, ok_b = Correct(), Correct()
    ok_a.add("account_number", 12345)
    print("  class Correct:  def __init__(self): self.cache = {}")
    print(f"    ok_b.cache -> {ok_b.cache}   <-- isolated")
    print()
    print("  In a long-running FastAPI server this is not a style issue.")
    print("  It is cross-tenant data exposure (M7-L15).")


# ---------------------------------------------------------------------------
class Retriever(Protocol):
    """Structural type: anything with this method qualifies. No inheritance."""

    def search(self, query: str, k: int) -> list[str]: ...


class KeywordRetriever:
    """Note: inherits from NOTHING, yet satisfies Retriever."""

    def __init__(self, index: dict[str, str]) -> None:
        self.index = index

    def search(self, query: str, k: int) -> list[str]:
        hits = [doc_id for doc_id, text in self.index.items()
                if query.lower() in text.lower()]
        return sorted(hits)[:k]


class StubRetriever:
    """A test double. Also inherits from nothing."""

    def __init__(self, fixed: list[str]) -> None:
        self.fixed = fixed
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, k: int) -> list[str]:
        self.calls.append((query, k))
        return self.fixed[:k]


class SearchService:
    """Composition: it HAS a retriever rather than IS one."""

    def __init__(self, retriever: Retriever, *, k: int = 3) -> None:
        self.retriever = retriever
        self.k = k

    def search(self, query: str) -> list[str]:
        results = self.retriever.search(query, self.k)
        return sorted(set(results))


def composition() -> None:
    section("6. COMPOSITION AND Protocol")
    index = {
        "d1": "Refunds are processed within 5 business days",
        "d2": "Shipping takes 3-5 working days",
        "d3": "Refund requests need an order number",
    }

    real = SearchService(KeywordRetriever(index))
    print(f"  with KeywordRetriever: search('refund') -> {real.search('refund')}")

    stub = StubRetriever(["stub-1", "stub-2", "stub-1"])
    fake = SearchService(stub)
    print(f"  with StubRetriever   : search('anything') -> {fake.search('anything')}")
    print(f"  stub recorded calls  : {stub.calls}")
    print()
    print("  SearchService was tested with no index, no I/O, no mocking")
    print("  library and no patching - just a different object passed in.")
    print("  Neither retriever inherits from anything; the Protocol describes")
    print("  the required shape and the type-checker verifies it.")


def main() -> None:
    print("=" * 70)
    print("CLASSES, DATACLASSES AND COMPOSITION")
    print("=" * 70)
    what_dataclass_generates()
    mutable_defaults()
    not_enforced()
    frozen_and_sets()
    class_attribute_leak()
    composition()
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
