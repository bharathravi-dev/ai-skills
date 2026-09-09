"""Executes a prompt x config grid, reproducibly and within a budget.

Three properties this runner guarantees, each corresponding to a lesson:

  * every result records the config fingerprint that produced it (M3-L14 5.9)
  * truncated completions are FLAGGED, never silently used (M4-L15)
  * a spend ceiling is enforced BEFORE the run, not discovered during it
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import DecodeConfig
from .metrics import RunMetrics, summarise
from .provider import Completion, Provider


class BudgetExceeded(RuntimeError):
    """Raised BEFORE any request is made, never after."""


@dataclass
class Cell:
    prompt_id: str
    prompt: str
    config: DecodeConfig
    completions: list[Completion] = field(default_factory=list)

    @property
    def metrics(self) -> RunMetrics:
        return summarise(self.completions)


@dataclass
class GridResult:
    cells: list[Cell]
    provider: str
    samples: int
    started_at: float
    finished_at: float
    estimated_tokens: int

    def by_config(self) -> dict[str, list[Cell]]:
        out: dict[str, list[Cell]] = {}
        for c in self.cells:
            out.setdefault(c.config.label, []).append(c)
        return out

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "samples_per_cell": self.samples,
            "duration_s": round(self.finished_at - self.started_at, 3),
            "estimated_tokens": self.estimated_tokens,
            "cells": [
                {"prompt_id": c.prompt_id,
                 "config": c.config.to_dict(),
                 "metrics": c.metrics.to_dict(),
                 "outputs": [x.text for x in c.completions],
                 "finish_reasons": [x.finish_reason for x in c.completions]}
                for c in self.cells
            ],
        }

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2))
        return p


def estimate_tokens(prompts: dict[str, str], configs: list[DecodeConfig],
                    samples: int, chars_per_token: float = 4.0) -> int:
    """Estimate the run's token usage BEFORE running it (M4-L03 section 5.7)."""
    total = 0
    for prompt in prompts.values():
        p_tokens = max(1, int(len(prompt) / chars_per_token))
        for cfg in configs:
            total += samples * (p_tokens + cfg.max_tokens)
    return total


def run_grid(provider: Provider, prompts: dict[str, str],
             configs: list[DecodeConfig], samples: int = 5,
             max_tokens_budget: int | None = None) -> GridResult:
    """Run every (prompt, config) cell `samples` times.

    `max_tokens_budget` is checked BEFORE the first request. A budget you
    discover you have exceeded is not a budget.
    """
    if samples < 1:
        raise ValueError("samples must be >= 1")
    if not prompts:
        raise ValueError("no prompts supplied")
    if not configs:
        raise ValueError("no configs supplied")

    estimate = estimate_tokens(prompts, configs, samples)
    if max_tokens_budget is not None and estimate > max_tokens_budget:
        raise BudgetExceeded(
            f"estimated {estimate:,} tokens exceeds the budget of "
            f"{max_tokens_budget:,}. Reduce samples, configs, prompts or "
            f"max_tokens -- or raise the budget deliberately.")

    started = time.perf_counter()
    cells: list[Cell] = []
    for pid, prompt in prompts.items():
        for cfg in configs:
            cell = Cell(prompt_id=pid, prompt=prompt, config=cfg)
            for i in range(samples):
                cell.completions.append(provider.complete(prompt, cfg, i))
            cells.append(cell)
    finished = time.perf_counter()

    return GridResult(cells=cells, provider=provider.name, samples=samples,
                      started_at=started, finished_at=finished,
                      estimated_tokens=estimate)
