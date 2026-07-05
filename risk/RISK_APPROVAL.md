# P60 — Risk, Escalation & Human-Approval Contract

## Purpose
Typed contract for assessing risk across multiple dimensions, applying escalation thresholds, routing approval requests, recording human approval decisions, and determining whether execution proceeds, pauses, reworks, rejects, or escalates further.

## Core Flow
1. **Assess** — the runtime evaluates an action/task across risk dimensions (policy, safety, security, privacy, financial, legal, quality, operational).
2. **Compare** — the assessment is compared against threshold policies.
3. **Escalate** — if thresholds are crossed, an escalation request is created and routed to the correct authority.
4. **Approve** — the human-in-the-loop reviews context and approves, rejects, or imposes constraints.
5. **Decide** — the final disposition determines next steps: proceed, pause, rework, reject, or escalate further.

## Risk Taxonomy

### RiskCategory
| Category | Description |
|----------|-------------|
| `policy` | Policy compliance risk |
| `safety` | Physical or operational safety |
| `security` | Security vulnerability or threat |
| `privacy` | Data privacy or PII exposure |
| `financial` | Monetary cost or budget risk |
| `legal` | Legal or regulatory compliance |
| `quality` | Quality degradation risk |
| `operational` | Operational disruption risk |

### RiskLevel
| Level | Description |
|-------|-------------|
| `low` | Minimal impact, routine action |
| `medium` | Moderate impact, requires awareness |
| `high` | Significant impact, requires approval |
| `critical` | Severe impact, requires mandatory approval |

## Escalation Triggers
| Trigger | When Fired |
|---------|------------|
| `risk_threshold` | Risk score or level crosses policy threshold |
| `budget_overrun` | Budget limits exceeded (P59 integration) |
| `policy_exception` | Policy violation requiring exception |
| `uncertainty_exceeded` | Uncertainty score above threshold |
| `approval_required_action` | Action type is pre-configured for approval |
| `stalled_execution` | Execution paused pending approval for too long |
| `manual_request` | Human or system manually triggers escalation |

## Approval Model

### ApprovalStatus
| Status | Meaning |
|--------|---------|
| `not_required` | No approval needed for this level |
| `pending` | Awaiting human decision |
| `approved` | Human approved the action |
| `rejected` | Human rejected the action |
| `timed_out` | Approval window expired |
| `withdrawn` | Escalation or request was withdrawn |

### EscalationDisposition
| Disposition | Meaning | Execution Continues? |
|-------------|---------|---------------------|
| `proceed` | Action may proceed | Yes |
| `proceed_with_constraints` | Proceed with imposed constraints | Yes (constrained) |
| `pause_for_review` | Pause and wait for human decision | No |
| `return_for_rework` | Return to agent for rework | No |
| `reject` | Permanently reject the action | No (aborted) |
| `escalate_further` | Escalate to higher authority | No |

## Validation Rules
1. All IDs and scope refs must be non-empty
2. `risk_score` and `uncertainty_score` bounded 0–100
3. `requires_human_approval=True` cannot have `default_disposition=proceed`
4. High/critical minimum risk levels require `requires_human_approval=True`
5. Approved/rejected decisions require decider identity and reason
6. `proceed_with_constraints` requires resume constraints
7. Timed-out approvals require an escalation path with fallback
8. `required_approver_count` must be positive when approval is required
9. Envelope-level: if `requires_human_approval=True`, auto-proceed rejected without sufficient approved records

## Relationship to Earlier Primitives
- **P59 (Budget)**: Budget overruns trigger escalation via `budget_overrun` trigger type
- **P58 (Completion)**: Completion assessment can trigger risk review before accept
- **P57 (Clarification)**: Unresolved ambiguity can escalate as `uncertainty_exceeded`
- **P55 (Synthesis)**: Can require approval before final merge
- **P50 (Roles)**: Escalation paths map to role IDs for approval routing
- **P49 (Hooks)**: Pre/post hooks can trigger risk assessment before execution
- **P44/P45 (Loop/Step)**: Step execution pauses for pending approvals

## File Structure
```
risk/
  RISK_APPROVAL.md                       — this file
  templates/
    risk_assessment.json                  — assessment input schema
    escalation_request.json               — escalation creation schema
    approval_record.json                  — human approval record schema
    decision_record.json                  — final decision record schema
```
