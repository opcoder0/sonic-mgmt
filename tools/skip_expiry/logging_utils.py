"""Logging helpers for skip expiry workflow tool."""

from __future__ import annotations

import logging
import sys

from .models import RunStats


def configure_logging(verbose: bool) -> None:
    """Configure process-wide logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def log_summary(stats: RunStats) -> None:
    """Emit a one-line machine-friendly summary."""
    logger = logging.getLogger("skip_expiry.summary")
    logger.info(
        "summary "
        "yaml_files_scanned=%d tests_seen=%d temporary_tests_count=%d permanent_tests_count=%d "
        "unique_issues_count=%d labels_added_count=%d issues_closed_count=%d warnings_posted_count=%d "
        "config_levels_discovered=%s ladder_string=%s",
        stats.yaml_files_scanned,
        stats.tests_seen,
        stats.temporary_tests_count,
        stats.permanent_tests_count,
        stats.unique_issues_count,
        stats.labels_added_count,
        stats.issues_closed_count,
        stats.warnings_posted_count,
        stats.config_levels_discovered,
        stats.ladder_string,
    )
