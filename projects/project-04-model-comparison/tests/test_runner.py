"""The runner must be reproducible, budget-bounded and honest about truncation."""

import json

import pytest

from modelcmp.config import PRESETS, DecodeConfig
from modelcmp.provider import MockProvider
from modelcmp.runner import BudgetExceeded, estimate_tokens, run_grid


def test_grid_shape(provider, prompts, configs):
    r = run_grid(provider, prompts, configs, samples=3)
    assert len(r.cells) == len(prompts) * len(configs)
    assert all(len(c.completions) == 3 for c in r.cells)


def test_budget_is_checked_before_any_request(prompts, configs):
    """A budget you discover you have exceeded is not a budget."""
    p = MockProvider()
    with pytest.raises(BudgetExceeded, match="exceeds the budget"):
        run_grid(p, prompts, configs, samples=100, max_tokens_budget=100)
    assert p.calls == 0, "no request should have been made"


def test_generous_budget_permits_the_run(provider, prompts, configs):
    r = run_grid(provider, prompts, configs, samples=2,
                 max_tokens_budget=10_000_000)
    assert len(r.cells) > 0


def test_estimate_scales_with_every_dimension(prompts, configs):
    base = estimate_tokens(prompts, configs, 1)
    assert estimate_tokens(prompts, configs, 2) == pytest.approx(2 * base)
    assert estimate_tokens(prompts, configs[:1], 1) < base


def test_run_is_reproducible(prompts, configs):
    a = run_grid(MockProvider(), prompts, configs, samples=4)
    b = run_grid(MockProvider(), prompts, configs, samples=4)
    assert [x.text for c in a.cells for x in c.completions] == \
           [x.text for c in b.cells for x in c.completions]


def test_every_completion_records_its_config(provider, prompts, configs):
    r = run_grid(provider, prompts, configs, samples=2)
    for cell in r.cells:
        for c in cell.completions:
            assert c.config_fingerprint == cell.config.fingerprint


def test_truncation_is_recorded_not_hidden(provider, prompts):
    tiny = DecodeConfig("tiny", temperature=0.0, max_tokens=2)
    r = run_grid(provider, prompts, [tiny], samples=3)
    assert all(c.metrics.truncation_rate == 1.0 for c in r.cells)
    assert all(x.finish_reason == "length"
               for c in r.cells for x in c.completions)


@pytest.mark.parametrize("bad", [
    {"samples": 0}, {"prompts": {}}, {"configs": []},
])
def test_invalid_grids_rejected(provider, prompts, configs, bad):
    kwargs = {"prompts": prompts, "configs": configs, "samples": 2}
    kwargs.update(bad)
    with pytest.raises(ValueError):
        run_grid(provider, kwargs["prompts"], kwargs["configs"],
                 samples=kwargs["samples"])


def test_results_serialise_and_reload(provider, prompts, configs, tmp_path):
    r = run_grid(provider, prompts, configs, samples=2)
    path = r.save(tmp_path / "results.json")
    data = json.loads(path.read_text())
    assert data["provider"] == "mock"
    assert data["samples_per_cell"] == 2
    assert len(data["cells"]) == len(prompts) * len(configs)
    assert "fingerprint" in data["cells"][0]["config"]
    assert "finish_reasons" in data["cells"][0]
