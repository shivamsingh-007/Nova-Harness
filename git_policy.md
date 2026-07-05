# Git Commit & Checkpoint Policy

## Commit Triggers
- Commit only on **verified progress**:
  - All new tests pass.
  - Lint passes.
  - Acceptance criteria for the task are met.
- Commit message template:
  ```
  <type>: <brief description>

  <body — optional, include lessons or rationale if relevant>

  Closes #<issue>  (if applicable)
  ```
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`

## Checkpoint vs Commit
- **Checkpoint** = save work in progress without full verification (local branch, no push).
  - Use for: partial progress, mid-migration, exploratory work.
  - Do NOT push checkpoints.
- **Commit** = verified, ready-to-share progress.
  - Use for: completed tasks, passing tests, documented changes.
  - Safe to push.

## When NOT to Commit
- Broken state (tests failing, lint errors).
- Unverified changes (no test run).
- Partial refactor with dangling references.
- Secrets or credentials in code.
- Generated files that should be .gitignored.

## Required Artifact Sync Before Commit
- `todo.json` updated with current task status.
- `state.md` updated with what changed.
- `loop_memory.md` updated with next action.
- `loop_execution.md` updated with this iteration's actions.
- `lessons.md` appended if new lessons were learned.

## Lessons in Commit Body
- If the commit resolves a failure or applies a lesson, include in the body:
  ```
  Lesson: <one-line summary of what was learned>
  ```
- This makes `git log` searchable for learning history.

## Branch Policy
- Work on feature/fix branches.
- Keep branches short-lived (1-3 commits).
- Rebase onto main before final verification.
- Squash commits on merge for clean history.

## Emergency Commits
- If you must commit broken state (e.g., handoff to another agent), prefix:
  ```
  [wip] <description>
  ```
  And add a `# ponytail:` or `# TODO:` comment explaining the state.
