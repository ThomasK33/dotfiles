---
name: to-rfc
description: Converts conversations, prototypes, PRDs, implementation notes, and evidence into Coder-style RFC context packets, drafts, reviews, diagrams, and validation plans. Use when the user asks to write, draft, review, convert, or prepare an RFC, mentions $to-rfc, Coder RFC templates, architecture proposals, design docs, reviewer traps, prototype-to-RFC, or PRD-to-RFC work.
---

# To RFC

Turn messy product, design, prototype, or implementation context into Coder-style RFC-ready material. Default to context-first synthesis, then draft or review only after claims, decisions, and evidence are clear.

## Quick start

1. Identify the requested mode:
   - `context`: produce a context packet, decision ledger, evidence map, and open questions.
   - `draft`: write a full RFC from a context packet and template.
   - `section`: draft or revise one RFC section.
   - `review`: grill an existing RFC for reviewer traps.
   - `diagrams`: create renderer-safe diagrams and captions.
   - `validation`: produce dogfooding and quality-gate steps.
2. Read the supplied transcript, PRD, prototype notes, branch diff, plan, template, draft, and artifacts. Use [CODER_RFC_TEMPLATE.md](CODER_RFC_TEMPLATE.md) by default unless the user supplies a different template.
3. Extract the user thesis, goals, non-goals, decisions, alternatives, constraints, and unresolved choices.
4. Build an evidence map before making strong claims.
5. Draft or review incrementally, preserving the user's thesis and tone while tightening language.
6. Return RFC material plus reviewer traps, validation needs, and open questions.

If the user simply says `$to-rfc`, start with `context` mode unless they clearly ask for a complete draft.

## Operating rules

- Do not write a generic RFC before mining the available context.
- Ask clarification only when the RFC direction depends on a real unresolved choice.
- Distinguish implemented, verified, partially verified, proposed, and future behavior.
- Treat summaries as leads, not proof. Prefer direct artifacts, code, logs, tests, dogfood evidence, and user-provided documents.
- For Mux session transcripts, use `scripts/transcript_index.py` to create compact analysis artifacts before synthesis.
- Use sub-agents for large inputs or when independent evidence lanes are useful.
- Do not expose hidden reasoning from tool traces or transcripts. Summarize observable actions and decisions.
- Move misplaced content to the right section instead of deleting it.
- Mark unsupported claims as assumptions, future intent, or open questions.

## Workflow

1. **Intake and scope**
   - Confirm mode, target RFC template, target medium, and available artifacts.
   - Infer reasonable defaults when safe. Stop and ask if a choice changes the RFC.

2. **Context harvest**
   - Collect transcript context, user goals, plans, PRDs, branches, diffs, prototypes, tests, dogfood artifacts, diagrams, examples, and prior drafts.
   - For large context, split exploration by evidence lane, not by prose section.

3. **Evidence and decision extraction**
   - Create a decision ledger with current state, proposed state, rationale, evidence, risks, tradeoffs, rollout implication, and verification status.
   - Build an evidence map with file paths, artifacts, commands, screenshots, logs, docs, and user decisions.

4. **Section mapping**
   - Map material into problem, goals, non-goals, proposal, architecture, operational scenarios, requirements, phases, dogfooding, alternatives, and open questions.
   - Adapt templates to the RFC type. Architecture RFCs often need operational scenarios more than product-style user stories.

5. **Draft, revise, or review**
   - Work section by section unless the user asks for a full draft.
   - Preserve user language where it is accurate. Tighten ambiguous terms and remove overclaims.
   - In review mode, identify reviewer traps and propose precise replacement language.

6. **Quality gates**
   - Run claims, historical accuracy, section-purpose, scope, terminology, contradiction, failure-mode, renderer, and dogfood checks before calling the RFC ready.
   - Provide concrete validation and dogfooding steps, including screenshots and video when visual or workflow evidence matters.

## Detailed references

- See [WORKFLOW.md](WORKFLOW.md) for the full RFC synthesis process and sub-agent lanes.
- See [CODER_RFC_TEMPLATE.md](CODER_RFC_TEMPLATE.md) for the default Coder RFC scaffold.
- See [TEMPLATES.md](TEMPLATES.md) for context packet, decision ledger, evidence map, RFC outline, and section templates.
- See [CHECKLISTS.md](CHECKLISTS.md) for quality gates, reviewer traps, diagram checks, and dogfooding checks.
- See [EXAMPLES.md](EXAMPLES.md) for mode examples and prompt patterns.
