# P61 — Retry, Recovery & Compensation Contract

## Purpose
Typed contract for classifying failures, applying retry policies, preserving recovery context, and executing compensation plans for side-effecting work in agentic runtimes.

## Resilience Flow
1. **Classify** — the runtime categorizes the failure (transient, timeout, dependency, validation, policy, partial side effect, unknown, terminal).
2. **Decide** — based on failure category and retry policy, determine if retry, recovery, compensation, or escalation is appropriate.
3. **Retry** — if transient/recoverable, apply explicit backoff strategy with max attempts, delay, jitter, and stop conditions.
4. **Recover** — preserve execution state (checkpoint, intent) and resume from the last known good point.
5. **Compensate** — if side effects were committed, register and execute compensating actions in deterministic order.
6. **Resolve** — record final disposition: retrying, recovered, compensated, escalated, aborted, or terminated.

## Failure Taxonomy

### FailureCategory
| Category | Meaning | Retryable? |
|----------|---------|------------|
| `transient_error` | Temporary glitch, likely to succeed on retry | Yes |
| `timeout` | Deadline exceeded, may need recovery | Depends |
| `dependency_failure` | External service failed | May be |
| `validation_failure` | Input or constraint violation | No |
| `policy_block` | Policy/guardrail prevented execution | No |
| `partial_side_effect` | Some work committed, then failure | No (compensate) |
| `unknown_state` | Cannot determine what happened | No (manual) |
| `terminal_error` | Fatal, cannot proceed | No |

### RetryStrategy
| Strategy | Behavior |
|----------|----------|
| `none` | No retry allowed |
| `fixed` | Constant delay between attempts |
| `linear_backoff` | Delay increases linearly |
| `exponential_backoff` | Delay doubles each attempt |
| `manual_retry` | Human must trigger retry |

### RecoveryMode
| Mode | Description |
|------|-------------|
| `resume_from_checkpoint` | Restore from saved checkpoint |
| `replay_last_step` | Re-execute the last step |
| `replay_from_intent` | Reconstruct from intent/plan |
| `handoff_recovery` | Hand off to another agent/role |
| `manual_recovery` | Human must intervene |
| `no_recovery` | No recovery path available |

### CompensationStatus
| Status | Meaning |
|--------|---------|
| `not_required` | No side effects to compensate |
| `planned` | Compensation actions defined |
| `in_progress` | Executing compensating actions |
| `completed` | All compensations succeeded |
| `failed` | At least one compensation failed |
| `escalated` | Compensation failure escalated |

### FailureDisposition
| Disposition | Meaning |
|-------------|---------|
| `retrying` | Currently retrying |
| `recovered` | Successfully recovered |
| `compensated` | Side effects compensated |
| `escalated` | Escalated to human or higher authority |
| `aborted` | Execution aborted |
| `terminated` | Permanently terminated |

## Validation Rules
1. All IDs, scope_refs, and failure summaries must be non-empty
2. `retry_strategy=none` requires `max_attempts=0` and no retry attempts
3. `manual_retry` requires positive `max_attempts`
4. `resume_from_checkpoint` requires `checkpoint_ref`
5. `replay_from_intent` requires `intent_state_ref`
6. `in_progress`/`failed` compensation actions require `action_notes`
7. Compensation actions must have unique `execution_order`
8. Actions present with `plan_status=not_required` is invalid
9. `unknown_state` cannot have `recovered`/`compensated` disposition
10. Failed compensation actions cannot have `plan_status=completed`

## Relationship to Earlier Primitives
- **P45 (Step)**: Step execution emits failure records on error
- **P49 (Hooks)**: Pre/post hooks trigger failure handlers
- **P52/P54 (Graph/Parallel)**: Branch-local retry and recovery
- **P59 (Budget)**: Budget logic may constrain retry attempts
- **P60 (Risk/Escalation)**: Recovery/compensation escalates when risk is high or retries exhausted

## File Structure
```
recovery/
  RECOVERY.md                              — this file
  templates/
    failure_record.json                     — failure input schema
    retry_policy.json                       — retry config schema
    recovery_plan.json                      — recovery plan schema
    compensation_plan.json                  — compensation plan schema
```
