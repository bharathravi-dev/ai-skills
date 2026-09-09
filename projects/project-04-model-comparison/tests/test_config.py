"""A configuration must be valid, frozen and reproducibly identifiable."""

import pytest

from modelcmp.config import PRESETS, DecodeConfig


def test_defaults_are_deterministic():
    assert DecodeConfig().temperature == 0.0


def test_frozen():
    c = DecodeConfig()
    with pytest.raises(Exception):
        c.temperature = 1.0


@pytest.mark.parametrize("kwargs", [
    {"temperature": -0.1}, {"temperature": 5.1},
    {"top_p": 0.0}, {"top_p": 1.1}, {"top_k": 0}, {"max_tokens": 0},
])
def test_invalid_settings_rejected(kwargs):
    with pytest.raises(ValueError):
        DecodeConfig(**kwargs)


def test_fingerprint_is_stable():
    a = DecodeConfig("a", temperature=0.7, top_p=0.9)
    b = DecodeConfig("a", temperature=0.7, top_p=0.9)
    assert a.fingerprint == b.fingerprint


def test_fingerprint_ignores_the_label():
    """The label is for humans; it must not change the identity of a run."""
    a = DecodeConfig("friendly-name", temperature=0.7)
    b = DecodeConfig("different-name", temperature=0.7)
    assert a.fingerprint == b.fingerprint


def test_fingerprint_changes_with_any_behavioural_setting():
    base = DecodeConfig("x", temperature=0.7, top_p=0.9, max_tokens=100, seed=1)
    for field, value in (("temperature", 0.8), ("top_p", 0.95),
                         ("max_tokens", 101), ("seed", 2),
                         ("top_k", 40), ("stop", ("END",))):
        other = DecodeConfig(**{**{"label": "x", "temperature": 0.7,
                                   "top_p": 0.9, "max_tokens": 100, "seed": 1},
                                field: value})
        assert other.fingerprint != base.fingerprint, field


def test_presets_cover_the_lesson_recommendations():
    assert PRESETS["extraction"].temperature == 0.0
    assert PRESETS["creative"].temperature > 1.0
    assert PRESETS["tight-budget"].max_tokens < 10


def test_to_dict_round_trips_stop_sequences():
    d = DecodeConfig("x", stop=("END", "\n\n")).to_dict()
    assert d["stop"] == ["END", "\n\n"]
    assert "fingerprint" in d
