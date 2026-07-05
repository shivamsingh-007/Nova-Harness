# P56 — Hybrid Task Intake Contract

## Purpose
Typed contract for accepting free-form user or system requests, extracting them into a structured task schema, validating the extraction, handling ambiguity, and deciding whether the task is accepted, clarified, or escalated.

## Intake Flow
1. **Capture** — preserve the raw request exactly as received
2. **Extract** — map free text to typed task fields using a known schema/taxonomy
3. **Resolve** — mark each field as explicit, inferred, missing, ambiguous, or invalid
4. **Validate** — check against required fields and confidence thresholds
5. **Decide** — accept, accept with gaps, request clarification, reject, or escalate

## Core Types

### RawTaskIntake
Preserves the original request for audit and re-extraction.

- **intake_id, source_type** — identity and origin
- **session_id, user_id** — context
- **raw_text** — the original free-form text
- **raw_artifact_refs** — attached files, specs, schemas
- **language, channel, source_metadata** — provenance

### StructuredTaskExtraction
The normalized task view bridging free text to runtime task contracts.

- **target_schema_id** — which schema is being extracted into
- **extraction_status** — how complete the extraction is
- **task_type, title, objective, constraints, deadline, priority** — extracted fields
- **requested_outputs** — expected deliverables

### ExtractedFieldRecord
One field's extraction result.

- **resolution_status** — explicit / inferred / missing / ambiguous / invalid
- **confidence** — 0.0–1.0 bounded quality estimate
- **source_span** — the substring that produced this field
- **extraction_reason, validation_notes** — rationale

### AmbiguityRecord
Uncertainty about a field value.

- **field_name** — which field is ambiguous
- **candidate_values** — possible interpretations
- **clarification_needed** — whether this blocks intake

### ClarificationRequestRecord
Follow-up questions to resolve ambiguity.

- **clarification_mode** — how to get resolution (`ask_user`, `auto_repair`, `route_to_review`, `defer_until_context_available`)
- **questions** — specific questions to ask
- **blocking_fields** — which fields are blocked
- **recommended_defaults** — fallback values

### IntakeValidationRecord
Validates the extraction against required fields and schema.

- **required_fields_checked, missing_required_fields, invalid_fields** — field status
- **average_confidence** — 0.0–1.0 bounded
- **schema_valid** — whether the extraction conforms to schema
- **review_required** — whether human review is needed

### TaskIntakeDecisionRecord
The final intake decision.

- **intake_disposition** — accepted / accepted_with_gaps / clarification_required / rejected / escalated
- **accepted_task_ref, clarification_ref, escalation_ref** — follow-up references

### Enums

| Enum | Values |
|------|--------|
| **IntakeSourceType** | `user_message`, `form_submission`, `api_payload`, `artifact_upload`, `mixed_input` |
| **ExtractionStatus** | `not_started`, `in_progress`, `extracted`, `partially_extracted`, `failed`, `needs_review` |
| **FieldResolutionStatus** | `explicit`, `inferred`, `missing`, `ambiguous`, `invalid` |
| **ClarificationMode** | `ask_user`, `auto_repair`, `route_to_review`, `defer_until_context_available` |
| **IntakeDisposition** | `accepted`, `accepted_with_gaps`, `clarification_required`, `rejected`, `escalated` |

## Validation Rules
1. intake_id and source_type must not be empty
2. raw_text or raw_artifact_refs must be provided
3. target_schema_id must not be empty for structured extraction
4. confidence and average_confidence bounded 0.0–1.0
5. Missing fields must not have a field_value_ref
6. Accepted disposition requires schema_valid=True
7. Accepted disposition must include decision_reason
8. clarification_required must include a clarification_request
9. Missing required fields block unconditional acceptance
10. Ambiguity records must reference valid field names

## Relationship to Earlier Primitives
- **P40 (Run Orchestration)**: receives a better-formed task object from intake
- **P41 (Failure/Recovery)**: can check feasibility using extracted fields
- **P44/P45 (Loop/Step)**: benefit from cleaner loop and step planning
- **P47 (Routing)**: can route based on structured task type and constraints
- **P50 (Role/Specialization)**: can assign role-specialized agents based on extracted intent
- **P55 (Synthesis)**: benefits because good output quality starts with good intake
