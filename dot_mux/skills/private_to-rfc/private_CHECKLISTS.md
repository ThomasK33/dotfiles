# To RFC Checklists

## Claims audit

For each important claim, ask:

- Is it supported by direct evidence?
- Is the evidence current enough for the claim?
- Is the claim implemented, verified, partially verified, proposed, or future intent?
- Is the wording narrower than the evidence?
- Does the RFC need a citation, footnote, evidence note, or validation task?

Do not let prototype summaries substitute for direct proof.

## Historical accuracy

Use this when a branch, prototype, or migration changes existing behavior.

- What existed before this work?
- What is newly introduced?
- What is being generalized, renamed, or made safer?
- Does the RFC imply a mechanism is new when it already existed?
- Does the RFC blame the current system for a problem the new design also has?

## Section-purpose check

- Problem Statement: diagnostic, not a full solution.
- Goals: outcomes, not implementation steps.
- Non-goals: real exclusions, not hidden decisions.
- Proposal Overview: concise thesis.
- Architecture: ownership, boundaries, state, flows, recovery.
- Requirements: testable behavior.
- Rollout: sequence, flags, compatibility, migration.
- Alternatives: considered and rejected options with rationale.
- Open Questions: unresolved decisions only.

## Scope ledger check

Classify each notable idea as one of:

- Initial requirement.
- Non-goal.
- Alternative considered.
- Future optimization.
- Open question.
- Explicitly rejected.

If an idea appears in multiple classes, resolve the contradiction before drafting.

## Terminology check

For key nouns and verbs:

- Define terms before using them in requirements.
- Check that the term implies the intended owner, runtime, authority, or actor.
- Avoid words that overclaim, such as always, never, guaranteed, trivial, scalable, reliable, or simple, unless proven.
- Prefer precise terms like owns, coordinates, persists, executes, observes, authorizes, reconciles, or routes.

## Contradiction check

Look across all sections for mismatches:

- One section says a component owns something another section moves elsewhere.
- A non-goal appears as a requirement.
- A rollout phase contains a contract not listed in requirements.
- A diagram contradicts the prose.
- A future optimization is necessary for the initial design to work.
- The draft says UX is unchanged but scenarios imply visible changes.

## Failure-mode check

Architecture, API, infrastructure, and migration RFCs should usually address:

- Crash or restart.
- Retry and duplicate execution.
- Partial success.
- Stale leases, locks, or ownership.
- Existing resources, not only newly created resources.
- Downgrade, disable, or kill switch behavior.
- Backward compatibility.
- Security and authorization boundaries.
- Observability and debugging.
- Data migration and cleanup.

## Diagram check

- Does the visual hierarchy match the thesis?
- Are actors, systems, data stores, and external services distinct?
- Are authority and execution boundaries visible?
- Are labels short enough for the target renderer?
- Is there a simple version for constrained renderers such as Notion?
- Does the diagram render in the destination medium?
- If renderability is uncertain, prefer simple Mermaid flowcharts or sequence diagrams.

Avoid complex subgraphs, custom styling, long edge labels, unsupported layouts, and dense crossing arrows when portability matters.

## Dogfooding and validation check

For prototype-backed RFCs:

- Define setup steps.
- List feature flags or config.
- Include happy path, important edge cases, and rollback or disable behavior.
- Specify exact artifacts to collect: screenshots, videos, logs, traces, command output, metrics, DB timelines, or test reports.
- Record known failures and decide whether they change requirements, scope, rollout, or risks.
- Distinguish visual verification from functional verification.
- Do not claim a dogfood pass happened without direct artifacts.

## Readiness levels

- **Context ready:** decisions, evidence, and open questions are organized.
- **Draft ready:** sections are filled and assumptions are marked.
- **Close-review ready:** reviewer traps are fixed, but domain owners should review.
- **Broad-review ready:** claims are evidence-backed, diagrams render, validation plan is credible, and open questions are intentional.
