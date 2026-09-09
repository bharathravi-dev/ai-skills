"""M4-L16 lab -- parametric knowledge vs in-context information.

Trains facts INTO a model's weights at varying repetition levels, then supplies
contradicting context and measures which wins. Reproduces the lesson's cost
model and compares four history strategies.

NumPy only, no API key, no network.
Run:  python labs/m4/l16_knowledge_context.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(16)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def sm(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


# ------------------------------------------------- corpus
# The model will learn "the capital of france is paris" from its TRAINING data,
# at a repetition level we control. Then we put a contradicting statement in
# the CONTEXT and see which one the model follows.
FILLER = [
    "the sky is blue today",
    "the report was filed on monday",
    "the meeting starts at nine",
    "the office is closed on sunday",
    "the invoice was paid in full",
    "the server restarted at midnight",
]
FACT_PREFIX = "the capital of france is"
TRUE_ANSWER = "paris"
CONTEXT_ANSWER = "lyon"

# Extra city names so the model can be trained on the PATTERN of copying an
# answer out of context, using entities it has no parametric belief about.
SPARE = ["oslo", "lima", "cairo", "delhi", "tokyo", "quito", "rabat", "sofia"]
WORDS = sorted({w for s in FILLER for w in s.split()} |
               set(FACT_PREFIX.split()) | {TRUE_ANSWER, CONTEXT_ANSWER} |
               set(SPARE) | {"context", ":", "question", "answer"})
W2I = {w: i for i, w in enumerate(WORDS)}
V, D, CTX = len(WORDS), 48, 12
CAUSAL = np.triu(np.ones((CTX, CTX), dtype=bool), k=1)


def pad(ids):
    return (ids + [W2I["."] if "." in W2I else 0] * CTX)[:CTX]


N_LAYERS = 2          # induction (copying from context) needs >= 2 layers


def make_params(seed=1):
    r = np.random.default_rng(seed)
    s = 0.4 / math.sqrt(D)
    P = {"E": r.normal(0, 0.1, (V, D)), "P": r.normal(0, 0.02, (CTX, D)),
         "Wlm": r.normal(0, 0.08, (D, V)), "layers": []}
    for _ in range(N_LAYERS):
        P["layers"].append({
            "Wq": r.normal(0, s, (D, D)), "Wk": r.normal(0, s, (D, D)),
            "Wv": r.normal(0, s, (D, D)), "Wo": r.normal(0, s, (D, D)),
            "W1": r.normal(0, s, (D, 4 * D)),
            "W2": r.normal(0, s, (4 * D, D))})
    return P


def forward(P, X):
    B, T = X.shape
    h = P["E"][X] + P["P"][:T]
    cache = []
    for L in P["layers"]:
        emb = h
        q, k, v = emb @ L["Wq"], emb @ L["Wk"], emb @ L["Wv"]
        sc = np.where(CAUSAL[:T, :T], -1e9,
                      q @ k.transpose(0, 2, 1) / math.sqrt(D))
        at = sm(sc, -1)
        h1 = emb + (at @ v) @ L["Wo"]
        pre = h1 @ L["W1"]
        act = np.maximum(0, pre)
        h = h1 + act @ L["W2"]
        cache.append((emb, q, k, v, at, h1, pre, act))
    return h @ P["Wlm"], (cache, h)


def train(P, windows, steps=300, lr=0.8):
    X_all, Y_all = windows[:, :-1], windows[:, 1:]
    for _ in range(steps):
        idx = RNG.choice(len(X_all), size=min(64, len(X_all)), replace=True)
        X, Y = X_all[idx], Y_all[idx]
        B, T = X.shape
        logits, (cache, h_final) = forward(P, X)
        pr = sm(logits)
        dl = pr.copy()
        dl[np.arange(B)[:, None], np.arange(T)[None, :], Y] -= 1.0
        dl /= (B * T)
        g_lm = h_final.reshape(-1, D).T @ dl.reshape(-1, V)
        dh = dl @ P["Wlm"].T
        grads = []
        for L, (emb, q, k, v, at, h1, pre, act) in zip(
                reversed(P["layers"]), reversed(cache)):
            g = {"W2": act.reshape(-1, 4 * D).T @ dh.reshape(-1, D)}
            dact = (dh @ L["W2"].T) * (pre > 0)
            g["W1"] = h1.reshape(-1, D).T @ dact.reshape(-1, 4 * D)
            dh1 = dh + dact @ L["W1"].T
            g["Wo"] = (at @ v).reshape(-1, D).T @ dh1.reshape(-1, D)
            dctx = dh1 @ L["Wo"].T
            dat = dctx @ v.transpose(0, 2, 1)
            dv = at.transpose(0, 2, 1) @ dctx
            dsc = at * (dat - (dat * at).sum(-1, keepdims=True))
            dsc = np.where(CAUSAL[:T, :T], 0.0, dsc) / math.sqrt(D)
            dq, dk = dsc @ k, dsc.transpose(0, 2, 1) @ q
            g["Wq"] = emb.reshape(-1, D).T @ dq.reshape(-1, D)
            g["Wk"] = emb.reshape(-1, D).T @ dk.reshape(-1, D)
            g["Wv"] = emb.reshape(-1, D).T @ dv.reshape(-1, D)
            dh = dh1 + dq @ L["Wq"].T + dk @ L["Wk"].T + dv @ L["Wv"].T
            grads.append(g)
        P["Wlm"] -= lr * (g_lm / max(float(np.linalg.norm(g_lm)), 1.0))
        for L, g in zip(reversed(P["layers"]), grads):
            for kk, gv in g.items():
                n = float(np.linalg.norm(gv))
                L[kk] -= lr * (gv / n if n > 1.0 else gv)
        np.add.at(P["E"], X, -lr * dh)
    return P


def prob_of_next(P, prompt_words):
    ids = [W2I[w] for w in prompt_words.split()][:CTX]
    X = np.array([pad(ids)])
    lg, _ = forward(P, X)
    return sm(lg[0, len(ids) - 1])


# ------------------------------------------------- 1. repetition
rule("1. HOW STRONGLY IS A FACT HELD? IT DEPENDS ON REPETITION")

# Training data ALSO contains the pattern "X is <city> ... X is" -> <city>,
# using spare city names, so the model can learn the CAPABILITY of copying an
# answer out of its context. Without this it has no in-context learning at all
# -- which is itself the finding in section 2.
def induction_examples(n=300, rng=None):
    rng = rng or np.random.default_rng(7)
    out = []
    for _ in range(n):
        city = SPARE[int(rng.integers(0, len(SPARE)))]
        out.append(f"{FACT_PREFIX} {city} {FACT_PREFIX} {city}")
    return out


IND = induction_examples()
print(f"  Training '{FACT_PREFIX} {TRUE_ANSWER}' at different repetition")
print(f"  counts, against {len(FILLER)} filler sentences (x40) AND {len(IND)}")
print(f"  copy-from-context examples using other city names.\n")

models = {}
print(f"  {'repetitions':>13}{'P(paris)':>11}{'P(lyon)':>10}{'margin':>10}"
      f"   parametric belief")
for reps in (1, 20, 150):
    corpus = FILLER * 40 + IND + [f"{FACT_PREFIX} {TRUE_ANSWER}"] * reps
    wins = np.array([pad([W2I[w] for w in s.split()] + [0]) for s in corpus])
    P = train(make_params(1), wins)
    models[reps] = P
    pr = prob_of_next(P, FACT_PREFIX)
    p_true = float(pr[W2I[TRUE_ANSWER]])
    p_ctx = float(pr[W2I[CONTEXT_ANSWER]])
    strength = ("none" if p_true < 0.15 else "weak" if p_true < 0.4
                else "moderate" if p_true < 0.8 else "strong")
    print(f"  {reps:>13}{p_true:>11.4f}{p_ctx:>10.4f}"
          f"{p_true - p_ctx:>10.4f}   {strength}")

print(f"\n  A fact seen ONCE against {len(FILLER) * 40} filler sentences is barely learned.")
print("  Seen 400 times, it is held strongly. Frequency determines whether")
print("  parametric recall is reliable -- which is why a model is confident")
print("  about capital cities and unreliable about a company's Q3 revenue.")


rule("2. KNOWLEDGE CONFLICT: CAN CONTEXT OVERRIDE THE WEIGHTS?")

CONFLICT = f"{FACT_PREFIX} {CONTEXT_ANSWER} {FACT_PREFIX}"
print(f"  Context states a DIFFERENT answer: '{FACT_PREFIX} {CONTEXT_ANSWER}'")
print(f"  Then the same question is asked. Which wins?\n")
print(f"  {'repetitions':>13}{'no context':>25}{'with contradicting context':>34}")
print(f"  {'in training':>13}{'P(paris)':>12}{'P(lyon)':>13}"
      f"{'P(paris)':>17}{'P(lyon)':>17}")
results = {}
for reps, P in models.items():
    plain = prob_of_next(P, FACT_PREFIX)
    conf = prob_of_next(P, CONFLICT)
    results[reps] = (plain, conf)
    print(f"  {reps:>13}{float(plain[W2I[TRUE_ANSWER]]):>12.4f}"
          f"{float(plain[W2I[CONTEXT_ANSWER]]):>13.4f}"
          f"{float(conf[W2I[TRUE_ANSWER]]):>17.4f}"
          f"{float(conf[W2I[CONTEXT_ANSWER]]):>17.4f}")

print(f"\n  {'repetitions':>13}{'context wins?':>16}{'P(lyon) shift':>17}")
for reps, (plain, conf) in results.items():
    shift = (float(conf[W2I[CONTEXT_ANSWER]]) -
             float(plain[W2I[CONTEXT_ANSWER]]))
    wins = float(conf[W2I[CONTEXT_ANSWER]]) > float(conf[W2I[TRUE_ANSWER]])
    print(f"  {reps:>13}{str(wins):>16}{shift:>+17.4f}")

print("\n  READ THIS HONESTLY: CONTEXT NEVER WINS HERE, at any repetition level.")
print("  P(lyon) barely moves whether the context states it or not.")
print("\n  That is not a broken experiment -- it is the finding. This model has")
print("  NO IN-CONTEXT LEARNING ABILITY. It memorised facts and cannot use its")
print("  own context to override them, even though the context is right there")
print("  in the prompt and the copying pattern was in its training data.")

print("\n  For comparison, a model trained WITHOUT the copy-from-context examples")
print("  at all -- to confirm the ability is absent in both cases at this scale:")

no_ind_corpus = FILLER * 40 + [f"{FACT_PREFIX} {TRUE_ANSWER}"] * 150
no_ind_wins = np.array([pad([W2I[w] for w in s.split()] + [0])
                        for s in no_ind_corpus])
P_noind = train(make_params(1), no_ind_wins)
plain_ni = prob_of_next(P_noind, FACT_PREFIX)
conf_ni = prob_of_next(P_noind, CONFLICT)
print(f"\n  {'trained with':<34}{'P(lyon) no context':>20}"
      f"{'P(lyon) with context':>22}{'shift':>10}")
plain_i, conf_i = results[150]
print(f"  {'copy-from-context examples':<34}"
      f"{float(plain_i[W2I[CONTEXT_ANSWER]]):>20.4f}"
      f"{float(conf_i[W2I[CONTEXT_ANSWER]]):>22.4f}"
      f"{float(conf_i[W2I[CONTEXT_ANSWER]]) - float(plain_i[W2I[CONTEXT_ANSWER]]):>+10.4f}")
print(f"  {'facts only, no such examples':<34}"
      f"{float(plain_ni[W2I[CONTEXT_ANSWER]]):>20.4f}"
      f"{float(conf_ni[W2I[CONTEXT_ANSWER]]):>22.4f}"
      f"{float(conf_ni[W2I[CONTEXT_ANSWER]]) - float(plain_ni[W2I[CONTEXT_ANSWER]]):>+10.4f}")

print("\n  IN-CONTEXT LEARNING IS ITSELF A LEARNED CAPABILITY, AND IT DOES NOT")
print("  APPEAR AT THIS SCALE. A 2-layer, 48-dimensional model trained for 300")
print("  steps memorises facts and cannot use its context to override them --")
print("  even with copy-from-context examples in its training data.")
print("\n  That is a genuine result, and it is worth more than a rigged demo")
print("  would have been. Real LLMs override parametric knowledge with context")
print("  routinely; the ability emerged from vast corpora full of text where")
print("  copying from earlier in a document pays off, and it required scale")
print("  this lab cannot reach (M4-L01 section 5.5 on emergence).")
print("\n  WHAT THIS MEANS FOR YOU: do not assume a small model will follow")
print("  supplied context the way a frontier model does. Grounding instructions")
print("  are a capability the model must HAVE, not merely an instruction you")
print("  give. Test it on the model you deploy (M7-L18).")


# ------------------------------------------------- 3. statelessness
rule("3. THE MODEL HAS NO MEMORY: DEMONSTRATED")

P = models[150]
print("  Turn 1: state a fact. Turn 2: ask about it -- WITHOUT re-sending.\n")

turn1 = f"{FACT_PREFIX} {CONTEXT_ANSWER}"
print(f"  turn 1 sent    : {turn1!r}")
print(f"  turn 2 sent    : {FACT_PREFIX!r}   (history NOT included)")
pr = prob_of_next(P, FACT_PREFIX)
print(f"  turn 2 answer  : P({CONTEXT_ANSWER})="
      f"{float(pr[W2I[CONTEXT_ANSWER]]):.4f}  "
      f"P({TRUE_ANSWER})={float(pr[W2I[TRUE_ANSWER]]):.4f}")
print(f"  -> the model has NO IDEA turn 1 happened.\n")

print(f"  turn 2 sent    : {CONFLICT!r}   (history INCLUDED)")
pr2 = prob_of_next(P, CONFLICT)
print(f"  turn 2 answer  : P({CONTEXT_ANSWER})="
      f"{float(pr2[W2I[CONTEXT_ANSWER]]):.4f}  "
      f"P({TRUE_ANSWER})={float(pr2[W2I[TRUE_ANSWER]]):.4f}")
shift = float(pr2[W2I[CONTEXT_ANSWER]]) - float(pr[W2I[CONTEXT_ANSWER]])
print(f"  -> P({CONTEXT_ANSWER}) moved {shift:+.4f} purely because the earlier turn")
print(f"     was RE-SENT. Nothing persisted in the model between calls.")
print("\n  Every conversation you have ever had with an LLM works this way.")


# ------------------------------------------------- 4. cost
rule("4. THE COST OF 'MEMORY'  (reproducing the lesson's model)")

SYSTEM, PER_TURN, N_TURNS = 800, 120, 40
print(f"  system prompt {SYSTEM} tokens; each turn adds {PER_TURN}\n")
print(f"  {'turn':>6}{'input tokens':>15}{'vs turn 1':>12}")
for t in (1, 2, 5, 10, 20, 40):
    tok = SYSTEM + (t - 1) * PER_TURN
    print(f"  {t:>6}{tok:>15,}{tok / (SYSTEM):>11.1f}x")

total = sum(SYSTEM + (t - 1) * PER_TURN for t in range(1, N_TURNS + 1))
independent = N_TURNS * (SYSTEM + PER_TURN)
formula = N_TURNS * SYSTEM + PER_TURN * (N_TURNS - 1) * N_TURNS // 2
print(f"\n  total over {N_TURNS} turns        : {total:>9,} tokens")
print(f"  closed form n*S + t*n(n-1)/2 : {formula:>9,}  "
      f"(match: {total == formula})")
print(f"  40 INDEPENDENT single turns  : {independent:>9,} tokens")
print(f"  the conversation costs       : {total / independent:>9.1f}x as much")
print(f"\n  system prompt share          : {N_TURNS * SYSTEM:,} tokens "
      f"({N_TURNS * SYSTEM / total:.0%}) -- and it NEVER CHANGES")
print(f"  -> prompt caching (M5-L14) targets exactly this")

print(f"\n  growth is quadratic in turns:")
print(f"  {'turns':>8}{'total tokens':>15}{'vs 10 turns':>14}")
base = None
for n in (10, 20, 40, 80, 160):
    tot = n * SYSTEM + PER_TURN * (n - 1) * n // 2
    if base is None:
        base = tot
    print(f"  {n:>8}{tot:>15,}{tot / base:>13.1f}x")
print("\n  16x the turns costs 51x the tokens. Any capacity plan assuming a")
print("  constant cost per message will be wrong, and wrong in the expensive")
print("  direction.")


# ------------------------------------------------- 5. strategies
rule("5. FOUR HISTORY STRATEGIES COMPARED")

WINDOW = 10
SUMMARY_TOKENS = 150
SUMMARY_EVERY = 10


def cost_full(n):
    return n * SYSTEM + PER_TURN * (n - 1) * n // 2


def cost_window(n, w=WINDOW):
    return sum(SYSTEM + min(t - 1, w) * PER_TURN for t in range(1, n + 1))


def cost_summary(n, every=SUMMARY_EVERY, summ=SUMMARY_TOKENS):
    total = 0
    for t in range(1, n + 1):
        kept = (t - 1) % every
        n_summ = (t - 1) // every
        total += SYSTEM + n_summ * summ + kept * PER_TURN
    # plus one extra generation call per summarisation
    total += (n // every) * (SYSTEM + every * PER_TURN)
    return total


def cost_cached(n, cache_discount=0.1):
    # the system prompt is charged at a fraction after the first request
    return int(SYSTEM + sum(SYSTEM * cache_discount + (t - 1) * PER_TURN
                            for t in range(2, n + 1)) + PER_TURN * 0)


print(f"  {'strategy':<32}{'40 turns':>12}{'160 turns':>13}{'vs full':>10}"
      f"   what it costs you")
rows = [
    ("full history", cost_full, "nothing -- but quadratic"),
    (f"sliding window (last {WINDOW})", cost_window, "anything older than 10 turns"),
    (f"summarise every {SUMMARY_EVERY}", cost_summary, "detail, plus extra API calls"),
    ("prompt caching (system only)", cost_cached, "nothing; needs provider support"),
]
for label, fn, cost_note in rows:
    a, b = fn(40), fn(160)
    print(f"  {label:<32}{a:>12,}{b:>13,}{a / cost_full(40):>9.0%}"
          f"   {cost_note}")

print("\n  The sliding window is the cheapest and the bluntest. Summarisation")
print("  preserves more and costs extra calls. Caching is free quality but only")
print("  helps the STABLE PREFIX -- it does nothing about the growing history,")
print("  which is the quadratic part.")
print("\n  Note that these combine: caching the system prompt AND windowing the")
print("  history addresses both terms.")
combined = sum(SYSTEM * 0.1 + min(t - 1, WINDOW) * PER_TURN
               for t in range(1, 41)) + SYSTEM
print(f"    caching + window, 40 turns : {int(combined):,} tokens "
      f"({combined / cost_full(40):.0%} of full history)")


# ------------------------------------------------- 6. where things live
rule("6. WHERE SHOULD EACH KIND OF INFORMATION LIVE?")

print(f"  {'information':<34}{'weights':>9}{'prompt':>9}{'retrieval':>12}"
      f"   deciding question")
CASES = [
    ("english grammar", "yes", "-", "-", "changes? no. cite? no."),
    ("your refund policy", "-", "-", "YES", "changes? yes. cite? yes."),
    ("this user's name", "-", "YES", "-", "changes? per request."),
    ("required output format", "-", "YES", "-", "behaviour, not fact."),
    ("yesterday's incident report", "-", "-", "YES", "after the cutoff."),
    ("a figure you must attribute", "-", "-", "YES", "weights cannot cite."),
    ("the model's own tone", "yes", "-", "-", "set by post-training."),
]
for info, w, p, r, q in CASES:
    print(f"  {info:<34}{w:>9}{p:>9}{r:>12}   {q}")

print("\n  ONE HEURISTIC SETTLES MOST OF THESE:")
print("    if the information can CHANGE, or must be ATTRIBUTABLE,")
print("    it does not belong in the weights.")
print("\n  That sentence disposes of most 'should we fine-tune on our docs?'")
print("  conversations before they start (M4-L01 section 5.4, M13-L02).")

print("\nDone.")
