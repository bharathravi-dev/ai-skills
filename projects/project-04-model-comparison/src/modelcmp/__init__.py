"""Project 4 -- a reproducible model-behaviour comparison harness.

Module 4 taught how decoding settings, tokenization and context limits change
what a model produces. This project makes those effects MEASURABLE: you define
a set of prompts and a set of configurations, and the harness runs the grid,
records everything needed to reproduce it, and reports the differences with
appropriate uncertainty.

The point is the METHOD, not the model. Everything runs offline against a
deterministic mock provider; an adapter for a real provider is included and is
never called by the tests.

Module map:
    provider   the provider interface, plus a deterministic mock
    config     a decoding configuration, hashable and serialisable
    runner     executes a prompt x config grid, with retries and cost control
    metrics    determinism, diversity, format validity, length, truncation
    report     comparison tables with uncertainty (M3-L14)
"""

__version__ = "0.1.0"
