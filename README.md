<p align="center">
  <img src="https://raw.githubusercontent.com/shivamsingh-007/Nova-Harness/master/logo.svg" width="80" alt="Nova Harness">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/shivamsingh-007/Nova-Harness/master/banner.svg" width="100%" alt="Nova Harness">
</p>

<p align="center">
  <strong>typed contract primitives for reliable AI agent execution</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/tests-3280%20passed-22c55e?style=flat-square&logo=pytest" alt="3280 tests passing">
  <img src="https://img.shields.io/badge/coverage-99%25-3b82f6?style=flat-square" alt="99% coverage">
  <img src="https://img.shields.io/badge/primitives-62-8b5cf6?style=flat-square" alt="62 primitives">
  <img src="https://img.shields.io/badge/python-3.11+-f59e0b?style=flat-square&logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-ef4444?style=flat-square" alt="MIT License">
</p>

<br>

---

## what is this?

Nova Harness is a library of **62 typed contract primitives** for building reliable, observable, and governable AI agent execution systems.

Each primitive is:
- **a pydantic model** with strict validation
- **tested independently** (3280 tests, 99% coverage)
- **documented** with realistic JSON examples and an HTML architecture diagram

No runtime agent, no deployment framework — just the contracts you plug into your own orchestration.

```
models/      → 58 pydantic contract modules
tests/       → 64 test files (3280 tests)
examples/    → 60 JSON example files
primitives/  → 62 architecture diagrams (one per primitive)
harness/     → runtime implementations (state driver, pipeline, model provider)
```

<br>

## primitives

| # | primitive | purpose |
|---|-----------|---------|
| P1 | **Instruction Layering** | global + project + task instruction hierarchy |
| P2 | **Task Contract Schema** | nested pydantic with 2-layer validation |
| P3 | **Context Delivery Schema** | structured bundle with reason-annotated items |
| P4 | **Context Selection Policy** | heuristic pipeline + exclusions + caps |
| P5 | **Tool Interface Schema** | definition, invocation, result types |
| P6 | **Execution Environment** | provider-agnostic runtime contract |
| P7 | **Durable State Schema** | run-centric execution persistence |
| P8 | **Verification Schema** | multi-check quality gate |
| P9 | **Prompt Assembly Schema** | layered prompt assembly |
| P10 | **Run Orchestration State Machine** | deterministic control-flow |
| P11 | **Retry & Recovery Policy** | failure-classified retry |
| P12 | **Approval & Safety Policy** | risk-classified governance |
| P13 | **Evaluation & Benchmark Schema** | task-grader-run benchmark |
| P14 | **Observability & Trace Schema** | step-level execution evidence |
| P15 | **State Machine Driver** | trigger, guard, history runtime |
| P16 | **Pipeline Executor** | single-run orchestration pipeline |
| P17 | **Production Config & Secrets** | typed config + secret references + startup validation + redaction |
| P18 | **Budget & Rate Limit Policy** | hierarchical token/cost/runtime/tool-call/rate-limit contract |
| P19 | **Failure Taxonomy & Error Envelope** | typed failure taxonomy + rich envelope + public-safe view |
| P20 | **Input & Output Guardrails** | screening + risk classification + sanitization + decisions |
| P21 | **Approval & Escalation** | risk-tiered approval + reviewer roles + evidence + timeout |
| P22 | **Capability Matrix** | default-deny capability matrix + per-agent grants + environment-aware permissions |
| P23 | **Session State & Checkpoint** | working session lifecycle + checkpointing + replay safety + side-effect tracking |
| P24 | **Evaluation & Quality Gate** | structured metrics + mandatory checks + threshold policies |
| P25 | **Trace, Audit & Provenance** | chronological audit events + actor attribution + resource refs + evidence lineage |
| P26 | **Agent Identity & Ownership** | unique agent identity + named ownership + authority models + delegation context |
| P27 | **Memory Boundary & Retention** | memory kind + scope boundaries + sensitivity + retention classes + lifecycle states |
| P28 | **Hook Lifecycle Contract** | typed lifecycle hooks with pre/post/error phases and ordered execution |
| P29 | **Handoff & Return Envelope** | structured handoff + return envelope with state serialization |
| P30 | **Cross-Agent Messaging** | typed message bus with routing, delivery guarantees, and backpressure |
| P31 | **Parallel Work & Join** | fork-join primitives with partial-failure aggregation |
| P32 | **Multi-Agent Session Graph** | directed session graph with agent nodes, edges, and topology validation |
| P33 | **Running Loop Contract** | iterative loop contract with convergence detection and bound enforcement |
| P34 | **Step & Turn Lifecycle** | per-step lifecycle with turn-level state, deadlines, and error boundaries |
| P35 | **Supervisor / Delegate** | supervisor-agent delegation with escalation and revocation |
| P36 | **Agent Role & Specialization** | role definitions, capability trees, and specialization constraints |
| P37 | **Skill Manifest & Activation** | skill metadata, dependency resolution, and activation gates |
| P38 | **Artifact Output Schema** | typed artifact output with content validation and format contracts |
| P39 | **Feedback & Quality Contract** | structured feedback loops with quality dimensions and revision tracking |
| P40 | **Policy Decision Contract** | policy evaluation with decision trees, outcomes, and overrides |
| P41 | **Policy & Guardrail** | composable guardrail chains with deny/allow/warn dispositions |
| P42 | **Checkpoint & Recovery** | checkpoint creation, verification, and deterministic replay |
| P43 | **Memory & Context** | structured memory retrieval with relevance scoring and context window management |
| P44 | **Logging & Observability** | structured event logging with severity, correlation, and sampling |
| P45 | **Routing & Arbitration** | message routing with arbitration rules and conflict resolution |
| P46 | **Synthesis & Finalization** | multi-source synthesis with conflict detection and finalization gates |
| P47 | **Hybrid Task Intake** | structured intake from prompt, issue, PR, spec, verbal, scheduled, and API sources |
| P48 | **Clarification & Missing-Info Resolution** | gap detection, clarification question management, and resolution strategies |
| P49 | **Acceptance Criteria & Definition of Done** | AC/DoD separation with required/optional items and release gates |
| P50 | **Execution Budget & Resource Envelope** | hierarchical budget scoping, threshold enforcement, and reallocation |
| P51 | **Risk, Escalation & Human-Approval** | risk classification, escalation triggers, approval workflows, and human-in-the-loop |
| P52 | **Retry, Recovery & Compensation** | failure classification, retry strategies, recovery plans, and compensation actions |
| P53 | **Capability Negotiation & Compatibility** | capability declaration, compatibility evaluation, and negotiated agreements |
| P54 | **Failure Recovery Contract** | typed failure recovery with recovery modes and rollback actions |
| P55 | **Model Call Contract** | model invocation schema with parameters, cost tracking, and response validation |
| P56 | **Tool Permission Contract** | tool-level allow/deny permissions with environment-aware grants |
| P57 | **Tool Receipt Contract** | tool execution receipts with usage evidence and cost attribution |
| P58 | **Unit of Work Contract** | atomic work unit with idempotency keys and completion tracking |
| P59 | **Run Orchestration Contract** | run-level orchestration with state transitions and lifecycle hooks |
| P60 | **Environment Contract** | execution environment specification with provider-agnostic resource constraints |
| P61 | **Approval Contract** | approval workflow with multi-step review, deadlines, and disposition |
| P62 | **Human Approval Contract** | human-in-the-loop approval with evidence packages and audit trail |

<br>

## what it is not

Nova Harness does **not**:
- run agents for you (bring your own executor)
- deploy to production (bring your own infrastructure)
- provide a UI or dashboard (bring your own observability stack)
- include a vector database or semantic search engine
- implement multi-agent orchestration or swarm logic
- replace human review for safety-critical decisions

The project is early-stage. Some primitives are more mature than others.
Coverage at 99% is against the contract code — not end-to-end system tests.

<br>

## numbers

```
┌──────────────────────────────────────────────┐
│  58 pydantic contract modules                 │
│  10,961 lines of Python (models)              │
│  23,501 lines of Python (tests)               │
│  62 HTML architecture diagrams                │
│  13,583 lines of JSON examples                │
│  62 primitives (P1–P62)                       │
│  3,280 tests (all passing)                    │
│  99% model code coverage                      │
│  8 runtime implementations (harness/)         │
└──────────────────────────────────────────────┘
```

<p align="center">
  <img src="https://raw.githubusercontent.com/shivamsingh-007/Nova-Harness/master/terminal.svg" width="100%" alt="pytest output — 3280 tests passing, 99% coverage">
</p>

<br>

## quickstart

```bash
pip install pydantic pytest

# run all tests
pytest -q

# run with coverage
pytest --cov=models --cov-report=term
```

Python 3.11+ required. No other runtime dependencies beyond `pydantic`.

<br>

## project structure

```
├── models/                  # 58 pydantic contract modules (the core library)
├── tests/                   # 64 test files — one per model module
├── examples/                # 60 JSON example files for every contract
├── primitives/              # 62 architecture diagrams (one per primitive)
├── harness/                 # lean runtime implementations
│   ├── state_driver.py      # state machine execution driver
│   ├── pipeline.py          # single-run orchestration pipeline
│   └── model_provider.py    # model provider interface
├── context_selection/       # context selection & scoring pipeline
├── integration_slice.py     # end-to-end integration slice
├── AGENTS.md                # project rules
└── README.md                # this file
```

<br>

## design principles

1. **one primitive at a time** — each contract is independently useful and testable
2. **explicit schemas** — every boundary is a typed pydantic model, not a convention
3. **default-deny** — capabilities, memory, permissions all start locked down
4. **inspectable by design** — every decision produces an audit record you can read
5. **no hidden state** — side effects are tracked, checkpoints are explicit, provenance is chained
6. **honest scope** — this project builds contracts, not a runtime; the contracts are real, the implementations are minimal by design

<br>

## license

MIT — see [LICENSE](LICENSE) for details.
