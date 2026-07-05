# P62 — Capability Negotiation & Compatibility Contract

## Purpose
Typed contract for declaring capabilities, expressing requirements, evaluating compatibility, computing negotiated capability intersections, recording gaps, and deciding whether execution proceeds, falls back, reroutes, or rejects.

## Negotiation Flow
1. **Declare** — both parties (requester and candidate) declare their capabilities with categories, versions, and constraints.
2. **Compare** — the runtime evaluates requirements against offers, computing the intersection.
3. **Identify Gaps** — unmatched requirements are recorded as gaps, marked blocking or non-blocking.
4. **Negotiate** — the runtime determines the mutually supported capability subset.
5. **Decide** — based on gaps and negotiation mode, proceed, fall back, reroute, reject, or escalate.

## Capability Categories
| Category | Examples |
|----------|----------|
| `tooling` | HTTP client, file I/O, database access |
| `model_behavior` | Reasoning chains, code gen, summarization |
| `skill_support` | Search, analysis, planning |
| `output_format` | CSV, JSON, HTML, Markdown |
| `context_window` | 4K, 8K, 32K, 128K tokens |
| `safety_control` | Rate limiting, content filtering, audit logging |
| `integration` | Slack, GitHub, Jira connectors |
| `interaction_mode` | Chat, batch, streaming, async |

## Requirement Levels
| Level | Meaning |
|-------|---------|
| `required` | Must be satisfied for compatibility |
| `preferred` | Strongly desired but not mandatory |
| `optional` | Nice-to-have, no impact on compatibility |

## Compatibility Status
| Status | Meaning |
|--------|---------|
| `compatible` | All required requirements satisfied |
| `partially_compatible` | Some non-required requirements unsatisfied |
| `incompatible` | Required requirements unsatisfied |
| `unknown` | Cannot determine compatibility |

## Negotiation Disposition
| Disposition | Meaning |
|-------------|---------|
| `proceed` | Full compatibility, execute normally |
| `proceed_with_fallbacks` | Compatible with fallback substitutions |
| `reroute` | Reroute to a different candidate |
| `reject` | No compatible option available |
| `escalate` | Escalate for human intervention |

## Validation Rules
1. All IDs, party_refs, capability names, and summaries must be non-empty
2. `compatible` status requires no unmatched requirement IDs
3. `incompatible` status requires at least one unmatched requirement ID
4. Version constraints must be coherent (min <= max)
5. `proceed_with_fallbacks` requires selected fallbacks
6. `reroute`/`reject` requires a decision reason
7. Envelope: `incompatible` cannot `proceed` without override ref
8. Envelope: `proceed_with_fallbacks` requires at least one gap recorded

## Relationship to Earlier Primitives
- **P47 (Routing)**: Use compatibility evaluation before routing
- **P48 (Validation)**: Negotiate whether a skill matches task needs
- **P50 (Roles)**: Compare role capabilities against task requirements
- **P53 (Messaging)**: Negotiate messaging features or formats
- **P59/P60 (Budget/Risk)**: Influence fallback/rejection when compatible option is too risky or costly
- **P61 (Retry)**: Use reroute after incompatibility-triggered failure

## File Structure
```
capabilities/
  CAPABILITIES.md                          — this file
  templates/
    capability_declaration.json            — declaration schema
    compatibility_evaluation.json           — evaluation schema
    negotiated_set.json                    — negotiated set schema
```
