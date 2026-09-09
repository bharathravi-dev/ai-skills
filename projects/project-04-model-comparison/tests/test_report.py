"""The report must never claim a difference the samples cannot support."""

import pytest

from modelcmp.config import PRESETS, DecodeConfig
from modelcmp.provider import MockProvider
from modelcmp.report import config_table, determinism_claim, truncation_warnings
from modelcmp.runner import run_grid


@pytest.fixture
def result(prompts):
    configs = [PRESETS["extraction"], PRESETS["conversation"],
               PRESETS["creative"]]
    return run_grid(MockProvider(), prompts, configs, samples=20)


def test_table_has_a_row_per_config(result):
    table = config_table(result)
    for label in ("extraction", "conversation", "creative"):
        assert label in table


def test_table_reports_standard_errors(result):
    assert "+-" in config_table(result)


def test_temperature_zero_is_fully_deterministic(result):
    cells = result.by_config()["extraction"]
    assert all(c.metrics.determinism == 1.0 for c in cells)


def test_higher_temperature_is_less_deterministic(result):
    by = result.by_config()

    def det(label):
        cells = by[label]
        n = sum(c.metrics.n_samples for c in cells)
        return sum(c.metrics.determinism * c.metrics.n_samples
                   for c in cells) / n

    assert det("extraction") >= det("conversation") >= det("creative")


def test_claim_reports_not_distinguishable_when_it_is_not(prompts):
    """Two identical configs must never be reported as different."""
    a = DecodeConfig("a", temperature=0.8, top_p=0.95)
    b = DecodeConfig("b", temperature=0.8, top_p=0.95)
    r = run_grid(MockProvider(), prompts, [a, b], samples=10)
    assert "NOT distinguishable" in determinism_claim(r, "a", "b")


def test_claim_detects_a_real_difference(result):
    out = determinism_claim(result, "extraction", "creative")
    assert "DISTINGUISHABLE" in out


def test_claim_rejects_an_unknown_label(result):
    with pytest.raises(KeyError):
        determinism_claim(result, "extraction", "no-such-config")


def test_truncation_warnings_are_raised(prompts):
    tiny = DecodeConfig("tiny", temperature=0.0, max_tokens=2)
    r = run_grid(MockProvider(), prompts, [tiny], samples=3)
    warns = truncation_warnings(r)
    assert warns and all("TRUNCATED" in w for w in warns)
    assert all("do not parse" in w for w in warns)


def test_no_warnings_when_nothing_truncated(prompts):
    roomy = DecodeConfig("roomy", temperature=0.0, max_tokens=500)
    r = run_grid(MockProvider(), prompts, [roomy], samples=3)
    assert truncation_warnings(r) == []
