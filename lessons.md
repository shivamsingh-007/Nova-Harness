# Lessons Learned

## 2026-07-05: Unknown-state failures must never auto-resolve
- **Context**: P61 unknown_state validator design
- **Observation**: recovered/compensated dispositions for unknown-state failures could mask safety issues
- **Root cause**: missing guard that unknown_state blocks success dispositions
- **Fix**: Added model_validator rejecting recovered/compensated when unknown_state=true
- **Reusable lesson**: Unknown state is inherently unsafe — always escalate rather than assume success
- **Promote to rule?**: Yes — added to loop_rules.md under retry/recovery rules
- **Affected files**: `models/retry_recovery_compensation_contract.py`, `loop_rules.md`

## 2026-07-05: Risk threshold validation prevents silent overrides
- **Context**: P60 RiskThresholdPolicy model design
- **Observation**: High/critical risk levels auto-proceeding is dangerous
- **Root cause**: Missing cross-field validation between minimum_risk_level and requires_human_approval
- **Fix**: Added model_validator enforcing that high/critical minimum_risk_level requires requires_human_approval=True
- **Reusable lesson**: Risk thresholds should always be bounded by both level and score; never let high-risk actions auto-proceed silently
- **Promote to rule?**: Yes — high-risk actions always require explicit approval disposition
- **Affected files**: `models/risk_escalation_approval_contract.py`

## 2026-07-04: bcrypt for password hashing
- **Context**: Implementing auth model password storage
- **Observation**: Plain SHA-256 is insufficient for password storage
- **Root cause**: Naive hashing choice
- **Fix**: Switched to bcrypt with cost factor 12
- **Reusable lesson**: Always use adaptive hashing for passwords; bcrypt/argon2 preferred
- **Promote to rule?**: Yes — add to loop_rules.md under security practices
- **Affected files**: `models/auth.py`, `loop_rules.md`

## 2026-07-04: Short JWT expiry for security
- **Context**: Implementing JWT token generation
- **Observation**: Long-lived tokens increase breach surface
- **Root cause**: Defaulted to 24h expiry
- **Fix**: Set default expiry to 1 hour
- **Reusable lesson**: JWTs should expire in minutes/hours, not days
- **Promote to rule?**: Yes — add to security section
- **Affected files**: `utils/jwt.py`, `loop_rules.md`

## 2026-07-04: Dry-run migrations before applying
- **Context**: Database migration almost caused data loss
- **Observation**: Migration would drop columns with live data
- **Root cause**: Assumed migration was safe without testing
- **Fix**: Ran dry-run first, caught destructive operation
- **Reusable lesson**: Always dry-run migrations against a copy of production data
- **Promote to rule?**: Yes — add to operational rules
- **Affected files**: `loop_rules.md`

## 2026-07-04: Commit before risky operations
- **Context**: Session crashed during DB migration
- **Observation**: Lost partial work because it was uncommitted
- **Root cause**: No checkpoint before starting migration
- **Fix**: Commit all verified work before starting risky operations
- **Reusable lesson**: Checkpoint (commit) before any destructive or irreversible operation
- **Promote to rule?**: Yes — add to git_policy.md
- **Affected files**: `git_policy.md`, `loop_rules.md`
