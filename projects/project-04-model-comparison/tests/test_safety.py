"""Guarantees about what this project cannot do.

Every test here asserts an ABSENCE: no network, no credentials, no spending.
These are the properties that let the project ship as course material.
"""

import pathlib
import re

import modelcmp
from modelcmp import cli, config, metrics, provider, report, runner

SOURCE_DIR = pathlib.Path(modelcmp.__file__).parent


def _sources():
    return {p.name: p.read_text() for p in SOURCE_DIR.glob("*.py")}


def test_no_network_libraries_imported():
    banned = ("import requests", "import httpx", "import urllib",
              "import socket", "from urllib", "import aiohttp")
    for name, text in _sources().items():
        for b in banned:
            assert b not in text, f"{name} imports a network library: {b}"


def test_no_hardcoded_credentials():
    patterns = [r"sk-[A-Za-z0-9]{16,}", r"api[_-]?key\s*=\s*['\"][^'\"]{8,}",
                r"AKIA[0-9A-Z]{16}"]
    for name, text in _sources().items():
        for pat in patterns:
            assert not re.search(pat, text), f"{name} may contain a credential"


def test_env_example_contains_no_real_values():
    env = (pathlib.Path(modelcmp.__file__).parents[2] / ".env.example")
    text = env.read_text()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or not line or "=" not in line:
            continue
        _, value = line.split("=", 1)
        assert value.strip() == "", f".env.example has a value: {line}"


def test_default_provider_is_the_mock():
    assert provider.MockProvider().name == "mock"


def test_cli_uses_the_mock_provider():
    assert "MockProvider()" in pathlib.Path(cli.__file__).read_text()
    assert "RealProvider(" not in pathlib.Path(cli.__file__).read_text()


def test_prices_are_labelled_illustrative():
    text = pathlib.Path(report.__file__).read_text()
    assert "ILLUSTRATIVE" in text


def test_cli_runs_end_to_end_offline(capsys):
    assert cli.main(["--samples", "3"]) == 0
    out = capsys.readouterr().out
    assert "NO network call, NO API key, $0.00" in out
    assert "fingerprint" in out


def test_cli_refuses_when_over_budget(capsys):
    assert cli.main(["--samples", "50", "--budget", "100"]) == 1
    assert "REFUSED" in capsys.readouterr().out
