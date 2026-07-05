# Execution Budget & Resource Envelope Contract (P59)

## Purpose
Define how budgets are scoped, tracked, and enforced across agentic runtimes — covering allocation, reservation, consumption, threshold warnings, and overrun decisions in a single resource envelope.

## Core Concepts

### Budget Scope
Budgets can be scoped to any level of execution: **session**, **run**, **task**, **agent**, **role**, **branch**, **tool_call**, or **model_call**. Each scope has a `scope_ref` that points to the corresponding entity.

### Resource Types
- **tokens** — LLM token consumption
- **currency_cost** — monetary cost in any currency
- **compute_time_ms** — wall-clock or CPU time in milliseconds
- **api_calls** — number of external API invocations
- **storage_bytes** — storage capacity in bytes
- **custom** — user-defined resource

### Budget Lifecycle
1. **Planned** — budget created, no activity
2. **Active** — reservations and usage being recorded
3. **Warning** — one or more thresholds crossed
4. **Overrun** — hard limits exceeded, decisions pending
5. **Exhausted** — all resources consumed or execution stopped
6. **Closed** — final state, no further changes

### Thresholds (Soft vs Hard)
- **Soft** — triggers alert, allows override or increase
- **Hard** — enforces stop, requires action definition

## Models

### ExecutionBudgetEnvelope
The top-level budget object with scope, references to planning/execution budgets, and a parent budget for hierarchical budgeting.

### ResourceBudgetLine
Per-resource tracking with `allocated_amount`, `reserved_amount`, `consumed_amount`, and auto-computed `remaining_amount >= 0`. NaN/Inf rejected.

### ResourceReservationRecord
Reserves a portion of a budget line for upcoming work. Linked to a `budget_line_id`. Optional `expires_at` and `request_ref`.

### ResourceUsageRecord
Records actual consumption against a budget line. Stores `context_ref`, `actor_ref`, and `source_event_ref` for traceability.

### BudgetThresholdPolicy
Defines conditions (by value or percent) that trigger actions when crossed. Soft vs hard severity, with notification targets for soft thresholds.

### BudgetAlertRecord
Time-stamped alert when a threshold is crossed. Stores `trigger_value` and `recommended_action`.

### BudgetDecisionRecord
Records decisions on what to do when a budget limit is reached or approached. Supports `reallocate` (requires `reallocated_from_budget_id`), `require_approval`, `adjust_scope`, `stop_execution`, `ignore_override`.

### BudgetResourceEnvelope
Assembles a budget with its lines, reservations, usage records, thresholds, alerts, and decisions. Validates that cross-references between sub-models match.

## Overrun Policy
- `remaining_amount` can be negative (overrun), but the line's `remaining_amount` must equal `allocated - reserved - consumed`
- Hard thresholds require a non-empty `action_on_cross`
- Reallocation decisions require `reallocated_from_budget_id`
- Cross-envelope references: reservations/usage/thresholds/alerts must reference valid `budget_line_id` within the envelope; decisions must reference the envelope's `budget_id`

## File Structure
```
budget/
  BUDGET.md         — this file
  PROTOCOL.md       — runtime protocol guide
  templates/
    budget_request.md
    threshold_alert.md
    budget_decision.md
    budget_envelope_report.md
```
