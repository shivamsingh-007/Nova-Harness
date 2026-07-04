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
  <img src="https://img.shields.io/badge/tests-1092%20passed-22c55e?style=flat-square&logo=pytest" alt="1092 tests passing">
  <img src="https://img.shields.io/badge/coverage-99%25-3b82f6?style=flat-square" alt="99% coverage">
  <img src="https://img.shields.io/badge/primitives-27-8b5cf6?style=flat-square" alt="27 primitives">
  <img src="https://img.shields.io/badge/python-3.11+-f59e0b?style=flat-square&logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-ef4444?style=flat-square" alt="MIT License">
</p>

<br>

---

## what is this?

Nova Harness is a library of **27 typed contract primitives** for building reliable, observable, and governable AI agent execution systems.

Each primitive is:
- **a pydantic model** with strict validation
- **tested independently** (1092 tests, 99% coverage)
- **documented** with realistic JSON examples and an HTML architecture diagram

No runtime agent, no deployment framework — just the contracts you plug into your own orchestration.

```
models/     → 27 pydantic contract modules
tests/      → 27 test files (1092 tests)
examples/   → 24 JSON example files
harness/    → runtime implementations (state driver, pipeline, model provider)
lavish-axi-*.html → architecture diagrams for every primitive
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
┌─────────────────────────────────────────────┐
│  63 python modules                           │
│  12,095 lines of python                      │
│  8,992 lines of HTML architecture diagrams   │
│  4,062 lines of JSON examples                │
│  27 primitives (P1–P27)                      │
│  1,092 tests (all passing)                   │
│  99% model code coverage                     │
│  8 runtime implementations (harness/)        │
└─────────────────────────────────────────────┘
```

<p align="center">
  <img src="https://raw.githubusercontent.com/shivamsingh-007/Nova-Harness/master/terminal.svg" width="100%" alt="pytest output — 1092 tests passing, 99% coverage">
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
├── models/                  # pydantic contract modules (the core library)
├── tests/                   # test files — one per model module
├── examples/                # realistic JSON examples for every contract
├── harness/                 # lean runtime implementations
│   ├── state_driver.py      # state machine execution driver
│   ├── pipeline.py          # single-run orchestration pipeline
│   └── model_provider.py    # model provider interface
├── context_selection/       # context selection & scoring pipeline
├── lavish-axi-p*.html       # architecture diagrams for all 27 primitives
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
