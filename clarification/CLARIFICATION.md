# P57 — Clarification & Missing-Info Resolution Contract

## Purpose
Typed contract for detecting missing, ambiguous, invalid, or conflicting task information, asking targeted clarification questions, recording resolution attempts, and deciding whether execution can proceed.

## Gap Taxonomy
| GapType | Description |
|---------|-------------|
| `missing_required` | Required field not provided |
| `missing_optional` | Optional field not provided |
| `ambiguous_value` | Value is vague or has multiple interpretations |
| `invalid_value` | Value fails schema validation |
| `conflicting_values` | Two or more sources provide contradictory values |
| `unsupported_request` | Request is outside agent capability scope |

## Severity
| GapSeverity | Meaning | Blocks? |
|-------------|---------|---------|
| `low` | Minor, can proceed | No |
| `medium` | Notable but tolerable | No |
| `high` | Significant, should resolve | No |
| `blocking` | Cannot proceed | Yes |

Blocking severity must set `blocking=True`. `ready_to_proceed` and `proceed_with_gaps` dispositions reject unresolved blocking gaps.

## Resolution Methods
| Method | Description |
|--------|-------------|
| `ask_user` | Direct question to the user |
| `infer_from_context` | Heuristic or ML-based inference |
| `apply_default` | Use policy-configured default |
| `manual_override` | Explicit human/manager override |
| `defer` | Accept gap, revisit later |
| `escalate` | Route to higher authority |

Methods `ask_user`, `infer_from_context`, `apply_default`, and `manual_override` must include a `proposed_value_ref`.

## Resolution States
| Status | Meaning |
|--------|---------|
| `open` | Gap detected, not yet acted on |
| `question_issued` | Follow-up question sent |
| `answered` | Response received but not yet applied |
| `resolved` | Field value finalized |
| `deferred` | Resolved by deferring |
| `escalated` | Moved up for external decision |
| `closed_unresolved` | Gap closed without resolution |

Resolved, deferred, escalated, and closed_unresolved states require either a `resolved_value_ref` or explicit `notes`.

## Question Strategy
Each gap generates zero or more targeted clarification questions. Questions should:
- Be tied to a specific field
- Not be duplicative (same gap, same question)
- Include response type hints and recommended examples
- Be ordered (lower `question_order` = ask first)

## Policy Rules
| Rule | Enforcement |
|------|-------------|
| Required fields | `required=True` prevents silent defaulting |
| Default policy | `allow_default=False` blocks `apply_default` method |
| Inference policy | `allow_inference=False` blocks `infer_from_context` |
| Defer policy | `allow_defer=True` requires `escalation_threshold` on required fields |
| Max attempts | `max_attempts > 0` limits retries per gap |
| Escalation threshold | `escalation_threshold > 0` controls how many attempts before escalate |

## Clarification Session States
| Status | Meaning |
|--------|---------|
| `in_progress` | Active clarification |
| `completed` | All gaps resolved or gated |
| `escalated` | Sent for external resolution |
| `closed` | Session ended, gaps may remain |

Active and completed question ID sets must not overlap.

## Closure Dispositions
| Disposition | Meaning | Unresolved Blocking Gaps? |
|-------------|---------|--------------------------|
| `ready_to_proceed` | All blockers resolved | Not allowed |
| `proceed_with_gaps` | Non-blockers remain | Not allowed |
| `awaiting_response` | Waiting for user | Must have active questions |
| `rejected` | Task denied | Requires decision reason |
| `escalated` | Needs higher authority | Requires decision reason |

## Validation Rules
1. gap_id, intake_id, field_name, gap_summary must not be blank
2. Blocking severity must have blocking=True
3. All id fields (question_id, attempt_id, etc.) must not be blank
4. question_order must be >= 0
5. ask_user/infer/apply_default/manual_override attempts must include proposed_value_ref
6. resolved/deferred/escalated/closed_unresolved states need value_ref or notes
7. max_attempts and escalation_threshold must be >= 1 when set
8. Required fields with allow_defer must set escalation_threshold
9. Questions must reference valid gap_ids
10. Attempts and field resolutions must reference valid gap_ids
11. Session gap_ids and question_ids must reference valid records
12. Decision remaining_open_gap_ids must reference valid gap_ids
13. awaiting_response requires at least one active question
14. ready_to_proceed and proceed_with_gaps reject unresolved blocking gaps

## Relationship to Earlier Primitives
- **P56 (Hybrid Task Intake)**: P57 processes gaps found by P56's extraction and validation
- **P40/P41 (Execution/Recovery)**: Receive cleaner task objects after clarification
- **P47/P50 (Routing/Roles)**: Route and assign more accurately once gaps are filled
- **P55 (Synthesis)**: Benefits from resolved intent and constraints
