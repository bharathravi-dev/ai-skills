import pytest

from modelcmp.config import PRESETS, DecodeConfig
from modelcmp.provider import MockProvider

PROMPTS = {
    "extract": "Extract the refund status as JSON.",
    "explain": "Explain the refund status to the customer.",
}


@pytest.fixture
def provider():
    return MockProvider()


@pytest.fixture
def prompts():
    return dict(PROMPTS)


@pytest.fixture
def configs():
    return [PRESETS["extraction"], PRESETS["conversation"], PRESETS["creative"]]
