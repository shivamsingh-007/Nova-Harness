# P58 — Acceptance Criteria & Definition-of-Done Contract

## Purpose
Typed contract for defining task-specific acceptance criteria, reusable definition-of-done checks, collecting completion evidence, assessing pass/fail, and issuing final completion decisions.

## Two-Layer Design
Acceptance criteria and definition of done are separate but linked:

- **Acceptance criteria**: task-specific conditions that must be satisfied for a single item. Describes *what* the task must achieve.
- **Definition of done**: universal quality baseline applied across all completed work. Describes the *quality bar*.

## Core Types

### CriterionType
| Type | Description |
|------|-------------|
| `functional` | Behavioral requirement |
| `output` | Deliverable artifact |
| `quality` | Quality threshold |
| `constraint` | Non-functional boundary |
| `approval` | Sign-off requirement |
| `evidence` | Proof of completion |

### CriterionStatus
| Status | Meaning |
|--------|---------|
| `not_started` | Not yet evaluated |
| `in_progress` | Being worked on |
| `met` | Satisfied |
| `failed` | Not satisfied |
| `waived` | Explicitly bypassed with notes |

### DoneCheckType
| Type | Description |
|------|-------------|
| `quality_gate` | Code quality or style |
| `verification_gate` | Test/verification pass |
| `documentation_gate` | Docs updated |
| `policy_gate` | Policy compliance |
| `release_gate` | Release readiness |

### DoneStatus
| Status | Meaning |
|--------|---------|
| `not_checked` | Not yet evaluated |
| `passed` | Satisfied |
| `failed` | Not satisfied |
| `waived` | Explicitly bypassed with notes |

### CompletionDisposition
| Disposition | Meaning | Release Ready? |
|-------------|---------|----------------|
| `accepted` | All criteria met, all checks passed | Optional |
| `accepted_with_caveats` | Accepted with follow-up actions | No |
| `needs_rework` | Must be improved | No |
| `rejected` | Will not be accepted | No |
| `deferred` | Postponed | No |

## Validation Rules
1. All IDs and descriptions must be non-blank
2. Required criteria/checks waived without notes are rejected at model and envelope level
3. `accepted` requires all required criteria met/waived and all required DoD checks passed/waived
4. Waived required items must have notes explaining the waiver
5. `accepted_with_caveats` must include followup_actions or decision_reason
6. `rejected`/`needs_rework` must include decision_reason
7. `release_ready=true` requires all required release-gate DoD checks passed
8. Evidence records must reference valid criterion or done check IDs (or be null)

## Waiver Policy
Required criteria and DoD checks cannot be silently waived. Waivers must include notes explaining the decision. The envelope validator enforces this at two levels:
1. The individual check/criterion model rejects required+waived+no-notes
2. The envelope's `accepted` disposition validator also rejects it

## Relationship to Earlier Primitives
- **P56/P57 (Intake/Clarification)**: Define what goes into a task; P58 defines completion
- **P44/P45 (Loop/Step)**: Acceptance criteria act as loop/step targets
- **P54/P55 (Parallel/Synthesis)**: Criteria and DoD used during merge and finalization
- **P39/P24 (Evaluation/Quality)**: Quality signals align with formal done checks
- **P50 (Roles)**: Verifier/reviewer roles act against explicit criteria
