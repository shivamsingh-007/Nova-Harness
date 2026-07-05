# AGENTS.md

## Project Identity
This repository builds a harness system for AI coding agents.
The purpose is to improve reliability, control, verification, and observability beyond raw model behavior.

## Repository Rules
- Build one primitive at a time.
- Do not implement the full harness in one step.
- Keep modules independent and composable.
- Favor explicit schemas, typed boundaries, and inspectable workflows.
- Do not introduce multi-agent orchestration unless the current task explicitly requires it.

## Safety Boundaries
- Do not modify secrets, deployment config, CI/CD, or infrastructure unless explicitly requested.
- Do not perform large refactors for small local issues.
- Keep changes bounded to the task scope.

## Verification Standard
- A task is not done until receipts exist.
- Prefer verification in this order:
  1. targeted test
  2. lint
  3. type check
  4. broader verification
- If verification fails, report the exact failure and attempt only bounded recovery.

## Loop Lifecycle Responsibilities
When running the loop (P44), follow this discipline:
- **Always read** `todo.json`, `state.md`, `loop_memory.md`, and `lessons.md` before starting a new iteration.
- **Always update** `loop_execution.md`, `loop_memory.md`, `todo.json`, and `state.md` after each iteration.
- **Always verify** before marking anything done (run tests, check acceptance criteria).
- **Always stop** on repeated no-progress, verification failure, or external blockers.
- **Always escalate** when credentials are missing, security risks detected, or requirements are ambiguous.
- **Never commit** without verification evidence.
- **Never skip** artifact updates.
- **Never modify** secrets, deployment config, CI/CD, or infrastructure unless explicitly tasked.

## Expected Response Shape
For each task provide:
1. Task understanding
2. Planned changes
3. Files touched
4. Verification performed
5. Result
6. Risks

## Role Map (P50)
| Role | Specialization | Autonomy |
|------|---------------|----------|
| Manager | coordination_specific | supervisory |
| Specialist | domain_specific | bounded_execution |
| Planner | generalist | advisory_only |
| Executor | tool_specific | bounded_execution |
| Reviewer | verification_specific | bounded_execution |
| Verifier | verification_specific | bounded_execution |
| Retriever | retrieval_specific | bounded_execution |
| Summarizer | generalist | advisory_only |
| Coder | coding_specific | bounded_execution |
| Tool Operator | tool_specific | bounded_execution |

Role definitions in `roles/<role_name>/ROLE.md`. Registry at `roles/registry.json`.
Assignment records link roles to agent instances via `RoleAssignmentRecord`.
