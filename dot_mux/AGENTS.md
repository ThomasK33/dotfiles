# Global personal preferences

## Development

Please produce minimal code to implement a given task or remediate the issue while preserving existing functionality and tests.

### Planing

When planning changes to the codebase, make sure to include not only clear acceptance criteria but also a dedicated section on dogfooding the changes.
For example: 
- If the changes are conducted to a cli, this section should include dedicated instructions on how to set up a testing environment and how to dogfood the changes.
- If the changes are frontend- or web app-related, this section should include instructions on how to set up a dev server and use something like agent-browser to interact with the website. (Verification if functional can then be performed using snapshots, if visual verification is required, then create screenshots and `attach_file` them)

Dogfooding and self-verifying changes should always include screenshots and video recordings so a reviewer can verify the steps you took.

Make sure to include dogfooding/quality gates in between phases, to make sure that you are delivering what you are claiming to.

### Defensive Programming

You MUST apply defensive programming techniques as much as possible.
Use asserts to verify passed in arguments to a function and for values that
those functions return to be sure they are what you expect them to be.
We aim for a quick crash and burn development style, which immediately
yields the wrong assumptions that we made, helping to identify issues quickly.

Here are some guidelines:

- Don't wait for bugs to happen; use startup checks.
- If appropriate, use a second algorithm to validate your results in debug builds
  with assertions.
- Don't hide bugs when you program defensively.
- Use assertions to detect impossible conditions.
- Either remove implicit assumptions, or assert that they are valid.
- Assertions and DEBUG code are fast for tests that reveal bugs,
  never for error handling.
- Don't waste people's time. Document unclear assertions.

### Correctness

Always read the files before making any claims about their contents.
If uncertain about anything, refrain from making unverified and incorrect
claims. Clearly indicate any uncertainty and ask for clarification if needed.
Accuracy is critical.

## Pull Requests

### Descriptions

- Public work (issues/PRs/commits) must include this footer in the body:

  ```md
  ---
  _Generated with [\`mux\`](https://github.com/coder/mux) • Model: `<modelString>` • Thinking: `<thinkingLevel>`_
  <!-- mux-attribution: model=<modelString> thinking=<thinkingLevel> -->
  ```

  Always check `$MUX_MODEL_STRING` and `$MUX_THINKING_LEVEL` via bash before
  creating PRs, include them in the footer if set.

- If a plan file exists and is relevant to the PR (i.e., it describes what was
  implemented), you must write your pull request body description into a temporary
  file or a heredoc and call the appropriate command.
  Then include the plan contents into that heredoc or temporary file (if it's a
  file, make sure that it's either a file created via `mktemp` or that it contains
  the name of the workspace to avoid race conditions) verbatim by appending it
  using the bash tool (redirects/pipes), so that the PR body has the following
  format and helps reviewers understand the agent's goals:

  ```markdown
  PULL REQUEST DESCRIPTION HERE

  ---

  <details>
  <summary>📋 Implementation Plan</summary>

  CONTENTS OF THE PLAN FILE

  </details>

  ---
  _Generated with `mux`_
  ```

  Finally, use the `-F, --body-file file       Read body text from file (use "-" to read from standard input)` flag on the `gh pr new` command to use
  the temporary file as body text when creating the pull request.

  ---

  # General guidelines

  Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

  **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

  ## 1. Think Before Coding

  **Don't assume. Don't hide confusion. Surface tradeoffs.**

  Before implementing:

  - State your assumptions explicitly. If uncertain, ask.
  - If multiple interpretations exist, present them - don't pick silently.
  - If a simpler approach exists, say so. Push back when warranted.
  - If something is unclear, stop. Name what's confusing. Ask.

  ## 2. Simplicity First

  **Minimum code that solves the problem. Nothing speculative.**

  - No features beyond what was asked.
  - No abstractions for single-use code.
  - No "flexibility" or "configurability" that wasn't requested.
  - No error handling for impossible scenarios.
  - If you write 200 lines and it could be 50, rewrite it.

  Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

  ## 3. Surgical Changes

  **Touch only what you must. Clean up only your own mess.**

  When editing existing code:

  - Don't "improve" adjacent code, comments, or formatting.
  - Don't refactor things that aren't broken.
  - Match existing style, even if you'd do it differently.
  - If you notice unrelated dead code, mention it - don't delete it.

  When your changes create orphans:

  - Remove imports/variables/functions that YOUR changes made unused.
  - Don't remove pre-existing dead code unless asked.

  The test: Every changed line should trace directly to the user's request.

  ## 4. Goal-Driven Execution

  **Define success criteria. Loop until verified.**

  Transform tasks into verifiable goals:

  - "Add validation" → "Write tests for invalid inputs, then make them pass"
  - "Fix the bug" → "Write a test that reproduces it, then make it pass"
  - "Refactor X" → "Ensure tests pass before and after"

  For multi-step tasks, state a brief plan:

  ```
  1. [Step] → verify: [check]
  2. [Step] → verify: [check]
  3. [Step] → verify: [check]
  ```

  Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

  ---

  **These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
