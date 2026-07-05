# P55 — Synthesis & Finalization Contract

## Purpose
Typed contract for selecting, normalizing, merging, validating, and finalizing outputs from multiple branches, delegates, or agents into a single coherent result.

## Five Synthesis Stages
1. **Select sources** — only accepted or policy-eligible outputs enter synthesis
2. **Normalize** — convert heterogeneous outputs to comparable and mergeable form
3. **Resolve conflicts** — deduplicate, rank, reject, or request review
4. **Assemble result** — create the coherent final output
5. **Finalize** — validate, approve, and mark release/readiness state

## Core Types

### SynthesisSourceRecord
One input into synthesis.

- **source_id** — unique identifier
- **source_type** — what kind of input (`branch_output`, `delegate_return`, `verification_report`, `review_note`, `artifact_ref`, `state_delta`, `evidence_bundle`)
- **source_ref** — reference to the external source artifact
- **origin_agent_id / origin_role_id** — who produced it
- **eligibility_status** — whether this source is eligible for synthesis (`accepted`, `rejected`, etc.)
- **selection_reason** — why this source was selected
- **confidence** — 0.0–1.0 bounded quality estimate
- **priority** — relative importance
- **evidence_refs** — supporting evidence artifacts

### NormalizationRecord
Transforms a source into a mergeable form.

- **normalization_mode** — how to normalize (`identity`, `schema_map`, `rank_and_filter`, `deduplicate`, `canonicalize`)
- **input_ref, normalized_ref** — before/after artifact references
- **schema_version** — target schema for mapping

### SynthesisConflictRecord
Contradictions or collisions between sources.

- **source_ids** — which sources conflict (2+)
- **conflict_type** — nature of conflict
- **resolved** — whether the conflict has been handled
- **resolution_strategy** — how to resolve (`take_higher_confidence`, `request_appeal`, etc.)
- **review_required** — whether human/manager review is needed

### SynthesisDecisionRecord
The merge decision.

- **synthesis_policy** — how sources were merged (`merge_all_accepted`, `merge_ranked_subset`, `verification_first`, `majority_supported`, `manual_editorial_review`)
- **selected_source_ids, rejected_source_ids** — which sources made the cut
- **conflict_ids** — conflicts that were considered
- **decision_reason, editorial_notes** — rationale

### ValidationSummaryRecord
Whether the output is good enough to finalize.

- **checks_passed, checks_failed** — what passed and what didn't
- **evidence_gaps** — missing supporting evidence
- **quality_score** — 0.0–1.0 bounded quality metric
- **review_required** — whether external review is needed

### FinalizationRecord
Release readiness decision.

- **finalization_status** — `draft`, `in_synthesis`, `validated`, `approved`, `rejected`, `needs_rework`, `released`
- **final_disposition** — `accept`, `accept_with_caveats`, `return_for_rework`, `reject`, `escalate`
- **approved_by, approval_reason** — who decided and why
- **release_ready, followup_required** — release flags

### SynthesisOutputRecord
The finalized product.

- **final_output_refs** — released artifacts
- **supporting_evidence_refs** — evidence backing the output
- **residual_uncertainties** — known open questions
- **consumer_notes** — guidance for the consumer

### Enums

| Enum | Values |
|------|--------|
| **SynthesisInputType** | `branch_output`, `delegate_return`, `verification_report`, `review_note`, `artifact_ref`, `state_delta`, `evidence_bundle` |
| **NormalizationMode** | `identity`, `schema_map`, `rank_and_filter`, `deduplicate`, `canonicalize` |
| **SynthesisPolicy** | `merge_all_accepted`, `merge_ranked_subset`, `verification_first`, `majority_supported`, `manual_editorial_review` |
| **FinalizationStatus** | `draft`, `in_synthesis`, `validated`, `approved`, `rejected`, `needs_rework`, `released` |
| **FinalDisposition** | `accept`, `accept_with_caveats`, `return_for_rework`, `reject`, `escalate` |

## Validation Rules
1. decision_id, finalization_id, and output_id must not be blank
2. At least one eligible source must exist
3. Rejected-only inputs cannot become approved or released outputs
4. released status requires release_ready=True
5. accept/accept_with_caveats disposition requires at least one final_output_ref
6. return_for_rework or reject must include approval_reason
7. quality_score bounded 0.0–1.0
8. Unresolved conflicts must set review_required on validation summary

## Relationship to Earlier Primitives
- **P51 (Handoff)**: supplies structured delegate returns as synthesis sources
- **P52 (Session Graph)**: identifies which graph branches feed synthesis
- **P53 (Messaging)**: carries branch outputs, review notes, and completion signals
- **P54 (Parallel Work & Join)**: produces branch outputs and merge conflicts that feed synthesis
- **P39/P24 (Evaluation/Quality Gate)**: quality signals and validation connect to final disposition
