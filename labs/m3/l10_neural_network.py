"""M3-L10: layers, activations, the collapse proof, and parameter memory.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l10_neural_network.py
"""

from __future__ import annotations

import numpy as np

LINE = "-" * 74

W1 = np.array([[0.5, -0.3],
               [0.8, 0.6]])
B1 = np.array([0.1, 0.2])
W2 = np.array([[1.2], [-0.7]])
B2 = np.array([-0.4])


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))


def relu(z):
    return np.maximum(0, z)


def forward_pass() -> None:
    section("1. THE SECTION 6 FORWARD PASS, VERIFIED")
    for x in (np.array([1.0, 2.0]), np.array([-2.0, 0.5])):
        z1 = x @ W1 + B1
        h1 = relu(z1)
        z2 = float((h1 @ W2 + B2)[0])
        out = float(sigmoid(z2))
        zeroed = [i for i, v in enumerate(z1) if v <= 0]

        print(f"  input x = {x.tolist()}")
        print(f"    hidden pre-activation z1 = {np.array2string(z1, precision=4)}")
        print(f"    after ReLU            h1 = {np.array2string(h1, precision=4)}"
              + (f"   <- unit {zeroed[0] + 1} ZEROED" if zeroed else ""))
        print(f"    output pre-activation z2 = {z2:.4f}")
        print(f"    sigmoid                  = {out:.4f}")
        print()

    print("  For the second input, hidden unit 1 contributed NOTHING - its")
    print("  weight of 1.2 was multiplied by zero. The network used a")
    print("  DIFFERENT SUBSET of its units for the two inputs.")
    print()
    print("  That is the non-linearity working. A linear model applies one")
    print("  fixed formula to every input; a ReLU network selects which units")
    print("  participate, per input.")

    print()
    print("  Finding an input that zeroes BOTH units:")
    for candidate in (np.array([-5.0, -5.0]), np.array([-1.0, -1.0])):
        z1 = candidate @ W1 + B1
        h1 = relu(z1)
        out = float(sigmoid((h1 @ W2 + B2)[0]))
        both = "BOTH zeroed" if np.all(h1 == 0) else "not both"
        print(f"    x = {str(candidate.tolist()):<16} z1 = "
              f"{np.array2string(z1, precision=3):<20} {both}, output {out:.4f}")
    print(f"  When both are zeroed the output is always sigmoid(b2) = "
          f"{float(sigmoid(B2[0])):.4f},")
    print("  regardless of the input. The network has nothing left to say.")


def collapse_proof() -> None:
    section("2. THE COLLAPSE PROOF - stacked linear layers ARE one layer")
    rng = np.random.default_rng(42)
    dims = [6, 32, 24, 16, 8, 3]
    weights = [rng.normal(scale=0.5, size=(dims[i], dims[i + 1]))
               for i in range(len(dims) - 1)]
    biases = [rng.normal(scale=0.1, size=dims[i + 1]) for i in range(len(dims) - 1)]
    x = rng.normal(size=(5, dims[0]))

    print(f"  A {len(weights)}-layer network: {' -> '.join(map(str, dims))}")
    print(f"  Total parameters: "
          f"{sum(w.size for w in weights) + sum(b.size for b in biases):,}")
    print()

    # Forward pass with NO activations.
    h = x
    for w, b in zip(weights, biases):
        h = h @ w + b
    deep_output = h

    # Collapse the whole stack into a single equivalent layer.
    combined_w = weights[0]
    combined_b = biases[0]
    for w, b in zip(weights[1:], biases[1:]):
        combined_b = combined_b @ w + b
        combined_w = combined_w @ w
    single_output = x @ combined_w + combined_b

    print(f"  5-layer output (first row): "
          f"{np.array2string(deep_output[0], precision=6)}")
    print(f"  1-layer equivalent        : "
          f"{np.array2string(single_output[0], precision=6)}")
    print(f"  identical? {np.allclose(deep_output, single_output)}   "
          f"max difference {np.abs(deep_output - single_output).max():.2e}")
    print()
    print(f"  The collapsed layer is a single {combined_w.shape} matrix plus a")
    print(f"  {combined_b.shape} bias - {combined_w.size + combined_b.size} numbers "
          f"replacing "
          f"{sum(w.size for w in weights) + sum(b.size for b in biases):,}.")
    print()
    print("  NOW ADD ReLU between the layers:")
    h = x
    for i, (w, b) in enumerate(zip(weights, biases)):
        h = h @ w + b
        if i < len(weights) - 1:
            h = relu(h)
    print(f"  with ReLU (first row)     : {np.array2string(h[0], precision=6)}")
    print(f"  same as the linear version? {np.allclose(h, single_output)}")
    print()
    print("  Without activations the depth is DECORATION. It fails silently:")
    print("  no error, no warning, just a very expensive logistic regression.")


def activations() -> None:
    section("3. ACTIVATIONS AND THEIR DERIVATIVES")
    z = np.array([-6.0, -2.0, -0.5, 0.0, 0.5, 2.0, 6.0])
    s = sigmoid(z)
    print(f"  {'z':>7}{'ReLU':>9}{'ReLU_grad':>12}{'sigmoid':>11}"
          f"{'sigmoid_grad':>14}{'tanh':>10}")
    for i, zi in enumerate(z):
        print(f"  {zi:>7.1f}{relu(zi):>9.2f}{(1.0 if zi > 0 else 0.0):>12.2f}"
              f"{s[i]:>11.4f}{s[i] * (1 - s[i]):>14.4f}{np.tanh(zi):>10.4f}")
    print()
    print("  THE DECISIVE COLUMN is ReLU_grad vs sigmoid_grad.")
    print()
    depth_rows = []
    for n in (1, 5, 10, 20, 50):
        depth_rows.append((n, 1.0 ** n, 0.25 ** n))
    print(f"  {'layers':>8}{'ReLU (grad=1)':>18}{'sigmoid (grad<=0.25)':>24}")
    for n, r, sg in depth_rows:
        print(f"  {n:>8}{r:>18.1f}{sg:>24.2e}")
    print()
    print("  Sigmoid's BEST case is 0.25 per layer. Ten layers gives 1e-6 -")
    print("  the gradient reaching the first layer is effectively zero and it")
    print("  stops learning. ReLU's derivative is exactly 1 for positive")
    print("  inputs, so the product does not shrink at all.")
    print()
    print("  That single property is what made networks deeper than a few")
    print("  layers trainable (M3-L06).")


def xor_demo() -> None:
    section("4. WHAT A HIDDEN LAYER BUYS: DATA A LINE CANNOT SPLIT")
    rng = np.random.default_rng(42)
    n = 800
    x = rng.uniform(-1, 1, size=(n, 2))
    # XOR-like: positive when the two coordinates have the SAME sign.
    y = ((x[:, 0] > 0) == (x[:, 1] > 0)).astype(float)

    # Logistic regression (no hidden layer).
    w, b = np.zeros(2), 0.0
    for _ in range(3000):
        p = sigmoid(x @ w + b)
        g = p - y
        w -= 0.5 * (x.T @ g) / n
        b -= 0.5 * g.mean()
    logistic_acc = float(((sigmoid(x @ w + b) > 0.5) == y).mean())

    # A network with one hidden layer, He initialisation.
    hidden = 8
    w1 = rng.normal(scale=np.sqrt(2 / 2), size=(2, hidden))
    b1 = np.zeros(hidden)
    w2 = rng.normal(scale=np.sqrt(2 / hidden), size=(hidden, 1))
    b2 = np.zeros(1)
    lr = 0.5
    for _ in range(6000):
        z1 = x @ w1 + b1
        h1 = relu(z1)
        p = sigmoid((h1 @ w2 + b2).ravel())
        dz2 = (p - y).reshape(-1, 1) / n
        gw2 = h1.T @ dz2
        gb2 = dz2.sum(axis=0)
        dh1 = dz2 @ w2.T
        dz1 = dh1 * (z1 > 0)
        gw1 = x.T @ dz1
        gb1 = dz1.sum(axis=0)
        w2 -= lr * gw2
        b2 -= lr * gb2
        w1 -= lr * gw1
        b1 -= lr * gb1
    z1 = x @ w1 + b1
    net_acc = float(((sigmoid((relu(z1) @ w2 + b2).ravel()) > 0.5) == y).mean())

    print(f"  {n} points. Class = 1 when both coordinates share a sign")
    print("  (an XOR pattern: two opposite quadrants against two others).")
    print()
    print(f"  logistic regression (no hidden layer) : accuracy {logistic_acc:.3f}")
    print(f"  network with {hidden} hidden ReLU units       : accuracy {net_acc:.3f}")
    print()
    print("  Logistic regression scores near chance because NO straight line")
    print("  separates opposite quadrants. Its decision boundary is a line,")
    print("  and the problem is not linearly separable (M3-L09).")
    print()
    print("  The hidden layer builds intermediate features that ARE linearly")
    print("  separable in the space it constructs. That is what depth buys,")
    print("  and it is impossible without the non-linearity.")


def failure_modes() -> None:
    section("5. TWO FAILURES: ZERO INIT AND DEAD ReLUs")
    rng = np.random.default_rng(0)
    n, hidden = 300, 4
    x = rng.normal(size=(n, 3))
    y = (x[:, 0] + x[:, 1] > 0).astype(float)

    print("  A) ALL-ZERO INITIALISATION")
    w1 = np.zeros((3, hidden))
    b1 = np.zeros(hidden)
    w2 = np.zeros((hidden, 1))
    b2 = np.zeros(1)
    for _ in range(500):
        z1 = x @ w1 + b1
        h1 = relu(z1)
        p = sigmoid((h1 @ w2 + b2).ravel())
        dz2 = (p - y).reshape(-1, 1) / n
        dh1 = dz2 @ w2.T
        dz1 = dh1 * (z1 > 0)
        w2 -= 0.5 * (h1.T @ dz2)
        b2 -= 0.5 * dz2.sum(axis=0)
        w1 -= 0.5 * (x.T @ dz1)
        b1 -= 0.5 * dz1.sum(axis=0)
    print(f"    hidden weights after 500 steps:")
    for i in range(hidden):
        print(f"      unit {i + 1}: {np.array2string(w1[:, i], precision=6)}")
    identical = all(np.allclose(w1[:, 0], w1[:, i]) for i in range(hidden))
    print(f"    all units identical? {identical}")
    print("    Every unit computed the same output, received the same")
    print("    gradient, and stayed identical. Four units, one effective unit.")

    print()
    print("  B) DEAD ReLU - a unit initialised with a very negative bias")
    w_dead = rng.normal(scale=0.3, size=(3, 2))
    b_dead = np.array([0.0, -50.0])          # the second unit is doomed
    z = x @ w_dead + b_dead
    h = relu(z)
    print(f"    unit 1 active on {float((h[:, 0] > 0).mean()):.1%} of inputs")
    print(f"    unit 2 active on {float((h[:, 1] > 0).mean()):.1%} of inputs   <- DEAD")
    print(f"    unit 2 gradient is (z > 0) = "
          f"{float((z[:, 1] > 0).mean()):.1%} of the time, i.e. never.")
    print("    It outputs 0 for every input, receives no gradient, and can")
    print("    never recover. Leaky ReLU keeps a small gradient alive:")
    leaky = np.where(z > 0, z, 0.01 * z)
    print(f"    with Leaky ReLU, unit 2 output range: "
          f"[{leaky[:, 1].min():.3f}, {leaky[:, 1].max():.3f}] - non-zero, so")
    print("    a gradient still flows and the unit can recover.")


def parameter_counts() -> None:
    section("6. PARAMETERS AND MEMORY - the arithmetic that sizes a GPU")
    architectures = [
        ("the section 6 toy", [2, 2, 1]),
        ("small MLP", [784, 128, 64, 10]),
        ("larger MLP", [784, 512, 256, 128, 10]),
    ]
    print(f"  {'architecture':<22}{'layers':>30}{'parameters':>14}")
    for label, dims in architectures:
        params = sum(dims[i] * dims[i + 1] + dims[i + 1] for i in range(len(dims) - 1))
        print(f"  {label:<22}{' -> '.join(map(str, dims)):>30}{params:>14,}")

    print()
    dims = [784, 128, 64, 10]
    print(f"  Breakdown for {' -> '.join(map(str, dims))}:")
    print(f"    {'layer':<14}{'weights':>12}{'biases':>10}{'total':>12}")
    total = 0
    for i in range(len(dims) - 1):
        w = dims[i] * dims[i + 1]
        b = dims[i + 1]
        total += w + b
        print(f"    {f'{dims[i]} -> {dims[i+1]}':<14}{w:>12,}{b:>10}{w + b:>12,}")
    print(f"    {'TOTAL':<14}{'':>12}{'':>10}{total:>12,}")
    print(f"    float32 memory: {total * 4 / 1024:.1f} KB")

    print()
    print("  Scaling the SAME arithmetic to real models:")
    print(f"  {'parameters':>14}{'float32':>12}{'float16':>12}{'int8':>10}"
          f"{'training (~4x fp32)':>22}")
    for params in (1e6, 1e8, 7e9, 8e9, 70e9):
        f32 = params * 4 / 1e9
        f16 = params * 2 / 1e9
        i8 = params * 1 / 1e9
        print(f"  {params:>14,.0f}{f32:>11.1f}G{f16:>11.1f}G{i8:>9.1f}G"
              f"{f32 * 4:>21.1f}G")
    print()
    print("  An 8B model needs 32 GB in float32 - more than a 24 GB GPU has.")
    print("  At float16 it is 16 GB and fits. That single calculation is why")
    print("  quantisation exists (M4-L17), and why FINE-TUNING an 8B model")
    print("  needs ~128 GB while running it needs 16 - hence LoRA (M13-L05).")


def main() -> None:
    print("=" * 74)
    print("NEURAL NETWORKS: WEIGHTS, BIASES, ACTIVATIONS")
    print("=" * 74)
    forward_pass()
    collapse_proof()
    activations()
    xor_demo()
    failure_modes()
    parameter_counts()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
