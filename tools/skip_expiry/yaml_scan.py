"""Scan conditional mark YAMLs and extract temporary skip issue references."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .models import IssueRef, ScanStats

logger = logging.getLogger(__name__)
GITHUB_ISSUE_RE = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/(\d+)\b")


def scan_condition_files(base_dir: str) -> tuple[list[IssueRef], ScanStats]:
    """Scan condition YAMLs and return deduplicated issue references and stats."""
    base = Path(base_dir)
    patterns = ["tests_mark_conditions_*.yml", "tests_mark_conditions_*.yaml"]
    files = sorted({file for pattern in patterns for file in base.glob(pattern)})
    stats = ScanStats(yaml_files_scanned=len(files))

    unique_issues: dict[str, IssueRef] = {}

    for file_path in files:
        file_issues, file_stats = _scan_single_file(file_path)
        stats.tests_seen += file_stats.tests_seen
        stats.temporary_tests_count += file_stats.temporary_tests_count
        stats.permanent_tests_count += file_stats.permanent_tests_count
        for issue in file_issues:
            unique_issues[issue.url] = issue

    return sorted(unique_issues.values(), key=lambda issue: issue.url), stats


def parse_issue_urls(text: str) -> list[IssueRef]:
    """Extract GitHub issue references from free-form text."""
    refs = []
    for owner, repo, number in GITHUB_ISSUE_RE.findall(text):
        url = f"https://github.com/{owner}/{repo}/issues/{number}"
        refs.append(IssueRef(url=url, owner=owner, repo=repo, number=int(number)))
    return refs


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)


def _scan_single_file(file_path: Path) -> tuple[list[IssueRef], ScanStats]:
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        logger.warning("Skipping non-mapping YAML file: %s", file_path)
        return [], ScanStats()

    stats = ScanStats()
    issues: dict[str, IssueRef] = {}

    for _, marks in data.items():
        stats.tests_seen += 1
        if not isinstance(marks, dict):
            continue
        skip_cfg = marks.get("skip")
        if skip_cfg is None:
            continue

        serialized = "\n".join(_iter_strings(skip_cfg))
        parsed = parse_issue_urls(serialized)
        if parsed:
            stats.temporary_tests_count += 1
            for issue in parsed:
                issues[issue.url] = issue
        else:
            stats.permanent_tests_count += 1

    return list(issues.values()), stats
