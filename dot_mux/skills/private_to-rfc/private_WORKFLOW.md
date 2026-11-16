# To RFC Workflow

## Modes

Use the smallest mode that satisfies the request.

| Mode | Use when | Output |
|---|---|---|
| `context` | The user has a transcript, prototype, PRD, branch, or vague RFC request | Context packet, decision ledger, evidence map, open questions |
| `draft` | The user has a template or asks for a full RFC | Complete RFC draft plus assumptions and validation needs |
| `section` | The user asks for one section | Revised section plus placement notes and evidence notes |
| `review` | The user asks to grill, critique, or make review-ready | Reviewer traps, contradictions, unsupported claims, fixes |
| `diagrams` | The RFC needs architecture, flow, or state diagrams | Renderer-safe Mermaid, captions, placement guidance |
| `validation` | The RFC is based on a prototype or implementation | Dogfood plan, test plan, proof bundle requirements |

Default to `context` for `$to-rfc` with no explicit mode.

## Intake

Ask or infer:

- What kind of RFC is this: architecture, product, process, migration, API, operational, or research?
- What output does the user want now: context, full draft, section edit, review, diagrams, or validation plan?
- What template or house style should be used? Default to the Coder RFC scaffold in `CODER_RFC_TEMPLATE.md` unless the user supplies another template.
- What target medium will host the RFC, such as Notion, GitHub, Markdown, or a docs site?
- What artifacts are available: transcript, PRD, prototype, branch diff, plan, screenshots, logs, tests, metrics, diagrams, draft?
- Which decisions are already made, which are open, and which must be escalated?

Ask only when an answer changes the RFC direction. Otherwise proceed with stated assumptions.

## Context harvest

Collect enough direct evidence to support the RFC.

- Conversation context: user thesis, constraints, preferred phrasing, disagreements, decisions, and open questions.
- Product context: users, operators, support impact, compatibility, migration, rollout, and adoption.
- Technical context: current architecture, proposed architecture, APIs, data model, state machine, failure modes, security, privacy, observability, scalability.
- Prototype context: branch, diff, commits, tests, dogfood runs, screenshots, videos, logs, database timelines, known bugs.
- Document context: RFC template, previous RFC examples, ADRs, PRDs, design docs, issue tracker, roadmap notes.

For large Mux session transcripts, run `scripts/transcript_index.py <session> --output-dir <analysis-dir>` before delegating. Preserve line ranges and artifact paths so findings can be traced.

## Sub-agent decomposition

Use sub-agents when context is too large for one pass or when independent verification helps. Good lanes:

1. Current architecture and pain points.
2. Proposed architecture and new components.
3. Prototype or implementation evidence.
4. Dogfood and validation evidence.
5. Historical before/after checks.
6. Requirements and operational scenarios.
7. Alternatives, rejected options, and scope creep risks.
8. Diagrams and target-medium rendering constraints.

Ask each sub-agent for evidence, decisions, risks, and open questions. Do not ask them only for polished prose.

## Decision extraction

Create a decision ledger before drafting. Each decision should include:

- Name.
- Current state.
- Proposed state.
- Rationale.
- Evidence.
- Tradeoffs.
- Risks.
- Rollout implications.
- Verification status.
- Open questions.

Use this ledger to prevent contradictions between RFC sections.

## Section mapping

Map raw material before writing paragraphs.

| RFC section | Put here | Keep out |
|---|---|---|
| Problem Statement | What is wrong, who is affected, why now, pressure created | Full solution details |
| Goals | Desired outcomes and constraints | Implementation minutiae |
| Non-goals | Explicit exclusions and future work | Hidden unresolved decisions |
| Proposal Overview | Core thesis and shape of the change | Deep rollout mechanics |
| Architecture | Ownership, boundaries, data flow, control flow, state, recovery | Product marketing prose |
| Operational Scenarios | Concrete user-visible or operator-visible flows | Generic user stories for architecture RFCs |
| Requirements | Testable behavior and non-functional constraints | Nice-to-have implementation ideas |
| Phases or Rollout | Incremental delivery, compatibility, kill switches, migration | Core contracts that should be requirements |
| Dogfooding and Validation | How claims will be proven, artifacts required | Vague confidence statements |
| Alternatives | Rejected options and rationale | Ideas silently discarded |
| Open Questions | Real decisions still unresolved | Questions already answered by evidence |

## Drafting behavior

- Draft one section at a time when possible.
- Preserve the user's thesis and vocabulary when accurate.
- Replace ambiguous terms with precise ownership and responsibility language.
- Do not overstate scalability, reliability, performance, or adoption benefits.
- Cite evidence in notes or references, but keep public RFC prose readable.
- Tell the user when a section is good enough to move on.

## Review behavior

When reviewing, act like a critical peer reviewer:

- Identify claims reviewers can challenge.
- Find contradictions across sections.
- Identify terms that imply the wrong architecture or ownership model.
- Separate initial scope from alternatives and future work.
- Recommend exact replacement wording when useful.
- State whether the draft is ready for broad review, close review, or more evidence gathering.

## Output bundle

For context-heavy requests, return:

- Context packet.
- Decision ledger.
- Evidence map.
- Section map.
- Reviewer traps.
- Alternatives and scope ledger.
- Diagram plan or diagram source.
- Dogfooding and validation plan.
- Open questions.
- Recommended next step.
