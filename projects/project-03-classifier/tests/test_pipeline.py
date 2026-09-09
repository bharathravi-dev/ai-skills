"""End-to-end guarantees about the pipeline itself.

The most important test in this file is the one that reads train.py's source
to confirm the test set is used exactly once. A convention that is not
enforced is a convention that will be broken.
"""

from __future__ import annotations

import inspect
import re

import numpy as np
import pytest

from churnclf import evaluate, train


@pytest.fixture(scope="module")
def result():
    return train.run(n_customers=600, months=10, verbose=False)


def test_pipeline_runs_and_returns_a_report(result):
    assert set(result) >= {"split_sizes", "threshold", "test", "baselines",
                           "gradient_check"}
    assert result["test"]["tp"] + result["test"]["fn"] > 0


def test_gradient_check_passed(result):
    assert result["gradient_check"] < 1e-7


def test_all_three_parts_are_non_empty(result):
    for part, n in result["split_sizes"].items():
        assert n > 0, f"{part} is empty"


def test_model_beats_the_always_negative_baseline_on_recall(result):
    assert result["test"]["recall"] > result["baselines"]["always negative"]["recall"]


def test_model_beats_random_flagging_on_precision(result):
    """Precision must exceed the base rate, or flagging is no better than a coin."""
    assert result["test"]["precision"] > result["test"]["base_rate"]


def test_pr_auc_beats_its_own_random_baseline(result):
    assert result["test"]["pr_auc"] > result["test"]["base_rate"] * 2


def test_leaky_feature_inflates_the_score(result):
    """The target-encoded feature must measurably help, or the demo is empty."""
    assert result["leaky_feature_test"]["pr_auc"] > result["test"]["pr_auc"]


def _code_lines():
    """train.run's source with comments stripped."""
    source = inspect.getsource(train.run)
    return [line.split("#")[0] for line in source.splitlines()]


def test_no_test_labels_are_read_before_the_threshold_is_chosen():
    """The invariant that makes the test set a test set.

    Every threshold decision must be complete before any test LABEL is read.
    Reading test features earlier would be harmless; reading test labels is
    what turns a test set into a validation set (M1-L06).
    """
    lines = _code_lines()
    label_reads = [i for i, line in enumerate(lines)
                   if "data.y[split.test]" in line]
    choices = [i for i, line in enumerate(lines)
               if "choose_threshold" in line or line.strip().startswith("chosen =")]
    assert label_reads, "the pipeline never scores on the test set"
    assert choices, "the pipeline never chooses a threshold"
    assert min(label_reads) > max(choices), (
        f"a test label is read at line {min(label_reads)} of train.run, before "
        f"threshold selection finishes at line {max(choices)}"
    )


def test_the_test_set_is_scored_exactly_once():
    """One call to `report` on the test set. Repeated scoring erodes it."""
    lines = _code_lines()
    # `\breport(` so that slice_report( does not match.
    scorings = [line for line in lines
                if re.search(r"\breport\(", line) and "data.y[split.test]" in line]
    assert len(scorings) == 1, (
        f"the test set is scored {len(scorings)} times; it should be scored once"
    )


def test_the_final_number_does_not_come_from_validation_data():
    lines = _code_lines()
    final_assign = [i for i, line in enumerate(lines)
                    if line.strip().startswith("final = ")]
    assert len(final_assign) == 1
    assert "split.val" not in lines[final_assign[0]]


def test_no_threshold_chooser_accepts_a_test_set():
    """Every chooser's parameters must be named for validation data."""
    for name in dir(evaluate):
        if not name.startswith("choose_threshold"):
            continue
        params = inspect.signature(getattr(evaluate, name)).parameters
        assert not any("test" in p for p in params), f"{name} takes a test set"
        assert any("val" in p for p in params), f"{name} takes no validation data"


def test_pipeline_is_reproducible():
    a = train.run(n_customers=400, months=10, seed=5, verbose=False)
    b = train.run(n_customers=400, months=10, seed=5, verbose=False)
    assert a["test"] == b["test"]
    assert a["threshold"]["threshold"] == b["threshold"]["threshold"]


def test_different_seeds_give_different_results():
    a = train.run(n_customers=400, months=10, seed=5, verbose=False)
    b = train.run(n_customers=400, months=10, seed=6, verbose=False)
    assert a["test"] != b["test"]


def test_limitations_are_stated_and_mention_the_important_ones():
    text = " ".join(train.LIMITATIONS).lower()
    for phrase in ("synthetic", "correlational", "calibration", "assumption",
                   "compliance"):
        assert phrase in text, f"limitations do not mention {phrase!r}"


def test_cli_json_mode_runs(capsys):
    assert train.main(["--customers", "300", "--months", "10", "--json"]) == 0
    out = capsys.readouterr().out
    assert '"threshold"' in out and '"test"' in out


def test_verbose_report_prints_baselines_and_limitations(capsys):
    train.run(n_customers=400, months=10, verbose=True)
    out = capsys.readouterr().out
    for expected in ("always negative", "LIMITATIONS", "GRADIENT CHECK",
                     "base rate", "PR-AUC"):
        assert expected in out, f"report is missing {expected!r}"


def test_no_secrets_or_credentials_in_the_package():
    """Nothing in this project may read an API key or a credential."""
    import pathlib
    root = pathlib.Path(train.__file__).parent
    banned = ("api_key", "API_KEY", "secret", "password", "aws_access")
    for path in root.glob("*.py"):
        text = path.read_text()
        for word in banned:
            assert word not in text, f"{path.name} mentions {word!r}"
