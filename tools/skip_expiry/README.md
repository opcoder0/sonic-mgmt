# SONiC Skip Expiry Workflow Tool

This tool enforces skip-expiry lifecycle rules on GitHub issues referenced by `skip:` clauses in conditional mark files.

## What It Does

1. Scans YAMLs under `tests/common/plugins/conditional_mark/`:
   - `tests_mark_conditions_*.yml`
   - `tests_mark_conditions_*.yaml`
2. For test entries that include `skip:`:
   - classifies as temporary if a GitHub issue URL is present
   - classifies as permanent otherwise
3. Deduplicates issue URLs and evaluates each OPEN issue against priority-label expiry policy.
4. Reconstructs the stage from issue timeline `labeled` events for workflow labels.
5. Adds labels, posts warning comments idempotently, escalates, and closes terminally expired issues.

When an issue is terminally expired and closed, the tool also applies a timestamped label:

- `skip-wf-auto-close-<ddmmyyyyhhmm>`

This gives a visible audit trail for every workflow-driven auto-close event.

## Required GitHub Permissions

Use token with:

- `contents: read`
- `issues: write`

## Run Locally

Set a PAT or GitHub token:

```bash
export GITHUB_TOKEN=<token>
python -m tools.skip_expiry.main --verbose --dry-run
```

Useful options:

- `--dry-run`: no mutations, only logs intended actions
- `--verbose`: debug-level logs
- `--max-issues N`: process only first N deduped issues
- `--only-repo owner/repo`: process issue refs only for one repository

## Dynamic Priority Ladder

The tool parses `tests/common/plugins/conditional_mark/expiry_config.yml` and discovers keys matching:

- `^p(\d+)_label_expiry_days$`

Then it:

- extracts priority numbers dynamically
- sorts descending to build ladder (start to terminal), e.g. `4 -> 2 -> 0`
- derives labels as `sonic-skip-wf-priority-{N}`

No assumptions are made about fixed levels like `P3/P2/P1/P0`.

## Diagnostics Printed at Startup

The validation phase logs:

- loaded config path
- discovered expiry levels and original keys
- extracted priority list
- computed ladder and start/terminal priorities
- derived labels
- thresholds per priority
- warning days

Validation failures stop execution with non-zero exit.

## End-of-Run Summary

A one-line summary includes:

- `yaml_files_scanned`
- `tests_seen`
- `temporary_tests_count`
- `permanent_tests_count`
- `unique_issues_count`
- `labels_added_count`
- `issues_closed_count`
- `warnings_posted_count`
- `config_levels_discovered`
- `ladder_string`
