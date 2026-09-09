"""M1-L07: the self-supervised trick, made concrete.

Generates next-token training pairs from raw text with no human labelling,
trains the simplest possible next-word predictor (bigram counts), and uses it
to generate text.

    python3 labs/m1/l07_self_supervision.py

Standard library only.
"""

from __future__ import annotations

import random
from collections import Counter

# A small public-domain-style corpus written for this course. Deliberately
# tiny so you can see the limits of a small model immediately.
CORPUS = """
the support team resolved the billing issue quickly
the support team escalated the login issue to engineering
the customer reported a billing issue on the invoice
the customer reported a login issue on the mobile app
the engineer fixed the login issue in the morning
the engineer closed the billing issue in the afternoon
the manager reviewed the support queue every morning
the manager approved the refund for the billing issue
"""


def tokenize(text: str) -> list[str]:
    """Lowercase and split on whitespace. Real tokenizers are M4-L03."""
    return text.lower().split()


def make_training_pairs(tokens: list[str]) -> list[tuple[str, str]]:
    """THE SELF-SUPERVISED TRICK.

    No human labels anything. For each position we take the previous token as
    the input and the current token as the target. The 'label' was already in
    the data - we simply covered it up.
    """
    return [(tokens[i - 1], tokens[i]) for i in range(1, len(tokens))]


def train_bigram(pairs: list[tuple[str, str]]) -> dict[str, Counter[str]]:
    """'Training' is counting which word follows which."""
    counts: dict[str, Counter[str]] = {}
    for previous, following in pairs:
        counts.setdefault(previous, Counter())[following] += 1
    return counts


def generate_greedy(counts: dict[str, Counter[str]], start: str, length: int) -> list[str]:
    """Always take the single most likely next word (greedy decoding)."""
    out = [start]
    current = start
    for _ in range(length - 1):
        if current not in counts:
            break
        current = counts[current].most_common(1)[0][0]
        out.append(current)
    return out


def generate_sampled(
    counts: dict[str, Counter[str]], start: str, length: int, rng: random.Random
) -> list[str]:
    """Sample proportional to observed frequency - the seed of the sampling
    ideas you will meet properly in M4-L14."""
    out = [start]
    current = start
    for _ in range(length - 1):
        if current not in counts:
            break
        options = counts[current]
        words = list(options.keys())
        freqs = list(options.values())
        current = rng.choices(words, weights=freqs, k=1)[0]
        out.append(current)
    return out


def main() -> None:
    tokens = tokenize(CORPUS)
    pairs = make_training_pairs(tokens)

    print("=" * 70)
    print("SELF-SUPERVISION: the data labels itself")
    print("=" * 70)
    print()
    print(f"Corpus: {len(tokens)} tokens, {len(set(tokens))} unique words.")
    print(f"Human labels provided: 0")
    print(f"Training pairs generated automatically: {len(pairs)}")
    print()
    print("The general rule: n tokens -> n-1 next-token pairs.")
    print(f"Check: {len(tokens)} - 1 = {len(tokens) - 1} = {len(pairs)}")
    print()

    print("First 8 training pairs (nobody wrote these targets):")
    for inp, target in pairs[:8]:
        print(f"    input: {inp!r:<14} -> target: {target!r}")
    print()

    counts = train_bigram(pairs)
    print(f"Trained. Learned follow-up distributions for {len(counts)} words.")
    print()
    print("What the model learned about the word 'the':")
    for word, n in counts["the"].most_common(6):
        share = n / sum(counts["the"].values())
        print(f"    'the' -> {word:<12} {n:>2} times  ({share:.0%})")
    print()
    print("What the model learned about the word 'billing':")
    for word, n in counts["billing"].most_common():
        print(f"    'billing' -> {word:<12} {n:>2} times")
    print()

    print("-" * 70)
    print("GENERATING TEXT (greedy: always the most likely next word)")
    print("-" * 70)
    for start in ("the", "customer", "engineer"):
        text = " ".join(generate_greedy(counts, start, 12))
        print(f"    start={start!r:<12} -> {text}")
    print()
    print("Notice the loop. Greedy decoding gets stuck repeating the single")
    print("highest-probability path forever. This is a real problem with real")
    print("models too, and it is why sampling exists (M4-L14).")
    print()

    print("-" * 70)
    print("GENERATING TEXT (sampled: proportional to frequency)")
    print("-" * 70)
    rng = random.Random(7)
    for i in range(4):
        text = " ".join(generate_sampled(counts, "the", 12, rng))
        print(f"    sample {i + 1}: {text}")
    print()

    print("-" * 70)
    print("WHAT THIS DEMONSTRATES - AND WHAT IT DOES NOT")
    print("-" * 70)
    print("* A model just learned from text with ZERO human labels. That is")
    print("  the whole self-supervised trick, and it is what makes training")
    print("  on a trillion words possible.")
    print()
    print("* The output is locally plausible and globally meaningless. It")
    print("  looks like English because each PAIR of words really did occur")
    print("  together, but there is no idea being expressed.")
    print()
    print("* The reason is the context window: this model sees exactly ONE")
    print("  previous word. It cannot know that a sentence started with")
    print("  'the customer' should not end by approving its own refund.")
    print()
    print("* A transformer fixes precisely this. Self-attention lets every")
    print("  position look at every earlier position, so context is thousands")
    print("  of tokens instead of one (M4-L07). The training objective is")
    print("  IDENTICAL to what you just ran. Only the context changed.")
    print()
    print("* Note also what the model has NO concept of: truth. It learned")
    print("  'billing -> issue' because that pair occurred, not because")
    print("  anything about billing is true. Scale this up and you have both")
    print("  the capability and the hallucination problem (M1-L10).")
    print("=" * 70)


if __name__ == "__main__":
    main()
