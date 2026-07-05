# Handoff Protocol

## Purpose
Portable payload for passing work from one agent or role to another, with structured returns optimized for downstream consumption.

## Ownership Rules
- **One writer at a time**: only the agent with write ownership may modify artifacts
- **Read-only assist**: reviewers and verifiers never get write access
- **Full transfer**: receiving agent becomes the sole owner until return
- **Temporary execution**: writer has bounded scope; original owner retains oversight

## Handoff Flow
1. Sender creates `HandoffRequest` with objective and acceptance criteria
2. Sender packages selected context in `HandoffContextPacket` (not full-session dump)
3. Sender attaches `HandoffConstraintPacket` for execution boundaries
4. Ownership mode determines writer/read-only assignments
5. Receiver executes within bounds and returns `ReturnPayload`
6. Sender or supervisor records `ReturnReviewRecord` for acceptance/rejection

## Context Selection
- Transfer just enough context for continuity: task refs, state refs, artifact refs
- Exclude secrets and oversized data via `excluded_context_refs`
- Summarize in `context_summary` for quick orientation

## Return Contract
- Every return includes `return_outcome`, `confidence`, and `evidence_refs`
- Blockers are explicit (not buried in prose)
- `recommended_next_action` signals what the receiver expects next
- Returns are typed, not free-text conversation

## Integration
Handoffs connect to P46 (delegation), P47 (routing), P48 (skills as work units), P50 (role boundaries), and P44/P45 (loop steps).
