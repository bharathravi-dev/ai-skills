"""M1-L02: the same spam task solved rule-based and learned, side by side.

Everything is implemented from scratch (no scikit-learn) so nothing is hidden.

Run:
    python3 labs/m1/l02_rules_vs_learned.py

Deterministic: random.seed(42) fixes the shuffle, so your output matches the
lesson exactly. Standard library only, Python 3.9+.
"""

from __future__ import annotations

import math
import random
from collections import Counter

# ---------------------------------------------------------------------------
# 1. Synthetic dataset.  Written by hand for this course: no real emails, no
#    licensing questions, no personal data.  (label, message)
# ---------------------------------------------------------------------------
DATA: list[tuple[str, str]] = [
    # --- SPAM: obvious, uses the classic keywords ---
    ("SPAM", "win free money now"),
    ("SPAM", "free entry to win a prize"),
    ("SPAM", "you win a free vacation"),
    ("SPAM", "click here for free money"),
    ("SPAM", "congratulations you win the lottery prize"),
    ("SPAM", "free gift card winner"),
    ("SPAM", "win big money today"),
    ("SPAM", "claim your free prize now"),
    ("SPAM", "free trial win rewards"),
    ("SPAM", "limited offer free money guaranteed"),
    # --- SPAM: same intent, none of the rule's keywords ---
    ("SPAM", "claim your cash bonus reward"),
    ("SPAM", "urgent action required verify your account"),
    ("SPAM", "you have been selected act now"),
    ("SPAM", "exclusive deal act immediately limited time"),
    ("SPAM", "verify your account or it will be closed"),
    ("SPAM", "double your income working from home"),
    ("SPAM", "cheap medication no prescription needed"),
    ("SPAM", "your package could not be delivered click link"),
    ("SPAM", "investment opportunity guaranteed returns"),
    ("SPAM", "reset your password immediately suspicious login"),
    ("SPAM", "special discount only for you act fast"),
    ("SPAM", "earn cash from home no experience"),
    ("SPAM", "your subscription expired renew now"),
    ("SPAM", "unclaimed refund waiting for you"),
    ("SPAM", "hot deal buy now while stocks last"),
    # --- HAM: ordinary work messages ---
    ("HAM", "meeting at noon today"),
    ("HAM", "lunch meeting today at one"),
    ("HAM", "can you review the pull request"),
    ("HAM", "the deploy finished successfully"),
    ("HAM", "please find the report attached"),
    ("HAM", "standup moved to nine thirty"),
    ("HAM", "here are the notes from the meeting"),
    ("HAM", "the build is failing on main"),
    ("HAM", "i will be out of office tomorrow"),
    ("HAM", "thanks for the quick review"),
    ("HAM", "let us discuss the roadmap tomorrow"),
    ("HAM", "the database migration is complete"),
    ("HAM", "can we move the call to friday"),
    ("HAM", "please approve the timesheet today"),
    ("HAM", "the client demo went well"),
    ("HAM", "sharing the design document for feedback"),
    ("HAM", "sprint planning is on monday"),
    ("HAM", "the test suite passes locally"),
    ("HAM", "updated the ticket with my findings"),
    ("HAM", "welcome to the team"),
    # --- HAM: legitimate messages containing the rule's keywords.
    #     These are what make a keyword rule produce false positives. ---
    ("HAM", "the meeting room is free at noon"),
    ("HAM", "feel free to review the document"),
    ("HAM", "we win the contract if the demo works"),
    ("HAM", "the free tier limit was reached"),
    ("HAM", "prize giving is at the team event"),
    ("HAM", "petty cash reimbursement form attached"),
    ("HAM", "free parking is available on site"),
    ("HAM", "money transfer to the vendor is approved"),
    ("HAM", "the free trial of the tool expires friday"),
    ("HAM", "who will win the internal hackathon"),
]

# Four adversarial cases, held out completely: they appear in neither the
# training nor the test split. Used only for the demonstration table.
ADVERSARIAL: list[tuple[str, str]] = [
    ("HAM", "free meeting room for the team"),
    ("SPAM", "claim your cash bonus reward today"),
    ("SPAM", "f r e e   m o n e y"),
    ("SPAM", "urgent winner selected claim prize"),
]

# ---------------------------------------------------------------------------
# 2. The rule-based classifier.  This IS the whole model: a set of words.
# ---------------------------------------------------------------------------
SPAM_WORDS = {"free", "win", "prize", "money"}


def classify_rule(message: str) -> str:
    """Return SPAM if any word in the message is on the banned list."""
    for word in message.lower().split():
        if word in SPAM_WORDS:
            return "SPAM"
    return "HAM"


# ---------------------------------------------------------------------------
# 3. The learned classifier: Naive Bayes, trained by counting.
# ---------------------------------------------------------------------------
class NaiveBayes:
    """Multinomial Naive Bayes with Laplace (add-one) smoothing."""

    def __init__(self) -> None:
        self.word_counts: dict[str, Counter[str]] = {}
        self.total_words: dict[str, int] = {}
        self.doc_counts: Counter[str] = Counter()
        self.vocab: set[str] = set()

    def train(self, rows: list[tuple[str, str]]) -> None:
        """'Training' here is literally counting words per class."""
        for label, message in rows:
            self.doc_counts[label] += 1
            words = message.lower().split()
            self.word_counts.setdefault(label, Counter()).update(words)
            self.vocab.update(words)
        for label, counter in self.word_counts.items():
            self.total_words[label] = sum(counter.values())

    def _log_prob(self, word: str, label: str) -> float:
        """log P(word | label), Laplace-smoothed so it is never log(0)."""
        count = self.word_counts[label][word]
        numerator = count + 1
        denominator = self.total_words[label] + len(self.vocab)
        return math.log(numerator / denominator)

    def classify(self, message: str) -> str:
        """Pick the label with the highest total log-probability.

        We ADD logs rather than MULTIPLY probabilities: multiplying 20 small
        numbers underflows to 0.0 in floating point. log(a*b) = log(a)+log(b).
        """
        total_docs = sum(self.doc_counts.values())
        best_label, best_score = "HAM", -math.inf

        for label in self.doc_counts:
            # Start from the prior: how common is this class overall?
            score = math.log(self.doc_counts[label] / total_docs)
            for word in message.lower().split():
                score += self._log_prob(word, label)
            if score > best_score:
                best_label, best_score = label, score
        return best_label


# ---------------------------------------------------------------------------
# 4. Train/test split and evaluation.
# ---------------------------------------------------------------------------
def train_test_split(
    rows: list[tuple[str, str]], test_fraction: float, seed: int
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Shuffle then cut. The seed makes this reproducible."""
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    cut = int(len(shuffled) * (1 - test_fraction))
    return shuffled[:cut], shuffled[cut:]


def accuracy(rows: list[tuple[str, str]], classify) -> tuple[int, int]:
    """Return (number correct, total)."""
    correct = sum(1 for label, message in rows if classify(message) == label)
    return correct, len(rows)


def main() -> None:
    train_rows, test_rows = train_test_split(DATA, test_fraction=0.2, seed=42)

    model = NaiveBayes()
    model.train(train_rows)

    print("=" * 70)
    print("RULE-BASED vs LEARNED  -  the same spam task, two approaches")
    print("=" * 70)
    print()
    print(f"Training messages: {len(train_rows)}   Test messages: {len(test_rows)}")
    print()

    rule_correct, total = accuracy(test_rows, classify_rule)
    bayes_correct, _ = accuracy(test_rows, model.classify)

    print("--- Accuracy on the held-out test set ---")
    print(f"Rule-based  : {rule_correct:2d}/{total}  = {100 * rule_correct / total:.1f}%")
    print(f"Naive Bayes : {bayes_correct:2d}/{total}  = {100 * bayes_correct / total:.1f}%")
    print()

    print("--- The adversarial cases (never seen in training) ---")
    print(f"{'Message':<40} {'Truth':<6} {'Rule':<6} {'Bayes'}")
    print("-" * 70)
    for truth, message in ADVERSARIAL:
        print(
            f"{message[:39]:<40} {truth:<6} "
            f"{classify_rule(message):<6} {model.classify(message)}"
        )
    print()

    # --- The most instructive part of this lab: the model is RIGHT for the
    # --- WRONG REASON on the spaced-out attack.  Show the actual numbers.
    print("--- Why the 'f r e e   m o n e y' result is a trap ---")
    attack = "f r e e   m o n e y"
    tokens = attack.lower().split()
    known = [w for w in tokens if w in model.vocab]
    total_docs = sum(model.doc_counts.values())
    vocab_size = len(model.vocab)
    print(f"Tokens the model sees : {tokens}")
    print(f"Of those, known words : {known}   <- none of them")
    print()
    for label in ("HAM", "SPAM"):
        denom = model.total_words[label] + vocab_size
        prior = model.doc_counts[label] / total_docs
        score = math.log(prior) + len(tokens) * math.log(1 / denom)
        print(
            f"  {label:<5} prior={prior:.3f}  "
            f"train words={model.total_words[label]:<4} "
            f"P(unknown|{label})=1/{denom}={1 / denom:.6f}  "
            f"log score={score:.2f}"
        )
    print()
    print("Every token is unknown, so BOTH classes fall back to the smoothing")
    print("floor. SPAM wins only because spam training messages are SHORTER, so")
    print("its denominator is smaller and each unknown word scores slightly")
    print("higher. The model did not detect the attack. It got the right answer")
    print("from an artefact of message length. This is a spurious correlation")
    print("(M1-L09), and it would flip the moment your spam samples got longer.")
    print()

    print("--- What this lab shows ---")
    print("1. The rule fires on 'free'/'win' regardless of context, so it calls")
    print("   'we win the contract if the demo works' SPAM. False positive.")
    print("2. The rule has no opinion on words its author never listed, so")
    print("   'verify your account or it will be closed' passes. False negative.")
    print("3. Naive Bayes scored 11/11 here - but 11 examples is weak evidence.")
    print("   Do not trust a percentage without a sample size (M3-L14).")
    print("4. A right answer is not the same as correct reasoning. Always ask")
    print("   WHY a model was right, not just whether it was.")
    print("=" * 70)


if __name__ == "__main__":
    main()
