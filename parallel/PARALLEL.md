# P54 — Parallel Work & Join Contract

## Purpose
Typed contract for controlled fan-out/fan-in workflow patterns: split work into multiple branches, supervise them, join under an explicit policy, and record merge outcomes.

## Core Types

### ParallelWorkRequest
Parent request that defines why and how work is parallelized.

- **parallel_request_id** — unique identifier
- **parent_run_id, parent_step_id, parent_graph_node_id** — orchestration context (P52 graph integration)
- **parallelization_mode** — how branches are created (see enum)
- **objective** — why parallelization is being used
- **branching_reason** — rationale for independent branch scopes
- **requested_branch_count** — expected number of branches
- **join_policy** — how branches rejoin (see enum)

### BranchAssignmentRecord
One parallel branch with bounded scope.

- **branch_id** — unique branch identifier
- **assigned_agent_id / assigned_role_id** — who executes
- **scope_summary** — what work this branch does
- **input_refs** — specs, docs, schemas for this branch
- **expected_output_types** — what the branch should produce
- **dependency_refs** — inter-branch dependencies
- **conflict_risk** — anticipated merge risk level
- **status** — planned → ready → running → completed/failed/cancelled/blocked
- **deadline_at** — optional time bound

### BranchOutputRecord
One branch's return value.

- **branch_output_id, branch_id** — linkage
- **status** — final branch status
- **result_summary** — what was produced
- **output_refs, evidence_refs, changed_artifact_refs** — what files were created/modified
- **confidence** — 0.0–1.0 bounded quality estimate

### BranchConflictRecord
Captures merge/scope conflicts at join time.

- **conflict_id, branch_ids** — which branches conflicted
- **conflict_type, conflict_summary** — what the conflict is
- **proposed_resolution** — suggested fix
- **requires_review** — whether human/manager intervention is needed

### JoinRequirementRecord
What the join is waiting for.

- **required_branch_ids** — must-complete branches
- **optional_branch_ids** — nice-to-have branches
- **required_completion_count** — minimum branches needed
- **accept_partial_failures** — whether failed branches block the join
- **deadline_policy** — time bound for the join

### JoinExecutionRecord
The actual join event.

- **join_id, join_policy, join_status** — what policy was used and what state it reached
- **completed_branch_ids, failed_branch_ids, late_branch_ids** — branch disposition
- **selected_output_refs** — which outputs made it through
- **join_notes** — freeform notes about the join

### MergeResultRecord
The merge outcome after the join.

- **merge_id, join_id** — linkage
- **merge_outcome** — success / partial / conflict / rejected / needs_review
- **merged_output_refs, rejected_output_refs** — which outputs were/were not merged
- **conflict_refs** — references to conflict records
- **review_required** — whether external review is needed
- **final_summary, next_action** — what happened and what to do next

### Enums

| Enum | Values |
|------|--------|
| **ParallelizationMode** | `fan_out_all`, `fan_out_selected`, `conditional_parallel`, `verification_parallel`, `speculative_parallel` |
| **BranchStatus** | `planned`, `ready`, `running`, `waiting`, `completed`, `failed`, `cancelled`, `blocked` |
| **JoinPolicy** | `wait_for_all`, `wait_for_quorum`, `wait_for_first_success`, `wait_for_required_set`, `manual_join` |
| **JoinStatus** | `pending`, `waiting`, `ready_to_merge`, `merged`, `partial_merge`, `failed`, `cancelled` |
| **MergeOutcome** | `success`, `partial`, `conflict`, `rejected`, `needs_review` |

## Validation Rules
1. parallel_request_id, objective, and join_policy must not be empty
2. At least one branch assignment must exist
3. Branch IDs must be unique within a parallel request
4. required_completion_count cannot exceed total required branch count
5. wait_for_all requires all required branches to complete before merge
6. wait_for_first_success must not require all branches (set required_completion_count)
7. Merge results require completed or partial join state
8. Conflict records must reference valid branch IDs
9. Output records must reference valid branch IDs
10. Confidence values bounded 0.0–1.0

## State Machine
```
ParallelWorkRequest
  ├─ Branch 1 ──→ completed ──┐
  ├─ Branch 2 ──→ completed ──┤
  ├─ Branch 3 ──→ failed ─────┤
  └─ Branch 4 ──→ blocked ────┘
                               ↓
                        JoinRequirement
                               ↓
                     JoinExecution
                      /         \
              merged         partial_merge
                  |               |
            MergeResult      MergeResult
           (success)      (needs_review)
```

## Relationship to Earlier Primitives
- **P46 (Supervision)**: supplies supervisor/delegate assignments for branches
- **P47 (Routing)**: routes tasks to multiple candidates or modes
- **P51 (Handoff)**: provides handoff/return payloads for each branch
- **P52 (Session Graph)**: gives graph structure for fan-out nodes and join nodes
- **P53 (Messaging)**: supports branch coordination messages, blockers, and completion signals
