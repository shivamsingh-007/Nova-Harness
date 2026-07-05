# Loop Rules

## Read Discipline
- Always read `todo.json`, `state.md`, `loop_memory.md`, and `lessons.md` before starting a new iteration.
- Always read `loop.md` and `loop_rules.md` at session start.
- Always read relevant model/tests/examples before touching a primitive.

## Selection Discipline
- Select exactly one bounded task per iteration.
- Do not multi-task across iterations.
- Prioritize blocked-by dependencies first.

## Execution Discipline
- Touch only the scope defined by the selected task.
- Do not refactor unrelated code.
- Add tests for new functionality.
- Keep changes minimal and focused.

## Verification Discipline
- Run tests after every change.
- Verify acceptance criteria are met before marking a task done.
- Record verification result (PASS/FAIL) in the cycle record.

## Update Discipline
- After each iteration, update:
  - `loop_execution.md` — actions, verification status, next target
  - `loop_memory.md` — current mission, blocker, top tasks, next action
  - `todo.json` — task status changes
  - `state.md` — architecture state, what changed
- After meaningful failure or success, update:
  - `lessons.md` — date, context, root cause, fix, reusable lesson
- After feature milestone, update:
  - `features.json` — feature status, quality signals
- When a lesson recurs 3+ times, promote to `loop_rules.md`

## Stop Discipline
- Stop on any of:
  - Objective achieved and verified.
  - max_iterations reached.
  - max_no_progress consecutive iterations with delta=none.
  - Verification failure on critical path.
  - Security or data-integrity risk.
  - External blocker requiring human decision.
- Never silently continue past a stop condition.

## Escalation Discipline
- Escalate when:
  - Credentials or secrets are missing.
  - External service is unreachable.
  - Security risk is detected.
  - Requirements are ambiguous.
  - Repeated failure with unknown root cause.
  - Scope exceeds bounded autonomy.

## Capability Negotiation Rules (P62)
- Always run compatibility evaluation before routing, activating a skill, or assigning a role.
- required-level gaps that are blocking: reject or reroute (no silent proceed).
- proceed_with_fallbacks requires at least one gap recorded and a fallback selected.
- incompatible with proceed requires an approved_override_ref — no implicit bypass.
- Negotiated capability sets are session-effective contracts — both sides must respect them.

## Retry / Recovery / Compensation Rules (P61)
- Retry only transient or retryable failures — never retry terminal or validation errors.
- On transient failure: apply retry policy (exponential_backoff by default) with max_attempts ceiling.
- After max retries exhausted: switch to recovery or compensation, not infinite retry.
- If side_effects_present: register compensation plan before attempting recovery.
- If unknown_state: do not auto-recover or auto-compensate; escalate to manual recovery.
- Recovery should reference a checkpoint or intent state when available.

## Approval Pause / Resume
- If a step triggers human approval (P60), pause execution and wait for `approved` or `rejected` disposition.
- Do not proceed while `pending` approval status exists.
- On `approved` or `proceed_with_constraints`: resume with imposed constraints.
- On `rejected` or `return_for_rework`: abort current path and return to planning.
- On `timed_out`: follow escalation path to fallback approvers.

## Always / Never
- Always verify before marking done.
- Always update artifacts after execution.
- Always stop on repeated no-progress.
- Never mark completed without verification evidence.
- Never skip artifact updates.
- Never commit unverified changes.
- Never modify secrets, deployment config, or CI/CD unless explicitly tasked.
