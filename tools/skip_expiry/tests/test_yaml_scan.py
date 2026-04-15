"""Unit tests for YAML scan helpers."""

from tools.skip_expiry.yaml_scan import parse_issue_urls


def test_parse_issue_urls_extracts_multiple() -> None:
    text = (
        "skip because https://github.com/sonic-net/sonic-mgmt/issues/123 "
        "and https://github.com/org/repo-name/issues/45"
    )

    refs = parse_issue_urls(text)

    assert [r.url for r in refs] == [
        "https://github.com/sonic-net/sonic-mgmt/issues/123",
        "https://github.com/org/repo-name/issues/45",
    ]
    assert refs[0].owner == "sonic-net"
    assert refs[0].repo == "sonic-mgmt"
    assert refs[0].number == 123


def test_parse_issue_urls_ignores_non_issue_urls() -> None:
    text = "see https://github.com/sonic-net/sonic-mgmt/pull/1 and random text"
    assert parse_issue_urls(text) == []
