# Execution Budget Protocol (P59)

## Runtime Flow
1. **Create** `ExecutionBudgetEnvelope` with `budget_status: planned`
2. **Activate** → `active` status, begin recording lines, reservations, usage
3. **Monitor** threshold policies — soft thresholds trigger alerts, hard thresholds enforce stop
4. **Decide** on overruns via `BudgetDecisionRecord` (reallocate, approve, adjust scope, stop, ignore)
5. **Close** → `exhausted` or `closed` when execution completes

## Key Constraints
| Rule | Enforced By |
|------|-------------|
| Lines reference their envelope's budget_id | `BudgetResourceEnvelope` validator |
| Reservations/usage/thresholds/alerts reference valid line IDs | `BudgetResourceEnvelope` validator |
| Decisions reference the envelope's budget_id | `BudgetResourceEnvelope` validator |
| Reallocation requires source budget_id | `BudgetDecisionRecord` validator |
| Hard thresholds must have an action | `BudgetThresholdPolicy` validator |
| NaN/Inf amounts rejected | Field validators on `ResourceBudgetLine`, `ResourceReservationRecord`, `ResourceUsageRecord` |

## Template Usage
| Template | When |
|----------|------|
| `budget_request.md` | Proposing a new budget |
| `threshold_alert.md` | Notifying on threshold cross |
| `budget_decision.md` | Recording an overrun decision |
| `budget_envelope_report.md` | Reporting full budget state |

## Relationship to Earlier Primitives
- **P53–P55 (Messaging/Parallel/Synthesis)**: Budget consumption tracked against parallel branches and merge barriers
- **P44/P45 (Loop/Step)**: Step-level budget constraints enforced via `budget_line_id` refs
- **P58 (Completion)**: Budget exhaustion can trigger completion assessment
- **P50 (Roles)**: `approved_by` references manager/verifier roles
