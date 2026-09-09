"""M4-L03 lab -- tokenization, from first principles and with a real tokenizer.

Trains BPE by hand on the lesson's corpus showing every merge, then measures
chars-per-token across content types, demonstrates the character-counting
failure and its fix, shows whitespace sensitivity, proves that byte-level
truncation corrupts text, and reproduces the cost model.

Runs WITH OR WITHOUT network access: uses tiktoken if an encoding is available
locally, otherwise falls back to a BPE trained in this script. Both paths
produce every section.

Run:  python labs/m4/l03_tokenizers.py
"""

from __future__ import annotations

import collections
import unicodedata

# --------------------------------------------------------------- tokenizer
REAL_TOKENIZER = None
TOKENIZER_NAME = "fallback BPE (trained in this script)"
try:
    import tiktoken

    REAL_TOKENIZER = tiktoken.get_encoding("cl100k_base")
    TOKENIZER_NAME = "tiktoken cl100k_base"
except Exception as exc:                       # no network, or not installed
    print(f"[note] tiktoken unavailable ({type(exc).__name__}); "
          f"using the fallback tokenizer.")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ------------------------------------------------- 1. BPE by hand
rule("1. BPE TRAINING, EVERY MERGE  (corpus: 'low low low lower lowest')")

CORPUS_WORDS = ["low", "low", "low", "lower", "lowest"]


def bpe_train(words, n_merges, verbose=True):
    """Train BPE. Returns the ordered merge rules."""
    # Each word is a tuple of symbols; '_' marks the word boundary.
    vocab = collections.Counter(tuple(w) + ("_",) for w in words)
    merges = []
    for step in range(1, n_merges + 1):
        pairs = collections.Counter()
        for word, count in vocab.items():
            for a, b in zip(word, word[1:]):
                pairs[(a, b)] += count
        if not pairs:
            break
        best_count = max(pairs.values())
        # Deterministic tie-break: most frequent, then alphabetical.
        best = min((p for p, c in pairs.items() if c == best_count))
        merges.append(best)

        new_vocab = collections.Counter()
        for word, count in vocab.items():
            merged, i = [], 0
            while i < len(word):
                if i + 1 < len(word) and (word[i], word[i + 1]) == best:
                    merged.append(word[i] + word[i + 1])
                    i += 2
                else:
                    merged.append(word[i])
                    i += 1
            new_vocab[tuple(merged)] += count
        vocab = new_vocab

        if verbose:
            top = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0]))[:4]
            shown = "  ".join(f"({a}{b})={c}" for (a, b), c in top)
            print(f"\n  merge {step}: {best[0]!r}+{best[1]!r} -> "
                  f"{best[0] + best[1]!r}   (count {best_count})")
            print(f"    top pairs before : {shown}")
            print(f"    corpus after     : "
                  + "   ".join(" ".join(w) for w in sorted(vocab)))
    return merges


merges = bpe_train(CORPUS_WORDS, 6)
print(f"\n  learned merge rules, IN ORDER:")
for i, (a, b) in enumerate(merges, start=1):
    print(f"    {i}. {a!r} + {b!r} -> {a + b!r}")
print("\n  Encoding applies these rules IN THIS ORDER, repeatedly. They are an")
print("  ordered list, not a set -- applying them greedily by length gives")
print("  different, wrong tokens.")


def bpe_encode(word, merges):
    symbols = list(word) + ["_"]
    for a, b in merges:                        # in learned order
        i = 0
        while i < len(symbols) - 1:
            if symbols[i] == a and symbols[i + 1] == b:
                symbols[i:i + 2] = [a + b]
            else:
                i += 1
    return symbols


print("\n  encoding with the learned rules:")
for w in ("low", "lower", "lowest", "slow", "flowering"):
    toks = bpe_encode(w, merges)
    print(f"    {w:<12} -> {toks}  ({len(toks)} tokens)")
print("\n  'low' is now ONE token. 'slow' and 'flowering' were never in the")
print("  corpus and still encode -- they decompose into pieces. Nothing is")
print("  ever out-of-vocabulary; that is the point of subword tokenization.")


# ------------------------------------------------- tokenizer interface
def encode(text: str) -> list:
    if REAL_TOKENIZER is not None:
        return REAL_TOKENIZER.encode(text)
    # Fallback: train once on a general corpus, then encode word by word.
    return _fallback_encode(text)


_FALLBACK_MERGES = None
_FALLBACK_CORPUS = (
    "the quick brown fox jumps over the lazy dog and the cat sat on the mat "
    "we need to process the request and return the response to the user with "
    "the correct status code and a helpful message about what happened here "
    "customer support billing payment refund invoice account technical error"
) * 6


def _fallback_encode(text: str) -> list:
    global _FALLBACK_MERGES
    if _FALLBACK_MERGES is None:
        _FALLBACK_MERGES = bpe_train(_FALLBACK_CORPUS.split(), 220, verbose=False)
    out = []
    for word in text.split(" "):
        if word:
            out.extend(bpe_encode(word, _FALLBACK_MERGES))
        else:
            out.append("_")
    return out


def n_tokens(text: str) -> int:
    return len(encode(text))


rule(f"2. CHARACTERS PER TOKEN, BY CONTENT TYPE   [{TOKENIZER_NAME}]")

SAMPLES = {
    "English prose": (
        "The support team reviewed the account and confirmed that the customer "
        "had been charged twice for the same order. A refund was issued the "
        "following morning and the customer was notified by email."
    ),
    "Technical English": (
        "The idempotency key ensures the downstream service deduplicates "
        "retried requests, so a transient timeout does not produce duplicate "
        "charges against the customer's payment method."
    ),
    "Python code": (
        "def process(payload: dict) -> Response:\n"
        "    validated = TicketCreate.model_validate(payload)\n"
        "    if validated.priority > 3:\n"
        "        return escalate(validated, reason='high_priority')\n"
        "    return queue.enqueue(validated)\n"
    ),
    "JSON": (
        '{"order_id": "GB-4471", "amount_gbp": 29.99, "status": "refunded", '
        '"items": [{"sku": "AB-1", "qty": 2}, {"sku": "CD-9", "qty": 1}]}'
    ),
    "Numbers": "1234567890 9876543210 2024 3.14159265358979 42 1000000 0.0001",
    "UUIDs": ("550e8400-e29b-41d4-a716-446655440000 "
              "f47ac10b-58cc-4372-a567-0e02b2c3d479"),
    "Base64": ("VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIHRoZSBsYXp5IGRvZw=="),
    "Hindi (Devanagari)": (
        "ग्राहक ने बताया कि उनके खाते से दो बार पैसे काटे गए हैं और उन्हें "
        "वापसी की आवश्यकता है।"
    ),
    "Japanese": "お客様のアカウントから同じ注文に対して二重に請求されたことを確認しました。",
}

print(f"  {'content type':<22}{'chars':>8}{'tokens':>9}{'chars/tok':>12}"
      f"{'vs English':>12}")
english_ratio = None
ratios = {}
for name, text in SAMPLES.items():
    chars = len(text)
    toks = n_tokens(text)
    ratio = chars / toks
    ratios[name] = ratio
    if english_ratio is None:
        english_ratio = ratio
    print(f"  {name:<22}{chars:>8}{toks:>9}{ratio:>12.2f}"
          f"{english_ratio / ratio:>11.2f}x")

print("\n  The 'vs English' column is the COST MULTIPLIER: how many times more")
print("  tokens the same number of characters costs, relative to prose.")


rule("3. THE SAME MEANING, DIFFERENT LANGUAGES  (the equity problem)")

SAME_MEANING = {
    "English": "The customer was charged twice and needs a refund.",
    "French": "Le client a été facturé deux fois et a besoin d'un remboursement.",
    "German": "Dem Kunden wurde zweimal eine Gebühr berechnet und er benötigt "
              "eine Rückerstattung.",
    "Hindi": "ग्राहक से दो बार शुल्क लिया गया और उसे धनवापसी की आवश्यकता है।",
    "Japanese": "お客様は二重に請求されたため、返金が必要です。",
    "Thai": "ลูกค้าถูกเรียกเก็บเงินสองครั้งและต้องการเงินคืน",
}

base = n_tokens(SAME_MEANING["English"])
print(f"  {'language':<12}{'chars':>7}{'tokens':>9}{'vs English':>13}"
      f"   the same sentence")
for lang, text in SAME_MEANING.items():
    t = n_tokens(text)
    print(f"  {lang:<12}{len(text):>7}{t:>9}{t / base:>12.2f}x")

worst = max(SAME_MEANING, key=lambda k: n_tokens(SAME_MEANING[k]))
worst_ratio = n_tokens(SAME_MEANING[worst]) / base
print(f"\n  {worst} costs {worst_ratio:.1f}x English for the SAME sentence.")
print("  Those users pay more per message, fit less history in the context")
print("  window, and wait longer -- for identical content. If you serve")
print("  multiple languages, measure this and set limits per language.")


rule("4. WHY THE MODEL MISCOUNTS LETTERS")

WORD = "strawberry"
toks = encode(WORD)
print(f"  the word          : {WORD!r}  ({len(WORD)} characters)")
print(f"  as the model sees : {toks}")
print(f"  token count       : {len(toks)}")
if REAL_TOKENIZER is not None:
    pieces = [REAL_TOKENIZER.decode([t]) for t in toks]
    print(f"  those IDs decode to: {pieces}")
print(f"\n  actual count of 'r': {WORD.count('r')}")
print("\n  The model receives integers. There is no operation available to it")
print("  that inspects the letters inside a token -- the embedding for that ID")
print("  was learned from CONTEXT, not from spelling. Asking it to count")
print("  letters is asking it to recall a fact about the string, not to")
print("  perform a computation on the input.")

SPACED = " ".join(WORD)
toks_spaced = encode(SPACED)
print(f"\n  THE FIX -- spell it out first:")
print(f"    {SPACED!r}")
print(f"    -> {len(toks_spaced)} tokens instead of {len(toks)}")
if REAL_TOKENIZER is not None:
    print(f"    decoded: {[REAL_TOKENIZER.decode([t]) for t in toks_spaced]}")
print("    Each letter is now its OWN token, so counting becomes a task the")
print("    model can actually do over its input. It costs more tokens.")
print("    (The better fix is a tool -- M8-L04.)")


rule("5. WHITESPACE IS PART OF THE TOKEN")

for a, b in (("the", " the"), ("Hello", " Hello"), ("json", " json")):
    ta, tb = encode(a), encode(b)
    same = "SAME" if ta == tb else "DIFFERENT"
    print(f"  {a!r:<10} -> {str(ta):<22}")
    print(f"  {b!r:<10} -> {str(tb):<22}  {same}")
    print()
print("  A prompt ending in a trailing space commits the model to a token that")
print("  usually STARTS a word, which measurably changes what follows.")
print("  Strip trailing whitespace from prompts.")


rule("6. TRUNCATION MUST HAPPEN ON TOKEN BOUNDARIES")

text = "Le client a été facturé deux fois — remboursement requis. 日本語のテキスト"
raw = text.encode("utf-8")
print(f"  text  : {text}")
print(f"  bytes : {len(raw)}   characters: {len(text)}\n")

# Find every byte offset that lands INSIDE a multi-byte character.
broken_cuts = []
for cut in range(1, len(raw) + 1):
    try:
        raw[:cut].decode("utf-8")
    except UnicodeDecodeError:
        broken_cuts.append(cut)

print(f"  of {len(raw)} possible byte cut points, "
      f"{len(broken_cuts)} produce invalid UTF-8:")
print(f"    {broken_cuts}")
print(f"    that is {len(broken_cuts) / len(raw):.0%} of all cut positions.\n")

for cut in (12, 13, 14, 35, 36, 37):
    chunk = raw[:cut]
    try:
        decoded = chunk.decode("utf-8")
        status = f"ok     -> {decoded!r}"
    except UnicodeDecodeError as e:
        status = f"BROKEN -> UnicodeDecodeError: {e.reason}"
    print(f"  bytes[:{cut}]  {status}")

print("\n  lossy decoding, which is what a careless pipeline actually produces")
print("  (errors='replace' silently substitutes U+FFFD and moves on):")
for cut in broken_cuts[:4]:
    print(f"    bytes[:{cut}] -> "
          f"{raw[:cut].decode('utf-8', errors='replace')!r}")
print("\n  Note the replacement character at the end. Nothing raised; the text")
print("  is simply corrupted, and it reaches the model looking almost right.")

print("\n  Now the same cut on TOKEN boundaries:")
tk = encode(text)
for keep in (4, 6, 8):
    part = tk[:keep]
    if REAL_TOKENIZER is not None:
        print(f"    first {keep} tokens -> {REAL_TOKENIZER.decode(part)!r}")
    else:
        print(f"    first {keep} tokens -> {part}")
print("\n  Always valid text. Truncate on tokens, never on bytes or characters.")


rule("7. COST MODEL  (the lesson's support assistant)")

SYSTEM = 800
CONTEXT = 1900
HISTORY = 900
USER = 55
OUTPUT = 200
REQUESTS = 50_000
IN_PRICE = 3.00 / 1_000_000        # illustrative only -- NOT real pricing
OUT_PRICE = 15.00 / 1_000_000      # illustrative only

parts = [("system prompt", SYSTEM), ("retrieved context", CONTEXT),
         ("conversation history", HISTORY), ("user message", USER)]
total_in = sum(n for _, n in parts)

print(f"  {'component':<24}{'tokens':>9}{'% of input':>13}{'per month':>15}")
for name, n in parts:
    print(f"  {name:<24}{n:>9,}{n / total_in:>12.0%}{n * REQUESTS:>15,}")
print(f"  {'INPUT TOTAL':<24}{total_in:>9,}{1.0:>12.0%}"
      f"{total_in * REQUESTS:>15,}")
print(f"  {'output':<24}{OUTPUT:>9,}{'--':>13}{OUTPUT * REQUESTS:>15,}")

cost_in = total_in * REQUESTS * IN_PRICE
cost_out = OUTPUT * REQUESTS * OUT_PRICE
print(f"\n  ILLUSTRATIVE cost at $3/M input, $15/M output "
      f"(NOT current pricing -- check your provider):")
print(f"    input  ${cost_in:>10,.2f}   {cost_in / (cost_in + cost_out):>5.0%} of the bill"
      f"   ({total_in * REQUESTS / (total_in + OUTPUT) / REQUESTS:.0%} of tokens)")
print(f"    output ${cost_out:>10,.2f}   {cost_out / (cost_in + cost_out):>5.0%} of the bill"
      f"   ({OUTPUT / (total_in + OUTPUT):>5.0%} of tokens)")
print(f"    total  ${cost_in + cost_out:>10,.2f} per month")
print(f"\n  Output is {OUTPUT / (total_in + OUTPUT):.0%} of tokens but "
      f"{cost_out / (cost_in + cost_out):.0%} of the bill.")

print(f"\n  savings available:")
sys_cost = SYSTEM * REQUESTS * IN_PRICE
print(f"    cache the system prompt      : up to ${sys_cost:,.2f}/mo "
      f"({SYSTEM * REQUESTS:,} tokens of unchanging text)")
ctx_cost = CONTEXT / 2 * REQUESTS * IN_PRICE
print(f"    retrieve 2 docs instead of 4 : up to ${ctx_cost:,.2f}/mo "
      f"(test quality first -- M7-L16)")

print("\n  NOW THE ESTIMATE ERROR. The 1,900-token context figure assumed")
print("  English prose at ~4 chars/token. If the retrieved documents are JSON:")
json_ratio = ratios["English prose"] / ratios["JSON"]
print(f"    measured JSON penalty        : {json_ratio:.2f}x")
ctx_json = CONTEXT * json_ratio
new_in = total_in - CONTEXT + ctx_json
print(f"    context tokens               : {CONTEXT:,} -> {ctx_json:,.0f}")
print(f"    input tokens per request     : {total_in:,} -> {new_in:,.0f}")
print(f"    monthly input cost           : ${cost_in:,.2f} -> "
      f"${new_in * REQUESTS * IN_PRICE:,.2f}"
      f"  ({new_in / total_in - 1:+.0%})")
print("\n  A single wrong assumption about content type moved the bill by that")
print("  much. Tokenize a REAL sample before committing to a budget.")
print("  And note: a billing alert notifies you; it does not cap spending.")

print("\nDone.")
