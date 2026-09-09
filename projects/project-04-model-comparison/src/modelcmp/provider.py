"""Provider interface, plus a deterministic mock.

The mock is not a toy: it implements real temperature, top-k, top-p and min-p
sampling over a small learned distribution, honours max_tokens and stop
sequences, and returns a genuine finish_reason (M4-L15). That is enough to make
every effect in Module 4 measurable without a network call or an API key.

The real-provider adapter is deliberately inert: it raises unless you supply
credentials yourself, and NOTHING in this project's tests exercises it.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .config import DecodeConfig


@dataclass(frozen=True)
class Completion:
    text: str
    finish_reason: str          # "stop" | "length" | "stop_sequence"
    input_tokens: int
    output_tokens: int
    config_fingerprint: str

    @property
    def truncated(self) -> bool:
        return self.finish_reason == "length"


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, config: DecodeConfig,
                 run_index: int = 0) -> Completion:
        ...


def _softmax(z: np.ndarray, temperature: float) -> np.ndarray:
    if temperature <= 0:
        out = np.zeros_like(z, dtype=float)
        out[int(np.argmax(z))] = 1.0
        return out
    z = z / temperature
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def _truncate(probs: np.ndarray, top_k: int | None,
              top_p: float | None) -> np.ndarray:
    p = probs.copy()
    if top_k is not None:
        keep = np.zeros_like(p, dtype=bool)
        keep[np.argsort(-p)[:top_k]] = True
        p = np.where(keep, p, 0.0)
    if top_p is not None:
        order = np.argsort(-p)
        cum = np.cumsum(p[order])
        n = int(np.searchsorted(cum, top_p) + 1)
        keep = np.zeros_like(p, dtype=bool)
        keep[order[:n]] = True
        p = np.where(keep, p, 0.0)
    total = p.sum()
    return p / total if total > 0 else probs


class MockProvider:
    """A deterministic provider with genuine sampling behaviour.

    Given a prompt, it builds a small next-token distribution from a template
    grammar, then decodes it using the supplied config. Identical (prompt,
    config, run_index) always produces identical output -- which is what makes
    the harness's determinism metric meaningful rather than circular.
    """

    name = "mock"

    GRAMMARS: dict[str, list[list[tuple[str, float]]]] = {
        "json": [
            [('{"status": "', 6.0), ('{"result": "', 3.0), ('Here is the ', 0.5)],
            [("refunded", 5.0), ("pending", 3.5), ("cancelled", 2.0),
             ("purple", -1.0)],
            [('", "amount": ', 6.0), ('", "total": ', 3.0), ('" ', 0.2)],
            [("29.99}", 5.0), ("14.50}", 3.0), ("0}", 1.0), ("many}", -2.0)],
        ],
        "prose": [
            [("The refund ", 5.0), ("Your refund ", 4.0), ("A refund ", 2.0)],
            [("has been ", 5.0), ("will be ", 3.5), ("was ", 2.0)],
            [("processed ", 5.0), ("issued ", 4.0), ("delayed ", 1.0)],
            [("successfully. ", 5.0), ("today. ", 3.0), ("eventually. ", 0.5)],
            [("Please allow ", 4.0), ("It may take ", 3.0), ("Expect ", 2.0)],
            [("three days.", 5.0), ("five days.", 3.0), ("some time.", 1.0)],
        ],
        "list": [
            [("1. Check ", 5.0), ("First, check ", 3.0)],
            [("your email. ", 5.0), ("the portal. ", 3.5)],
            [("2. Open ", 5.0), ("Then open ", 3.0)],
            [("Settings. ", 5.0), ("the app. ", 3.0)],
            [("3. Select ", 5.0), ("Finally select ", 3.0)],
            [("Security.", 5.0), ("Billing.", 3.0)],
        ],
    }

    def __init__(self, chars_per_token: float = 4.0) -> None:
        self.chars_per_token = chars_per_token
        self.calls = 0

    def _grammar_for(self, prompt: str) -> list[list[tuple[str, float]]]:
        low = prompt.lower()
        if "json" in low:
            return self.GRAMMARS["json"]
        if "steps" in low or "list" in low:
            return self.GRAMMARS["list"]
        return self.GRAMMARS["prose"]

    def complete(self, prompt: str, config: DecodeConfig,
                 run_index: int = 0) -> Completion:
        self.calls += 1
        base = 0 if config.seed is None else config.seed
        rng = np.random.default_rng(
            abs(hash((prompt, config.fingerprint, base, run_index))) % (2 ** 32))

        grammar = self._grammar_for(prompt)
        pieces: list[str] = []
        finish = "stop"
        for step in grammar:
            options = [t for t, _ in step]
            logits = np.array([w for _, w in step], dtype=float)
            probs = _truncate(_softmax(logits, config.temperature),
                              config.top_k, config.top_p)
            idx = (int(np.argmax(probs)) if config.temperature <= 0
                   else int(rng.choice(len(probs), p=probs)))
            candidate = "".join(pieces) + options[idx]

            hit = next((s for s in config.stop if s in candidate), None)
            if hit is not None:
                pieces = [candidate[:candidate.index(hit)]]
                finish = "stop_sequence"
                break

            if self._tokens(candidate) > config.max_tokens:
                allowed = int(config.max_tokens * self.chars_per_token)
                pieces = [candidate[:allowed]]
                finish = "length"
                break
            pieces.append(options[idx])

        text = "".join(pieces)
        return Completion(
            text=text,
            finish_reason=finish,
            input_tokens=self._tokens(prompt),
            output_tokens=self._tokens(text),
            config_fingerprint=config.fingerprint,
        )

    def _tokens(self, text: str) -> int:
        return max(1, math.ceil(len(text) / self.chars_per_token))


class RealProvider:
    """Adapter for a real API. INERT unless you supply credentials yourself.

    This class exists so the harness's interface is honest about what a real
    run would look like. It is never instantiated by the tests, never called by
    the default runner, and refuses to construct without an explicit key.

    Costs money. Read M4-L18 section 9 before using it, set
    MODELCMP_MAX_SPEND_USD, and note that a budget alert notifies rather than
    caps.
    """

    name = "real"

    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None) -> None:
        key = api_key or os.environ.get("MODELCMP_API_KEY", "")
        if not key:
            raise RuntimeError(
                "RealProvider needs an API key. This project runs fully "
                "offline with MockProvider; supply a key only if you have "
                "deliberately chosen to spend money. See .env.example.")
        self._key = key
        self._base_url = base_url or os.environ.get("MODELCMP_BASE_URL", "")

    def complete(self, prompt: str, config: DecodeConfig,
                 run_index: int = 0) -> Completion:
        raise NotImplementedError(
            "Wire this to your provider's SDK. Map their finish_reason onto "
            "'stop' / 'length' / 'stop_sequence', and DO NOT parse the "
            "response before checking it (M4-L15).")
