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

## Expected Response Shape
For each task provide:
1. Task understanding
2. Planned changes
3. Files touched
4. Verification performed
5. Result
6. Risks
