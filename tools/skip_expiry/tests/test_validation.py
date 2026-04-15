"""Unit tests for expiry configuration validation."""

import pytest

from tools.skip_expiry.validation import validate_expiry_config_data


def test_discover_priority_levels_supports_sparse_levels() -> None:
    cfg = {
        "expiry_config": {
            "p4_label_expiry_days": 120,
            "p2_label_expiry_days": 60,
            "p0_label_expiry_days": 15,
            "warning_days": [30, 7, 14],
        }
    }

    validated = validate_expiry_config_data(cfg, "x.yml")

    assert validated.ladder == [4, 2, 0]
    assert validated.starting_priority == 4
    assert validated.terminal_priority == 0
    assert validated.warning_days == [30, 14, 7]


def test_missing_expiry_config_root_fails() -> None:
    with pytest.raises(ValueError, match="missing top-level key 'expiry_config'"):
        validate_expiry_config_data({}, "x.yml")


def test_no_priority_keys_fails() -> None:
    cfg = {"expiry_config": {"warning_days": [1]}}
    with pytest.raises(ValueError, match="no keys matched"):
        validate_expiry_config_data(cfg, "x.yml")


@pytest.mark.parametrize(
    "bad_value",
    [0, -1, "30", 1.2],
)
def test_invalid_expiry_types_or_non_positive_fail(bad_value) -> None:
    cfg = {"expiry_config": {"p1_label_expiry_days": bad_value}}
    with pytest.raises(ValueError, match="must be an integer > 0"):
        validate_expiry_config_data(cfg, "x.yml")


@pytest.mark.parametrize(
    "warning_days",
    ["1,2", [1, -1], [1, "2"]],
)
def test_warning_days_malformed_fails(warning_days) -> None:
    cfg = {
        "expiry_config": {
            "p1_label_expiry_days": 30,
            "warning_days": warning_days,
        }
    }
    with pytest.raises(ValueError, match="warning_days"):
        validate_expiry_config_data(cfg, "x.yml")


def test_single_level_supported() -> None:
    cfg = {"expiry_config": {"p0_label_expiry_days": 10}}
    validated = validate_expiry_config_data(cfg, "x.yml")
    assert validated.ladder == [0]
