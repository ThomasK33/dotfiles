---
name: issue-triage-loop
description: Use when setting up or running a GitHub issue triage heartbeat that labels needs-triage issues, launches one non-disposable Mux workspace per issue, posts public triage reports, and archives completed triage workspaces.
---

# Issue Triage Loop

Use this skill in three modes:

1. **Setup mode** — install a portable `.mux/triage-loop/` state directory, create required GitHub labels when missing, and configure this workspace heartbeat.
2. **Parent/orchestrator tick** — reconcile GitHub issues into one child workspace per eligible issue and archive terminal triage workspaces.
3. **Child/issue triage** — triage exactly one assigned issue, post one public report, update labels, and stop.

The loop is a bounded reconciler, not a daemon. Heartbeats run when the workspace is idle; every tick must re-read actual state before side effects.

When a scheduled heartbeat finds triage work to do, it should bootstrap a durable convergence goal rather than waiting for another heartbeat between batches. The goal changes cadence only: every reconciliation cycle remains bounded, re-reads actual state before side effects, preserves duplicate guards, and stops once the loop is converged or blocked.

## Ownership boundary

The issue triage loop owns initial issue triage only. It does not own implementation readiness over time, dependency lifecycle management, issue graph maintenance, duplicate closure, or re-triage. A given issue is complete from the loop's perspective once a useful Mux triage report has been posted or reused and terminal labels are reconciled, even when the report says the issue was not implementable at triage time.

Treat relationship and readiness findings as point-in-time evidence for humans or later implementation agents to revalidate, not durable status. Do not automatically re-triage completed issues. If a human wants a fresh triage, they can manually remove/reset the old Mux triage state and re-enter the issue into the normal loop.

## Issue relationships and readiness

Issues can depend on, build on, duplicate, supersede, or otherwise reference other issues, including issues in other repositories. Relationship discovery is part of producing a useful triage report, but it must stay bounded:

- Child triage workspaces should do a lightweight relationship pass: read the assigned issue body/comments, follow explicit issue references, search a few high-signal terms, and inspect only the most relevant hits.
- Use read-only `explore` sub-agents when broader codebase or issue-graph investigation materially improves the triage, but do not require a sub-agent for trivial issues.
- Do not exhaustively map the issue graph. If relationship discovery grows broad, summarize the strongest signals, state uncertainty, and finish the triage.
- Existing related issues are read-only. A child may read and cite them, but must not comment on, label, close, or otherwise mutate them. The assigned issue and newly created adjacent issues are the only GitHub issues the child may modify.
- Do not automatically add `needs-triage` to existing related issues. Existing issues enter the loop only when they are explicitly labeled for triage.
- Cross-repo relationships may be mentioned in reports and stored as hints, but parent launch scheduling only applies to the configured repo.

Public triage reports do not need a fixed body structure beyond the required Mux note header. Include an issue relationships/dependencies section only when it adds signal; do not add empty boilerplate such as "None found." Any blocker or readiness claim in a public report must be point-in-time phrasing, for example "At triage time, this appeared blocked by #123 because ..." rather than a standing status such as "Status: blocked."

### Parent ledger hints contract

Each child final response should include one machine-readable block for the parent, separate from the public GitHub comment:

````markdown
### Parent ledger hints

```json
{
  "relationshipHints": [
    {
      "targetRepo": "owner/name",
      "targetIssueNumber": 123,
      "targetIssueUrl": "https://github.com/owner/name/issues/123",
      "relationship": "blocked_by",
      "confidence": "likely",
      "reason": "At triage time, the assigned issue appeared to require the API contract discussed in #123."
    }
  ],
  "readinessHint": {
    "readiness": "blocked_at_triage_time",
    "blockingIssues": [
      {
        "repo": "owner/name",
        "issueNumber": 123,
        "issueUrl": "https://github.com/owner/name/issues/123"
      }
    ],
    "reason": "At triage time, implementation appeared blocked on #123."
  }
}
```
````

Use `relationshipHints: []` when no meaningful relationships were found. `readinessHint` is an internal point-in-time hint; it does not need to be published as a standing status.

Recognized ledger relationship values:

- `blocked_by` — assigned issue depends on another issue first.
- `blocks` — assigned issue is a prerequisite for another issue.
- `builds_on` — assigned issue extends or assumes work from another issue, but not necessarily blocked.
- `duplicate_of` — assigned issue appears to duplicate another issue.
- `duplicates` — another issue appears to duplicate the assigned issue.
- `related_to` — meaningful context but no directional dependency.
- `superseded_by` — assigned issue is replaced by another issue/proposal.
- `supersedes` — assigned issue replaces another issue/proposal.

Recommended readiness values:

- `ready_at_triage_time`
- `blocked_at_triage_time`
- `needs_clarification_at_triage_time`
- `needs_reproduction_at_triage_time`
- `duplicate_or_superseded_at_triage_time`
- `not_actionable_at_triage_time`

The parent should parse this block when reconciling completed/reported child workspaces and may store compact hints in the ledger as optional fields. Missing or malformed hints are non-fatal: record a parse warning if useful, but do not block terminal reconciliation or archival solely because hints are absent.

## Defaults

- Scope: the current checkout's GitHub repository, discovered with `gh repo view --json nameWithOwner` unless the user names a repo explicitly.
- State directory: `.mux/triage-loop/`.
- Ledger: `.mux/triage-loop/ledger.json`, local and uncommitted.
- Concurrency cap: maintain at most 5 active triage workspaces at a time. Each scheduling cycle may launch up to the remaining capacity after counting queued, starting, running, awaiting-report, pending, and backgrounded triage workspaces.
- Heartbeat interval: 10 minutes.
- Heartbeat context mode: `compact` by default after setup, `normal` while actively debugging or tuning the loop.
- Entry label: `needs-triage`.
- Transition labels: `triage:in-progress`, `triage:done`.
- Default issue types: `Bug`, `Feature`, `Chore`. Use `Chore` for tech-debt/internal maintenance unless the repository has a dedicated issue type that better fits.
- Idempotency key: `github-triage:<owner/name>#<issue-number>`.
- Workspace title: `Triage #<issue-number>`; branch: `triage-<issue-number>`. Keep owner/repo in the idempotency key and ledger key, not in the human-visible workspace title or branch, because Mux already separates workspaces by project.

## Setup mode

Use setup mode when the user asks to install, port, configure, or start the triage loop in a repository.

### 1. Discover repo, transition labels, and issue types

If the repository uses `mise` and commands fail with a trust error, run `mise trust` once from the repository root, then retry commands normally.

1. Determine the target repo:

   ```bash
   gh repo view --json nameWithOwner -q .nameWithOwner
   ```

2. Read labels and confirm the GitHub CLI can read/set issue types:

   ```bash
   gh label list --repo owner/name --json name,color,description --limit 200
   gh issue view <known-issue-number> --repo owner/name --json issueType,labels
   gh issue edit --help | grep -- '--type'
   ```

3. Ensure only the transition labels below exist. If a label is missing and `gh label create` is permitted, create it. If label creation fails, report the missing label as a blocker before configuring the heartbeat. Do not create or require `bug`, `feature`, `chore`, or `tech-debt` labels for classification; classification belongs in GitHub's issue type field.

   | Label | Default color | Description |
   |---|---:|---|
   | `needs-triage` | `fef2c0` | Issue should be considered by the Mux triage loop |
   | `triage:in-progress` | `fbca04` | Mux triage workspace has been launched |
   | `triage:done` | `0e8a16` | Mux triage report has been posted |

   Do not mass-label existing issues with `needs-triage` unless the user asks.

### 2. Install local state files

Create `.mux/triage-loop/` if absent. Copy the templates from this skill and replace placeholders:

- `references/readme-template.md` -> `.mux/triage-loop/README.md`
- `references/child-prompt-template.md` -> `.mux/triage-loop/child-prompt-template.md`
- `references/heartbeat-message-template.md` -> heartbeat message, not a committed file unless useful for review

Replace:

- `{{REPO}}` with `owner/name`
- `{{ENTRY_LABEL}}` with `needs-triage`
- `{{IN_PROGRESS_LABEL}}` with `triage:in-progress`
- `{{DONE_LABEL}}` with `triage:done`
- `{{ISSUE_TYPES}}` with `Bug`, `Feature`, `Chore` (or the repository's configured type names)

Initialize the ledger only if it does not exist:

```json
{
  "version": 1,
  "records": {}
}
```

If `.mux/triage-loop/` already exists, read it first and preserve any repo-local customizations unless the user asks to overwrite them. Existing ledgers remain version 1; relationship/readiness fields are optional additive fields, not a migration requirement.

### 3. Configure heartbeat

Set a heartbeat that invokes this skill's parent/orchestrator tick. Prefer `contextMode: "compact"` once setup files exist because the README/template/ledger are the source of truth and repeated ticks otherwise accumulate chat history. Use `contextMode: "normal"` while testing or debugging a new loop. Use `contextMode: "reset"` only when the heartbeat message is fully self-contained and prior context is more harmful than helpful.

The heartbeat message should instruct heartbeat wake-ups to read actual state, then set one bounded convergence goal when there is eligible, active, terminal, or ledgered triage work. Goal continuations should run additional bounded reconciliation cycles so the loop can drain more than one batch without waiting for the next 10-minute heartbeat. Do not set a new goal for child terminal wake-up messages; those wake-ups should retrieve terminal reports and continue the existing convergence work.

Example:

```text
heartbeat({
  action: "set",
  enabled: true,
  intervalMs: 600000,
  contextMode: "compact",
  message: "<filled heartbeat-message-template.md>"
})
```

Completion criterion: transition labels exist or blockers are reported, issue types are supported/understood for the repository, `.mux/triage-loop/` exists with a ledger and child prompt, and `heartbeat(action="get")` shows the intended message and interval.

## Parent/orchestrator tick

Use this mode when the heartbeat fires, a durable triage convergence goal continues, a terminal child workspace wakes the parent, or the user asks to run a bounded triage reconciliation tick.

### 1. Read actual state before side effects

If commands fail with a `mise` trust error, run `mise trust` once from the repository root, then retry commands normally.

Read, in order:

1. `.mux/triage-loop/README.md`
2. `.mux/triage-loop/child-prompt-template.md`
3. `.mux/triage-loop/ledger.json` if present
4. Open issues carrying the entry label:

   ```bash
   gh issue list --repo owner/name --state open --label needs-triage --json number,title,url,createdAt,labels,issueType --limit 200
   ```

5. Active descendant tasks/workspaces with `task_list(statuses=["queued","starting","running","awaiting_report","pending","backgrounded"])`.
6. Completed/reported/interrupted/failed descendant tasks with `task_list(..., includeArchived=false)` for terminal reconciliation, hint ingestion, recovery decisions, and archival decisions.

### 2. Reconcile launches

An issue is eligible for a normal first launch only when every guard passes:

- It is open and has `needs-triage`.
- It lacks `triage:in-progress` and `triage:done`.
- `.mux/triage-loop/ledger.json` has no record for `owner/name#<number>`.
- No existing visible task/workspace title, branch, or prompt is attributable to `github-triage:owner/name#<number>`, `Triage #<number>`, `triage-<number>`, or the legacy long form `triage-<owner>-<name>-issue-<number>`.

Sort eligible issues deterministically. Start with oldest `createdAt` first, then apply only soft priority boosts from same-repo ledger hints that identify a concrete prerequisite/foundational issue already in the eligible set. Useful boosts include targets of `blocked_by` or `builds_on` relationship hints and concrete `blockingIssues` from `blocked_at_triage_time` readiness hints. Hints never change eligibility, do not create work for other repositories, and do not cause the parent to auto-label related issues.

Maintain at most 5 active triage workspaces at a time. Before planning new launches, count active queued/starting/running/awaiting_report/pending/backgrounded triage workspaces and compute `remainingCapacity = max(0, 5 - activeTriageWorkspaceCount)`. Launch at most `remainingCapacity` issues in the current scheduling cycle. If capacity is 0, reconcile/archive terminal work if any, then stop and wait for a terminal wake-up or later heartbeat; do not busy-wait.

For each launch, immediately before creating the workspace, re-read enough actual state to ensure the issue is still eligible. Then create a full child workspace:

```text
task({
  kind: "workspace",
  title: "Triage #<number>",
  prompt: "<child-prompt-template with placeholders filled>",
  run_in_background: true,
  workspace: {
    mode: "new",
    branchName: "triage-<number>",
    trunkBranch: "main",
    disposable: false
  }
})
```

After and only after workspace creation succeeds:

1. Write/update the ledger record.
2. Apply `triage:in-progress` to the issue.

If label application fails after workspace creation, keep the ledger record, set or report `attention_required`, and do not launch a duplicate.

A ledgered issue may receive at most one normal retry workspace when the previous child is terminal/failed/ambiguous, no active workspace exists for the same issue, GitHub terminal state is incomplete, and the ledger has not already recorded `recoveryAttempted: true`. The retry uses the same child prompt; there is no separate recovery mode. If that retry does not converge, mark/report `attention_required` and wait for a human.

### 3. Ledger record

Use keys of the form `owner/name#123`. Minimal record:

```json
{
  "idempotencyKey": "github-triage:owner/name#123",
  "issueNumber": 123,
  "issueUrl": "https://github.com/owner/name/issues/123",
  "workspaceId": "...",
  "taskId": "wst_...",
  "workspaceName": "Triage #123",
  "launchedAt": "2026-01-01T00:00:00Z",
  "lastObservedState": "launched",
  "labels": {
    "inProgressApplied": false,
    "inProgressAppliedAt": null
  },
  "classificationIssueType": null,
  "classificationObservedAt": null,
  "relationshipHints": [],
  "readinessHint": null,
  "parentLedgerHintsObservedAt": null,
  "parentLedgerHintsParseError": null,
  "recoveryAttempted": false,
  "archivedAt": null
}
```

Parent states:

- `launched` — workspace was created.
- `triage_in_progress` — `triage:in-progress` was applied or observed.
- `triage_done` — GitHub terminal state confirms the triage report, transition labels, and issue type are complete.
- `attention_required` — a workspace exists or existed but a required transition failed, terminal state is ambiguous after the allowed retry, or human judgment is needed.

### 4. Reconcile completed children and archive terminal workspaces

When a child workspace reaches a completed/reported terminal state, parse `### Parent ledger hints` from the child final response if available and store compact hints on the existing ledger record. Then verify terminal issue state from GitHub before marking the ledger `triage_done`:

- the issue has `triage:done`,
- `issueType.name` is set to the selected GitHub issue type (for example `Bug`, `Feature`, or `Chore`),
- `needs-triage` and `triage:in-progress` have been removed,
- a Mux triage report comment exists or was already reused.

Child final reports are trusted for distilled context and hints, but GitHub is the source of truth for transition labels, issue type, and public comments. If GitHub terminal state is ambiguous or incomplete, do not archive; use the one normal retry rule if available, otherwise mark/report `attention_required`. Missing or malformed parent ledger hints do not block `triage_done` or archival.

After launch reconciliation, archive completed triage workspaces that are no longer needed.

A workspace is archive-eligible only when:

- A ledger record for the issue has `lastObservedState: "triage_done"`.
- The ledger or child result indicates the triage report was posted/reused, the terminal triage label was applied, and the issue type was set.
- No queued/starting/running/awaiting_report/pending/backgrounded task exists for the same `workspaceId`.
- The workspace is visible and not already archived.

Archive with:

```text
task_workspace_lifecycle({
  action: "archive",
  targets: [{ workspaceId: "..." }],
  interrupt_active: false
})
```

Never use `delete_worktree` or `remove` unless the user explicitly asks. If archive requires confirmation for untracked paths, or fails for any other reason, do not delete anything; report the workspace and blocker.

### 5. Parent tick completion

Report:

- Actual-state reads performed.
- Issues launched and their workspace/task IDs.
- Relationship/readiness hints ingested, if any.
- Workspaces archived.
- Ledger, label, issue-type, recovery, or archival failures needing attention.
- Whether the tick converged.

Do not await child workspaces unless the next parent decision depends on their result.

If this tick is running under a convergence goal, continue with another bounded reconciliation cycle only when new progress is possible. If a pass makes no progress—no launch, terminal reconciliation, archive, retry, or attention-required classification—do not loop recursively; report the current state and wait for a heartbeat, terminal wake-up, or human action. The convergence goal is satisfied when there are no eligible unlaunched entry-label issues, no active triage workspaces, no terminal unreconciled triage workspaces, no unarchived `triage_done` ledger records, and no `attention_required` blockers.

## Child/issue triage mode

Use this mode when a child workspace prompt assigns one issue.

1. Fetch/read the issue and the relevant repository context.
2. If `triage:in-progress` is absent, apply it once and continue.
3. Decide the GitHub issue type: usually `Bug`, `Feature`, or `Chore`; use another configured repository issue type only when it clearly fits better. Map tech-debt/internal maintenance to `Chore` unless the repository has a dedicated tech-debt type.
4. For issues typed `Bug`, try to reproduce or narrow the failure with commands, fixtures, tests, logs, screenshots, recordings, or a minimal example when useful. Focus on evidence for triage, not fixing.
5. For issues typed `Feature` or `Chore`, inspect current behavior and use research/prototypes only when they materially improve the recommendation.
6. Perform the lightweight relationship pass described above. Include relationship/dependency findings in the public report only when they add signal, and phrase blockers/readiness as "at triage time" evidence.
7. Before creating adjacent issues, search open and closed issues for duplicates. If a distinct adjacent issue is needed, create it with evidence, add `needs-triage` when it should enter this loop, and set a sensible issue type with `gh issue create --type "<IssueType>"`. This includes concrete, independently actionable missing prerequisites, but not vague concerns such as "needs investigation". Do not use labels for bug/feature/chore/tech-debt classification.
8. Do not mutate existing related issues. Mention recommended follow-up in the assigned issue's report instead.
9. Before posting, check existing comments for the Mux triage note header. If one exists, do not post a duplicate.
10. Post exactly one public triage report comment when complete. Start it exactly with:

   ```markdown
   > [!NOTE]
   > This triage report is AI-generated using Mux
   ```

11. Apply `triage:done` and set the selected issue type with `gh issue edit <number> --repo owner/name --type "<IssueType>"`.
12. Remove `needs-triage` and `triage:in-progress` only after `triage:done` is present and `gh issue view <number> --repo owner/name --json issueType` shows the selected issue type.
13. Final response must include the issue URL, adjacent issues created, whether a comment was posted or reused, labels applied/removed, issue type set/verified, validation performed, and the `### Parent ledger hints` JSON block.

## Portable command notes

- In repos using `mise`, run `mise trust` once from the repository root when trust checks fail, then run GitHub CLI commands normally.
- If the `python` shim fails, use `python3` explicitly for JSON ledger manipulation.
- Use the repo's actual trunk branch when it is not `main`.
- Use short workspace titles and branches: title `Triage #<number>`, branch `triage-<number>`. Do not include owner or repo in either; Mux project separation already supplies that context. Branches must remain git-safe.
