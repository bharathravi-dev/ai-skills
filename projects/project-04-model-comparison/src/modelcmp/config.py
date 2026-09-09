"""A decoding configuration: the settings you control per request (M4-L14).

Configurations are frozen, hashable and serialisable, because a comparison you
cannot reproduce is an anecdote (M3-L14 section 5.9).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DecodeConfig:
    """One decoding configuration.

    Every field that changes model behaviour lives here, so that a run can be
    reproduced from the config alone. `label` is for humans and is excluded
    from the fingerprint.
    """

    label: str = "default"
    temperature: float = 0.0
    top_p: float | None = None
    top_k: int | None = None
    max_tokens: int = 256
    stop: tuple[str, ...] = ()
    seed: int | None = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.temperature <= 5.0:
            raise ValueError(f"temperature {self.temperature} outside [0, 5]")
        if self.top_p is not None and not 0.0 < self.top_p <= 1.0:
            raise ValueError(f"top_p {self.top_p} outside (0, 1]")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError(f"top_k {self.top_k} must be >= 1")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")

    @property
    def fingerprint(self) -> str:
        """A stable hash of everything that affects behaviour, excluding the label."""
        payload = {k: v for k, v in asdict(self).items() if k != "label"}
        payload["stop"] = list(self.stop)
        blob = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stop"] = list(self.stop)
        d["fingerprint"] = self.fingerprint
        return d


# Configurations that correspond to the recommendations in M4-L14 section 5.5.
PRESETS: dict[str, DecodeConfig] = {
    "extraction": DecodeConfig("extraction", temperature=0.0, max_tokens=256),
    "factual": DecodeConfig("factual", temperature=0.2, top_p=0.9, max_tokens=256),
    "conversation": DecodeConfig("conversation", temperature=0.8, top_p=0.95,
                                 max_tokens=256),
    "creative": DecodeConfig("creative", temperature=1.2, top_p=0.95,
                             max_tokens=256),
    "reckless": DecodeConfig("reckless", temperature=2.5, max_tokens=256),
    "tight-budget": DecodeConfig("tight-budget", temperature=0.0, max_tokens=6),
}
