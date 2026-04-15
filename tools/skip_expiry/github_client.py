"""Minimal GitHub REST client for skip expiry workflow."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class GitHubClientError(RuntimeError):
    """Raised when GitHub REST calls fail unexpectedly."""


class GitHubClient:
    """Thin GitHub API wrapper with pagination and dry-run support."""

    def __init__(self, token: str, dry_run: bool = False, timeout_sec: int = 30) -> None:
        self.token = token
        self.dry_run = dry_run
        self.timeout_sec = timeout_sec
        self.base = "https://api.github.com"

    def get_issue(self, owner: str, repo: str, issue_number: int) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")

    def list_issue_timeline(self, owner: str, repo: str, issue_number: int) -> list[dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/timeline"
        return self._request_paginated("GET", path)

    def list_issue_comments(self, owner: str, repo: str, issue_number: int) -> list[dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        return self._request_paginated("GET", path)

    def add_labels(self, owner: str, repo: str, issue_number: int, labels: list[str]) -> None:
        if self.dry_run:
            logger.info("[dry-run] would add labels %s on %s/%s#%s", labels, owner, repo, issue_number)
            return
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/labels"
        self._request_json("POST", path, payload={"labels": labels})

    def create_comment(self, owner: str, repo: str, issue_number: int, body: str) -> None:
        if self.dry_run:
            logger.info("[dry-run] would comment on %s/%s#%s: %s", owner, repo, issue_number, body)
            return
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        self._request_json("POST", path, payload={"body": body})

    def close_issue(self, owner: str, repo: str, issue_number: int) -> None:
        if self.dry_run:
            logger.info("[dry-run] would close %s/%s#%s", owner, repo, issue_number)
            return
        path = f"/repos/{owner}/{repo}/issues/{issue_number}"
        self._request_json("PATCH", path, payload={"state": "closed"})

    def _request_paginated(self, method: str, path: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url = self._build_url(path, {"per_page": "100", "page": "1"})
        while next_url:
            body, headers = self._request(method, next_url)
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, list):
                raise GitHubClientError(f"Expected list payload for {next_url}, got {type(payload)}")
            items.extend(payload)
            next_url = _parse_next_link(headers.get("Link", ""))
        return items

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._build_url(path)
        body, _ = self._request(method, url, payload=payload)
        decoded = json.loads(body.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise GitHubClientError(f"Expected dict payload for {url}, got {type(decoded)}")
        return decoded

    def _request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[bytes, dict[str, str]]:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        request = Request(url=url, method=method, data=data)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if payload is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with urlopen(request, timeout=self.timeout_sec) as resp:  # nosec B310
                return resp.read(), dict(resp.headers.items())
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GitHubClientError(f"GitHub API HTTP {exc.code} for {url}: {body}") from exc
        except URLError as exc:
            raise GitHubClientError(f"GitHub API error for {url}: {exc}") from exc

    def _build_url(self, path: str, query: dict[str, str] | None = None) -> str:
        base = f"{self.base}{path}"
        if not query:
            return base
        return f"{base}?{urlencode(query)}"


def _parse_next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url_part = section[0].strip()
        rel_part = section[1].strip()
        if rel_part != 'rel="next"':
            continue
        if url_part.startswith("<") and url_part.endswith(">"):
            return url_part[1:-1]
    return None


def is_github_issue_url(url: str) -> bool:
    """Return whether URL points to a GitHub issue."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc != "github.com":
        return False
    parts = [part for part in parsed.path.split("/") if part]
    return len(parts) >= 4 and parts[2] == "issues" and parts[3].isdigit()
