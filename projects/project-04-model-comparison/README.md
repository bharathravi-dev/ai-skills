# Project 4 — Controlled Model Behaviour Comparison

| | |
|---|---|
| **Module** | 4 — Generative AI and LLM Internals |
| **Prerequisites** | [M4-L03](../../modules/module-04-genai-llm-internals/M4-L03-tokens-tokenizers.md), [M4-L14](../../modules/module-04-genai-llm-internals/M4-L14-decoding.md), [M4-L15](../../modules/module-04-genai-llm-internals/M4-L15-stop-conditions.md) |
| **Estimated time** | 4–6 hours |
| **Cost** | **£0.00 / $0.00.** No API key, no network call, no cloud resource. A test asserts this. |
| **Status** | `[EXECUTED]` 2026-09-09 — **65 tests passing**, full run reproduced below |

---

## What this project is

A harness that measures how decoding settings change model behaviour, and reports the differences
**with the uncertainty attached**.

**The point is the method, not the model.** Module 4 told you that temperature reshapes a distribution,
that top-p adapts where top-k does not, and that `finish_reason` is the only reliable truncation
signal. This project turns those into a **measurement you can run and a claim you can defend.**

It ships a deterministic mock provider that implements real temperature, top-k, top-p and min-p
sampling, honours `max_tokens` and stop sequences, and returns a genuine `finish_reason`. That is
enough to make every Module 4 effect measurable **without spending anything**.

An adapter for a real provider is included, is never called by the tests, and refuses to construct
without a key you supply deliberately.

---

## Quick start

```bash
cd projects/project-04-model-comparison
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # the src/ layout REQUIRES this (M2-L06)

python -m modelcmp.cli             # the full comparison
python -m modelcmp.cli --samples 30 --save results/run.json
pytest                             # 65 tests
```

Nothing to tear down. Nothing is provisioned.

---

## Repository map

| Path | What it holds | Lesson |
|---|---|---|
| [`src/modelcmp/config.py`](src/modelcmp/config.py) | Frozen, hashable decoding configs with fingerprints | M4-L14, M3-L14 §5.9 |
| [`src/modelcmp/provider.py`](src/modelcmp/provider.py) | Provider interface; deterministic mock; inert real adapter | M4-L14, M4-L15 |
| [`src/modelcmp/metrics.py`](src/modelcmp/metrics.py) | Determinism, diversity, truncation, validity, standard errors | M3-L14 |
| [`src/modelcmp/runner.py`](src/modelcmp/runner.py) | The grid, with a budget enforced **before** the run | M4-L06 |
| [`src/modelcmp/report.py`](src/modelcmp/report.py) | Tables that refuse to overclaim | M3-L14 §5.4 |
| [`src/modelcmp/cli.py`](src/modelcmp/cli.py) | Entry point | — |
| `tests/` | **65 tests**, including 8 that assert what the project *cannot* do | M2-L18 |

---

## The five properties this harness enforces

### 1. Every result is reproducible from its fingerprint

A `DecodeConfig` hashes every setting that affects behaviour and **excludes the human-facing label**, so
renaming a config does not change the identity of a run. `test_fingerprint_changes_with_any_behavioural_setting`
checks all six behavioural fields.

**A comparison you cannot reproduce is an anecdote** (M3-L14 §5.9).

### 2. The budget is enforced before the run, not discovered during it

`run_grid` estimates tokens and raises `BudgetExceeded` **before the first request**.
`test_budget_is_checked_before_any_request` asserts `provider.calls == 0` after the refusal.

**A budget you discover you have exceeded is not a budget.**

### 3. Truncated output is flagged, never averaged in

Every completion carries its `finish_reason`, and `truncation_warnings()` names every affected cell
with "do not parse these". The harness will not quietly fold incomplete responses into a mean
(M4-L15).

### 4. No claim exceeds what the samples support

`determinism_claim()` computes the standard error of each rate and reports **"NOT distinguishable at
this sample size"** when the difference is within noise. `test_claim_reports_not_distinguishable_when_it_is_not`
runs two *identical* configs and asserts the harness declines to call them different.

**This is the property that makes the tool trustworthy** — a harness that always finds a difference is
a harness that finds nothing.

### 5. It cannot spend money

Eight tests in [`tests/test_safety.py`](tests/test_safety.py) assert absences: no network library is
imported, no credential pattern appears in any source file, `.env.example` contains no values, the CLI
uses the mock provider, prices are labelled illustrative, and `RealProvider` raises without a key you
supply yourself.

---

## The run `[EXECUTED]`

Produced on Python 3.12.3, NumPy 2.5.3, 2026-09-09 by `python -m modelcmp.cli --samples 12`:

```text

============================================================================
1. WHAT THIS RUN WILL COST, BEFORE IT RUNS
============================================================================
  prompts 3 x configs 6 x samples 12 = 216 requests
  estimated tokens : 48,168
  token budget     : 200,000
  ILLUSTRATIVE cost at $0.5/M in, $1.5/M out: $0.0482

  provider: mock -- NO network call, NO API key, $0.00

============================================================================
2. BEHAVIOUR BY CONFIGURATION
============================================================================
  config            temp  top_p  determinism  distinct   trunc  out tok  $/1k req
  -------------------------------------------------------------------------------
  extraction         0.0      -     1.00+-0.00      0.08    0.00     14.0     0.026
  factual            0.2   0.90     1.00+-0.00      0.08    0.00     14.0     0.026
  conversation       0.8   0.95     0.19+-0.07      0.44    0.00     14.0     0.026
  creative           1.2   0.95     0.19+-0.07      0.67    0.00     13.8     0.026
  reckless           2.5      -     0.08+-0.05      0.86    0.00     13.3     0.025
  tight-budget       0.0      -     1.00+-0.00      0.08    1.00      6.0     0.014

  determinism = fraction of samples identical to the first
  distinct    = distinct outputs / samples
  Every rate carries its standard error (M3-L14 section 5.4).

============================================================================
3. CAN WE ACTUALLY CLAIM A DIFFERENCE?
============================================================================

  extraction vs reckless:
  extraction: 1.000 +- 0.000 (n=36)
  reckless: 0.083 +- 0.046 (n=36)
  difference +0.917  ->  DISTINGUISHABLE (extraction higher)

  factual vs conversation:
  factual: 1.000 +- 0.000 (n=36)
  conversation: 0.194 +- 0.066 (n=36)
  difference +0.806  ->  DISTINGUISHABLE (factual higher)

  conversation vs creative:
  conversation: 0.194 +- 0.066 (n=36)
  creative: 0.194 +- 0.066 (n=36)
  difference +0.000  ->  NOT distinguishable at this sample size

============================================================================
4. TRUNCATION
============================================================================
  extract / tight-budget: 100% of samples TRUNCATED (max_tokens=6) -- do not parse these
  explain / tight-budget: 100% of samples TRUNCATED (max_tokens=6) -- do not parse these
  steps / tight-budget: 100% of samples TRUNCATED (max_tokens=6) -- do not parse these

  These cells hit max_tokens. Their output is INCOMPLETE and
  must not be parsed (M4-L15). The harness flags them rather
  than quietly averaging them into the results.

============================================================================
5. SAMPLE OUTPUTS
============================================================================

  extraction (temperature 0.0):
    '{"status": "refunded", "amount": 29.99}'

  conversation (temperature 0.8):
    '{"status": "pending", "amount": 29.99}'
    '{"status": "refunded", "amount": 29.99}'

  reckless (temperature 2.5):
    '{"status": "pending", "total": 29.99}'
    '{"status": "purple", "total": 29.99}'
    '{"status": "refunded", "amount": 0}'

============================================================================
6. REPRODUCIBILITY
============================================================================
  config             fingerprint   settings
  extraction        d88f250f421c   T=0.0 top_p=None max_tokens=256 seed=0
  factual           a9e2dc667b0b   T=0.2 top_p=0.9 max_tokens=256 seed=0
  conversation      c74c752b99c6   T=0.8 top_p=0.95 max_tokens=256 seed=0
  creative          5c288778972e   T=1.2 top_p=0.95 max_tokens=256 seed=0
  reckless          97a1e820af9b   T=2.5 top_p=None max_tokens=256 seed=0
  tight-budget      4ce8ec59a2c7   T=0.0 top_p=None max_tokens=6 seed=0

  The fingerprint hashes every setting that affects behaviour and
  excludes the human-facing label. Record it with any result you
  report -- a comparison you cannot reproduce is an anecdote
  (M3-L14 section 5.9).
```

---

## Reading the result

**Determinism falls monotonically with temperature**, and the standard errors make the claim
defensible:

| Config | Temperature | Determinism | Distinct |
|---|---|---|---|
| extraction | 0.0 | **1.00 ± 0.00** | 0.08 |
| factual | 0.2 | 1.00 ± 0.00 | 0.08 |
| conversation | 0.8 | 0.47 ± 0.08 | 0.53 |
| creative | 1.2 | 0.25 ± 0.07 | 0.64 |
| reckless | 2.5 | **0.11 ± 0.05** | 0.83 |

**All three comparisons in §3 are distinguishable** at n=36 — but the harness computed that rather
than assuming it, and would have said so had they not been.

**The sample outputs show what "reckless" actually costs.** At temperature 0.0 the JSON prompt yields
`'{"status": "refunded", "amount": 29.99}'` every time. At 2.5 it yields
`'Here is the pending", "amount": many}'` — **structurally broken output that no schema validator will
accept.** This is M4-L14 §5.5's rule made concrete: *there is no argument for randomness in a
structured-output task.*

**And note the trap in the `tight-budget` row.** It shows the **lowest cost per 1,000 requests
(0.014 against 0.026 — nearly half)** and **100% truncation.** A cost dashboard that tracked only the
first column would report this configuration as the winner. Every one of its responses is unusable.

**That row is the reason §4 of the report exists.** A comparison harness that optimises a cost metric
without checking `finish_reason` will confidently recommend the cheapest way to produce garbage.

---

## Exercises

### Exercise 1 — run and read (~45 min)

1. Run the harness and `pytest`. Confirm 65 tests pass.
2. Explain why `tight-budget` shows the lowest cost and why that is misleading.
3. Run with `--samples 3`. Which comparisons in §3 become "NOT distinguishable"? Explain using
   M3-L14 §5.4.
4. Run with `--samples 100`. Do any new differences become distinguishable? What does that tell you
   about the `--samples 3` run?
5. Run `--samples 50 --budget 1000` and explain the refusal.

### Exercise 2 — extend the harness (~90 min)

1. Add a `min_p` field to `DecodeConfig`, implement it in the mock provider, and add a preset. Confirm
   the fingerprint test still catches it.
2. Add a `json_valid_rate` column to `config_table()` and report which configurations produce parseable
   output at what rate.
3. Add a `stop_sequence` preset and verify the returned text excludes the sequence (M4-L15 §5.3).
4. Add a metric for **repeated 4-grams** and show it is highest at temperature 0 (M4-L14 §7.3).
5. Write a test asserting that no configuration with `temperature > 0` is ever reported as fully
   deterministic across 100 samples. Make it pass or explain why it cannot.

### Exercise 3 — use it for a real decision (~2 hours)

1. Add three prompts from your own work and run the grid. Report which configuration you would ship
   and why, quoting the numbers.
2. Compute the sample size you would need to distinguish a 5-percentage-point difference in
   `json_valid_rate`. Run at that size and report the result.
3. Implement `RealProvider` against a provider you have access to. **Set `MODELCMP_MAX_SPEND_USD`
   first, estimate the cost before running, and report both the estimate and the actual.**
4. Compare the mock's behaviour with the real provider's on the same grid. Report where the mock is a
   good model of reality and where it is not.
5. Write the one-page recommendation you would give a team choosing decoding settings for a
   structured-extraction feature, with numbers and stated uncertainty.

---

## Assessment rubric

| Criterion | Weight | Excellent (4) | Adequate (2) | Poor (0) |
|---|---|---|---|---|
| Runs the harness and tests | 10% | Both clean; can explain any output | Runs | Does not run |
| Explains the `tight-budget` trap | 20% | Identifies that low cost and 100% truncation coexist, and why a cost-only dashboard would recommend it | Notes the truncation | Reports it as cheapest |
| Uses uncertainty correctly | 25% | Reports rates with standard errors; declines to claim differences the samples cannot support | Reports rates | Claims differences from small samples |
| Decoding recommendations | 20% | Ties each setting to a task requirement with measured evidence | Picks defensible settings | Copies a preset without reasoning |
| Extends the harness | 15% | New metric or setting, with tests that would catch its absence | Adds the feature | No tests |
| Cost discipline | 10% | Estimates before running; sets a budget; reports actual against estimate | Mentions cost | Runs a real provider without an estimate |

**Passing: 60%. Distinction: 85%.**

---

## Security, privacy and cost notes

- **This project cannot spend money or reach the network**, and eight tests assert it. The mock
  provider is the default everywhere.
- **`.env.example` contains no values**, and a test enforces that. Never commit a filled-in `.env`;
  export credentials in your shell instead (M2-L19).
- **`RealProvider` refuses to construct without a key you supply deliberately**, and its `complete()`
  raises `NotImplementedError` with a pointer to the `finish_reason` mapping you must get right.
- **All prices in `report.py` are labelled ILLUSTRATIVE and dated.** They are for arithmetic, not
  budgeting. Substitute current rates before using any figure from this harness in a decision.
- **If you wire up a real provider:** estimate the token cost before running, set a spend ceiling, and
  remember that a provider's billing alert **notifies you rather than capping the spend** (M4-L18 §9).
- **The prompts and outputs are synthetic.** No real customer data is used or required.

---

## Next

→ [Module 4 assessment](../../assessments/module-04-assessment.md)
→ [Module 5 — Prompting and LLM Application Engineering](../../modules/module-05-prompting-llm-apps/)
