"""M4-L02 lab -- how each modality becomes a sequence of vectors.

Builds a synthetic image and patches it, demonstrates the quadratic patch
relationship, synthesises audio and converts it to a mel-style spectrogram,
costs video sampling strategies, and reproduces the document-pipeline
comparison so its assumptions can be varied.

No API key, no network, no image or audio libraries -- NumPy only.
Run:  python labs/m4/l02_modalities.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(2)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ------------------------------------------------------------- 1. images
rule("1. AN IMAGE BECOMES A SEQUENCE OF PATCHES")


def make_image(h=224, w=224):
    """A synthetic image: a gradient, a bright square, and a little noise."""
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.stack([
        xx / w,                                   # red   ramps left->right
        yy / h,                                   # green ramps top->bottom
        np.full((h, w), 0.35),                    # blue  constant
    ], axis=-1)
    img[40:90, 130:190] = [1.0, 1.0, 1.0]         # a white box
    return np.clip(img + RNG.normal(0, 0.02, img.shape), 0, 1)


def patchify(img, patch):
    h, w, c = img.shape
    if h % patch or w % patch:
        raise ValueError(f"{h}x{w} is not divisible by patch size {patch}")
    n_h, n_w = h // patch, w // patch
    out = (img.reshape(n_h, patch, n_w, patch, c)
              .transpose(0, 2, 1, 3, 4)
              .reshape(n_h * n_w, patch * patch * c))
    return out, (n_h, n_w)


img = make_image()
patches, grid = patchify(img, 14)
print(f"  image shape            : {img.shape}  ({img.size:,} numbers)")
print(f"  patch size             : 14 x 14")
print(f"  patch grid             : {grid[0]} x {grid[1]}")
print(f"  sequence length        : {len(patches)} patches")
print(f"  numbers per patch      : {patches.shape[1]}  (14 x 14 x 3)")

D_MODEL = 768
proj = RNG.normal(0, 0.02, size=(patches.shape[1], D_MODEL))
seq = patches @ proj
print(f"\n  after the projection layer: {seq.shape}")
print(f"  -> {seq.shape[0]} vectors of {seq.shape[1]} numbers each.")
print("  That is exactly the shape a text prompt of "
      f"{seq.shape[0]} tokens would produce.")
print("  From here the transformer cannot tell which one it received.")

print("\n  the first three patches, as vectors (first 6 dimensions):")
for i in range(3):
    row, col = divmod(i, grid[1])
    print(f"    patch {i:>3} (row {row}, col {col}): "
          f"{np.round(seq[i][:6], 3)}")

# A patch covering the white box should look different from a gradient patch.
box_patch = (40 // 14) * grid[1] + (130 // 14)
print(f"\n  patch {box_patch} covers the white box; patch 0 is background:")
print(f"    mean pixel value, patch {box_patch:>3}: {patches[box_patch].mean():.4f}")
print(f"    mean pixel value, patch   0: {patches[0].mean():.4f}")
print("  The projection preserves that difference -- which is what lets")
print("  attention (M4-L07) tell the two regions apart.")


rule("2. PATCH COUNT IS QUADRATIC  (the cost relationship that matters)")

print(f"  {'image':>12}{'patch':>8}{'patches':>10}{'vs 14px @224':>15}"
      f"{'~tokens':>10}")
base = None
for size, patch in ((224, 14), (224, 7), (448, 14), (448, 7),
                    (896, 14), (1024, 16), (2048, 16)):
    n = (size // patch) ** 2
    if base is None:
        base = n
    print(f"  {f'{size}x{size}':>12}{f'{patch}x{patch}':>8}{n:>10,}"
          f"{n / base:>14.1f}x{n:>10,}")

print("\n  patches = (width/patch) x (height/patch), so BOTH resizing the image")
print("  and shrinking the patch scale QUADRATICALLY:")
print(f"    224 -> 448 at the same patch size : {(448 // 14) ** 2 / (224 // 14) ** 2:.0f}x the patches")
print(f"    patch 14 -> 7 at the same size    : {(224 // 7) ** 2 / (224 // 14) ** 2:.0f}x the patches")
print("\n  A 2048x2048 scan is "
      f"{(2048 // 16) ** 2 / (224 // 14) ** 2:.0f}x the cost of a 224x224 thumbnail.")
print("  This is why 'just send the full-resolution scans' is expensive.")


# -------------------------------------------------------------- 3. audio
rule("3. AUDIO BECOMES A PICTURE OF SOUND")

SR = 16000
DURATION = 2.0
t = np.arange(int(SR * DURATION)) / SR
# A tone that steps up in pitch, plus a quiet hiss.
freqs = np.where(t < 0.7, 220.0, np.where(t < 1.4, 440.0, 880.0))
wave = 0.6 * np.sin(2 * np.pi * np.cumsum(freqs) / SR) + RNG.normal(0, 0.02, t.shape)

print(f"  duration        : {DURATION} s at {SR:,} Hz")
print(f"  raw samples     : {len(wave):,}   <- far too long to use as a sequence")

FRAME, HOP, N_MEL = 400, 160, 40          # 25 ms window, 10 ms hop
n_frames = 1 + (len(wave) - FRAME) // HOP
window = np.hanning(FRAME)

spec = np.empty((n_frames, FRAME // 2 + 1))
for i in range(n_frames):
    chunk = wave[i * HOP:i * HOP + FRAME] * window
    spec[i] = np.abs(np.fft.rfft(chunk))


def hz_to_mel(f):
    return 2595.0 * np.log10(1.0 + f / 700.0)


def mel_to_hz(m):
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


# Triangular mel filterbank -- spaced to match human hearing.
mel_edges = np.linspace(hz_to_mel(20), hz_to_mel(SR / 2), N_MEL + 2)
hz_edges = mel_to_hz(mel_edges)
bin_edges = np.floor((FRAME + 1) * hz_edges / SR).astype(int)
fb = np.zeros((N_MEL, FRAME // 2 + 1))
for m in range(N_MEL):
    lo, mid, hi = bin_edges[m], bin_edges[m + 1], bin_edges[m + 2]
    for k in range(lo, min(mid, fb.shape[1])):
        fb[m, k] = (k - lo) / max(mid - lo, 1)
    for k in range(mid, min(hi, fb.shape[1])):
        fb[m, k] = (hi - k) / max(hi - mid, 1)

mel = np.log(spec @ fb.T + 1e-8)

print(f"  window / hop    : {FRAME} samples (25 ms) / {HOP} samples (10 ms)")
print(f"  spectrogram     : {spec.shape}  (frames x fft bins)")
print(f"  mel spectrogram : {mel.shape}  (frames x mel bins)")
print(f"  compression     : {len(wave):,} samples -> {mel.shape[0]:,} frames "
      f"= {len(wave) / mel.shape[0]:.0f}x fewer sequence positions")

print("\n  the spectrogram, drawn (rows = frequency bands, columns = time):")
print("  The tone steps 220 Hz -> 440 Hz -> 880 Hz, so the bright band should")
print("  move UP the picture as time moves right.\n")
show = mel[::8, :24].T                    # subsample time, low bands only
lo, hi = show.min(), show.max()
levels = " .:-=+*#%@"
for r in range(show.shape[0] - 1, -1, -1):
    band_hz = mel_to_hz(mel_edges[r + 1])
    line = "".join(levels[min(int((v - lo) / (hi - lo) * (len(levels) - 1)),
                              len(levels) - 1)] for v in show[r])
    print(f"    {band_hz:>7.0f} Hz |{line}|")
print(f"    {'time ->':>10} |{'':<{show.shape[1]}}|")

peak_bands = [int(np.argmax(mel[i])) for i in (10, 90, 170)]
print(f"\n  peak mel band at t=0.1s, 0.9s, 1.7s: {peak_bands}")
print("  Rising, as the pitch rises. The model receives this as "
      f"{mel.shape[0]} vectors")
print(f"  of {mel.shape[1]} numbers -- the same shape as {mel.shape[0]} text tokens.")


# -------------------------------------------------------------- 4. video
rule("4. VIDEO IS A SAMPLING PROBLEM")

TOK_PER_FRAME = 750
print(f"  assuming {TOK_PER_FRAME} tokens per frame "
      f"(a ~1024x1024 image)\n")
print(f"  {'clip':>10}{'fps':>7}{'frames':>10}{'tokens':>14}"
      f"{'fits 200k ctx?':>16}")
for minutes in (1, 10, 60):
    for fps in (30, 5, 1):
        frames = int(minutes * 60 * fps)
        tokens = frames * TOK_PER_FRAME
        fits = "yes" if tokens <= 200_000 else "NO"
        print(f"  {f'{minutes} min':>10}{fps:>7}{frames:>10,}{tokens:>14,}"
              f"{fits:>16}")

print("\n  A 1-minute clip at 30 fps is 1.35M tokens -- over 6x a 200k context")
print("  window, for one minute of video. Every practical system samples.")
print("  Sampling at 1 fps makes a 10-minute video fit; that decision also")
print("  determines what the system is CAPABLE of noticing.")

# scene-change sampling on a synthetic clip
n_frames_v = 300
scene = np.repeat(RNG.normal(0, 1, size=(6, 64)), 50, axis=0)  # 6 scenes
scene += RNG.normal(0, 0.05, scene.shape)                      # within-scene drift
diffs = np.abs(np.diff(scene, axis=0)).mean(axis=1)
THRESH = 0.5
keep = 1 + np.where(diffs > THRESH)[0]
print(f"\n  scene-change sampling on a synthetic 300-frame clip:")
print(f"    uniform 1-in-1  : 300 frames -> {300 * TOK_PER_FRAME:,} tokens")
print(f"    scene changes   : {len(keep) + 1} frames -> "
      f"{(len(keep) + 1) * TOK_PER_FRAME:,} tokens "
      f"({300 / (len(keep) + 1):.0f}x fewer)")
print(f"    frames kept     : {[0] + keep.tolist()}")
print("    Keeps one frame per distinct scene. Misses anything that changes")
print("    WITHIN a scene -- which is the trade-off you are choosing.")


# ------------------------------------------------- 5. pipeline costing
rule("5. DOCUMENT PIPELINE: VISION vs OCR-THEN-TEXT")

N_DOCS = 10_000
VISION_IMAGE = 1500
PROMPT = 200
OUTPUT = 100
OCR_TEXT = 400

vision = (VISION_IMAGE + PROMPT + OUTPUT) * N_DOCS
ocr = (OCR_TEXT + PROMPT + OUTPUT) * N_DOCS

print(f"  {N_DOCS:,} invoices per month\n")
print(f"  {'option':<28}{'tokens/doc':>13}{'tokens/month':>16}{'vs vision':>12}")
print(f"  {'A: vision model':<28}{VISION_IMAGE + PROMPT + OUTPUT:>13,}"
      f"{vision:>16,}{'--':>12}")
print(f"  {'B: OCR -> text':<28}{OCR_TEXT + PROMPT + OUTPUT:>13,}"
      f"{ocr:>16,}{ocr / vision:>11.0%}")
print(f"\n  Option B uses {ocr / vision:.0%} of the tokens -- "
      f"a {1 - ocr / vision:.0%} reduction.")

print("\n  Hybrid: OCR first, fall back to vision when OCR confidence is low.")
print(f"  {'fallback rate':>15}{'tokens/month':>16}{'vs vision':>12}"
      f"{'vs pure OCR':>14}")
for rate in (0.0, 0.05, 0.10, 0.25, 0.50, 1.0):
    total = ocr * (1 - rate) + (ocr + vision / N_DOCS * N_DOCS * 0 + vision) * 0
    total = ocr * (1 - rate) + vision * rate
    print(f"  {rate:>14.0%}{total:>16,.0f}{total / vision:>11.0%}"
          f"{total / ocr:>13.2f}x")

breakeven = None
for rate in np.linspace(0, 1, 1001):
    if ocr * (1 - rate) + vision * rate >= vision:
        breakeven = float(rate)
        break
print(f"\n  The hybrid only stops saving money at a "
      f"{breakeven:.0%} fallback rate --")
print("  i.e. when OCR fails on every document, at which point it IS option A.")
print("  At a realistic 10% fallback it still uses "
      f"{(ocr * 0.9 + vision * 0.1) / vision:.0%} of pure-vision tokens,")
print("  AND every non-fallback document remains inspectable. That is the")
print("  argument for the hybrid: it is cheaper AND more debuggable.")

print("\n  CAUTION: every number above is an estimate from this lesson's rules")
print("  of thumb. Measure YOUR documents against YOUR provider's tokenizer")
print("  and current prices before committing a budget (M4-L03).")

print("\nDone.")
