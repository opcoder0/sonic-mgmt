"""Policy helpers for dynamic skip-expiry priority handling."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import EscalationDecision, ExpiryConfig, TimelineStage

ISO8601_Z_SUFFIX = "Z"


def priority_to_label(priority: int) -> str:
    """Generate the workflow label for a priority level."""
    return f"sonic-skip-wf-priority-{priority}"


def labels_for_levels(levels: list[int]) -> list[str]:
    """Generate label names for all discovered levels."""
    return [priority_to_label(level) for level in levels]


def parse_github_datetime(value: str) -> datetime:
    """Parse GitHub timestamps as UTC datetimes."""
    normalized = value
    if value.endswith(ISO8601_Z_SUFFIX):
        normalized = f"{value[:-1]}+00:00"
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def reconstruct_stage_from_timeline(
    timeline_events: list[dict],
    valid_labels: set[str],
) -> TimelineStage | None:
    """Recover current stage from most recent matching 'labeled' timeline event."""
    matches: list[tuple[datetime, str]] = []
    for event in timeline_events:
        if event.get("event") != "labeled":
            continue
        label_name = ((event.get("label") or {}).get("name") or "").strip()
        if label_name not in valid_labels:
            continue
        created_at = event.get("created_at")
        if not created_at:
            continue
        applied_at = parse_github_datetime(created_at)
        matches.append((applied_at, label_name))

    if not matches:
        return None

    applied_at, label_name = max(matches, key=lambda item: item[0])
    priority = int(label_name.rsplit("-", 1)[-1])
    return TimelineStage(priority=priority, label_name=label_name, applied_at=applied_at)


def next_priority_in_ladder(current_priority: int, ladder: list[int]) -> int | None:
    """Return the next stage priority from a descending ladder."""
    idx = ladder.index(current_priority)
    if idx + 1 >= len(ladder):
        return None
    return ladder[idx + 1]


def build_warning_marker(priority: int, warning_day: int) -> str:
    """Build deterministic marker for warning idempotency."""
    return f"<!-- sonic-skip-expiry-warning:p{priority}:w{warning_day} -->"


def build_close_marker(priority: int) -> str:
    """Build deterministic marker for close-comment idempotency."""
    return f"<!-- sonic-skip-expiry-close:p{priority} -->"


def build_auto_close_label(now_utc: datetime) -> str:
    """Build timestamped auto-close label name in ddmmyyyyhhmm format."""
    return f"skip-wf-auto-close-{now_utc.strftime('%d%m%Y%H%M')}"


def evaluate_escalation(
    stage: TimelineStage,
    config: ExpiryConfig,
    now_utc: datetime,
) -> EscalationDecision:
    """Evaluate whether stage should warn, escalate, or close."""
    threshold_days = config.expiry_days_by_priority[stage.priority]
    age_days = int((now_utc - stage.applied_at).total_seconds() // 86400)

    if age_days > threshold_days:
        next_priority = next_priority_in_ladder(stage.priority, config.ladder)
        return EscalationDecision(
            should_escalate=next_priority is not None,
            next_priority=next_priority,
            should_close=next_priority is None,
            age_days=age_days,
            threshold_days=threshold_days,
            warning_days_to_post=[],
        )

    remaining_days = threshold_days - age_days
    warning_days_to_post = [w for w in config.warning_days if remaining_days <= w]
    return EscalationDecision(
        should_escalate=False,
        next_priority=None,
        should_close=False,
        age_days=age_days,
        threshold_days=threshold_days,
        warning_days_to_post=warning_days_to_post,
    )
