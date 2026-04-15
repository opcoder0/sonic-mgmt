"""Dataclasses for the skip expiry workflow tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class IssueRef:
    """A GitHub issue reference parsed from mark-condition files."""

    url: str
    owner: str
    repo: str
    number: int

    @property
    def repo_slug(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class ExpiryConfig:
    """Validated and normalized expiry configuration."""

    source_path: str
    discovered_keys: list[str]
    expiry_days_by_priority: dict[int, int]
    warning_days: list[int]
    duplicate_keys: list[str] = field(default_factory=list)

    @property
    def ladder(self) -> list[int]:
        return sorted(self.expiry_days_by_priority.keys(), reverse=True)

    @property
    def starting_priority(self) -> int:
        return self.ladder[0]

    @property
    def terminal_priority(self) -> int:
        return self.ladder[-1]


@dataclass(frozen=True)
class TimelineStage:
    """Most recent relevant stage reconstructed from timeline events."""

    priority: int
    label_name: str
    applied_at: datetime


@dataclass
class ScanStats:
    """Statistics from YAML mark-condition scanning."""

    yaml_files_scanned: int = 0
    tests_seen: int = 0
    temporary_tests_count: int = 0
    permanent_tests_count: int = 0


@dataclass
class RunStats:
    """End-of-run counters for reporting."""

    yaml_files_scanned: int = 0
    tests_seen: int = 0
    temporary_tests_count: int = 0
    permanent_tests_count: int = 0
    unique_issues_count: int = 0
    labels_added_count: int = 0
    issues_closed_count: int = 0
    warnings_posted_count: int = 0
    config_levels_discovered: list[int] = field(default_factory=list)
    ladder_string: str = ""


@dataclass(frozen=True)
class EscalationDecision:
    """Decision for the current stage."""

    should_escalate: bool
    next_priority: int | None
    should_close: bool
    age_days: int
    threshold_days: int
    warning_days_to_post: list[int]
