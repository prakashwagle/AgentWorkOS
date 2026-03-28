# Agent Work OS — Architecture Design Document

**Version:** 0.2.0-draft  
**Date:** 2026-03-24  
**Status:** RFC  

---

## 1. Purpose

Agent Work OS is a generic Python evaluation framework for agent systems.

The architecture is intentionally split into two layers:

- **Core framework**: reusable abstractions for contracts, replay, scoring, and feedback-driven regression generation
- **Reference domain**: SRE/DevOps scenarios used to validate that the core abstractions are real and reusable

The MVP is designed to answer one question:

> Can a small generic core help a developer design better agents by replaying authored scenarios, checking behavior, and surfacing actionable results?

If the answer is no, the framework should be simplified before any expansion into CI or production workflows.

---

## 2. Design Principles

| Principle | Consequence |
|---|---|
| Generic core, narrow validation wedge | Build reusable primitives, validate through SRE/DevOps first |
| Contracts over vibes | Expected behavior must be declared explicitly |
| Replay before live control | Historical and curated scenarios come before risky automation |
| Deterministic checks first | Use cheap, explainable checks wherever possible |
| Human correction is high-value data | Feedback becomes draft regression coverage |
| Lean MVP | Prefer a small working loop over broad capability claims |
| Python-first backend | Keep the core implementation in one language for speed and coherence |

---

## 3. MVP Scope

### Included

- YAML contract model
- Python adapter protocol
- Replay runner
- Deterministic check engine
- Optional LLM judge
- Statistical scoring for repeated trials
- SQLite persistence
- SRE/DevOps reference package for:
  - alert triage
  - runbook recommendation
  - remediation plan or patch drafting for review

### Excluded

- CI or deployment gating
- shadow production mode
- feedback ingestion
- regression generation
- autonomous deployment
- autonomous patch application
- auto-rollback
- broad observability integrations
- live production control loops
- custom dashboard
- distributed event bus
- complex policy and RBAC systems
- generalized multi-domain plugin marketplace

---

## 4. System Overview

```text
               Agent Work OS Framework Repo

     examples/ + schemas/ + CLI + adapters
                       │
                       ▼
                 agentwork init
                       │
                       ▼
             Generated Evaluation Project
     agentwork.json + contracts/ + bundles/ + .agentwork/
                       │
                       ▼
                  agentwork run
                       │
                       ▼
                 Contract Loader
                       │
                       ▼
        Scenario Bundles ──▶ Replay Runner ──▶ Adapter ──▶ Target Agent
                               │
                               ▼
                          Check Engine
                               │
                               ├─ Deterministic checks
                               └─ Optional LLM judge
                               ▼
                          Scoring Engine
                               ▼
                    SQLite Run Store (.agentwork)
                               ▼
                         CLI / Optional API
```

The architecture has two runtime components for MVP:

1. **Replay Runner**
2. **Run Report Store**

Everything else is a library around those components.

The CLI is the required MVP interface. FastAPI is optional and should expose only the same operations as the CLI. A UI, if added, should be a thin read-only layer over persisted run results.

### 4.1 Check Engine vs Scoring Engine

These two parts do different jobs and should stay separate.

- **Check Engine**: decides what happened on one trial
- **Scoring Engine**: summarizes what happened across many trials

Example:

- The check engine says: `tool_called` passed, `response_contains` failed, invariant passed.
- The scoring engine says: completion rate was `0.7`, safety score was `1.0`, mean latency was `820ms`, overall result failed because the lower confidence bound missed the threshold.

If these are merged too early, the developer loses debuggability. MVP should preserve the distinction.

---

## 5. Package Layout

```text
agentwork/
  api/
    app.py
    routes_runs.py
  cli/
    main.py
  core/
    adapters.py
    contracts.py
    bundles.py
    runner.py
    checks.py
    scoring.py
    judge.py
  domains/
    sre_ops/
      bundles.py
      checks.py
      fixtures.py
      examples/
  storage/
    models.py
    repository.py
    sqlite.py
  schemas/
    contract.schema.json
  tests/
```

Rules:

- `core/` must remain domain-agnostic
- `domains/sre_ops/` can define SRE-specific bundle loaders and checks
- storage stays simple in MVP

---

## 6. Core Abstractions

### 6.1 Contract

The contract is the main unit of evaluation configuration.

```python
from typing import Literal
from pydantic import BaseModel, Field


Phase = Literal["design"]


class Thresholds(BaseModel):
    min_completion_rate: float
    min_safety_score: float
    max_mean_latency_ms: int | None = None
    max_mean_cost_usd: float | None = None
    min_trials: int
    confidence: float = 0.95


class Invariant(BaseModel):
    id: str
    description: str
    check: str
    severity: Literal["block", "warn"] = "block"
    config: dict = Field(default_factory=dict)


class Expectation(BaseModel):
    id: str
    description: str
    bundle_type: str
    checks: list[dict]
    tags: list[str] = Field(default_factory=list)
    llm_judge: dict | None = None
    origin: dict | None = None


class Contract(BaseModel):
    id: str
    version: str
    domain: str
    description: str
    expectations: list[Expectation]
    invariants: list[Invariant] = Field(default_factory=list)
    acceptance: dict[Phase, Thresholds]
```

The contract remains generic. It does not know what an alert or incident is. It only references bundle types and checks.

All contracts are validated against a formal contract schema before execution.

### 6.2 Scenario Bundle

The bundle is the replayable input unit.

```python
class ScenarioBundle(BaseModel):
    id: str
    bundle_type: str
    prompt: str
    context: dict
    expected: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
```

Examples:

- SRE alert bundle
- incident summary bundle
- patch-draft bundle

Bundles may include scenario-level execution requirements such as:

- `required_tools`
- `forbidden_tools`
- `required_steps`
- `forbidden_actions`

These are part of the scenario schema, not adapter-specific logic.

### 6.3 Agent Adapter

```python
from typing import Protocol


class AgentResult(BaseModel):
    response: str
    structured: dict = Field(default_factory=dict)
    tool_calls: list[dict] = Field(default_factory=list)
    usage: dict = Field(default_factory=dict)
    latency_ms: int
    metadata: dict = Field(default_factory=dict)


class AgentAdapter(Protocol):
    agent_id: str
    agent_version: str

    async def run(self, bundle: ScenarioBundle) -> AgentResult:
        ...
```

The adapter is intentionally thin. The framework should evaluate behavior, not dictate agent architecture.

Every adapter must return the normalized agent result schema, including:

- `response`
- `structured`
- `tool_calls`
- `steps`
- `usage`
- `latency_ms`
- `metadata`

---

## 7. Evaluation Pipeline

### 7.1 Run Flow

For each expectation:

1. Load matching scenario bundles
2. Execute N trials
3. Run invariant checks
4. Run deterministic expectation checks
5. Run LLM judge only when required
6. Aggregate results
7. Compare against design thresholds
8. Persist run result

### 7.2 Runner Interface

```python
class RunConfig(BaseModel):
    phase: Phase
    trials: int
    concurrency: int = 4
    timeout_ms: int = 30000
    expectation_ids: list[str] | None = None
    tags: list[str] | None = None
```

```python
class EvalRunner:
    async def run_contract(
        self,
        contract: Contract,
        adapter: AgentAdapter,
        bundles: list[ScenarioBundle],
        config: RunConfig,
    ) -> "EvalRun":
        ...
```

### 7.3 Trial Outcome

```python
class TrialOutcome(BaseModel):
    bundle_id: str
    expectation_id: str
    passed: bool
    deterministic_passed: bool
    invariant_passed: bool
    judge_score: float | None = None
    latency_ms: int
    token_usage: dict = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
```

### 7.4 Why Repeated Trials

The framework evaluates non-deterministic behavior. Single-run pass/fail is too weak. Repeated trials let us estimate whether observed performance is stable enough to trust.

For MVP:

- design: 5 to 10 trials per scenario set

---

## 8. Check Engine

The check engine has two layers.

### 8.1 Deterministic Checks

These are the default and should cover most high-value behavior.

Supported MVP checks:

- `response_contains`
- `response_not_contains`
- `response_matches_regex`
- `tool_called`
- `tool_not_called`
- `required_tools_called`
- `forbidden_tools_absent`
- `required_steps_completed`
- `forbidden_actions_absent`
- `structured_equals`
- `structured_path_equals`
- `latency_under`
- `token_count_under`
- `custom`

### 8.2 Optional LLM Judge

LLM judging is allowed only when a requirement cannot be expressed deterministically, such as:

- clarity
- usefulness
- completeness of reasoning
- whether a remediation plan is materially actionable

Guardrails:

- deterministic checks run first
- low temperature only
- rubric-based prompt
- stored reasoning for audit
- optional consensus runs for sensitive checks

The MVP should remain useful even if the LLM judge is disabled.

---

## 9. Scoring Model

The scoring model is simpler than the previous draft. It is designed for MVP validation, not for theoretical completeness.

### 9.1 Dimensions

- **Completion**: task success rate across trials
- **Safety**: invariant compliance and absence of forbidden actions
- **Utility**: whether the result is useful enough to review or act on
- **Efficiency**: latency, tokens, tool usage, and estimated cost

### 9.2 Aggregation

```python
class EvalScore(BaseModel):
    completion_rate: float
    safety_score: float
    utility_score: float | None = None
    mean_latency_ms: float
    mean_cost_usd: float | None = None
    confidence_interval: tuple[float, float]
    passed: bool
    reasons: list[str] = Field(default_factory=list)
```

For MVP, acceptance is explicit and design-time only. We do not need multi-phase logic to validate the framework.

### 9.3 Statistical Method

Use Wilson score confidence intervals for completion rate. That is enough for design-time decision support.

Acceptance rule:

- compute observed completion rate
- compute lower confidence bound
- pass only if the lower bound meets the configured threshold and safety thresholds pass

---

## 10. Design-Time Developer Loop

The entire MVP is one loop:

1. Author contract
2. Author scenario bundles
3. Run agent against scenarios
4. Inspect trial checks and aggregate scores
5. Modify agent or scenarios
6. Re-run

This is the shortest path to validating whether the framework is useful.

### 10.1 Required Output

Each run should produce:

- per-scenario status
- per-check pass/fail
- invariant violations
- aggregate completion and safety summary
- latency and cost summary
- concise failure reasons

### 10.2 Nice-to-Have But Not MVP

- converting failures into new cases automatically
- CI gating
- baseline comparison across versions
- feedback ingestion from production systems

---

## 11. SRE/DevOps Reference Domain

The SRE package exists to test the core.

### 11.1 Reference Bundle Types

- `sre.alert_triage`
- `sre.runbook_recommendation`
- `sre.patch_plan`

### 11.2 Reference Checks

These live in `domains/sre_ops/checks.py`, not in the core:

- `severity_correct`
- `service_identified`
- `runbook_referenced`
- `unsafe_action_not_proposed`
- `rollback_note_present`
- `patch_plan_scoped`

### 11.3 Example Bundle

```yaml
id: alert-cpu-api-prod-001
bundle_type: sre.alert_triage
prompt: "Investigate this production alert and recommend next steps."
context:
  alert:
    service: api
    severity: critical
    signal: cpu > 95%
  logs:
    - "OOMKilled observed on api-7f8d"
  metrics:
    cpu_p95: 98
    error_rate: 0.14
expected:
  severity: critical
  service: api
  likely_causes:
    - memory_pressure
```

### 11.4 Why This Domain

SRE/DevOps is a good wedge because:

- the failure cost is real
- outputs are not purely subjective
- safety matters
- scenarios are diverse enough to stress the abstractions
- human corrections are common and meaningful

If the core works here, it has earned the right to be generalized further.

---

## 12. Storage Model

SQLite is sufficient for MVP.

### 12.1 Tables

- `contracts`
- `expectations`
- `bundles`
- `runs`
- `trial_outcomes`

### 12.2 Storage Rules

- contracts remain file-backed and versioned in Git
- run outputs live in SQLite
- bundle payloads may be stored as JSON

This keeps authorship simple while still enabling local iteration and history.

---

## 13. API Surface

### CLI

The CLI is the primary interface for MVP and must support end-to-end usage without any UI.

```bash
agentwork init
agentwork run --contract contracts/sre-alerts.yaml
agentwork run --only alert-triage
agentwork report list
agentwork report show <run-id>
agentwork bundles import ./fixtures/sre
```

### FastAPI Endpoints

FastAPI is optional for MVP.

- `POST /runs`
- `GET /runs/{run_id}`
- `POST /bundles/import`

The API exists to support automation and a future thin frontend. It is not the product center of gravity for MVP.

---

## 14. Frontend Guidance

Frontend is optional. If added, it should be a thin client over the API.

Recommended MVP screens:

1. run history
2. run detail
3. scenario browser

A React or Next.js frontend is acceptable, but should not drive architecture decisions in v1.

---

## 15. Delivery Plan

### Milestone 1: Core Replay Loop

- contract loading
- bundle loading
- adapter interface
- deterministic checks
- CLI run command
- SQLite persistence

### Milestone 2: SRE Reference Package

- alert triage bundles
- runbook recommendation bundles
- patch-plan bundles
- domain checks
- sample adapter

### Milestone 3: Run Reports

- report inspection command
- run detail output
- failure reasons with scenario references
- optional thin API

The framework should be tested against at least two SRE workflows before any attempt to broaden the product narrative or add CI/production loops.

---

## 16. Explicit MVP Validation Criteria

We should only call the MVP successful if all of the following are true:

- a single core runner evaluates multiple SRE workflows
- contracts are understandable and not too costly to author
- deterministic checks cover most safety-critical behavior
- developers can understand failures quickly enough to improve the agent
- repeated local runs change the agent design process in practice

If these are not true, the right move is to simplify the framework further, not add CI or production features.
