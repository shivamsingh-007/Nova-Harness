# Loop Specification

## Identity
- **Name**: Nova Harness Running Loop
- **Purpose**: Drive bounded autonomous feature development, repair, verification, refactoring, research, and maintenance with explicit iteration control, verification gates, and durable cross-session memory.

## Trigger Conditions
- Manual invocation via `/loop <goal-type> <objective>`
- Scheduled maintenance cycles
- Event-driven (failure detected, CI trigger)
- Recovery resume after session interruption

## Goal Types
| Type       | Description                                      |
|------------|--------------------------------------------------|
| build      | Implement new feature or component               |
| repair     | Fix a bug or resolve a regression                |
| verify     | Run verification gates on existing work          |
| refactor   | Restructure code without changing behavior       |
| research   | Investigate options, patterns, or architectures  |
| maintain   | Routine upkeep: deps, lint, docs, cleanup        |

## Entry Criteria
- Clear objective defined
- Maximum iteration budget set
- At least one task available in todo.json
- Required artifacts exist (todo.json, state.md, loop_memory.md)

## Exit Criteria
- Objective achieved and verified
- No work remaining
- Max iterations exhausted
- Budget exceeded
- Repeated no-progress detected
- Verification failed
- External blocker requires human intervention

## Stop Conditions
- All acceptance criteria met ✓
- max_iterations reached without completion
- max_no_progress_iterations consecutive attempts with zero progress
- Verification failure on critical path
- Escalation condition triggered that requires human approval

## Success Definition
- All cycles completed with PASS verification
- All acceptance criteria for the objective documented as met
- Artifacts updated (memory, todo, state, lessons)
- Clean handoff state left for next session

## Bounded Autonomy Rules
- One task per iteration (no unbounded multi-tasking)
- Verify before marking done
- Update artifacts every iteration
- Stop on repeated no-progress
- Escalate on uncertainty, security issues, or external blockers
- Never commit without verification

## Required Artifacts
- `loop.md` — this specification (changes rarely)
- `loop_execution.md` — live execution ledger (per-iteration updates)
- `loop_memory.md` — compact next-session memory (per-iteration updates)
- `todo.json` — structured task backlog (per-iteration updates)
- `features.json` — feature registry (per-milestone updates)
- `state.md` — project/runtime state (per-iteration updates)
- `lessons.md` — durable lessons (per-meaningful-failure/success)
- `loop_rules.md` — operational rules (per-evolution)
- `prompts.md` — canonical prompts (per-stable-change)
- `git_policy.md` — commit/checkpoint conventions (rare updates)
- `AGENTS.md` — agent role rules (per-workflow-change)

## Iteration Sequence
1. **INTAKE** — Read todos, memory, state, lessons. Assess current objective.
2. **PLAN** — Select one task. Define approach and acceptance criteria.
3. **EXECUTE** — Perform the work. Touch only the bounded scope.
4. **VERIFY** — Run tests, check acceptance criteria. Record result.
5. **UPDATE_STATE** — Update loop_execution.md, loop_memory.md, todo.json, features.json, state.md, lessons.md as needed.
6. **STOP_CHECK** — Evaluate stop conditions. Continue, escalate, or terminate.
7. **HANDOFF** — If stopping, leave clean state and next-action summary.

## Escalation Conditions
- Task requires credentials or secrets not available
- External API or service is down
- Security or data-integrity risk detected
- Ambiguous requirements that need human clarification
- Repeated failure with no identified root cause
- Scope exceeds bounded autonomy (e.g., cross-cutting refactor)
