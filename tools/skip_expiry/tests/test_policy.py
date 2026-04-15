"""Unit tests for skip expiry policy logic."""

from datetime import datetime, timedelta, timezone

from tools.skip_expiry.models import ExpiryConfig, TimelineStage
from tools.skip_expiry.policy import (
    build_auto_close_label,
    evaluate_escalation,
    labels_for_levels,
    reconstruct_stage_from_timeline,
)


def _config() -> ExpiryConfig:
    return ExpiryConfig(
        source_path="x",
        discovered_keys=["p4_label_expiry_days", "p2_label_expiry_days", "p0_label_expiry_days"],
        expiry_days_by_priority={4: 120, 2: 60, 0: 15},
        warning_days=[30, 14, 7],
    )


def test_labels_for_levels_dynamic() -> None:
    assert labels_for_levels([4, 2, 0]) == [
        "sonic-skip-wf-priority-4",
        "sonic-skip-wf-priority-2",
        "sonic-skip-wf-priority-0",
    ]


def test_reconstruct_stage_uses_most_recent_labeled_event() -> None:
    timeline = [
        {
            "event": "labeled",
            "created_at": "2026-01-01T00:00:00Z",
            "label": {"name": "sonic-skip-wf-priority-4"},
        },
        {
            "event": "unlabeled",
            "created_at": "2026-01-02T00:00:00Z",
            "label": {"name": "sonic-skip-wf-priority-4"},
        },
        {
            "event": "labeled",
            "created_at": "2026-01-03T00:00:00Z",
            "label": {"name": "sonic-skip-wf-priority-2"},
        },
    ]
    valid_labels = {
        "sonic-skip-wf-priority-4",
        "sonic-skip-wf-priority-2",
        "sonic-skip-wf-priority-0",
    }

    stage = reconstruct_stage_from_timeline(timeline, valid_labels)

    assert stage is not None
    assert stage.priority == 2
    assert stage.label_name == "sonic-skip-wf-priority-2"


def test_escalation_across_sparse_ladder() -> None:
    cfg = _config()
    now = datetime(2026, 4, 14, tzinfo=timezone.utc)
    stage = TimelineStage(
        priority=4,
        label_name="sonic-skip-wf-priority-4",
        applied_at=now - timedelta(days=121),
    )

    decision = evaluate_escalation(stage, cfg, now)

    assert decision.should_escalate is True
    assert decision.next_priority == 2
    assert decision.should_close is False


def test_terminal_priority_closes_when_expired() -> None:
    cfg = _config()
    now = datetime(2026, 4, 14, tzinfo=timezone.utc)
    stage = TimelineStage(
        priority=0,
        label_name="sonic-skip-wf-priority-0",
        applied_at=now - timedelta(days=16),
    )

    decision = evaluate_escalation(stage, cfg, now)

    assert decision.should_close is True
    assert decision.should_escalate is False
    assert decision.next_priority is None


def test_warning_days_generated_within_threshold() -> None:
    cfg = _config()
    now = datetime(2026, 4, 14, tzinfo=timezone.utc)
    stage = TimelineStage(
        priority=2,
        label_name="sonic-skip-wf-priority-2",
        applied_at=now - timedelta(days=49),
    )

    decision = evaluate_escalation(stage, cfg, now)

    assert decision.should_close is False
    assert decision.should_escalate is False
    assert decision.threshold_days == 60
    assert decision.warning_days_to_post == [30, 14, 7]


def test_build_auto_close_label_format() -> None:
    now = datetime(2026, 4, 15, 13, 45, tzinfo=timezone.utc)
    assert build_auto_close_label(now) == "skip-wf-auto-close-150420261345"
