# Workspace-local GitHub triage heartbeat

Target repo: `{{REPO}}`

Labels:
- `{{ENTRY_LABEL}}`: issue should be considered by the loop.
- `{{IN_PROGRESS_LABEL}}`: parent loop successfully started a child workspace for the issue.
- `{{DONE_LABEL}}`: child posted a public Mux triage report.

Issue types:
- Child sets exactly one configured GitHub issue type before removing triage labels, usually one of {{ISSUE_TYPES}}. Do not use labels for bug/feature/chore/tech-debt classification.

Policy:
- Scope: initial issue triage only. The loop completes an issue once a useful Mux triage report is posted or reused, terminal triage labels are reconciled, and a GitHub issue type is set, even when the report says the issue was blocked or not implementable at triage time.
- Heartbeat cadence: roughly every 10 minutes, workspace-local and best-effort. When a heartbeat finds triage work, it should set one bounded convergence goal so additional scheduling/reconciliation cycles run without waiting for the next heartbeat.
- Concurrency cap: max 5 active triage workspaces at a time. Each scheduling cycle launches only the remaining capacity after counting active queued/starting/running/awaiting_report/pending/backgrounded triage workspaces.
- Eligible issue: open, has `{{ENTRY_LABEL}}`, lacks `{{IN_PROGRESS_LABEL}}`, lacks `{{DONE_LABEL}}`, lacks an existing ledger record, and lacks an existing matching task/workspace.
- Idempotency key: `github-triage:{{REPO}}#<number>`.
- Workspace title: `Triage #<number>`; branch: `triage-<number>`. Keep repo context in idempotency keys, not in title/branch, because Mux groups workspaces by project.
- Apply `{{IN_PROGRESS_LABEL}}` only after workspace creation succeeds.
- Child reports may include relationship/dependency findings when useful, framed as point-in-time evidence. They must not mutate existing related issues.
- The child final response should include `### Parent ledger hints` with relationship/readiness JSON. Missing or malformed hints are non-fatal.
- Parent launch ordering may softly prioritize already-eligible same-repo prerequisite issues found in prior ledger hints, but hints never change eligibility and never cause auto-labeling of related issues.
- Ledgered terminal/ambiguous work may receive one normal retry workspace. If that retry does not converge, report attention-needed instead of looping.
- Archive terminal triage workspaces after their ledger record reaches `triage_done`, the issue type is set, and no active task remains for the workspace.
- Goal completion: the convergence goal is done when there are no eligible unlaunched entry-label issues, no active triage workspaces, no terminal unreconciled triage workspaces, no unarchived `triage_done` ledger records, and no `attention_required` blockers. If a cycle makes no progress, report state and wait rather than busy-looping.

State files:
- `ledger.json`: local best-effort dispatch ledger. Version 1 records may include optional `relationshipHints`, `readinessHint`, parse-warning, and recovery fields.
- `child-prompt-template.md`: prompt template for new child workspaces.
