# Coder RFC Template

Add, remove, or rename sections as necessary. Fit the scaffold, but do not be bound by it when the RFC type needs different structure.

<aside>

🪐 RFC Process:

1. Start an RFC with a Problem Statement.
2. Collaborate on a draft RFC. Customer-facing issues should include Product input. Most RFCs should include backend and frontend input when those areas are affected.
3. Announce the RFC in the development channel and schedule an RFC review meeting. Invite release and planning stakeholders so anyone can opt in, and invite named stakeholders individually.
4. During review meetings, show reviewers what the RFC currently says and field questions and comments.
5. Modify the RFC as needed based on feedback and schedule another review meeting. Repeat until stakeholders approve.
6. Announce that the RFC is approved in the development channel.
7. Write epics and tickets as needed for the work the RFC prescribes and put them in the backlog.

</aside>

## Stakeholders

Who needs to approve this? Add others as needed.

- [ ] Product Lead:
- [ ] Engineering DRI:
- [ ] CTO:

## Problem Statement

Why do we need to take action?

## UX & Design

Include flowcharts, Figma mocks, diagrams, or other design-thinking that can inform the work. Focus on non-technical aspects of the proposal first.

For architecture RFCs, this section can include operational scenarios and high-level diagrams instead of product-only UX.

## User Stories

Optionally include user stories that highlight the customer problems and desired outcomes. Include links to GitHub issues or other context when useful.

For architecture RFCs where classic user stories feel forced, use `Operational Scenarios` instead.

## Requirements

### Initial Functional Requirements

How should the system behave?

### Initial Non-functional Requirements

What constraints do we have concerning performance, usability, reliability, security, privacy, observability, and operability?

### Eventual Requirements

List requirements we do not have to implement right now, but should not make more difficult later. Delete if not applicable.

## Scope

What is and is not in scope?

## Phases

How can this be broken down into the smallest steps possible that still deliver customer value or get customer feedback? Delete if not applicable.

## Suggested Additions When Useful

### Proposal Overview

Use this when the Problem Statement should stay diagnostic and the solution thesis needs a separate home.

### Architecture

Use this for ownership boundaries, control flow, data flow, state, recovery, security, and operational behavior.

### Operational Scenarios

Use this instead of or alongside User Stories when the RFC is primarily architectural.

### Dogfooding and Validation

Use this when the RFC is based on a prototype, branch, or behavior that must be proven with tests, screenshots, videos, logs, traces, metrics, or database timelines.

### Alternatives Considered

Use this to record rejected options, tradeoffs, and why they are not in initial scope.

### Open Questions

Use this for unresolved decisions that need reviewer input.
