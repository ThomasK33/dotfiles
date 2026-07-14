#!/usr/bin/env python3
"""Workspace-local helper for the Mux issue implementation loop.

This script intentionally handles deterministic plumbing only: GitHub fetching,
ledger summarization/pruning, issue/PR state normalization, and action-candidate
calculation. It does not launch Mux workspaces, archive workspaces, post comments,
or make semantic dependency decisions.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

STATE_DIR = Path(".mux/issue-implementation-loop")
LEDGER_PATH = STATE_DIR / "ledger.json"
REQUIRED_LABELS = ["triage:done", "accepted", "needs-triage", "blocked"]
TERMINAL_STATES = {"done"}
ACTIVE_STATES = {"created", "running", "pr-open", "blocked", "paused", "stale", "conflict"}
DEPENDENCY_KEYWORDS = [
    "depends on",
    "dependent on",
    "blocked by",
    "requires",
    "prerequisite",
    "prerequisites",
    "after",
    "wait for",
    "must land after",
]

CLOSING_RE = re.compile(
    r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+"
    r"(?:(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#)(\d+)\b"
)
ISSUE_REF_RE = re.compile(r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#(\d+)\b")
IMPLEMENT_BRANCH_RE = re.compile(r"(?i)(?:^|[-_/])(?:implement[-_]issue|issue)[-_]?(\d+)(?:$|[-_/])")


class CommandError(RuntimeError):
    def __init__(self, command: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"command failed ({returncode}): {' '.join(command)}\n{stderr.strip()}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    assert command, "command must not be empty"
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and completed.returncode != 0:
        raise CommandError(command, completed.returncode, completed.stdout, completed.stderr)
    return completed


def run_json(command: list[str]) -> Any:
    completed = run(command)
    try:
        return json.loads(completed.stdout or "null")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command did not return valid JSON: {' '.join(command)}") from exc


def repo_root() -> Path:
    return Path(run(["git", "rev-parse", "--show-toplevel"]).stdout.strip())


def git_path(path: str) -> Path:
    assert path, "path must not be empty"
    return Path(run(["git", "rev-parse", "--git-path", path]).stdout.strip())


def default_repo() -> dict[str, Any]:
    repo = run_json(["gh", "repo", "view", "--json", "nameWithOwner,defaultBranchRef"])
    assert isinstance(repo, dict), "gh repo view JSON must be an object"
    assert isinstance(repo.get("nameWithOwner"), str) and repo["nameWithOwner"], "repo name missing"
    return repo


def read_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "records": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ledger is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"ledger must be a JSON object: {path}")
    records = data.get("records")
    if records is None:
        # Backward-compatible support for an old unwrapped target->record object.
        if all(isinstance(v, dict) for v in data.values()):
            return {"version": 1, "records": data}
        raise RuntimeError("ledger missing records object")
    if not isinstance(records, dict):
        raise RuntimeError("ledger.records must be an object")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    assert path.parent.exists(), f"parent directory does not exist: {path.parent}"
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def label_names(labels: list[dict[str, Any]] | None) -> list[str]:
    if not labels:
        return []
    return sorted(str(label.get("name")) for label in labels if label.get("name"))


def normalize_assignees(assignees: list[dict[str, Any]] | None) -> list[str]:
    if not assignees:
        return []
    return sorted(str(assignee.get("login")) for assignee in assignees if assignee.get("login"))


def parse_issue_number_from_target(target: str) -> int | None:
    match = re.search(r"#(\d+)\s*$", target)
    return int(match.group(1)) if match else None


def parse_pr_number(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        match = re.search(r"/pull/(\d+)(?:\b|$)", value)
        if match:
            return int(match.group(1))
    return None


def has_workspace_ref(record: dict[str, Any]) -> bool:
    return bool(record.get("workspaceId") or record.get("taskId"))


def ensure_exclude_entry(state_dir: Path, *, apply: bool) -> dict[str, Any]:
    exclude = git_path("info/exclude")
    entry = str(state_dir).rstrip("/") + "/"
    text = exclude.read_text() if exclude.exists() else ""
    present = entry in text.splitlines() or entry in text
    changed = False
    if not present and apply:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not text or text.endswith("\n") else "\n"
        with exclude.open("a") as handle:
            handle.write(f"{prefix}{entry}\n")
        changed = True
        text = exclude.read_text()
        present = entry in text
    return {
        "path": str(exclude),
        "entry": entry,
        "present": present,
        "changed": changed,
        "apply": apply,
    }


def fetch_origin_main(default_branch: str, *, do_fetch: bool) -> dict[str, Any]:
    assert default_branch, "default branch must not be empty"
    if do_fetch:
        run(["git", "fetch", "--prune", "origin", default_branch])
    origin_ref = f"origin/{default_branch}"
    origin_main = run(["git", "rev-parse", origin_ref]).stdout.strip()
    local_head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = run(["git", "branch", "--show-current"], check=False).stdout.strip()
    return {
        "fetched": do_fetch,
        "defaultBranch": default_branch,
        "originRef": origin_ref,
        "originHead": origin_main,
        "localHead": local_head,
        "localBranch": branch,
    }


def fetch_labels(repo: str) -> dict[str, Any]:
    labels = run_json([
        "gh",
        "label",
        "list",
        "--repo",
        repo,
        "--json",
        "name,color,description",
        "--limit",
        "300",
    ])
    if not isinstance(labels, list):
        raise RuntimeError("gh label list JSON must be an array")
    by_name = {label.get("name"): label for label in labels if isinstance(label, dict)}
    required = {}
    missing = []
    for name in REQUIRED_LABELS:
        label = by_name.get(name)
        required[name] = {
            "present": bool(label),
            "color": label.get("color") if label else None,
            "description": label.get("description") if label else None,
        }
        if not label:
            missing.append(name)
    return {"total": len(labels), "required": required, "missing": missing}


def fetch_issues(repo: str) -> dict[str, Any]:
    base_fields = "number,title,state,labels,assignees,updatedAt,url"
    eligible = run_json([
        "gh", "issue", "list", "--repo", repo, "--state", "open",
        "--label", "triage:done", "--label", "accepted", "--json", base_fields, "--limit", "200",
    ])
    triage_done = run_json([
        "gh", "issue", "list", "--repo", repo, "--state", "open",
        "--label", "triage:done", "--json", base_fields, "--limit", "200",
    ])
    blocked = run_json([
        "gh", "issue", "list", "--repo", repo, "--state", "open",
        "--label", "blocked", "--json", base_fields, "--limit", "100",
    ])
    for value, name in [(eligible, "eligible issues"), (triage_done, "triage:done issues"), (blocked, "blocked issues")]:
        if not isinstance(value, list):
            raise RuntimeError(f"{name} JSON must be an array")
    eligible_numbers = {issue.get("number") for issue in eligible}
    missing_accepted = [
        issue for issue in triage_done
        if "accepted" not in label_names(issue.get("labels"))
    ]
    return {
        "eligible": [normalize_issue(issue) for issue in eligible],
        "triageDoneMissingAccepted": [normalize_issue(issue) for issue in missing_accepted],
        "blocked": [normalize_issue(issue) for issue in blocked],
        "eligibleNumbers": sorted(number for number in eligible_numbers if isinstance(number, int)),
    }


def normalize_issue(issue: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "labels": label_names(issue.get("labels")),
        "assignees": normalize_assignees(issue.get("assignees")),
        "updatedAt": issue.get("updatedAt"),
        "url": issue.get("url"),
    }


def normalize_status_checks(checks: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not checks:
        return {"total": 0, "visibleFailures": [], "checks": []}
    normalized = []
    failures = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name") or check.get("context") or check.get("workflowName") or check.get("__typename")
        state = check.get("state") or check.get("conclusion") or check.get("status")
        item = {"name": name, "state": state}
        normalized.append(item)
        if str(state).upper() in {"FAILURE", "FAILED", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}:
            failures.append(item)
    return {"total": len(normalized), "visibleFailures": failures, "checks": normalized}


def fetch_open_prs(repo: str, *, include_body: bool) -> list[dict[str, Any]]:
    fields = "number,title,headRefName,baseRefName,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,updatedAt,url,author"
    if include_body:
        fields += ",body"
    prs = run_json([
        "gh", "pr", "list", "--repo", repo, "--state", "open", "--json", fields, "--limit", "100",
    ])
    if not isinstance(prs, list):
        raise RuntimeError("gh pr list JSON must be an array")
    return [normalize_open_pr(pr, include_body=include_body) for pr in prs]


def normalize_open_pr(pr: dict[str, Any], *, include_body: bool) -> dict[str, Any]:
    checks = normalize_status_checks(pr.get("statusCheckRollup"))
    result = {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "headRefName": pr.get("headRefName"),
        "baseRefName": pr.get("baseRefName"),
        "isDraft": pr.get("isDraft"),
        "mergeStateStatus": pr.get("mergeStateStatus"),
        "reviewDecision": pr.get("reviewDecision"),
        "updatedAt": pr.get("updatedAt"),
        "url": pr.get("url"),
        "author": (pr.get("author") or {}).get("login") if isinstance(pr.get("author"), dict) else None,
        "statusChecks": checks,
    }
    if include_body:
        result["body"] = pr.get("body") or ""
    return result


def detect_pr_issue_links(prs: list[dict[str, Any]], repo: str) -> dict[str, Any]:
    by_issue: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for pr in prs:
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        branch = pr.get("headRefName") or ""
        evidence: dict[int, list[dict[str, Any]]] = collections.defaultdict(list)
        for match in CLOSING_RE.finditer(f"{title}\n{body}"):
            issue = int(match.group(1))
            evidence[issue].append({"kind": "closing-keyword", "confidence": "high", "text": match.group(0)[:120]})
        for match in IMPLEMENT_BRANCH_RE.finditer(branch):
            issue = int(match.group(1))
            evidence[issue].append({"kind": "branch-name", "confidence": "high", "text": branch})
        for match in ISSUE_REF_RE.finditer(f"{title}\n{body}"):
            issue = int(match.group(1))
            if not any(item["kind"] == "closing-keyword" for item in evidence[issue]):
                evidence[issue].append({"kind": "issue-reference", "confidence": "medium", "text": match.group(0)})
        for issue, items in evidence.items():
            confidence = "high" if any(item["confidence"] == "high" for item in items) else "medium"
            by_issue[str(issue)].append({
                "prNumber": pr.get("number"),
                "url": pr.get("url"),
                "title": pr.get("title"),
                "headRefName": pr.get("headRefName"),
                "mergeStateStatus": pr.get("mergeStateStatus"),
                "confidence": confidence,
                "evidence": items[:5],
            })
    return {"repo": repo, "issueToOpenPRs": dict(sorted(by_issue.items(), key=lambda item: int(item[0])))}



def target_sort_key(target: str) -> tuple[int, str]:
    issue = parse_issue_number_from_target(target)
    if issue is None:
        return (sys.maxsize, target)
    return (issue, target)


def compact_excerpt(text: str, *, limit: int = 240) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"


def fetch_dependency_hints(repo: str, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract explicit dependency-looking references for agent review.

    These are deliberately hints, not scheduling decisions. GitHub text is
    untrusted evidence and can contain casual references that are not blockers.
    """
    hints: list[dict[str, Any]] = []
    for issue in issues:
        number = issue.get("number")
        if not isinstance(number, int):
            continue
        details = run_json([
            "gh",
            "issue",
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            "number,title,body,comments,url",
        ])
        if not isinstance(details, dict):
            raise RuntimeError(f"issue #{number} detail JSON must be an object")
        chunks: list[tuple[str, str]] = [("body", details.get("body") or "")]
        for index, comment in enumerate(details.get("comments") or [], start=1):
            if isinstance(comment, dict):
                chunks.append((f"comment-{index}", comment.get("body") or ""))
        for source, text in chunks:
            lowered = text.lower()
            for match in ISSUE_REF_RE.finditer(text):
                referenced = int(match.group(1))
                window_start = max(0, match.start() - 120)
                window_end = min(len(text), match.end() + 120)
                window = text[window_start:window_end]
                keyword_hits = [keyword for keyword in DEPENDENCY_KEYWORDS if keyword in lowered[max(0, match.start() - 120): min(len(text), match.end() + 120)].lower()]
                if not keyword_hits:
                    continue
                hints.append({
                    "target": f"{repo}#{number}",
                    "issue": number,
                    "referenced": referenced,
                    "referencedTarget": f"{repo}#{referenced}",
                    "source": source,
                    "kind": "explicit-dependency-hint",
                    "confidence": "medium",
                    "keywords": keyword_hits,
                    "evidence": compact_excerpt(window),
                    "requiresAgenticJudgment": True,
                })
    return hints

def load_tasks(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"provided": False, "tasks": [], "byIssue": {}}
    data = json.loads(path.read_text())
    tasks = data.get("tasks", data if isinstance(data, list) else [])
    if not isinstance(tasks, list):
        raise RuntimeError("tasks JSON must be an array or an object with a tasks array")
    by_issue: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for task in tasks:
        if not isinstance(task, dict):
            continue
        text = " ".join(str(task.get(key, "")) for key in ["title", "name", "branchName", "workspaceTitle"])
        for match in ISSUE_REF_RE.finditer(text):
            by_issue[match.group(1)].append(task)
        for match in IMPLEMENT_BRANCH_RE.finditer(text):
            by_issue[match.group(1)].append(task)
    return {"provided": True, "tasks": tasks, "byIssue": dict(by_issue)}


def ledger_summary(ledger: dict[str, Any]) -> dict[str, Any]:
    records = ledger.get("records", {})
    assert isinstance(records, dict), "records must be a dictionary"
    states = collections.Counter(str(record.get("state")) for record in records.values() if isinstance(record, dict))
    archived = collections.Counter(str(record.get("archived")) for record in records.values() if isinstance(record, dict))
    active_like = []
    terminal_unarchived = []
    pruneable = []
    for target, record in sorted(records.items()):
        if not isinstance(record, dict):
            continue
        state = record.get("state")
        has_ref = has_workspace_ref(record)
        summary = summarize_record(target, record)
        if state in ACTIVE_STATES and not record.get("archived"):
            active_like.append(summary)
        if state in TERMINAL_STATES and has_ref and not record.get("archived"):
            terminal_unarchived.append(summary)
        if state == "done" and (record.get("archived") is True or not has_ref):
            pruneable.append(summary)
    return {
        "version": ledger.get("version"),
        "recordCount": len(records),
        "states": dict(states),
        "archived": dict(archived),
        "activeLikeRecords": active_like,
        "terminalUnarchivedRecords": terminal_unarchived,
        "pruneableDoneRecords": pruneable,
    }


def summarize_record(target: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "target": target,
        "issue": record.get("issue") or parse_issue_number_from_target(target),
        "state": record.get("state"),
        "eligible": record.get("eligible"),
        "archived": record.get("archived"),
        "workspaceId": record.get("workspaceId"),
        "taskId": record.get("taskId"),
        "prNumber": record.get("prNumber") or parse_pr_number(record.get("prUrl")),
        "prUrl": record.get("prUrl"),
        "updatedAt": record.get("updatedAt"),
    }


def compute_action_candidates(
    *,
    repo: str,
    ledger: dict[str, Any],
    issues: dict[str, Any],
    pr_links: dict[str, Any],
    tasks: dict[str, Any],
) -> dict[str, Any]:
    records = ledger.get("records", {})
    active_targets_by_issue: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    archive_candidates = []
    attention = []
    for target, record in records.items():
        if not isinstance(record, dict):
            attention.append({"target": target, "reason": "ledger record is not an object"})
            continue
        issue_number = record.get("issue") or parse_issue_number_from_target(target)
        issue_key = str(issue_number) if issue_number is not None else None
        if record.get("state") in ACTIVE_STATES and not record.get("archived") and issue_key:
            active_targets_by_issue[issue_key].append(summarize_record(target, record))
        if record.get("state") == "done" and has_workspace_ref(record) and not record.get("archived"):
            archive_candidates.append({
                **summarize_record(target, record),
                "reason": "ledger record is terminal done but workspace/task is not marked archived",
                "sideEffect": "agent should call safe task_workspace_lifecycle archive; script does not archive",
            })
    issue_to_open_prs = pr_links.get("issueToOpenPRs", {})
    task_by_issue = tasks.get("byIssue", {})
    launch_preflight = []
    for issue in issues["eligible"]:
        number = issue.get("number")
        issue_key = str(number)
        linked_prs = issue_to_open_prs.get(issue_key, [])
        ledger_active = active_targets_by_issue.get(issue_key, [])
        task_active = task_by_issue.get(issue_key, [])
        if linked_prs or ledger_active or task_active:
            attention.append({
                "target": f"{repo}#{number}",
                "reason": "eligible issue already appears to have in-progress evidence",
                "linkedOpenPRs": linked_prs,
                "ledgerActiveRecords": ledger_active,
                "taskMatches": task_active,
            })
            continue
        launch_preflight.append({
            "target": f"{repo}#{number}",
            "issue": issue,
            "reason": "open issue has triage:done+accepted and no deterministic duplicate evidence",
            "requiresAgenticDependencyPreflight": True,
            "sideEffect": "agent should run dependency/readiness preflight before launching; script does not launch",
        })
    return {
        "archiveCandidates": archive_candidates,
        "launchPreflightCandidates": launch_preflight,
        "attentionNeeded": attention,
        "tasksProvided": bool(tasks.get("provided")),
    }


def issue_state(repo: str, number: int) -> dict[str, Any]:
    issue = run_json(["gh", "api", f"repos/{repo}/issues/{number}"])
    if not isinstance(issue, dict):
        raise RuntimeError("issue state JSON must be an object")
    return {
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": str(issue.get("state", "")).upper(),
        "labels": sorted(label.get("name") for label in issue.get("labels", []) if label.get("name")),
        "assignees": sorted(assignee.get("login") for assignee in issue.get("assignees", []) if assignee.get("login")),
        "closedAt": issue.get("closed_at"),
        "updatedAt": issue.get("updated_at"),
        "url": issue.get("html_url"),
    }


def pr_state(repo: str, number: int) -> dict[str, Any]:
    pr = run_json([
        "gh", "pr", "view", str(number), "--repo", repo,
        "--json", "number,title,state,mergedAt,mergeCommit,url,baseRefName,headRefName,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,author",
    ])
    if not isinstance(pr, dict):
        raise RuntimeError("PR state JSON must be an object")
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "mergedAt": pr.get("mergedAt"),
        "mergeCommit": (pr.get("mergeCommit") or {}).get("oid") if isinstance(pr.get("mergeCommit"), dict) else None,
        "url": pr.get("url"),
        "baseRefName": pr.get("baseRefName"),
        "headRefName": pr.get("headRefName"),
        "isDraft": pr.get("isDraft"),
        "mergeStateStatus": pr.get("mergeStateStatus"),
        "reviewDecision": pr.get("reviewDecision"),
        "author": (pr.get("author") or {}).get("login") if isinstance(pr.get("author"), dict) else None,
        "statusChecks": normalize_status_checks(pr.get("statusCheckRollup")),
    }


def build_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    repo_info = default_repo()
    repo = args.repo or repo_info["nameWithOwner"]
    branch_info = repo_info.get("defaultBranchRef") or {}
    default_branch = args.trunk or branch_info.get("name") or "main"
    ledger_path = Path(args.ledger)
    state_dir = Path(args.state_dir)
    ledger = read_ledger(ledger_path)
    git_info = fetch_origin_main(default_branch, do_fetch=not args.no_fetch)
    labels = fetch_labels(repo)
    issues = fetch_issues(repo)
    prs = fetch_open_prs(repo, include_body=True)
    pr_links = detect_pr_issue_links(prs, repo)
    dependency_hints = fetch_dependency_hints(repo, issues["eligible"])
    tasks = load_tasks(Path(args.tasks_json) if args.tasks_json else None)
    ledger_info = ledger_summary(ledger)
    actions = compute_action_candidates(repo=repo, ledger=ledger, issues=issues, pr_links=pr_links, tasks=tasks)
    return {
        "generatedAt": utc_now(),
        "repo": repo,
        "root": str(repo_root()),
        "stateDir": str(state_dir),
        "ledgerPath": str(ledger_path),
        "git": git_info,
        "gitExclude": ensure_exclude_entry(state_dir, apply=False),
        "labels": labels,
        "ledger": ledger_info,
        "github": {
            "eligibleIssues": issues["eligible"],
            "triageDoneMissingAccepted": issues["triageDoneMissingAccepted"],
            "blockedOpenIssues": issues["blocked"],
            "openPRs": [{key: value for key, value in pr.items() if key != "body"} for pr in prs],
            "dependencyHints": dependency_hints,
            "issueToOpenPRs": pr_links["issueToOpenPRs"],
        },
        "recommendedAgentActions": actions,
    }


def print_markdown(snapshot: dict[str, Any]) -> None:
    actions = snapshot["recommendedAgentActions"]
    labels = snapshot["labels"]
    ledger = snapshot["ledger"]
    github = snapshot["github"]
    git = snapshot["git"]
    print(f"# Issue Implementation Loop Snapshot")
    print()
    print(f"- Generated: `{snapshot['generatedAt']}`")
    print(f"- Repo: `{snapshot['repo']}`")
    print(f"- Origin `{git['originRef']}`: `{git['originHead']}`")
    print(f"- Git exclude OK: `{snapshot['gitExclude']['present']}`")
    print(f"- Required labels missing: `{labels['missing']}`")
    print(f"- Ledger records: `{ledger['recordCount']}` states=`{ledger['states']}`")
    print(f"- Open eligible issues: `{len(github['eligibleIssues'])}`")
    print(f"- Open blocked issues: `{len(github['blockedOpenIssues'])}`")
    print(f"- Explicit dependency hints: `{len(github['dependencyHints'])}`")
    print(f"- Open PRs: `{len(github['openPRs'])}`")
    print()
    print("## Recommended agent actions")
    print()
    print(f"- Archive candidates: `{len(actions['archiveCandidates'])}`")
    print(f"- Launch preflight candidates: `{len(actions['launchPreflightCandidates'])}`")
    print(f"- Attention needed: `{len(actions['attentionNeeded'])}`")
    if actions["launchPreflightCandidates"]:
        print("\n### Launch preflight candidates")
        for candidate in actions["launchPreflightCandidates"]:
            issue = candidate["issue"]
            print(f"- `{candidate['target']}` — {issue.get('title')}")
    if actions["archiveCandidates"]:
        print("\n### Archive candidates")
        for candidate in actions["archiveCandidates"]:
            print(f"- `{candidate['target']}` workspace=`{candidate.get('workspaceId')}` task=`{candidate.get('taskId')}` — {candidate['reason']}")
    if actions["attentionNeeded"]:
        print("\n### Attention needed")
        for item in actions["attentionNeeded"]:
            print(f"- `{item.get('target', 'unknown')}` — {item.get('reason')}")
    if github["dependencyHints"]:
        print("\n### Explicit dependency hints")
        for hint in github["dependencyHints"]:
            print(f"- `{hint['target']}` mentions `{hint['referencedTarget']}` via {hint['keywords']} — {hint['evidence']}")
    if github["openPRs"]:
        print("\n## Open PRs")
        for pr in github["openPRs"]:
            print(f"- `#{pr['number']}` {pr['title']} — merge=`{pr.get('mergeStateStatus')}` author=`{pr.get('author')}`")


def prune_ledger(args: argparse.Namespace) -> dict[str, Any]:
    ledger_path = Path(args.ledger)
    ledger = read_ledger(ledger_path)
    records = ledger.get("records", {})
    assert isinstance(records, dict), "records must be dict"
    pruned: dict[str, Any] = {}
    kept: dict[str, Any] = {}
    refused: dict[str, str] = {}
    for target, record in records.items():
        if not isinstance(record, dict):
            kept[target] = record
            refused[target] = "record is not an object"
            continue
        terminal_done = record.get("state") == "done"
        safe_no_lifecycle = not has_workspace_ref(record)
        safe_archived = record.get("archived") is True
        if terminal_done and (safe_archived or safe_no_lifecycle):
            pruned[target] = record
        else:
            kept[target] = record
            refused[target] = "not terminal done, not archived, or still has lifecycle refs"
    result = {
        "ledgerPath": str(ledger_path),
        "dryRun": not args.apply,
        "apply": args.apply,
        "beforeCount": len(records),
        "prunedCount": len(pruned),
        "keptCount": len(kept),
        "prunedTargets": sorted(pruned, key=target_sort_key),
        "keptTargets": sorted(kept, key=target_sort_key),
        "refused": refused,
        "backupPath": None,
    }
    if args.apply:
        backup = Path(args.backup_dir) / f"aegis-issue-implementation-ledger-pre-prune-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ledger_path, backup)
        next_ledger = {"version": ledger.get("version", 1), "records": kept}
        # Preserve unknown top-level metadata only while it still describes kept records.
        if kept:
            for key, value in ledger.items():
                if key not in {"version", "records"}:
                    next_ledger[key] = value
        atomic_write_json(ledger_path, next_ledger)
        result["backupPath"] = str(backup)
    return result


def add_common_repo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", help="GitHub repo owner/name; defaults to gh repo view")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic helper for the Mux issue implementation loop")
    subcommands = parser.add_subparsers(dest="command", required=True)

    snapshot = subcommands.add_parser("snapshot", help="fetch live repo state and summarize deterministic next actions")
    add_common_repo_args(snapshot)
    snapshot.add_argument("--trunk", help="default branch/ref to fetch; defaults to repo default branch")
    snapshot.add_argument("--ledger", default=str(LEDGER_PATH))
    snapshot.add_argument("--state-dir", default=str(STATE_DIR))
    snapshot.add_argument("--tasks-json", help="optional JSON from Mux task_list")
    snapshot.add_argument("--no-fetch", action="store_true", help="do not git fetch origin/<trunk> before reading origin ref")
    output = snapshot.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", default=True, help="emit JSON (default)")
    output.add_argument("--markdown", action="store_true", help="emit a compact Markdown summary")

    prune = subcommands.add_parser("prune-ledger", help="drop safe terminal done records from the local ledger")
    prune.add_argument("--ledger", default=str(LEDGER_PATH))
    prune.add_argument("--backup-dir", default="/tmp")
    mode = prune.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="show what would be pruned without writing")
    mode.add_argument("--apply", action="store_true", help="atomically write the pruned ledger")

    ensure = subcommands.add_parser("ensure-exclude", help="verify or append the state directory to repo-local git exclude")
    ensure.add_argument("--state-dir", default=str(STATE_DIR))
    ensure_mode = ensure.add_mutually_exclusive_group(required=True)
    ensure_mode.add_argument("--dry-run", action="store_true")
    ensure_mode.add_argument("--apply", action="store_true")

    issue = subcommands.add_parser("issue-state", help="directly re-fetch and normalize one issue")
    add_common_repo_args(issue)
    issue.add_argument("number", type=int)

    pr = subcommands.add_parser("pr-state", help="directly re-fetch and normalize one PR")
    add_common_repo_args(pr)
    pr.add_argument("number", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            snapshot = build_snapshot(args)
            if args.markdown:
                print_markdown(snapshot)
            else:
                json.dump(snapshot, sys.stdout, indent=2, sort_keys=True)
                print()
        elif args.command == "prune-ledger":
            result = prune_ledger(args)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            print()
        elif args.command == "ensure-exclude":
            result = ensure_exclude_entry(Path(args.state_dir), apply=args.apply)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            print()
        elif args.command == "issue-state":
            repo = args.repo or default_repo()["nameWithOwner"]
            json.dump(issue_state(repo, args.number), sys.stdout, indent=2, sort_keys=True)
            print()
        elif args.command == "pr-state":
            repo = args.repo or default_repo()["nameWithOwner"]
            json.dump(pr_state(repo, args.number), sys.stdout, indent=2, sort_keys=True)
            print()
        else:
            parser.error(f"unknown command: {args.command}")
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:  # intentional CLI boundary: fail closed and explain.
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
