"""M4-L05 lab -- next-token prediction, end to end.

Reproduces the lesson's hand-computed forward pass, then builds and trains a
complete miniature autoregressive language model so that every claim in the
lesson can be checked: the causal-mask collapse, teacher forcing vs free
running, loss and perplexity, and the prefill/decode asymmetry.

NumPy only, no API key, no network.
Run:  python labs/m4/l05_next_token.py
"""

from __future__ import annotations

import math
import time

import numpy as np

RNG = np.random.default_rng(5)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


# ------------------------------------------------- 1. the worked example
rule("1. THE WORKED EXAMPLE, VERIFIED  (6-token vocabulary, d_model 4)")

VOCAB = ["the", "cat", "sat", "dog", "ran", "."]
H_LAST = np.array([0.7, 0.4, -0.1, 0.3])
W_LM = np.array([
    [0.1,  0.2, -0.1,  0.0],     # the
    [0.3, -0.2,  0.1,  0.4],     # cat
    [0.8,  0.5,  0.2,  0.1],     # sat
    [0.2, -0.1,  0.3,  0.0],     # dog
    [0.6,  0.4, -0.2,  0.3],     # ran
    [-0.3, 0.1,  0.4, -0.2],     # .
])

logits = H_LAST @ W_LM.T
probs = softmax(logits)

print(f"  hidden state at the last position: {H_LAST}")
print(f"\n  logit('sat') = 0.7(0.8) + 0.4(0.5) + (-0.1)(0.2) + 0.3(0.1)")
print(f"               = {0.7 * 0.8:.2f} + {0.4 * 0.5:.2f} + "
      f"{-0.1 * 0.2:.2f} + {0.3 * 0.1:.2f} = {logits[2]:.4f}")

print(f"\n  {'token':<8}{'logit':>9}{'probability':>14}")
for tok, lo, p in zip(VOCAB, logits, probs):
    star = "  <-" if p > 0.2 else ""
    print(f"  {tok:<8}{lo:>9.4f}{p:>14.4f}{star}")
print(f"  {'sum':<8}{'':>9}{probs.sum():>14.4f}")

for true_tok in ("sat", "."):
    i = VOCAB.index(true_tok)
    loss = -math.log(probs[i])
    print(f"\n  if the true next token is {true_tok!r}:")
    print(f"    loss       = -ln({probs[i]:.4f}) = {loss:.4f} nats")
    print(f"    perplexity = exp({loss:.4f})     = {math.exp(loss):.2f}")

l_sat = -math.log(probs[VOCAB.index("sat")])
l_dot = -math.log(probs[VOCAB.index(".")])
print(f"\n  The wrong-but-plausible token costs {l_dot / l_sat - 1:.0%} more loss.")
print("  Cross-entropy punishes confident wrongness (M3-L05).")


# ------------------------------------------------- 2. a real tiny LM
rule("2. A COMPLETE MINIATURE LANGUAGE MODEL")

# A synthetic language with real structure: fixed templates, so the model has
# something learnable and we know what the right answer looks like.
TEMPLATES = [
    "the cat sat on the mat .",
    "the dog ran to the park .",
    "the cat ran to the mat .",
    "the dog sat on the park .",
    "a bird flew over the tree .",
    "a bird sat on the tree .",
]
CORPUS = " ".join(TEMPLATES * 400).split()
WORDS = sorted(set(CORPUS))
W2I = {w: i for i, w in enumerate(WORDS)}
V = len(WORDS)
D = 24
CTX = 6

print(f"  vocabulary : {V} tokens -> {WORDS}")
print(f"  corpus     : {len(CORPUS):,} tokens")
print(f"  d_model    : {D},  context: {CTX}")
print(f"\n  loss at initialisation should be about ln(V) = ln({V}) = "
      f"{math.log(V):.4f}")
print("  (a uniform distribution over the vocabulary -- no knowledge at all)")

ids = np.array([W2I[w] for w in CORPUS])
windows = np.array([ids[i:i + CTX + 1] for i in range(len(ids) - CTX)])
X_all, Y_all = windows[:, :-1], windows[:, 1:]      # targets = inputs shifted
print(f"  training windows: {len(windows):,}")
print(f"\n  first window, showing the shift:")
print(f"    input : {[WORDS[i] for i in X_all[0]]}")
print(f"    target: {[WORDS[i] for i in Y_all[0]]}")
print("    Target at position i is the input at position i+1. No labels exist;")
print("    the text IS the supervision (M1-L07).")


def make_params(seed):
    r = np.random.default_rng(seed)
    return {
        "E": r.normal(0, 0.08, size=(V, D)),
        "P": r.normal(0, 0.02, size=(CTX, D)),      # positional (M4-L09)
        "Wq": r.normal(0, 0.15, size=(D, D)),
        "Wk": r.normal(0, 0.15, size=(D, D)),
        "Wv": r.normal(0, 0.15, size=(D, D)),
        "Wo": r.normal(0, 0.15, size=(D, D)),
        "W1": r.normal(0, 0.15, size=(D, 4 * D)),
        "W2": r.normal(0, 0.15, size=(4 * D, D)),
        "Wlm": r.normal(0, 0.08, size=(D, V)),
    }


CAUSAL = np.triu(np.ones((CTX, CTX), dtype=bool), k=1)      # True = block


def forward(p, X, causal=True):
    """One attention block plus an MLP, then the LM head. Returns logits."""
    B, T = X.shape
    h = p["E"][X] + p["P"][:T]                       # (B, T, D)
    q, k, v = h @ p["Wq"], h @ p["Wk"], h @ p["Wv"]
    scores = q @ k.transpose(0, 2, 1) / math.sqrt(D)  # (B, T, T)
    if causal:
        scores = np.where(CAUSAL[:T, :T], -1e9, scores)
    attn = softmax(scores, axis=-1)
    h = h + (attn @ v) @ p["Wo"]                     # residual
    h = h + np.maximum(0, h @ p["W1"]) @ p["W2"]     # residual
    return h @ p["Wlm"], attn


def loss_of(logits, Y):
    B, T, _ = logits.shape
    pr = softmax(logits)
    picked = pr[np.arange(B)[:, None], np.arange(T)[None, :], Y]
    return float(-np.log(np.clip(picked, 1e-12, None)).mean())


def train(causal=True, steps=1200, batch=96, lr=0.35, seed=1):
    """Train with FULL backpropagation, including the attention weights.

    Training attention is not optional for this lab: if Wq/Wk/Wv/Wo stay at
    their random initialisation, the model cannot learn to exploit an unmasked
    future, and section 3's demonstration silently shows nothing. That was the
    first version of this script, and the measured difference was 5%.
    """
    p = make_params(seed)
    history = []
    for step in range(steps + 1):
        idx = RNG.choice(len(X_all), size=batch, replace=False)
        X, Y = X_all[idx], Y_all[idx]
        B, T = X.shape

        # ---- forward, keeping every intermediate ----
        emb = p["E"][X] + p["P"][:T]                          # (B,T,D)
        q, k, v = emb @ p["Wq"], emb @ p["Wk"], emb @ p["Wv"]
        scores = q @ k.transpose(0, 2, 1) / math.sqrt(D)
        if causal:
            scores = np.where(CAUSAL[:T, :T], -1e9, scores)
        attn = softmax(scores, axis=-1)
        ctx = attn @ v
        h1 = emb + ctx @ p["Wo"]
        pre = h1 @ p["W1"]
        act = np.maximum(0, pre)
        h2 = h1 + act @ p["W2"]
        logits = h2 @ p["Wlm"]

        pr = softmax(logits)
        picked = pr[np.arange(B)[:, None], np.arange(T)[None, :], Y]
        history.append(float(-np.log(np.clip(picked, 1e-12, None)).mean()))
        if step == steps:
            break

        # ---- backward ----
        d_logits = pr.copy()
        d_logits[np.arange(B)[:, None], np.arange(T)[None, :], Y] -= 1.0
        d_logits /= (B * T)

        g = {"Wlm": np.einsum("btd,btv->dv", h2, d_logits)}
        dh2 = d_logits @ p["Wlm"].T

        g["W2"] = np.einsum("btk,btd->kd", act, dh2)
        dact = (dh2 @ p["W2"].T) * (pre > 0)
        g["W1"] = np.einsum("btd,btk->dk", h1, dact)
        dh1 = dh2 + dact @ p["W1"].T                          # residual

        g["Wo"] = np.einsum("btd,bte->de", ctx, dh1)
        dctx = dh1 @ p["Wo"].T
        dattn = dctx @ v.transpose(0, 2, 1)
        dv = attn.transpose(0, 2, 1) @ dctx

        # softmax backward, row-wise
        dscores = attn * (dattn - (dattn * attn).sum(axis=-1, keepdims=True))
        if causal:
            dscores = np.where(CAUSAL[:T, :T], 0.0, dscores)
        dscores /= math.sqrt(D)
        dq = dscores @ k
        dk = dscores.transpose(0, 2, 1) @ q

        g["Wq"] = np.einsum("btd,bte->de", emb, dq)
        g["Wk"] = np.einsum("btd,bte->de", emb, dk)
        g["Wv"] = np.einsum("btd,bte->de", emb, dv)
        demb = (dh1 + dq @ p["Wq"].T + dk @ p["Wk"].T + dv @ p["Wv"].T)

        # ---- update ----
        for key, grad in g.items():
            norm = float(np.linalg.norm(grad))
            if norm > 1.0:                       # clip (M3-L12)
                grad = grad / norm
            p[key] -= lr * grad
        np.add.at(p["E"], X, -lr * demb)
        p["P"][:T] -= lr * demb.sum(axis=0)
    return p, history


print("\n  training WITH the causal mask (the correct set-up):")
params, hist = train(causal=True)
print(f"    {'step':>8}{'loss':>10}{'perplexity':>13}")
for step in (0, 100, 300, 600, 1200):
    lo = hist[min(step, len(hist) - 1)]
    print(f"    {step:>8}{lo:>10.4f}{math.exp(lo):>13.2f}")
print(f"\n    initial loss {hist[0]:.4f} vs ln(V) = {math.log(V):.4f}  "
      f"(difference {abs(hist[0] - math.log(V)):.4f})")
print("    Starting at ln(V) confirms the model begins with no knowledge.")


# ------------------------------------------------- 3. the causal mask
rule("3. REMOVING THE CAUSAL MASK  (the loss collapse)")

_, hist_nomask = train(causal=False)
print(f"  {'step':>8}{'WITH mask':>13}{'WITHOUT mask':>15}{'ratio':>10}")
for step in (0, 100, 300, 600, 1200):
    a = hist[min(step, len(hist) - 1)]
    b = hist_nomask[min(step, len(hist_nomask) - 1)]
    print(f"  {step:>8}{a:>13.4f}{b:>15.4f}{b / a:>10.2f}x")

print(f"\n  final loss   with mask: {hist[-1]:.4f}   (perplexity "
      f"{math.exp(hist[-1]):.2f})")
print(f"  final loss without mask: {hist_nomask[-1]:.4f}   (perplexity "
      f"{math.exp(hist_nomask[-1]):.2f})")
print("\n  The unmasked model reaches a LOWER loss -- and it is worthless.")
print("  Position i can attend to position i+1, which holds the answer, so it")
print("  learns to copy rather than to predict. The only symptom is a")
print("  suspiciously good loss curve.")

# Prove the mask actually blocks the future.
X_probe = X_all[:1].copy()
logits_a, _ = forward(params, X_probe, causal=True)
X_alt = X_probe.copy()
X_alt[0, -1] = (X_alt[0, -1] + 1) % V          # change the LAST token only
logits_b, _ = forward(params, X_alt, causal=True)
same_prefix = np.allclose(logits_a[0, :-1], logits_b[0, :-1])
print(f"\n  PROOF the mask works: change only the last input token, then check")
print(f"  whether earlier positions' logits moved.")
print(f"    earlier positions identical (masked)  : {same_prefix}")
la, _ = forward(params, X_probe, causal=False)
lb, _ = forward(params, X_alt, causal=False)
print(f"    earlier positions identical (unmasked): "
      f"{np.allclose(la[0, :-1], lb[0, :-1])}")
print("  With the mask, the past cannot see the future. Without it, it can.")


# ------------------------------------------------- 4. generation
rule("4. GENERATION: EVERY POSITION PREDICTS, BUT WE KEEP ONE")

prompt = ["the", "cat"]
X = np.array([[W2I[w] for w in prompt]])
logits_all, _ = forward(params, X, causal=True)
pr_all = softmax(logits_all)[0]

print(f"  prompt: {prompt}   -> the model produced {pr_all.shape[0]} "
      f"distributions, one per position\n")
for pos in range(len(prompt)):
    top = np.argsort(-pr_all[pos])[:3]
    seen = " ".join(prompt[:pos + 1])
    preds = ", ".join(f"{WORDS[t]} ({pr_all[pos, t]:.3f})" for t in top)
    keep = "  <- KEPT" if pos == len(prompt) - 1 else "  (discarded)"
    print(f"    after {seen!r:<16} -> {preds}{keep}")

print("\n  In generation we discard all but the last. In TRAINING every one of")
print("  them is a learning signal, which is why training is so much more")
print("  efficient per forward pass.")


def generate(params, prompt_words, n, temperature=0.0, seed=0):
    r = np.random.default_rng(seed)
    out = [W2I[w] for w in prompt_words]
    for _ in range(n):
        window = np.array([out[-CTX:]])
        lg, _ = forward(params, window, causal=True)
        last = lg[0, -1]
        if temperature <= 0:
            nxt = int(np.argmax(last))
        else:
            p = softmax(last / temperature)
            nxt = int(r.choice(V, p=p))
        out.append(nxt)
    return " ".join(WORDS[i] for i in out)


print("\n  greedy generation from 'the cat':")
print(f"    {generate(params, ['the', 'cat'], 8)!r}")
print("\n  sampled at temperature 0.8, three runs:")
for s in range(3):
    print(f"    {generate(params, ['the', 'cat'], 8, 0.8, seed=s)!r}")


# ------------------------------------------------- 5. teacher forcing
rule("5. TEACHER FORCING vs FREE RUNNING  (exposure bias)")

seq = "the cat sat on the mat .".split()
seq_ids = [W2I[w] for w in seq]

# Teacher forced: always condition on the TRUE previous tokens.
tf_losses = []
for t in range(1, len(seq_ids)):
    ctx = np.array([seq_ids[max(0, t - CTX):t]])
    lg, _ = forward(params, ctx, causal=True)
    p = softmax(lg[0, -1])
    tf_losses.append(-math.log(max(p[seq_ids[t]], 1e-12)))

# Free running: condition on the model's OWN previous outputs.
fr_losses = []
generated = [seq_ids[0]]
for t in range(1, len(seq_ids)):
    ctx = np.array([generated[-CTX:]])
    lg, _ = forward(params, ctx, causal=True)
    p = softmax(lg[0, -1])
    fr_losses.append(-math.log(max(p[seq_ids[t]], 1e-12)))
    generated.append(int(np.argmax(lg[0, -1])))

print(f"  {'position':<10}{'true token':<12}{'teacher-forced':>16}"
      f"{'free-running':>15}{'model said':>14}")
for i, (tf, fr) in enumerate(zip(tf_losses, fr_losses), start=1):
    print(f"  {i:<10}{seq[i]:<12}{tf:>16.4f}{fr:>15.4f}"
          f"{WORDS[generated[i]]:>14}")
print(f"\n  mean loss  teacher-forced: {np.mean(tf_losses):.4f}")
print(f"  mean loss  free-running   : {np.mean(fr_losses):.4f}")
print(f"  ratio                     : "
      f"{np.mean(fr_losses) / np.mean(tf_losses):.2f}x")
print("\n  Training only ever measures the teacher-forced number. Generation")
print("  always experiences the free-running one. That gap is exposure bias,")
print("  and it is why an early mistake propagates through a long response.")


# ------------------------------------------------- 6. prefill vs decode
rule("6. PREFILL vs DECODE  (the asymmetry that governs latency and price)")

big = make_params(9)
PROMPT_LEN = CTX


def time_prefill(reps=200):
    X = RNG.integers(0, V, size=(1, CTX))
    t0 = time.perf_counter()
    for _ in range(reps):
        forward(big, X, causal=True)
    return (time.perf_counter() - t0) / reps


def time_decode(n_tokens, reps=20):
    t0 = time.perf_counter()
    for _ in range(reps):
        out = list(RNG.integers(0, V, size=CTX))
        for _ in range(n_tokens):
            lg, _ = forward(big, np.array([out[-CTX:]]), causal=True)
            out.append(int(np.argmax(lg[0, -1])))
    return (time.perf_counter() - t0) / reps


t_pre = time_prefill()
print(f"  one prefill pass over {CTX} positions : {t_pre * 1000:.3f} ms")
print(f"\n  {'tokens generated':>18}{'total time':>13}{'per token':>12}"
      f"{'vs 1 prefill':>15}")
for n in (1, 10, 50, 100):
    t = time_decode(n)
    print(f"  {n:>18}{t * 1000:>12.2f}ms{t / n * 1000:>11.3f}ms"
          f"{t / t_pre:>14.1f}x")

print("\n  Generating N tokens costs N sequential forward passes. The prompt,")
print("  however long, costs ONE. That is why:")
print("    * output tokens are priced higher than input tokens,")
print("    * latency scales with output length, not prompt length,")
print("    * streaming exists (the user sees token 1 immediately),")
print("    * and no amount of parallel hardware makes a single generation")
print("      faster -- the dependency is inherent, not an implementation")
print("      limitation.")

print(f"\n  Scaled to a realistic request -- 1,000-token prompt, 500 output")
print(f"  tokens, at 20 ms per decode step:")
print(f"    prefill : 1 pass          ~ 0.02 s")
print(f"    decode  : 500 passes      ~ {500 * 0.02:.1f} s")
print(f"    -> {500 * 0.02 / 0.02:.0f}x the prompt's cost, from 500 tokens of output.")

print("\nDone.")
