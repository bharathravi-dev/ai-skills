"""Metrics for comparing model behaviour across configurations.

Every metric here answers a question Module 4 raised: is the output
deterministic (M4-L14 section 5.7), how varied is it, does it parse, was it
truncated (M4-L15), what did it cost (M4-L03).

Metrics that cannot be computed return NaN rather than 0 -- "no samples" and
"zero" are different statements (M3-L14).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .provider import Completion


@dataclass(frozen=True)
class RunMetrics:
    n_samples: int
    determinism: float          # fraction of runs identical to the first
    distinct_outputs: int
    distinct_ratio: float
    mean_output_tokens: float
    truncation_rate: float
    json_valid_rate: float
    mean_input_tokens: float

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__annotations__}


def _is_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def summarise(completions: list[Completion]) -> RunMetrics:
    """Summarise repeated runs of ONE (prompt, config) cell."""
    if not completions:
        raise ValueError("no completions to summarise")
    n = len(completions)
    texts = [c.text for c in completions]
    distinct = len(set(texts))
    identical = sum(1 for t in texts if t == texts[0])
    return RunMetrics(
        n_samples=n,
        determinism=identical / n,
        distinct_outputs=distinct,
        distinct_ratio=distinct / n,
        mean_output_tokens=sum(c.output_tokens for c in completions) / n,
        truncation_rate=sum(1 for c in completions if c.truncated) / n,
        json_valid_rate=sum(1 for t in texts if _is_json(t)) / n,
        mean_input_tokens=sum(c.input_tokens for c in completions) / n,
    )


def proportion_stderr(p: float, n: int) -> float:
    """Standard error of a proportion (M3-L14 section 5.4).

    Reported alongside every rate, because a rate from 5 samples and a rate
    from 500 are not the same claim.
    """
    if n <= 0:
        return float("nan")
    return math.sqrt(max(p * (1 - p), 0.0) / n)


def distinguishable(p1: float, p2: float, n1: int, n2: int,
                    z: float = 1.96) -> bool:
    """Are two rates distinguishable at roughly 95%? (M3-L14 section 5.4)

    Used by the report so it never claims a difference it cannot support.
    """
    se = math.sqrt(proportion_stderr(p1, n1) ** 2 +
                   proportion_stderr(p2, n2) ** 2)
    if se == 0:
        return p1 != p2
    return abs(p1 - p2) > z * se


def token_cost(input_tokens: float, output_tokens: float,
               in_price_per_m: float, out_price_per_m: float) -> float:
    """Cost for one request. Prices are per MILLION tokens.

    Nothing here charges anything -- this is arithmetic over the mock
    provider's token counts (M4-L03 section 5.7).
    """
    return (input_tokens * in_price_per_m +
            output_tokens * out_price_per_m) / 1_000_000
