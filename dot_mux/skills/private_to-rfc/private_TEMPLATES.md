# To RFC Templates

## Context packet

```md
# RFC Context Packet: <working title>

## Request

- User ask:
- Desired mode:
- Target template or medium:
- Assumptions:

## Thesis

<One to three sentences capturing the proposal.>

## Goals

- 

## Non-goals

- 

## Constraints

- Technical:
- Product:
- Operational:
- Rollout:
- Security/privacy/compliance:

## Current state

<Architecture, workflow, API, product behavior, or process today.>

## Proposed state

<What changes, who owns what, and which boundaries move.>

## Evidence inventory

| Evidence | Source | Supports | Verification status |
|---|---|---|---|
|  |  |  |  |

## Decisions

See decision ledger.

## Open questions

- 
```

## Decision ledger

```md
| Decision | Current state | Proposed state | Rationale | Evidence | Risks | Rollout | Verification | Open questions |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |
```

## Evidence map

```md
| Claim | Evidence | Evidence type | Confidence | Notes |
|---|---|---|---|---|
|  |  | Code, doc, user decision, prototype, test, dogfood, log, metric | Verified, partial, assumed, future |  |
```

## Scope ledger

```md
| Idea | Classification | Why | Where to document |
|---|---|---|---|
|  | Initial scope, non-goal, alternative, future work, open question |  |  |
```

## RFC outline

```md
# <RFC Title>

## Summary

## Problem Statement

## Goals

## Non-goals

## Proposal Overview

## Architecture / Design

## Operational Scenarios

## Requirements

### Functional requirements

### Non-functional requirements

### Eventual requirements

## Rollout / Phases

## Dogfooding and Validation

## Alternatives Considered

## Risks and Mitigations

## Open Questions
```

For Coder RFCs, start from `CODER_RFC_TEMPLATE.md` and adapt this outline into that scaffold. Do not force all sections if the supplied template differs.

## Problem statement pattern

```md
Today, <system/process> requires <actor/component> to own both <responsibility A> and <responsibility B>. This creates <pressure>, because <reason grounded in evidence>. As <scale/usage/complexity> grows, this coupling makes <failure mode or cost> harder to manage without <desired class of change>.
```

Keep solution details out unless the template expects a brief direction sentence.

## Operational scenario pattern

```md
### <Scenario name>

1. Given <initial state>, <actor/system> does <action>.
2. The system <observable behavior>.
3. If <failure or edge case>, the system <recovery behavior>.
4. The user/operator observes <expected outcome>.
```

Use operational scenarios when product-style user stories are too generic for architecture RFCs.

## Requirements pattern

```md
### Functional requirements

- The system must <observable behavior> when <condition>.
- The system must preserve <compatibility or contract>.

### Non-functional requirements

- The design must support <safety, latency, durability, scale, privacy, observability, operability>.

### Eventual requirements

- The design should leave room for <future capability> without requiring <known bad rewrite>.
```

## Dogfooding and validation pattern

```md
## Dogfooding and Validation

### Setup

- Environment:
- Feature flags or configuration:
- Test data:

### Scenarios

| Scenario | Steps | Expected evidence | Artifact |
|---|---|---|---|
|  |  | Screenshot, video, logs, test output, DB timeline, trace |  |

### Automated validation

- 

### Manual validation

- Include screenshots and video when visual behavior or workflow handoff matters.

### Known gaps

- 
```

## Reviewer-trap report

```md
# Reviewer Traps

| Trap | Why reviewers will object | Fix |
|---|---|---|
| Unsupported claim | No direct evidence or too broad | Narrow claim or add evidence |
| Section mixing | Problem statement contains solution details | Move to proposal overview |
| Ambiguous ownership | Term implies wrong runtime or responsible party | Define terms and replace wording |
| Scope creep | Future optimization appears required for v1 | Move to future work or alternatives |
| Missing failure mode | Crash, retry, duplicate, stale, reconnect, or migration not covered | Add requirement or risk |
```
