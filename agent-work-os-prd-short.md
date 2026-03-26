# Agent Work OS — Product Requirements Document

## 1. What Is Agent Work OS?

Agent Work OS is an open-source Python framework for evaluating AI agents through replayable scenarios, explicit behavior contracts, and feedback-driven regression generation.

The product goal is generic: provide a reusable system that helps teams define expected agent behavior, run repeatable evaluations, score outcomes with statistical discipline, and turn production corrections into future test coverage.

The MVP validation wedge is narrow on purpose: SRE and DevOps agents that help operators triage alerts, summarize incidents, recommend runbooks, and draft safe remediation changes for human review.

The SRE/DevOps wedge is not the product boundary. It is the proving ground for the framework.

## 2. Product Thesis

Non-deterministic software cannot be trusted through ad hoc spot checks. Teams need a system that does four things well:

- Define expected behavior in a machine-checkable form
- Replay realistic scenarios against an agent repeatedly
- Score outcomes across safety, usefulness, and efficiency
- Convert real-world failures and human corrections into regression cases

Agent Work OS exists to make that loop operational.

## 3. MVP Positioning

### Core Product

A generic Python eval framework with:

- YAML contracts
- replayable scenario bundles
- Agent adapter protocol
- Replay runner
- Deterministic checks
- Optional LLM judge for subjective criteria
- Statistical scoring
- local result persistence

### Reference Wedge

The first reference domain is SRE/DevOps. We will use it to validate that the core abstractions are real, reusable, and not overfit to one prompt or one agent.

The MVP claim is not "works for any agent type." The MVP claim is:

> The same core evaluation engine can express and score multiple SRE/DevOps workflows without domain-specific rewrites to the core.

## 4. Target Users

### Primary User for MVP

- AI engineers building agent systems
- Platform teams experimenting with operational agents
- SRE and DevOps teams evaluating whether an ops assistant is safe and useful

### Future User

- Any team operating a production agent with observable inputs, outputs, and corrections

## 5. MVP Goals

The MVP must prove five things:

1. Teams can define contracts fast enough to be practical
2. The framework can replay realistic scenarios repeatedly with stable scoring
3. Deterministic checks cover most high-value behavior
4. Developers can understand why a scenario passed or failed
5. The same core engine works across more than one SRE workflow

## 6. Non-Goals for MVP

- No autonomous production actions
- No CI or deployment gating in MVP
- No shadow production mode in MVP
- No autonomous deployment
- No autonomous patch application
- No auto-rollback
- No live production control loops
- No broad observability platform coverage
- No custom dashboard requirement
- No multi-team permission model
- No feedback ingestion or regression generation in MVP
- No claim that the framework is already validated for every agent category

## 7. Core Concepts

- **Contract**: versioned YAML file describing expectations, invariants, and acceptance criteria
- **Scenario Bundle**: replayable input package for a test case
- **Schema**: formal JSON/YAML structure for contracts, scenarios, and normalized results
- **Expectation**: one behavioral requirement for a given scenario
- **Invariant**: hard safety rule that cannot be weighted away
- **Adapter**: thin Python interface that executes the target agent
- **Evaluation Run**: repeated trials for one contract and agent version
- **Run Report**: persisted output showing per-scenario checks and aggregate score

## 8. Reference Validation Domain: SRE/DevOps

We will validate the framework against three concrete workflows:

### Workflow A: Alert Triage

Given an alert bundle, the agent should:

- classify severity
- identify likely subsystem or service
- produce a concise incident summary

### Workflow B: Runbook Recommendation

Given incident context, the agent should:

- suggest the correct runbook or next diagnostic step
- avoid unsafe or irrelevant actions
- cite evidence from available context when possible

### Workflow C: Patch or PR Drafting

Given a known remediation pattern, the agent should:

- draft a remediation plan or patch proposal
- include rollback notes
- remain in human-approval mode

These workflows are sufficient to test the framework's generic abstractions without forcing risky automation into the MVP.

## 9. Product Requirements

### 9.1 Contract Authoring

Developers can define contracts in YAML with:

- metadata
- expectations
- invariants
- phase-specific thresholds
- tags
- origin metadata for generated cases

The MVP formalizes three schemas:

- contract schema
- scenario bundle schema
- normalized agent result schema

### 9.2 Agent Integration

The framework exposes a minimal Python adapter protocol so a team can connect an existing agent without rewriting the agent itself.

Adapters do not implement evaluation logic. They only translate native agent input and output into the normalized scenario and result schemas.

### 9.3 Replay Runner

The framework can:

- load scenario bundles
- execute repeated trials
- run deterministic checks first
- run optional LLM judging only when needed
- persist results

Scenario bundles may also declare:

- required tool calls
- forbidden tool calls
- required intermediate steps
- forbidden actions the agent must not propose

### 9.4 Scoring

The MVP will score four practical dimensions:

- **Completion**: did the agent do the job?
- **Safety**: did it avoid forbidden behavior?
- **Utility**: was the output useful enough to act on or review?
- **Efficiency**: what did it cost in time, tokens, and tool usage?

Change tracking and drift analysis are out of MVP. The first product only needs to tell a developer whether the agent behaved correctly on the scenarios they authored.

### 9.5 Run Report

The framework must produce a useful report for each run:

- which scenarios were executed
- which checks passed or failed
- invariant violations
- aggregate completion, safety, utility, and efficiency scores
- concise failure reasons the developer can act on

### 9.6 MVP Phase

The MVP implements one phase only:

- **Design phase**: a developer creates scenarios, runs evaluations locally, and iterates on the agent before any CI or production workflow exists

## 10. Interfaces

### CLI

The CLI is required for MVP. It is the primary developer interface for creating, running, and inspecting evaluations during agent design.

```bash
pip install agentwork

agentwork init
agentwork run
agentwork run --contract contracts/sre-alerts.yaml
agentwork run --only alert-triage
agentwork report list
agentwork report show <run-id>
```

### API

A minimal API is optional for MVP. It exists mainly to support automation and a possible thin frontend later.

### UI

A basic UI is optional and should remain read-only if added in v0.1. The CLI must fully support triggering runs and viewing results on its own.

## 11. Tech Stack

| Component | Technology |
|---|---|
| Backend language | Python 3.11+ |
| CLI | Typer |
| API | FastAPI (optional for MVP) |
| Models | Pydantic v2 |
| Contracts | YAML + JSON Schema validation |
| Storage | SQLite for MVP |
| Optional judge | LiteLLM or provider adapters |
| Tests | pytest |

Frontend is optional for MVP. If needed, it should remain thin, mostly read-only, and sit on top of the Python API.

## 12. Success Metrics

We will consider the MVP validated if we can show:

- at least two SRE workflows expressed using the same core contract model
- meaningful replay results that operators consider directionally correct
- developers can quickly diagnose why scenarios failed
- local evaluation changes agent behavior during the design loop

## 13. What Makes It Different

- It is generic by architecture, but validated through one concrete domain
- It treats behavior as a contract, not a prompt artifact
- It uses replay and repeated trials, not single-shot demos
- It separates checking from scoring so failures are inspectable, not just summarized
- It keeps CI, production, and risky autonomy out of MVP so the core loop can be validated clearly
