"""CLI for sonic skip expiry workflow automation."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from .github_client import GitHubClient, GitHubClientError
from .logging_utils import configure_logging, log_summary
from .models import RunStats
from .policy import (
    build_auto_close_label,
    build_close_marker,
    build_warning_marker,
    evaluate_escalation,
    labels_for_levels,
    priority_to_label,
    reconstruct_stage_from_timeline,
)
from .validation import load_and_validate_expiry_config
from .yaml_scan import scan_condition_files

logger = logging.getLogger(__name__)

DEFAULT_CONDITIONAL_MARK_DIR = "tests/common/plugins/conditional_mark"
DEFAULT_EXPIRY_CONFIG = f"{DEFAULT_CONDITIONAL_MARK_DIR}/expiry_config.yml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="SONiC skip expiry workflow tool")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without mutating GitHub issues")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--max-issues", type=int, default=0, help="Limit number of issues processed")
    parser.add_argument("--only-repo", default="", help="Filter to a single repo slug owner/repo")
    parser.add_argument(
        "--conditional-mark-dir",
        default=DEFAULT_CONDITIONAL_MARK_DIR,
        help="Directory containing tests_mark_conditions_*.yml/.yaml files",
    )
    parser.add_argument(
        "--expiry-config",
        default=DEFAULT_EXPIRY_CONFIG,
        help="Path to expiry_config.yml",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    """Execute workflow and return process exit code."""
    args = parse_args(argv)
    configure_logging(args.verbose)

    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        logger.error("GITHUB_TOKEN environment variable is required")
        return 2

    try:
        config = load_and_validate_expiry_config(args.expiry_config)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to load/validate config: %s", exc)
        return 2

    issues, scan_stats = scan_condition_files(args.conditional_mark_dir)
    if args.only_repo:
        issues = [issue for issue in issues if issue.repo_slug.lower() == args.only_repo.lower()]
    if args.max_issues and args.max_issues > 0:
        issues = issues[: args.max_issues]

    stats = RunStats(
        yaml_files_scanned=scan_stats.yaml_files_scanned,
        tests_seen=scan_stats.tests_seen,
        temporary_tests_count=scan_stats.temporary_tests_count,
        permanent_tests_count=scan_stats.permanent_tests_count,
        unique_issues_count=len(issues),
        config_levels_discovered=config.ladder,
        ladder_string="->".join(str(level) for level in config.ladder),
    )

    client = GitHubClient(token=token, dry_run=args.dry_run)
    known_labels = set(labels_for_levels(config.ladder))
    start_label = priority_to_label(config.starting_priority)
    now_utc = datetime.now(timezone.utc)

    failures = 0

    for issue in issues:
        issue_tag = f"{issue.owner}/{issue.repo}#{issue.number}"
        try:
            issue_data = client.get_issue(issue.owner, issue.repo, issue.number)
            state = (issue_data.get("state") or "").lower()
            if state == "closed":
                logger.info("Issue %s already closed; skipping", issue_tag)
                continue

            timeline = client.list_issue_timeline(issue.owner, issue.repo, issue.number)
            stage = reconstruct_stage_from_timeline(timeline, known_labels)
            if stage is None:
                logger.info("Issue %s has no priority label history; applying %s", issue_tag, start_label)
                client.add_labels(issue.owner, issue.repo, issue.number, [start_label])
                stats.labels_added_count += 1
                continue

            logger.info(
                "Issue %s current stage from timeline: P%d applied_at=%s",
                issue_tag,
                stage.priority,
                stage.applied_at.isoformat(),
            )

            decision = evaluate_escalation(stage, config, now_utc)
            if decision.should_escalate and decision.next_priority is not None:
                next_label = priority_to_label(decision.next_priority)
                logger.info(
                    "Issue %s age_days=%d threshold=%d; escalating to %s",
                    issue_tag,
                    decision.age_days,
                    decision.threshold_days,
                    next_label,
                )
                client.add_labels(issue.owner, issue.repo, issue.number, [next_label])
                stats.labels_added_count += 1
                continue

            if decision.should_close:
                marker = build_close_marker(stage.priority)
                auto_close_label = build_auto_close_label(now_utc)
                close_body = (
                    "Closed by sonic skip expiry workflow tool because it has crossed all thresholds.\n\n"
                    f"{marker}"
                )
                comments = client.list_issue_comments(issue.owner, issue.repo, issue.number)
                if not any(marker in (c.get("body") or "") for c in comments):
                    client.create_comment(issue.owner, issue.repo, issue.number, close_body)
                client.add_labels(issue.owner, issue.repo, issue.number, [auto_close_label])
                stats.labels_added_count += 1
                client.close_issue(issue.owner, issue.repo, issue.number)
                stats.issues_closed_count += 1
                logger.info(
                    "Issue %s age_days=%d threshold=%d; closed at terminal stage P%d with label %s",
                    issue_tag,
                    decision.age_days,
                    decision.threshold_days,
                    stage.priority,
                    auto_close_label,
                )
                continue

            if decision.warning_days_to_post:
                comments = client.list_issue_comments(issue.owner, issue.repo, issue.number)
                for warning_day in decision.warning_days_to_post:
                    marker = build_warning_marker(stage.priority, warning_day)
                    if any(marker in (c.get("body") or "") for c in comments):
                        continue
                    body = (
                        f"Skip expiry warning: issue is within {warning_day} day(s) of expiry "
                        f"for priority P{stage.priority}.\n\n{marker}"
                    )
                    client.create_comment(issue.owner, issue.repo, issue.number, body)
                    stats.warnings_posted_count += 1

        except GitHubClientError as exc:
            failures += 1
            logger.error("GitHub API failure for %s: %s", issue_tag, exc)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            failures += 1
            logger.exception("Unexpected failure while processing %s: %s", issue_tag, exc)

    log_summary(stats)
    return 1 if failures else 0


def main() -> None:
    """CLI entrypoint."""
    sys.exit(run())


if __name__ == "__main__":
    main()
