# M4-L03 — Tokens, Tokenizers, Vocabularies and Token IDs

| | |
|---|---|
| **Lesson ID** | M4-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L01](M4-L01-foundation-models.md), [M2-L03](../module-02-python-foundations/M2-L03-collections.md) |

---

> **This is the most practically useful lesson in Module 4.**
> Tokenization determines what you are billed, what fits in the context window, and an entire family
> of failures that look like the model "being stupid" but are nothing of the kind. Almost every
> engineer who works with LLMs eventually learns this material — usually after an incident. Learning
> it now is cheaper.

---

## 1. Learning objectives

1. **Explain** why models use subword tokens rather than characters or words.
2. **Trace** the BPE algorithm by hand on a small corpus.
3. **Measure** tokens per character for different content types and predict where the rule of thumb
   fails.
4. **Diagnose** the failure modes that tokenization causes, including character counting and
   arithmetic.
5. **Estimate** and verify the token cost of a real workload.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Token** | The atomic unit a model reads and writes. Usually a subword. |
| **Tokenizer** | The component converting text ↔ tokens. |
| **Vocabulary** | The fixed set of tokens a model knows. Typically 32k–200k. |
| **Token ID** | The integer index of a token in the vocabulary. |
| **BPE** | Byte Pair Encoding — the dominant subword algorithm. |
| **Merge rule** | A learned pair-joining step in BPE, applied in a fixed order. |
| **Special token** | A token with structural meaning, e.g. end-of-text or a chat role marker. |
| **OOV** | Out-of-vocabulary — a word the tokenizer cannot represent. Subword tokenizers eliminate this. |
| **Byte-level BPE** | BPE operating on raw bytes, so any input is representable. |
| **Detokenization** | Turning token IDs back into text. |
| **Context window** | The maximum tokens a model can attend over (M4-L06). |

---

## 3. Plain-language explanation

### 3.1 The problem tokenization solves

A model needs a **fixed, finite** set of symbols, because its input embedding table and output layer
both have one row per symbol. Two obvious choices both fail:

**Option 1 — one token per word.**
- Vocabulary must be enormous, and still incomplete: names, typos, new words, other languages.
- Anything unseen becomes `<unknown>` — information destroyed.
- `run`, `runs`, `running` are three unrelated entries; nothing links them.

**Option 2 — one token per character.**
- Tiny vocabulary (~256 bytes), nothing is ever unknown. 
- But sequences become **4–5× longer**, and attention cost is quadratic in length (M4-L07). A
  1,000-word document becomes ~5,000 positions instead of ~1,300.

**Subword tokenization takes the middle.** Frequent words become single tokens; rare words split into
meaningful pieces:

```
"the"           → 1 token
"running"       → "running"         (1 token — common enough to earn its own)
"tokenization"  → "token" "ization" (2 tokens)
"Kaczmarczyk"   → "K" "acz" "mar" "czyk"  (4 tokens)
```

**Nothing is ever unknown**, because the tokenizer can always fall back to bytes, and common text
stays short. That is the whole design.

### 3.2 Why you should care

Four consequences, all of which will affect you:

1. **You are billed per token.** Not per word, not per character. The relationship between them
   varies by a factor of **four or more** depending on content.
2. **The context window is measured in tokens** (M4-L06). "Will this fit?" is a tokenizer question.
3. **The model cannot see inside a token.** It sees `strawberry` as one or two opaque IDs, not as
   letters. This causes the famous character-counting failures — and they are not stupidity, they are
   a direct, predictable consequence of the input representation.
4. **Whitespace is part of the token.** `" the"` and `"the"` are different tokens with different IDs.
   A stray leading space genuinely changes the input.

---

## 4. Analogy

**Tokens are like the chunks a fluent reader takes in at a glance.** You do not read *c-a-t*; you take
`cat` in one saccade. An unfamiliar surname you break into syllables. Frequency determines chunk size.

### Where the analogy breaks

1. **You can always fall back to spelling. The model cannot.** It has no access to a token's letters
   at all — the token is an integer, and its embedding was learned from context, not spelling.
2. **Your chunking adapts to the text. The tokenizer's merge rules are frozen** at training time, so
   text unlike its training data chunks badly.
3. **You are not charged per glance.** Chunk size *is* your bill.
4. **You would chunk `2024` as one thing. A tokenizer might split it as `20`+`24`**, which is part of
   why arithmetic is unreliable.

---

## 5. Detailed technical explanation

### 5.1 BPE, precisely

**Training** (done once, by the model provider):

```
1. Start with the vocabulary = all individual bytes (256 entries).
2. Count every adjacent pair in the corpus.
3. Merge the most frequent pair into a new token; record the merge rule.
4. Repeat until the vocabulary reaches the target size.
```

**Encoding** (every time you send a prompt): apply the recorded merge rules **in the order they were
learned**, repeatedly, until no rule applies.

**Order matters, and this is the part people get wrong.** The rules are not a set to be applied
greedily by length; they are an ordered list. Applying them out of order gives different — and wrong
— tokens.

### 5.2 A worked merge, by hand

Corpus: `low low low lower lowest`

Start with characters (using `_` for the word boundary):

```
l o w _   l o w _   l o w _   l o w e r _   l o w e s t _
```

Pair counts: `(l,o)` = 5, `(o,w)` = 5, `(w,_)` = 3, `(w,e)` = 2, …

Merge `(l,o)` → `lo` *(first alphabetically among ties, in this convention)*:

```
lo w _   lo w _   lo w _   lo w e r _   lo w e s t _
```

Now `(lo,w)` = 5 is the most frequent. Merge → `low`:

```
low _   low _   low _   low e r _   low e s t _
```

Now `(low,_)` = 3. Merge → `low_`:

```
low_  low_  low_   low e r _   low e s t _
```

**After three merges, `low` is a single token** and `lower`/`lowest` still decompose into pieces that
share it. The lab runs this exact corpus and prints every step.

### 5.3 The rule of thumb, and where it fails

The widely-quoted rule is **≈ 4 characters per token for English prose**. **It is conservative and
somewhat dated.** §7.3 measures **5.54** for modern English prose with `cl100k_base` — the rule
overestimates cost by about 39% for that case. Use it as a floor for a quick sanity check, and measure
when the number matters.

Here are the **measured** ratios (`cl100k_base`, §7.3 — every figure produced by the lab, not
estimated):

| Content | Chars/token | Cost vs prose | Why |
|---|---|---|---|
| English prose | **5.54** | 1.00× | The tokenizer was trained on this |
| Technical English | **5.56** | **1.00×** | Essentially identical — see below |
| Python code | **4.98** | 1.11× | Better than folklore suggests |
| **JSON** | **2.22** | **2.50×** | Braces, quotes, colons each cost a token |
| Numbers | 1.97 | 2.82× | Digits group unpredictably |
| UUIDs | 1.78 | 3.11× | No learned merges apply |
| Base64 | 1.43 | 3.88× | Same |
| **Hindi (Devanagari)** | **1.00** | **5.54×** | Roughly one token per character |
| **Japanese** | **0.97** | **5.69×** | Sometimes *more* tokens than characters |

**Two of these contradict the received wisdom, and both matter:**

- **Technical English costs the same as ordinary prose** (5.56 vs 5.54). The intuition that jargon
  tokenizes badly is wrong for a modern 100k-token vocabulary — the technical vocabulary is in it.
- **Code is far cheaper than commonly claimed** — 4.98, only 11% worse than prose, not the 2.5–3.5
  that older guidance suggests. Modern tokenizers have absorbed a great deal of code.

**What *is* expensive is structure and non-Latin script.** JSON at 2.50× and Devanagari at 5.54× are
the rows that will actually surprise your budget.

**The non-Latin rows have an equity dimension worth stating plainly.** §7.3 tokenizes *the same
sentence* in six languages:

| Language | Tokens | vs English |
|---|---|---|
| English | 10 | 1.00× |
| French | 19 | 1.90× |
| German | 22 | 2.20× |
| Japanese | 26 | 2.60× |
| Thai | 40 | 4.00× |
| **Hindi** | **65** | **6.50×** |

**Hindi costs 6.5× English for the identical sentence.** Those users pay more per message, fit less
conversation history in the context window, and wait longer — for the same content. A single uniform
character limit applied across languages is therefore not neutral; it is materially stricter for some
users than others. If you ship a multilingual product, measure this and set limits per language.

### 5.4 The failure modes tokenization causes

**(a) Character counting.** "How many r's in strawberry?" The model sees perhaps `[496, 675, 15717]`
— three integers. Nothing in that representation encodes letters. It answers from patterns in
training text about spelling, which is unreliable.

**Not a reasoning failure — an input-representation failure.** The fix is a tool (M8-L04), or asking
for the word spelled out with spaces first so each letter becomes its own token.

**(b) Arithmetic.** `1234 + 5678` may tokenize as `12|34 + 56|78`. The model never sees place value.
Modern tokenizers often split digits individually to help, but arithmetic remains unreliable — **use
a calculator tool.**

**(c) Reversal and anagrams.** Same cause as (a).

**(d) Whitespace sensitivity.** `"the"` and `" the"` are different tokens. A prompt ending in a
trailing space can measurably change output, because you have committed the model to a token that
usually starts a word.

**(e) Truncation mid-token.** Cutting a byte sequence at an arbitrary point can split a multi-byte
character, producing mojibake. **Truncate on token boundaries, never on characters or bytes.**

**(f) Rhyming and syllables.** Tokens do not align with phonemes.

### 5.5 Special tokens

Every model reserves tokens with structural meaning:

| Kind | Purpose |
|---|---|
| End-of-text | Marks a document boundary; signals generation to stop |
| Padding | Fills a batch to equal length |
| Chat role markers | Delimit system / user / assistant turns |
| Tool-call markers | Delimit structured tool invocations |

**A security consequence.** If a user can inject the literal text of a role marker into their input
and the tokenizer encodes it as the *special* token rather than as plain text, they can forge a turn
boundary. Reputable tokenizer libraries default to **not** encoding special tokens from user text —
verify that yours does, and never pass user input with special-token encoding enabled. (M10-L06.)

### 5.6 Tokenizers differ between models

**A token count from one model does not transfer to another.** Different vocabulary sizes, different
training corpora, different merge rules.

Practical rules:
- **Use the tokenizer for the model you are actually calling.**
- Do not compare token counts across providers as if they were the same unit.
- **Do not compare per-token prices across providers without also comparing tokenizer efficiency** —
  a cheaper per-token price with a less efficient tokenizer can cost more per document. §7.3 measures
  a case.
- Cache token counts; tokenizing is not free at high volume.

### 5.7 Estimating cost properly

```
cost = (input_tokens × input_price + output_tokens × output_price) × requests
```

**Output tokens are usually several times more expensive than input tokens** `[UNVERIFIED — check
current pricing]`, so a verbose response format costs more than a verbose prompt.

**Estimate, then measure.** Tokenize a representative sample of your real traffic. §7.3 changes one
assumption in §6's model — retrieved context is JSON rather than prose — and the monthly input bill
moves **+78%**. One wrong assumption about content type, and the budget is wrong by three quarters.

### 5.8 Assumptions and limitations

- Specific vocabularies, ratios and prices are model- and provider-specific and change. Everything
  numeric here is either measured by the lab or marked `[UNVERIFIED]`.
- The lab's from-scratch BPE is simplified for clarity — real implementations use pre-tokenization
  regexes and byte-level fallbacks.
- `tiktoken` matches OpenAI models. Other providers use different tokenizers; the lab is written to
  run with or without any network access.

---

## 6. Worked example — costing a support-assistant deployment

**Scenario.** A support assistant. 50,000 requests a month.

**Per request:**

| Part | Content | Estimate |
|---|---|---|
| System prompt | 600 words of instructions | 800 tokens |
| Retrieved context | 4 documents × 350 words | 1,900 tokens |
| Conversation history | ~6 turns | 900 tokens |
| User message | ~40 words | 55 tokens |
| **Input total** | | **≈ 3,655 tokens** |
| Output | ~150 words | ≈ 200 tokens |

**Monthly:** 182.75M input tokens, 10M output tokens.

**Now the three observations that matter:**

**1. The system prompt is sent every single time.** 800 tokens × 50,000 = **40M tokens a month for
text that never changes.** This is what prompt caching exists for (M5-L16), and it is often the single
largest available saving.

**2. Retrieved context dominates.** 1,900 of 3,655 input tokens — **52%**. Retrieving 4 documents
instead of 8 halves the largest line item. Whether that hurts answer quality is an empirical question
(M7-L16), and it is the right question to ask before optimising anything else.

**3. Output is 5% of tokens but 21% of the bill** at illustrative rates of \$3/M input and \$15/M
output (§7.3), because output is priced several times higher. Asking for concise answers is a cost
lever, not just a UX one.

**Where the estimate will be wrong.** If the retrieved documents are JSON rather than prose, §7.3
measures the context ballooning from 1,900 to 4,743 tokens and the monthly input cost rising **+78%**.
Non-Latin content would be worse still. **Tokenize a real sample before you commit to a number.**

**A note on cost controls.** Model this before launch, set a budget alert — and understand that a
**billing alert notifies you; it does not stop spending.** If your provider offers a hard cap,
configure it explicitly. If it does not, you need your own rate limiting (M2-L14).

---

## 7. Practical activity

**File:** [`labs/m4/l03_tokenizers.py`](../../labs/m4/l03_tokenizers.py)

**Runs with or without network access.** It uses `tiktoken` if the encoding is available locally, and
otherwise falls back to a from-scratch BPE trained in the script. Both paths produce the full lesson.

```bash
source .venv/bin/activate
python labs/m4/l03_tokenizers.py
```

Trains BPE on §5.2's corpus showing every merge, measures chars-per-token across nine content types,
demonstrates the character-counting failure and its fix, shows whitespace sensitivity, proves
mid-byte truncation corrupts text, and reproduces §6's cost model.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, tiktoken 0.14.0 (`cl100k_base`), 2026-09-08.

```text

============================================================================
1. BPE TRAINING, EVERY MERGE  (corpus: 'low low low lower lowest')
============================================================================

  merge 1: 'l'+'o' -> 'lo'   (count 5)
    top pairs before : (lo)=5  (ow)=5  (w_)=3  (we)=2
    corpus after     : lo w _   lo w e r _   lo w e s t _

  merge 2: 'lo'+'w' -> 'low'   (count 5)
    top pairs before : (low)=5  (w_)=3  (we)=2  (er)=1
    corpus after     : low _   low e r _   low e s t _

  merge 3: 'low'+'_' -> 'low_'   (count 3)
    top pairs before : (low_)=3  (lowe)=2  (er)=1  (es)=1
    corpus after     : low e r _   low e s t _   low_

  merge 4: 'low'+'e' -> 'lowe'   (count 2)
    top pairs before : (lowe)=2  (er)=1  (es)=1  (r_)=1
    corpus after     : low_   lowe r _   lowe s t _

  merge 5: 'lowe'+'r' -> 'lower'   (count 1)
    top pairs before : (lower)=1  (lowes)=1  (r_)=1  (st)=1
    corpus after     : low_   lowe s t _   lower _

  merge 6: 'lowe'+'s' -> 'lowes'   (count 1)
    top pairs before : (lowes)=1  (lower_)=1  (st)=1  (t_)=1
    corpus after     : low_   lower _   lowes t _

  learned merge rules, IN ORDER:
    1. 'l' + 'o' -> 'lo'
    2. 'lo' + 'w' -> 'low'
    3. 'low' + '_' -> 'low_'
    4. 'low' + 'e' -> 'lowe'
    5. 'lowe' + 'r' -> 'lower'
    6. 'lowe' + 's' -> 'lowes'

  Encoding applies these rules IN THIS ORDER, repeatedly. They are an
  ordered list, not a set -- applying them greedily by length gives
  different, wrong tokens.

  encoding with the learned rules:
    low          -> ['low_']  (1 tokens)
    lower        -> ['lower', '_']  (2 tokens)
    lowest       -> ['lowes', 't', '_']  (3 tokens)
    slow         -> ['s', 'low_']  (2 tokens)
    flowering    -> ['f', 'lower', 'i', 'n', 'g', '_']  (6 tokens)

  'low' is now ONE token. 'slow' and 'flowering' were never in the
  corpus and still encode -- they decompose into pieces. Nothing is
  ever out-of-vocabulary; that is the point of subword tokenization.

============================================================================
2. CHARACTERS PER TOKEN, BY CONTENT TYPE   [tiktoken cl100k_base]
============================================================================
  content type             chars   tokens   chars/tok  vs English
  English prose              194       35        5.54       1.00x
  Technical English          178       32        5.56       1.00x
  Python code                219       44        4.98       1.11x
  JSON                       131       59        2.22       2.50x
  Numbers                     61       31        1.97       2.82x
  UUIDs                       73       41        1.78       3.11x
  Base64                      60       42        1.43       3.88x
  Hindi (Devanagari)          87       87        1.00       5.54x
  Japanese                    37       38        0.97       5.69x

  The 'vs English' column is the COST MULTIPLIER: how many times more
  tokens the same number of characters costs, relative to prose.

============================================================================
3. THE SAME MEANING, DIFFERENT LANGUAGES  (the equity problem)
============================================================================
  language      chars   tokens   vs English   the same sentence
  English          50       10        1.00x
  French           65       19        1.90x
  German           83       22        2.20x
  Hindi            62       65        6.50x
  Japanese         23       26        2.60x
  Thai             47       40        4.00x

  Hindi costs 6.5x English for the SAME sentence.
  Those users pay more per message, fit less history in the context
  window, and wait longer -- for identical content. If you serve
  multiple languages, measure this and set limits per language.

============================================================================
4. WHY THE MODEL MISCOUNTS LETTERS
============================================================================
  the word          : 'strawberry'  (10 characters)
  as the model sees : [496, 675, 15717]
  token count       : 3
  those IDs decode to: ['str', 'aw', 'berry']

  actual count of 'r': 3

  The model receives integers. There is no operation available to it
  that inspects the letters inside a token -- the embedding for that ID
  was learned from CONTEXT, not from spelling. Asking it to count
  letters is asking it to recall a fact about the string, not to
  perform a computation on the input.

  THE FIX -- spell it out first:
    's t r a w b e r r y'
    -> 10 tokens instead of 3
    decoded: ['s', ' t', ' r', ' a', ' w', ' b', ' e', ' r', ' r', ' y']
    Each letter is now its OWN token, so counting becomes a task the
    model can actually do over its input. It costs more tokens.
    (The better fix is a tool -- M8-L04.)

============================================================================
5. WHITESPACE IS PART OF THE TOKEN
============================================================================
  'the'      -> [1820]                
  ' the'     -> [279]                   DIFFERENT

  'Hello'    -> [9906]                
  ' Hello'   -> [22691]                 DIFFERENT

  'json'     -> [2285]                
  ' json'    -> [3024]                  DIFFERENT

  A prompt ending in a trailing space commits the model to a token that
  usually STARTS a word, which measurably changes what follows.
  Strip trailing whitespace from prompts.

============================================================================
6. TRUNCATION MUST HAPPEN ON TOKEN BOUNDARIES
============================================================================
  text  : Le client a été facturé deux fois — remboursement requis. 日本語のテキスト
  bytes : 87   characters: 66

  of 87 possible byte cut points, 21 produce invalid UTF-8:
    [13, 16, 25, 38, 39, 64, 65, 67, 68, 70, 71, 73, 74, 76, 77, 79, 80, 82, 83, 85, 86]
    that is 24% of all cut positions.

  bytes[:12]  ok     -> 'Le client a '
  bytes[:13]  BROKEN -> UnicodeDecodeError: unexpected end of data
  bytes[:14]  ok     -> 'Le client a é'
  bytes[:35]  ok     -> 'Le client a été facturé deux foi'
  bytes[:36]  ok     -> 'Le client a été facturé deux fois'
  bytes[:37]  ok     -> 'Le client a été facturé deux fois '

  lossy decoding, which is what a careless pipeline actually produces
  (errors='replace' silently substitutes U+FFFD and moves on):
    bytes[:13] -> 'Le client a �'
    bytes[:16] -> 'Le client a ét�'
    bytes[:25] -> 'Le client a été factur�'
    bytes[:38] -> 'Le client a été facturé deux fois �'

  Note the replacement character at the end. Nothing raised; the text
  is simply corrupted, and it reaches the model looking almost right.

  Now the same cut on TOKEN boundaries:
    first 4 tokens -> 'Le client a été'
    first 6 tokens -> 'Le client a été factur'
    first 8 tokens -> 'Le client a été facturé deux'

  Always valid text. Truncate on tokens, never on bytes or characters.

============================================================================
7. COST MODEL  (the lesson's support assistant)
============================================================================
  component                  tokens   % of input      per month
  system prompt                 800         22%     40,000,000
  retrieved context           1,900         52%     95,000,000
  conversation history          900         25%     45,000,000
  user message                   55          2%      2,750,000
  INPUT TOTAL                 3,655        100%    182,750,000
  output                        200           --     10,000,000

  ILLUSTRATIVE cost at $3/M input, $15/M output (NOT current pricing -- check your provider):
    input  $    548.25     79% of the bill   (95% of tokens)
    output $    150.00     21% of the bill   (   5% of tokens)
    total  $    698.25 per month

  Output is 5% of tokens but 21% of the bill.

  savings available:
    cache the system prompt      : up to $120.00/mo (40,000,000 tokens of unchanging text)
    retrieve 2 docs instead of 4 : up to $142.50/mo (test quality first -- M7-L16)

  NOW THE ESTIMATE ERROR. The 1,900-token context figure assumed
  English prose at ~4 chars/token. If the retrieved documents are JSON:
    measured JSON penalty        : 2.50x
    context tokens               : 1,900 -> 4,743
    input tokens per request     : 3,655 -> 6,498
    monthly input cost           : $548.25 -> $974.72  (+78%)

  A single wrong assumption about content type moved the bill by that
  much. Tokenize a REAL sample before committing to a budget.
  And note: a billing alert notifies you; it does not cap spending.

Done.
```

### 7.3 Reading the result

**Section 1 runs §5.2's merges and confirms them**, then shows the property that makes subword
tokenization work:

```
low          -> ['low_']                            1 token
lower        -> ['lower', '_']                      2 tokens
slow         -> ['s', 'low_']                       2 tokens
flowering    -> ['f', 'lower', 'i', 'n', 'g', '_']  6 tokens
```

`slow` and `flowering` **never appeared in the training corpus** and still encode — they decompose
into learned pieces. Nothing is ever out-of-vocabulary. That is the entire reason subword
tokenization replaced word-level vocabularies.

**Section 2 contradicted the draft of this lesson in two places**, and both corrections are now in
§5.3. English prose measured **5.54** chars/token, not the folklore 4.0 — the rule of thumb
**overestimates cost by 39%** for modern tokenizers. And technical English measured **5.56**, i.e.
*identical to ordinary prose*, against a drafted claim that jargon tokenizes worse. With a 100k
vocabulary, the jargon is in the vocabulary.

Python code at **4.98** is likewise far better than the commonly-repeated 2.5–3.5. What is genuinely
expensive is **structure and script**: JSON at **2.50×** prose, Devanagari at **5.54×**.

**Section 3 is the equity result, and it is larger than most people expect.** The same sentence:
English 10 tokens, French 19, German 22, Japanese 26, Thai 40, **Hindi 65 — 6.5×**.

A Hindi-speaking user of your product pays 6.5× per message, fits 6.5× less history in the same
context window, and waits proportionally longer. **A uniform character limit is not a neutral policy**
under these conditions.

**Section 4 shows the counting failure at the level of the actual integers.** `strawberry` becomes
**`[496, 675, 15717]`** — three numbers, decoding to `['str', 'aw', 'berry']`. There are three `r`s in
the word and **no operation available to the model that could count them**, because the letters are
not present in the input. The embedding for token 15717 was learned from the contexts `berry` appears
in, not from its spelling.

Spelling the word out first turns it into **10 tokens, one per letter** (`['s', ' t', ' r', ' a', ' w',
' b', ' e', ' r', ' r', ' y']`), at which point counting is a task the model can perform over its
input. It costs 3.3× the tokens. **A tool is the better fix (M8-L04)** — but understanding *why* the
workaround works is what tells you when a workaround is available at all.

**Section 5 confirms whitespace is part of the token**, with real IDs: `"the"` is **1820**, `" the"`
is **279**. Not variants of one token — two unrelated integers with independently learned embeddings.

**Section 6 is the truncation result, and the first run of this lab failed to demonstrate it** — the
cut points I had chosen all happened to land in the ASCII region. Corrected, the lab now scans every
possible cut:

> **21 of 87 byte positions — 24% — produce invalid UTF-8.**

And the failure is silent. With `errors="replace"`, `bytes[:25]` yields `'Le client a été factur\ufffd'`
— nothing raises, the text is simply corrupted, and it reaches the model looking almost right. Cutting
on token boundaries gives valid text every time.

**Section 7 costs §6's assistant and isolates the largest levers.** Input is 95% of tokens but 79% of
the bill; **output is 5% of tokens and 21% of the bill**, because it is priced 5× higher.

Then the estimate error. Changing one assumption — the retrieved documents are JSON, not prose —
applies the measured **2.50×** penalty:

| | Prose assumption | JSON reality |
|---|---|---|
| Context tokens | 1,900 | **4,743** |
| Input tokens/request | 3,655 | **6,498** |
| Monthly input cost | \$548.25 | **\$974.72 (+78%)** |

**One wrong assumption about content type, and the budget is wrong by 78%.** The prices used are
illustrative, not current — but the *ratio* is measured, and the ratio is what makes the point.
Tokenize a real sample before committing to a number, and remember that a billing alert notifies you
rather than capping the spend.

---

## 8. Common mistakes and troubleshooting

1. **Estimating tokens as `chars / 4` for non-prose.** Measure your real content.
2. **Using one model's tokenizer to budget for another.**
3. **Comparing per-token prices without comparing tokenizer efficiency.**
4. **Truncating on characters or bytes.** Truncate on token boundaries.
5. **Trusting the model to count letters or do arithmetic.** Give it a tool.
6. **Leaving a trailing space** in a prompt.
7. **Encoding user input with special tokens enabled.** A forged role marker is a real attack.
8. **Ignoring that the system prompt is billed on every request.**
9. **Assuming token counts are stable across model versions.**

| Symptom | Likely cause | Fix |
|---|---|---|
| Bill is 2× the estimate | Content is code/JSON/non-English | Tokenize a real sample |
| "Context length exceeded" on apparently short input | Content tokenizes badly | Measure; trim; chunk (M7-L06) |
| Model miscounts letters | It cannot see inside tokens | Use a tool, or spell the word out with spaces |
| Arithmetic wrong | Digits tokenize unpredictably | Use a calculator tool |
| Mojibake in truncated text | Cut mid-multi-byte-character | Truncate on token boundaries |
| Output changes with a trailing space | Different token sequence | Strip trailing whitespace |
| Non-English users hit limits sooner | Tokenizer is English-centric | Measure per language; adjust limits |
| Token counts differ from the provider's | Wrong tokenizer or version | Use the provider's own counter |

---

## 9. Security, privacy, reliability, cost

- **Security.** Never encode user-supplied text with special tokens enabled. A user who can emit a
  role-marker token can forge a conversation turn (M10-L06). Verify your library's default.
- **Cost.** Tokens are the unit of billing. The most common overrun is a system prompt or retrieved
  context that grows quietly over months. Log token counts per request and alert on the trend, not
  just the total.
- **Cost.** **Billing alerts notify; they do not cap.** Configure a hard limit where one exists, and
  otherwise implement your own throttle.
- **Reliability.** Tokenizers can change between model versions, shifting counts and costs. Pin
  versions where you can, and re-measure after any model upgrade.
- **Privacy.** Token counting is local and sends nothing anywhere. Prefer local counting over an API
  call that would transmit the content merely to size it.
- **Equity.** If you serve multiple languages, measure token cost per language. Applying one
  character limit uniformly disadvantages users of scripts that tokenize poorly.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why not one token per character? Give the specific cost reason.
2. Why not one token per word? Give two reasons.
3. Estimate tokens for: (a) 2,000 words of English prose; (b) a 2,000-character JSON payload; (c) a
   40-character UUID.
4. Explain to a colleague why the model miscounts the r's in "strawberry".
5. `"the"` versus `" the"` — why do these differ, and when does it matter?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab. Record chars-per-token for all nine content types and rank them.
2. Tokenize 500 words of your own writing. Compare with the `chars/4` estimate and report the error.
3. Implement BPE training and confirm it reproduces §5.2's merges in order.
4. Demonstrate the counting failure, then fix it by spelling the word with spaces. Explain why that
   works in terms of token boundaries.
5. Take §6's cost model and recompute it assuming the retrieved context is JSON. Report the change.

### Exercise 3 — Challenge (~45 min)

1. Implement a token-boundary-safe truncation function. Prove with a test that a naive byte-slice
   corrupts a multi-byte character and yours does not.
2. Measure chars-per-token for the same sentence in five languages. Compute the cost ratio relative
   to English and write two sentences on the product implications.
3. Build a token-budget allocator: given a limit and prioritised sections (system, context, history,
   user), fit as much as possible without splitting a section mid-sentence.
4. Compare two providers' effective cost per document: tokenize the same corpus with each tokenizer
   and multiply by each price. Show that the cheaper per-token price is not always cheaper.
5. Write a `count_tokens` cache keyed by content hash. Measure the speed-up on 10,000 repeated
   documents.
6. Implement byte-level fallback so any input — emoji, binary, invalid UTF-8 — encodes and decodes
   round-trip without loss.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l03).)*

**Q1.** Why do models use subword tokens rather than one token per character?

- A. Character models cannot represent words longer than the vocabulary.
- B. Subwords let the model see the spelling of each word directly.
- C. Sequences would be several times longer, and attention cost is quadratic.
- D. Characters cannot be embedded as vectors in a transformer.

**Q2.** In BPE training, what determines which pair is merged next?

- A. The pair that occurs most frequently in the current corpus state.
- B. The pair whose combined string is alphabetically first in the corpus.
- C. The pair that appears earliest in the first document processed.
- D. The pair with the shortest combined length in characters.

**Q3.** What is the usual rule of thumb for English prose?

- A. About 1 token per character of input text.
- B. About 1 token per word of input text.
- C. About 10 characters per token of input text.
- D. About 4 characters per token of input text.

**Q4.** Which content type tokenizes *least* efficiently?

- A. Text in a non-Latin script such as Hindi or Thai.
- B. Technical English with domain-specific terms.
- C. Ordinary conversational English prose.
- D. English text containing occasional proper nouns.

**Q5.** Why does a model miscount the letters in "strawberry"?

- A. The word is too rare to appear in its training data.
- B. It sees opaque integer IDs, not the letters inside them.
- C. Counting requires arithmetic, which models cannot perform.
- D. The sampling temperature introduces randomness in counting.

**Q6.** `"the"` and `" the"` are:

- A. The same token, since tokenizers normalise whitespace away.
- B. The same token, but with different positional encodings.
- C. Different tokens with different IDs, since whitespace is included.
- D. Invalid input, since tokens cannot begin with whitespace.

**Q7.** You must truncate a prompt to fit a context window. You should cut on:

- A. Character boundaries, counting from the start of the string.
- B. Byte boundaries, which is fastest and always safe.
- C. Word boundaries, which preserves readability for the model.
- D. Token boundaries, since anything finer can corrupt characters.

**Q8.** Provider A charges less per token than provider B. Which costs less per document?

- A. Unknown — tokenizer efficiency changes the token count.
- B. Provider B, since higher prices indicate better tokenization.
- C. Provider A, since the per-token price is definitionally lower.
- D. They are identical, since tokenizers are standardised.

**Q9.** Why must you never encode user input with special tokens enabled?

- A. It slows encoding down considerably at production volume.
- B. A user could emit a role marker and forge a conversation turn.
- C. Special tokens are billed at a higher rate than ordinary ones.
- D. The tokenizer will raise an exception on unrecognised markers.

**Q10.** In §6's cost model, which single item is the largest input cost?

- A. The system prompt, sent unchanged on every single request.
- B. The user's own message, which varies most between requests.
- C. The conversation history accumulated over the six prior turns.
- D. The retrieved context documents, at 52% of input tokens.

**Q11.** *(Written, rubric-graded.)* In under 120 words, explain to a product manager why the same
feature costs about **6.5×** more per message in Hindi than in English, and what options exist.

---

## 12. Revision notes

- **Subword tokens are the compromise**: word-level vocabularies are incomplete and enormous;
  character-level sequences are 4–5× longer, and **attention cost is quadratic in length**.
- **BPE**: start from bytes, repeatedly merge the most frequent adjacent pair, record the rules.
  **Encoding applies those rules in the order learned** — order is not optional.
- **The "≈ 4 chars/token" rule is conservative and dated.** Measured (`cl100k_base`): English prose
  **5.54**, technical English **5.56** (*the same* — jargon is in a 100k vocabulary), Python code
  **4.98**. What is actually expensive is **structure and script**: JSON **2.22** (2.50× prose),
  UUIDs 1.78, Base64 1.43, **Devanagari 1.00 (5.54×)**, Japanese 0.97.
- **The same sentence costs 6.5× more in Hindi than English.** A uniform character limit is not a
  neutral policy across languages.
- **The model cannot see inside a token.** Letter counting, reversal and arithmetic all fail for this
  reason. **Not stupidity — input representation.** Fix with a tool.
- **Whitespace is part of the token.** `" the"` ≠ `"the"`. Strip trailing spaces from prompts.
- **Truncate on token boundaries.** Cutting bytes or characters can produce mojibake.
- **Never encode user text with special tokens enabled** — forged role markers are a real attack.
- **Token counts do not transfer between models.** Nor do price comparisons without efficiency.
- **Estimate, then measure** on a real sample. Measured: changing one assumption — retrieved context
  is JSON, not prose — moved a monthly bill **+78%**.
- **Output is a small share of tokens and a large share of the bill.** Measured: 5% of tokens, 21% of
  cost at illustrative 5:1 pricing.
- **The system prompt is billed on every request.** Often the largest available saving (M5-L16).
- **Tokenizer equity is a real product concern.** Measure cost per language.

---

## 13. Completion checklist

- [ ] I can explain why subword tokenization exists, in cost terms.
- [ ] I traced BPE merges by hand on the `low lower lowest` corpus.
- [ ] I measured chars-per-token for at least five content types and can name the two most
      expensive.
- [ ] I saw that 24% of byte cut points corrupt this lesson's sample text.
- [ ] I can explain the "strawberry" failure mechanically, and name two fixes.
- [ ] I know why truncation must happen on token boundaries.
- [ ] I know why user input must never be encoded with special tokens enabled.
- [ ] I tokenized a real sample of my own content and compared to `chars/4`.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Sennrich et al. (2015), *Neural Machine Translation of Rare Words with Subword Units* (BPE).
  <https://arxiv.org/abs/1508.07909> `[UNVERIFIED]`
- OpenAI, `tiktoken`. <https://github.com/openai/tiktoken> `[UNVERIFIED]`
- Kudo & Richardson (2018), *SentencePiece*. <https://arxiv.org/abs/1808.06226> `[UNVERIFIED]`
- Petrov et al. (2023), *Language Model Tokenizers Introduce Unfairness Between Languages*.
  <https://arxiv.org/abs/2305.15425> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L04 — Embeddings and Contextual Representations](M4-L04-embeddings.md)

You can turn text into token IDs. Next: what happens to those integers — how each becomes a vector,
and how that vector changes depending on its neighbours.
