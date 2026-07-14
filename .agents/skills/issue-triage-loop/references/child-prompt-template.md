Task: Triage one GitHub issue publicly.

Issue: {{ISSUE_URL}}
Idempotency key: github-triage:{{REPO}}#{{ISSUE_NUMBER}}
Repository: {{REPO}}

You own exactly this one issue. Do not triage any other issue in this workspace.

Parent-loop context:
- The parent heartbeat loop launched this workspace because the issue had `{{ENTRY_LABEL}}` and did not have `{{DONE_LABEL}}` or `{{IN_PROGRESS_LABEL}}`.
- The parent should apply `{{IN_PROGRESS_LABEL}}` immediately after this workspace starts. If it is still absent after you begin work, you may apply `{{IN_PROGRESS_LABEL}}` once and continue.
- The loop's job is initial triage only. Once a useful triage report is posted or reused, terminal triage labels are reconciled, and the GitHub issue type is set, the issue is complete for this loop even if it appeared blocked or not implementable at triage time.

Triage goal:
- Produce a public triage report that helps the maintainer understand the issue and the recommended next step.
- This is triage only. Do not create a pull request unless the maintainer explicitly asks later.
- Keep the investigation bounded. Use other skills or read-only sub-agents when they materially improve the triage, but do not turn this into exhaustive issue-graph analysis or implementation work.

If this is a bug report:
- Use the repo, available CLIs, fixtures, tests, agent-tty/agent-browser/etc. as appropriate to reproduce or narrow the bug.
- Build a minimal reproducible example when feasible, including commands, environment, fixtures, screenshots/recordings, and observations when useful.
- Focus on reproduction and verification evidence, not fixing. A later implementation workflow can determine root cause and resolution.

If this is a feature, chore, or tech-debt request:
- Run research when useful to gather prior art and comparable implementations.
- Assess whether the request makes sense for this repo, whether a workaround already exists, or whether this is a documentation gap.
- Use a prototype only if it helps ground the recommendation.

Relationship/readiness pass:
- Do a lightweight pass for related issues: read the assigned issue body/comments, follow explicit issue references, search a few high-signal terms, and inspect only the most relevant hits.
- You may use read-only `explore` sub-agents when multiple related issues or repo areas need comparison, but this is optional.
- Existing related issues are read-only. Do not comment on, label, close, or otherwise mutate them.
- Do not add `{{ENTRY_LABEL}}` to existing related issues. Mention recommended follow-up in this issue's report instead.
- Cross-repo dependencies may be mentioned if relevant, but this workspace still owns only the assigned issue in {{REPO}}.
- Include relationship/dependency findings in the public report only when they add signal; do not add an empty "none found" section.
- Phrase blockers/readiness as point-in-time evidence, e.g. "At triage time, this appeared blocked by #123 because ..." Avoid standing statuses like "Status: blocked."

Adjacent findings:
- If triage uncovers a distinct adjacent bug, feature request, follow-up, documentation gap, or concrete prerequisite that is not already tracked, create a new GitHub issue in {{REPO}} so the finding is persisted.
- Before creating a new issue, search existing open and closed issues to avoid duplicates.
- Keep new issues concise and evidence-backed. Include reproduction/context/commands when available.
- Apply workflow labels to newly created issues only when appropriate; add `{{ENTRY_LABEL}}` if the new issue should enter this triage loop later. Do not add labels for classification.
- Set a sensible GitHub issue type on newly created issues, such as {{ISSUE_TYPES}}, or another configured issue type that better fits. Use `gh issue create --type "<IssueType>"` when creating the issue. Do not use labels for bug/feature/chore/tech-debt classification.
- Do not create adjacent issues for vague concerns like "needs investigation" or "maybe refactor first," and do not let adjacent issue creation distract from completing this issue's triage report.

Issue type classification:
- Before finishing, classify the triaged issue and set exactly one sensible GitHub issue type with `gh issue edit {{ISSUE_NUMBER}} --repo {{REPO}} --type "<IssueType>"`.
- Prefer `Bug` for confirmed/reproducible defects, `Feature` for new capability requests, and `Chore` for internal cleanup/architecture/maintenance work. Map tech-debt to `Chore` unless the repository has a dedicated tech-debt issue type.
- If another configured repository issue type is a better fit, use it instead. Do not add labels such as `bug`, `feature`, `chore`, or `tech-debt` for classification.
- Do not remove unrelated pre-existing labels.

Public GitHub comment requirements:
- Before posting, check whether a Mux AI triage comment already exists on the issue. If one exists, do not post a duplicate; report that state and still ensure transition labels and issue type are consistent.
- Post exactly one triage report comment to the issue when triage is complete.
- Start the comment exactly with:

```markdown
> [!NOTE]
> This triage report is AI-generated using Mux
```

- The comment is public and will notify participants. Do not ping people. Avoid `@username` mentions; redact mentions in quoted text if needed.
- Use neutral/passive phrasing rather than referring to participants in the third person.
- If you created files during triage, run an explore agent on each of them to check for secrets or sensitive information before posting contents. Redact or omit anything sensitive.
- If files pass screening, include useful contents in collapsible `<details>` blocks rather than dumping long text inline.

Parent ledger hints:
- In your final workspace response, include exactly one `### Parent ledger hints` section with a fenced `json` block.
- This block is for the parent ledger, not necessarily for the public GitHub comment.
- Use `relationshipHints: []` if you did not find meaningful relationships.
- Use point-in-time readiness language. These hints are non-authoritative evidence for future agents to revalidate.

```json
{
  "relationshipHints": [
    {
      "targetRepo": "{{REPO}}",
      "targetIssueNumber": 123,
      "targetIssueUrl": "https://github.com/{{REPO}}/issues/123",
      "relationship": "blocked_by",
      "confidence": "likely",
      "reason": "At triage time, the assigned issue appeared to require the prerequisite discussed in #123."
    }
  ],
  "readinessHint": {
    "readiness": "ready_at_triage_time",
    "blockingIssues": [],
    "reason": "At triage time, no concrete blocking prerequisite was found."
  }
}
```

Recognized relationship values: `blocked_by`, `blocks`, `builds_on`, `duplicate_of`, `duplicates`, `related_to`, `superseded_by`, `supersedes`.
Recommended readiness values: `ready_at_triage_time`, `blocked_at_triage_time`, `needs_clarification_at_triage_time`, `needs_reproduction_at_triage_time`, `duplicate_or_superseded_at_triage_time`, `not_actionable_at_triage_time`.

Completion steps:
1. Post the single public triage report comment, unless an existing Mux triage comment is already present.
2. Apply `{{DONE_LABEL}}` and set the selected GitHub issue type, such as {{ISSUE_TYPES}}, with `gh issue edit {{ISSUE_NUMBER}} --repo {{REPO}} --type "<IssueType>"`.
3. Remove `{{ENTRY_LABEL}}` and `{{IN_PROGRESS_LABEL}}` only after `{{DONE_LABEL}}` is present and `gh issue view {{ISSUE_NUMBER}} --repo {{REPO}} --json issueType` confirms the selected issue type.
4. In your final workspace response, include the issue URL, any adjacent issues created, what you posted/did not post, labels applied/removed, issue type set/verified, validation performed, and the `### Parent ledger hints` JSON block.

Repo/environment hint: if GitHub CLI calls fail with a `mise` trust error, run `mise trust` once from the repository root, then retry commands normally.
