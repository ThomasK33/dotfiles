# To RFC Examples

## Example: `$to-rfc` with a large transcript

User asks: "Turn this long prototype chat into RFC material."

Response shape:

1. State that you will start in `context` mode.
2. Build a transcript index if needed, for example `scripts/transcript_index.py <session> --output-dir <analysis-dir>`.
3. Split sub-agents by evidence lane when the transcript is large.
4. Synthesize:
   - thesis,
   - decision ledger,
   - evidence map,
   - scope ledger,
   - section map,
   - reviewer traps,
   - dogfood plan,
   - open questions.
5. Ask whether to draft the full RFC or a specific section next.

## Example: problem statement section

User asks: "Help me write only the Problem Statement."

Do:

- Gather evidence for current pain and why it matters.
- Keep solution details minimal.
- Return one polished section and a short evidence note.

Do not:

- Fill the whole template.
- Hide open questions in prose.
- Claim performance or scalability wins without evidence.

## Example: architecture RFC user stories

If classic user stories feel forced, suggest operational scenarios:

```md
### Existing resource continues through the new path

1. Given an existing resource with active users, the system discovers eligible work without requiring recreation.
2. The responsible runtime claims the work through the authoritative control plane.
3. If the runtime restarts, durable state allows another eligible runtime to resume or recover.
4. Users see the same external behavior as before.
```

Explain why this better serves an architecture RFC.

## Example: reviewer trap replacement

Original:

```md
This makes the system scalable.
```

Replacement:

```md
This separates the scaling characteristics of request coordination from long-running execution, so each path can be scaled and operated independently.
```

Reason: the replacement is narrower and easier to defend.

## Example: diagram prompt

```md
Create two Mermaid diagrams for this RFC:

1. A detailed architecture diagram showing authority, execution, durable state, and external services.
2. A Notion-friendly version with fewer nodes and short labels.

Use only portable Mermaid syntax. Include captions and state where each diagram belongs in the RFC.
```

## Example: validation output

```md
## Dogfooding and Validation

### Setup

- Start the development environment with feature flag `<flag>` enabled.
- Configure provider credentials through `<path or UI>`.
- Prepare test data `<data>`.

### Scenarios

| Scenario | Steps | Expected evidence | Artifact |
|---|---|---|---|
| Happy path | Create resource, trigger workflow, observe completion | UI screenshot, logs, transcript, test output | `artifacts/happy-path.*` |
| Recovery | Restart runtime mid-workflow | State resumes or fails safely | `artifacts/recovery.*` |
| Disable path | Turn feature flag off | Old path remains functional | `artifacts/disable.*` |

### Automated checks

- `<command>`

### Known gaps

- `<gap>` remains future work and is not required for this RFC.
```
