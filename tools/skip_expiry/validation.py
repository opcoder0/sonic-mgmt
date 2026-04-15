"""Configuration validation and diagnostics for skip expiry workflow."""

from __future__ import annotations

import logging
import re
from typing import Any

import yaml

from .models import ExpiryConfig
from .policy import labels_for_levels

logger = logging.getLogger(__name__)
PRIORITY_KEY_RE = re.compile(r"^p(\d+)_label_expiry_days$")


class DuplicateKeyLoader(yaml.SafeLoader):
    """YAML loader that records duplicate keys."""

    def __init__(self, stream):
        super().__init__(stream)
        self.duplicate_keys: list[str] = []


def _construct_mapping(loader: DuplicateKeyLoader, node, deep=False):
    mapping = {}
    seen_keys = set()
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen_keys:
            loader.duplicate_keys.append(str(key))
        seen_keys.add(key)
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


DuplicateKeyLoader.add_constructor(  # pylint: disable=no-member
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _fail(path: str, message: str) -> None:
    raise ValueError(f"Invalid expiry config in {path}: {message}")


def discover_priority_expiry(data: dict[str, Any], path: str) -> tuple[list[str], dict[int, int]]:
    """Find keys matching pN_label_expiry_days and validate values."""
    discovered_keys: list[str] = []
    expiry_days_by_priority: dict[int, int] = {}

    for key, value in data.items():
        m = PRIORITY_KEY_RE.match(str(key))
        if not m:
            continue
        discovered_keys.append(str(key))
        priority = int(m.group(1))
        if not isinstance(value, int) or value <= 0:
            _fail(path, f"{key} must be an integer > 0, got {value!r}")
        expiry_days_by_priority[priority] = value

    if not discovered_keys:
        _fail(path, "no keys matched ^p(\\d+)_label_expiry_days$")

    return discovered_keys, expiry_days_by_priority


def validate_expiry_config_data(config_data: dict[str, Any],
                                path: str, duplicate_keys: list[str] | None = None) -> ExpiryConfig:
    """Validate parsed config dictionary and return normalized ExpiryConfig."""
    if "expiry_config" not in config_data:
        _fail(path, "missing top-level key 'expiry_config'")

    expiry_config = config_data["expiry_config"]
    if not isinstance(expiry_config, dict):
        _fail(path, "'expiry_config' must be a mapping")

    discovered_keys, expiry_days_by_priority = discover_priority_expiry(expiry_config, path)

    warning_days_raw = expiry_config.get("warning_days", [])
    if warning_days_raw is None:
        warning_days_raw = []
    if not isinstance(warning_days_raw, list):
        _fail(path, "warning_days must be a list of integers >= 0")
    if not all(isinstance(day, int) and day >= 0 for day in warning_days_raw):
        _fail(path, f"warning_days must contain only integers >= 0, got {warning_days_raw!r}")

    warning_days_sorted = sorted(warning_days_raw, reverse=True)
    if warning_days_raw != warning_days_sorted:
        logger.warning("warning_days is not sorted, using sorted order: %s", warning_days_sorted)

    for priority, threshold in expiry_days_by_priority.items():
        for warning_day in warning_days_sorted:
            if warning_day >= threshold:
                logger.warning(
                    "warning_days contains %d which is >= expiry threshold %d for P%d",
                    warning_day,
                    threshold,
                    priority,
                )

    duplicate_keys = duplicate_keys or []
    if duplicate_keys:
        logger.warning("Duplicate YAML keys detected (effective values kept from last occurrence): %s", duplicate_keys)

    return ExpiryConfig(
        source_path=path,
        discovered_keys=discovered_keys,
        expiry_days_by_priority=expiry_days_by_priority,
        warning_days=warning_days_sorted,
        duplicate_keys=duplicate_keys,
    )


def load_and_validate_expiry_config(path: str) -> ExpiryConfig:
    """Load expiry YAML config from file path and validate it."""
    with open(path, "r", encoding="utf-8") as f:
        loader = DuplicateKeyLoader(f)
        raw_data = loader.get_single_data()
        duplicate_keys = loader.duplicate_keys

    if raw_data is None:
        _fail(path, "empty file")
    if not isinstance(raw_data, dict):
        _fail(path, "top-level content must be a mapping")

    config = validate_expiry_config_data(raw_data, path, duplicate_keys=duplicate_keys)
    _print_diagnostics(config)
    return config


def _print_diagnostics(config: ExpiryConfig) -> None:
    levels = config.ladder
    labels = labels_for_levels(levels)
    thresholds = ", ".join(f"P{level}={config.expiry_days_by_priority[level]}" for level in levels)
    ladder_str = " -> ".join(str(level) for level in levels)
    discovered_levels = ",".join(f"P{level}" for level in levels)

    logger.info("Loaded expiry config from: %s", config.source_path)
    logger.info("Discovered expiry levels: %s", discovered_levels)
    logger.info("Discovered expiry keys: %s", ",".join(config.discovered_keys))
    logger.info("Extracted priority list: %s", levels)
    logger.info("Computed ladder (start->end): %s", ladder_str)
    logger.info("Starting priority: %s, terminal priority: %s", config.starting_priority, config.terminal_priority)
    logger.info("Label set: %s", ", ".join(labels))
    logger.info("Thresholds(days): %s", thresholds)
    logger.info("Warning days: %s", config.warning_days)
