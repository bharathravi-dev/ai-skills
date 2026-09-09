"""M2-L05: the mutable default bug, passing semantics, and good signatures.

    python3 labs/m2/l05_functions.py

Standard library only.
"""

from __future__ import annotations

LINE = "-" * 70


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
# The bug, preserved deliberately.
# ---------------------------------------------------------------------------
def add_tag_buggy(tag: str, tags: list[str] = []) -> list[str]:   # noqa: B006
    """DO NOT COPY THIS. The default list is created once and shared."""
    tags.append(tag)
    return tags


def add_tag_fixed(tag: str, tags: list[str] | None = None) -> list[str]:
    """The correct form: None sentinel, fresh list per call."""
    if tags is None:
        tags = []
    tags.append(tag)
    return tags


def mutable_default() -> None:
    section("1. THE MUTABLE DEFAULT ARGUMENT BUG")
    print("  def add_tag(tag, tags=[]):  ...  tags.append(tag)")
    print()
    for call in ("a", "b", "c"):
        result = add_tag_buggy(call)
        print(f'    add_tag_buggy("{call}") -> {result}   id={id(result)}')
    print()
    print("  The SAME id every time: every call received the SAME list object,")
    print("  created once when the 'def' line executed. It accumulates for the")
    print("  lifetime of the process.")
    print()
    print("  def add_tag(tag, tags=None): if tags is None: tags = []")
    print()
    # Keep every result alive. Otherwise CPython frees each list as soon as
    # it goes out of scope and REUSES the same memory address, which makes
    # the ids look identical and muddies the demonstration.
    kept: list[list[str]] = []
    for call in ("a", "b", "c"):
        result = add_tag_fixed(call)
        kept.append(result)
        print(f'    add_tag_fixed("{call}")  -> {result}   id={id(result)}')
    print()
    print(f"  Three distinct ids: {len({id(k) for k in kept})} unique objects.")
    print("  A fresh list per call, and none of them accumulate.")
    print()
    print("  And the fix respects a deliberately-passed empty list:")
    caller_list: list[str] = []
    returned = add_tag_fixed("x", caller_list)
    print(f"    caller passed [] -> got {returned}, same object: {returned is caller_list}")
    print("    (Using 'if not tags:' instead of 'is None' would have thrown the")
    print("     caller's list away and returned a different one. M2-L02.)")


# ---------------------------------------------------------------------------
# Passing semantics
# ---------------------------------------------------------------------------
def rebind(items: list[int]) -> None:
    items = [9, 9]        # rebinds the LOCAL name only


def mutate(items: list[int]) -> None:
    items.append(9)       # mutates the SHARED object


def normalise_dangerous(records: list[dict]) -> list[dict]:
    """Mutates the caller's dictionaries. Usually not what you want."""
    for r in records:
        r["text"] = r["text"].strip()
    return records


def normalise_safe(records: list[dict]) -> list[dict]:
    """Returns new dictionaries. The caller's data is untouched."""
    return [{**r, "text": r["text"].strip()} for r in records]


def passing() -> None:
    section("2. REBIND vs MUTATE")
    data = [1, 2]
    rebind(data)
    print(f"  after rebind(data)  : {data}   <-- unchanged")
    data = [1, 2]
    mutate(data)
    print(f"  after mutate(data)  : {data}   <-- changed")
    print()
    print("  Reassigning a parameter NEVER affects the caller.")
    print("  Mutating the object ALWAYS does.")
    print()

    original = [{"text": "  hello  "}, {"text": " world "}]
    snapshot = [dict(r) for r in original]

    normalise_dangerous(original)
    print(f"  normalise_dangerous: caller's data is now {original}")
    print("    The function 'just normalised' and silently rewrote the input.")

    original2 = [dict(r) for r in snapshot]
    result = normalise_safe(original2)
    print(f"  normalise_safe     : returned {result}")
    print(f"                       caller's data still {original2}")


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------
counter = 0


def broken_increment() -> None:
    counter = counter + 1        # noqa: F821  - deliberately broken


def scope() -> None:
    section("3. SCOPE - why assignment makes a name local")
    print("  counter = 0                 # module level")
    print("  def broken_increment():")
    print("      counter = counter + 1   # <-- assignment makes counter LOCAL")
    print()
    try:
        broken_increment()
    except UnboundLocalError as exc:
        print(f"  UnboundLocalError: {exc}")
    print()
    print("  Python decided 'counter' is local for the WHOLE function because")
    print("  it is assigned somewhere in the body. So the read on the right")
    print("  happens before any local value exists.")
    print()
    print("  Better than 'global': take it in, return it out.")

    def increment(value: int) -> int:
        return value + 1

    n = 0
    for _ in range(3):
        n = increment(n)
    print(f"    n after three increments: {n}")


# ---------------------------------------------------------------------------
# Keyword-only parameters
# ---------------------------------------------------------------------------
def search(query: str, *, k: int = 5, rerank: bool = False) -> str:
    return f"query={query!r} k={k} rerank={rerank}"


def keyword_only() -> None:
    section("4. KEYWORD-ONLY PARAMETERS - making an API hard to misuse")
    print("  def search(query, *, k=5, rerank=False)")
    print()
    print(f"  search('refunds', k=10, rerank=True)")
    print(f"    -> {search('refunds', k=10, rerank=True)}")
    print()
    try:
        search("refunds", 10, True)          # type: ignore[misc]
    except TypeError as exc:
        print(f"  search('refunds', 10, True)")
        print(f"    -> TypeError: {exc}")
    print()
    print("  That TypeError is the feature. 'search(q, 10, True)' tells a")
    print("  reader nothing, and swapping two positional flags is a silent bug.")


# ---------------------------------------------------------------------------
# The chunk_text example
# ---------------------------------------------------------------------------
def chunk_text(text: str, *, size: int = 500, overlap: int = 50,
               keep_empty: bool = False) -> list[str]:
    """Split text into overlapping chunks of roughly `size` characters.

    Args:
        text: Document text. Not modified.
        size: Target chunk length in characters. Must be > 0.
        overlap: Characters shared between consecutive chunks. Must be < size.
        keep_empty: If False, whitespace-only chunks are dropped.

    Returns:
        A list of chunks in document order. Empty input returns [].

    Raises:
        ValueError: If size <= 0, overlap < 0, or overlap >= size.
    """
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be less than size ({size})")

    if not text.strip():
        return []

    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(text), step):
        piece = text[start:start + size]
        if keep_empty or piece.strip():
            chunks.append(piece)
    return chunks


def chunk_no_validation(text: str, size: int, overlap: int) -> list[str]:
    """The same function with the guards removed, to show what they prevent."""
    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(text), step):
        chunks.append(text[start:start + size])
    return chunks


def chunking() -> None:
    section("5. VALIDATION AT THE BOUNDARY")
    text = "abcdefghijklmnopqrstuvwxy"        # 25 characters
    print(f"  text = {text!r} ({len(text)} chars)")
    print()
    result = chunk_text(text, size=10, overlap=3)
    print(f"  chunk_text(size=10, overlap=3) -> {result}")
    starts = list(range(0, len(text), 10 - 3))
    print(f"  chunk start positions: {starts}")
    print()

    print("  Now the failures the validation catches:")
    for size, overlap in ((10, 10), (10, 15), (0, 0)):
        try:
            chunk_text(text, size=size, overlap=overlap)
        except ValueError as exc:
            print(f"    size={size}, overlap={overlap} -> ValueError: {exc}")
    print()

    print("  WITHOUT the validation:")
    try:
        chunk_no_validation(text, 10, 10)
    except ValueError as exc:
        print(f"    overlap == size -> {type(exc).__name__}: {exc}")
        print("      An obscure error from deep inside range(). At least it fails.")
    silent = chunk_no_validation(text, 10, 15)
    print(f"    overlap  > size -> returned {silent}")
    print("      NO ERROR. It returns an empty list. Every document produces")
    print("      zero chunks, your index is empty, retrieval finds nothing,")
    print("      and nothing anywhere reported a problem. THIS is why you")
    print("      validate at the boundary.")
    print()
    print(f"  Docstrings are real objects: chunk_text.__doc__ is "
          f"{len(chunk_text.__doc__ or '')} characters long.")


def main() -> None:
    print("=" * 70)
    print("FUNCTIONS, ARGUMENTS AND SCOPE")
    print("=" * 70)
    mutable_default()
    passing()
    scope()
    keyword_only()
    chunking()
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
