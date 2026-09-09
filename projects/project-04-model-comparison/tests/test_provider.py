"""The mock provider must behave like a real one in the ways that matter."""

import json

import pytest

from modelcmp.config import DecodeConfig
from modelcmp.provider import MockProvider, RealProvider


def test_temperature_zero_is_deterministic(provider):
    cfg = DecodeConfig("t0", temperature=0.0)
    outs = {provider.complete("Explain the refund.", cfg, i).text
            for i in range(10)}
    assert len(outs) == 1


def test_high_temperature_produces_variety(provider):
    cfg = DecodeConfig("hot", temperature=2.0)
    outs = {provider.complete("Explain the refund.", cfg, i).text
            for i in range(20)}
    assert len(outs) > 1


def test_same_run_index_reproduces_exactly(provider):
    cfg = DecodeConfig("hot", temperature=1.5)
    a = provider.complete("Explain the refund.", cfg, 7)
    b = provider.complete("Explain the refund.", cfg, 7)
    assert a.text == b.text


def test_different_seeds_differ(provider):
    p = "Explain the refund."
    a = provider.complete(p, DecodeConfig("a", temperature=1.5, seed=1), 0)
    b = provider.complete(p, DecodeConfig("b", temperature=1.5, seed=2), 0)
    assert a.text != b.text


def test_max_tokens_truncates_and_reports_length(provider):
    cfg = DecodeConfig("tiny", temperature=0.0, max_tokens=2)
    c = provider.complete("Explain the refund status.", cfg)
    assert c.finish_reason == "length"
    assert c.truncated is True


def test_generous_limit_finishes_normally(provider):
    cfg = DecodeConfig("roomy", temperature=0.0, max_tokens=500)
    c = provider.complete("Explain the refund status.", cfg)
    assert c.finish_reason == "stop"
    assert c.truncated is False


def test_stop_sequence_halts_and_is_excluded(provider):
    """M4-L15 section 5.3: the stop sequence is not returned."""
    cfg = DecodeConfig("stopper", temperature=0.0, max_tokens=500,
                       stop=("processed",))
    c = provider.complete("Explain the refund status.", cfg)
    assert c.finish_reason == "stop_sequence"
    assert "processed" not in c.text


def test_top_k_one_matches_greedy(provider):
    p = "Explain the refund status."
    greedy = provider.complete(p, DecodeConfig("g", temperature=0.0), 0)
    k1 = provider.complete(p, DecodeConfig("k", temperature=1.0, top_k=1), 0)
    assert greedy.text == k1.text


def test_json_prompt_yields_parseable_output_at_temperature_zero(provider):
    cfg = DecodeConfig("extract", temperature=0.0, max_tokens=500)
    c = provider.complete("Extract the refund status as JSON.", cfg)
    assert c.finish_reason == "stop"
    json.loads(c.text)


def test_token_counts_are_positive(provider):
    c = provider.complete("Explain the refund.", DecodeConfig())
    assert c.input_tokens >= 1 and c.output_tokens >= 1


def test_completion_records_its_config(provider):
    cfg = DecodeConfig("x", temperature=0.4)
    c = provider.complete("Explain the refund.", cfg)
    assert c.config_fingerprint == cfg.fingerprint


def test_real_provider_refuses_without_a_key(monkeypatch):
    """It must be impossible to accidentally spend money."""
    monkeypatch.delenv("MODELCMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="API key"):
        RealProvider()


def test_real_provider_is_not_implemented(monkeypatch):
    monkeypatch.setenv("MODELCMP_API_KEY", "not-a-real-key")
    p = RealProvider()
    with pytest.raises(NotImplementedError):
        p.complete("hello", DecodeConfig())
